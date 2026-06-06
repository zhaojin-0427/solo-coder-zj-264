# 花艺工作室订单管理与花材养护追踪系统

基于 FastAPI + Vue 3 + TypeScript 的全栈花艺工作室管理系统。

## 功能特性

### 客户端（端口 9101）
- 在线选购花束，展示花语寓意和保鲜期说明
- 查看花材组成和当前库存
- 购物车功能与在线下单
- 保鲜养护小贴士

### 管理后台
- **花材库存**：管理花材信息，查看保鲜期剩余天数，即将过期自动预警
- **订单管理**：处理订单、查看详情、更新订单状态，自动计算最佳制作时间
- **养护日志**：记录每日花材检查情况（温度、换水、损耗），自动扣减损耗库存
- **配送跟踪**：管理配送状态、配送员信息，自动判断是否准时送达
- **统计分析**：
  - 各花材损耗率统计（图表展示）
  - 热门花束搭配排行（饼图）
  - 配送准时率统计（环形图）
  - 客户复购周期分析（折线图）
  - 即将过期花材预警提示

## 技术栈

### 后端（端口 9201）
- FastAPI 0.109
- SQLAlchemy 2.0
- SQLite 数据库
- Pydantic v2

### 前端（端口 9101）
- Vue 3 + TypeScript
- Vite 5
- Element Plus
- Pinia
- ECharts
- Axios

## 快速开始

### 方式一：使用启动脚本

macOS / Linux：
```bash
chmod +x start.sh
./start.sh
```

Windows：
```cmd
start.bat
```

### 方式二：手动启动

#### 启动后端服务
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 9201 --reload
```

#### 启动前端服务
```bash
cd frontend
npm install
npm run dev
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 客户端选购页面 | http://localhost:9101 |
| 管理后台 | http://localhost:9101/admin/flowers |
| 后端 API | http://localhost:9201 |
| Swagger 文档 | http://localhost:9201/docs |

## 系统说明

### 订单流程
1. 客户在选购页面选择花束加入购物车
2. 填写收货信息和期望送达时间后提交订单
3. 系统自动：
   - 检查并扣减对应花材库存
   - 根据花束制作时间计算最佳制作时间（送达时间 - 制作时长 - 30分钟缓冲）
   - 生成唯一订单号
   - 自动创建配送记录

### 花材养护
- 花艺师每日记录花材状态：温度、是否换水、损耗数量
- 系统自动根据入库日期和保鲜期计算剩余天数
- 剩余天数低于预警阈值时自动标记为预警状态
- 养护记录中的损耗自动从库存中扣减

### 统计分析
- **损耗率** = 累计损耗数量 / (当前库存 + 累计损耗数量)
- **配送准时率** = 准时送达订单数 / 总配送订单数
- **复购周期** = 同一客户相邻两次下单的平均间隔天数

## 项目结构

```
.
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py       # 应用入口
│   │   ├── database.py   # 数据库配置
│   │   ├── models.py     # SQLAlchemy 模型
│   │   ├── schemas.py    # Pydantic 模式
│   │   ├── seed.py       # 初始化示例数据
│   │   └── routers/      # API 路由
│   │       ├── flowers.py
│   │       ├── bouquets.py
│   │       ├── orders.py
│   │       ├── maintenance.py
│   │       ├── deliveries.py
│   │       └── stats.py
│   └── requirements.txt
├── frontend/             # Vue 3 前端
│   ├── src/
│   │   ├── api/          # API 请求封装
│   │   ├── layout/       # 后台布局组件
│   │   ├── router/       # 路由配置
│   │   ├── styles/       # 全局样式
│   │   ├── types/        # TypeScript 类型定义
│   │   ├── utils/        # 工具函数
│   │   ├── views/        # 页面组件
│   │   │   ├── Shop.vue  # 客户端选购
│   │   │   └── admin/    # 管理后台页面
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
├── start.sh              # macOS/Linux 启动脚本
└── start.bat             # Windows 启动脚本
```
