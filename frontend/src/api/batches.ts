import request from '@/utils/request'
import type { FlowerBatch, FlowerBatchCreate, FlowerBatchUpdate } from '@/types'

export const getBatches = (params?: { flower_id?: number; status?: string; expiring_only?: boolean }) =>
  request.get<any, FlowerBatch[]>('/batches', { params })

export const getBatch = (id: number) => request.get<any, FlowerBatch>(`/batches/${id}`)

export const createBatch = (data: FlowerBatchCreate) =>
  request.post<any, FlowerBatch>('/batches', data)

export const updateBatch = (id: number, data: FlowerBatchUpdate) =>
  request.put<any, FlowerBatch>(`/batches/${id}`, data)

export const deleteBatch = (id: number) => request.delete<any, void>(`/batches/${id}`)
