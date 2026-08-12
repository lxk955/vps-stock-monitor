from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.models.subscription import Subscription
from app.models.product import Product
from app.core.security import verify_admin_token
from app.services.email_service import get_smtp_config, send_email, render_magic_link_html

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

class SubscribeRequest(BaseModel):
    product_id: int
    email: EmailStr
    notify_stock: bool = True
    notify_price_drop: bool = True
    target_price: Optional[float] = None

class UpdateSubscriptionRequest(BaseModel):
    notify_stock: Optional[bool] = None
    notify_price_drop: Optional[bool] = None
    target_price: Optional[float] = None
    is_active: Optional[bool] = None

class RequestLinkRequest(BaseModel):
    email: EmailStr

@router.post("")
async def create_subscription(data: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    """Subscribe to stock or price drop notifications for a specific product"""
    prod_res = await db.execute(select(Product).where(Product.id == data.product_id))
    product = prod_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    email_clean = data.email.strip().lower()

    sub_res = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.product))
        .where(
            Subscription.product_id == data.product_id,
            Subscription.email == email_clean
        )
    )
    existing_sub = sub_res.scalar_one_or_none()

    if existing_sub:
        existing_sub.notify_stock = data.notify_stock
        existing_sub.notify_price_drop = data.notify_price_drop
        existing_sub.target_price = data.target_price
        existing_sub.is_active = True
        await db.commit()
        await db.refresh(existing_sub)
        return {
            "message": "关注设置已成功更新！",
            "subscription": existing_sub.to_dict()
        }

    new_sub = Subscription(
        product_id=data.product_id,
        email=email_clean,
        notify_stock=data.notify_stock,
        notify_price_drop=data.notify_price_drop,
        target_price=data.target_price,
        is_active=True
    )
    db.add(new_sub)
    await db.commit()
    
    sub_res = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.product))
        .where(Subscription.id == new_sub.id)
    )
    saved_sub = sub_res.scalar_one()

    return {
        "message": "关注成功！当该产品有货或降价时，系统将第一时间向您的邮箱发送提醒通知。",
        "subscription": saved_sub.to_dict()
    }

@router.get("/my")
async def get_my_subscriptions(
    token: Optional[str] = None,
    email: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve subscriptions by user token or email"""
    if not token and not email:
        raise HTTPException(status_code=400, detail="请提供 Token 或邮箱地址")

    query = select(Subscription).options(selectinload(Subscription.product)).where(Subscription.is_active == True)

    if token:
        token_sub_res = await db.execute(select(Subscription).where(Subscription.unsubscribe_token == token.strip()))
        token_sub = token_sub_res.scalar_one_or_none()
        if not token_sub:
            raise HTTPException(status_code=404, detail="无效或已过期的访问密钥")
        query = query.where(Subscription.email == token_sub.email)
    elif email:
        query = query.where(Subscription.email == email.strip().lower())

    result = await db.execute(query.order_by(desc(Subscription.created_at)))
    subscriptions = result.scalars().all()

    return [s.to_dict() for s in subscriptions]

@router.put("/{id}")
async def update_subscription(
    id: int,
    data: UpdateSubscriptionRequest,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Update subscription settings"""
    sub_res = await db.execute(
        select(Subscription).options(selectinload(Subscription.product)).where(Subscription.id == id)
    )
    sub = sub_res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    if token and sub.unsubscribe_token != token.strip():
        raise HTTPException(status_code=403, detail="无权修改此订阅")

    if data.notify_stock is not None: sub.notify_stock = data.notify_stock
    if data.notify_price_drop is not None: sub.notify_price_drop = data.notify_price_drop
    if data.target_price is not None: sub.target_price = data.target_price
    if data.is_active is not None: sub.is_active = data.is_active

    await db.commit()
    await db.refresh(sub)
    return sub.to_dict()

@router.delete("/{id}")
async def unsubscribe(
    id: int,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Cancel subscription"""
    sub_res = await db.execute(select(Subscription).where(Subscription.id == id))
    sub = sub_res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    if token and sub.unsubscribe_token != token.strip():
        raise HTTPException(status_code=403, detail="无权取消此订阅")

    await db.delete(sub)
    await db.commit()
    return {"message": "已成功取消该产品的关注提醒"}

@router.post("/request-link")
async def request_magic_link(data: RequestLinkRequest, db: AsyncSession = Depends(get_db)):
    """Send magic link to user email to manage all their subscriptions"""
    email_clean = data.email.strip().lower()
    
    sub_res = await db.execute(
        select(Subscription).where(
            Subscription.email == email_clean,
            Subscription.is_active == True
        )
    )
    subs = sub_res.scalars().all()
    
    if not subs:
        return {"message": "如果该邮箱存在有效关注记录，管理链接已发送至您的邮箱，请注意查收。"}

    token = subs[0].unsubscribe_token
    smtp_cfg = await get_smtp_config()
    site_url = smtp_cfg.get("site_url", "http://localhost:5173")

    try:
        html = render_magic_link_html(email_clean, token, site_url, len(subs))
        await send_email(
            to_email=email_clean,
            subject="🔑【我的关注】管理您的 VPS 关注与降价通知",
            html_content=html,
            alert_type="magic_link"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"邮件发送失败: {str(e)}")

    return {"message": "管理链接已发送至您的邮箱，请前往查收邮件！"}

@router.get("/all")
async def get_all_subscriptions(
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Protected: list all subscriptions (requires admin token)"""
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.product))
        .order_by(desc(Subscription.created_at))
    )
    subs = result.scalars().all()
    return [s.to_dict() for s in subs]
