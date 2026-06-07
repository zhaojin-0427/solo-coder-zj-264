export interface Flower {
  id: number
  name: string
  meaning: string
  shelf_life_days: number
  storage_temp: number
  current_stock: number
  unit: string
  purchase_date: string
  warning_threshold: number
  days_left?: number
  is_warning?: boolean
}

export interface FlowerBatch {
  id: number
  flower_id: number
  batch_no: string
  total_quantity: number
  remaining_quantity: number
  inbound_date: string
  shelf_life_days: number
  storage_temp: number
  supplier?: string
  status: string
  remark?: string
  days_left?: number
  is_warning?: boolean
  is_expired?: boolean
  flower?: Flower
  created_at: string
  updated_at: string
}

export interface FlowerBatchCreate {
  flower_id: number
  total_quantity: number
  remaining_quantity?: number
  inbound_date: string
  shelf_life_days: number
  storage_temp: number
  supplier?: string
  status?: string
  remark?: string
}

export interface FlowerBatchUpdate {
  flower_id?: number
  total_quantity?: number
  remaining_quantity?: number
  inbound_date?: string
  shelf_life_days?: number
  storage_temp?: number
  supplier?: string
  status?: string
  remark?: string
}

export interface OrderItemBatch {
  id: number
  order_item_id: number
  batch_id: number
  flower_id: number
  quantity: number
  created_at: string
  batch?: FlowerBatch
}

export interface BouquetFlower {
  id: number
  flower_id: number
  quantity: number
  flower?: Flower
}

export interface Bouquet {
  id: number
  name: string
  description?: string
  price: number
  image_url?: string
  meaning: string
  shelf_life_days: number
  production_time_minutes: number
  flowers: BouquetFlower[]
}

export interface Customer {
  id: number
  name: string
  phone: string
  address?: string
  total_orders: number
  last_order_date?: string
}

export interface OrderItem {
  id: number
  bouquet_id: number
  quantity: number
  unit_price: number
  bouquet?: Bouquet
  batch_usages: OrderItemBatch[]
}

export interface Delivery {
  id: number
  order_id: number
  delivery_person?: string
  status: string
  actual_delivery_time?: string
  on_time: number
  note?: string
  created_at: string
  updated_at: string
}

export interface Order {
  id: number
  order_no: string
  customer_id: number
  total_amount: number
  status: string
  delivery_address: string
  delivery_phone: string
  delivery_time: string
  best_production_time?: string
  remark?: string
  created_at: string
  updated_at: string
  customer?: Customer
  items: OrderItem[]
  delivery?: Delivery
}

export interface MaintenanceLog {
  id: number
  flower_id: number
  batch_id?: number
  temperature: number
  water_changed: number
  loss_quantity: number
  loss_reason?: string
  status: string
  note?: string
  check_date: string
  created_at: string
  flower?: Flower
  batch?: FlowerBatch
}

export interface ProductionScheduleItem {
  order_id: number
  order_no: string
  customer_name: string
  delivery_time: string
  best_production_time: string
  production_time_minutes: number
  remaining_shelf_life_days: number
  status: string
  items_summary: string
}

export interface BatchLossRate {
  batch_id: number
  batch_no: string
  flower_name: string
  total_quantity: number
  loss_quantity: number
  loss_rate: number
}

export interface BatchExpiryStat {
  total_batches: number
  expiring_batches: number
  expiring_ratio: number
  expired_batches: number
  expired_ratio: number
}

export interface FulfillmentRisk {
  total_orders: number
  risk_orders: number
  risk_details: Array<{
    order_id: number
    order_no: string
    delivery_time: string
    reasons: string[]
  }>
}

export interface CapacityLoadItem {
  date: string
  total_minutes: number
  order_count: number
  load_ratio: number
}

export interface FlowerLossRate {
  flower_id: number
  flower_name: string
  total_stock: number
  total_loss: number
  loss_rate: number
}

export interface PopularBouquet {
  bouquet_id: number
  bouquet_name: string
  order_count: number
  total_quantity: number
}

export interface DeliveryStat {
  total_deliveries: number
  on_time_deliveries: number
  on_time_rate: number
}

export interface RepurchaseCycle {
  customer_id: number
  customer_name: string
  order_count: number
  avg_days_between_orders: number
}

export interface StatsResponse {
  flower_loss_rates: FlowerLossRate[]
  popular_bouquets: PopularBouquet[]
  delivery_stats: DeliveryStat
  repurchase_cycles: RepurchaseCycle[]
  warning_flowers: Flower[]
  batch_loss_rates: BatchLossRate[]
  batch_expiry: BatchExpiryStat
  fulfillment_risk: FulfillmentRisk
  capacity_load: CapacityLoadItem[]
}
