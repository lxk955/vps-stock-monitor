from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base

class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, nullable=True, index=True)
    product_id = Column(Integer, nullable=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    product_name = Column(String(255), nullable=True)
    alert_type = Column(String(50), nullable=False)
    subject = Column(String(255), nullable=False)
    status = Column(String(30), default="sent")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "product_id": self.product_id,
            "email": self.email,
            "product_name": self.product_name,
            "alert_type": self.alert_type,
            "subject": self.subject,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
