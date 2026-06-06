<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Warning } from '@element-plus/icons-vue'
import { getFlowers, createFlower, updateFlower, deleteFlower } from '@/api/flowers'
import type { Flower, FlowerCreate, FlowerUpdate } from '@/types'

const flowers = ref<Flower[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const warningOnly = ref(false)

const form = ref<FlowerCreate>({
  name: '',
  meaning: '',
  shelf_life_days: 7,
  storage_temp: 4.0,
  current_stock: 0,
  unit: '支',
  purchase_date: new Date().toISOString().split('T')[0],
  warning_threshold: 2,
})

const formRef = ref()

const fetchData = async () => {
  loading.value = true
  try {
    flowers.value = await getFlowers({ warning_only: warningOnly.value })
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  editingId.value = null
  form.value = {
    name: '',
    meaning: '',
    shelf_life_days: 7,
    storage_temp: 4.0,
    current_stock: 0,
    unit: '支',
    purchase_date: new Date().toISOString().split('T')[0],
    warning_threshold: 2,
  }
  dialogVisible.value = true
}

const handleEdit = (row: Flower) => {
  isEdit.value = true
  editingId.value = row.id
  form.value = {
    name: row.name,
    meaning: row.meaning,
    shelf_life_days: row.shelf_life_days,
    storage_temp: row.storage_temp,
    current_stock: row.current_stock,
    unit: row.unit,
    purchase_date: row.purchase_date,
    warning_threshold: row.warning_threshold,
  }
  dialogVisible.value = true
}

const handleDelete = async (row: Flower) => {
  try {
    await ElMessageBox.confirm(`确定删除花材「${row.name}」吗？`, '提示', {
      type: 'warning',
    })
    await deleteFlower(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    if (isEdit.value && editingId.value) {
      await updateFlower(editingId.value, form.value as FlowerUpdate)
      ElMessage.success('更新成功')
    } else {
      await createFlower(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {}
}

const statusTagType = (row: Flower) => {
  if (row.is_warning) return 'danger'
  if ((row.days_left ?? 10) <= row.warning_threshold + 1) return 'warning'
  return 'success'
}

const statusText = (row: Flower) => {
  if (row.is_warning) return '即将过期'
  if ((row.days_left ?? 10) <= row.warning_threshold + 1) return '注意'
  return '正常'
}

onMounted(fetchData)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">花材库存</h2>
      <div style="display: flex; gap: 12px;">
        <el-switch
          v-model="warningOnly"
          active-text="仅预警"
          inactive-text="全部"
          @change="fetchData"
        />
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增花材</el-button>
      </div>
    </div>

    <el-table :data="flowers" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="name" label="花材名称" min-width="120" />
      <el-table-column prop="meaning" label="花语寓意" min-width="200" show-overflow-tooltip />
      <el-table-column label="库存" width="100">
        <template #default="{ row }">
          <span>{{ row.current_stock }} {{ row.unit }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="storage_temp" label="储存温度(℃)" width="120" />
      <el-table-column prop="shelf_life_days" label="保鲜期(天)" width="100" />
      <el-table-column prop="purchase_date" label="入库日期" width="120" />
      <el-table-column label="剩余天数" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.days_left !== undefined" :type="statusTagType(row)">
            {{ row.days_left }} 天
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row)">
            <el-icon v-if="row.is_warning"><Warning /></el-icon>
            {{ statusText(row) }}
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑花材' : '新增花材'" width="560px">
      <el-form ref="formRef" :model="form" label-width="100px">
        <el-form-item label="花材名称" prop="name" :rules="[{ required: true, message: '请输入名称' }]">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="花语寓意" prop="meaning" :rules="[{ required: true, message: '请输入花语' }]">
          <el-input v-model="form.meaning" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="当前库存" prop="current_stock">
          <el-input-number v-model="form.current_stock" :min="0" />
        </el-form-item>
        <el-form-item label="单位">
          <el-select v-model="form.unit">
            <el-option label="支" value="支" />
            <el-option label="束" value="束" />
            <el-option label="朵" value="朵" />
            <el-option label="扎" value="扎" />
          </el-select>
        </el-form-item>
        <el-form-item label="储存温度(℃)" prop="storage_temp">
          <el-input-number v-model="form.storage_temp" :step="0.5" :precision="1" />
        </el-form-item>
        <el-form-item label="保鲜期(天)" prop="shelf_life_days">
          <el-input-number v-model="form.shelf_life_days" :min="1" />
        </el-form-item>
        <el-form-item label="预警阈值(天)" prop="warning_threshold">
          <el-input-number v-model="form.warning_threshold" :min="1" />
        </el-form-item>
        <el-form-item label="入库日期" prop="purchase_date">
          <el-date-picker v-model="form.purchase_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
