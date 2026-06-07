from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict
from datetime import date, datetime, timedelta
from ..database import get_db
from .. import models, schemas
from .flowers import enrich_flower
from .batches import calc_batch_days_left

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

    batches = db.query(models.FlowerBatch).all()
    batch_loss_rates = []
    total_batches = len(batches)
    expiring_batches = 0
    expired_batches = 0
    for b in batches:
        days_left = calc_batch_days_left(b)
        if days_left <= 0:
            expired_batches += 1
        elif days_left <= 2:
            expiring_batches += 1
        flower = db.query(models.Flower).filter(models.Flower.id == b.flower_id).first()
        loss_from_logs = (
            db.query(func.coalesce(func.sum(models.MaintenanceLog.loss_quantity), 0))
            .filter(models.MaintenanceLog.batch_id == b.id)
            .scalar()
        )
        used_quantity = (
            db.query(func.coalesce(func.sum(models.OrderItemBatch.quantity), 0))
            .filter(models.OrderItemBatch.batch_id == b.id)
            .scalar()
        )
        loss_quantity = loss_from_logs + (b.total_quantity - b.remaining_quantity - used_quantity)
        loss_quantity = max(0, loss_quantity)
        loss_rate = (loss_from_logs / b.total_quantity * 100) if b.total_quantity > 0 else 0.0
        batch_loss_rates.append(
            schemas.BatchLossRate(
                batch_id=b.id,
                batch_no=b.batch_no,
                flower_name=flower.name if flower else "未知",
                total_quantity=b.total_quantity,
                loss_quantity=loss_from_logs,
                loss_rate=round(loss_rate, 2),
            )
        )
    batch_loss_rates.sort(key=lambda x: x.loss_rate, reverse=True)

    batch_expiry = schemas.BatchExpiryStat(
        total_batches=total_batches,
        expiring_batches=expiring_batches,
        expiring_ratio=round(expiring_batches / total_batches * 100, 2) if total_batches > 0 else 0.0,
        expired_batches=expired_batches,
        expired_ratio=round(expired_batches / total_batches * 100, 2) if total_batches > 0 else 0.0,
    )

    today = date.today()
    three_days_later = today + timedelta(days=3)
    pending_orders = (
        db.query(models.Order)
        .filter(
            and_(
                models.Order.status.in_(["pending", "producing"]),
                func.date(models.Order.delivery_time) <= three_days_later,
            )
        )
        .all()
    )
    risk_orders = 0
    risk_details = []
    for o in pending_orders:
        is_risk = False
        reasons = []
        for item in o.items:
            bouquet = item.bouquet
            if bouquet:
                for bf in bouquet.flowers:
                    flower = db.query(models.Flower).filter(models.Flower.id == bf.flower_id).first()
                    required = bf.quantity * item.quantity
                    if flower and flower.current_stock < required:
                        is_risk = True
                        reasons.append(f"{flower.name}库存不足")
                    else:
                        fb_list = (
                            db.query(models.FlowerBatch)
                            .filter(
                                models.FlowerBatch.flower_id == bf.flower_id,
                                models.FlowerBatch.remaining_quantity > 0,
                                models.FlowerBatch.status == "in_stock",
                            )
                            .all()
                        )
                        if fb_list:
                            min_days = min(calc_batch_days_left(fb) for fb in fb_list)
                            if min_days <= 1:
                                is_risk = True
                                reasons.append(f"{flower.name if flower else '花材'}临期")
        if is_risk:
            risk_orders += 1
            risk_details.append(
                {
                    "order_id": o.id,
                    "order_no": o.order_no,
                    "delivery_time": o.delivery_time.isoformat(),
                    "reasons": reasons,
                }
            )
    fulfillment_risk = schemas.FulfillmentRisk(
        total_orders=len(pending_orders),
        risk_orders=risk_orders,
        risk_details=risk_details,
    )

    capacity_load = []
    work_minutes_per_day = 8 * 60
    for day_offset in range(3):
        d = today + timedelta(days=day_offset)
        next_d = d + timedelta(days=1)
        day_orders = (
            db.query(models.Order)
            .filter(
                and_(
                    func.date(models.Order.delivery_time) >= d,
                    func.date(models.Order.delivery_time) < next_d,
                    models.Order.status.in_(["pending", "producing"]),
                )
            )
            .all()
        )
        total_minutes = 0
        for o in day_orders:
            for item in o.items:
                if item.bouquet:
                    total_minutes += item.bouquet.production_time_minutes * item.quantity
        load_ratio = round(total_minutes / work_minutes_per_day * 100, 2) if work_minutes_per_day > 0 else 0.0
        capacity_load.append(
            schemas.CapacityLoadItem(
                date=d.isoformat(),
                total_minutes=total_minutes,
                order_count=len(day_orders),
                load_ratio=min(load_ratio, 999.99),
            )
        )

    current_month_start = date(today.year, today.month, 1)
    enterprise_orders = (
        db.query(
            models.Order.enterprise_customer_id if hasattr(models.Order, 'enterprise_customer_id') else models.Subscription.enterprise_customer_id,
            func.sum(models.Order.total_amount),
            func.count(models.Order.id.distinct()),
        )
        .outerjoin(models.Subscription, models.Order.subscription_id == models.Subscription.id)
        .filter(
            and_(
                models.Order.order_type == "subscription",
                func.date(models.Order.delivery_time) >= current_month_start,
                models.Order.status.in_(["delivered", "completed", "delivering", "producing", "pending"]),
            )
        )
        .group_by(models.Subscription.enterprise_customer_id)
        .all()
    )
    enterprise_monthly_consumption = []
    for ec_id, total_amt, order_cnt in enterprise_orders:
        if ec_id is None:
            continue
        ec = db.query(models.EnterpriseCustomer).filter(models.EnterpriseCustomer.id == ec_id).first()
        if ec:
            enterprise_monthly_consumption.append(
                schemas.EnterpriseMonthlyConsumption(
                    enterprise_customer_id=ec_id,
                    company_name=ec.company_name,
                    month=today.strftime("%Y-%m"),
                    total_amount=round(float(total_amt or 0), 2),
                    order_count=int(order_cnt or 0),
                )
            )
    enterprise_monthly_consumption.sort(key=lambda x: x.total_amount, reverse=True)

    renewal_reminders = []
    active_subs = db.query(models.Subscription).filter(models.Subscription.status.in_(["active", "paused"])).all()
    month_start = date(today.year, today.month, 1)
    for sub in active_subs:
        days_left = (sub.contract_end_date - today).days
        if days_left <= sub.renewal_remind_days and days_left >= -30:
            ec = db.query(models.EnterpriseCustomer).filter(models.EnterpriseCustomer.id == sub.enterprise_customer_id).first()
            sp = db.query(models.ServicePoint).filter(models.ServicePoint.id == sub.service_point_id).first()
            month_total = (
                db.query(func.coalesce(func.sum(models.Order.total_amount), 0))
                .filter(
                    and_(
                        models.Order.subscription_id == sub.id,
                        func.date(models.Order.delivery_time) >= month_start,
                        models.Order.status.in_(["delivered", "completed", "delivering", "producing", "pending"]),
                    )
                )
                .scalar()
            )
            renewal_reminders.append(
                schemas.RenewalReminder(
                    subscription_id=sub.id,
                    subscription_no=sub.subscription_no,
                    subscription_name=sub.name,
                    company_name=ec.company_name if ec else "未知",
                    service_point_name=sp.location_name if sp else "未知",
                    contract_end_date=sub.contract_end_date,
                    days_left=days_left,
                    monthly_amount=round(float(month_total or 0), 2),
                )
            )
    renewal_reminders.sort(key=lambda x: x.days_left)

    point_on_time_rates = []
    service_points = db.query(models.ServicePoint).filter(models.ServicePoint.status == "active").all()
    for sp in service_points:
        deliveries_q = (
            db.query(models.Delivery)
            .join(models.Order, models.Delivery.order_id == models.Order.id)
            .filter(
                and_(
                    models.Order.service_point_id == sp.id,
                    models.Delivery.status == "delivered",
                )
            )
        )
        total_d = deliveries_q.count()
        on_time_d = deliveries_q.filter(models.Delivery.on_time == 1).count()
        if total_d > 0:
            ec = db.query(models.EnterpriseCustomer).filter(models.EnterpriseCustomer.id == sp.enterprise_customer_id).first()
            point_on_time_rates.append(
                schemas.PointOnTimeRate(
                    service_point_id=sp.id,
                    location_name=sp.location_name,
                    company_name=ec.company_name if ec else "未知",
                    total_deliveries=total_d,
                    on_time_deliveries=on_time_d,
                    late_deliveries=total_d - on_time_d,
                    on_time_rate=round(on_time_d / total_d * 100, 2),
                )
            )
    point_on_time_rates.sort(key=lambda x: x.on_time_rate)

    subscription_flower_forecast = []
    flower_req_map: Dict[int, int] = {}
    active_subs_f = db.query(models.Subscription).filter(models.Subscription.status == "active").all()
    from .subscriptions import get_subscription_delivery_dates
    end_30 = today + timedelta(days=30)
    for sub in active_subs_f:
        dates = get_subscription_delivery_dates(sub, today, end_30)
        bouquet = None
        if sub.default_bouquet_id:
            bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == sub.default_bouquet_id).first()
        if not bouquet:
            first_b = db.query(models.Bouquet).first()
            bouquet = first_b
        if bouquet:
            for _ in dates:
                for bf in bouquet.flowers:
                    if bf.flower_id not in flower_req_map:
                        flower_req_map[bf.flower_id] = 0
                    flower_req_map[bf.flower_id] += bf.quantity
    for fid, qty in flower_req_map.items():
        flower = db.query(models.Flower).filter(models.Flower.id == fid).first()
        cur_stock = flower.current_stock if flower else 0
        subscription_flower_forecast.append(
            schemas.SubscriptionFlowerForecast(
                flower_id=fid,
                flower_name=flower.name if flower else f"花材{fid}",
                forecast_quantity=qty,
                current_stock=cur_stock,
                safe_stock=max(qty, int(cur_stock * 0.3)) if flower else 0,
            )
        )
    subscription_flower_forecast.sort(key=lambda x: x.forecast_quantity, reverse=True)

    capacity_load_30 = []
    for day_offset in range(30):
        d = today + timedelta(days=day_offset)
        next_d = d + timedelta(days=1)
        day_orders = (
            db.query(models.Order)
            .filter(
                and_(
                    func.date(models.Order.delivery_time) >= d,
                    func.date(models.Order.delivery_time) < next_d,
                    models.Order.status.in_(["pending", "producing"]),
                )
            )
            .all()
        )
        total_minutes = 0
        sub_minutes = 0
        retail_minutes = 0
        for o in day_orders:
            for item in o.items:
                if item.bouquet:
                    mins = item.bouquet.production_time_minutes * item.quantity
                    total_minutes += mins
                    if o.order_type == "subscription":
                        sub_minutes += mins
                    else:
                        retail_minutes += mins
        load_ratio = round(total_minutes / work_minutes_per_day * 100, 2) if work_minutes_per_day > 0 else 0.0
        capacity_load_30.append(
            schemas.CapacityLoad30Item(
                date=d.isoformat(),
                total_minutes=total_minutes,
                order_count=len(day_orders),
                load_ratio=min(load_ratio, 999.99),
                subscription_minutes=sub_minutes,
                retail_minutes=retail_minutes,
            )
        )

    return schemas.StatsResponse(
        flower_loss_rates=flower_loss_rates,
        popular_bouquets=popular_bouquets,
        delivery_stats=delivery_stats,
        repurchase_cycles=repurchase_cycles,
        warning_flowers=warning_flowers,
        batch_loss_rates=batch_loss_rates,
        batch_expiry=batch_expiry,
        fulfillment_risk=fulfillment_risk,
        capacity_load=capacity_load,
        enterprise_monthly_consumption=enterprise_monthly_consumption,
        renewal_reminders=renewal_reminders,
        point_on_time_rates=point_on_time_rates,
        subscription_flower_forecast=subscription_flower_forecast,
        capacity_load_30=capacity_load_30,
    )
