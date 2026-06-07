<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElTooltip } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import { getProductionSchedule, getTodaySchedule, updateProductionStatus } from '@/api/production'
import type { ProductionScheduleItem } from '@/types'

const schedule = ref<ProductionScheduleItem[]>([])
const loading = ref(false)
const activeTab = ref('today')

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待制作', type: 'info' },
  producing: { label: '制作中', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  delivering: { label: '配送中', type: '' },
  delivered: { label: '已送达', type: 'success' },
  cancelled: { label: '已取消', type: 'info' },
}

const typeMap: Record<string, { label: string; type: string }> = {
  retail: { label: '零售', type: 'info' },
  subscription: { label: '订阅', type: 'primary' },
}

const nextStatusMap: Record<string, string> = {
  pending: 'producing',
  producing: 'completed',
}

const nextStatusLabelMap: Record<string, string> = {
  pending: '标为制作中',
  producing: '标为已完成',
}

const sortedSchedule = computed(() => {
  return [...schedule.value].sort(
    (a, b) => new Date(a.delivery_time).getTime() - new Date(b.delivery_time).getTime()
  )
})

const getShelfLifeClass = (days: number) => {
  if (days <= 1) return 'color: #f56c6c;'
  if (days <= 3) return 'color: #e6a23c;'
  return ''
}

const fetchData = async () => {
  loading.value = true
  try {
    if (activeTab.value === 'today') {
      schedule.value = await getTodaySchedule()
    } else {
      schedule.value = await getProductionSchedule(3)
    }
  } finally {
    loading.value = false
  }
}

const handleTabChange = (tab: string) => {
  activeTab.value = tab
  fetchData()
}

const handleStatusChange = async (row: ProductionScheduleItem) => {
  const nextStatus = nextStatusMap[row.status]
  if (!nextStatus) return
  try {
    await updateProductionStatus(row.order_id, nextStatus)
    ElMessage.success('状态更新成功')
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
      <h2 class="page-title">制作排程</h2>
      <el-tabs v-model="activeTab" style="margin: 0" @tab-change="handleTabChange">
        <el-tab-pane label="今日" name="today" />
        <el-tab-pane label="未来3天" name="future" />
      </el-tabs>
    </div>

    <el-table :data="sortedSchedule" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="order_no" label="订单号" width="180" />
      <el-table-column label="类型" width="80">
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
      <el-table-column label="客户/企业" width="130">
        <template #default="{ row }">
          {{ row.customer_name || row.subscription_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="服务点位" min-width="130" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.service_point_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="期望送达" width="150">
        <template #default="{ row }">
          {{ formatDateTime(row.delivery_time) }}
        </template>
      </el-table-column>
      <el-table-column label="最佳制作时间" width="150">
        <template #default="{ row }">
          {{ formatDateTime(row.best_production_time) }}
        </template>
      </el-table-column>
      <el-table-column label="制作时长" width="90">
        <template #default="{ row }">
          {{ row.production_time_minutes }}分钟
        </template>
      </el-table-column>
      <el-table-column label="花材剩余保鲜" width="120">
        <template #default="{ row }">
          <span :style="getShelfLifeClass(row.remaining_shelf_life_days)">
            {{ row.remaining_shelf_life_days }}天
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="items_summary" label="花束明细" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag
            :type="statusMap[row.status]?.type || 'info'"
            :effect="row.status === 'delivering' ? 'plain' : 'dark'"
          >
            {{ statusMap[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="nextStatusMap[row.status]"
            link
            type="primary"
            @click="handleStatusChange(row)"
          >
            {{ nextStatusLabelMap[row.status] }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
</style>
