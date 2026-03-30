from pydantic import BaseModel, Field, ConfigDict, field_validator
import re
from typing import Optional

class StealthCheckoutSchema(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)

    product_id: str = Field(..., description="ID của sản phẩm")
    variant_id: Optional[str] = Field(None, description="ID của phiên bản sản phẩm (nếu có)")
    customer_name: str = Field(..., min_length=2, max_length=100, description="Tên khách hàng")
    customer_phone: str = Field(..., description="Số điện thoại khách hàng")
    customer_address: str = Field(..., min_length=5, max_length=500, description="Địa chỉ nhận hàng")
    quantity: int = Field(default=1, ge=1, le=10, description="Số lượng sản phẩm")

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Chuẩn hóa số điện thoại Việt Nam: (0|84) + [3|5|7|8|9] + 8 số
        pattern = re.compile(r"^(0|84|)(3|5|7|8|9)([0-9]{8})$")
        if not pattern.match(v):
            raise ValueError("Số điện thoại không hợp lệ (Chuẩn Việt Nam)")
        return v

class CustomerLookupSchema(BaseModel):
    phone: str = Field(..., description="Số điện thoại cần tra cứu")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        pattern = re.compile(r"^(0|84|)(3|5|7|8|9)([0-9]{8})$")
        if not pattern.match(v):
            raise ValueError("Số điện thoại không hợp lệ")
        return v

class CustomerLookupResponseSchema(BaseModel):
    is_recurring: bool = Field(False, description="Khách hàng cũ hay mới")
    is_trusted_device: bool = Field(False, description="Thiết bị có tin cậy (khớp session) không")
    name_masked: Optional[str] = Field(None, description="Tên đã che (***)")
    address_masked: Optional[str] = Field(None, description="Địa chỉ đã che (***)")

class CustomerVerifySchema(BaseModel):
    phone: str = Field(..., description="Số điện thoại")
    name: str = Field(..., description="Tên khách hàng nhập vào để xác minh")

class CustomerVerifyResponseSchema(BaseModel):
    verified: bool = Field(False, description="Xác minh thành công hay không")
    address: Optional[str] = Field(None, description="Địa chỉ nếu xác minh thành công")
