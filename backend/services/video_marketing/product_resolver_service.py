import re
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import ProductBase, ProductVariant
from backend.database.models import Category

logger = logging.getLogger("api-gateway")

class ProductResolverService:
    """Dịch vụ trích xuất và định dạng ngữ cảnh sản phẩm từ Database nội bộ."""
    
    @staticmethod
    def _extract_slug_or_id(source: str) -> str:
        """Trích xuất slug hoặc ID từ URL sản phẩm hoặc chuỗi nhập vào."""
        source = source.strip()
        # Nếu là URL, tìm phần slug ở cuối đường dẫn
        if source.startswith("http://") or source.startswith("https://"):
            # Loại bỏ query parameters nếu có
            path = source.split("?")[0]
            # Loại bỏ slash cuối cùng nếu có
            if path.endswith("/"):
                path = path[:-1]
            # Lấy phần tử cuối cùng của path
            segment = path.split("/")[-1]
            return segment
        return source

    @classmethod
    async def get_product_context(cls, source: str, db: AsyncSession) -> Optional[str]:
        """
        Truy vấn thông tin sản phẩm và định dạng thành Markdown.
        Chấp nhận URL sản phẩm, Slug sản phẩm hoặc Product ID.
        """
        key = cls._extract_slug_or_id(source)
        logger.info(f"[ProductResolver] Resolving context for key: {key}")
        
        # 1. Tìm theo ID hoặc Slug (UUID/ID thường dài 36 ký tự hoặc định dạng khác)
        stmt = (
            select(ProductBase)
            .where(
                (ProductBase.id == key) | 
                (ProductBase.slug == key) |
                (ProductBase.sku == key)
            )
            .where(ProductBase.deleted_at.is_(None))
        )
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            logger.warning(f"[ProductResolver] No product found for key: {key}")
            return None
            
        # Lấy thêm thông tin Category nếu có
        category_name = "N/A"
        if product.category_id:
            cat_stmt = select(Category).where(Category.id == product.category_id)
            cat_res = await db.execute(cat_stmt)
            cat = cat_res.scalar_one_or_none()
            if cat:
                category_name = getattr(cat, "name", None) or "N/A"

        # Định dạng thông tin giá bán
        price_vnd = f"{product.price:,}₫"
        discount_price_vnd = f"{product.discount_price:,}₫" if product.discount_price else "Không có giảm giá"
        discount_percent = f"{product.discount_percent}%" if product.discount_percent else "0%"
        
        # Tạo Markdown context
        context = f"""--- THÔNG TIN SẢN PHẨM TRONG HỆ THỐNG ---
- **Tên sản phẩm**: {product.name}
- **Danh mục**: {category_name}
- **Mã sản phẩm (SKU)**: {product.sku or 'N/A'}
- **Giá gốc**: {price_vnd}
- **Giá ưu đãi**: {discount_price_vnd} (Giảm: {discount_percent})
- **Trạng thái tồn kho**: {'Còn hàng' if product.stock > 0 else 'Hết hàng'} (Số lượng: {product.stock})

--- MÔ TẢ TỐM TẮT ---
{product.short_description or 'Không có mô tả ngắn.'}

--- MÔ TẢ CHI TIẾT ---
{product.description or 'Không có mô tả chi tiết.'}
"""

        # Bổ sung các thông số thuộc tính (Attributes) nếu có
        if product.attributes:
            context += "\n--- ĐẶC TÍNH SẢN PHẨM ---\n"
            for k, v in product.attributes.items():
                context += f"- **{k.capitalize()}**: {v}\n"

        return context.strip()

product_resolver_service = ProductResolverService()
