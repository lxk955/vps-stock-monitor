from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.security import generate_unsubscribe_token

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    
    notify_stock = Column(Boolean, default=True)
    notify_price_drop = Column(Boolean, default=True)
    target_price = Column(Float, nullable=True)
    
    is_active = Column(Boolean, default=True, index=True)
    unsubscribe_token = Column(String(64), default=generate_unsubscribe_token, index=True)
    
    last_notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="subscriptions")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "provider": self.product.provider if self.product else None,
            "current_price": self.product.price if self.product else None,
            "current_status": self.product.status if self.product else None,
            "currency": self.product.currency if self.product else "USD",
            "email": self.email,
            "notify_stock": self.notify_stock,
            "notify_price_drop": self.notify_price_drop,
            "target_price": self.target_price,
            "is_active": self.is_active,
            "unsubscribe_token": self.unsubscribe_token,
            "last_notified_at": self.last_notified_at.isoformat() if self.last_notified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
