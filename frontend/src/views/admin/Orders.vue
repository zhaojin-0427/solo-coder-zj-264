<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Delete, Warning } from '@element-plus/icons-vue'
import { getOrders, deleteOrder, updateOrder } from '@/api/orders'
import type { Order, OrderUpdate } from '@/types'

const orders = ref<Order[]>([])
const loading = ref(false)
const statusFilter = ref('')
const typeFilter = ref('')
const detailVisible = ref(false)
const currentOrder = ref<Order | null>(null)

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待处理', type: 'warning' },
  producing: { label: '制作中', type: 'primary' },
  completed: { label: '制作完成', type: 'success' },
  delivering: { label: '配送中', type: 'info' },
  delivered: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'info' },
}

const typeMap: Record<string, { label: string; type: string }> = {
  retail: { label: '零售', type: 'info' },
  subscription: { label: '订阅', type: 'primary' },
}

const filteredOrders = computed(() => {
  let list = orders.value
  if (statusFilter.value) list = list.filter((o) => o.status === statusFilter.value)
  if (typeFilter.value) list = list.filter((o) => (o.order_type || 'retail') === typeFilter.value)
  return list
})

const batchUsageRows = computed(() => {
  if (!currentOrder.value) return []
  const rows: Array<{
    bouquet_name: string
    flower_name: string
    batch_no: string
    quantity: number
    inbound_date: string
    days_left: number | undefined
  }> = []
  for (const item of currentOrder.value.items) {
    for (const usage of item.batch_usages) {
      rows.push({
        bouquet_name: item.bouquet?.name || '-',
        flower_name: usage.batch?.flower?.name || '-',
        batch_no: usage.batch?.batch_no || '-',
        quantity: usage.quantity,
        inbound_date: usage.batch?.inbound_date || '-',
        days_left: usage.batch?.days_left,
      })
    }
  }
  return rows
})

const fetchData = async () => {
  loading.value = true
  try {
    orders.value = await getOrders()
  } finally {
    loading.value = false
  }
}

const handleView = (row: Order) => {
  currentOrder.value = row
  detailVisible.value = true
}

const handleStatusChange = async (row: Order, status: string) => {
  try {
    await updateOrder(row.id, { status } as OrderUpdate)
    ElMessage.success('状态更新成功')
    fetchData()
  } catch {}
}

const handleDelete = async (row: Order) => {
  try {
    await ElMessageBox.confirm(`确定删除订单「${row.order_no}」吗？`, '提示', {
      type: 'warning',
    })
    await deleteOrder(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const formatDateTime = (str?: string) => {
  if (!str) return '-'
  return str.replace('T', ' ').slice(0, 16)
}

onMounted(fetchData)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">订单管理</h2>
      <div>
        <el-radio-group v-model="statusFilter" size="default" style="margin-right: 16px;">
          <el-radio-button value="">全部状态</el-radio-button>
          <el-radio-button value="pending">待处理</el-radio-button>
          <el-radio-button value="producing">制作中</el-radio-button>
          <el-radio-button value="delivering">配送中</el-radio-button>
          <el-radio-button value="delivered">已完成</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="typeFilter" size="default">
          <el-radio-button value="">全部类型</el-radio-button>
          <el-radio-button value="retail">零售</el-radio-button>
          <el-radio-button value="subscription">订阅</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <el-table :data="filteredOrders" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="order_no" label="订单号" width="180" />
      <el-table-column label="订单类型" width="90">
        <template #default="{ row }">
          <el-tag :type="typeMap[row.order_type || 'retail']?.type || 'info'" size="small">
            {{ typeMap[row.order_type || 'retail']?.label || '零售' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="风险" width="60" align="center">
        <template #default="{ row }">
          <el-tooltip v-if="row.is_risk" :content="(row.risk_reasons || []).join('；')">
            <el-icon :size="18" color="#f56c6c"><Warning /></el-icon>
          </el-tooltip>
          <span v-else style="color: #67c23a;">-</span>
        </template>
      </el-table-column>
      <el-table-column label="客户" width="120">
        <template #default="{ row }">
          {{ row.customer?.name || row.subscription?.enterprise_customer?.company_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="联系电话" width="130">
        <template #default="{ row }">
          {{ row.delivery_phone }}
        </template>
      </el-table-column>
      <el-table-column prop="total_amount" label="金额(元)" width="100">
        <template #default="{ row }">
          ¥{{ row.total_amount.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column label="配送地址/点位" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.service_point?.location_name ? `【${row.service_point.location_name}】` : '' }}
          {{ row.delivery_address }}
        </template>
      </el-table-column>
      <el-table-column label="期望送达" width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.delivery_time) }}
        </template>
      </el-table-column>
      <el-table-column label="最佳制作时间" width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.best_production_time) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'">
            {{ statusMap[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="View" @click="handleView(row)">详情</el-button>
          <el-dropdown v-if="row.status !== 'delivered' && row.status !== 'cancelled'" trigger="click" @command="(cmd) => handleStatusChange(row, cmd)">
            <el-button link type="success">更改状态</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="producing">制作中</el-dropdown-item>
                <el-dropdown-item command="delivering">配送中</el-dropdown-item>
                <el-dropdown-item command="delivered">已完成</el-dropdown-item>
                <el-dropdown-item command="cancelled">已取消</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="detailVisible" title="订单详情" width="760px">
      <div v-if="currentOrder" class="order-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ currentOrder.order_no }}</el-descriptions-item>
          <el-descriptions-item label="订单类型">
            <el-tag :type="typeMap[currentOrder.order_type || 'retail']?.type || 'info'">
              {{ typeMap[currentOrder.order_type || 'retail']?.label || '零售' }}
            </el-tag>
            <el-tag v-if="currentOrder.is_risk" type="danger" effect="light" style="margin-left: 8px;">
              <el-icon style="margin-right: 4px;"><Warning /></el-icon>
              履约风险
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="订单金额">¥{{ currentOrder.total_amount.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ formatDateTime(currentOrder.created_at) }}</el-descriptions-item>
          <el-descriptions-item v-if="currentOrder.order_type === 'subscription' || currentOrder.subscription" label="所属订阅" :span="2">
            {{ currentOrder.subscription?.subscription_no || '-' }}（{{ currentOrder.subscription?.name || '-' }}）
            <span v-if="currentOrder.subscription?.enterprise_customer" style="margin-left: 12px; color: #909399;">
              企业：{{ currentOrder.subscription.enterprise_customer.company_name }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item v-if="currentOrder.service_point" label="服务点位" :span="2">
            【{{ currentOrder.service_point.location_name }}】 {{ currentOrder.service_point.address }}
            {{ currentOrder.service_point.floor_room ? '，' + currentOrder.service_point.floor_room : '' }}
          </el-descriptions-item>
          <el-descriptions-item label="客户姓名">{{ currentOrder.customer?.name || currentOrder.service_point?.contact_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ currentOrder.delivery_phone || currentOrder.service_point?.contact_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="配送地址" :span="2">{{ currentOrder.delivery_address }}</el-descriptions-item>
          <el-descriptions-item label="期望送达">{{ formatDateTime(currentOrder.delivery_time) }}</el-descriptions-item>
          <el-descriptions-item label="最佳制作时间">{{ formatDateTime(currentOrder.best_production_time) }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="statusMap[currentOrder.status]?.type || 'info'">
              {{ statusMap[currentOrder.status]?.label }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="currentOrder.is_risk" label="风险原因" :span="2">
            <el-tag v-for="(r, i) in (currentOrder.risk_reasons || [])" :key="i" type="danger" effect="light" style="margin-right: 6px;">
              {{ r }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ currentOrder.remark || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 class="section-title" style="margin-top: 20px;">花束明细</h4>
        <el-table :data="currentOrder.items" border>
          <el-table-column label="花束名称">
            <template #default="{ row }">
              {{ row.bouquet?.name }}
            </template>
          </el-table-column>
          <el-table-column label="单价" width="100">
            <template #default="{ row }">
              ¥{{ row.unit_price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="数量" width="80">
            <template #default="{ row }">
              {{ row.quantity }}
            </template>
          </el-table-column>
          <el-table-column label="小计" width="120">
            <template #default="{ row }">
              ¥{{ (row.unit_price * row.quantity).toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>

        <h4 class="section-title" style="margin-top: 20px;">花材批次使用明细</h4>
        <el-table v-if="batchUsageRows.length > 0" :data="batchUsageRows" border>
          <el-table-column label="花束名称">
            <template #default="{ row }">
              {{ row.bouquet_name }}
            </template>
          </el-table-column>
          <el-table-column label="花材名称">
            <template #default="{ row }">
              {{ row.flower_name }}
            </template>
          </el-table-column>
          <el-table-column label="批次号" width="160">
            <template #default="{ row }">
              {{ row.batch_no }}
            </template>
          </el-table-column>
          <el-table-column label="使用数量" width="100">
            <template #default="{ row }">
              {{ row.quantity }}
            </template>
          </el-table-column>
          <el-table-column label="批次入库日期" width="130">
            <template #default="{ row }">
              {{ row.inbound_date }}
            </template>
          </el-table-column>
          <el-table-column label="保鲜剩余天数" width="120">
            <template #default="{ row }">
              {{ row.days_left !== undefined ? row.days_left + ' 天' : '-' }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无批次使用记录" :image-size="80" />
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.order-detail {
  padding: 0 10px;
}
</style>
