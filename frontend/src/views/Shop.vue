<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ShoppingCart, InfoFilled, Clock, Calendar, Setting, ArrowLeft } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { getBouquets } from '@/api/bouquets'
import { getFlowers } from '@/api/flowers'
import { createOrder } from '@/api/orders'
import type { Bouquet, Flower, OrderCreate, OrderItemBase, CustomerCreate } from '@/types'

const router = useRouter()
const bouquets = ref<Bouquet[]>([])
const flowers = ref<Flower[]>([])
const loading = ref(false)
const selectedBouquet = ref<Bouquet | null>(null)
const detailVisible = ref(false)

const cartVisible = ref(false)
const cart = ref<{ bouquet: Bouquet; quantity: number }[]>([])

const orderVisible = ref(false)
const customerForm = ref<CustomerCreate>({
  name: '',
  phone: '',
  address: '',
})
const deliveryTime = ref('')
const remark = ref('')
const formRef = ref()

const totalAmount = computed(() => {
  return cart.value.reduce((sum, item) => sum + item.bouquet.price * item.quantity, 0)
})

const totalQuantity = computed(() => {
  return cart.value.reduce((sum, item) => sum + item.quantity, 0)
})

const fetchData = async () => {
  loading.value = true
  try {
    bouquets.value = await getBouquets()
    flowers.value = await getFlowers()
  } finally {
    loading.value = false
  }
}

const flowerName = (id: number) => {
  return flowers.value.find((f) => f.id === id)?.name || '-'
}

const flowerStock = (id: number) => {
  return flowers.value.find((f) => f.id === id)?.current_stock || 0
}

const viewDetail = (bouquet: Bouquet) => {
  selectedBouquet.value = bouquet
  detailVisible.value = true
}

const addToCart = (bouquet: Bouquet) => {
  const existing = cart.value.find((c) => c.bouquet.id === bouquet.id)
  if (existing) {
    existing.quantity++
  } else {
    cart.value.push({ bouquet, quantity: 1 })
  }
  ElMessage.success(`已添加「${bouquet.name}」到购物车`)
}

const removeFromCart = (index: number) => {
  cart.value.splice(index, 1)
}

const changeQuantity = (index: number, qty: number) => {
  if (qty <= 0) {
    removeFromCart(index)
  } else {
    cart.value[index].quantity = qty
  }
}

const openCheckout = () => {
  if (cart.value.length === 0) {
    ElMessage.warning('购物车为空')
    return
  }
  cartVisible.value = false
  orderVisible.value = true
}

const submitOrder = async () => {
  try {
    await formRef.value.validate()
    if (!deliveryTime.value) {
      ElMessage.warning('请选择期望送达时间')
      return
    }
    const items: OrderItemBase[] = cart.value.map((c) => ({
      bouquet_id: c.bouquet.id,
      quantity: c.quantity,
      unit_price: c.bouquet.price,
    }))
    const payload: OrderCreate = {
      customer: customerForm.value,
      items,
      delivery_address: customerForm.value.address,
      delivery_phone: customerForm.value.phone,
      delivery_time: new Date(deliveryTime.value).toISOString(),
      remark: remark.value,
    }
    const order = await createOrder(payload)
    ElMessage.success(`下单成功！订单号：${order.order_no}`)
    orderVisible.value = false
    cart.value = []
    customerForm.value = { name: '', phone: '', address: '' }
    deliveryTime.value = ''
    remark.value = ''
  } catch {}
}

const goToAdmin = () => {
  router.push('/admin/flowers')
}

const flowerStockStatus = (id: number) => {
  const stock = flowerStock(id)
  if (stock <= 5) return { text: '库存紧张', type: 'danger' }
  if (stock <= 20) return { text: '库存较少', type: 'warning' }
  return { text: '库存充足', type: 'success' }
}

const colorMap: Record<number, string> = {
  1: '#ff9a9e, #fad0c4',
  2: '#a18cd1, #fbc2eb',
  3: '#ffecd2, #fcb69f',
  4: '#f6d365, #fda085',
  5: '#84fab0, #8fd3f4',
}

const getBouquetColor = (id: number): string => {
  return colorMap[id] || '#c3cfe2, #f5f7fa'
}

onMounted(fetchData)
</script>

<template>
  <div class="shop-page">
    <header class="shop-header">
      <div class="header-inner">
        <div class="shop-logo">
          <span class="logo-icon">🌸</span>
          <span class="logo-title">花语轩花艺工作室</span>
        </div>
        <div class="header-actions">
          <el-button type="primary" plain @click="goToAdmin">
            管理后台
          </el-button>
          <el-button type="primary" :icon="ShoppingCart" @click="cartVisible = true">
            购物车
            <el-badge v-if="totalQuantity > 0" :value="totalQuantity" :max="99" class="cart-badge" />
          </el-button>
        </div>
      </div>
    </header>

    <section class="shop-banner">
      <div class="banner-inner">
        <h1>用心传递每一份美好</h1>
        <p>精选优质花材 · 专业花艺设计 · 新鲜配送到家</p>
      </div>
    </section>

    <main class="shop-main">
      <div class="shop-container">
        <h2 class="shop-section-title">精选花束</h2>
        <div v-loading="loading" class="bouquet-grid">
          <el-card
            v-for="bouquet in bouquets"
            :key="bouquet.id"
            class="bouquet-card"
            shadow="hover"
          >
            <div class="bouquet-image" :style="{ background: `linear-gradient(135deg, ${getBouquetColor(bouquet.id)})` }">
              <span class="bouquet-emoji">💐</span>
            </div>
            <div class="bouquet-info">
              <div class="bouquet-header">
                <h3 class="bouquet-name">{{ bouquet.name }}</h3>
                <span class="bouquet-price">¥{{ bouquet.price }}</span>
              </div>
              <p class="bouquet-meaning">{{ bouquet.meaning }}</p>
              <div class="bouquet-meta">
                <el-tag type="info" size="small" effect="plain">
                  <el-icon><Clock /></el-icon>
                  保鲜期 {{ bouquet.shelf_life_days }} 天
                </el-tag>
                <el-tag type="success" size="small" effect="plain">
                  <el-icon><Setting /></el-icon>
                  制作约 {{ bouquet.production_time_minutes }} 分钟
                </el-tag>
              </div>
              <div class="bouquet-actions">
                <el-button type="primary" plain size="small" :icon="InfoFilled" @click="viewDetail(bouquet)">
                  详情
                </el-button>
                <el-button type="primary" size="small" :icon="ShoppingCart" @click="addToCart(bouquet)">
                  加入购物车
                </el-button>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </main>

    <el-dialog v-model="detailVisible" title="花束详情" width="600px">
      <div v-if="selectedBouquet" class="bouquet-detail">
        <div class="detail-image" :style="{ background: `linear-gradient(135deg, ${getBouquetColor(selectedBouquet.id)})` }">
          <span class="detail-emoji">💐</span>
        </div>
        <h3 class="detail-name">{{ selectedBouquet.name }}</h3>
        <div class="detail-price">¥{{ selectedBouquet.price }}</div>

        <div class="detail-section">
          <div class="section-header">
            <span class="section-icon">💝</span>
            <span class="section-title">花语寓意</span>
          </div>
          <p class="section-content">{{ selectedBouquet.meaning }}</p>
        </div>

        <div class="detail-section">
          <div class="section-header">
            <span class="section-icon">📋</span>
            <span class="section-title">花束描述</span>
          </div>
          <p class="section-content">{{ selectedBouquet.description || '暂无描述' }}</p>
        </div>

        <div class="detail-section">
          <div class="section-header">
            <span class="section-icon">🌸</span>
            <span class="section-title">花材组成</span>
          </div>
          <div class="flower-composition">
            <div v-for="bf in selectedBouquet.flowers" :key="bf.id" class="flower-item">
              <span class="flower-name">{{ flowerName(bf.flower_id) }} × {{ bf.quantity }}</span>
              <el-tag
                :type="flowerStockStatus(bf.flower_id).type as any"
                size="small"
                effect="plain"
              >
                库存 {{ flowerStock(bf.flower_id) }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <div class="section-header">
            <span class="section-icon">⏰</span>
            <span class="section-title">保鲜与制作</span>
          </div>
          <div class="info-row">
            <el-icon><Clock /></el-icon>
            <span>保鲜期：{{ selectedBouquet.shelf_life_days }} 天</span>
          </div>
          <div class="info-row">
            <el-icon><Setting /></el-icon>
            <span>制作时长：约 {{ selectedBouquet.production_time_minutes }} 分钟</span>
          </div>
        </div>

        <div class="detail-section">
          <div class="section-header">
            <span class="section-icon">💡</span>
            <span class="section-title">保鲜小贴士</span>
          </div>
          <ul class="tips-list">
            <li>收到花束后，立即斜剪花茎 2-3cm，去除水下叶片</li>
            <li>使用干净的花瓶，注入 2/3 的清水</li>
            <li>每 1-2 天更换一次水，并重新剪根</li>
            <li>避免阳光直射和空调出风口</li>
            <li>远离成熟水果，减少乙烯催熟</li>
          </ul>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="selectedBouquet && addToCart(selectedBouquet)">加入购物车</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="cartVisible" title="购物车" direction="rtl" size="420px">
      <div v-if="cart.length === 0" class="empty-cart">
        <div class="empty-icon">🛒</div>
        <p>购物车还是空的</p>
        <p class="empty-tip">快去挑选心仪的花束吧</p>
      </div>
      <div v-else>
        <div v-for="(item, index) in cart" :key="item.bouquet.id" class="cart-item">
          <div class="cart-item-image" :style="{ background: `linear-gradient(135deg, ${getBouquetColor(item.bouquet.id)})` }">
            💐
          </div>
          <div class="cart-item-info">
            <div class="cart-item-name">{{ item.bouquet.name }}</div>
            <div class="cart-item-price">¥{{ item.bouquet.price }}</div>
          </div>
          <div class="cart-item-actions">
            <el-input-number
              v-model="item.quantity"
              size="small"
              :min="1"
              @change="(v) => changeQuantity(index, v)"
            />
            <el-button link type="danger" @click="removeFromCart(index)">删除</el-button>
          </div>
        </div>
        <div class="cart-summary">
          <div class="cart-total">
            <span>共计 {{ totalQuantity }} 件</span>
            <span class="total-amount">¥{{ totalAmount.toFixed(2) }}</span>
          </div>
          <el-button type="primary" size="large" style="width: 100%" @click="openCheckout">
            去结算
          </el-button>
        </div>
      </div>
    </el-drawer>

    <el-dialog v-model="orderVisible" title="确认订单" width="520px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="customerForm" label-width="90px">
        <el-form-item label="收货人" prop="name" :rules="[{ required: true, message: '请输入收货人姓名' }]">
          <el-input v-model="customerForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone" :rules="[{ required: true, message: '请输入手机号' }, { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }]">
          <el-input v-model="customerForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="收货地址" prop="address" :rules="[{ required: true, message: '请输入收货地址' }]">
          <el-input v-model="customerForm.address" type="textarea" :rows="2" placeholder="请输入详细收货地址" />
        </el-form-item>
        <el-form-item label="送达时间" prop="deliveryTime" :rules="[{ required: true, message: '请选择期望送达时间' }]">
          <el-date-picker
            v-model="deliveryTime"
            type="datetime"
            placeholder="选择期望送达时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="remark" type="textarea" :rows="2" placeholder="如有特殊需求请备注（如贺卡内容等）" />
        </el-form-item>
      </el-form>

      <el-divider />
      <div class="order-summary">
        <div v-for="item in cart" :key="item.bouquet.id" class="order-item-row">
          <span>{{ item.bouquet.name }} × {{ item.quantity }}</span>
          <span>¥{{ (item.bouquet.price * item.quantity).toFixed(2) }}</span>
        </div>
        <el-divider />
        <div class="order-total-row">
          <span>合计</span>
          <span class="order-total">¥{{ totalAmount.toFixed(2) }}</span>
        </div>
      </div>

      <template #footer>
        <el-button @click="orderVisible = false">取消</el-button>
        <el-button type="primary" @click="submitOrder">提交订单</el-button>
      </template>
    </el-dialog>

    <footer class="shop-footer">
      <p>© 2024 花语轩花艺工作室 · 用花传递爱与美好</p>
    </footer>
  </div>
</template>

<script lang="ts">
const colorMap: Record<number, string> = {
  1: '#ff9a9e, #fad0c4',
  2: '#a18cd1, #fbc2eb',
  3: '#ffecd2, #fcb69f',
  4: '#f6d365, #fda085',
  5: '#84fab0, #8fd3f4',
}

function getBouquetColor(id: number): string {
  return colorMap[id] || '#c3cfe2, #f5f7fa'
}
</script>

<style scoped>
.shop-page {
  min-height: 100vh;
  background: #faf8f5;
}

.shop-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.shop-logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 28px;
}

.logo-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #e91e63, #ff5722);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.cart-badge {
  margin-left: 4px;
}

.shop-banner {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
  padding: 60px 24px;
  text-align: center;
}

.banner-inner h1 {
  margin: 0 0 12px;
  font-size: 36px;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.banner-inner p {
  margin: 0;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.95);
}

.shop-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px;
}

.shop-section-title {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 24px;
  padding-left: 12px;
  border-left: 4px solid #e91e63;
}

.bouquet-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.bouquet-card {
  overflow: hidden;
  border-radius: 12px;
  transition: transform 0.3s ease;
}

.bouquet-card:hover {
  transform: translateY(-4px);
}

.bouquet-image {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px 8px 0 0;
  margin: -1px -1px 0;
}

.bouquet-emoji {
  font-size: 72px;
}

.bouquet-info {
  padding: 16px 4px 4px;
}

.bouquet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.bouquet-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.bouquet-price {
  font-size: 20px;
  font-weight: 700;
  color: #e91e63;
}

.bouquet-meaning {
  margin: 0 0 12px;
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bouquet-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.bouquet-actions {
  display: flex;
  gap: 8px;
}

.bouquet-detail {
  padding: 0 8px;
}

.detail-image {
  height: 220px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.detail-emoji {
  font-size: 96px;
}

.detail-name {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.detail-price {
  font-size: 28px;
  font-weight: 700;
  color: #e91e63;
  margin-bottom: 16px;
}

.detail-section {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #faf8f5;
  border-radius: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.section-icon {
  font-size: 18px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.section-content {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.flower-composition {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.flower-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flower-name {
  color: #606266;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  margin-bottom: 4px;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 1.8;
}

.empty-cart {
  text-align: center;
  padding: 80px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-tip {
  font-size: 13px;
  margin-top: 4px;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.cart-item-image {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.cart-item-info {
  flex: 1;
  min-width: 0;
}

.cart-item-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.cart-item-price {
  font-size: 16px;
  font-weight: 600;
  color: #e91e63;
}

.cart-item-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.cart-summary {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #ebeef5;
}

.cart-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.total-amount {
  font-size: 22px;
  font-weight: 700;
  color: #e91e63;
}

.order-summary {
  padding: 4px;
}

.order-item-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  color: #606266;
}

.order-total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.order-total {
  font-size: 22px;
  color: #e91e63;
}

.shop-footer {
  text-align: center;
  padding: 24px;
  color: #909399;
  font-size: 13px;
}
</style>
