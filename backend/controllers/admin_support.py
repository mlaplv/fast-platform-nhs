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
            text = await noise_cleaner.clean(text, strip_html=True, strip_markdown=False)
            
            if not text or not text.strip():
                return OptimizeContentResponse(ok=False, error="Nội dung sau khi lọc rác hoàn toàn trống rỗng.")
            
            xohi_optimizer_agent = Agent()
            
            system_prompt = (
                "Bạn là một chuyên gia quản trị tri thức (Knowledge Manager) cao cấp, chuyên môn hóa tài liệu khoa học kỹ thuật và RAG Knowledge Base.\n"
                "Nhiệm vụ của bạn là phân tích, làm sạch, hệ thống hóa tài liệu chuyên sâu được cung cấp thành một bài viết Tri thức Doanh nghiệp (Corporate Knowledge Base) chuẩn mực, dễ tra cứu và sao chép. BẮT BUỘC tuân thủ các nguyên tắc sau:\n\n"
                "1. PHONG THÁI & HÀNH VĂN (KNOWLEDGE ARCHITECT STANDARDS):\n"
                "   - Sử dụng ngôn ngữ khách quan, khoa học, súc tích, mang tính chuyên môn cao.\n"
                "   - Tuyệt đối KHÔNG có các từ ngữ dẫn dắt mang tính đàm thoại hay giao tiếp (ví dụ: 'Dưới đây là...', 'Chào bạn...', 'Hy vọng tài liệu này giúp ích...').\n"
                "   - Viết ở ngôi thứ ba, giọng văn trang trọng và uy tín.\n\n"
                "2. LÀM SẠCH DỮ LIỆU TUYỆT ĐỐI:\n"
                "   - Loại bỏ hoàn toàn các yếu tố thừa: số trang, đầu trang/chân trang lặp lại, hướng dẫn in ấn, câu từ tiếp thị, quảng bá quá đà.\n"
                "   - Chỉ giữ lại thông tin kỹ thuật, khoa học và giá trị cốt lõi của tài liệu.\n\n"
                "3. CẤU TRÚC HÓA BẰNG MARKDOWN CHUYÊN NGHIỆP:\n"
                "   - Sử dụng tiêu đề phân cấp hợp lý (# H1 cho Tên tài liệu/Chủ đề chính, ## H2 cho các mục lớn, ### H3 cho các nhánh nhỏ).\n"
                "   - Sử dụng danh sách có ký hiệu đầu dòng (bullet points) để tóm tắt các đặc tính, thuộc tính kỹ thuật.\n"
                "   - BẮT BUỘC sử dụng bảng (Markdown Table) đối với các thông số kỹ thuật, tiêu chuẩn chất lượng, hoặc dữ liệu cần so sánh đối chiếu.\n\n"
                "4. CHIA PHÂN KHU LOGIC TRA CỨU:\n"
                "   Bài viết Knowledge Base phải được sắp xếp khoa học theo các phần tương ứng sau (nếu tài liệu gốc có thông tin):\n"
                "   - **Tổng Quan / Định Nghĩa**: Khái niệm cốt lõi.\n"
                "   - **Cơ Chế Hoạt Động**: Mô tả cơ chế khoa học của thành phần/sản phẩm.\n"
                "   - **Thông Số Kỹ Thuật / Tiêu Chuẩn Nguyên Liệu**: (Trình bày bằng bảng).\n"
                "   - **Ứng Dụng Thực Tiễn / Hướng Dẫn**: Cách dùng, liều lượng, trường hợp chỉ định.\n"
                "   - **Lưu Ý / Chống Chỉ Định**.\n\n"
                "5. BẢO TOÀN GIÁ TRỊ GỐC:\n"
                "   - Không tự ý sáng tạo hay thêm bớt thông tin sai lệch so với tài liệu gốc.\n"
                "   - Đảm bảo đầu ra là một tài liệu tri thức tinh khiết, sẵn sàng đồng bộ vào Cơ sở dữ liệu RAG của doanh nghiệp.\n"
                "   Lưu ý: Không bọc văn bản trong các khối mã ```markdown ... ```, hãy xuất trực tiếp nội dung dưới định dạng Markdown thô."
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

    @get("/sandbox")
    async def list_sandbox_knowledge(
        self,
        db_session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> SupportKnowledgeListResponse:
        """Elite V3.5: List all sandboxed auto-learned items waiting for admin review."""
        from sqlalchemy import select, func, and_
        from backend.database.models.system import SupportKnowledge
        
        conditions = [
            SupportKnowledge.deleted_at == None,
            SupportKnowledge.source_type == "AUTO_LEARNED",
            SupportKnowledge.is_active == False
        ]
        
        stmt = select(SupportKnowledge).where(and_(*conditions)).limit(limit).offset(offset).order_by(SupportKnowledge.created_at.desc())
        items = (await db_session.execute(stmt)).scalars().all()
        
        count_stmt = select(func.count(SupportKnowledge.id)).where(and_(*conditions))
        total = await db_session.scalar(count_stmt) or 0
        
        data = [
            SupportKnowledgeResponse(
                id=m.id,
                category=m.category,
                question=m.question,
                answer=m.answer,
                is_active=m.is_active,
                priority=m.priority,
                tags=m.tags,
                product_id=m.product_id,
                source_type=m.source_type,
                source_url=m.source_url,
                created_at=m.created_at.isoformat()
            ) for m in items
        ]
        
        return SupportKnowledgeListResponse(data=data, total=total)

    @post("/sandbox/{item_id:str}/approve")
    async def approve_sandbox(
        self,
        db_session: AsyncSession,
        item_id: str
    ) -> SuccessResponse:
        """Elite V3.5: Approve and vector-index a sandbox item thưa sếp."""
        from backend.services.commerce.self_learning import helen_self_learning
        ok = await helen_self_learning.approve_sandbox_item(db_session, item_id)
        if not ok:
            return SuccessResponse(ok=False)
        return SuccessResponse(ok=True, id=item_id)

    @post("/sandbox/{item_id:str}/reject")
    async def reject_sandbox(
        self,
        db_session: AsyncSession,
        item_id: str
    ) -> SuccessResponse:
        """Elite V3.5: Reject and soft-delete a sandbox item thưa sếp."""
        from backend.services.commerce.self_learning import helen_self_learning
        ok = await helen_self_learning.reject_sandbox_item(db_session, item_id)
        if not ok:
            return SuccessResponse(ok=False)
        return SuccessResponse(ok=True, id=item_id)



