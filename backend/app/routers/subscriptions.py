from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Tuple, Dict
from datetime import datetime, timedelta, date, time
import random, string
from ..database import get_db
from .. import models, schemas
from .batches import deduct_batch_stock, release_batch_stock, calc_batch_days_left

router = APIRouter()

WORK_MINUTES_PER_DAY = 8 * 60
CHINA_HOLIDAYS_2025_2026 = [
    date(2025, 1, 1), date(2025, 1, 28), date(2025, 1, 29), date(2025, 1, 30),
    date(2025, 1, 31), date(2025, 2, 1), date(2025, 2, 2), date(2025, 2, 3),
    date(2025, 2, 4), date(2025, 4, 4), date(2025, 4, 5), date(2025, 4, 6),
    date(2025, 5, 1), date(2025, 5, 2), date(2025, 5, 3), date(2025, 5, 4),
    date(2025, 5, 5), date(2025, 6, 1), date(2025, 6, 2), date(2025, 10, 1),
    date(2025, 10, 2), date(2025, 10, 3), date(2025, 10, 4), date(2025, 10, 5),
    date(2025, 10, 6), date(2025, 10, 7), date(2025, 10, 8),
    date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3),
    date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18), date(2026, 2, 19),
    date(2026, 2, 20), date(2026, 2, 21), date(2026, 2, 22), date(2026, 2, 23),
    date(2026, 2, 24), date(2026, 4, 4), date(2026, 4, 5), date(2026, 4, 6),
    date(2026, 5, 1), date(2026, 5, 2), date(2026, 5, 3), date(2026, 5, 4),
    date(2026, 5, 5), date(2026, 6, 19), date(2026, 6, 20), date(2026, 6, 21),
    date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3), date(2026, 10, 4),
    date(2026, 10, 5), date(2026, 10, 6), date(2026, 10, 7), date(2026, 10, 8),
]


def generate_subscription_no() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"SUB{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"


def generate_order_no() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"FL{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"


def is_holiday(d: date) -> bool:
    return d in CHINA_HOLIDAYS_2025_2026 or d.weekday() >= 5


def parse_time_str(t: str) -> time:
    try:
        h, m = map(int, t.split(":"))
        return time(h, m)
    except Exception:
        return time(9, 0)


def get_subscription_delivery_dates(
    sub: models.Subscription, start_date: date, end_date: date
) -> List[date]:
    dates = []
    d = max(start_date, sub.contract_start_date)
    actual_end = min(end_date, sub.contract_end_date)
    if sub.pause_start_date and sub.pause_end_date:
        pause_s = sub.pause_start_date
        pause_e = sub.pause_end_date
    elif sub.pause_start_date:
        pause_s = sub.pause_start_date
        pause_e = date(2099, 12, 31)
    else:
        pause_s = None
        pause_e = None

    while d <= actual_end:
        if pause_s and pause_e and pause_s <= d <= pause_e:
            d += timedelta(days=1)
            continue
        if sub.status != "active":
            break
        should_deliver = False
        if sub.frequency == "weekly":
            wd = d.weekday()
            week_days = sub.week_days or [0, 1, 2, 3, 4]
            should_deliver = wd in week_days
        elif sub.frequency == "monthly":
            md = d.day
            month_days = sub.month_days or [1, 15]
            should_deliver = md in month_days
        elif sub.frequency == "daily":
            should_deliver = True

        if should_deliver:
            if is_holiday(d):
                if sub.holiday_policy == "advance":
                    target = d
                    for _ in range(sub.holiday_advance_days or 1):
                        target -= timedelta(days=1)
                        while is_holiday(target):
                            target -= timedelta(days=1)
                    if target not in dates and target >= start_date:
                        dates.append(target)
                elif sub.holiday_policy == "deliver":
                    dates.append(d)
            else:
                dates.append(d)
        d += timedelta(days=1)
    return sorted(set(dates))


def get_flower_loss_rate(db: Session, flower_id: int) -> float:
    total_loss = (
        db.query(func.coalesce(func.sum(models.MaintenanceLog.loss_quantity), 0))
        .filter(models.MaintenanceLog.flower_id == flower_id)
        .scalar()
    )
    batches = db.query(models.FlowerBatch).filter(models.FlowerBatch.flower_id == flower_id).all()
    total_stock = sum(b.total_quantity for b in batches)
    if total_stock == 0:
        return 0.05
    return total_loss / total_stock


def assess_fulfillment_risk(
    db: Session,
    sub: models.Subscription,
    delivery_date: date,
    bouquet: models.Bouquet,
    quantity: int = 1,
) -> Tuple[bool, List[str], Dict, int]:
    reasons = []
    stock_required: Dict[int, int] = {}
    stock_available: Dict[int, Dict] = {}
    total_capacity_min = bouquet.production_time_minutes * quantity

    for bf in bouquet.flowers:
        flower_id = bf.flower_id
        required = bf.quantity * quantity
        loss_rate = get_flower_loss_rate(db, flower_id)
        required_with_loss = int(required * (1 + loss_rate))
        stock_required[flower_id] = required_with_loss

        batches = (
            db.query(models.FlowerBatch)
            .filter(
                models.FlowerBatch.flower_id == flower_id,
                models.FlowerBatch.remaining_quantity > 0,
                models.FlowerBatch.status == "in_stock",
            )
            .all()
        )
        available = 0
        valid_available = 0
        flower = db.query(models.Flower).filter(models.Flower.id == flower_id).first()
        for b in batches:
            days_left = calc_batch_days_left(b)
            available += b.remaining_quantity
            if days_left >= 2:
                valid_available += b.remaining_quantity
        stock_available[flower_id] = {
            "name": flower.name if flower else f"花材{flower_id}",
            "available": available,
            "valid_available": valid_available,
            "required": required_with_loss,
        }
        if valid_available < required_with_loss:
            reasons.append(f"{flower.name if flower else '花材'}库存/保鲜期不足")

    existing_orders = (
        db.query(models.Order)
        .filter(
            and_(
                func.date(models.Order.delivery_time) == delivery_date,
                models.Order.status.in_(["pending", "producing"]),
            )
        )
        .all()
    )
    existing_capacity = 0
    for o in existing_orders:
        for item in o.items:
            if item.bouquet:
                existing_capacity += item.bouquet.production_time_minutes * item.quantity
    total_capacity_used = existing_capacity + total_capacity_min
    if total_capacity_used > WORK_MINUTES_PER_DAY:
        reasons.append(f"产能不足（已用{existing_capacity}分钟，需{total_capacity_min}分钟）")

    if sub.forbidden_flower_ids:
        for bf in bouquet.flowers:
            if bf.flower_id in sub.forbidden_flower_ids:
                f = db.query(models.Flower).filter(models.Flower.id == bf.flower_id).first()
                reasons.append(f"包含禁用花材{f.name if f else ''}")

    can_fulfill = len(reasons) == 0
    return can_fulfill, reasons, stock_available, total_capacity_used


def create_subscription_order(
    db: Session,
    sub: models.Subscription,
    service_point: models.ServicePoint,
    enterprise: models.EnterpriseCustomer,
    delivery_date: date,
) -> models.Order:
    bouquet_id = sub.default_bouquet_id
    if not bouquet_id:
        bouquet_id = db.query(models.Bouquet).first().id if db.query(models.Bouquet).count() > 0 else None
    if not bouquet_id:
        raise HTTPException(status_code=400, detail="系统中没有可用花束")
    bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == bouquet_id).first()

    delivery_time_str = sub.default_delivery_time or service_point.default_delivery_time or "09:00"
    t = parse_time_str(delivery_time_str)
    delivery_dt = datetime.combine(delivery_date, t)

    customer = (
        db.query(models.Customer)
        .filter(models.Customer.phone == enterprise.contact_phone)
        .first()
    )
    if not customer:
        customer = models.Customer(
            name=enterprise.company_name,
            phone=enterprise.contact_phone,
            address=service_point.address,
        )
        db.add(customer)
        db.flush()

    can_fulfill, reasons, _stock, _cap = assess_fulfillment_risk(db, sub, delivery_date, bouquet, 1)

    best_prod_time = delivery_dt - timedelta(minutes=bouquet.production_time_minutes + 30)

    order = models.Order(
        order_no=generate_order_no(),
        customer_id=customer.id,
        total_amount=bouquet.price,
        status="pending",
        delivery_address=f"{service_point.address} {service_point.floor_room or ''}".strip(),
        delivery_phone=service_point.contact_phone,
        delivery_time=delivery_dt,
        best_production_time=best_prod_time,
        remark=f"订阅订单：{sub.name}",
        order_type="subscription",
        subscription_id=sub.id,
        is_risk=not can_fulfill,
        risk_reasons=reasons if not can_fulfill else None,
        service_point_id=service_point.id,
    )
    db.add(order)
    db.flush()

    oi = models.OrderItem(
        order_id=order.id,
        bouquet_id=bouquet.id,
        quantity=1,
        unit_price=bouquet.price,
    )
    db.add(oi)
    db.flush()

    try:
        for bf in bouquet.flowers:
            required = bf.quantity * 1
            deduct_batch_stock(db, oi.id, bf.flower_id, required)
    except HTTPException as e:
        order.is_risk = True
        existing_reasons = order.risk_reasons or []
        existing_reasons.append(str(e.detail))
        order.risk_reasons = existing_reasons

    delivery = models.Delivery(order_id=order.id, status="pending")
    db.add(delivery)

    return order


@router.get("/enterprise-customers", response_model=List[schemas.EnterpriseCustomer])
def list_enterprise_customers(
    skip: int = 0, limit: int = 100, status: str = None, db: Session = Depends(get_db)
):
    query = db.query(models.EnterpriseCustomer)
    if status:
        query = query.filter(models.EnterpriseCustomer.status == status)
    return query.order_by(models.EnterpriseCustomer.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/enterprise-customers/{ec_id}", response_model=schemas.EnterpriseCustomer)
def get_enterprise_customer(ec_id: int, db: Session = Depends(get_db)):
    ec = db.query(models.EnterpriseCustomer).filter(models.EnterpriseCustomer.id == ec_id).first()
    if not ec:
        raise HTTPException(status_code=404, detail="企业客户不存在")
    return ec


@router.post("/enterprise-customers", response_model=schemas.EnterpriseCustomer)
def create_enterprise_customer(
    ec_in: schemas.EnterpriseCustomerCreate, db: Session = Depends(get_db)
):
    ec = models.EnterpriseCustomer(**ec_in.model_dump())
    db.add(ec)
    db.commit()
    db.refresh(ec)
    return ec


@router.put("/enterprise-customers/{ec_id}", response_model=schemas.EnterpriseCustomer)
def update_enterprise_customer(
    ec_id: int, ec_in: schemas.EnterpriseCustomerUpdate, db: Session = Depends(get_db)
):
    ec = db.query(models.EnterpriseCustomer).filter(models.EnterpriseCustomer.id == ec_id).first()
    if not ec:
        raise HTTPException(status_code=404, detail="企业客户不存在")
    for k, v in ec_in.model_dump(exclude_unset=True).items():
        setattr(ec, k, v)
    db.commit()
    db.refresh(ec)
    return ec


@router.delete("/enterprise-customers/{ec_id}")
def delete_enterprise_customer(ec_id: int, db: Session = Depends(get_db)):
    ec = db.query(models.EnterpriseCustomer).filter(models.EnterpriseCustomer.id == ec_id).first()
    if not ec:
        raise HTTPException(status_code=404, detail="企业客户不存在")
    db.delete(ec)
    db.commit()
    return {"message": "删除成功"}


@router.get("/enterprise-customers/{ec_id}/service-points", response_model=List[schemas.ServicePoint])
def list_service_points(ec_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.ServicePoint)
        .filter(models.ServicePoint.enterprise_customer_id == ec_id)
        .all()
    )


@router.get("/service-points", response_model=List[schemas.ServicePoint])
def list_all_service_points(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return db.query(models.ServicePoint).order_by(models.ServicePoint.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/service-points", response_model=schemas.ServicePoint)
def create_service_point(sp_in: schemas.ServicePointCreate, db: Session = Depends(get_db)):
    sp = models.ServicePoint(**sp_in.model_dump())
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return sp


@router.put("/service-points/{sp_id}", response_model=schemas.ServicePoint)
def update_service_point(
    sp_id: int, sp_in: schemas.ServicePointUpdate, db: Session = Depends(get_db)
):
    sp = db.query(models.ServicePoint).filter(models.ServicePoint.id == sp_id).first()
    if not sp:
        raise HTTPException(status_code=404, detail="服务点位不存在")
    for k, v in sp_in.model_dump(exclude_unset=True).items():
        setattr(sp, k, v)
    db.commit()
    db.refresh(sp)
    return sp


@router.delete("/service-points/{sp_id}")
def delete_service_point(sp_id: int, db: Session = Depends(get_db)):
    sp = db.query(models.ServicePoint).filter(models.ServicePoint.id == sp_id).first()
    if not sp:
        raise HTTPException(status_code=404, detail="服务点位不存在")
    db.delete(sp)
    db.commit()
    return {"message": "删除成功"}


@router.get("", response_model=List[schemas.Subscription])
def list_subscriptions(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    enterprise_customer_id: int = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Subscription)
    if status:
        query = query.filter(models.Subscription.status == status)
    if enterprise_customer_id:
        query = query.filter(models.Subscription.enterprise_customer_id == enterprise_customer_id)
    return query.order_by(models.Subscription.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{sub_id}", response_model=schemas.Subscription)
def get_subscription(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(models.Subscription).filter(models.Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    return sub


@router.post("", response_model=schemas.Subscription)
def create_subscription(sub_in: schemas.SubscriptionCreate, db: Session = Depends(get_db)):
    sub = models.Subscription(
        **sub_in.model_dump(),
        subscription_no=generate_subscription_no(),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.put("/{sub_id}", response_model=schemas.Subscription)
def update_subscription(
    sub_id: int, sub_in: schemas.SubscriptionUpdate, db: Session = Depends(get_db)
):
    sub = db.query(models.Subscription).filter(models.Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    for k, v in sub_in.model_dump(exclude_unset=True).items():
        setattr(sub, k, v)
    db.commit()
    db.refresh(sub)
    return sub


@router.post("/{sub_id}/pause", response_model=schemas.Subscription)
def pause_subscription(
    sub_id: int, pause_in: schemas.PauseSubscription, db: Session = Depends(get_db)
):
    sub = db.query(models.Subscription).filter(models.Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    sub.status = "paused"
    sub.pause_start_date = pause_in.pause_start_date
    sub.pause_end_date = pause_in.pause_end_date
    start = pause_in.pause_start_date
    end = pause_in.pause_end_date or date(2099, 12, 31)
    pending_orders = (
        db.query(models.Order)
        .filter(
            and_(
                models.Order.subscription_id == sub_id,
                models.Order.status.in_(["pending", "producing"]),
                func.date(models.Order.delivery_time) >= start,
                func.date(models.Order.delivery_time) <= end,
            )
        )
        .all()
    )
    for o in pending_orders:
        order_items = (
            db.query(models.OrderItem)
            .filter(models.OrderItem.order_id == o.id)
            .all()
        )
        for oi in order_items:
            release_batch_stock(db, oi.id)
        o.status = "cancelled"
        delivery = db.query(models.Delivery).filter(models.Delivery.order_id == o.id).first()
        if delivery:
            delivery.status = "failed"
    db.commit()
    db.refresh(sub)
    return sub


@router.post("/{sub_id}/resume", response_model=schemas.Subscription)
def resume_subscription(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(models.Subscription).filter(models.Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    sub.status = "active"
    sub.pause_start_date = None
    sub.pause_end_date = None
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/{sub_id}")
def delete_subscription(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(models.Subscription).filter(models.Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    pending_orders = (
        db.query(models.Order)
        .filter(
            and_(
                models.Order.subscription_id == sub_id,
                models.Order.status.in_(["pending", "producing"]),
            )
        )
        .all()
    )
    for o in pending_orders:
        order_items = (
            db.query(models.OrderItem)
            .filter(models.OrderItem.order_id == o.id)
            .all()
        )
        for oi in order_items:
            release_batch_stock(db, oi.id)
        o.status = "cancelled"
        delivery = db.query(models.Delivery).filter(models.Delivery.order_id == o.id).first()
        if delivery:
            delivery.status = "failed"
    db.delete(sub)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{sub_id}/generate-orders", response_model=List[schemas.Order])
def generate_subscription_orders(
    sub_id: int, req: schemas.GenerateOrdersRequest, db: Session = Depends(get_db)
):
    sub = db.query(models.Subscription).filter(models.Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    if sub.status != "active":
        raise HTTPException(status_code=400, detail="订阅未激活，无法生成订单")
    service_point = (
        db.query(models.ServicePoint)
        .filter(models.ServicePoint.id == sub.service_point_id)
        .first()
    )
    if not service_point:
        raise HTTPException(status_code=400, detail="服务点位不存在")
    enterprise = (
        db.query(models.EnterpriseCustomer)
        .filter(models.EnterpriseCustomer.id == sub.enterprise_customer_id)
        .first()
    )
    if not enterprise:
        raise HTTPException(status_code=400, detail="企业客户不存在")

    start_date = date.today()
    end_date = start_date + timedelta(days=req.days - 1)
    delivery_dates = get_subscription_delivery_dates(sub, start_date, end_date)

    created_orders = []
    for d in delivery_dates:
        existing = (
            db.query(models.Order)
            .filter(
                and_(
                    models.Order.subscription_id == sub_id,
                    func.date(models.Order.delivery_time) == d,
                    models.Order.status.in_(["pending", "producing", "completed", "delivering"]),
                )
            )
            .first()
        )
        if existing and not req.force:
            continue
        if existing and req.force:
            order_items = (
                db.query(models.OrderItem)
                .filter(models.OrderItem.order_id == existing.id)
                .all()
            )
            for oi in order_items:
                release_batch_stock(db, oi.id)
            db.query(models.OrderItem).filter(models.OrderItem.order_id == existing.id).delete()
            db.query(models.Delivery).filter(models.Delivery.order_id == existing.id).delete()
            db.delete(existing)
            db.flush()
        order = create_subscription_order(db, sub, service_point, enterprise, d)
        created_orders.append(order)
    db.commit()
    result = []
    for o in created_orders:
        db.refresh(o)
        from .orders import enrich_order_batches
        result.append(enrich_order_batches(o))
    return result


@router.post("/generate-all-orders", response_model=List[schemas.Order])
def generate_all_subscription_orders(
    req: schemas.GenerateOrdersRequest, db: Session = Depends(get_db)
):
    active_subs = (
        db.query(models.Subscription).filter(models.Subscription.status == "active").all()
    )
    all_orders = []
    for sub in active_subs:
        try:
            orders = generate_subscription_orders(sub.id, req, db)
            all_orders.extend(orders)
        except Exception:
            continue
    return all_orders


@router.post("/{sub_id}/orders/{order_id}/adjust-bouquet", response_model=schemas.Order)
def adjust_subscription_order_bouquet(
    sub_id: int,
    order_id: int,
    bouquet_id: int,
    db: Session = Depends(get_db),
):
    order = (
        db.query(models.Order)
        .filter(
            and_(
                models.Order.id == order_id,
                models.Order.subscription_id == sub_id,
            )
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="订阅订单不存在")
    if order.status not in ["pending", "producing"]:
        raise HTTPException(status_code=400, detail="订单已处理，无法调整花束")
    bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == bouquet_id).first()
    if not bouquet:
        raise HTTPException(status_code=404, detail="花束不存在")
    order_items = (
        db.query(models.OrderItem)
        .filter(models.OrderItem.order_id == order.id)
        .all()
    )
    for oi in order_items:
        release_batch_stock(db, oi.id)
    db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).delete()
    db.flush()

    order.total_amount = bouquet.price * 1
    max_prod_time = bouquet.production_time_minutes
    order.best_production_time = order.delivery_time - timedelta(minutes=max_prod_time + 30)

    oi = models.OrderItem(
        order_id=order.id,
        bouquet_id=bouquet.id,
        quantity=1,
        unit_price=bouquet.price,
    )
    db.add(oi)
    db.flush()

    can_fulfill, reasons = True, []
    sub = db.query(models.Subscription).filter(models.Subscription.id == sub_id).first()
    deliv_date = order.delivery_time.date()
    can_fulfill, reasons, _s, _c = assess_fulfillment_risk(db, sub, deliv_date, bouquet, 1)
    order.is_risk = not can_fulfill
    order.risk_reasons = reasons if not can_fulfill else None

    try:
        for bf in bouquet.flowers:
            deduct_batch_stock(db, oi.id, bf.flower_id, bf.quantity)
    except HTTPException as e:
        order.is_risk = True
        r = order.risk_reasons or []
        r.append(str(e.detail))
        order.risk_reasons = r

    db.commit()
    db.refresh(order)
    from .orders import enrich_order_batches
    return enrich_order_batches(order)


@router.post("/batch-confirm-week")
def batch_confirm_week(req: schemas.BatchConfirmRequest, db: Session = Depends(get_db)):
    count = 0
    for oid in req.order_ids:
        order = (
            db.query(models.Order)
            .filter(
                and_(
                    models.Order.id == oid,
                    models.Order.order_type == "subscription",
                    models.Order.status == "pending",
                )
            )
            .first()
        )
        if order:
            order.status = "producing"
            delivery = db.query(models.Delivery).filter(models.Delivery.order_id == oid).first()
            if delivery:
                delivery.status = "pending"
            count += 1
    db.commit()
    return {"message": f"批量确认成功，共处理 {count} 个订单", "count": count}


@router.get("/{sub_id}/service-records", response_model=List[schemas.ServiceRecord])
def list_subscription_service_records(sub_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.ServiceRecord)
        .filter(models.ServiceRecord.subscription_id == sub_id)
        .order_by(models.ServiceRecord.service_date.desc())
        .all()
    )


@router.post("/service-records", response_model=schemas.ServiceRecord)
def create_service_record(sr_in: schemas.ServiceRecordCreate, db: Session = Depends(get_db)):
    sr = models.ServiceRecord(**sr_in.model_dump())
    db.add(sr)
    db.commit()
    db.refresh(sr)
    return sr


@router.get("/risk-assessment/{sub_id}", response_model=schemas.FulfillmentRiskAssessment)
def get_subscription_risk_assessment(
    sub_id: int, days: int = 30, db: Session = Depends(get_db)
):
    sub = db.query(models.Subscription).filter(models.Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    bouquet_id = sub.default_bouquet_id or (db.query(models.Bouquet).first().id if db.query(models.Bouquet).count() > 0 else None)
    if not bouquet_id:
        raise HTTPException(status_code=400, detail="无可用花束")
    bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == bouquet_id).first()

    start_date = date.today()
    end_date = start_date + timedelta(days=days - 1)
    delivery_dates = get_subscription_delivery_dates(sub, start_date, end_date)

    all_reasons = []
    total_stock_required: Dict[int, int] = {}
    total_stock_available: Dict[int, Dict] = {}
    total_capacity = 0

    for d in delivery_dates:
        ok, reasons, stock_avail, cap = assess_fulfillment_risk(db, sub, d, bouquet, 1)
        if reasons:
            for r in reasons:
                if r not in all_reasons:
                    all_reasons.append(r)
        for fid, info in stock_avail.items():
            if fid not in total_stock_available:
                total_stock_available[fid] = info
            if fid not in total_stock_required:
                total_stock_required[fid] = 0
        for bf in bouquet.flowers:
            if bf.flower_id not in total_stock_required:
                total_stock_required[bf.flower_id] = 0
            total_stock_required[bf.flower_id] += bf.quantity
        total_capacity += cap

    return schemas.FulfillmentRiskAssessment(
        can_fulfill=len(all_reasons) == 0,
        reasons=all_reasons,
        stock_available={str(k): v for k, v in total_stock_available.items()},
        stock_required={str(k): v for k, v in total_stock_required.items()},
        capacity_minutes=total_capacity,
        capacity_available=WORK_MINUTES_PER_DAY * days,
    )
