from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from ..database import get_db
from .. import models, schemas
from .batches import deduct_batch_stock, release_batch_stock

router = APIRouter()


def generate_order_no() -> str:
    return f"FL{datetime.now().strftime('%Y%m%d%H%M%S')}"


@router.get("", response_model=List[schemas.Order])
def list_orders(
    skip: int = 0, limit: int = 100, status: str = None, db: Session = Depends(get_db)
):
    query = db.query(models.Order)
    if status:
        query = query.filter(models.Order.status == status)
    orders = query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.post("", response_model=schemas.Order)
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    customer = (
        db.query(models.Customer)
        .filter(models.Customer.phone == order_in.customer.phone)
        .first()
    )
    if not customer:
        customer = models.Customer(**order_in.customer.model_dump())
        db.add(customer)
        db.flush()

    total_amount = sum(item.unit_price * item.quantity for item in order_in.items)

    max_production_time = 0
    for item in order_in.items:
        bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == item.bouquet_id).first()
        if not bouquet:
            raise HTTPException(status_code=400, detail=f"花束 {item.bouquet_id} 不存在")
        if bouquet.production_time_minutes > max_production_time:
            max_production_time = bouquet.production_time_minutes

        for bf in bouquet.flowers:
            flower = db.query(models.Flower).filter(models.Flower.id == bf.flower_id).first()
            if not flower:
                raise HTTPException(status_code=400, detail=f"花材 {bf.flower_id} 不存在")
            required = bf.quantity * item.quantity
            if flower.current_stock < required:
                raise HTTPException(
                    status_code=400,
                    detail=f"花材 {flower.name} 库存不足，需要 {required}，当前 {flower.current_stock}",
                )

    best_production_time = order_in.delivery_time - timedelta(minutes=max_production_time + 30)

    order = models.Order(
        order_no=generate_order_no(),
        customer_id=customer.id,
        total_amount=total_amount,
        delivery_address=order_in.delivery_address,
        delivery_phone=order_in.delivery_phone,
        delivery_time=order_in.delivery_time,
        remark=order_in.remark,
        best_production_time=best_production_time,
        status="pending",
    )
    db.add(order)
    db.flush()

    for item in order_in.items:
        oi = models.OrderItem(
            order_id=order.id,
            bouquet_id=item.bouquet_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        db.add(oi)
        db.flush()

        bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == item.bouquet_id).first()
        for bf in bouquet.flowers:
            required = bf.quantity * item.quantity
            deduct_batch_stock(db, oi.id, bf.flower_id, required)

    delivery = models.Delivery(order_id=order.id, status="pending")
    db.add(delivery)

    customer.total_orders += 1
    customer.last_order_date = datetime.now().date()

    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}", response_model=schemas.Order)
def update_order(
    order_id: int, order_in: schemas.OrderUpdate, db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    old_status = order.status
    update_data = order_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

    if "status" in update_data:
        new_status = update_data["status"]
        if old_status != "cancelled" and new_status == "cancelled":
            order_items = (
                db.query(models.OrderItem)
                .filter(models.OrderItem.order_id == order_id)
                .all()
            )
            for oi in order_items:
                release_batch_stock(db, oi.id)

        status_map = {
            "pending": "pending",
            "producing": "pending",
            "delivering": "shipping",
            "delivered": "delivered",
            "cancelled": "failed",
        }
        delivery_status = status_map.get(new_status)
        if delivery_status:
            delivery = (
                db.query(models.Delivery)
                .filter(models.Delivery.order_id == order_id)
                .first()
            )
            if delivery:
                delivery.status = delivery_status
                if new_status == "delivered" and not delivery.actual_delivery_time:
                    delivery.actual_delivery_time = datetime.utcnow()
                    if delivery.actual_delivery_time <= order.delivery_time:
                        delivery.on_time = 1
                    else:
                        delivery.on_time = 0

    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "cancelled":
        order_items = (
            db.query(models.OrderItem)
            .filter(models.OrderItem.order_id == order_id)
            .all()
        )
        for oi in order_items:
            release_batch_stock(db, oi.id)
    db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).delete()
    db.query(models.Delivery).filter(models.Delivery.order_id == order_id).delete()
    db.delete(order)
    db.commit()
    return {"message": "删除成功"}
