from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Tuple
from datetime import date, datetime, timedelta
from ..database import get_db
from .. import models, schemas

router = APIRouter()


def generate_batch_no() -> str:
    return f"B{datetime.now().strftime('%Y%m%d%H%M%S')}"


def calc_batch_days_left(batch: models.FlowerBatch) -> int:
    if batch.inbound_date:
        elapsed = (date.today() - batch.inbound_date).days
        return batch.shelf_life_days - elapsed
    return batch.shelf_life_days


def enrich_batch(batch: models.FlowerBatch, flower: models.Flower = None) -> schemas.FlowerBatch:
    days_left = calc_batch_days_left(batch)
    data = schemas.FlowerBatch.model_validate(batch)
    data.days_left = days_left
    if flower:
        data.is_warning = days_left <= flower.warning_threshold
    else:
        data.is_warning = days_left <= 2
    data.is_expired = days_left <= 0
    return data


def recalc_flower_stock(db: Session, flower_id: int):
    batches = (
        db.query(models.FlowerBatch)
        .filter(
            models.FlowerBatch.flower_id == flower_id,
            models.FlowerBatch.status != "discarded",
        )
        .all()
    )
    total = sum(b.remaining_quantity for b in batches)
    flower = db.query(models.Flower).filter(models.Flower.id == flower_id).first()
    if flower:
        flower.current_stock = max(0, total)


def get_batches_by_fefo(
    db: Session, flower_id: int, required: int
) -> List[Tuple[models.FlowerBatch, int]]:
    batches = (
        db.query(models.FlowerBatch)
        .filter(
            models.FlowerBatch.flower_id == flower_id,
            models.FlowerBatch.remaining_quantity > 0,
            models.FlowerBatch.status == "in_stock",
        )
        .order_by(
            (models.FlowerBatch.inbound_date + models.FlowerBatch.shelf_life_days).asc(),
            models.FlowerBatch.inbound_date.asc(),
        )
        .all()
    )
    allocations: List[Tuple[models.FlowerBatch, int]] = []
    remaining = required
    for b in batches:
        if remaining <= 0:
            break
        take = min(b.remaining_quantity, remaining)
        allocations.append((b, take))
        remaining -= take
    if remaining > 0:
        raise HTTPException(
            status_code=400,
            detail=f"花材批次库存不足，需要 {required}，可用 {required - remaining}",
        )
    return allocations


def deduct_batch_stock(
    db: Session, order_item_id: int, flower_id: int, required: int
):
    allocations = get_batches_by_fefo(db, flower_id, required)
    for batch, take in allocations:
        batch.remaining_quantity -= take
        if batch.remaining_quantity == 0:
            batch.status = "depleted"
        usage = models.OrderItemBatch(
            order_item_id=order_item_id,
            batch_id=batch.id,
            flower_id=flower_id,
            quantity=take,
        )
        db.add(usage)
    recalc_flower_stock(db, flower_id)


def release_batch_stock(db: Session, order_item_id: int):
    usages = (
        db.query(models.OrderItemBatch)
        .filter(models.OrderItemBatch.order_item_id == order_item_id)
        .all()
    )
    for u in usages:
        batch = db.query(models.FlowerBatch).filter(models.FlowerBatch.id == u.batch_id).first()
        if batch:
            batch.remaining_quantity += u.quantity
            if batch.status == "depleted" and batch.remaining_quantity > 0:
                batch.status = "in_stock"
            recalc_flower_stock(db, u.flower_id)
        db.delete(u)


@router.get("", response_model=List[schemas.FlowerBatch])
def list_batches(
    skip: int = 0,
    limit: int = 100,
    flower_id: int = None,
    status: str = None,
    expiring_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(models.FlowerBatch)
    if flower_id:
        query = query.filter(models.FlowerBatch.flower_id == flower_id)
    if status:
        query = query.filter(models.FlowerBatch.status == status)
    batches = query.order_by(models.FlowerBatch.inbound_date.desc()).offset(skip).limit(limit).all()
    result = [enrich_batch(b, b.flower) for b in batches]
    if expiring_only:
        result = [b for b in result if b.is_warning or b.is_expired]
    return result


@router.get("/{batch_id}", response_model=schemas.FlowerBatch)
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(models.FlowerBatch).filter(models.FlowerBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    return enrich_batch(batch, batch.flower)


@router.post("", response_model=schemas.FlowerBatch)
def create_batch(batch_in: schemas.FlowerBatchCreate, db: Session = Depends(get_db)):
    flower = db.query(models.Flower).filter(models.Flower.id == batch_in.flower_id).first()
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")
    remaining = batch_in.remaining_quantity if batch_in.remaining_quantity > 0 else batch_in.total_quantity
    batch = models.FlowerBatch(
        **batch_in.model_dump(exclude={"remaining_quantity"}),
        remaining_quantity=remaining,
        batch_no=generate_batch_no(),
    )
    db.add(batch)
    db.flush()
    recalc_flower_stock(db, batch_in.flower_id)
    db.commit()
    db.refresh(batch)
    return enrich_batch(batch, flower)


@router.put("/{batch_id}", response_model=schemas.FlowerBatch)
def update_batch(
    batch_id: int, batch_in: schemas.FlowerBatchUpdate, db: Session = Depends(get_db)
):
    batch = db.query(models.FlowerBatch).filter(models.FlowerBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    old_flower_id = batch.flower_id
    update_data = batch_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(batch, key, value)
    db.flush()
    recalc_flower_stock(db, old_flower_id)
    if "flower_id" in update_data and update_data["flower_id"] != old_flower_id:
        recalc_flower_stock(db, update_data["flower_id"])
    db.commit()
    db.refresh(batch)
    return enrich_batch(batch, batch.flower)


@router.delete("/{batch_id}")
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(models.FlowerBatch).filter(models.FlowerBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    flower_id = batch.flower_id
    db.query(models.OrderItemBatch).filter(models.OrderItemBatch.batch_id == batch_id).delete()
    db.query(models.MaintenanceLog).filter(models.MaintenanceLog.batch_id == batch_id).update({"batch_id": None})
    db.delete(batch)
    recalc_flower_stock(db, flower_id)
    db.commit()
    return {"message": "删除成功"}
