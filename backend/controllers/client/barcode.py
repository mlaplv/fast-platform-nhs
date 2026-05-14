from typing import Optional
from litestar import Controller, get
from litestar.params import Parameter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import ProductBase
from backend.services.commerce.barcode_agent import barcode_agent
from backend.schemas.barcode import BarcodeVerificationResponse
from litestar.exceptions import NotFoundException
import logging

logger = logging.getLogger("api-gateway.barcode")

class BarcodeController(Controller):
    path = "/api/v1/client/barcode"
    tags = ["Client - Barcode"]

    @get("/verify")
    async def verify_barcode(
        self,
        db_session: AsyncSession,
        barcode: str = Parameter(description="Mã vạch sản phẩm"),
        product_id: Optional[str] = Parameter(default=None, description="ID sản phẩm (tùy chọn)")
    ) -> BarcodeVerificationResponse:
        """
        Elite V2.2: Barcode Verification Endpoint.
        - Trình diện sự thật (Truth) qua AI.
        - Kích thích mua hàng (FOMO).
        """
        logger.info(f"🔍 [BarcodeController] Verifying barcode: {barcode}")
        
        # 1. Tìm sản phẩm trong DB để lấy Tên và Thương hiệu chính thống
        stmt = select(ProductBase).where(ProductBase.sku == barcode, ProductBase.deleted_at == None)
        if product_id:
            stmt = select(ProductBase).where(ProductBase.id == product_id, ProductBase.deleted_at == None)
            
        res = await db_session.execute(stmt)
        product = res.scalar_one_or_none()
        
        if not product:
            logger.warning(f"⚠️ [BarcodeController] SKU {barcode} not found in DB. Falling back to search.")
            product_name = "Sản phẩm ẩn danh"
            brand = "Unknown Brand"
            metadata: dict = {}
            attributes: dict = {}
        else:
            product_name = product.name
            metadata = getattr(product, 'product_metadata', {}) or {}
            attributes = getattr(product, 'attributes', {}) or {}
            brand = metadata.get("brand") or attributes.get("brand")
            
            # Elite V2.2: Intelligent Brand Extraction fallback
            if not brand or brand == "Thương hiệu quốc tế":
                name_upper = product_name.upper()
                if "MICCOSMO" in name_upper or "HURRY HARRY" in name_upper:
                    brand = "Miccosmo"
                elif "OSMO" in name_upper:
                    brand = "Osmo"
                else:
                    brand = brand or "Thương hiệu quốc tế"

        # 2. Extract Regulatory Data from DB Metadata (Elite V2.2 Truth Source)
        reg_info = {
            "notification_no": metadata.get("notification_no"),
            "notification_date": metadata.get("notification_date"),
            "notification_doc": metadata.get("notification_doc"),
            "mfg_date": metadata.get("mfg_date"),
            "expiry_date": metadata.get("expiry_date"),
            "batch_dna": metadata.get("batch_dna"),
            "factory_address": metadata.get("factory_address"),
            "origin": metadata.get("origin"),
        }

        # 3. Gọi Agent để thẩm định nguồn gốc
        verification_data = await barcode_agent.verify(barcode, product_name, brand, reg_info=reg_info)
        
        return verification_data
