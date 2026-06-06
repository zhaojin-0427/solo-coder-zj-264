from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import flowers, bouquets, orders, maintenance, deliveries, stats
from . import seed

Base.metadata.create_all(bind=engine)

app = FastAPI(title="花艺工作室订单管理与花材养护追踪系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(flowers.router, prefix="/api/flowers", tags=["花材库存"])
app.include_router(bouquets.router, prefix="/api/bouquets", tags=["花束管理"])
app.include_router(orders.router, prefix="/api/orders", tags=["订单管理"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["养护日志"])
app.include_router(deliveries.router, prefix="/api/deliveries", tags=["配送跟踪"])
app.include_router(stats.router, prefix="/api/stats", tags=["统计分析"])


@app.on_event("startup")
async def startup_event():
    from .database import SessionLocal
    db = SessionLocal()
    try:
        seed.seed_data(db)
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "花艺工作室系统运行正常"}
