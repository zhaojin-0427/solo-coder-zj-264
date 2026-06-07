from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from . import models


def seed_data(db: Session):
    if db.query(models.Flower).count() > 0:
        return

    flowers_data = [
        {
            "name": "红玫瑰",
            "meaning": "热烈的爱情，表达深深的爱意与激情，适合情人节、纪念日等浪漫场合",
            "shelf_life_days": 7,
            "storage_temp": 4.0,
            "current_stock": 100,
            "unit": "支",
            "purchase_date": date.today(),
            "warning_threshold": 2,
        },
        {
            "name": "白百合",
            "meaning": "纯洁无瑕、百年好合，象征着纯真与神圣的爱情，常用于婚礼",
            "shelf_life_days": 10,
            "storage_temp": 5.0,
            "current_stock": 50,
            "unit": "支",
            "purchase_date": date.today() - timedelta(days=3),
            "warning_threshold": 2,
        },
        {
            "name": "康乃馨",
            "meaning": "感恩、母爱、温馨祝福，适合母亲节和表达感谢之情",
            "shelf_life_days": 14,
            "storage_temp": 3.5,
            "current_stock": 80,
            "unit": "支",
            "purchase_date": date.today() - timedelta(days=1),
            "warning_threshold": 2,
        },
        {
            "name": "向日葵",
            "meaning": "阳光、希望、忠诚，传递积极向上的正能量",
            "shelf_life_days": 8,
            "storage_temp": 6.0,
            "current_stock": 30,
            "unit": "支",
            "purchase_date": date.today() - timedelta(days=6),
            "warning_threshold": 3,
        },
        {
            "name": "郁金香",
            "meaning": "优雅、高贵、爱的告白，代表永恒的祝福",
            "shelf_life_days": 6,
            "storage_temp": 4.5,
            "current_stock": 60,
            "unit": "支",
            "purchase_date": date.today() - timedelta(days=5),
            "warning_threshold": 2,
        },
        {
            "name": "满天星",
            "meaning": "思念、清纯、真心喜欢，常作为配花点缀",
            "shelf_life_days": 12,
            "storage_temp": 4.0,
            "current_stock": 40,
            "unit": "束",
            "purchase_date": date.today() - timedelta(days=2),
            "warning_threshold": 2,
        },
        {
            "name": "尤加利叶",
            "meaning": "恩赐、回忆，清新芳香，常用于花艺配叶",
            "shelf_life_days": 20,
            "storage_temp": 5.0,
            "current_stock": 25,
            "unit": "束",
            "purchase_date": date.today() - timedelta(days=4),
            "warning_threshold": 3,
        },
    ]

    flowers = []
    for fd in flowers_data:
        f = models.Flower(**fd)
        db.add(f)
        db.flush()
        flowers.append(f)

    db.flush()

    if db.query(models.FlowerBatch).count() == 0:
        suppliers = ["昆明花卉基地", "云南花田直供", "上海进口花卉"]
        for i, f in enumerate(flowers):
            batch_qty = f.current_stock
            batch_count = 2 if batch_qty >= 20 else 1
            for bi in range(batch_count):
                qty_part = batch_qty // batch_count if bi < batch_count - 1 else batch_qty - (batch_qty // batch_count) * (batch_count - 1)
                if qty_part <= 0:
                    continue
                batch = models.FlowerBatch(
                    flower_id=f.id,
                    batch_no=f"B{datetime.now().strftime('%Y%m%d')}{1000 + i * 10 + bi}",
                    total_quantity=qty_part,
                    remaining_quantity=qty_part,
                    inbound_date=f.purchase_date,
                    shelf_life_days=f.shelf_life_days,
                    storage_temp=f.storage_temp,
                    supplier=suppliers[i % len(suppliers)],
                    status="in_stock",
                )
                db.add(batch)

    db.commit()

    bouquets_data = [
        {
            "name": "浪漫玫瑰",
            "description": "经典11支红玫瑰花束，搭配满天星点缀，是表达爱意的最佳选择",
            "price": 399.0,
            "meaning": "一生一世的承诺，代表一心一意的爱情",
            "shelf_life_days": 5,
            "production_time_minutes": 45,
            "flowers": [
                {"flower_id": flowers[0].id, "quantity": 11},
                {"flower_id": flowers[5].id, "quantity": 1},
            ],
        },
        {
            "name": "百年好合",
            "description": "白百合与玫瑰的完美组合，寓意美好，适合婚礼和祝福",
            "price": 499.0,
            "meaning": "纯洁的爱情，百年好合，永结同心",
            "shelf_life_days": 7,
            "production_time_minutes": 60,
            "flowers": [
                {"flower_id": flowers[1].id, "quantity": 6},
                {"flower_id": flowers[0].id, "quantity": 9},
                {"flower_id": flowers[6].id, "quantity": 1},
            ],
        },
        {
            "name": "感恩之心",
            "description": "粉色康乃馨花束，传递温暖与感恩",
            "price": 288.0,
            "meaning": "感谢母亲的养育之恩，表达深深的爱意",
            "shelf_life_days": 10,
            "production_time_minutes": 40,
            "flowers": [
                {"flower_id": flowers[2].id, "quantity": 19},
                {"flower_id": flowers[5].id, "quantity": 1},
            ],
        },
        {
            "name": "阳光明媚",
            "description": "向日葵花束，带来满满的正能量和希望",
            "price": 368.0,
            "meaning": "愿你如向日葵般，永远面向阳光，积极向上",
            "shelf_life_days": 6,
            "production_time_minutes": 50,
            "flowers": [
                {"flower_id": flowers[3].id, "quantity": 9},
                {"flower_id": flowers[6].id, "quantity": 2},
            ],
        },
        {
            "name": "优雅绽放",
            "description": "郁金香与尤加利叶的优雅组合，高贵典雅",
            "price": 458.0,
            "meaning": "高贵优雅，如郁金香般绽放迷人光彩",
            "shelf_life_days": 5,
            "production_time_minutes": 55,
            "flowers": [
                {"flower_id": flowers[4].id, "quantity": 15},
                {"flower_id": flowers[6].id, "quantity": 2},
            ],
        },
    ]

    for bd in bouquets_data:
        flowers_list = bd.pop("flowers")
        b = models.Bouquet(**bd)
        db.add(b)
        db.flush()
        for fl in flowers_list:
            bf = models.BouquetFlower(
                bouquet_id=b.id, flower_id=fl["flower_id"], quantity=fl["quantity"]
            )
            db.add(bf)

    db.commit()

    customers_data = [
        {"name": "张小姐", "phone": "13800138001", "address": "北京市朝阳区建国路88号"},
        {"name": "李先生", "phone": "13800138002", "address": "北京市海淀区中关村大街1号"},
        {"name": "王女士", "phone": "13800138003", "address": "北京市西城区金融街1号"},
    ]

    customers = []
    for cd in customers_data:
        c = models.Customer(**cd)
        db.add(c)
        db.flush()
        customers.append(c)

    db.commit()

    for i, (customer, bouquet_idx) in enumerate(
        [(customers[0], 0), (customers[1], 1), (customers[2], 2), (customers[0], 3)]
    ):
        bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == bouquet_idx + 1).first()
        order_date = datetime.now() - timedelta(days=i * 5 + 1)
        delivery_time = order_date + timedelta(hours=3)
        order = models.Order(
            order_no=f"FL{order_date.strftime('%Y%m%d')}{1000+i}",
            customer_id=customer.id,
            total_amount=bouquet.price * 1,
            status="delivered",
            delivery_address=customer.address,
            delivery_phone=customer.phone,
            delivery_time=delivery_time,
            best_production_time=delivery_time - timedelta(minutes=90),
            created_at=order_date,
            updated_at=order_date,
        )
        db.add(order)
        db.flush()

        for bf in bouquet.flowers:
            flower = db.query(models.Flower).filter(models.Flower.id == bf.flower_id).first()
            if flower:
                flower.current_stock = max(0, flower.current_stock - bf.quantity)

        oi = models.OrderItem(
            order_id=order.id,
            bouquet_id=bouquet.id,
            quantity=1,
            unit_price=bouquet.price,
        )
        db.add(oi)

        d = models.Delivery(
            order_id=order.id,
            delivery_person=["小王", "小张", "小李", "小王"][i],
            status="delivered",
            actual_delivery_time=delivery_time - timedelta(minutes=10 if i != 2 else 20),
            on_time=0 if i == 2 else 1,
            created_at=order_date,
            updated_at=order_date,
        )
        db.add(d)

    customer0 = customers[0]
    customer0.total_orders = 2
    customer0.last_order_date = date.today()
    customer1 = customers[1]
    customer1.total_orders = 1
    customer1.last_order_date = date.today() - timedelta(days=5)
    customer2 = customers[2]
    customer2.total_orders = 1
    customer2.last_order_date = date.today() - timedelta(days=10)

    maintenance_data = [
        {
            "flower_id": flowers[0].id,
            "temperature": 4.2,
            "water_changed": 1,
            "loss_quantity": 2,
            "loss_reason": "部分花瓣边缘枯萎",
            "status": "良好",
            "note": "整体状态不错，少数花朵略有萎蔫",
            "check_date": date.today(),
        },
        {
            "flower_id": flowers[1].id,
            "temperature": 5.1,
            "water_changed": 1,
            "loss_quantity": 1,
            "loss_reason": "运输挤压受损",
            "status": "良好",
            "note": "已换水，状态正常",
            "check_date": date.today(),
        },
        {
            "flower_id": flowers[3].id,
            "temperature": 6.0,
            "water_changed": 1,
            "loss_quantity": 3,
            "loss_reason": "接近保鲜期，部分花朵凋谢",
            "status": "警告",
            "note": "建议尽快使用，保鲜期即将结束",
            "check_date": date.today(),
        },
        {
            "flower_id": flowers[4].id,
            "temperature": 4.8,
            "water_changed": 0,
            "loss_quantity": 0,
            "loss_reason": None,
            "status": "良好",
            "note": "状态良好，无需换水",
            "check_date": date.today(),
        },
    ]

    for md in maintenance_data:
        ml = models.MaintenanceLog(**md)
        db.add(ml)
        if md["loss_quantity"] > 0:
            flower = db.query(models.Flower).filter(models.Flower.id == md["flower_id"]).first()
            if flower:
                flower.current_stock = max(0, flower.current_stock - md["loss_quantity"])

    db.commit()
