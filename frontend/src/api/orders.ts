import request from '@/utils/request'
import type { Order, OrderCreate, OrderUpdate } from '@/types'

export const getOrders = (params?: { status?: string }) =>
  request.get<any, Order[]>('/orders', { params })

export const getOrder = (id: number) => request.get<any, Order>(`/orders/${id}`)

export const createOrder = (data: OrderCreate) =>
  request.post<any, Order>('/orders', data)

export const updateOrder = (id: number, data: OrderUpdate) =>
  request.put<any, Order>(`/orders/${id}`, data)

export const deleteOrder = (id: number) => request.delete<any, void>(`/orders/${id}`)
