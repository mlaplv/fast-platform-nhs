from pydantic import BaseModel, Field, ConfigDict, field_validator
import re
from typing import Optional

from datetime import datetime
from typing import Optional

class CheckoutItemSchema(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = Field(default=1, ge=1, le=1000)
    price: float = Field(..., ge=0)

class CustomItemSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    image_url: Optional[str] = Field(None)
    price: Optional[float] = Field(None, ge=0)
    quantity: int = Field(default=1, ge=1)

class GiftInfoSchema(BaseModel):
    sender_name: str = Field(..., min_length=1, max_length=100)
    sender_phone: str = Field(..., description="Số điện thoại người tặng/người đặt")
    message: Optional[str] = Field(None, max_length=500)
    packaging: Optional[str] = Field(None, description="Loại đóng gói/thiệp")
    scheduled_at: Optional[datetime] = Field(None, description="Thời gian giao quà")
    recurring_type: Optional[str] = Field("none", description="Kiểu lặp lại: none, daily, weekly, monthly, yearly")
    recurring_metadata: Optional[dict] = Field(None, description="Metadata lặp lại: days_of_week, day_of_month...")

class StealthCheckoutSchema(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)

    items: list[CheckoutItemSchema] = Field(
        ...,
        min_length=1,
        max_length=20,  # [SECURITY H-02] Chặn OOM/DDoS
        description="Danh sách sản phẩm trong giỏ"
    )
    custom_items: list[CustomItemSchema] = Field(
        default_factory=list,
        max_length=10,  # [SECURITY H-02]
        description="Danh sách sản phẩm yêu cầu thêm"
    )
    gift_info: Optional[GiftInfoSchema] = Field(None, description="Thông tin quà tặng")
    voucher_ids: list[str] = Field(
        default_factory=list,
        max_length=5,  # [SECURITY C-03] Chặn near-zero dollar bằng voucher stacking
        description="Danh sách mã giảm giá áp dụng"
    )
    customer_name: str = Field(..., min_length=2, max_length=100, description="Tên khách hàng")
    customer_phone: str = Field(..., description="Số điện thoại khách hàng")
    customer_address: str = Field(..., min_length=5, max_length=500, description="Địa chỉ nhận hàng")
    total_amount: float = Field(..., ge=0, description="Tổng tiền sau giảm giá")
    shipping_fee: float = Field(default=0, ge=0, description="Phí vận chuyển")
    payment_method: str = Field(default="cod", description="Phương thức thanh toán: cod, bank")
    points_redeemed: Optional[int] = Field(default=0, ge=0, description="Hệ thống Loyalty: Số điểm muốn trừ tiền")
    note: Optional[str] = Field(None, description="Ghi chú đơn hàng từ khách hàng")
    # CTV Attribution — Viral 2026 (manual fallback nếu không có cookie)
    ctv_code: Optional[str] = Field(
        None, max_length=20, pattern=r"^[A-Za-z0-9]*$",
        description="Mã người giới thiệu CTV (optional)"
    )

    @field_validator("customer_phone", mode="before")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        if isinstance(v, str):
            # Clean: +84 912-345.678 -> 0912345678
            v = re.sub(r"[\s\.\-\+]", "", v)
            if v.startswith("84"):
                v = "0" + v[2:]
        return v

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Standard VN format: 0 + [3|5|7|8|9] + 8 digits
        pattern = re.compile(r"^0(3|5|7|8|9)([0-9]{8})$")
        if not pattern.match(v):
            raise ValueError("Số điện thoại không hợp lệ (Chuẩn Việt Nam 10 số)")
        return v

class CustomerLookupSchema(BaseModel):
    phone: str = Field(..., description="Số điện thoại cần tra cứu")

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        if isinstance(v, str):
            v = re.sub(r"[\s\.\-\+]", "", v)
            if v.startswith("84"):
                v = "0" + v[2:]
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        pattern = re.compile(r"^0(3|5|7|8|9)([0-9]{8})$")
        if not pattern.match(v):
            raise ValueError("Số điện thoại không hợp lệ")
        return v

class CustomerLookupResponseSchema(BaseModel):
    is_recurring: bool = Field(False, description="Khách hàng cũ hay mới")
    is_trusted_device: bool = Field(False, description="Thiết bị có tin cậy (khớp session) không")
    name_masked: Optional[str] = Field(None, description="Tên đã che (***)")
    address_masked: Optional[str] = Field(None, description="Địa chỉ đã che (***)")
    name: Optional[str] = Field(None, description="Tên đầy đủ (nếu đã xác thực)")
    address: Optional[str] = Field(None, description="Địa chỉ đầy đủ (nếu đã xác thực)")

class CustomerVerifySchema(BaseModel):
    phone: str = Field(..., description="Số điện thoại")
    name: str = Field(..., description="Tên khách hàng nhập vào để xác minh")

class CustomerVerifyResponseSchema(BaseModel):
    verified: bool = Field(False, description="Xác minh thành công hay không")
    address: Optional[str] = Field(None, description="Địa chỉ nếu xác minh thành công")
