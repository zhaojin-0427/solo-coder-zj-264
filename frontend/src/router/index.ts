import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import Layout from '@/layout/Index.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/shop',
  },
  {
    path: '/shop',
    name: 'Shop',
    component: () => import('@/views/Shop.vue'),
    meta: { title: '在线选购' },
  },
  {
    path: '/admin',
    component: Layout,
    redirect: '/admin/flowers',
    children: [
      {
        path: 'flowers',
        name: 'Flowers',
        component: () => import('@/views/admin/Flowers.vue'),
        meta: { title: '花材库存' },
      },
      {
        path: 'batches',
        name: 'Batches',
        component: () => import('@/views/admin/Batches.vue'),
        meta: { title: '花材批次' },
      },
      {
        path: 'production',
        name: 'Production',
        component: () => import('@/views/admin/Production.vue'),
        meta: { title: '制作排程' },
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/views/admin/Orders.vue'),
        meta: { title: '订单管理' },
      },
      {
        path: 'maintenance',
        name: 'Maintenance',
        component: () => import('@/views/admin/Maintenance.vue'),
        meta: { title: '养护日志' },
      },
      {
        path: 'deliveries',
        name: 'Deliveries',
        component: () => import('@/views/admin/Deliveries.vue'),
        meta: { title: '配送跟踪' },
      },
      {
        path: 'stats',
        name: 'Stats',
        component: () => import('@/views/admin/Stats.vue'),
        meta: { title: '统计分析' },
      },
      {
        path: 'enterprise-customers',
        name: 'EnterpriseCustomers',
        component: () => import('@/views/admin/EnterpriseCustomers.vue'),
        meta: { title: '企业客户' },
      },
      {
        path: 'subscriptions',
        name: 'Subscriptions',
        component: () => import('@/views/admin/Subscriptions.vue'),
        meta: { title: '订阅管理' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
