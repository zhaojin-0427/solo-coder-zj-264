<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Warning } from '@element-plus/icons-vue'
import { getBatches, createBatch, updateBatch, deleteBatch } from '@/api/batches'
import { getFlowers } from '@/api/flowers'
import type { FlowerBatch, FlowerBatchCreate, FlowerBatchUpdate, Flower } from '@/types'

const batches = ref<FlowerBatch[]>([])
const flowers = ref<Flower[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const warningOnly = ref(false)
const filterFlowerId = ref<number | null>(null)
const filterStatus = ref<string>('')

const form = ref<FlowerBatchCreate>({
  flower_id: 0,
  total_quantity: 0,
  remaining_quantity: 0,
  inbound_date: new Date().toISOString().split('T')[0],
  shelf_life_days: 7,
  storage_temp: 4.0,
  supplier: '',
  status: 'in_stock',
  remark: '',
})

const formRef = ref()

const fetchData = async () => {
  loading.value = true
  try {
    const params: { flower_id?: number; status?: string; expiring_only?: boolean } = {}
    if (filterFlowerId.value) params.flower_id = filterFlowerId.value
    if (filterStatus.value) params.status = filterStatus.value
    if (warningOnly.value) params.expiring_only = true
    batches.value = await getBatches(params)
  } finally {
    loading.value = false
  }
}

const fetchFlowers = async () => {
  flowers.value = await getFlowers()
}

const handleAdd = () => {
  isEdit.value = false
  editingId.value = null
  form.value = {
    flower_id: flowers.value.length > 0 ? flowers.value[0].id : 0,
    total_quantity: 0,
    remaining_quantity: 0,
    inbound_date: new Date().toISOString().split('T')[0],
    shelf_life_days: 7,
    storage_temp: 4.0,
    supplier: '',
    status: 'in_stock',
    remark: '',
  }
  dialogVisible.value = true
}

const handleEdit = (row: FlowerBatch) => {
  isEdit.value = true
  editingId.value = row.id
  form.value = {
    flower_id: row.flower_id,
    total_quantity: row.total_quantity,
    remaining_quantity: row.remaining_quantity,
    inbound_date: row.inbound_date,
    shelf_life_days: row.shelf_life_days,
    storage_temp: row.storage_temp,
    supplier: row.supplier,
    status: row.status,
    remark: row.remark,
  }
  dialogVisible.value = true
}

const handleDelete = async (row: FlowerBatch) => {
  try {
    await ElMessageBox.confirm(`确定删除批次「${row.batch_no}」吗？`, '提示', {
      type: 'warning',
    })
    await deleteBatch(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    if (isEdit.value && editingId.value) {
      await updateBatch(editingId.value, form.value as FlowerBatchUpdate)
      ElMessage.success('更新成功')
    } else {
      await createBatch(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {}
}

watch(() => form.value.total_quantity, (newVal) => {
  if (!isEdit.value) {
    form.value.remaining_quantity = newVal
  }
})

const statusTagType = (status: string) => {
  switch (status) {
    case 'in_stock':
      return 'success'
    case 'depleted':
      return 'info'
    case 'expired':
      return 'danger'
    case 'discarded':
      return 'warning'
    default:
      return 'info'
  }
}

const statusText = (status: string) => {
  switch (status) {
    case 'in_stock':
      return '在库'
    case 'depleted':
      return '已耗尽'
    case 'expired':
      return '已过期'
    case 'discarded':
      return '已废弃'
    default:
      return status
  }
}

const daysLeftTagType = (row: FlowerBatch) => {
  if (row.is_expired) return 'danger'
  if (row.is_warning) return 'warning'
  return 'success'
}

const daysLeftText = (row: FlowerBatch) => {
  if (row.is_expired) return '已过期'
  if (row.is_warning) return '临期'
  return '正常'
}

const statusOptions = [
  { value: 'in_stock', label: '在库' },
  { value: 'depleted', label: '已耗尽' },
  { value: 'expired', label: '已过期' },
  { value: 'discarded', label: '已废弃' },
]

onMounted(() => {
  fetchFlowers()
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">批次管理</h2>
      <div style="display: flex; gap: 12px; align-items: center;">
        <el-select
          v-model="filterFlowerId"
          placeholder="选择花材"
          clearable
          style="width: 160px;"
          @change="fetchData"
        >
          <el-option
            v-for="flower in flowers"
            :key="flower.id"
            :label="flower.name"
            :value="flower.id"
          />
        </el-select>
        <el-select
          v-model="filterStatus"
          placeholder="选择状态"
          clearable
          style="width: 140px;"
          @change="fetchData"
        >
          <el-option
            v-for="opt in statusOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-switch
          v-model="warningOnly"
          active-text="仅预警"
          inactive-text="全部"
          @change="fetchData"
        />
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增批次</el-button>
      </div>
    </div>

    <el-table :data="batches" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="batch_no" label="批次号" min-width="160" />
      <el-table-column label="花材名称" min-width="120">
        <template #default="{ row }">
          <span>{{ row.flower?.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="total_quantity" label="总数量" width="100" />
      <el-table-column prop="remaining_quantity" label="剩余数量" width="100" />
      <el-table-column prop="inbound_date" label="入库日期" width="120" />
      <el-table-column label="保鲜期" width="100">
        <template #default="{ row }">
          <span>{{ row.shelf_life_days }}天</span>
        </template>
      </el-table-column>
      <el-table-column label="储存温度" width="110">
        <template #default="{ row }">
          <span>{{ row.storage_temp }}℃</span>
        </template>
      </el-table-column>
      <el-table-column prop="supplier" label="供应商" min-width="120" />
      <el-table-column label="剩余天数" width="100">
        <template #default="{ row }">
          <el-tag :type="daysLeftTagType(row)">
            <el-icon v-if="row.is_warning || row.is_expired"><Warning /></el-icon>
            {{ daysLeftText(row) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">
            {{ statusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑批次' : '新增批次'" width="560px">
      <el-form ref="formRef" :model="form" label-width="100px">
        <el-form-item label="花材" prop="flower_id" :rules="[{ required: true, message: '请选择花材' }]">
          <el-select v-model="form.flower_id" placeholder="请选择花材">
            <el-option
              v-for="flower in flowers"
              :key="flower.id"
              :label="flower.name"
              :value="flower.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="总数量" prop="total_quantity" :rules="[{ required: true, message: '请输入总数量' }]">
          <el-input-number v-model="form.total_quantity" :min="0" />
        </el-form-item>
        <el-form-item label="剩余数量" prop="remaining_quantity">
          <el-input-number v-model="form.remaining_quantity" :min="0" />
        </el-form-item>
        <el-form-item label="入库日期" prop="inbound_date" :rules="[{ required: true, message: '请选择入库日期' }]">
          <el-date-picker v-model="form.inbound_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="保鲜期(天)" prop="shelf_life_days" :rules="[{ required: true, message: '请输入保鲜期' }]">
          <el-input-number v-model="form.shelf_life_days" :min="1" />
        </el-form-item>
        <el-form-item label="储存温度(℃)" prop="storage_temp" :rules="[{ required: true, message: '请输入储存温度' }]">
          <el-input-number v-model="form.storage_temp" :step="0.5" :precision="1" />
        </el-form-item>
        <el-form-item label="供应商" prop="supplier">
          <el-input v-model="form.supplier" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status">
            <el-option
              v-for="opt in statusOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
