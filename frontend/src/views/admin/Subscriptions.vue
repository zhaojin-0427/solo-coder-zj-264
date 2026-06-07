<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  View,
  VideoPlay,
  VideoPause,
  MagicStick,
  Check,
  Warning,
} from '@element-plus/icons-vue'
import {
  getSubscriptions,
  createSubscription,
  updateSubscription,
  deleteSubscription,
  pauseSubscription,
  resumeSubscription,
  generateSubscriptionOrders,
  generateAllSubscriptionOrders,
  adjustSubscriptionOrderBouquet,
  batchConfirmWeek,
  getSubscriptionServiceRecords,
  getSubscriptionRiskAssessment,
  getEnterpriseCustomers,
  getServicePointsByEnterprise,
} from '@/api/subscriptions'
import { getOrders, updateOrder } from '@/api/orders'
import { getBouquets } from '@/api/bouquets'
import type {
  Subscription,
  SubscriptionCreate,
  SubscriptionUpdate,
  EnterpriseCustomer,
  ServicePoint,
  Bouquet,
  Order,
  ServiceRecord,
  FulfillmentRiskAssessment,
} from '@/types'

const loading = ref(false)
const list = ref<Subscription[]>([])
const statusFilter = ref('')
const enterpriseFilter = ref<number | null>(null)
const enterpriseList = ref<EnterpriseCustomer[]>([])
const bouquets = ref<Bouquet[]>([])
const orders = ref<Order[]>([])

const dialogVisible = ref(false)
const formType = ref<'create' | 'edit'>('create')
const currentId = ref<number | null>(null)
const form = ref<SubscriptionCreate>({
  enterprise_customer_id: 0,
  service_point_id: 0,
  name: '',
  frequency: 'weekly',
  week_days: [1, 3, 5],
  month_days: [1, 15],
  holiday_policy: 'skip',
  holiday_advance_days: 1,
  budget_limit: undefined,
  default_bouquet_id: undefined,
  preferred_flower_ids: [],
  forbidden_flower_ids: [],
  default_delivery_time: '09:00',
  contract_start_date: '',
  contract_end_date: '',
  renewal_remind_days: 30,
  status: 'active',
  remark: '',
})
const availableServicePoints = ref<ServicePoint[]>([])

const pauseDialogVisible = ref(false)
const pauseForm = ref({ pause_start_date: '', pause_end_date: '' })

const ordersTabActive = ref(false)
const selectedSubId = ref<number | null>(null)
const subscriptionOrders = computed(() => {
  if (!selectedSubId.value) return []
  return orders.value.filter((o) => o.subscription_id === selectedSubId.value)
})
const batchSelectedOrderIds = ref<number[]>([])
const adjustDialogVisible = ref(false)
const adjustingOrderId = ref<number | null>(null)
const adjustingBouquetId = ref<number | null>(null)

const serviceRecords = ref<ServiceRecord[]>([])
const recordsTabActive = ref(false)

const riskAssessment = ref<FulfillmentRiskAssessment | null>(null)
const riskTabActive = ref(false)

const statusMap: Record<string, { label: string; type: string }> = {
  active: { label: '运行中', type: 'success' },
  paused: { label: '已暂停', type: 'warning' },
  expired: { label: '已到期', type: 'info' },
  cancelled: { label: '已取消', type: 'danger' },
}

const frequencyMap: Record<string, string> = {
  weekly: '周更',
  monthly: '月更',
  daily: '日更',
}

const holidayPolicyMap: Record<string, string> = {
  skip: '跳过',
  advance: '提前配送',
  deliver: '照常配送',
}

const filteredList = computed(() => {
  let result = list.value
  if (statusFilter.value) {
    result = result.filter((s) => s.status === statusFilter.value)
  }
  if (enterpriseFilter.value) {
    result = result.filter((s) => s.enterprise_customer_id === enterpriseFilter.value)
  }
  return result
})

const weekDayOptions = [
  { label: '周一', value: 0 },
  { label: '周二', value: 1 },
  { label: '周三', value: 2 },
  { label: '周四', value: 3 },
  { label: '周五', value: 4 },
  { label: '周六', value: 5 },
  { label: '周日', value: 6 },
]

const formatDate = (d?: string) => (d ? d : '-')

const formatDateTime = (str?: string) => {
  if (!str) return '-'
  return str.replace('T', ' ').slice(0, 16)
}

const fetchData = async () => {
  loading.value = true
  try {
    const [subs, eps, bqs, ods] = await Promise.all([
      getSubscriptions(),
      getEnterpriseCustomers(),
      getBouquets(),
      getOrders(),
    ])
    list.value = subs
    enterpriseList.value = eps
    bouquets.value = bqs
    orders.value = ods
  } finally {
    loading.value = false
  }
}

watch(
  () => form.value.enterprise_customer_id,
  async (val) => {
    if (val) {
      try {
        availableServicePoints.value = await getServicePointsByEnterprise(val)
      } catch {
        availableServicePoints.value = []
      }
    } else {
      availableServicePoints.value = []
    }
  }
)

const openCreate = () => {
  formType.value = 'create'
  currentId.value = null
  form.value = {
    enterprise_customer_id: enterpriseList.value[0]?.id || 0,
    service_point_id: 0,
    name: '',
    frequency: 'weekly',
    week_days: [1, 3, 5],
    month_days: [1, 15],
    holiday_policy: 'skip',
    holiday_advance_days: 1,
    budget_limit: undefined,
    default_bouquet_id: bouquets.value[0]?.id,
    preferred_flower_ids: [],
    forbidden_flower_ids: [],
    default_delivery_time: '09:00',
    contract_start_date: new Date().toISOString().slice(0, 10),
    contract_end_date: new Date(Date.now() + 365 * 24 * 3600 * 1000).toISOString().slice(0, 10),
    renewal_remind_days: 30,
    status: 'active',
    remark: '',
  }
  dialogVisible.value = true
}

const openEdit = (row: Subscription) => {
  formType.value = 'edit'
  currentId.value = row.id
  form.value = {
    enterprise_customer_id: row.enterprise_customer_id,
    service_point_id: row.service_point_id,
    name: row.name,
    frequency: row.frequency,
    week_days: row.week_days || [],
    month_days: row.month_days || [],
    holiday_policy: row.holiday_policy,
    holiday_advance_days: row.holiday_advance_days,
    budget_limit: row.budget_limit,
    default_bouquet_id: row.default_bouquet_id,
    preferred_flower_ids: row.preferred_flower_ids || [],
    forbidden_flower_ids: row.forbidden_flower_ids || [],
    default_delivery_time: row.default_delivery_time,
    contract_start_date: row.contract_start_date,
    contract_end_date: row.contract_end_date,
    renewal_remind_days: row.renewal_remind_days,
    status: row.status,
    remark: row.remark,
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.name || !form.value.enterprise_customer_id || !form.value.service_point_id || !form.value.contract_start_date || !form.value.contract_end_date) {
    ElMessage.warning('请填写必填项')
    return
  }
  try {
    if (formType.value === 'create') {
      await createSubscription(form.value)
      ElMessage.success('创建订阅成功')
    } else if (currentId.value) {
      await updateSubscription(currentId.value, form.value as SubscriptionUpdate)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {}
}

const handleDelete = async (row: Subscription) => {
  try {
    await ElMessageBox.confirm(`确定删除订阅「${row.name}」吗？相关待处理订单将被取消。`, '提示', { type: 'warning' })
    await deleteSubscription(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const openPause = (row: Subscription) => {
  currentId.value = row.id
  pauseForm.value = {
    pause_start_date: new Date().toISOString().slice(0, 10),
    pause_end_date: '',
  }
  pauseDialogVisible.value = true
}

const handlePause = async () => {
  if (!pauseForm.value.pause_start_date || !currentId.value) return
  try {
    await pauseSubscription(currentId.value, {
      pause_start_date: pauseForm.value.pause_start_date,
      pause_end_date: pauseForm.value.pause_end_date || undefined,
    })
    ElMessage.success('已暂停订阅')
    pauseDialogVisible.value = false
    fetchData()
  } catch {}
}

const handleResume = async (row: Subscription) => {
  try {
    await resumeSubscription(row.id)
    ElMessage.success('已恢复订阅')
    fetchData()
  } catch {}
}

const handleGenerateOrders = async (row: Subscription) => {
  try {
    await ElMessageBox.confirm(`将为订阅「${row.name}」生成未来 30 天的订单，是否继续？`, '提示', { type: 'info' })
    const res = await generateSubscriptionOrders(row.id, { days: 30, force: false })
    ElMessage.success(`成功生成 ${res.length} 个订单`)
    fetchData()
  } catch {}
}

const handleGenerateAll = async () => {
  try {
    await ElMessageBox.confirm('将为所有激活的订阅生成未来 30 天的订单，是否继续？', '提示', { type: 'info' })
    const res = await generateAllSubscriptionOrders({ days: 30, force: false })
    ElMessage.success(`共生成 ${res.length} 个订单`)
    fetchData()
  } catch {}
}

const openOrders = async (row: Subscription) => {
  selectedSubId.value = row.id
  ordersTabActive.value = true
  batchSelectedOrderIds.value = []
}

const handleBatchConfirm = async () => {
  if (batchSelectedOrderIds.value.length === 0) {
    ElMessage.warning('请选择要确认的订单')
    return
  }
  try {
    const res = await batchConfirmWeek({ order_ids: batchSelectedOrderIds.value })
    ElMessage.success(res.message)
    fetchData()
  } catch {}
}

const openAdjustBouquet = (order: Order) => {
  adjustingOrderId.value = order.id
  adjustingBouquetId.value = order.items[0]?.bouquet_id || null
  adjustDialogVisible.value = true
}

const handleAdjustBouquet = async () => {
  if (!adjustingOrderId.value || !adjustingBouquetId.value || !selectedSubId.value) return
  try {
    await adjustSubscriptionOrderBouquet(selectedSubId.value, adjustingOrderId.value, adjustingBouquetId.value)
    ElMessage.success('花束调整成功')
    adjustDialogVisible.value = false
    fetchData()
  } catch {}
}

const handleOrderStatus = async (row: Order, status: string) => {
  try {
    await updateOrder(row.id, { status })
    ElMessage.success('状态更新成功')
    fetchData()
  } catch {}
}

const openServiceRecords = async (row: Subscription) => {
  selectedSubId.value = row.id
  recordsTabActive.value = true
  try {
    serviceRecords.value = await getSubscriptionServiceRecords(row.id)
  } catch {
    serviceRecords.value = []
  }
}

const openRiskAssessment = async (row: Subscription) => {
  selectedSubId.value = row.id
  riskTabActive.value = true
  try {
    riskAssessment.value = await getSubscriptionRiskAssessment(row.id, 30)
  } catch {
    riskAssessment.value = null
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">订阅管理</h2>
      <div style="display: flex; gap: 12px; align-items: center;">
        <el-select v-model="enterpriseFilter" placeholder="全部企业" clearable style="width: 180px">
          <el-option
            v-for="ep in enterpriseList"
            :key="ep.id"
            :label="ep.company_name"
            :value="ep.id"
          />
        </el-select>
        <el-radio-group v-model="statusFilter" size="default">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="active">运行中</el-radio-button>
          <el-radio-button value="paused">已暂停</el-radio-button>
          <el-radio-button value="expired">已到期</el-radio-button>
        </el-radio-group>
        <el-button type="success" :icon="MagicStick" @click="handleGenerateAll">一键生成全部30天订单</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增订阅</el-button>
      </div>
    </div>

    <el-table :data="filteredList" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="subscription_no" label="订阅编号" width="180" />
      <el-table-column prop="name" label="订阅名称" width="180" />
      <el-table-column label="企业客户" width="160">
        <template #default="{ row }">
          {{ enterpriseList.find((e) => e.id === row.enterprise_customer_id)?.company_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="服务点位" width="140">
        <template #default="{ row }">
          {{ row.service_point?.point_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="周期" width="80">
        <template #default="{ row }">{{ frequencyMap[row.frequency] || row.frequency }}</template>
      </el-table-column>
      <el-table-column label="配送日期" width="140">
        <template #default="{ row }">
          <span v-if="row.frequency === 'weekly'">
            {{ (row.week_days || []).map((d) => ['一','二','三','四','五','六','日'][d]).join('、') }}
          </span>
          <span v-else-if="row.frequency === 'monthly'">
            {{ (row.month_days || []).map((d) => d + '号').join('、') }}
          </span>
          <span v-else>每日</span>
        </template>
      </el-table-column>
      <el-table-column label="节假日" width="100">
        <template #default="{ row }">{{ holidayPolicyMap[row.holiday_policy] }}</template>
      </el-table-column>
      <el-table-column label="合同期" width="220">
        <template #default="{ row }">
          {{ formatDate(row.contract_start_date) }} ~ {{ formatDate(row.contract_end_date) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'">
            {{ statusMap[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="380" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="MagicStick" @click="handleGenerateOrders(row)">生成订单</el-button>
          <el-button link type="primary" :icon="View" @click="openOrders(row)">订单</el-button>
          <el-button link type="primary" :icon="Warning" @click="openRiskAssessment(row)">风险评估</el-button>
          <el-button link type="primary" @click="openServiceRecords(row)">服务记录</el-button>
          <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-if="row.status === 'active'"
            link
            type="warning"
            :icon="VideoPause"
            @click="openPause(row)"
          >暂停</el-button>
          <el-button
            v-if="row.status === 'paused'"
            link
            type="success"
            :icon="VideoPlay"
            @click="handleResume(row)"
          >恢复</el-button>
          <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="formType === 'create' ? '新增订阅' : '编辑订阅'" width="700px">
      <el-form :model="form" label-width="130px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="订阅名称" required>
              <el-input v-model="form.name" placeholder="如：酒店大堂每周花艺" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="企业客户" required>
              <el-select v-model="form.enterprise_customer_id" style="width: 100%">
                <el-option
                  v-for="ep in enterpriseList"
                  :key="ep.id"
                  :label="ep.company_name"
                  :value="ep.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="服务点位" required>
              <el-select v-model="form.service_point_id" style="width: 100%">
                <el-option
                  v-for="sp in availableServicePoints"
                  :key="sp.id"
                  :label="sp.location_name"
                  :value="sp.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认花束">
              <el-select v-model="form.default_bouquet_id" style="width: 100%" clearable>
                <el-option v-for="b in bouquets" :key="b.id" :label="b.name" :value="b.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="配送周期" required>
              <el-select v-model="form.frequency">
                <el-option label="周更" value="weekly" />
                <el-option label="月更" value="monthly" />
                <el-option label="日更" value="daily" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="默认配送时间">
              <el-time-select v-model="form.default_delivery_time" start="08:00" step="00:30" end="18:00" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="预算上限(元)">
              <el-input-number v-model="form.budget_limit" :min="0" :precision="2" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item v-if="form.frequency === 'weekly'" label="每周配送日">
          <el-checkbox-group v-model="form.week_days">
            <el-checkbox v-for="w in weekDayOptions" :key="w.value" :label="w.value">{{ w.label }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item v-if="form.frequency === 'monthly'" label="每月配送日">
          <el-select v-model="form.month_days" multiple collapse-tags collapse-tags-tooltip style="width: 100%">
            <el-option v-for="d in Array.from({ length: 28 }, (_, i) => i + 1)" :key="d" :label="d + '号'" :value="d" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="节假日策略">
              <el-select v-model="form.holiday_policy">
                <el-option label="跳过配送" value="skip" />
                <el-option label="提前配送" value="advance" />
                <el-option label="照常配送" value="deliver" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="提前天数">
              <el-input-number v-model="form.holiday_advance_days" :min="0" :max="7" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="合同开始日期" required>
              <el-date-picker v-model="form.contract_start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同结束日期" required>
              <el-date-picker v-model="form.contract_end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="续约提醒天数">
          <el-input-number v-model="form.renewal_remind_days" :min="1" :max="90" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="运行中" value="active" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已到期" value="expired" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pauseDialogVisible" title="暂停订阅" width="400px">
      <el-form label-width="110px">
        <el-form-item label="暂停开始日期" required>
          <el-date-picker v-model="pauseForm.pause_start_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="暂停结束日期">
          <el-date-picker v-model="pauseForm.pause_end_date" type="date" value-format="YYYY-MM-DD" />
          <div style="color: #909399; font-size: 12px;">不填则长期暂停，需手动恢复</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pauseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePause">确认暂停</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="ordersTabActive" title="订阅订单" size="900px" @close="ordersTabActive = false">
      <div class="page-header" style="padding: 0 0 16px;">
        <h3 class="section-title">该订阅订单列表</h3>
        <div style="display: flex; gap: 10px;">
          <el-button type="success" :icon="Check" @click="handleBatchConfirm">
            批量确认本周 ({{ batchSelectedOrderIds.length }})
          </el-button>
        </div>
      </div>
      <el-table
        :data="subscriptionOrders"
        stripe
        @selection-change="(val: Order[]) => batchSelectedOrderIds = val.map((o) => o.id)"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column label="配送时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.delivery_time) }}</template>
        </el-table-column>
        <el-table-column prop="total_amount" label="金额" width="100">
          <template #default="{ row }">¥{{ row.total_amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="风险标记" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_risk" type="danger" size="small" :icon="Warning">风险</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险原因" min-width="180">
          <template #default="{ row }">
            <el-tag
              v-for="(r, i) in row.risk_reasons || []"
              :key="i"
              type="danger"
              effect="light"
              size="small"
              style="margin: 2px;"
            >{{ r }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="
              row.status === 'delivered' ? 'success' :
              row.status === 'cancelled' ? 'info' :
              row.status === 'producing' ? 'primary' : 'warning'
            ">
              {{ row.status === 'pending' ? '待处理' : row.status === 'producing' ? '制作中' : row.status === 'delivered' ? '已完成' : row.status === 'cancelled' ? '已取消' : row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending' || row.status === 'producing'"
              link
              type="primary"
              size="small"
              @click="openAdjustBouquet(row)"
            >调整花束</el-button>
            <el-dropdown
              v-if="row.status !== 'delivered' && row.status !== 'cancelled'"
              trigger="click"
              @command="(cmd: string) => handleOrderStatus(row, cmd)"
            >
              <el-button link type="success" size="small">更改状态</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="producing">制作中</el-dropdown-item>
                  <el-dropdown-item command="delivering">配送中</el-dropdown-item>
                  <el-dropdown-item command="delivered">已完成</el-dropdown-item>
                  <el-dropdown-item command="cancelled">已取消</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <el-dialog v-model="adjustDialogVisible" title="调整配送花束" width="400px">
      <el-form label-width="100px">
        <el-form-item label="选择花束">
          <el-select v-model="adjustingBouquetId" style="width: 100%">
            <el-option v-for="b in bouquets" :key="b.id" :label="`${b.name}（¥${b.price}）`" :value="b.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adjustDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAdjustBouquet">确认调整</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="recordsTabActive" title="服务记录" size="700px" @close="recordsTabActive = false">
      <el-table :data="serviceRecords" stripe>
        <el-table-column label="服务日期" width="140">
          <template #default="{ row }">{{ row.service_date }}</template>
        </el-table-column>
        <el-table-column label="关联订单" width="180">
          <template #default="{ row }">{{ row.order?.order_no || '-' }}</template>
        </el-table-column>
        <el-table-column label="满意度" width="100">
          <template #default="{ row }">
            <el-rate v-if="row.satisfaction" :model-value="row.satisfaction" disabled size="small" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="feedback" label="反馈" min-width="250" show-overflow-tooltip />
        <el-table-column label="记录时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="serviceRecords.length === 0" description="暂无服务记录" />
    </el-drawer>

    <el-drawer v-model="riskTabActive" title="履约风险评估（未来30天）" size="600px" @close="riskTabActive = false">
      <div v-if="riskAssessment">
        <el-alert
          :type="riskAssessment.can_fulfill ? 'success' : 'error'"
          :title="riskAssessment.can_fulfill ? '履约状态良好，暂无风险' : '存在履约风险，请关注'"
          show-icon
          style="margin-bottom: 20px;"
        />
        <div v-if="riskAssessment.reasons.length > 0" style="margin-bottom: 20px;">
          <h4 class="section-title">风险原因</h4>
          <el-tag
            v-for="(r, i) in riskAssessment.reasons"
            :key="i"
            type="danger"
            effect="light"
            style="margin: 4px;"
          >{{ r }}</el-tag>
        </div>
        <el-card style="margin-bottom: 20px;">
          <template #header>产能评估</template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="所需产能">{{ riskAssessment.capacity_minutes }} 分钟</el-descriptions-item>
            <el-descriptions-item label="可用产能">{{ riskAssessment.capacity_available }} 分钟</el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-card>
          <template #header>花材库存评估</template>
          <el-table :data="Object.entries(riskAssessment.stock_available).map(([k, v]: [string, any]) => ({
            id: k,
            name: v.name,
            available: v.available,
            required: riskAssessment.stock_required[k] || 0,
            valid: v.valid_available,
          }))" stripe size="small">
            <el-table-column prop="name" label="花材" />
            <el-table-column prop="required" label="需用量" width="100" />
            <el-table-column prop="available" label="总库存" width="100" />
            <el-table-column prop="valid" label="有效库存(≥2天)" width="130" />
          </el-table>
        </el-card>
      </div>
    </el-drawer>
  </div>
</template>
