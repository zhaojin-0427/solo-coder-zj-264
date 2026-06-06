import request from '@/utils/request'
import type { Delivery, DeliveryUpdate } from '@/types'

export const getDeliveries = (params?: { status?: string }) =>
  request.get<any, Delivery[]>('/deliveries', { params })

export const getDelivery = (id: number) => request.get<any, Delivery>(`/deliveries/${id}`)

export const updateDelivery = (id: number, data: DeliveryUpdate) =>
  request.put<any, Delivery>(`/deliveries/${id}`, data)
