import request from '@/utils/request'
import type { MaintenanceLog, MaintenanceLogCreate } from '@/types'

export const getMaintenanceLogs = (params?: { flower_id?: number }) =>
  request.get<any, MaintenanceLog[]>('/maintenance', { params })

export const getMaintenanceLog = (id: number) =>
  request.get<any, MaintenanceLog>(`/maintenance/${id}`)

export const createMaintenanceLog = (data: MaintenanceLogCreate) =>
  request.post<any, MaintenanceLog>('/maintenance', data)

export const updateMaintenanceLog = (id: number, data: MaintenanceLogCreate) =>
  request.put<any, MaintenanceLog>(`/maintenance/${id}`, data)

export const deleteMaintenanceLog = (id: number) =>
  request.delete<any, void>(`/maintenance/${id}`)
