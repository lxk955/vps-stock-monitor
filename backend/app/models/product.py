from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    group = Column(String(100), nullable=True)
    
    cpu = Column(String(50), nullable=True)
    ram = Column(String(50), nullable=True)
    disk = Column(String(50), nullable=True)
    transfer = Column(String(50), nullable=True)
    port_speed = Column(String(50), nullable=True)
    
    cpu_cores = Column(Integer, default=1, index=True)
    ram_mb = Column(Integer, default=1024, index=True)
    disk_gb = Column(Integer, default=20, index=True)
    transfer_gb = Column(Integer, default=1000)
    port_mbps = Column(Integer, default=1000)
    
    regions_json = Column(Text, default="[]")
    lines_json = Column(Text, default="[]")
    
    status = Column(String(30), default="in_stock", index=True)
    stock_qty = Column(Integer, nullable=True)
    
    price = Column(Float, nullable=False, default=0.0, index=True)
    original_price = Column(Float, nullable=True)
    previous_price = Column(Float, nullable=True)
    currency = Column(String(10), default="USD", index=True)
    price_cycle = Column(String(30), default="annually", index=True)
    
    affiliate_url = Column(String(500), nullable=True)
    stock_check_url = Column(String(500), nullable=True)
    stock_check_type = Column(String(50), default="manual")
    out_of_stock_keyword = Column(String(100), default="Out of Stock")
    
    recommended = Column(Boolean, default=False, index=True)
    clicks = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    
    last_checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    subscriptions = relationship("Subscription", back_populates="product", cascade="all, delete-orphan")
    price_histories = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_products_provider_status", "provider", "status"),
        Index("ix_products_price_status", "price", "status"),
    )

    @property
    def regions(self):
        try:
            return json.loads(self.regions_json) if self.regions_json else []
        except Exception:
            return []

    @regions.setter
    def regions(self, val):
        self.regions_json = json.dumps(val, ensure_ascii=False)

    @property
    def lines(self):
        try:
            return json.loads(self.lines_json) if self.lines_json else []
        except Exception:
            return []

    @lines.setter
    def lines(self, val):
        self.lines_json = json.dumps(val, ensure_ascii=False)

    def to_dict(self):
        return {
            "id": self.id,
            "provider": self.provider,
            "name": self.name,
            "group": self.group,
            "cpu": self.cpu,
            "ram": self.ram,
            "disk": self.disk,
            "transfer": self.transfer,
            "port_speed": self.port_speed,
            "cpu_cores": self.cpu_cores,
            "ram_mb": self.ram_mb,
            "disk_gb": self.disk_gb,
            "transfer_gb": self.transfer_gb,
            "port_mbps": self.port_mbps,
            "regions": self.regions,
            "lines": self.lines,
            "status": self.status,
            "stock_qty": self.stock_qty,
            "price": self.price,
            "original_price": self.original_price,
            "previous_price": self.previous_price,
            "currency": self.currency,
            "price_cycle": self.price_cycle,
            "affiliate_url": self.affiliate_url,
            "stock_check_url": self.stock_check_url,
            "stock_check_type": self.stock_check_type,
            "out_of_stock_keyword": self.out_of_stock_keyword,
            "recommended": bool(self.recommended),
            "clicks": self.clicks or 0,
            "is_active": bool(self.is_active),
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class PriceHistory(Base):
    __tablename__ = "price_histories"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(String(30), default="in_stock")
    stock_qty = Column(Integer, nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    product = relationship("Product", back_populates="price_histories")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "price": self.price,
            "currency": self.currency,
            "status": self.status,
            "stock_qty": self.stock_qty,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }
