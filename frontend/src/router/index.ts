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
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
