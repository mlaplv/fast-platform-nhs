"""
Elite V2.2 — Money Utility: Single Source of Truth cho tài chính VNĐ.

NGUYÊN TẮC:
- Lưu trữ: BigInteger (đơn vị VNĐ nguyên, không thập phân)
- Tỷ lệ %: Basis Points (1% = 100 bps, 15% = 1500 bps)
- Phép toán: Integer-only, KHÔNG dùng float cho tài chính
- Hiển thị: format_vnd() chỉ dùng ở tầng API response

TRÁNH:
  ❌ 150_000 * 0.15          → 22_499.999... (IEEE 754 error)
  ✅ apply_bps(150_000, 1500) → 22_500        (exact integer)
"""
from __future__ import annotations
from typing import Annotated
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


# ── Basis Points helpers ───────────────────────────────────────────────────────

def pct_to_bps(percent: float) -> int:
    """Chuyển % sang basis points. VD: 15.0 → 1500"""
    return round(percent * 100)


def bps_to_pct(bps: int) -> float:
    """Chuyển basis points sang %. VD: 1500 → 15.0"""
    return bps / 100.0


def apply_bps(amount_vnd: int, rate_bps: int) -> int:
    """
    Tính số tiền từ tỷ lệ basis points. Integer-only, KHÔNG float.
    VD: apply_bps(150_000, 1500) → 22_500 (chính xác tuyệt đối)
    """
    return (amount_vnd * rate_bps) // 10_000


def apply_pct(amount_vnd: int, percent: float) -> int:
    """
    Shorthand: tính tiền từ % (chuyển sang bps nội bộ).
    VD: apply_pct(150_000, 15.0) → 22_500
    """
    return apply_bps(amount_vnd, pct_to_bps(percent))


# ── Conversion helpers ─────────────────────────────────────────────────────────

def to_vnd(amount: float | int) -> int:
    """
    Chuyển giá trị float sang integer VNĐ (round, không truncate).
    Dùng khi nhập dữ liệu từ API cũ hoặc DB legacy.
    VD: to_vnd(149_999.9) → 150_000
    """
    return round(float(amount))


def from_float_price(price: float | None) -> int:
    """An toàn hơn: xử lý None và chuyển về int VNĐ."""
    if price is None:
        return 0
    return round(float(price))


# ── Display only (KHÔNG dùng cho logic tài chính) ─────────────────────────────

def format_vnd(amount_vnd: int) -> str:
    """
    Định dạng hiển thị VNĐ cho API response/UI.
    VD: format_vnd(1_500_000) → '1.500.000đ'
    CHÚ Ý: Chỉ dùng ở tầng presentation, KHÔNG dùng trong logic tính toán.
    """
    return f"{amount_vnd:,}".replace(",", ".") + "đ"


# ── Pydantic MoneyVND validator class ─────────────────────────────────────────

class _MoneyVNDAnnotation:
    """
    Internal validator class cho Pydantic v2 MoneyVND type.
    Không dùng trực tiếp — dùng MoneyVND type alias bên dưới.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: object,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.int_schema(),
            serialization=core_schema.int_schema(),
        )

    @classmethod
    def _validate(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"MoneyVND không thể âm: {v}")
        return v


# MoneyVND = integer VNĐ với validation >= 0
# Dùng làm type hint trong Pydantic schemas:
#   price: MoneyVND          # validated int >= 0
#   discount_price: MoneyVND | None
MoneyVND = Annotated[int, _MoneyVNDAnnotation]


# ── SQLAlchemy column shorthand ────────────────────────────────────────────────

def money_column(default: int = 0, nullable: bool = False, **kwargs):
    """
    Shorthand tạo SQLAlchemy BigInteger column cho tiền tệ.
    Thay thế: mapped_column(Float, default=0)
    Bằng:     money_column(0)
    """
    from sqlalchemy import BigInteger
    from sqlalchemy.orm import mapped_column
    return mapped_column(BigInteger, default=default, nullable=nullable, **kwargs)
