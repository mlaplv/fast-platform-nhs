from __future__ import annotations
import logging
from typing import Optional
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repositories import provide_support_kb_repo
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.support import (
    CreateSupportKnowledgeRequest,
    UpdateSupportKnowledgeRequest, 
    SupportKnowledgeResponse, 
    SupportKnowledgeListResponse,
    BulkDeleteRequest,
    BulkToggleRequest,
    SupportKnowledgeCategory,
    ExtractContentRequest,
    ExtractContentResponse,
    OptimizeContentRequest,
    OptimizeContentResponse,
    CheckDuplicateRequest,
    CheckDuplicateResponse
)
from backend.schemas.common import SuccessResponse
from backend.services.commerce.support_knowledge import SupportKnowledgeService, provide_support_kb_service
from backend.services.commerce.knowledge_parser import knowledge_parser_service
from backend.utils.noise_cleaner import noise_cleaner
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from pydantic_ai import Agent

logger = logging.getLogger("api-gateway")

class AdminSupportController(Controller):
    """Elite V2.2: Admin Controller for Support Knowledge Base management."""
    path = "/api/v1/admin/support/knowledge"
    guards = [PermissionGuard(PermissionEnum.PRODUCT_WRITE)] # Reuse product write for now or define SUPPORT_WRITE
    dependencies = {
        "kb_service": Provide(provide_support_kb_service),
        "kb_repo": Provide(provide_support_kb_repo),
    }

    @get("/")
    async def list_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        limit: int = 20,
        offset: int = 0,
        category: Optional[SupportKnowledgeCategory] = None,
        search: Optional[str] = None,
    ) -> SupportKnowledgeListResponse:
        return await kb_service.list_knowledge(
            db_session=db_session, 
            limit=limit, 
            offset=offset, 
            category=category, 
            search=search
        )

    @get("/{item_id:str}")
    async def get_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        item_id: str
    ) -> SupportKnowledgeResponse:
        return await kb_service.get_knowledge(db_session, item_id)

    @post("/")
    async def create_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        data: CreateSupportKnowledgeRequest
    ) -> SuccessResponse:
        res = await kb_service.create_knowledge(db_session, data)
        await db_session.commit()
        return res

    @patch("/{item_id:str}")
    async def update_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        item_id: str,
        data: UpdateSupportKnowledgeRequest
    ) -> SuccessResponse:
        res = await kb_service.update_knowledge(db_session, item_id, data)
        await db_session.commit()
        return res

    @delete("/{item_id:str}", status_code=200)
    async def delete_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        item_id: str
    ) -> SuccessResponse:
        res = await kb_service.delete_knowledge(db_session, item_id)
        await db_session.commit()
        return res

    @post("/bulk-delete")
    async def bulk_delete(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        data: BulkDeleteRequest
    ) -> SuccessResponse:
        res = await kb_service.bulk_delete(db_session, data)
        await db_session.commit()
        return res

    @post("/bulk-toggle")
    async def bulk_toggle(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        data: BulkToggleRequest
    ) -> SuccessResponse:
        res = await kb_service.bulk_toggle_active(db_session, data)
        await db_session.commit()
        return res

    @post("/reindex")
    async def reindex_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService
    ) -> SuccessResponse:
        """🚀 Elite V2.2: Force Re-indexing of entire brain."""
        res = await kb_service.reindex_all_knowledge(db_session)
        await db_session.commit()
        return res

    @post("/extract")
    async def extract_content(
        self,
        data: ExtractContentRequest
    ) -> ExtractContentResponse:
        """⚡ Elite V2.2: Instant neural extraction from URL, PDF, or HTML source."""
        source_type = data.source_type
        source_url = data.source_url
        if not source_url:
            return ExtractContentResponse(ok=False, error="Vui lòng nhập đường dẫn URL hoặc tải lên file tài liệu trước.")
        
        try:
            extracted_text = None
            if source_type == "PDF":
                extracted_text = await knowledge_parser_service.extract_text_from_pdf(source_url)
            elif source_type == "URL":
                extracted_text = await knowledge_parser_service.extract_text_from_url(source_url)
            elif source_type == "HTML":
                extracted_text = await knowledge_parser_service.extract_text_from_file(source_url)
                
            if extracted_text:
                return ExtractContentResponse(ok=True, text=extracted_text)
            else:
                return ExtractContentResponse(ok=False, error="Không thể trích xuất nội dung từ nguồn này. Vui lòng kiểm tra lại URL hoặc file.")
        except Exception as e:
            logger.error(f"[AdminSupportController] Extraction failed: {e}")
            return ExtractContentResponse(ok=False, error=f"Lỗi hệ thống khi trích xuất: {str(e)}")

    @post("/optimize")
    async def optimize_content(
        self,
        data: OptimizeContentRequest
    ) -> OptimizeContentResponse:
        """✨ Elite V2.2: Optimize and clean knowledge raw text using XOHI Neural Agent."""
        text = data.text
        if not text or not text.strip():
            return OptimizeContentResponse(ok=False, error="Vui lòng nhập hoặc bóc tách nội dung trước khi tối ưu hóa.")
            
        try:
            # Pre-processing Layer: Dọn sạch HTML tags, code artifacts, markdown fences
            # bằng cơ chế deterministic CPU (0 token AI cost) TRƯỚC khi nạp cho AI
            text = await noise_cleaner.clean(text, strip_html=True, strip_markdown=True)
            
            if not text or not text.strip():
                return OptimizeContentResponse(ok=False, error="Nội dung sau khi lọc rác hoàn toàn trống rỗng.")
            
            xohi_optimizer_agent = Agent()
            
            system_prompt = (
                "Bạn là Senior Knowledge Architect tại osmo, chuyên gia tối ưu hóa tri thức RAG.\n"
                "Nhiệm vụ tối cao của bạn là thực hiện HIỆU CHỈNH và LỌC BỎ các thông tin rác nhiễu khỏi văn bản gốc được cung cấp. "
                "TUYỆT ĐỐI CẤM VIẾT LẠI HOẶC TỰ Ý SÁNG TẠO THÊM NỘI DUNG MỚI.\n\n"
                "LUẬT HIỆU CHỈNH & LỌC BỎ (TUÂN THỦ 100%):\n"
                "1. BẢO TOÀN TRÍ CHẤT GỐC: Giữ nguyên vẹn 100% nội dung tri thức, cấu trúc ý chính, câu từ, và phong thái học thuật của văn bản gốc. Chỉ thực hiện cắt tỉa các phần rác nhiễu còn sót lại dưới đây.\n"
                "2. TRIỆT TIÊU RÁC IN ẤN & SỐ TRANG: Loại bỏ hoàn toàn các thông tin chỉ số trang (như 'Trang 1/2', 'Trang 2/2') và toàn bộ phần hướng dẫn xuất PDF, phím tắt in ấn ở cuối văn bản.\n"
                "3. DỌN SẠCH MÃ NGUỒN LẬP TRÌNH CÒN SÓT: Nếu còn sót các khối code lập trình, hãy tóm gọn thành 1 câu mô tả tự nhiên ngắn gọn.\n"
                "4. LÀM SẠCH LATEX TOÁN HỌC: Sửa đổi biểu thức LaTeX phức tạp thành sơ đồ văn bản trần đơn giản (dùng ký tự `->` hoặc `=>`).\n"
                "5. BẢO TOÀN TRÍCH DẪN (CITATION GUARD): Giữ lại nguyên vẹn các trích dẫn dạng `[cite: X]` hoặc `[X]`.\n"
                "6. ĐẦU RA TINH KHIẾT: Trả về văn bản gốc đã được làm sạch. Không nhúng trong code block ```markdown ... ```."
            )
            
            # Sử dụng trinity_bridge để chạy agent phi nghẽn, tự xoay key và chống quá tải
            # Sửa bug: Truyền system_prompt vào trinity_bridge.run để AI thực sự áp dụng!
            res = await trinity_bridge.run(xohi_optimizer_agent, text, role="brain", system_prompt=system_prompt)
            optimized_text = str(res)
            
            # Loại bỏ code block ```markdown ... ``` nếu AI vô tình thêm vào
            if optimized_text.startswith("```"):
                lines = optimized_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                optimized_text = "\n".join(lines).strip()
                
            return OptimizeContentResponse(ok=True, text=optimized_text)
        except Exception as e:
            logger.error(f"[AdminSupportController] Optimization failed: {e}")
            return OptimizeContentResponse(ok=False, error=f"Lỗi hệ thống khi tối ưu hóa: {str(e)}")

    @post("/check-duplicate")
    async def check_duplicate(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        data: CheckDuplicateRequest
    ) -> CheckDuplicateResponse:
        """✨ Elite V2.2: Semantically check if knowledge already exists in RAG vector DB."""
        text = data.text
        current_id = data.current_id
        threshold = data.threshold if data.threshold is not None else 0.82
        
        if not text or not text.strip():
            return CheckDuplicateResponse(ok=True, has_duplicate=False, duplicates=[])
            
        try:
            # Pre-processing Layer: Normalize text trước khi vector hóa pgvector
            cleaned_text = await noise_cleaner.clean(text, strip_html=True, strip_markdown=True)
            
            res = await kb_service.check_duplicate_knowledge(db_session, cleaned_text or text, current_id, threshold)
            
            duplicates_list = []
            for item in res.get("duplicates", []):
                duplicates_list.append(DuplicateItem(
                    id=str(item["id"]),
                    question=str(item["question"]),
                    match_score=float(item["match_score"]),
                    snippet=str(item["snippet"])
                ))
                
            return CheckDuplicateResponse(
                ok=True,
                has_duplicate=bool(res.get("has_duplicate", False)),
                duplicates=duplicates_list
            )
        except Exception as e:
            logger.error(f"[AdminSupportController] Duplicate check failed: {e}")
            return CheckDuplicateResponse(ok=False, error=f"Lỗi hệ thống khi kiểm tra trùng lặp: {str(e)}")



