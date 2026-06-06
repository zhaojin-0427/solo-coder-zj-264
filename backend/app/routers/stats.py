from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date, datetime
from ..database import get_db
from .. import models, schemas
from .flowers import enrich_flower

router = APIRouter()


@router.get("", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    flowers = db.query(models.Flower).all()
    flower_loss_rates = []
    for f in flowers:
        total_loss = (
            db.query(func.coalesce(func.sum(models.MaintenanceLog.loss_quantity), 0))
            .filter(models.MaintenanceLog.flower_id == f.id)
            .scalar()
        )
        total_stock = f.current_stock + total_loss
        loss_rate = (total_loss / total_stock * 100) if total_stock > 0 else 0.0
        flower_loss_rates.append(
            schemas.FlowerLossRate(
                flower_id=f.id,
                flower_name=f.name,
                total_stock=total_stock,
                total_loss=total_loss,
                loss_rate=round(loss_rate, 2),
            )
        )
    flower_loss_rates.sort(key=lambda x: x.loss_rate, reverse=True)

    bouquet_stats = (
        db.query(
            models.OrderItem.bouquet_id,
            models.Bouquet.name,
            func.count(models.OrderItem.order_id.distinct()).label("order_count"),
            func.sum(models.OrderItem.quantity).label("total_quantity"),
        )
        .join(models.Bouquet, models.OrderItem.bouquet_id == models.Bouquet.id)
        .group_by(models.OrderItem.bouquet_id, models.Bouquet.name)
        .order_by(func.sum(models.OrderItem.quantity).desc())
        .all()
    )
    popular_bouquets = [
        schemas.PopularBouquet(
            bouquet_id=bs[0], bouquet_name=bs[1], order_count=bs[2], total_quantity=bs[3]
        )
        for bs in bouquet_stats
    ]

    total_deliveries = db.query(models.Delivery).count()
    on_time_deliveries = (
        db.query(models.Delivery).filter(models.Delivery.on_time == 1).count()
    )
    on_time_rate = (
        round(on_time_deliveries / total_deliveries * 100, 2)
        if total_deliveries > 0
        else 0.0
    )
    delivery_stats = schemas.DeliveryStat(
        total_deliveries=total_deliveries,
        on_time_deliveries=on_time_deliveries,
        on_time_rate=on_time_rate,
    )

    customers = db.query(models.Customer).filter(models.Customer.total_orders >= 2).all()
    repurchase_cycles = []
    for c in customers:
        orders = (
            db.query(models.Order)
            .filter(models.Order.customer_id == c.id)
            .order_by(models.Order.created_at.asc())
            .all()
        )
        if len(orders) >= 2:
            diffs = []
            for i in range(1, len(orders)):
                delta = (orders[i].created_at - orders[i - 1].created_at).days
                diffs.append(delta)
            avg_days = round(sum(diffs) / len(diffs), 1)
            repurchase_cycles.append(
                schemas.RepurchaseCycle(
                    customer_id=c.id,
                    customer_name=c.name,
                    order_count=len(orders),
                    avg_days_between_orders=avg_days,
                )
            )
    repurchase_cycles.sort(key=lambda x: x.avg_days_between_orders)

    warning_flowers = [
        enrich_flower(f)
        for f in flowers
        if enrich_flower(f).is_warning
    ]

    return schemas.StatsResponse(
        flower_loss_rates=flower_loss_rates,
        popular_bouquets=popular_bouquets,
        delivery_stats=delivery_stats,
        repurchase_cycles=repurchase_cycles,
        warning_flowers=warning_flowers,
    )
