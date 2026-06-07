<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import {
  getEnterpriseCustomers,
  createEnterpriseCustomer,
  updateEnterpriseCustomer,
  deleteEnterpriseCustomer,
  getServicePointsByEnterprise,
  createServicePoint,
  updateServicePoint,
  deleteServicePoint,
} from '@/api/subscriptions'
import type {
  EnterpriseCustomer,
  EnterpriseCustomerCreate,
  EnterpriseCustomerUpdate,
  ServicePoint,
  ServicePointCreate,
  ServicePointUpdate,
} from '@/types'

const loading = ref(false)
const list = ref<EnterpriseCustomer[]>([])
const statusFilter = ref('')
const dialogVisible = ref(false)
const formType = ref<'create' | 'edit'>('create')
const currentId = ref<number | null>(null)
const form = ref<EnterpriseCustomerCreate>({
  company_name: '',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  industry: '',
  address: '',
  tax_no: '',
  invoice_title: '',
  bank_info: '',
  remark: '',
  status: 'active',
})

const pointDialogVisible = ref(false)
const pointFormType = ref<'create' | 'edit'>('create')
const currentPointId = ref<number | null>(null)
const currentEnterpriseId = ref<number | null>(null)
const pointForm = ref<ServicePointCreate>({
  enterprise_customer_id: 0,
  location_name: '',
  contact_name: '',
  contact_phone: '',
  address: '',
  floor_room: '',
  default_delivery_time: '09:00',
  access_instructions: '',
  status: 'active',
})
const servicePoints = ref<ServicePoint[]>([])
const pointDrawerVisible = ref(false)

const filteredList = computed(() => {
  if (!statusFilter.value) return list.value
  return list.value.filter((e) => e.status === statusFilter.value)
})

const statusMap: Record<string, { label: string; type: string }> = {
  active: { label: '合作中', type: 'success' },
  inactive: { label: '已停用', type: 'info' },
  paused: { label: '暂停', type: 'warning' },
}

const fetchData = async () => {
  loading.value = true
  try {
    list.value = await getEnterpriseCustomers()
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  formType.value = 'create'
  currentId.value = null
  form.value = {
    company_name: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    industry: '',
    address: '',
    tax_no: '',
    invoice_title: '',
    bank_info: '',
    remark: '',
    status: 'active',
  }
  dialogVisible.value = true
}

const openEdit = (row: EnterpriseCustomer) => {
  formType.value = 'edit'
  currentId.value = row.id
  form.value = {
    company_name: row.company_name,
    contact_person: row.contact_person,
    contact_phone: row.contact_phone,
    contact_email: row.contact_email,
    industry: row.industry,
    address: row.address,
    tax_no: row.tax_no,
    invoice_title: row.invoice_title,
    bank_info: row.bank_info,
    remark: row.remark,
    status: row.status,
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.company_name || !form.value.contact_person || !form.value.contact_phone) {
    ElMessage.warning('请填写必填项')
    return
  }
  try {
    if (formType.value === 'create') {
      await createEnterpriseCustomer(form.value)
      ElMessage.success('创建成功')
    } else if (currentId.value) {
      await updateEnterpriseCustomer(currentId.value, form.value as EnterpriseCustomerUpdate)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {}
}

const handleDelete = async (row: EnterpriseCustomer) => {
  try {
    await ElMessageBox.confirm(`确定删除企业客户「${row.company_name}」吗？相关服务点位和订阅也将被删除。`, '提示', {
      type: 'warning',
    })
    await deleteEnterpriseCustomer(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const openPoints = async (row: EnterpriseCustomer) => {
  currentEnterpriseId.value = row.id
  pointDrawerVisible.value = true
  try {
    servicePoints.value = await getServicePointsByEnterprise(row.id)
  } catch {
    servicePoints.value = []
  }
}

const openPointCreate = () => {
  pointFormType.value = 'create'
  currentPointId.value = null
  pointForm.value = {
    enterprise_customer_id: currentEnterpriseId.value || 0,
    location_name: '',
    contact_name: '',
    contact_phone: '',
    address: '',
    floor_room: '',
    default_delivery_time: '09:00',
    access_instructions: '',
    status: 'active',
  }
  pointDialogVisible.value = true
}

const openPointEdit = (p: ServicePoint) => {
  pointFormType.value = 'edit'
  currentPointId.value = p.id
  pointForm.value = {
    enterprise_customer_id: p.enterprise_customer_id,
    location_name: p.location_name,
    contact_name: p.contact_name,
    contact_phone: p.contact_phone,
    address: p.address,
    floor_room: p.floor_room,
    default_delivery_time: p.default_delivery_time,
    access_instructions: p.access_instructions,
    status: p.status,
  }
  pointDialogVisible.value = true
}

const handlePointSubmit = async () => {
  if (!pointForm.value.location_name || !pointForm.value.contact_name || !pointForm.value.contact_phone || !pointForm.value.address) {
    ElMessage.warning('请填写必填项')
    return
  }
  try {
    if (pointFormType.value === 'create') {
      await createServicePoint(pointForm.value)
      ElMessage.success('创建点位成功')
    } else if (currentPointId.value) {
      await updateServicePoint(currentPointId.value, pointForm.value as ServicePointUpdate)
      ElMessage.success('更新点位成功')
    }
    pointDialogVisible.value = false
    if (currentEnterpriseId.value) {
      servicePoints.value = await getServicePointsByEnterprise(currentEnterpriseId.value)
    }
  } catch {}
}

const handlePointDelete = async (p: ServicePoint) => {
  try {
    await ElMessageBox.confirm(`确定删除服务点位「${p.location_name}」吗？`, '提示', { type: 'warning' })
    await deleteServicePoint(p.id)
    ElMessage.success('删除成功')
    if (currentEnterpriseId.value) {
      servicePoints.value = await getServicePointsByEnterprise(currentEnterpriseId.value)
    }
  } catch {}
}

onMounted(fetchData)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">企业客户档案</h2>
      <div style="display: flex; gap: 12px;">
        <el-radio-group v-model="statusFilter" size="default">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="active">合作中</el-radio-button>
          <el-radio-button value="paused">暂停</el-radio-button>
          <el-radio-button value="inactive">已停用</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增企业客户</el-button>
      </div>
    </div>

    <el-table :data="filteredList" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="company_name" label="企业名称" min-width="200" />
      <el-table-column prop="industry" label="行业" width="120" />
      <el-table-column prop="contact_person" label="联系人" width="100" />
      <el-table-column prop="contact_phone" label="联系电话" width="140" />
      <el-table-column prop="contact_email" label="邮箱" width="180" />
      <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
      <el-table-column prop="invoice_title" label="发票抬头" width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'">
            {{ statusMap[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openPoints(row)">服务点位</el-button>
          <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="formType === 'create' ? '新增企业客户' : '编辑企业客户'" width="600px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="企业名称" required>
          <el-input v-model="form.company_name" placeholder="请输入企业名称" />
        </el-form-item>
        <el-form-item label="行业">
          <el-input v-model="form.industry" placeholder="如：酒店、写字楼、展厅" />
        </el-form-item>
        <el-form-item label="联系人" required>
          <el-input v-model="form.contact_person" />
        </el-form-item>
        <el-form-item label="联系电话" required>
          <el-input v-model="form.contact_phone" />
        </el-form-item>
        <el-form-item label="联系邮箱">
          <el-input v-model="form.contact_email" />
        </el-form-item>
        <el-form-item label="企业地址">
          <el-input v-model="form.address" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="税号">
          <el-input v-model="form.tax_no" />
        </el-form-item>
        <el-form-item label="发票抬头">
          <el-input v-model="form.invoice_title" />
        </el-form-item>
        <el-form-item label="银行信息">
          <el-input v-model="form.bank_info" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="合作中" value="active" />
            <el-option label="暂停" value="paused" />
            <el-option label="已停用" value="inactive" />
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

    <el-drawer v-model="pointDrawerVisible" title="服务点位管理" size="600px" @close="currentEnterpriseId = null">
      <div class="page-header" style="padding: 0 0 16px;">
        <h3 class="section-title">服务点位列表</h3>
        <el-button type="primary" :icon="Plus" size="default" @click="openPointCreate">新增点位</el-button>
      </div>
      <el-table :data="servicePoints" stripe style="width: 100%">
        <el-table-column prop="location_name" label="点位名称" width="160" />
        <el-table-column prop="contact_name" label="联系人" width="100" />
        <el-table-column prop="contact_phone" label="联系电话" width="130" />
        <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
        <el-table-column prop="floor_room" label="楼层/房间" width="120" />
        <el-table-column prop="default_delivery_time" label="默认配送时间" width="120" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="openPointEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="handlePointDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <el-dialog v-model="pointDialogVisible" :title="pointFormType === 'create' ? '新增服务点位' : '编辑服务点位'" width="500px">
      <el-form :model="pointForm" label-width="110px">
        <el-form-item label="点位名称" required>
          <el-input v-model="pointForm.location_name" placeholder="如：大堂前台、总经理办公室" />
        </el-form-item>
        <el-form-item label="联系人" required>
          <el-input v-model="pointForm.contact_name" />
        </el-form-item>
        <el-form-item label="联系电话" required>
          <el-input v-model="pointForm.contact_phone" />
        </el-form-item>
        <el-form-item label="配送地址" required>
          <el-input v-model="pointForm.address" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="楼层/房间">
          <el-input v-model="pointForm.floor_room" />
        </el-form-item>
        <el-form-item label="默认配送时间">
          <el-time-select v-model="pointForm.default_delivery_time" start="08:00" step="00:30" end="18:00" />
        </el-form-item>
        <el-form-item label="进入说明">
          <el-input v-model="pointForm.access_instructions" type="textarea" :rows="2" placeholder="如：需前台登记、联系某某开门" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="pointForm.status">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pointDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePointSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
</style>
