"""
AI Agent Error Contract — Phase 1 AI Gateway
==============================================
Elite V2.2: Machine-readable error codes cho external AI Agents.

Design: Thay vì sửa global_exception_handler (rủi ro phá storefront),
AI Agents đọc field `error_code` trong JSON response body.
Storefront vẫn đọc `detail` như bình thường — zero regression.

Usage (AI Agent side):
    resp = POST /api/v1/client/checkout/stealth
    if resp.status_code != 200:
        code = resp.json().get("error_code")
        match code:
            case "SPAM_BLOCKED": retry = False
            case "PRICE_CHANGED": refetch_product(); retry = True
            case "OUT_OF_STOCK": notify_user(); retry = False
"""
from __future__ import annotations
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AgentErrorCode(StrEnum):
    """
    Danh sách mã lỗi machine-readable cho AI Agent.
    Prefix:
      ORDER_   → Lỗi nghiệp vụ đơn hàng
      AUTH_    → Lỗi xác thực / phân quyền
      QUOTA_   → Giới hạn token / rate limit
      INPUT_   → Lỗi dữ liệu đầu vào
      SYSTEM_  → Lỗi hạ tầng
    """
    # ── Đơn hàng ─────────────────────────────────────────
    SPAM_BLOCKED        = "ORDER_SPAM_BLOCKED"        # AntiSpam score >= 90
    SPAM_CHALLENGE      = "ORDER_SPAM_CHALLENGE"      # AntiSpam score 70-89
    PRICE_CHANGED       = "ORDER_PRICE_CHANGED"       # Giá sản phẩm thay đổi kể từ khi agent fetch
    OUT_OF_STOCK        = "ORDER_OUT_OF_STOCK"        # Hết hàng
    MIN_AMOUNT          = "ORDER_MIN_AMOUNT"          # Đơn hàng dưới mức tối thiểu
    EXTREME_DISCOUNT    = "ORDER_EXTREME_DISCOUNT"    # Tổng thanh toán < 50% giá gốc
    PRICE_MISMATCH      = "ORDER_PRICE_MISMATCH"      # Payload.total_amount ≠ server calculation
    PRODUCT_NOT_FOUND   = "ORDER_PRODUCT_NOT_FOUND"   # Sản phẩm/variant không tồn tại
    VOUCHER_INVALID     = "ORDER_VOUCHER_INVALID"     # Mã giảm giá không hợp lệ
    VOUCHER_LOCKED      = "ORDER_VOUCHER_LOCKED"      # Mã giảm giá chưa được unlock
    IDEMPOTENT_REPLAY   = "ORDER_IDEMPOTENT_REPLAY"   # Đơn đã tạo trước đó (idempotency hit)

    # ── Xác thực / bảo mật ──────────────────────────────
    INPUT_INJECTION     = "AUTH_INPUT_INJECTION"      # Prompt injection detected
    QUOTA_EXCEEDED      = "AUTH_SESSION_QUOTA"        # Session token limit reached
    BLACKLISTED         = "AUTH_BLACKLISTED"          # IP blacklisted

    # ── Hệ thống ─────────────────────────────────────────
    SYSTEM_READONLY     = "SYSTEM_MARTIAL_LAW"        # Hệ thống đang Martial Law (Read-Only)
    UNKNOWN             = "SYSTEM_UNKNOWN"


class AgentErrorResponse(BaseModel):
    """
    Response body chuẩn cho AI Agent khi gặp lỗi.
    Storefront chỉ đọc `detail`. AI Agent đọc `error_code` + `retry_after`.
    """
    model_config = ConfigDict(strict=False)

    detail: str                                   # Human-readable (tiếng Việt cho storefront)
    error_code: AgentErrorCode = AgentErrorCode.UNKNOWN
    retry: bool = False                           # Agent có nên thử lại không?
    retry_after: Optional[int] = None            # Số giây nên chờ trước khi retry
    trace_id: Optional[str] = None               # Để debug
    hint: Optional[str] = None                   # Gợi ý hành động tiếp theo (EN)
