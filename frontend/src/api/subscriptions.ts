import request from '@/utils/request'
import type {
  EnterpriseCustomer,
  EnterpriseCustomerCreate,
  EnterpriseCustomerUpdate,
  ServicePoint,
  ServicePointCreate,
  ServicePointUpdate,
  Subscription,
  SubscriptionCreate,
  SubscriptionUpdate,
  PauseSubscription,
  GenerateOrdersRequest,
  BatchConfirmRequest,
  ServiceRecord,
  FulfillmentRiskAssessment,
  Order,
} from '@/types'

export const getEnterpriseCustomers = (params?: { status?: string }) =>
  request.get<any, EnterpriseCustomer[]>('/subscriptions/enterprise-customers', { params })

export const getEnterpriseCustomer = (id: number) =>
  request.get<any, EnterpriseCustomer>(`/subscriptions/enterprise-customers/${id}`)

export const createEnterpriseCustomer = (data: EnterpriseCustomerCreate) =>
  request.post<any, EnterpriseCustomer>('/subscriptions/enterprise-customers', data)

export const updateEnterpriseCustomer = (id: number, data: EnterpriseCustomerUpdate) =>
  request.put<any, EnterpriseCustomer>(`/subscriptions/enterprise-customers/${id}`, data)

export const deleteEnterpriseCustomer = (id: number) =>
  request.delete<any, { message: string }>(`/subscriptions/enterprise-customers/${id}`)

export const getServicePointsByEnterprise = (enterpriseId: number) =>
  request.get<any, ServicePoint[]>(`/subscriptions/enterprise-customers/${enterpriseId}/service-points`)

export const getAllServicePoints = () =>
  request.get<any, ServicePoint[]>('/subscriptions/service-points')

export const createServicePoint = (data: ServicePointCreate) =>
  request.post<any, ServicePoint>('/subscriptions/service-points', data)

export const updateServicePoint = (id: number, data: ServicePointUpdate) =>
  request.put<any, ServicePoint>(`/subscriptions/service-points/${id}`, data)

export const deleteServicePoint = (id: number) =>
  request.delete<any, { message: string }>(`/subscriptions/service-points/${id}`)

export const getSubscriptions = (params?: { status?: string; enterprise_customer_id?: number }) =>
  request.get<any, Subscription[]>('/subscriptions', { params })

export const getSubscription = (id: number) =>
  request.get<any, Subscription>(`/subscriptions/${id}`)

export const createSubscription = (data: SubscriptionCreate) =>
  request.post<any, Subscription>('/subscriptions', data)

export const updateSubscription = (id: number, data: SubscriptionUpdate) =>
  request.put<any, Subscription>(`/subscriptions/${id}`, data)

export const deleteSubscription = (id: number) =>
  request.delete<any, { message: string }>(`/subscriptions/${id}`)

export const pauseSubscription = (id: number, data: PauseSubscription) =>
  request.post<any, Subscription>(`/subscriptions/${id}/pause`, data)

export const resumeSubscription = (id: number) =>
  request.post<any, Subscription>(`/subscriptions/${id}/resume`)

export const generateSubscriptionOrders = (id: number, data: GenerateOrdersRequest) =>
  request.post<any, Order[]>(`/subscriptions/${id}/generate-orders`, data)

export const generateAllSubscriptionOrders = (data: GenerateOrdersRequest) =>
  request.post<any, Order[]>('/subscriptions/generate-all-orders', data)

export const adjustSubscriptionOrderBouquet = (subId: number, orderId: number, bouquetId: number) =>
  request.post<any, Order>(`/subscriptions/${subId}/orders/${orderId}/adjust-bouquet`, null, {
    params: { bouquet_id: bouquetId },
  })

export const batchConfirmWeek = (data: BatchConfirmRequest) =>
  request.post<any, { message: string; count: number }>('/subscriptions/batch-confirm-week', data)

export const getSubscriptionServiceRecords = (subId: number) =>
  request.get<any, ServiceRecord[]>(`/subscriptions/${subId}/service-records`)

export const createServiceRecord = (data: ServiceRecord) =>
  request.post<any, ServiceRecord>('/subscriptions/service-records', data)

export const getSubscriptionRiskAssessment = (subId: number, days = 30) =>
  request.get<any, FulfillmentRiskAssessment>(`/subscriptions/risk-assessment/${subId}`, { params: { days } })
