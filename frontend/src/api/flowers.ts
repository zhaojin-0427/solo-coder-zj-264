import request from '@/utils/request'
import type { Flower, FlowerCreate, FlowerUpdate } from '@/types'

export const getFlowers = (params?: { warning_only?: boolean }) =>
  request.get<any, Flower[]>('/flowers', { params })

export const getFlower = (id: number) => request.get<any, Flower>(`/flowers/${id}`)

export const createFlower = (data: FlowerCreate) =>
  request.post<any, Flower>('/flowers', data)

export const updateFlower = (id: number, data: FlowerUpdate) =>
  request.put<any, Flower>(`/flowers/${id}`, data)

export const deleteFlower = (id: number) => request.delete<any, void>(`/flowers/${id}`)
