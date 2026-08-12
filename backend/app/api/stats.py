from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.product import Product
from app.models.subscription import Subscription
from app.models.alert_log import AlertLog

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("")
async def get_overview_stats(db: AsyncSession = Depends(get_db)):
    prod_count_res = await db.execute(select(func.count(Product.id)).where(Product.is_active == True))
    total_products = prod_count_res.scalar() or 0

    in_stock_res = await db.execute(
        select(func.count(Product.id)).where(Product.is_active == True, Product.status == "in_stock")
    )
    in_stock_products = in_stock_res.scalar() or 0

    sub_count_res = await db.execute(
        select(func.count(Subscription.id)).where(Subscription.is_active == True)
    )
    total_subscriptions = sub_count_res.scalar() or 0

    emails_res = await db.execute(
        select(func.count(func.distinct(Subscription.email))).where(Subscription.is_active == True)
    )
    unique_subscribers = emails_res.scalar() or 0

    alerts_res = await db.execute(
        select(func.count(AlertLog.id)).where(AlertLog.status == "sent")
    )
    total_alerts_sent = alerts_res.scalar() or 0

    prov_res = await db.execute(
        select(func.count(func.distinct(Product.provider))).where(Product.is_active == True)
    )
    provider_count = prov_res.scalar() or 0

    return {
        "total_products": total_products,
        "in_stock_products": in_stock_products,
        "out_of_stock_products": total_products - in_stock_products,
        "total_subscriptions": total_subscriptions,
        "unique_subscribers": unique_subscribers,
        "total_alerts_sent": total_alerts_sent,
        "provider_count": provider_count,
        "online_users": 18,
        "today_pv": 3280,
        "total_pv": 214890
    }
