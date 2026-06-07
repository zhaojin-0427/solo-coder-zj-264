<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import { getDeliveries, updateDelivery } from '@/api/deliveries'
import { getOrders } from '@/api/orders'
import type { Delivery, Order, DeliveryUpdate } from '@/types'

const deliveries = ref<Delivery[]>([])
const orders = ref<Order[]>([])
const loading = ref(false)
const statusFilter = ref('')
const dialogVisible = ref(false)
const currentDelivery = ref<Delivery | null>(null)

const form = ref<DeliveryUpdate>({
  delivery_person: '',
  status: '',
  note: '',
})

const formRef = ref()

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待发货', type: 'warning' },
  ready: { label: '待发货', type: 'warning' },
  shipping: { label: '配送中', type: 'primary' },
  delivered: { label: '已送达', type: 'success' },
  failed: { label: '配送失败', type: 'danger' },
}

const filteredDeliveries = computed(() => {
  if (!statusFilter.value) return deliveries.value
  return deliveries.value.filter((d) => d.status === statusFilter.value)
})

const fetchDeliveries = async () => {
  loading.value = true
  try {
    deliveries.value = await getDeliveries()
  } finally {
    loading.value = false
  }
}

const fetchOrders = async () => {
  orders.value = await getOrders()
}

const getOrder = (orderId: number) => {
  return orders.value.find((o) => o.id === orderId)
}

const handleEdit = (row: Delivery) => {
  currentDelivery.value = row
  form.value = {
    delivery_person: row.delivery_person || '',
    status: row.status,
    note: row.note || '',
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    if (currentDelivery.value) {
      await updateDelivery(currentDelivery.value.id, form.value)
      ElMessage.success('更新成功')
      dialogVisible.value = false
      fetchDeliveries()
    }
  } catch {}
}

const formatDateTime = (str?: string) => {
  if (!str) return '-'
  return str.replace('T', ' ').slice(0, 16)
}

onMounted(async () => {
  await fetchOrders()
  fetchDeliveries()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">配送跟踪</h2>
      <el-radio-group v-model="statusFilter" size="default">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="pending">待发货</el-radio-button>
        <el-radio-button value="shipping">配送中</el-radio-button>
        <el-radio-button value="delivered">已送达</el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="filteredDeliveries" v-loading="loading" stripe style="width: 100%">
      <el-table-column label="订单号" width="180">
        <template #default="{ row }">
          {{ getOrder(row.order_id)?.order_no || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="收货人" width="100">
        <template #default="{ row }">
          {{ getOrder(row.order_id)?.customer?.name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="联系电话" width="130">
        <template #default="{ row }">
          {{ getOrder(row.order_id)?.delivery_phone || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="配送地址" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          {{ getOrder(row.order_id)?.delivery_address || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="期望送达" width="160">
        <template #default="{ row }">
          {{ formatDateTime(getOrder(row.order_id)?.delivery_time) }}
        </template>
      </el-table-column>
      <el-table-column label="实际送达" width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.actual_delivery_time) }}
        </template>
      </el-table-column>
      <el-table-column label="配送员" width="100">
        <template #default="{ row }">
          {{ row.delivery_person || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="是否准时" width="100">
        <template #default="{ row }">
          <el-tag :type="row.on_time ? 'success' : 'danger'">
            {{ row.on_time ? '准时' : '延迟' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'">
            {{ statusMap[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="编辑配送信息" width="480px">
      <el-form ref="formRef" :model="form" label-width="100px">
        <el-form-item label="配送员">
          <el-input v-model="form.delivery_person" placeholder="请输入配送员姓名" />
        </el-form-item>
        <el-form-item label="配送状态" prop="status" :rules="[{ required: true, message: '请选择状态' }]">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="待发货" value="pending" />
            <el-option label="待发货(已制作)" value="ready" />
            <el-option label="配送中" value="shipping" />
            <el-option label="已送达" value="delivered" />
            <el-option label="配送失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
