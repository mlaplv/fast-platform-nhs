from typing import Optional
import sqlalchemy as sa
from sqlalchemy import String, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin
from backend.utils.uid import new_id_default

class VideoScriptStyle(Base, AuditMixin):
    """
    Bảng lưu trữ các phong cách kịch bản/xu hướng video ngắn (TikTok/Reels/Shorts).
    Cho phép mở rộng động bằng cách thêm mới các trend mà không cần sửa code.
    """
    __tablename__ = 'video_script_styles'

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # slug, ví dụ: 'tiktok_drama'
    name: Mapped[str] = mapped_column(String(100))                 # tên hiển thị
    platform: Mapped[str] = mapped_column(String(20))              # TikTok, Reels, YouTube
    hook_template: Mapped[str] = mapped_column(Text)               # Chỉ thị làm hook 3s đầu
    style_instruction: Mapped[str] = mapped_column(Text)           # Hướng dẫn phong cách chung
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class VideoScript(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    """
    Bảng lưu kịch bản video đã tạo thành công và liên kết với sản phẩm.
    """
    __tablename__ = 'video_scripts'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id_default)
    product_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('product_bases.id'), nullable=True)
    style_id: Mapped[str] = mapped_column(String(50), ForeignKey('video_script_styles.id'))
    title: Mapped[str] = mapped_column(String)
    structured_script: Mapped[dict[str, object]] = mapped_column(JSONB) # Lưu trữ JSON kịch bản phân cảnh
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('users.id'), nullable=True)

    # Relationships
    product: Mapped[Optional["ProductBase"]] = relationship("ProductBase")
    style: Mapped["VideoScriptStyle"] = relationship("VideoScriptStyle")
