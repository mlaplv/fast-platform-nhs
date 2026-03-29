from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator, AliasChoices
from typing import Optional, List, Union, Dict
from datetime import datetime


class OrderItem(BaseModel):
    model_config = ConfigDict(strict=True, populate_by_name=True)
    productId: str = Field(..., alias="product_id", validation_alias=AliasChoices("product_id", "id"))
    name: str = Field("Sản phẩm", min_length=1)
    price: float = Field(..., alias="unit_price", validation_alias=AliasChoices("unit_price", "price"))
    quantity: int = Field(..., alias="qty", validation_alias=AliasChoices("qty", "quantity"))
    totalPrice: float = Field(0.0, alias="total_price")

    @field_validator("productId", mode="before")
    @classmethod
    def map_id_alias(cls, v: object) -> object:
        # Handle cases where DB has 'id' instead of 'product_id'
        if isinstance(v, dict) and "id" in v and "product_id" not in v:
            return v["id"]
        return v


class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    items: List[Dict[str, Union[str, int, float, bool, None, List[object], Dict[str, object]]]]
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
    previous_orders: List[Dict[str, object]] = Field(default_factory=list)


class PublicCustomerInsight(BaseModel):
    """Elite V2.2: Restricted Insight for Public Tracking Page thưa sếp!"""
    total_orders: int = 0


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)

    id: str
    customerName: Optional[str] = Field(None, alias="customer_name", validation_alias=AliasChoices("customer_name", "customerName"))
    customerPhone: Optional[str] = Field(None, alias="customer_phone", validation_alias=AliasChoices("customer_phone", "customerPhone"))
    customerAddress: Optional[str] = Field(None, alias="customer_address", validation_alias=AliasChoices("customer_address", "customerAddress"))
    customerIp: Optional[str] = Field(None, alias="customer_ip", validation_alias=AliasChoices("customer_ip", "customerIp"))
    userName: Optional[str] = Field(None, alias="user_name", validation_alias=AliasChoices("user_name", "userName"))
    status: str
    total: float = Field(..., alias="total_amount", validation_alias=AliasChoices("total_amount", "total"))
    items: Union[List[OrderItem], int, List[Dict[str, object]]] 
    createdAt: datetime = Field(alias="created_at", validation_alias=AliasChoices("created_at", "createdAt"))
    cancellationReason: Optional[str] = Field(None, alias="cancellation_reason", validation_alias=AliasChoices("cancellation_reason", "cancellationReason"))
    isSpam: bool = Field(False, alias="is_spam", validation_alias=AliasChoices("is_spam", "isSpam"))
    spamScore: float = Field(0.0, alias="spam_score", validation_alias=AliasChoices("spam_score", "spamScore"))
    spamReason: Optional[str] = Field(None, alias="spam_reason", validation_alias=AliasChoices("spam_reason", "spamReason"))
    fingerprint: Optional[str] = None
    orderMetadata: Dict[str, object] = Field(default_factory=dict, alias="order_metadata", validation_alias=AliasChoices("order_metadata", "orderMetadata"))
    successfulOrdersCount: int = Field(0, alias="successful_count", validation_alias=AliasChoices("successful_count", "successfulOrdersCount"))
    cancelledOrdersCount: int = Field(0, alias="cancelled_count", validation_alias=AliasChoices("cancelled_count", "cancelledOrdersCount"))
    history: List[Dict[str, Union[str, int, float, bool, None]]] = Field(default_factory=list)
    insight: Optional[CustomerInsight] = None

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v):
        return str(v) if v is not None else None

    @computed_field
    @property
    def displayStatus(self) -> str:
        return self.status.lower()

    @computed_field
    @property
    def finalCustomerName(self) -> str:
        return self.customerName or self.userName or "Guest Customer"

    @computed_field
    @property
    def itemCount(self) -> int:
        items = self.items
        if isinstance(items, list):
            total = 0
            for item in items:
                if isinstance(item, OrderItem):
                    total += item.quantity
                elif isinstance(item, dict):
                    qty = item.get("quantity") or item.get("qty")
                    if isinstance(qty, (int, float)):
                        total += int(qty)
            return total
        if isinstance(items, int):
            return items
        return 0


class OrderListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: List[OrderResponse]
    total: int


class PublicOrderResponse(BaseModel):
    """Elite V2.2: Hardened Order Response for Public/Client access thưa sếp!"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)

    id: str
    customerName: Optional[str] = Field(None, alias="customer_name", validation_alias=AliasChoices("customer_name", "customerName"))
    customerPhone: Optional[str] = Field(None, alias="customer_phone", validation_alias=AliasChoices("customer_phone", "customerPhone"))
    customerAddress: Optional[str] = Field(None, alias="customer_address", validation_alias=AliasChoices("customer_address", "customerAddress"))
    userName: Optional[str] = Field(None, alias="user_name", validation_alias=AliasChoices("user_name", "userName"))
    status: str
    total: float = Field(..., alias="total_amount", validation_alias=AliasChoices("total_amount", "total"))
    items: Union[List[OrderItem], int, List[Dict[str, object]]]
    createdAt: datetime = Field(alias="created_at", validation_alias=AliasChoices("created_at", "createdAt"))
    cancellationReason: Optional[str] = Field(None, alias="cancellation_reason", validation_alias=AliasChoices("cancellation_reason", "cancellationReason"))
    successfulOrdersCount: int = Field(0, alias="successful_count", validation_alias=AliasChoices("successful_count", "successfulOrdersCount"))
    cancelledOrdersCount: int = Field(0, alias="cancelled_count", validation_alias=AliasChoices("cancelled_count", "cancelledOrdersCount"))
    insight: Optional[PublicCustomerInsight] = None

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v):
        return str(v) if v is not None else None

    @computed_field
    @property
    def displayStatus(self) -> str:
        return self.status.lower()

    @computed_field
    @property
    def finalCustomerName(self) -> str:
        return self.customerName or self.userName or "Guest Customer"

    @computed_field
    @property
    def itemCount(self) -> int:
        items = self.items
        if isinstance(items, list):
            total = 0
            for item in items:
                if isinstance(item, OrderItem):
                    total += item.quantity
                elif isinstance(item, dict):
                    qty = item.get("quantity") or item.get("qty")
                    if isinstance(qty, (int, float)):
                        total += int(qty)
            return total
        if isinstance(items, int):
            return items
        return 0
