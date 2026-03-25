from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator
from typing import Optional, List, Union, Dict, Any
from datetime import datetime


class OrderItem(BaseModel):
    model_config = ConfigDict(strict=True)
    productId: Optional[str] = Field(None, alias="product_id")
    name: str
    price: float
    quantity: int


class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    items: List[Dict[str, Union[str, int, float, bool, None]]] # Simplified for now as items can be complex JSON
    total_amount: float = Field(..., ge=0)
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_email: str = Field(..., min_length=3, max_length=200)
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = Field(..., pattern=r"^(PENDING|PAID|PROCESSING|SHIPPED|DELIVERED|COMPLETED|CANCELLED)$")


class CancelOrderRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    reason: str = Field(..., min_length=1, max_length=1000)


class CustomerInsight(BaseModel):
    ltv: float = 0.0
    total_orders: int = 0
    trust_score: float = 0.0
    first_order: Optional[str] = None
    last_order: Optional[str] = None
    previous_orders: List[Dict[str, Any]] = Field(default_factory=list)

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)

    id: str
    customerName: Optional[str] = Field(None, alias="customer_name")
    customerPhone: Optional[str] = Field(None, alias="customer_phone")
    customerAddress: Optional[str] = Field(None, alias="customer_address")
    customerIp: Optional[str] = Field(None, alias="customer_ip")
    userName: Optional[str] = Field(None, alias="user_name")
    status: str
    total: float = Field(..., alias="total_amount")
    items: Union[List[OrderItem], int] # Can be list of items or count depending on context
    createdAt: datetime = Field(alias="created_at")
    cancellationReason: Optional[str] = Field(None, alias="cancellation_reason")
    isSpam: bool = Field(False, alias="is_spam")
    spamScore: float = Field(0.0, alias="spam_score")
    spamReason: Optional[str] = Field(None, alias="spam_reason")
    fingerprint: Optional[str] = None
    orderMetadata: Dict[str, object] = Field(default_factory=dict, alias="order_metadata")
    successfulOrdersCount: int = Field(0, alias="successful_count")
    cancelledOrdersCount: int = Field(0, alias="cancelled_count")
    history: List[Dict[str, Union[str, int, float, bool, None]]] = Field(default_factory=list)
    insight: Optional[CustomerInsight] = None
    cancellationReason: Optional[str] = Field(None, alias="cancellation_reason")

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v):
        return str(v) if v is not None else None

    @computed_field
    @property
    def display_status(self) -> str:
        return self.status.lower()

    @computed_field
    @property
    def finalCustomerName(self) -> str:
        return self.customerName or self.userName or "Guest Customer"

    @computed_field
    @property
    def itemCount(self) -> int:
        if isinstance(self.items, list):
            # Sum quantities if list of dicts or OrderItem
            total = 0
            for item in self.items:
                if isinstance(item, OrderItem):
                    total += item.quantity
                elif isinstance(item, dict):
                    total += int(item.get("quantity", 0))
            return total
        if isinstance(self.items, int):
            return self.items
        return 0


class OrderListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: List[OrderResponse]
    total: int
