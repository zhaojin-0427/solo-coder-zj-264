from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas

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


@router.post("", response_model=schemas.MaintenanceLog)
def create_log(log_in: schemas.MaintenanceLogCreate, db: Session = Depends(get_db)):
    flower = db.query(models.Flower).filter(models.Flower.id == log_in.flower_id).first()
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")
    log = models.MaintenanceLog(**log_in.model_dump())
    db.add(log)
    if log_in.loss_quantity > 0:
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
    update_data = log_in.model_dump()
    for key, value in update_data.items():
        setattr(log, key, value)
    if old_loss != log_in.loss_quantity:
        flower = db.query(models.Flower).filter(models.Flower.id == log_in.flower_id).first()
        if flower:
            flower.current_stock = max(
                0, flower.current_stock + old_loss - log_in.loss_quantity
            )
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(models.MaintenanceLog).filter(models.MaintenanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="养护日志不存在")
    db.delete(log)
    db.commit()
    return {"message": "删除成功"}
