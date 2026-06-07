import request from '@/utils/request'
import type { ProductionScheduleItem } from '@/types'

export const getProductionSchedule = (days = 3) =>
  request.get<any, ProductionScheduleItem[]>('/production/schedule', { params: { days } })

export const getTodaySchedule = () =>
  request.get<any, ProductionScheduleItem[]>('/production/schedule/today')

export const updateProductionStatus = (orderId: number, status: string) =>
  request.put<any, { message: string; order_id: number; status: string }>(`/production/orders/${orderId}/status`, null, { params: { status } })
