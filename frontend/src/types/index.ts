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
  temperature: number
  water_changed: number
  loss_quantity: number
  loss_reason?: string
  status: string
  note?: string
  check_date: string
  created_at: string
  flower?: Flower
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
}
