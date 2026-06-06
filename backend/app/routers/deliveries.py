from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from .. import models, schemas

router = APIRouter()


@router.get("", response_model=List[schemas.Delivery])
def list_deliveries(
    skip: int = 0, limit: int = 100, status: str = None, db: Session = Depends(get_db)
):
    query = db.query(models.Delivery)
    if status:
        query = query.filter(models.Delivery.status == status)
    deliveries = (
        query.order_by(models.Delivery.created_at.desc()).offset(skip).limit(limit).all()
    )
    return deliveries


@router.get("/{delivery_id}", response_model=schemas.Delivery)
def get_delivery(delivery_id: int, db: Session = Depends(get_db)):
    delivery = (
        db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    )
    if not delivery:
        raise HTTPException(status_code=404, detail="配送记录不存在")
    return delivery


@router.put("/{delivery_id}", response_model=schemas.Delivery)
def update_delivery(
    delivery_id: int, delivery_in: schemas.DeliveryUpdate, db: Session = Depends(get_db)
):
    delivery = (
        db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    )
    if not delivery:
        raise HTTPException(status_code=404, detail="配送记录不存在")
    update_data = delivery_in.model_dump(exclude_unset=True)
    if update_data.get("status") == "delivered" and not delivery.actual_delivery_time:
        update_data["actual_delivery_time"] = datetime.utcnow()
        order = db.query(models.Order).filter(models.Order.id == delivery.order_id).first()
        if order:
            if update_data["actual_delivery_time"] <= order.delivery_time:
                update_data["on_time"] = 1
            else:
                update_data["on_time"] = 0
            order.status = "delivered"
    for key, value in update_data.items():
        setattr(delivery, key, value)
    db.commit()
    db.refresh(delivery)
    return delivery
