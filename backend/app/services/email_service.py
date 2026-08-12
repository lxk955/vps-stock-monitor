import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, formataddr
import asyncio
from datetime import datetime, timezone
import httpx
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.setting import Setting
from app.models.alert_log import AlertLog

async def get_smtp_config():
    """Retrieve SMTP & Resend configuration from settings database"""
    async with async_session_maker() as session:
        result = await session.execute(select(Setting))
        settings_list = result.scalars().all()
        config = {s.key: s.value for s in settings_list}
        return {
            "provider_type": config.get("email_provider_type", "smtp"), # "smtp" or "resend"
            "resend_api_key": config.get("resend_api_key", ""),
            "host": config.get("smtp_host", ""),
            "port": int(config.get("smtp_port", 465) or 465),
            "user": config.get("smtp_user", ""),
            "pass": config.get("smtp_pass", ""),
            "from_name": config.get("smtp_from_name", "VPS 实时库存与降价监控"),
            "from_email": config.get("smtp_from_email", "") or config.get("smtp_user", ""),
            "ssl": config.get("smtp_ssl", "true").lower() in ("true", "1", "yes"),
            "tls": config.get("smtp_tls", "false").lower() in ("true", "1", "yes"),
            "site_url": config.get("site_url", "https://vps.220360.xyz")
        }

async def _send_resend_http_email(api_key: str, from_name: str, from_email: str, to_email: str, subject: str, html_content: str):
    """Send email via Resend HTTP REST API over standard HTTPS port 443 (never blocked by cloud PaaS)"""
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    sender = f"{from_name} <{from_email}>" if from_name and from_email else (from_email or "onboarding@resend.dev")
    if "@" not in sender:
        sender = "onboarding@resend.dev"

    payload = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=12.0)
        if resp.status_code >= 400:
            err_text = resp.text
            try:
                err_json = resp.json()
                err_text = err_json.get("message", err_text)
            except Exception:
                pass
            raise ValueError(f"Resend HTTP API 发信失败 ({resp.status_code}): {err_text}")
        return resp.json()

def _send_sync_smtp_email(smtp_cfg: dict, to_email: str, subject: str, html_content: str, text_content: str = ""):
    """Synchronous SMTP email sender called inside asyncio.to_thread with IPv4 fallback"""
    host = (smtp_cfg.get("host") or "").strip()
    user = (smtp_cfg.get("user") or "").strip()
    password = (smtp_cfg.get("pass") or "").strip()
    port = int(smtp_cfg.get("port") or 465)

    if not host or not user:
        raise ValueError("SMTP 服务器或发件人账号尚未填写完整。")

    msg = MIMEMultipart("alternative")
    from_name = smtp_cfg.get("from_name", "VPS 监控")
    from_email = smtp_cfg.get("from_email") or user
    msg["From"] = formataddr((from_name, from_email))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)

    if text_content:
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    use_ssl = smtp_cfg.get("ssl", True)
    use_tls = smtp_cfg.get("tls", False)

    try:
        if (use_ssl and port in (465, 994)) or (port == 465):
            server = smtplib.SMTP_SSL(host, port, timeout=12)
        else:
            server = smtplib.SMTP(host, port, timeout=12)
            if use_tls or port == 587:
                server.starttls()

        if user and password:
            server.login(user, password)

        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
    except smtplib.SMTPAuthenticationError as e:
        raise ValueError(f"SMTP 身份验证失败 (535)：账号或授权码/密码错误，请检查是否填写了正确的邮箱授权码 (而非邮箱登录密码)。原错误: {e}")
    except smtplib.SMTPConnectError as e:
        raise ValueError(f"SMTP 服务器连接失败：无法连接到 {host}:{port}，请检查服务器地址和端口是否正确。原错误: {e}")
    except (TimeoutError, OSError) as e:
        err_str = str(e)
        if "101" in err_str or "unreachable" in err_str.lower():
            raise ValueError(f"网络不可达 [Errno 101]：Render.com 免费容器限制了出站 SMTP 端口 (25/465/587)。推荐在后台切换为【Resend API (HTTP 443 永不封锁)】或部署在自有 VPS 上发信。原错误: {e}")
        raise ValueError(f"SMTP 连接超时或不可达：{err_str}")
    except Exception as e:
        raise ValueError(f"发信失败: {str(e)}")

async def send_email(to_email: str, subject: str, html_content: str, alert_type: str = "general", product_id: int = None, product_name: str = None, subscription_id: int = None, custom_smtp_cfg: dict = None):
    """Async unified email dispatcher supporting both Resend HTTP API and Standard SMTP"""
    smtp_cfg = custom_smtp_cfg or await get_smtp_config()
    status = "sent"
    error_msg = None

    resend_key = smtp_cfg.get("resend_api_key", "").strip()
    provider_type = smtp_cfg.get("provider_type", "smtp")

    try:
        if (provider_type == "resend" or resend_key.startswith("re_")) and resend_key:
            from_name = smtp_cfg.get("from_name", "VPS 实时监控")
            from_email = smtp_cfg.get("from_email", "onboarding@resend.dev")
            await _send_resend_http_email(resend_key, from_name, from_email, to_email, subject, html_content)
        else:
            await asyncio.to_thread(_send_sync_smtp_email, smtp_cfg, to_email, subject, html_content)
    except Exception as e:
        status = "failed"
        error_msg = str(e)
        raise e
    finally:
        async with async_session_maker() as session:
            try:
                log = AlertLog(
                    subscription_id=subscription_id,
                    product_id=product_id,
                    email=to_email,
                    product_name=product_name,
                    alert_type=alert_type,
                    subject=subject,
                    status=status,
                    error_message=error_msg,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(log)
                await session.commit()
            except Exception as log_err:
                print(f"[Log Error] Failed to write alert log: {log_err}")
                await session.commit()
            except Exception:
                pass

def render_stock_alert_html(product: dict, subscription: dict, site_url: str = "https://vps.220360.xyz") -> str:
    """Render stock restock alert email template"""
    unsubscribe_url = f"{site_url}/my-subscriptions?token={subscription.get('unsubscribe_token', '')}&unsub={subscription.get('id', '')}"
    manage_url = f"{site_url}/my-subscriptions?token={subscription.get('unsubscribe_token', '')}"
    buy_url = product.get('affiliate_url') or site_url

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
        <div style="max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 28px 24px; text-align: center; color: #ffffff;">
                <h1 style="margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.5px;">⚡ 补货通知：心仪机型已上架！</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 13px;">您关注的 VPS 刚刚检测到已恢复有货状态，抢购从速！</p>
            </div>
            
            <div style="padding: 24px;">
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="background: #e2e8f0; color: #334155; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">{product.get('provider', '')}</span>
                        <span style="color: #10b981; font-weight: 700; font-size: 12px;">🟢 现已现货</span>
                    </div>
                    <h2 style="margin: 0 0 8px 0; font-size: 17px; color: #0f172a;">{product.get('name', '')}</h2>
                    <div style="font-size: 20px; font-weight: 800; color: #2563eb; margin-bottom: 12px;">
                        ${product.get('price', 0)} <span style="font-size: 12px; color: #64748b; font-weight: 400;">{product.get('currency', 'USD')} / {product.get('price_cycle', '年付')}</span>
                    </div>
                    <div style="background: #ffffff; border: 1px solid #edf2f7; border-radius: 8px; padding: 10px; font-size: 12px; color: #475569; line-height: 1.6;">
                        <strong>配置规格：</strong> {product.get('cpu', '—')} · {product.get('ram', '—')} · {product.get('disk', '—')} · {product.get('transfer', '—')} · {product.get('port_speed', '—')}
                    </div>
                </div>

                <div style="text-align: center; margin: 24px 0;">
                    <a href="{buy_url}" target="_blank" style="display: inline-block; background: #2563eb; color: #ffffff; text-decoration: none; padding: 12px 32px; border-radius: 10px; font-weight: 700; font-size: 14px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);">👉 立即前往官方抢购</a>
                </div>

                <div style="border-top: 1px solid #f1f5f9; padding-top: 16px; font-size: 11px; color: #94a3b8; line-height: 1.5; text-align: center;">
                    <p style="margin: 0 0 6px 0;">您收到此邮件是因为在 <a href="{site_url}" style="color: #64748b; text-decoration: none;">VPS 实时监控平台</a> 订阅了该产品的补货提醒。</p>
                    <p style="margin: 0;">
                        <a href="{manage_url}" style="color: #2563eb; text-decoration: none; margin-right: 12px;">管理所有关注</a>
                        <a href="{unsubscribe_url}" style="color: #ef4444; text-decoration: none;">取消此产品关注</a>
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def render_price_drop_alert_html(product: dict, old_price: float, new_price: float, subscription: dict, site_url: str = "https://vps.220360.xyz") -> str:
    """Render price drop alert email template"""
    unsubscribe_url = f"{site_url}/my-subscriptions?token={subscription.get('unsubscribe_token', '')}&unsub={subscription.get('id', '')}"
    manage_url = f"{site_url}/my-subscriptions?token={subscription.get('unsubscribe_token', '')}"
    buy_url = product.get('affiliate_url') or site_url

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
        <div style="max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <div style="background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%); padding: 28px 24px; text-align: center; color: #ffffff;">
                <h1 style="margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.5px;">📉 降价通知：特惠降至 ${new_price}！</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 13px;">您关注的 VPS 机型官方价格已下调，手慢无！</p>
            </div>
            
            <div style="padding: 24px;">
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="background: #e2e8f0; color: #334155; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">{product.get('provider', '')}</span>
                        <span style="color: #e11d48; font-weight: 700; font-size: 12px;">📉 降价 ${round(old_price - new_price, 2) if old_price else 0}</span>
                    </div>
                    <h2 style="margin: 0 0 8px 0; font-size: 17px; color: #0f172a;">{product.get('name', '')}</h2>
                    <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 12px;">
                        <span style="font-size: 24px; font-weight: 800; color: #e11d48;">${new_price}</span>
                        <span style="font-size: 14px; color: #94a3b8; text-decoration: line-through;">${old_price}</span>
                        <span style="font-size: 12px; color: #64748b;">{product.get('currency', 'USD')} / {product.get('price_cycle', '年付')}</span>
                    </div>
                    <div style="background: #ffffff; border: 1px solid #edf2f7; border-radius: 8px; padding: 10px; font-size: 12px; color: #475569; line-height: 1.6;">
                        <strong>配置规格：</strong> {product.get('cpu', '—')} · {product.get('ram', '—')} · {product.get('disk', '—')} · {product.get('transfer', '—')} · {product.get('port_speed', '—')}
                    </div>
                </div>

                <div style="text-align: center; margin: 24px 0;">
                    <a href="{buy_url}" target="_blank" style="display: inline-block; background: #e11d48; color: #ffffff; text-decoration: none; padding: 12px 32px; border-radius: 10px; font-weight: 700; font-size: 14px; box-shadow: 0 4px 6px -1px rgba(225, 29, 72, 0.2);">👉 立即前往官方抢购</a>
                </div>

                <div style="border-top: 1px solid #f1f5f9; padding-top: 16px; font-size: 11px; color: #94a3b8; line-height: 1.5; text-align: center;">
                    <p style="margin: 0 0 6px 0;">您收到此邮件是因为在 <a href="{site_url}" style="color: #64748b; text-decoration: none;">VPS 实时监控平台</a> 订阅了该产品的降价提醒。</p>
                    <p style="margin: 0;">
                        <a href="{manage_url}" style="color: #2563eb; text-decoration: none; margin-right: 12px;">管理所有关注</a>
                        <a href="{unsubscribe_url}" style="color: #ef4444; text-decoration: none;">取消此产品关注</a>
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def render_magic_link_html(email: str, token: str, site_url: str = "https://vps.220360.xyz", count: int = 1) -> str:
    """Render magic link email template for managing watchlist"""
    manage_url = f"{site_url}/my-subscriptions?token={token}"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
        <div style="max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <div style="background: #2563eb; padding: 24px; text-align: center; color: #ffffff;">
                <h1 style="margin: 0; font-size: 20px; font-weight: 700;">🔑 您的 VPS 关注管理专属链接</h1>
            </div>
            
            <div style="padding: 24px;">
                <p style="font-size: 14px; color: #334155; line-height: 1.6; margin-top: 0;">
                    您好！您使用邮箱 <strong>{email}</strong> 当前共关注了 <strong>{count}</strong> 款 VPS 机型。
                </p>
                <p style="font-size: 13px; color: #64748b; line-height: 1.6;">
                    点击下方按钮，即可在任何设备上免密查看、修改或取消您关注的所有 VPS 产品：
                </p>

                <div style="text-align: center; margin: 28px 0;">
                    <a href="{manage_url}" target="_blank" style="display: inline-block; background: #2563eb; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 10px; font-weight: 700; font-size: 14px;">👉 进入我的关注管理中心</a>
                </div>

                <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 10px; font-size: 11px; color: #64748b; word-break: break-all;">
                    备用直达链接: <br>{manage_url}
                </div>

                <div style="border-top: 1px solid #f1f5f9; margin-top: 20px; padding-top: 14px; font-size: 11px; color: #94a3b8; text-align: center;">
                    如果您未请求此邮件，请直接忽略。该链接长期有效且仅限您个人访问。
                </div>
            </div>
        </div>
    </body>
    </html>
    """
