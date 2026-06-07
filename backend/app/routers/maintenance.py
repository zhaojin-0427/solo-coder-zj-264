from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas
from .batches import recalc_flower_stock, calc_batch_days_left

router = APIRouter()


@router.get("", response_model=List[schemas.MaintenanceLog])
def list_logs(
    skip: int = 0, limit: int = 100, flower_id: int = None, db: Session = Depends(get_db)
):
    query = db.query(models.MaintenanceLog)
    if flower_id:
        query = query.filter(models.MaintenanceLog.flower_id == flower_id)
    logs = query.order_by(models.MaintenanceLog.check_date.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/{log_id}", response_model=schemas.MaintenanceLog)
def get_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(models.MaintenanceLog).filter(models.MaintenanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="养护日志不存在")
    return log


def deduct_loss_from_batch(db: Session, batch_id: int, quantity: int):
    batch = db.query(models.FlowerBatch).filter(models.FlowerBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    if batch.remaining_quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"批次剩余数量不足，需要 {quantity}，当前 {batch.remaining_quantity}",
        )
    batch.remaining_quantity -= quantity
    if batch.remaining_quantity == 0:
        batch.status = "depleted"
    elif calc_batch_days_left(batch) <= 0:
        batch.status = "expired"
    recalc_flower_stock(db, batch.flower_id)


def add_loss_back_to_batch(db: Session, batch_id: int, quantity: int):
    batch = db.query(models.FlowerBatch).filter(models.FlowerBatch.id == batch_id).first()
    if batch:
        batch.remaining_quantity += quantity
        if batch.status == "depleted" and batch.remaining_quantity > 0:
            batch.status = "in_stock"
        recalc_flower_stock(db, batch.flower_id)


@router.post("", response_model=schemas.MaintenanceLog)
def create_log(log_in: schemas.MaintenanceLogCreate, db: Session = Depends(get_db)):
    flower = db.query(models.Flower).filter(models.Flower.id == log_in.flower_id).first()
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")
    if log_in.batch_id:
        batch = db.query(models.FlowerBatch).filter(models.FlowerBatch.id == log_in.batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")
        if batch.flower_id != log_in.flower_id:
            raise HTTPException(status_code=400, detail="批次与花材不匹配")
    log = models.MaintenanceLog(**log_in.model_dump())
    db.add(log)
    if log_in.loss_quantity > 0:
        if log_in.batch_id:
            deduct_loss_from_batch(db, log_in.batch_id, log_in.loss_quantity)
        else:
            flower.current_stock = max(0, flower.current_stock - log_in.loss_quantity)
    db.commit()
    db.refresh(log)
    return log


@router.put("/{log_id}", response_model=schemas.MaintenanceLog)
def update_log(
    log_id: int, log_in: schemas.MaintenanceLogCreate, db: Session = Depends(get_db)
):
    log = db.query(models.MaintenanceLog).filter(models.MaintenanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="养护日志不存在")
    old_loss = log.loss_quantity
    old_batch_id = log.batch_id
    update_data = log_in.model_dump()
    for key, value in update_data.items():
        setattr(log, key, value)
    if old_loss != log_in.loss_quantity or old_batch_id != log_in.batch_id:
        if old_batch_id and old_loss > 0:
            add_loss_back_to_batch(db, old_batch_id, old_loss)
        elif old_loss > 0:
            flower = db.query(models.Flower).filter(models.Flower.id == log.flower_id).first()
            if flower:
                flower.current_stock = max(0, flower.current_stock + old_loss)
        if log_in.loss_quantity > 0:
            if log_in.batch_id:
                deduct_loss_from_batch(db, log_in.batch_id, log_in.loss_quantity)
            else:
                flower = db.query(models.Flower).filter(models.Flower.id == log_in.flower_id).first()
                if flower:
                    flower.current_stock = max(0, flower.current_stock - log_in.loss_quantity)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(models.MaintenanceLog).filter(models.MaintenanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="养护日志不存在")
    if log.loss_quantity > 0:
        if log.batch_id:
            add_loss_back_to_batch(db, log.batch_id, log.loss_quantity)
        else:
            flower = db.query(models.Flower).filter(models.Flower.id == log.flower_id).first()
            if flower:
                flower.current_stock = max(0, flower.current_stock + log.loss_quantity)
    db.delete(log)
    db.commit()
    return {"message": "删除成功"}
