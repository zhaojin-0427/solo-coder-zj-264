from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List
from datetime import datetime, timedelta, date
from ..database import get_db
from .. import models, schemas
from .batches import calc_batch_days_left

router = APIRouter()


def compute_schedule(
    db: Session, start_date: date, end_date: date
) -> List[schemas.ProductionScheduleItem]:
    orders = (
        db.query(models.Order)
        .filter(
            and_(
                models.Order.status.in_(["pending", "producing"]),
                func.date(models.Order.delivery_time) >= start_date,
                func.date(models.Order.delivery_time) <= end_date,
            )
        )
        .order_by(models.Order.delivery_time.asc())
        .all()
    )

    result = []
    for order in orders:
        customer = order.customer
        max_production_time = 0
        items_summary_parts = []
        min_days_left = 999
        for item in order.items:
            bouquet = item.bouquet
            if bouquet:
                items_summary_parts.append(f"{bouquet.name} x{item.quantity}")
                if bouquet.production_time_minutes > max_production_time:
                    max_production_time = bouquet.production_time_minutes
                for bf in bouquet.flowers:
                    flower_batches = (
                        db.query(models.FlowerBatch)
                        .filter(
                            models.FlowerBatch.flower_id == bf.flower_id,
                            models.FlowerBatch.remaining_quantity > 0,
                            models.FlowerBatch.status == "in_stock",
                        )
                        .all()
                    )
                    for fb in flower_batches:
                        dl = calc_batch_days_left(fb)
                        if dl < min_days_left:
                            min_days_left = dl
        if min_days_left == 999:
            min_days_left = 0
        result.append(
            schemas.ProductionScheduleItem(
                order_id=order.id,
                order_no=order.order_no,
                customer_name=customer.name if customer else "未知",
                delivery_time=order.delivery_time,
                best_production_time=order.best_production_time or order.delivery_time,
                production_time_minutes=max_production_time,
                remaining_shelf_life_days=min_days_left,
                status=order.status,
                items_summary="，".join(items_summary_parts),
            )
        )
    return result


@router.get("/schedule", response_model=List[schemas.ProductionScheduleItem])
def get_production_schedule(
    days: int = 3,
    db: Session = Depends(get_db),
):
    start_date = date.today()
    end_date = start_date + timedelta(days=days - 1)
    return compute_schedule(db, start_date, end_date)


@router.get("/schedule/today", response_model=List[schemas.ProductionScheduleItem])
def get_today_schedule(db: Session = Depends(get_db)):
    today = date.today()
    return compute_schedule(db, today, today)


@router.put("/orders/{order_id}/status")
def update_production_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
):
    valid_statuses = ["pending", "producing", "completed", "delivering", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态: {status}")

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    old_status = order.status
    order.status = status

    delivery_status_map = {
        "pending": "pending",
        "producing": "pending",
        "completed": "ready",
        "delivering": "shipping",
        "delivered": "delivered",
        "cancelled": "failed",
    }
    delivery = (
        db.query(models.Delivery)
        .filter(models.Delivery.order_id == order_id)
        .first()
    )
    if delivery and status in delivery_status_map:
        delivery.status = delivery_status_map[status]
        if status == "delivered" and not delivery.actual_delivery_time:
            delivery.actual_delivery_time = datetime.utcnow()
            delivery.on_time = 1 if delivery.actual_delivery_time <= order.delivery_time else 0

    db.commit()
    db.refresh(order)
    return {"message": "状态更新成功", "order_id": order_id, "status": status}
