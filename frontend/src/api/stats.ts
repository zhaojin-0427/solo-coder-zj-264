import request from '@/utils/request'
import type { StatsResponse } from '@/types'

export const getStats = () => request.get<any, StatsResponse>('/stats')
