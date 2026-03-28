from typing import Optional, List
import sqlalchemy as sa
from sqlalchemy import (
    String, ForeignKey, Integer, Float, Boolean, JSON, Index, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin

class Order(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'orders'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    user: Mapped["User"] = relationship("User", back_populates="orders")
    total_amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    items: Mapped[Optional[dict]] = mapped_column(JSON)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String)
    history: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    # V2026 Identity Snapshot (Immutable Point-in-Time Data)
    customer_name: Mapped[Optional[str]] = mapped_column(String, index=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String, index=True)
    customer_address: Mapped[Optional[str]] = mapped_column(Text)
    customer_ip: Mapped[Optional[str]] = mapped_column(String)
    order_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # V56.5 Anti-Spam Shield Fields
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    spam_score: Mapped[float] = mapped_column(Float, default=0.0)
    fingerprint: Mapped[Optional[str]] = mapped_column(String)
    spam_reason: Mapped[Optional[str]] = mapped_column(String)
    
    __table_args__ = (
        Index("ix_orders_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_orders_created_at", "created_at"),
    )

class ProductBase(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'product_bases'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    short_description: Mapped[Optional[str]] = mapped_column(String(1000))
    description: Mapped[Optional[str]] = mapped_column(Text)
    sku: Mapped[Optional[str]] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float, default=0)
    discount_price: Mapped[Optional[float]] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="DRAFT")
    type: Mapped[str] = mapped_column(String, default="RETAIL")
    
    # R102 Professional Upgrade: SEO & Fashion
    slug: Mapped[str] = mapped_column(String, index=True)
    seo_title: Mapped[Optional[str]] = mapped_column(String)
    seo_description: Mapped[Optional[str]] = mapped_column(String)
    seo_keywords: Mapped[Optional[str]] = mapped_column(String)
    images: Mapped[Optional[list]] = mapped_column(JSON, default=list) # List of image URLs
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, default=dict) # {"size": ["S", "M"], "color": ["Black"]}
    tier_variations: Mapped[Optional[list]] = mapped_column(JSON, default=list) # R102 Matrix: [{"name": "Màu", "options": ["Đỏ", "Xanh"], "images": ["url1", "url2"]}, {"name": "Size", "options": ["S", "M"]}]
    
    category_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('categories.id'))
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    
    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product_base")
    rentals: Mapped[List["RentalContract"]] = relationship("RentalContract", back_populates="product_base")
    embedding: Mapped[Optional["ProductEmbedding"]] = relationship("ProductEmbedding", back_populates="product_base", uselist=False)
    
    __table_args__ = (
        Index("ix_products_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_products_created_at", "created_at"),
    )

class ProductVariant(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = 'product_variants'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    product_base_id: Mapped[str] = mapped_column(String, ForeignKey('product_bases.id'))
    product_base: Mapped["ProductBase"] = relationship("ProductBase", back_populates="variants")
    tier_index: Mapped[Optional[list]] = mapped_column(JSON, default=list) # R102 Matrix Index: e.g [0, 1] means Đỏ, Size M
    sku: Mapped[Optional[str]] = mapped_column(String, unique=True)
    price: Mapped[float] = mapped_column(Float)
    discount_price: Mapped[Optional[float]] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)

class RentalContract(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = 'rental_contracts'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    product_base_id: Mapped[str] = mapped_column(String, ForeignKey('product_bases.id'))
    product_base: Mapped["ProductBase"] = relationship("ProductBase", back_populates="rentals")
    start_date: Mapped[sa.DateTime] = mapped_column(sa.DateTime(timezone=True))
    end_date: Mapped[sa.DateTime] = mapped_column(sa.DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    terms: Mapped[Optional[dict]] = mapped_column(JSON)

class ProductEmbedding(Base, AuditMixin):
    __tablename__ = 'product_embeddings'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    product_base_id: Mapped[str] = mapped_column(String, ForeignKey('product_bases.id'), unique=True)
    product_base: Mapped["ProductBase"] = relationship("ProductBase", back_populates="embedding")
    embedding: Mapped[str] = mapped_column(Text)
