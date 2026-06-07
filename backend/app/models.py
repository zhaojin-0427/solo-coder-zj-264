from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from .database import Base


class Flower(Base):
    __tablename__ = "flowers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    meaning = Column(Text, nullable=False)
    shelf_life_days = Column(Integer, nullable=False)
    storage_temp = Column(Float, nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    unit = Column(String(20), nullable=False, default="支")
    purchase_date = Column(Date, default=date.today)
    warning_threshold = Column(Integer, default=2)

    maintenance_logs = relationship("MaintenanceLog", back_populates="flower")
    bouquet_items = relationship("BouquetFlower", back_populates="flower")
    batches = relationship("FlowerBatch", back_populates="flower", cascade="all, delete-orphan")


class FlowerBatch(Base):
    __tablename__ = "flower_batches"

    id = Column(Integer, primary_key=True, index=True)
    flower_id = Column(Integer, ForeignKey("flowers.id"), nullable=False)
    batch_no = Column(String(50), unique=True, nullable=False)
    total_quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=False, default=0)
    inbound_date = Column(Date, nullable=False, default=date.today)
    shelf_life_days = Column(Integer, nullable=False)
    storage_temp = Column(Float, nullable=False)
    supplier = Column(String(200))
    status = Column(String(20), nullable=False, default="in_stock")
    remark = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    flower = relationship("Flower", back_populates="batches")
    maintenance_logs = relationship("MaintenanceLog", back_populates="batch")
    order_item_usages = relationship("OrderItemBatch", back_populates="batch", cascade="all, delete-orphan")


class Bouquet(Base):
    __tablename__ = "bouquets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image_url = Column(String(500))
    meaning = Column(Text, nullable=False)
    shelf_life_days = Column(Integer, nullable=False)
    production_time_minutes = Column(Integer, nullable=False, default=60)

    flowers = relationship("BouquetFlower", back_populates="bouquet")
    order_items = relationship("OrderItem", back_populates="bouquet")


class BouquetFlower(Base):
    __tablename__ = "bouquet_flowers"

    id = Column(Integer, primary_key=True, index=True)
    bouquet_id = Column(Integer, ForeignKey("bouquets.id"), nullable=False)
    flower_id = Column(Integer, ForeignKey("flowers.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    bouquet = relationship("Bouquet", back_populates="flowers")
    flower = relationship("Flower", back_populates="bouquet_items")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(500))
    total_orders = Column(Integer, default=0)
    last_order_date = Column(Date)

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    delivery_address = Column(String(500), nullable=False)
    delivery_phone = Column(String(20), nullable=False)
    delivery_time = Column(DateTime, nullable=False)
    best_production_time = Column(DateTime)
    remark = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    delivery = relationship("Delivery", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    bouquet_id = Column(Integer, ForeignKey("bouquets.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    bouquet = relationship("Bouquet", back_populates="order_items")
    batch_usages = relationship("OrderItemBatch", back_populates="order_item", cascade="all, delete-orphan")


class OrderItemBatch(Base):
    __tablename__ = "order_item_batches"

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("flower_batches.id"), nullable=False)
    flower_id = Column(Integer, ForeignKey("flowers.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order_item = relationship("OrderItem", back_populates="batch_usages")
    batch = relationship("FlowerBatch", back_populates="order_item_usages")


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(Integer, primary_key=True, index=True)
    flower_id = Column(Integer, ForeignKey("flowers.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("flower_batches.id"))
    check_date = Column(Date, default=date.today)
    temperature = Column(Float, nullable=False)
    water_changed = Column(Integer, nullable=False, default=1)
    loss_quantity = Column(Integer, default=0)
    loss_reason = Column(Text)
    status = Column(String(50), nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    flower = relationship("Flower", back_populates="maintenance_logs")
    batch = relationship("FlowerBatch", back_populates="maintenance_logs")


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    delivery_person = Column(String(50))
    status = Column(String(20), nullable=False, default="pending")
    actual_delivery_time = Column(DateTime)
    on_time = Column(Integer, default=1)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="delivery")
