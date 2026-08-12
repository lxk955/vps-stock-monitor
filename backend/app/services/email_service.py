import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, formataddr
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.setting import Setting
from app.models.alert_log import AlertLog

async def get_smtp_config():
    """Retrieve SMTP configuration from settings database"""
    async with async_session_maker() as session:
        result = await session.execute(select(Setting))
        settings_list = result.scalars().all()
        config = {s.key: s.value for s in settings_list}
        return {
            "host": config.get("smtp_host", ""),
            "port": int(config.get("smtp_port", 465) or 465),
            "user": config.get("smtp_user", ""),
            "pass": config.get("smtp_pass", ""),
            "from_name": config.get("smtp_from_name", "VPS 实时库存与降价监控"),
            "from_email": config.get("smtp_from_email", "") or config.get("smtp_user", ""),
            "ssl": config.get("smtp_ssl", "true").lower() in ("true", "1", "yes"),
            "tls": config.get("smtp_tls", "false").lower() in ("true", "1", "yes"),
            "site_url": config.get("site_url", "http://localhost:5173")
        }

def _send_sync_email(smtp_cfg: dict, to_email: str, subject: str, html_content: str, text_content: str = ""):
    """Synchronous SMTP email sender called inside asyncio.to_thread"""
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
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
            if use_tls or port == 587:
                server.starttls()

        if user and password:
            server.login(user, password)

        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
    except smtplib.SMTPAuthenticationError as e:
        raise ValueError(f"SMTP 身份验证失败 (535)：账号或授权码/密码错误，请检查是否填写了正确的邮箱授权码 (而非邮箱登录密码)。原错误: {e}")
    except smtplib.SMTPConnectError as e:
        raise ValueError(f"SMTP 服务器连接失败：无法连接到 {host}:{port}，请检查服务器地址和端口是否正确，或是否需要开启/关闭 SSL。原错误: {e}")
    except TimeoutError:
        raise ValueError(f"SMTP 连接超时：连接 {host}:{port} 超时，请检查网络或端口是否被云平台防火墙限制。")
    except Exception as e:
        raise ValueError(f"发信失败: {str(e)}")

async def send_email(to_email: str, subject: str, html_content: str, alert_type: str = "general", product_id: int = None, product_name: str = None, subscription_id: int = None, custom_smtp_cfg: dict = None):
    """Async wrapper to send email and write audit log"""
    smtp_cfg = custom_smtp_cfg or await get_smtp_config()
    status = "sent"
    error_msg = None

    try:
        await asyncio.to_thread(_send_sync_email, smtp_cfg, to_email, subject, html_content)
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

def render_stock_alert_html(product: dict, sub: dict, site_url: str) -> str:
    """Generate HTML email template for Back-in-Stock alerts"""
    buy_url = product.get("affiliate_url") or "#"
    unsub_url = f"{site_url}/my-subscriptions?token={sub.get('unsubscribe_token')}"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #10b981, #059669); color: #ffffff; padding: 24px; text-align: center; }}
            .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 700; }}
            .header p {{ margin: 0; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 24px; }}
            .product-card {{ background: #f1f5f9; border-radius: 8px; padding: 18px; margin-bottom: 20px; border-left: 4px solid #10b981; }}
            .product-title {{ font-size: 17px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
            .provider-badge {{ display: inline-block; background: #e2e8f0; color: #475569; font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 600; margin-bottom: 12px; }}
            .spec-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px; color: #334155; margin-bottom: 14px; }}
            .price-box {{ font-size: 20px; font-weight: 800; color: #059669; margin-top: 10px; }}
            .price-box small {{ font-size: 13px; font-weight: normal; color: #64748b; }}
            .btn-action {{ display: block; text-align: center; background: #10b981; color: #ffffff !important; text-decoration: none; font-weight: 700; padding: 14px 20px; border-radius: 8px; font-size: 16px; margin: 24px 0 16px 0; }}
            .footer {{ border-top: 1px solid #e2e8f0; padding: 16px 24px; font-size: 12px; color: #94a3b8; text-align: center; }}
            .footer a {{ color: #64748b; text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ 您关注的 VPS 已补货上架！</h1>
                <p>实时库存监控系统第一时间提醒您</p>
            </div>
            <div class="content">
                <div class="product-card">
                    <span class="provider-badge">{product.get('provider')}</span>
                    <div class="product-title">{product.get('name')}</div>
                    <div class="spec-grid">
                        <div>🖥️ <strong>CPU:</strong> {product.get('cpu') or '—'}</div>
                        <div>🧠 <strong>内存:</strong> {product.get('ram') or '—'}</div>
                        <div>💾 <strong>硬盘:</strong> {product.get('disk') or '—'}</div>
                        <div>🌐 <strong>流量:</strong> {product.get('transfer') or '—'}</div>
                        <div>🚀 <strong>带宽:</strong> {product.get('port_speed') or '—'}</div>
                        <div>📍 <strong>地区:</strong> {", ".join(product.get('regions', [])) or '—'}</div>
                    </div>
                    <div class="price-box">
                        {product.get('currency')} ${product.get('price')} <small>/{product.get('price_cycle')}</small>
                    </div>
                </div>

                <a href="{buy_url}" target="_blank" class="btn-action">👉 立即前往抢购 (直达官网)</a>
                
                <p style="font-size: 13px; color: #64748b; text-align: center; margin: 0;">
                    热门 VPS 库存通常消耗极快，建议尽快完成下单。
                </p>
            </div>
            <div class="footer">
                本邮件由 <a href="{site_url}">VPS 库存监控面板</a> 自动发送。<br>
                如需修改提醒或取消关注此产品，请点击 <a href="{unsub_url}">管理我的关注与订阅</a>。
            </div>
        </div>
    </body>
    </html>
    """

def render_price_drop_alert_html(product: dict, old_price: float, new_price: float, sub: dict, site_url: str) -> str:
    """Generate HTML email template for Price Drop alerts"""
    buy_url = product.get("affiliate_url") or "#"
    unsub_url = f"{site_url}/my-subscriptions?token={sub.get('unsubscribe_token')}"
    drop_amount = round(old_price - new_price, 2)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #f59e0b, #d97706); color: #ffffff; padding: 24px; text-align: center; }}
            .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 700; }}
            .header p {{ margin: 0; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 24px; }}
            .product-card {{ background: #fef3c7; border-radius: 8px; padding: 18px; margin-bottom: 20px; border-left: 4px solid #f59e0b; }}
            .product-title {{ font-size: 17px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
            .provider-badge {{ display: inline-block; background: #fde68a; color: #92400e; font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 600; margin-bottom: 12px; }}
            .price-compare {{ display: flex; align-items: baseline; gap: 12px; margin: 12px 0; font-size: 14px; }}
            .old-price {{ text-decoration: line-through; color: #94a3b8; font-size: 16px; }}
            .new-price {{ font-size: 24px; font-weight: 800; color: #dc2626; }}
            .badge-drop {{ background: #fee2e2; color: #dc2626; font-size: 12px; font-weight: 700; padding: 2px 6px; border-radius: 4px; }}
            .btn-action {{ display: block; text-align: center; background: #d97706; color: #ffffff !important; text-decoration: none; font-weight: 700; padding: 14px 20px; border-radius: 8px; font-size: 16px; margin: 24px 0 16px 0; }}
            .footer {{ border-top: 1px solid #e2e8f0; padding: 16px 24px; font-size: 12px; color: #94a3b8; text-align: center; }}
            .footer a {{ color: #64748b; text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📉 您关注的 VPS 发生降价！</h1>
                <p>价格从 {product.get('currency')} ${old_price} 下降至 ${new_price}</p>
            </div>
            <div class="content">
                <div class="product-card">
                    <span class="provider-badge">{product.get('provider')}</span>
                    <div class="product-title">{product.get('name')}</div>
                    
                    <div class="price-compare">
                        <span class="old-price">${old_price}</span>
                        <span class="new-price">${new_price}</span>
                        <span class="badge-drop">直降 ${drop_amount}</span>
                        <span style="color: #64748b;">/{product.get('price_cycle')}</span>
                    </div>

                    <div style="font-size: 13px; color: #4b5563; margin-top: 8px;">
                        ⚙️ <strong>配置:</strong> {product.get('cpu')} · {product.get('ram')} · {product.get('disk')} · {product.get('transfer')}
                    </div>
                </div>

                <a href="{buy_url}" target="_blank" class="btn-action">👉 立即按优惠价购买</a>
            </div>
            <div class="footer">
                本邮件由 <a href="{site_url}">VPS 库存监控面板</a> 自动发送。<br>
                如需修改或取消关注，请点击 <a href="{unsub_url}">管理我的关注与订阅</a>。
            </div>
        </div>
    </body>
    </html>
    """

def render_magic_link_html(email: str, token: str, site_url: str, active_count: int) -> str:
    """Generate Magic Link email for subscribers to manage their watchlists"""
    manage_url = f"{site_url}/my-subscriptions?token={token}"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
            .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
            .header {{ background: #0f172a; color: #ffffff; padding: 20px; text-align: center; }}
            .content {{ padding: 24px; text-align: center; }}
            .btn-action {{ display: inline-block; background: #3b82f6; color: #ffffff !important; text-decoration: none; font-weight: 700; padding: 12px 28px; border-radius: 8px; font-size: 15px; margin: 20px 0; }}
            .footer {{ border-top: 1px solid #e2e8f0; padding: 14px; font-size: 12px; color: #94a3b8; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">VPS 监控面板 · 订阅管理中心</h2>
            </div>
            <div class="content">
                <p style="font-size: 15px; margin-bottom: 8px;">您好，<strong>{email}</strong>：</p>
                <p style="font-size: 14px; color: #64748b; margin-top: 0;">您当前正在监控 <strong>{active_count}</strong> 款 VPS 产品的有货与降价动态。</p>
                
                <a href="{manage_url}" class="btn-action">🔑 点击进入我的关注管理中心</a>
                
                <p style="font-size: 12px; color: #94a3b8; word-break: break-all; margin-top: 16px;">
                    如果按钮无法点击，请复制以下链接在浏览器中打开：<br>
                    <a href="{manage_url}" style="color: #3b82f6;">{manage_url}</a>
                </p>
            </div>
            <div class="footer">
                此链接包含您的专属访问密钥，请妥善保管。如非本人操作请忽略此邮件。
            </div>
        </div>
    </body>
    </html>
    """
