from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, func
import json

from app.core.config import settings
from app.core.database import engine, Base, async_session_maker
from app.models.product import Product, PriceHistory
from app.models.subscription import Subscription
from app.models.setting import Setting
from app.models.alert_log import AlertLog
from app.services.presets import PRESET_PRODUCTS
from app.services.crawler_service import run_stock_check_cycle
from app.core.security import get_password_hash

from app.api.products import router as products_router
from app.api.subscriptions import router as subscriptions_router
from app.api.settings import router as settings_router
from app.api.crawler import router as crawler_router
from app.api.stats import router as stats_router

scheduler = AsyncIOScheduler()

async def init_db_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        res = await session.execute(select(func.count(Product.id)))
        count = res.scalar() or 0
        if count == 0:
            print("[Init] Seeding preset VPS products...")
            for item in PRESET_PRODUCTS:
                prod = Product(
                    provider=item["provider"],
                    name=item["name"],
                    group=item.get("group", ""),
                    cpu=item.get("cpu"),
                    ram=item.get("ram"),
                    disk=item.get("disk"),
                    transfer=item.get("transfer"),
                    port_speed=item.get("port_speed"),
                    cpu_cores=item.get("cpu_cores", 1),
                    ram_mb=item.get("ram_mb", 1024),
                    disk_gb=item.get("disk_gb", 20),
                    transfer_gb=item.get("transfer_gb", 1000),
                    port_mbps=item.get("port_mbps", 1000),
                    regions_json=json.dumps(item.get("regions", []), ensure_ascii=False),
                    lines_json=json.dumps(item.get("lines", []), ensure_ascii=False),
                    status=item.get("status", "in_stock"),
                    stock_qty=item.get("stock_qty"),
                    price=item.get("price", 0.0),
                    original_price=item.get("original_price"),
                    currency=item.get("currency", "USD"),
                    price_cycle=item.get("price_cycle", "annually"),
                    affiliate_url=item.get("affiliate_url"),
                    stock_check_url=item.get("stock_check_url"),
                    stock_check_type=item.get("stock_check_type", "manual"),
                    out_of_stock_keyword=item.get("out_of_stock_keyword", "Out of Stock"),
                    recommended=item.get("recommended", False),
                    clicks=item.get("clicks", 0)
                )
                session.add(prod)
            await session.commit()

            prod_res = await session.execute(select(Product))
            for p in prod_res.scalars().all():
                h = PriceHistory(
                    product_id=p.id,
                    price=p.price,
                    currency=p.currency,
                    status=p.status,
                    stock_qty=p.stock_qty
                )
                session.add(h)
            await session.commit()

        pwd_res = await session.execute(select(Setting).where(Setting.key == "admin_password_hash"))
        if not pwd_res.scalar_one_or_none():
            default_hash = get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)
            session.add(Setting(key="admin_password_hash", value=default_hash, description="管理员后台密码Hash"))
            session.add(Setting(key="site_url", value="https://vps.220360.xyz", description="前端网站访问地址"))
            session.add(Setting(key="crawler_interval_seconds", value=str(settings.DEFAULT_CHECK_INTERVAL_SECONDS), description="库存自动检测间隔(秒)"))
            session.add(Setting(key="crawler_enabled", value="true", description="是否开启自动定时监控"))
            await session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_data()
    
    scheduler.add_job(
        run_stock_check_cycle,
        "interval",
        seconds=settings.DEFAULT_CHECK_INTERVAL_SECONDS,
        id="stock_check_job",
        replace_existing=True
    )
    scheduler.start()
    print(f"[Scheduler] Stock check scheduler started (Interval: {settings.DEFAULT_CHECK_INTERVAL_SECONDS}s)")
    
    yield
    
    scheduler.shutdown()
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router, prefix=settings.API_V1_STR)
app.include_router(subscriptions_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(crawler_router, prefix=settings.API_V1_STR)
app.include_router(stats_router, prefix=settings.API_V1_STR)

# Production Static Frontend SPA Support
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if not os.path.exists(dist_dir):
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return {"error": "API not found"}
        target_file = os.path.join(dist_dir, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "status": "running",
            "docs": "/docs",
            "api": settings.API_V1_STR
        }

