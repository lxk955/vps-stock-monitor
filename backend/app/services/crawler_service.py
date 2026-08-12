import asyncio
from datetime import datetime, timezone, timedelta
import httpx
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.product import Product, PriceHistory
from app.models.subscription import Subscription
from app.models.setting import Setting
from app.services.email_service import (
    get_smtp_config,
    send_email,
    render_stock_alert_html,
    render_price_drop_alert_html
)
from app.services.aff_service import inject_affiliate_code

is_checking = False
last_check_time = None
last_check_result = {"total": 0, "restocked": 0, "price_drops": 0, "errors": 0}

async def get_system_settings_dict():
    """Retrieve all key-value settings from DB"""
    async with async_session_maker() as session:
        result = await session.execute(select(Setting))
        settings_list = result.scalars().all()
        return {s.key: s.value for s in settings_list}

async def check_single_product_stock_http(client: httpx.AsyncClient, product: Product, sem: asyncio.Semaphore) -> tuple[str, float | None]:
    """Check product stock and price via HTTP/WHMCS with concurrency control"""
    if not product.stock_check_url or product.stock_check_type == "manual":
        return product.status, product.price

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }

    async with sem:
        try:
            resp = await client.get(product.stock_check_url, headers=headers, timeout=10.0, follow_redirects=True)
            if resp.status_code == 200:
                text = resp.text
                kw = product.out_of_stock_keyword or "Out of Stock"
                
                out_indicators = [
                    kw.lower(),
                    "out of stock",
                    "outofstock",
                    "缺货",
                    "已售罄",
                    "已售完",
                    "暂时无货",
                    "currently unavailable",
                    "sold out"
                ]
                
                is_out = any(ind in text.lower() for ind in out_indicators if ind)
                new_status = "out_of_stock" if is_out else "in_stock"
                return new_status, product.price
            else:
                return product.status, product.price
        except Exception:
            return product.status, product.price

async def run_stock_check_cycle():
    """Concurrent stock check cycle with anti-harassment cooldown and dynamic AFF injection"""
    global is_checking, last_check_time, last_check_result
    if is_checking:
        return {"status": "already_running"}

    is_checking = True
    smtp_cfg = await get_smtp_config()
    site_url = smtp_cfg.get("site_url", "http://localhost:5173")
    settings_dict = await get_system_settings_dict()

    # Cooldown duration (default 30 minutes)
    cooldown_minutes = int(settings_dict.get("notification_cooldown_minutes", 30) or 30)
    cooldown_delta = timedelta(minutes=cooldown_minutes)

    restocked_count = 0
    price_drop_count = 0
    errors_count = 0
    now_utc = datetime.now(timezone.utc)

    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Product).where(Product.is_active == True)
            )
            products = result.scalars().all()
            total_products = len(products)

            if total_products == 0:
                return {"total": 0, "restocked": 0, "price_drops": 0, "errors": 0}

            sem = asyncio.Semaphore(10)
            async with httpx.AsyncClient() as client:
                tasks = [check_single_product_stock_http(client, p, sem) for p in products]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for prod, res in zip(products, results):
                    if isinstance(res, Exception):
                        errors_count += 1
                        continue

                    old_status = prod.status
                    old_price = prod.price
                    new_status, new_price = res

                    prod.last_checked_at = now_utc
                    status_changed_to_in_stock = (old_status == "out_of_stock" and new_status == "in_stock")
                    price_dropped = (new_price is not None and old_price is not None and new_price < old_price)

                    prod.status = new_status
                    if new_price is not None and new_price != old_price:
                        prod.previous_price = old_price
                        prod.price = new_price

                        history = PriceHistory(
                            product_id=prod.id,
                            price=new_price,
                            currency=prod.currency,
                            status=new_status,
                            stock_qty=prod.stock_qty,
                            recorded_at=now_utc
                        )
                        session.add(history)

                    # Dynamic AFF Injection for product snapshot
                    prod_dict = prod.to_dict()
                    if prod.affiliate_url:
                        prod_dict["affiliate_url"] = inject_affiliate_code(prod.affiliate_url, prod.provider, settings_dict)

                    # Dispatch Restock Email Alerts (with anti-flapping cooldown)
                    if status_changed_to_in_stock:
                        restocked_count += 1
                        sub_res = await session.execute(
                            select(Subscription).where(
                                Subscription.product_id == prod.id,
                                Subscription.is_active == True,
                                Subscription.notify_stock == True
                            )
                        )
                        subs = sub_res.scalars().all()
                        for sub in subs:
                            # Check Cooldown
                            if sub.last_notified_at:
                                notified_dt = sub.last_notified_at
                                if notified_dt.tzinfo is None:
                                    notified_dt = notified_dt.replace(tzinfo=timezone.utc)
                                if now_utc - notified_dt < cooldown_delta:
                                    print(f"[Cooldown Skip] Skipping restock email to {sub.email} for {prod.name} (within {cooldown_minutes}m cooldown)")
                                    continue

                            try:
                                html = render_stock_alert_html(prod_dict, sub.to_dict(), site_url)
                                await send_email(
                                    to_email=sub.email,
                                    subject=f"⚡【有货提醒】您关注的 {prod.provider} - {prod.name} 已补货！",
                                    html_content=html,
                                    alert_type="stock_restock",
                                    product_id=prod.id,
                                    product_name=prod.name,
                                    subscription_id=sub.id
                                )
                                sub.last_notified_at = now_utc
                            except Exception as em_err:
                                print(f"[Alert Error] Failed to send restock email to {sub.email}: {em_err}")

                    # Dispatch Price Drop Email Alerts (with anti-flapping cooldown)
                    if price_dropped:
                        price_drop_count += 1
                        sub_res = await session.execute(
                            select(Subscription).where(
                                Subscription.product_id == prod.id,
                                Subscription.is_active == True,
                                Subscription.notify_price_drop == True
                            )
                        )
                        subs = sub_res.scalars().all()
                        for sub in subs:
                            if sub.target_price is not None and new_price > sub.target_price:
                                continue

                            # Check Cooldown
                            if sub.last_notified_at:
                                notified_dt = sub.last_notified_at
                                if notified_dt.tzinfo is None:
                                    notified_dt = notified_dt.replace(tzinfo=timezone.utc)
                                if now_utc - notified_dt < cooldown_delta:
                                    print(f"[Cooldown Skip] Skipping price drop email to {sub.email} for {prod.name} (within {cooldown_minutes}m cooldown)")
                                    continue

                            try:
                                html = render_price_drop_alert_html(prod_dict, old_price, new_price, sub.to_dict(), site_url)
                                await send_email(
                                    to_email=sub.email,
                                    subject=f"📉【降价提醒】您关注的 {prod.provider} - {prod.name} 降价至 ${new_price}！",
                                    html_content=html,
                                    alert_type="price_drop",
                                    product_id=prod.id,
                                    product_name=prod.name,
                                    subscription_id=sub.id
                                )
                                sub.last_notified_at = now_utc
                            except Exception as em_err:
                                print(f"[Alert Error] Failed to send price drop email to {sub.email}: {em_err}")

            await session.commit()

            last_check_time = datetime.now(timezone.utc).isoformat()
            last_check_result = {
                "total": total_products,
                "restocked": restocked_count,
                "price_drops": price_drop_count,
                "errors": errors_count,
                "time": last_check_time
            }
            return last_check_result

    finally:
        is_checking = False
