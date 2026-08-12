from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict

from app.core.database import get_db
from app.models.setting import Setting
from app.models.alert_log import AlertLog
from app.core.security import verify_password, get_password_hash, create_access_token, verify_admin_token
from app.services.email_service import get_smtp_config, send_email

router = APIRouter(prefix="/settings", tags=["Settings"])

class SmtpTestRequest(BaseModel):
    test_email: EmailStr

class AdminAuthRequest(BaseModel):
    password: str

@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting))
    settings_list = result.scalars().all()
    config = {s.key: s.value for s in settings_list}

    smtp_pass_set = bool(config.get("smtp_pass"))
    
    return {
        "smtp_host": config.get("smtp_host", ""),
        "smtp_port": int(config.get("smtp_port", 465) or 465),
        "smtp_user": config.get("smtp_user", ""),
        "smtp_pass_configured": smtp_pass_set,
        "smtp_from_name": config.get("smtp_from_name", "VPS 实时库存与降价监控"),
        "smtp_from_email": config.get("smtp_from_email", ""),
        "smtp_ssl": config.get("smtp_ssl", "true").lower() in ("true", "1", "yes"),
        "smtp_tls": config.get("smtp_tls", "false").lower() in ("true", "1", "yes"),
        "crawler_interval_seconds": int(config.get("crawler_interval_seconds", 180) or 180),
        "crawler_enabled": config.get("crawler_enabled", "true").lower() in ("true", "1", "yes"),
        "notification_cooldown_minutes": int(config.get("notification_cooldown_minutes", 30) or 30),
        "site_title": config.get("site_title", "VPS 超市 / 实时库存与降价监控"),
        "site_announcement": config.get("site_announcement", "欢迎使用 VPS 实时库存与降价监控平台！关注心仪机型，有货或降价第一时间邮件送达。"),
        "site_url": config.get("site_url", "http://localhost:5173"),
        # Vendor AFF Referral Codes
        "aff_bwh": config.get("aff_bwh", ""),
        "aff_racknerd": config.get("aff_racknerd", ""),
        "aff_dmit": config.get("aff_dmit", ""),
        "aff_clawcloud": config.get("aff_clawcloud", ""),
        "aff_vps": config.get("aff_vps", ""),
        "aff_spartan": config.get("aff_spartan", ""),
        "aff_netcup": config.get("aff_netcup", ""),
        "aff_hetzner": config.get("aff_hetzner", ""),
        "aff_buyvm": config.get("aff_buyvm", ""),
        "aff_akile": config.get("aff_akile", ""),
        "aff_wikihost": config.get("aff_wikihost", ""),
        "aff_kurun": config.get("aff_kurun", ""),
        "aff_cloudcone": config.get("aff_cloudcone", ""),
    }

@router.put("")
async def update_settings(
    data: dict,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Protected: update settings (requires admin token)"""
    for key, val in data.items():
        if val is None:
            continue
        if key == "smtp_pass" and val == "":
            continue

        result = await db.execute(select(Setting).where(Setting.key == key))
        setting_obj = result.scalar_one_or_none()
        if setting_obj:
            setting_obj.value = str(val)
        else:
            db.add(Setting(key=key, value=str(val)))

    await db.commit()
    return {"message": "系统设置已成功保存！"}

@router.post("/test-email")
async def test_smtp_email(
    data: SmtpTestRequest,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Protected: send test email (requires admin token)"""
    test_html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: sans-serif; background-color: #f8fafc; padding: 20px; color: #1e293b;">
        <div style="max-width: 500px; margin: 0 auto; background: #ffffff; padding: 24px; border-radius: 10px; border: 1px solid #e2e8f0;">
            <h2 style="color: #10b981; margin-top: 0;">🎉 SMTP 邮件服务配置成功！</h2>
            <p>这是一封来自 <strong>VPS 实时库存与价格监控系统</strong> 的测试邮件。</p>
            <p style="color: #64748b; font-size: 14px;">如果您收到了此邮件，说明您的 SMTP 服务器（发件箱、端口、密码/授权码）配置完全正常，后续产品补货和降价提醒将能准时送达。</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="font-size: 12px; color: #94a3b8; margin: 0;">测试收件邮箱：{data.test_email}</p>
        </div>
    </body>
    </html>
    """

    try:
        await send_email(
            to_email=data.test_email,
            subject="🎉【配置测试】VPS 监控面板 SMTP 发信测试成功",
            html_content=test_html,
            alert_type="test"
        )
        return {"message": f"测试邮件已成功发送至 {data.test_email}，请查收！"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发信失败: {str(e)}")

@router.post("/verify-admin")
async def verify_admin_password(data: AdminAuthRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting).where(Setting.key == "admin_password_hash"))
    setting_obj = result.scalar_one_or_none()
    
    is_valid = False
    if not setting_obj or not setting_obj.value:
        if data.password == "admin123456":
            is_valid = True
    elif verify_password(data.password, setting_obj.value):
        is_valid = True
    
    if is_valid:
        token = create_access_token({"sub": "admin", "role": "admin"})
        return {"valid": True, "token": token}
    
    raise HTTPException(status_code=401, detail="密码错误")

@router.get("/alert-logs")
async def get_alert_logs(
    limit: int = 50,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Protected: retrieve audit logs (requires admin token)"""
    result = await db.execute(select(AlertLog).order_by(desc(AlertLog.created_at)).limit(limit))
    logs = result.scalars().all()
    return [l.to_dict() for l in logs]
