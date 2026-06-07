<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts/core'
import {
  BarChart,
  LineChart,
  PieChart,
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { use } from 'echarts/core'
import VChart from 'vue-echarts'
import { Warning } from '@element-plus/icons-vue'
import { getStats } from '@/api/stats'
import type { StatsResponse } from '@/types'

use([
  BarChart,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  CanvasRenderer,
])

const stats = ref<StatsResponse | null>(null)
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    stats.value = await getStats()
  } finally {
    loading.value = false
  }
}

const lossRateOption = computed(() => {
  if (!stats.value) return {}
  const data = stats.value.flower_loss_rates.slice(0, 8)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.flower_name),
      axisLabel: { rotate: 30 },
    },
    yAxis: {
      type: 'value',
      name: '损耗率(%)',
    },
    series: [
      {
        type: 'bar',
        data: data.map((d) => d.loss_rate),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#f56c6c' },
            { offset: 1, color: '#e6a23c' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        label: { show: true, position: 'top', formatter: '{c}%' },
      },
    ],
  }
})

const popularBouquetOption = computed(() => {
  if (!stats.value) return {}
  const data = stats.value.popular_bouquets
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{d}%' },
        data: data.map((d) => ({ name: d.bouquet_name, value: d.total_quantity })),
        color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#8e44ad'],
      },
    ],
  }
})

const deliveryOption = computed(() => {
  if (!stats.value) return {}
  const s = stats.value.delivery_stats
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [
      {
        type: 'pie',
        radius: ['50%', '75%'],
        label: {
          show: true,
          position: 'center',
          formatter: `准时率\n${s.on_time_rate}%`,
          fontSize: 18,
          fontWeight: 'bold',
        },
        data: [
          { value: s.on_time_deliveries, name: '准时送达', itemStyle: { color: '#67c23a' } },
          { value: s.total_deliveries - s.on_time_deliveries, name: '延迟送达', itemStyle: { color: '#f56c6c' } },
        ],
      },
    ],
  }
})

const repurchaseOption = computed(() => {
  if (!stats.value) return {}
  const data = stats.value.repurchase_cycles
  return {
    tooltip: { trigger: 'axis', formatter: (params: any) => `${params[0].name}<br/>平均复购周期: ${params[0].value} 天` },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.customer_name),
      axisLabel: { rotate: 0 },
    },
    yAxis: {
      type: 'value',
      name: '天数',
    },
    series: [
      {
        type: 'line',
        data: data.map((d) => d.avg_days_between_orders),
        smooth: true,
        symbol: 'circle',
        symbolSize: 10,
        lineStyle: { width: 3, color: '#409eff' },
        itemStyle: { color: '#409eff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.3)' },
            { offset: 1, color: 'rgba(64,158,255,0.05)' },
          ]),
        },
      },
    ],
  }
})

const batchLossRateOption = computed(() => {
  if (!stats.value) return {}
  const data = stats.value.batch_loss_rates.slice(0, 8)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.batch_no),
      axisLabel: { rotate: 30 },
    },
    yAxis: {
      type: 'value',
      name: '损耗率(%)',
    },
    series: [
      {
        type: 'bar',
        data: data.map((d) => d.loss_rate),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#f56c6c' },
            { offset: 1, color: '#e6a23c' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        label: { show: true, position: 'top', formatter: '{c}%' },
      },
    ],
  }
})

const batchExpiryOption = computed(() => {
  if (!stats.value) return {}
  const s = stats.value.batch_expiry
  const normal = s.total_batches - s.expiring_batches - s.expired_batches
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{d}%' },
        data: [
          { name: '正常批次', value: normal },
          { name: '临期批次', value: s.expiring_batches },
          { name: '已过期批次', value: s.expired_batches },
        ],
        color: ['#67c23a', '#e6a23c', '#f56c6c'],
      },
    ],
  }
})

const capacityLoadOption = computed(() => {
  if (!stats.value) return {}
  const data = stats.value.capacity_load
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = params[0]
        return `${p.name}<br/>负载比例: ${p.value}%<br/>订单数: ${data[p.dataIndex].order_count}<br/>总工时: ${data[p.dataIndex].total_minutes} 分钟`
      },
    },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: data.map((d) => {
        const dt = new Date(d.date)
        return `${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
      }),
      axisLabel: { rotate: 0 },
    },
    yAxis: {
      type: 'value',
      name: '负载比例(%)',
      max: 150,
    },
    series: [
      {
        type: 'bar',
        data: data.map((d) => ({
          value: d.load_ratio,
          itemStyle: {
            color: d.load_ratio > 100 ? '#f56c6c' : '#409eff',
            borderRadius: [4, 4, 0, 0],
          },
        })),
        label: { show: true, position: 'top', formatter: '{c}%' },
      },
    ],
  }
})

onMounted(fetchData)
</script>

<template>
  <div class="page-container" v-loading="loading">
    <h2 class="page-title" style="margin-bottom: 20px;">统计分析</h2>

    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-card-title">总配送次数</div>
          <div class="stat-card-value" style="color: #409eff">
            {{ stats?.delivery_stats.total_deliveries || 0 }}
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-card-title">准时送达</div>
          <div class="stat-card-value" style="color: #67c23a">
            {{ stats?.delivery_stats.on_time_deliveries || 0 }}
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-card-title">配送准时率</div>
          <div class="stat-card-value" style="color: #e6a23c">
            {{ stats?.delivery_stats.on_time_rate || 0 }}%
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-card-title">预警花材数</div>
          <div class="stat-card-value" style="color: #f56c6c">
            {{ stats?.warning_flowers.length || 0 }}
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-card-title">批次总数</div>
          <div class="stat-card-value" style="color: #909399">
            {{ stats?.batch_expiry.total_batches || 0 }}
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-card-title">临期批次</div>
          <div class="stat-card-value" style="color: #e6a23c">
            {{ stats?.batch_expiry.expiring_batches || 0 }}
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-card-title">已过期批次</div>
          <div class="stat-card-value" style="color: #f56c6c">
            {{ stats?.batch_expiry.expired_batches || 0 }}
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-card-title">履约风险订单数</div>
          <div class="stat-card-value" style="color: #f56c6c">
            {{ stats?.fulfillment_risk.risk_orders || 0 }}
          </div>
        </div>
      </el-col>
    </el-row>

    <el-alert
      v-if="stats && stats.warning_flowers.length > 0"
      type="warning"
      show-icon
      style="margin-bottom: 20px;"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 8px;">
          <el-icon><Warning /></el-icon>
          <span>花材保鲜预警：以下花材即将过期</span>
        </div>
      </template>
      <template #default>
        <el-tag
          v-for="f in stats.warning_flowers"
          :key="f.id"
          type="danger"
          style="margin-right: 8px; margin-top: 8px;"
        >
          {{ f.name }}（剩余 {{ f.days_left }} 天）
        </el-tag>
      </template>
    </el-alert>

    <el-alert
      v-if="stats && stats.fulfillment_risk.risk_orders > 0"
      type="error"
      show-icon
      style="margin-bottom: 20px;"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 8px;">
          <el-icon><Warning /></el-icon>
          <span>订单履约风险：共有 {{ stats.fulfillment_risk.risk_orders }} 个订单存在履约风险</span>
        </div>
      </template>
      <template #default>
        <div style="margin-top: 8px;">
          <div
            v-for="detail in stats.fulfillment_risk.risk_details"
            :key="detail.order_id"
            style="padding: 8px 0; border-bottom: 1px dashed #e4e7ed;"
          >
            <div style="font-weight: 600; margin-bottom: 4px;">
              订单号：{{ detail.order_no }}
              <span style="font-weight: normal; color: #909399; margin-left: 12px;">
                配送时间：{{ detail.delivery_time }}
              </span>
            </div>
            <div>
              <el-tag
                v-for="(reason, idx) in detail.reasons"
                :key="idx"
                type="danger"
                effect="light"
                style="margin-right: 6px;"
              >
                {{ reason }}
              </el-tag>
            </div>
          </div>
        </div>
      </template>
    </el-alert>

    <el-alert
      v-else-if="stats && stats.fulfillment_risk.risk_orders === 0"
      type="success"
      show-icon
      style="margin-bottom: 20px;"
    >
      <template #title>
        <span>订单履约状态正常，暂无风险订单</span>
      </template>
    </el-alert>

    <el-row :gutter="20">
      <el-col :span="12" style="margin-bottom: 20px;">
        <div class="stat-card">
          <h4 class="section-title">各花材损耗率</h4>
          <v-chart :option="lossRateOption" style="height: 300px;" autoresize />
        </div>
      </el-col>
      <el-col :span="12" style="margin-bottom: 20px;">
        <div class="stat-card">
          <h4 class="section-title">热门花束搭配</h4>
          <v-chart :option="popularBouquetOption" style="height: 300px;" autoresize />
        </div>
      </el-col>
      <el-col :span="12" style="margin-bottom: 20px;">
        <div class="stat-card">
          <h4 class="section-title">配送准时率</h4>
          <v-chart :option="deliveryOption" style="height: 300px;" autoresize />
        </div>
      </el-col>
      <el-col :span="12" style="margin-bottom: 20px;">
        <div class="stat-card">
          <h4 class="section-title">客户复购周期（天）</h4>
          <v-chart :option="repurchaseOption" style="height: 300px;" autoresize />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12" style="margin-bottom: 20px;">
        <div class="stat-card">
          <h4 class="section-title">批次损耗率排行</h4>
          <v-chart :option="batchLossRateOption" style="height: 300px;" autoresize />
        </div>
      </el-col>
      <el-col :span="12" style="margin-bottom: 20px;">
        <div class="stat-card">
          <h4 class="section-title">批次临期/过期占比</h4>
          <v-chart :option="batchExpiryOption" style="height: 300px;" autoresize />
        </div>
      </el-col>
      <el-col :span="24" style="margin-bottom: 20px;">
        <div class="stat-card">
          <h4 class="section-title">未来三天产能负载</h4>
          <v-chart :option="capacityLoadOption" style="height: 300px;" autoresize />
        </div>
      </el-col>
    </el-row>

    <div class="stat-card" v-if="stats">
      <h4 class="section-title">花材损耗详情</h4>
      <el-table :data="stats.flower_loss_rates" stripe>
        <el-table-column prop="flower_name" label="花材名称" />
        <el-table-column prop="total_stock" label="总库存(累计)" width="150" />
        <el-table-column prop="total_loss" label="总损耗量" width="120" />
        <el-table-column label="损耗率" width="150">
          <template #default="{ row }">
            <el-progress
              :percentage="row.loss_rate"
              :color="row.loss_rate > 20 ? '#f56c6c' : row.loss_rate > 10 ? '#e6a23c' : '#67c23a'"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="stat-card" style="margin-top: 20px;" v-if="stats">
      <h4 class="section-title">批次损耗详情</h4>
      <el-table :data="stats.batch_loss_rates" stripe>
        <el-table-column prop="batch_no" label="批次号" />
        <el-table-column prop="flower_name" label="花材名称" />
        <el-table-column prop="total_quantity" label="总数量" width="120" />
        <el-table-column prop="loss_quantity" label="损耗量" width="120" />
        <el-table-column label="损耗率" width="180">
          <template #default="{ row }">
            <el-progress
              :percentage="row.loss_rate"
              :color="row.loss_rate > 20 ? '#f56c6c' : row.loss_rate > 10 ? '#e6a23c' : '#67c23a'"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="stat-card" style="margin-top: 20px;" v-if="stats">
      <h4 class="section-title">热门花束销量排行</h4>
      <el-table :data="stats.popular_bouquets" stripe>
        <el-table-column label="排名" width="80">
          <template #default="{ $index }">
            <el-tag
              :type="$index === 0 ? 'danger' : $index === 1 ? 'warning' : $index === 2 ? 'success' : 'info'"
            >
              {{ $index + 1 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="bouquet_name" label="花束名称" />
        <el-table-column prop="order_count" label="订单数" width="120" />
        <el-table-column prop="total_quantity" label="总销量" width="120" />
      </el-table>
    </div>

    <div class="stat-card" style="margin-top: 20px;" v-if="stats">
      <h4 class="section-title">客户复购分析</h4>
      <el-table :data="stats.repurchase_cycles" stripe>
        <el-table-column prop="customer_name" label="客户姓名" />
        <el-table-column prop="order_count" label="订单数" width="100" />
        <el-table-column label="平均复购周期(天)" width="180">
          <template #default="{ row }">
            <el-tag :type="row.avg_days_between_orders <= 7 ? 'success' : 'warning'">
              {{ row.avg_days_between_orders }} 天
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
