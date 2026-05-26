from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
import math

class PricingInputItem(BaseModel):
    """Elite V2.2: Input model for PricingEngine to ensure 100% static typing."""
    model_config = ConfigDict(strict=False)
    product_id: str
    name: str = "Sản phẩm"
    quantity: int = 1
    unit_price: float = 0.0

class PricingItem(BaseModel):
    model_config = ConfigDict(strict=False)
    product_id: str
    name: str
    quantity: int
    unit_price: float
    total_price: float

class PricingBreakdown(BaseModel):
    """Elite V2.2: Unified Pricing Breakdown Model"""
    model_config = ConfigDict(strict=False)
    
    items: List[PricingItem] = Field(default_factory=list)
    
    subtotal: float = 0.0
    combo_discount: float = 0.0
    voucher_discount: float = 0.0
    
    base_shipping_fee: float = 0.0
    shipping_discount: float = 0.0
    final_shipping_fee: float = 0.0
    
    max_point_discount_allowed: float = 0.0
    points_redeemed: int = 0
    point_discount_amount: float = 0.0
    
    final_payable: float = 0.0
    points_to_earn: int = 0
    
    # Metadata for UI/AI reporting
    applied_voucher_ids: List[str] = Field(default_factory=list)
    applied_combo_ids: List[str] = Field(default_factory=list)

    @field_validator(
        "subtotal", "combo_discount", "voucher_discount", 
        "base_shipping_fee", "shipping_discount", "final_shipping_fee",
        "max_point_discount_allowed", "points_redeemed", "point_discount_amount",
        "final_payable", "points_to_earn",
        mode="before"
    )
    @classmethod
    def sanitize_numeric_inputs(cls, v):
        if v is None:
            return 0
        if isinstance(v, (int, float)):
            if math.isnan(v) or math.isinf(v):
                return 0
        elif isinstance(v, str):
            if v.lower() in ("nan", "null", "undefined", ""):
                return 0
            try:
                return float(v)
            except ValueError:
                return 0
        return v

