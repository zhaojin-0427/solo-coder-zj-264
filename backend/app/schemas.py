from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List


class FlowerBase(BaseModel):
    name: str
    meaning: str
    shelf_life_days: int
    storage_temp: float
    current_stock: int = 0
    unit: str = "支"
    purchase_date: date = date.today()
    warning_threshold: int = 2


class FlowerCreate(FlowerBase):
    pass


class FlowerUpdate(BaseModel):
    name: Optional[str] = None
    meaning: Optional[str] = None
    shelf_life_days: Optional[int] = None
    storage_temp: Optional[float] = None
    current_stock: Optional[int] = None
    unit: Optional[str] = None
    purchase_date: Optional[date] = None
    warning_threshold: Optional[int] = None


class Flower(FlowerBase):
    id: int
    days_left: Optional[int] = None
    is_warning: Optional[bool] = None

    class Config:
        from_attributes = True


class FlowerBatchBase(BaseModel):
    flower_id: int
    total_quantity: int
    remaining_quantity: int = 0
    inbound_date: date = date.today()
    shelf_life_days: int
    storage_temp: float
    supplier: Optional[str] = None
    status: str = "in_stock"
    remark: Optional[str] = None


class FlowerBatchCreate(FlowerBatchBase):
    pass


class FlowerBatchUpdate(BaseModel):
    flower_id: Optional[int] = None
    total_quantity: Optional[int] = None
    remaining_quantity: Optional[int] = None
    inbound_date: Optional[date] = None
    shelf_life_days: Optional[int] = None
    storage_temp: Optional[float] = None
    supplier: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class FlowerBatch(FlowerBatchBase):
    id: int
    batch_no: str
    days_left: Optional[int] = None
    is_warning: Optional[bool] = None
    is_expired: Optional[bool] = None
    flower: Optional[Flower] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderItemBatchBase(BaseModel):
    order_item_id: int
    batch_id: int
    flower_id: int
    quantity: int


class OrderItemBatch(OrderItemBatchBase):
    id: int
    created_at: datetime
    batch: Optional[FlowerBatch] = None

    class Config:
        from_attributes = True


class BouquetFlowerBase(BaseModel):
    flower_id: int
    quantity: int


class BouquetFlower(BouquetFlowerBase):
    id: int
    flower: Optional[Flower] = None

    class Config:
        from_attributes = True


class BouquetBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    meaning: str
    shelf_life_days: int
    production_time_minutes: int = 60


class BouquetCreate(BouquetBase):
    flowers: List[BouquetFlowerBase]


class BouquetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    meaning: Optional[str] = None
    shelf_life_days: Optional[int] = None
    production_time_minutes: Optional[int] = None
    flowers: Optional[List[BouquetFlowerBase]] = None


class Bouquet(BouquetBase):
    id: int
    flowers: List[BouquetFlower] = []

    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    name: str
    phone: str
    address: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class Customer(CustomerBase):
    id: int
    total_orders: int = 0
    last_order_date: Optional[date] = None

    class Config:
        from_attributes = True


class OrderItemBase(BaseModel):
    bouquet_id: int
    quantity: int
    unit_price: float


class OrderItem(OrderItemBase):
    id: int
    bouquet: Optional[Bouquet] = None
    batch_usages: List[OrderItemBatch] = []

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_id: int
    total_amount: float
    delivery_address: str
    delivery_phone: str
    delivery_time: datetime
    remark: Optional[str] = None


class OrderCreate(BaseModel):
    customer: CustomerCreate
    items: List[OrderItemBase]
    delivery_address: str
    delivery_phone: str
    delivery_time: datetime
    remark: Optional[str] = None


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_phone: Optional[str] = None
    delivery_time: Optional[datetime] = None
    remark: Optional[str] = None


class Order(OrderBase):
    id: int
    order_no: str
    status: str
    best_production_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    customer: Optional[Customer] = None
    items: List[OrderItem] = []
    delivery: Optional["Delivery"] = None

    class Config:
        from_attributes = True


class MaintenanceLogBase(BaseModel):
    flower_id: int
    batch_id: Optional[int] = None
    temperature: float
    water_changed: int = 1
    loss_quantity: int = 0
    loss_reason: Optional[str] = None
    status: str
    note: Optional[str] = None
    check_date: date = date.today()


class MaintenanceLogCreate(MaintenanceLogBase):
    pass


class MaintenanceLog(MaintenanceLogBase):
    id: int
    created_at: datetime
    flower: Optional[Flower] = None
    batch: Optional[FlowerBatch] = None

    class Config:
        from_attributes = True


class DeliveryBase(BaseModel):
    order_id: int
    delivery_person: Optional[str] = None
    status: str = "pending"
    note: Optional[str] = None


class DeliveryUpdate(BaseModel):
    delivery_person: Optional[str] = None
    status: Optional[str] = None
    actual_delivery_time: Optional[datetime] = None
    on_time: Optional[int] = None
    note: Optional[str] = None


class Delivery(DeliveryBase):
    id: int
    actual_delivery_time: Optional[datetime] = None
    on_time: int = 1
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


Order.model_rebuild()


class FlowerLossRate(BaseModel):
    flower_id: int
    flower_name: str
    total_stock: int
    total_loss: int
    loss_rate: float


class PopularBouquet(BaseModel):
    bouquet_id: int
    bouquet_name: str
    order_count: int
    total_quantity: int


class DeliveryStat(BaseModel):
    total_deliveries: int
    on_time_deliveries: int
    on_time_rate: float


class RepurchaseCycle(BaseModel):
    customer_id: int
    customer_name: str
    order_count: int
    avg_days_between_orders: float


class ProductionScheduleItem(BaseModel):
    order_id: int
    order_no: str
    customer_name: str
    delivery_time: datetime
    best_production_time: datetime
    production_time_minutes: int
    remaining_shelf_life_days: int
    status: str
    items_summary: str


class BatchLossRate(BaseModel):
    batch_id: int
    batch_no: str
    flower_name: str
    total_quantity: int
    loss_quantity: int
    loss_rate: float


class BatchExpiryStat(BaseModel):
    total_batches: int
    expiring_batches: int
    expiring_ratio: float
    expired_batches: int
    expired_ratio: float


class FulfillmentRisk(BaseModel):
    total_orders: int
    risk_orders: int
    risk_details: List[dict]


class CapacityLoadItem(BaseModel):
    date: str
    total_minutes: int
    order_count: int
    load_ratio: float


class StatsResponse(BaseModel):
    flower_loss_rates: List[FlowerLossRate]
    popular_bouquets: List[PopularBouquet]
    delivery_stats: DeliveryStat
    repurchase_cycles: List[RepurchaseCycle]
    warning_flowers: List[Flower]
    batch_loss_rates: List[BatchLossRate]
    batch_expiry: BatchExpiryStat
    fulfillment_risk: FulfillmentRisk
    capacity_load: List[CapacityLoadItem]
