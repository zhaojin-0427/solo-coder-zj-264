import request from '@/utils/request'
import type { Bouquet, BouquetCreate, BouquetUpdate } from '@/types'

export const getBouquets = () => request.get<any, Bouquet[]>('/bouquets')

export const getBouquet = (id: number) => request.get<any, Bouquet>(`/bouquets/${id}`)

export const createBouquet = (data: BouquetCreate) =>
  request.post<any, Bouquet>('/bouquets', data)

export const updateBouquet = (id: number, data: BouquetUpdate) =>
  request.put<any, Bouquet>(`/bouquets/${id}`, data)

export const deleteBouquet = (id: number) => request.delete<any, void>(`/bouquets/${id}`)
