<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Delete } from '@element-plus/icons-vue'
import { getOrders, deleteOrder, updateOrder } from '@/api/orders'
import type { Order, OrderUpdate } from '@/types'

const orders = ref<Order[]>([])
const loading = ref(false)
const statusFilter = ref('')
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

const filteredOrders = computed(() => {
  if (!statusFilter.value) return orders.value
  return orders.value.filter((o) => o.status === statusFilter.value)
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
      <el-radio-group v-model="statusFilter" size="default">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="pending">待处理</el-radio-button>
        <el-radio-button value="producing">制作中</el-radio-button>
        <el-radio-button value="delivering">配送中</el-radio-button>
        <el-radio-button value="delivered">已完成</el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="filteredOrders" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="order_no" label="订单号" width="180" />
      <el-table-column label="客户" width="120">
        <template #default="{ row }">
          {{ row.customer?.name || '-' }}
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
      <el-table-column label="配送地址" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
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

    <el-dialog v-model="detailVisible" title="订单详情" width="700px">
      <div v-if="currentOrder" class="order-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ currentOrder.order_no }}</el-descriptions-item>
          <el-descriptions-item label="订单金额">¥{{ currentOrder.total_amount.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="客户姓名">{{ currentOrder.customer?.name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ currentOrder.delivery_phone }}</el-descriptions-item>
          <el-descriptions-item label="配送地址" :span="2">{{ currentOrder.delivery_address }}</el-descriptions-item>
          <el-descriptions-item label="期望送达">{{ formatDateTime(currentOrder.delivery_time) }}</el-descriptions-item>
          <el-descriptions-item label="最佳制作时间">{{ formatDateTime(currentOrder.best_production_time) }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="statusMap[currentOrder.status]?.type || 'info'">
              {{ statusMap[currentOrder.status]?.label }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ formatDateTime(currentOrder.created_at) }}</el-descriptions-item>
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
