<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { getFlowers } from '@/api/flowers'
import { getBatches } from '@/api/batches'
import {
  getMaintenanceLogs,
  createMaintenanceLog,
  updateMaintenanceLog,
  deleteMaintenanceLog,
} from '@/api/maintenance'
import type { MaintenanceLog, MaintenanceLogCreate, Flower, FlowerBatch } from '@/types'

const logs = ref<MaintenanceLog[]>([])
const flowers = ref<Flower[]>([])
const batches = ref<FlowerBatch[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const flowerFilter = ref<number | undefined>(undefined)

const form = ref<MaintenanceLogCreate>({
  flower_id: 0,
  batch_id: null,
  temperature: 4.0,
  water_changed: 1,
  loss_quantity: 0,
  loss_reason: '',
  status: '良好',
  note: '',
  check_date: new Date().toISOString().split('T')[0],
})

const formRef = ref()

const currentFlowerBatches = computed(() => {
  if (!form.value.flower_id) return []
  return batches.value.filter((b) => b.flower_id === form.value.flower_id && b.remaining_quantity > 0)
})

const fetchFlowers = async () => {
  flowers.value = await getFlowers()
}

const fetchBatches = async () => {
  batches.value = await getBatches()
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = flowerFilter.value ? { flower_id: flowerFilter.value } : {}
    logs.value = await getMaintenanceLogs(params)
  } finally {
    loading.value = false
  }
}

watch(
  () => form.value.flower_id,
  () => {
    if (!isEdit.value) {
      form.value.batch_id = currentFlowerBatches.value[0]?.id ?? null
    }
  }
)

const handleAdd = () => {
  isEdit.value = false
  editingId.value = null
  const firstFlowerId = flowers.value[0]?.id || 0
  form.value = {
    flower_id: firstFlowerId,
    batch_id: null,
    temperature: 4.0,
    water_changed: 1,
    loss_quantity: 0,
    loss_reason: '',
    status: '良好',
    note: '',
    check_date: new Date().toISOString().split('T')[0],
  }
  const firstBatches = batches.value.filter((b) => b.flower_id === firstFlowerId && b.remaining_quantity > 0)
  if (firstBatches.length > 0) {
    form.value.batch_id = firstBatches[0].id
  }
  dialogVisible.value = true
}

const handleEdit = (row: MaintenanceLog) => {
  isEdit.value = true
  editingId.value = row.id
  form.value = {
    flower_id: row.flower_id,
    batch_id: row.batch_id ?? null,
    temperature: row.temperature,
    water_changed: row.water_changed,
    loss_quantity: row.loss_quantity,
    loss_reason: row.loss_reason || '',
    status: row.status,
    note: row.note || '',
    check_date: row.check_date,
  }
  dialogVisible.value = true
}

const handleDelete = async (row: MaintenanceLog) => {
  try {
    await ElMessageBox.confirm('确定删除该养护日志吗？', '提示', { type: 'warning' })
    await deleteMaintenanceLog(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    const submitData = { ...form.value }
    if (submitData.batch_id === null || submitData.batch_id === undefined) {
      delete submitData.batch_id
    }
    if (isEdit.value && editingId.value) {
      await updateMaintenanceLog(editingId.value, submitData)
      ElMessage.success('更新成功')
    } else {
      await createMaintenanceLog(submitData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
    fetchBatches()
  } catch {}
}

const flowerName = (id: number) => {
  return flowers.value.find((f) => f.id === id)?.name || '-'
}

const batchNo = (batchId?: number) => {
  if (!batchId) return '-'
  return batches.value.find((b) => b.id === batchId)?.batch_no || '-'
}

const statusTagType = (status: string) => {
  if (status === '良好') return 'success'
  if (status === '警告') return 'warning'
  return 'danger'
}

onMounted(async () => {
  await fetchFlowers()
  await fetchBatches()
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">养护日志</h2>
      <div style="display: flex; gap: 12px;">
        <el-select
          v-model="flowerFilter"
          placeholder="按花材筛选"
          clearable
          style="width: 180px"
          @change="fetchData"
        >
          <el-option
            v-for="f in flowers"
            :key="f.id"
            :label="f.name"
            :value="f.id"
          />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="handleAdd">记录养护</el-button>
      </div>
    </div>

    <el-table :data="logs" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="check_date" label="检查日期" width="120" />
      <el-table-column label="花材" width="120">
        <template #default="{ row }">
          {{ flowerName(row.flower_id) }}
        </template>
      </el-table-column>
      <el-table-column label="批次号" width="180">
        <template #default="{ row }">
          {{ batchNo(row.batch_id) }}
        </template>
      </el-table-column>
      <el-table-column label="温度(℃)" width="100">
        <template #default="{ row }">
          {{ row.temperature }}
        </template>
      </el-table-column>
      <el-table-column label="换水" width="80">
        <template #default="{ row }">
          {{ row.water_changed ? '是' : '否' }}
        </template>
      </el-table-column>
      <el-table-column label="损耗数量" width="100">
        <template #default="{ row }">
          <span :class="row.loss_quantity > 0 ? 'tag-danger' : 'tag-success'">
            {{ row.loss_quantity }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="损耗原因" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.loss_reason || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="备注" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.note || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑养护记录' : '新增养护记录'" width="520px">
      <el-form ref="formRef" :model="form" label-width="100px">
        <el-form-item label="花材" prop="flower_id" :rules="[{ required: true, message: '请选择花材' }]">
          <el-select v-model="form.flower_id" placeholder="请选择花材" style="width: 100%">
            <el-option v-for="f in flowers" :key="f.id" :label="f.name" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="批次">
          <el-select v-model="form.batch_id" placeholder="不选则扣减花材总库存" clearable style="width: 100%">
            <el-option
              v-for="b in currentFlowerBatches"
              :key="b.id"
              :label="`${b.batch_no} (剩余${b.remaining_quantity}支)`"
              :value="b.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="检查日期" prop="check_date">
          <el-date-picker v-model="form.check_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="温度(℃)" prop="temperature">
          <el-input-number v-model="form.temperature" :step="0.5" :precision="1" />
        </el-form-item>
        <el-form-item label="是否换水">
          <el-switch v-model="form.water_changed" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="损耗数量" prop="loss_quantity">
          <el-input-number v-model="form.loss_quantity" :min="0" />
        </el-form-item>
        <el-form-item label="损耗原因">
          <el-input v-model="form.loss_reason" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status">
            <el-option label="良好" value="良好" />
            <el-option label="警告" value="警告" />
            <el-option label="异常" value="异常" />
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
