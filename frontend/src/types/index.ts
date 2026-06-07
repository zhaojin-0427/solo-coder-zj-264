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
  order_type: string
  subscription_id?: number
  is_risk: boolean
  risk_reasons?: string[]
  service_point_id?: number
  created_at: string
  updated_at: string
  customer?: Customer
  items: OrderItem[]
  delivery?: Delivery
  subscription?: Subscription
  service_point?: ServicePoint
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

export interface MaintenanceLogCreate {
  flower_id: number
  batch_id?: number | null
  temperature: number
  water_changed: number
  loss_quantity: number
  loss_reason?: string
  status: string
  note?: string
  check_date: string
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
  order_type: string
  is_risk: boolean
  risk_reasons?: string[]
  subscription_name?: string
  service_point_name?: string
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

export interface EnterpriseCustomer {
  id: number
  company_name: string
  contact_person: string
  contact_phone: string
  contact_email?: string
  industry?: string
  address?: string
  tax_no?: string
  invoice_title?: string
  bank_info?: string
  remark?: string
  status: string
  created_at: string
  updated_at: string
  service_points: ServicePoint[]
}

export interface EnterpriseCustomerCreate {
  company_name: string
  contact_person: string
  contact_phone: string
  contact_email?: string
  industry?: string
  address?: string
  tax_no?: string
  invoice_title?: string
  bank_info?: string
  remark?: string
  status?: string
}

export interface EnterpriseCustomerUpdate {
  company_name?: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  industry?: string
  address?: string
  tax_no?: string
  invoice_title?: string
  bank_info?: string
  remark?: string
  status?: string
}

export interface ServicePoint {
  id: number
  enterprise_customer_id: number
  location_name: string
  contact_name: string
  contact_phone: string
  address: string
  floor_room?: string
  default_delivery_time: string
  access_instructions?: string
  status: string
  created_at: string
  updated_at: string
}

export interface ServicePointCreate {
  enterprise_customer_id: number
  location_name: string
  contact_name: string
  contact_phone: string
  address: string
  floor_room?: string
  default_delivery_time?: string
  access_instructions?: string
  status?: string
}

export interface ServicePointUpdate {
  enterprise_customer_id?: number
  location_name?: string
  contact_name?: string
  contact_phone?: string
  address?: string
  floor_room?: string
  default_delivery_time?: string
  access_instructions?: string
  status?: string
}

export interface Subscription {
  id: number
  subscription_no: string
  enterprise_customer_id: number
  service_point_id: number
  name: string
  frequency: string
  week_days?: number[]
  month_days?: number[]
  holiday_policy: string
  holiday_advance_days: number
  budget_limit?: number
  default_bouquet_id?: number
  preferred_flower_ids?: number[]
  forbidden_flower_ids?: number[]
  default_delivery_time: string
  contract_start_date: string
  contract_end_date: string
  renewal_remind_days: number
  status: string
  pause_start_date?: string
  pause_end_date?: string
  remark?: string
  created_at: string
  updated_at: string
  enterprise_customer?: EnterpriseCustomer
  service_point?: ServicePoint
  default_bouquet?: Bouquet
}

export interface SubscriptionCreate {
  enterprise_customer_id: number
  service_point_id: number
  name: string
  frequency?: string
  week_days?: number[]
  month_days?: number[]
  holiday_policy?: string
  holiday_advance_days?: number
  budget_limit?: number
  default_bouquet_id?: number
  preferred_flower_ids?: number[]
  forbidden_flower_ids?: number[]
  default_delivery_time?: string
  contract_start_date: string
  contract_end_date: string
  renewal_remind_days?: number
  status?: string
  remark?: string
}

export interface SubscriptionUpdate {
  enterprise_customer_id?: number
  service_point_id?: number
  name?: string
  frequency?: string
  week_days?: number[]
  month_days?: number[]
  holiday_policy?: string
  holiday_advance_days?: number
  budget_limit?: number
  default_bouquet_id?: number
  preferred_flower_ids?: number[]
  forbidden_flower_ids?: number[]
  default_delivery_time?: string
  contract_start_date?: string
  contract_end_date?: string
  renewal_remind_days?: number
  status?: string
  pause_start_date?: string
  pause_end_date?: string
  remark?: string
}

export interface PauseSubscription {
  pause_start_date: string
  pause_end_date?: string
}

export interface GenerateOrdersRequest {
  days?: number
  force?: boolean
}

export interface BatchConfirmRequest {
  order_ids: number[]
}

export interface ServiceRecord {
  id: number
  order_id: number
  subscription_id: number
  enterprise_customer_id: number
  service_point_id: number
  service_date: string
  feedback?: string
  satisfaction?: number
  photo_url?: string
  created_at: string
  updated_at: string
  order?: Order
}

export interface FulfillmentRiskAssessment {
  can_fulfill: boolean
  reasons: string[]
  stock_available: Record<string, any>
  stock_required: Record<string, any>
  capacity_minutes: number
  capacity_available: number
}

export interface EnterpriseMonthlyConsumption {
  enterprise_customer_id: number
  company_name: string
  month: string
  total_amount: number
  order_count: number
}

export interface RenewalReminder {
  subscription_id: number
  subscription_no: string
  subscription_name: string
  company_name: string
  service_point_name: string
  contract_end_date: string
  days_left: number
  monthly_amount: number
}

export interface PointOnTimeRate {
  service_point_id: number
  location_name: string
  company_name: string
  total_deliveries: number
  on_time_deliveries: number
  late_deliveries: number
  on_time_rate: number
}

export interface SubscriptionFlowerForecast {
  flower_id: number
  flower_name: string
  forecast_quantity: number
  current_stock: number
  safe_stock: number
}

export interface CapacityLoad30Item {
  date: string
  total_minutes: number
  order_count: number
  load_ratio: number
  subscription_minutes: number
  retail_minutes: number
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
  enterprise_monthly_consumption: EnterpriseMonthlyConsumption[]
  renewal_reminders: RenewalReminder[]
  point_on_time_rates: PointOnTimeRate[]
  subscription_flower_forecast: SubscriptionFlowerForecast[]
  capacity_load_30: CapacityLoad30Item[]
}
