import logging
import os
import json
import time
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import List, Optional

from litestar import Controller, get, post, patch, delete, Response, Request
from litestar.exceptions import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models.video_marketing import VideoScript, VideoScriptStyle
from backend.database.models.commerce import ProductBase
from backend.database.models.content import Article
from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.prompts import composer
from backend.services.video_marketing.product_resolver_service import product_resolver_service
from backend.services.video_marketing.script_generator_service import script_generator_service, VideoScriptModel
from backend.services.video_marketing.schemas import (
    GenerateScriptRequest, CreateStyleRequest, VideoScriptResponse, VideoStyleResponse, VideoScriptListResponse, UpdateScriptRequest, ScriptEvaluationReport
)
from backend.schemas.common import SuccessResponse
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

class VideoScriptController(Controller):
    """API Controller quản lý kịch bản Video Marketing và Dynamic Styles."""
    path = "/api/v1/video"
    tags = ["Video Marketing"]
    guards = [PermissionGuard(PermissionEnum.CONTENT_WRITE)]

    @post("/script/analyze-competitors")
    async def analyze_competitors(self, db_session: AsyncSession, data: GenerateScriptRequest) -> SuccessResponse:
        """Phân tích đối thủ cạnh tranh & điểm mạnh sản phẩm trước khi sinh kịch bản."""
        source_name = ""
        source_desc = ""
        
        if data.source_type == "product":
            if not data.product_id:
                raise HTTPException(status_code=400, detail="Vui lòng cung cấp product_id khi chọn nguồn sản phẩm.")
                
            key = product_resolver_service._extract_slug_or_id(data.product_id)
            prod_stmt = select(ProductBase).where(
                (ProductBase.id == key) | 
                (ProductBase.slug == key) | 
                (ProductBase.sku == key)
            ).where(ProductBase.deleted_at.is_(None))
            prod_res = await db_session.execute(prod_stmt)
            product = prod_res.scalar_one_or_none()
            if not product:
                raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")
            source_name = product.name
            source_desc = product.description or ""
            
        elif data.source_type == "article":
            if not data.article_id:
                raise HTTPException(status_code=400, detail="Vui lòng cung cấp article_id khi chọn nguồn bài viết.")
                
            art_stmt = select(Article).where(Article.id == data.article_id).where(Article.deleted_at.is_(None))
            art_res = await db_session.execute(art_stmt)
            article = art_res.scalar_one_or_none()
            if not article:
                raise HTTPException(status_code=404, detail="Không tìm thấy bài viết.")
            source_name = article.title
            source_desc = article.content or article.excerpt or ""
            
        elif data.source_type == "custom":
            if not data.description:
                raise HTTPException(status_code=400, detail="Vui lòng cung cấp mô tả chi tiết khi chọn nhập tay tự do.")
            source_name = data.description[:40] + "..." if len(data.description) > 40 else data.description
            source_desc = data.description
        else:
            raise HTTPException(status_code=400, detail="source_type không hợp lệ")

        await db_session.close()

        try:
            analysis = await script_generator_service.analyze_competitors(source_name, source_desc)
            return SuccessResponse(message="Phân tích đối thủ thành công!", data=analysis)
        except Exception as e:
            logger.error(f"⚠️ [VideoController] Competitor analysis failed: {e}")
            fallback = {
                "competitor_weaknesses": [
                    "Đối thủ chưa tối ưu trải nghiệm cho khách hàng Việt Nam",
                    "Chi phí cao, giá bán chưa tối ưu so với giá trị thực tế",
                    "Thiếu sự hỗ trợ trực tiếp và đồng hành chuyên nghiệp"
                ],
                "our_strengths": [
                    "Giải pháp trực diện nỗi đau của khách hàng",
                    "Tối ưu chi phí tốt nhất thị trường",
                    "Đồng hành chuyên nghiệp 24/7"
                ],
                "core_message": f"Sản phẩm {source_name} là sự lựa chọn vượt trội nhất dành cho bạn!"
            }
            return SuccessResponse(message="Phân tích đối thủ (Fallback) thành công!", data=fallback)

    @post("/script/generate")
    async def generate_script(self, db_session: AsyncSession, data: GenerateScriptRequest) -> SuccessResponse[VideoScriptResponse]:
        """Sinh kịch bản video từ sản phẩm, bài viết hoặc mô tả, có phân tích đối thủ và cấu hình khung hình/thời lượng."""
        source_context = ""
        source_name = ""
        source_desc = ""
        product_id = None
        
        # 1. Giải quyết ngữ cảnh nguồn dựa trên source_type
        if data.source_type == "product":
            if not data.product_id:
                raise HTTPException(status_code=400, detail="Vui lòng cung cấp product_id khi chọn nguồn sản phẩm.")
                
            key = product_resolver_service._extract_slug_or_id(data.product_id)
            prod_stmt = select(ProductBase).where(
                (ProductBase.id == key) | 
                (ProductBase.slug == key) | 
                (ProductBase.sku == key)
            ).where(ProductBase.deleted_at.is_(None))
            prod_res = await db_session.execute(prod_stmt)
            product = prod_res.scalar_one_or_none()
            
            if not product:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy sản phẩm với khóa: {data.product_id}")
                
            product_id = product.id
            source_context = await product_resolver_service.get_product_context(product.id, db_session)
            source_name = product.name
            source_desc = product.description or ""
            
        elif data.source_type == "article":
            if not data.article_id:
                raise HTTPException(status_code=400, detail="Vui lòng cung cấp article_id khi chọn nguồn bài viết.")
                
            art_stmt = select(Article).where(Article.id == data.article_id).where(Article.deleted_at.is_(None))
            art_res = await db_session.execute(art_stmt)
            article = art_res.scalar_one_or_none()
            
            if not article:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy bài viết với ID: {data.article_id}")
                
            source_context = f"TIÊU ĐỀ BÀI VIẾT: {article.title}\n\nTÓM TẮT: {article.excerpt or ''}\n\nNỘI DUNG CHÍNH:\n{article.content or ''}"
            source_name = article.title
            source_desc = article.content or article.excerpt or ""
            
        elif data.source_type == "custom":
            if not data.description:
                raise HTTPException(status_code=400, detail="Vui lòng cung cấp mô tả chi tiết khi chọn nhập tay tự do.")
                
            source_context = f"MÔ TẢ CHI TIẾT Ý TƯỞNG / SẢN PHẨM / DỊCH VỤ:\n{data.description}"
            source_name = data.description[:40] + "..." if len(data.description) > 40 else data.description
            source_desc = data.description
            
        else:
            raise HTTPException(status_code=400, detail="source_type không hợp lệ (hỗ trợ: product, article, custom)")

        if not source_context:
            raise HTTPException(status_code=400, detail="Không thể phân giải ngữ cảnh nguồn để sinh kịch bản.")

        # 1.1 Lấy phong cách kịch bản từ database trước khi giải phóng session
        style = None
        if data.style_id:
            style_stmt = select(VideoScriptStyle).where(VideoScriptStyle.id == data.style_id).where(VideoScriptStyle.is_active == True)
            style_res = await db_session.execute(style_stmt)
            style = style_res.scalar_one_or_none()

        # Giải phóng connection về pool ngay lập tức trước khi gọi AI/Search tốn thời gian
        await db_session.close()

        # 2. Phân tích đối thủ cạnh tranh bằng Google Search & AI phản biện (nếu chưa có từ client)
        competitor_analysis = None
        if data.competitor_analysis:
            competitor_analysis = data.competitor_analysis.model_dump()
        else:
            try:
                competitor_analysis = await script_generator_service.analyze_competitors(source_name, source_desc)
            except Exception as e:
                logger.error(f"⚠️ [VideoController] Competitor analysis failed: {e}. Proceeding with default template.")

        # 3. Sinh kịch bản qua AI Core
        try:
            generated_script = await script_generator_service.generate_script(
                source_context=source_context,
                style=style,
                aspect_ratio=data.aspect_ratio or "9:16",
                target_duration=data.target_duration or 30,
                competitor_analysis=competitor_analysis
            )
        except Exception as e:
            logger.error(f"❌ [VideoController] Script generation failed: {e}")
            raise HTTPException(status_code=400, detail=f"Lỗi khi gọi AI sinh kịch bản: {str(e)}")

        # 4. Lưu kịch bản vào cơ sở dữ liệu (sử dụng session mới để không giữ connection quá lâu)
        from backend.database.alchemy_config import alchemy_config
        from backend.database import current_tenant_id
        active_tenant = current_tenant_id.get() or "osmo.vn"

        async with alchemy_config.create_session_maker()() as new_session:
            script_db = VideoScript(
                product_id=product_id,
                style_id=data.style_id,
                title=generated_script.title,
                structured_script=generated_script.model_dump(),
                tenant_id=active_tenant
            )
            new_session.add(script_db)
            await new_session.commit()
            
            # Trích xuất thông tin cần thiết trước khi đóng session
            script_id = script_db.id
            product_id_db = script_db.product_id
            style_id_db = script_db.style_id
            title_db = script_db.title
            created_at_iso = script_db.created_at.isoformat()
        
        # 5. Trả về kết quả chuẩn
        result = VideoScriptResponse(
            id=script_id,
            product_id=product_id_db,
            style_id=style_id_db,
            title=title_db,
            structured_script=generated_script,
            created_at=created_at_iso
        )
        
        return SuccessResponse(
            message="Sinh kịch bản video marketing thành công!",
            data=result
        )

    @get("/script/{script_id:str}")
    async def get_script(self, db_session: AsyncSession, script_id: str) -> SuccessResponse[VideoScriptResponse]:
        """Lấy chi tiết kịch bản đã sinh."""
        stmt = select(VideoScript).where(VideoScript.id == script_id).where(VideoScript.deleted_at == None)
        res = await db_session.execute(stmt)
        script = res.scalar_one_or_none()
        
        if not script:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy kịch bản với ID: {script_id}")
            
        result = VideoScriptResponse(
            id=script.id,
            product_id=script.product_id,
            style_id=script.style_id,
            title=script.title,
            structured_script=VideoScriptModel(**script.structured_script),
            created_at=script.created_at.isoformat()
        )
        return SuccessResponse(data=result)

    @get("/styles")
    async def list_styles(self, db_session: AsyncSession) -> SuccessResponse[List[VideoStyleResponse]]:
        """Lấy danh sách các phong cách/xu hướng video ngắn đang hoạt động."""
        stmt = select(VideoScriptStyle).where(VideoScriptStyle.is_active == True)
        res = await db_session.execute(stmt)
        styles = res.scalars().all()
        
        result = [
            VideoStyleResponse(
                id=s.id,
                name=s.name,
                platform=s.platform,
                hook_template=s.hook_template,
                style_instruction=s.style_instruction,
                is_active=s.is_active
            )
            for s in styles
        ]
        return SuccessResponse(data=result)

    @post("/styles")
    async def create_or_update_style(self, db_session: AsyncSession, data: CreateStyleRequest) -> SuccessResponse[VideoStyleResponse]:
        """Tạo mới hoặc cập nhật thông tin một phong cách kịch bản/xu hướng."""
        stmt = select(VideoScriptStyle).where(VideoScriptStyle.id == data.id)
        res = await db_session.execute(stmt)
        style = res.scalar_one_or_none()
        
        if not style:
            style = VideoScriptStyle(id=data.id)
            db_session.add(style)
            msg = "Thêm phong cách video mới thành công!"
        else:
            msg = "Cập nhật phong cách video thành công!"
            
        style.name = data.name
        style.platform = data.platform
        style.hook_template = data.hook_template
        style.style_instruction = data.style_instruction
        style.is_active = data.is_active
        
        await db_session.commit()
        
        result = VideoStyleResponse(
            id=style.id,
            name=style.name,
            platform=style.platform,
            hook_template=style.hook_template,
            style_instruction=style.style_instruction,
            is_active=style.is_active
        )
        return SuccessResponse(message=msg, data=result)

    @get("/script/{script_id:str}/export")
    async def export_script(self, request: Request, db_session: AsyncSession, script_id: str) -> Response:
        """Xuất kịch bản ra định dạng Markdown chuyên nghiệp tối ưu cho AI & Con người."""
        from backend.database import current_tenant_id
        active_tenant = current_tenant_id.get() or "osmo.vn"

        stmt = select(VideoScript).where(VideoScript.id == script_id).where(VideoScript.tenant_id == active_tenant).where(VideoScript.deleted_at == None)
        res = await db_session.execute(stmt)
        script = res.scalar_one_or_none()
        
        if not script:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy kịch bản với ID: {script_id}")
            
        data = script.structured_script
        scenes = data.get("scenes", [])
        
        # Xác định host hiện tại để chuyển đổi các đường dẫn tương đối thành tuyệt đối
        host = request.headers.get("host", "admin.osmo.vn")
        scheme = "https" if request.url.scheme == "https" or "https" in request.headers.get("x-forwarded-proto", "") else "http"
        base_url = f"{scheme}://{host}"
        
        # Tạo danh sách phân cảnh
        updated_scenes = []
        for scene in scenes:
            scene_copy = dict(scene)
            # Remove legacy / audio cue fields
            scene_copy.pop("audio_cue", None)
            updated_scenes.append(scene_copy)
            
        md = []
        # 1. YAML Front Matter (Metadata chuẩn cho LLM/Gemini Pro parse nhanh)
        md.append("---")
        md.append(f"id: {script_id}")
        md.append(f"title: {json.dumps(script.title, ensure_ascii=False)}")
        md.append(f"style: {json.dumps(data.get('style_name', 'N/A'), ensure_ascii=False)}")
        md.append(f"target_audience: {json.dumps(data.get('target_audience', 'N/A'), ensure_ascii=False)}")
        md.append(f"total_duration: {data.get('total_duration', 0)}")
        md.append(f"exported_at: \"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\"")
        md.append("---")
        md.append("")
        
        # 2. Nội dung hiển thị đẹp mắt cho con người
        md.append(f"# KỊCH BẢN VIDEO: {script.title.upper()}")
        md.append("")
        md.append("## THÔNG TIN TỔNG QUAN")
        md.append(f"- **Phong cách/Xu hướng**: {data.get('style_name', 'N/A')}")
        md.append(f"- **Đối tượng khách hàng**: {data.get('target_audience', 'N/A')}")
        md.append(f"- **Tổng thời lượng**: {data.get('total_duration', 0)} giây")
        if data.get("notes"):
            md.append(f"- **Ghi chú đạo diễn (Tổng quát)**: {data.get('notes')}")
        md.append("")
        md.append("## PHÂN CẢNH CHI TIẾT (STORYBOARD)")
        md.append("")
        
        for scene in updated_scenes:
            md.append(f"### Phân Cảnh {scene.get('scene_number')} ({scene.get('duration')}s)")
            md.append(f"- **Mô tả hình ảnh (Visuals)**: {scene.get('visual_description')}")
            md.append(f"- **Lời thoại (Voiceover)**: \"{scene.get('voiceover')}\"")
            if scene.get("scene_notes"):
                md.append(f"- **Chuyển động camera & Ghi chú**: {scene.get('scene_notes')}")
            md.append("")
            md.append("-" * 40)
            md.append("")
            
        # 3. Khối JSON Thô (Dành cho việc Import trực tiếp vào Gemini Pro hoặc AI Agents)
        md.append("## DỮ LIỆU CẤU TRÚC JSON (RAW DATA FOR AI IMPORT)")
        md.append("Sao chép khối JSON dưới đây nạp thẳng vào LLM/API để phục vụ việc tự động hóa xử lý mà không cần parse text:")
        md.append("```json")
        md.append(json.dumps({
            "id": script_id,
            "title": script.title,
            "style_name": data.get('style_name'),
            "target_audience": data.get('target_audience'),
            "total_duration": data.get('total_duration'),
            "notes": data.get('notes'),
            "scenes": updated_scenes
        }, indent=2, ensure_ascii=False))
        md.append("```")
        
        md_content = "\n".join(md)
        
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=script_{script_id}.md"}
        )

    @get("/scripts")
    async def list_scripts(
        self,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None
    ) -> VideoScriptListResponse:
        """Lấy danh sách các kịch bản video đã tạo với phân trang & tìm kiếm."""
        from backend.database import current_tenant_id
        active_tenant = current_tenant_id.get() or "osmo.vn"

        stmt = select(VideoScript).options(
            selectinload(VideoScript.product),
            selectinload(VideoScript.style)
        ).where(VideoScript.deleted_at.is_(None)).where(VideoScript.tenant_id == active_tenant)
        
        if search:
            stmt = stmt.where(VideoScript.title.ilike(f"%{search}%"))
            
        stmt = stmt.order_by(VideoScript.created_at.desc())
        
        # Query total count
        count_stmt = select(func.count()).select_from(VideoScript).where(VideoScript.deleted_at.is_(None)).where(VideoScript.tenant_id == active_tenant)
        if search:
            count_stmt = count_stmt.where(VideoScript.title.ilike(f"%{search}%"))
            
        total_res = await db_session.execute(count_stmt)
        total = total_res.scalar_one() or 0
        
        # Query list
        list_stmt = stmt.limit(limit).offset(offset)
        res = await db_session.execute(list_stmt)
        scripts = res.scalars().all()
        
        data_list = []
        for script in scripts:
            # Safely parse structured script
            structured = script.structured_script
            if isinstance(structured, str):
                structured = json.loads(structured)
            
            data_list.append(
                VideoScriptResponse(
                    id=script.id,
                    product_id=script.product_id,
                    product_name=script.product.name if script.product else None,
                    style_id=script.style_id,
                    style_name=script.style.name if script.style else None,
                    style_platform=script.style.platform if script.style else None,
                    title=script.title,
                    structured_script=VideoScriptModel(**structured),
                    created_at=script.created_at.isoformat()
                )
            )
            
        return VideoScriptListResponse(data=data_list, total=total)

    @delete("/script/{script_id:str}", status_code=200)
    async def delete_script(self, db_session: AsyncSession, script_id: str) -> SuccessResponse:
        """Soft delete a video script."""
        from backend.database import current_tenant_id
        active_tenant = current_tenant_id.get() or "osmo.vn"

        stmt = select(VideoScript).where(VideoScript.id == script_id).where(VideoScript.tenant_id == active_tenant).where(VideoScript.deleted_at.is_(None))
        res = await db_session.execute(stmt)
        script = res.scalar_one_or_none()
        
        if not script:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy kịch bản với ID: {script_id}")
            
        script.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()
        return SuccessResponse(message="Xóa kịch bản video thành công!")

    @patch("/script/{script_id:str}")
    async def update_script(
        self,
        db_session: AsyncSession,
        script_id: str,
        data: UpdateScriptRequest
    ) -> SuccessResponse[VideoScriptResponse]:
        """Cập nhật thông tin chi tiết (tiêu đề, ghi chú, phân cảnh) của kịch bản."""
        from backend.database import current_tenant_id
        active_tenant = current_tenant_id.get() or "osmo.vn"

        stmt = select(VideoScript).where(VideoScript.id == script_id).where(VideoScript.tenant_id == active_tenant).where(VideoScript.deleted_at.is_(None))
        res = await db_session.execute(stmt)
        script = res.scalar_one_or_none()
        
        if not script:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy kịch bản với ID: {script_id}")
            
        if data.title is not None:
            script.title = data.title
            
        if data.structured_script is not None:
            script.structured_script = data.structured_script.model_dump()
            
        await db_session.commit()
        
        # Reload relationships to build response
        stmt_refresh = select(VideoScript).options(
            selectinload(VideoScript.product),
            selectinload(VideoScript.style)
        ).where(VideoScript.id == script_id)
        res_refresh = await db_session.execute(stmt_refresh)
        script_refreshed = res_refresh.scalar_one()
        
        result = VideoScriptResponse(
            id=script_refreshed.id,
            product_id=script_refreshed.product_id,
            product_name=script_refreshed.product.name if script_refreshed.product else None,
            style_id=script_refreshed.style_id,
            style_name=script_refreshed.style.name if script_refreshed.style else None,
            style_platform=script_refreshed.style.platform if script_refreshed.style else None,
            title=script_refreshed.title,
            structured_script=VideoScriptModel(**script_refreshed.structured_script),
            created_at=script_refreshed.created_at.isoformat()
        )
        
        return SuccessResponse(
            message="Cập nhật kịch bản video thành công!",
            data=result
        )

    @post("/script/{script_id:str}/evaluate")
    async def evaluate_script(self, db_session: AsyncSession, script_id: str) -> SuccessResponse[ScriptEvaluationReport]:
        """Đánh giá kịch bản video theo 5 chuẩn chuyên nghiệp quốc tế."""
        from backend.database import current_tenant_id
        active_tenant = current_tenant_id.get() or "osmo.vn"
        
        stmt = select(VideoScript).where(VideoScript.id == script_id).where(VideoScript.tenant_id == active_tenant).where(VideoScript.deleted_at == None)
        res = await db_session.execute(stmt)
        script = res.scalar_one_or_none()
        
        if not script:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy kịch bản với ID: {script_id}")
        
        # 1. Chuẩn bị kịch bản text để gửi cho LLM
        model_data = VideoScriptModel(**script.structured_script)
        
        script_text = f"TIÊU ĐỀ: {model_data.title}\n"
        script_text += f"PHONG CÁCH: {model_data.style_name}\n"
        script_text += f"ĐỐI TƯỢNG: {model_data.target_audience}\n"
        
        target_dur = model_data.target_duration or 30
        script_text += f"THỜI LƯỢNG MỤC TIÊU: {target_dur} giây\n"
        script_text += f"TỔNG THỜI LƯỢNG THỰC TẾ: {model_data.total_duration} giây\n"
        
        script_text += "DANH SÁCH PHÂN CẢNH:\n"
        for scene in model_data.scenes:
            script_text += f"--- CẢNH {scene.scene_number} ({scene.duration}s) ---\n"
            script_text += f"Visual: {scene.visual_description}\n"
            script_text += f"Voiceover: {scene.voiceover}\n"
            if scene.scene_notes:
                script_text += f"Notes: {scene.scene_notes}\n"
        
        # 2. Gọi AI để đánh giá (sử dụng trinity_bridge)
        try:
            prompt_content = composer.compose("video_script_evaluation")
            eval_agent = Agent(
                output_type=ScriptEvaluationReport,
                retries=2
            )
            report = await trinity_bridge.run(
                agent=eval_agent,
                prompt=script_text,
                system_prompt=prompt_content,
                role="brain",
                per_model_timeout=35.0
            )
            
            # 3. Cập nhật kết quả vào database
            model_dump = model_data.model_dump()
            model_dump["evaluation"] = report.model_dump()
            script.structured_script = model_dump
            await db_session.commit()
            
            return SuccessResponse(
                message="Đánh giá kịch bản thành công!",
                data=report
            )
        except Exception as e:
            logger.error(f"❌ [ScriptEvaluation] Error: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi khi đánh giá kịch bản: {str(e)}")

    @post("/script/{script_id:str}/optimize")
    async def optimize_script(self, db_session: AsyncSession, script_id: str) -> SuccessResponse[VideoScriptResponse]:
        """Tự động tối ưu/sửa lỗi kịch bản dựa trên báo cáo đánh giá lỗi."""
        from backend.database import current_tenant_id
        active_tenant = current_tenant_id.get() or "osmo.vn"
        
        stmt = select(VideoScript).where(VideoScript.id == script_id).where(VideoScript.tenant_id == active_tenant).where(VideoScript.deleted_at == None)
        res = await db_session.execute(stmt)
        script = res.scalar_one_or_none()
        
        if not script:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy kịch bản với ID: {script_id}")
            
        model_data = VideoScriptModel(**script.structured_script)
        
        is_valid_report = False
        if model_data.evaluation and isinstance(model_data.evaluation, dict):
            required_keys = {
                "hook_retention", "audio_visual_harmony", "ai_generation_viability", 
                "platform_optimization", "brand_integrity", "duration_compliance"
            }
            if required_keys.issubset(model_data.evaluation.keys()):
                is_valid_report = True

        if not is_valid_report:
            # Tự động thực hiện đánh giá kịch bản trước nếu báo cáo chưa có hoặc không hợp lệ
            logger.info(f"🔄 [ScriptOptimization] Evaluation report missing or invalid for script {script_id}. Running auto-evaluation...")
            eval_script_text = f"TIÊU ĐỀ: {model_data.title}\n"
            eval_script_text += f"PHONG CÁCH: {model_data.style_name}\n"
            eval_script_text += f"ĐỐI TƯỢNG: {model_data.target_audience}\n"
            for scene in model_data.scenes:
                eval_script_text += f"--- CẢNH {scene.scene_number} ({scene.duration}s) ---\n"
                eval_script_text += f"Visual: {scene.visual_description}\n"
                eval_script_text += f"Voiceover: {scene.voiceover}\n"
                if scene.scene_notes:
                    eval_script_text += f"Notes: {scene.scene_notes}\n"
            
            try:
                prompt_content = composer.compose("video_script_evaluation")
                eval_agent = Agent(
                    output_type=ScriptEvaluationReport,
                    retries=2
                )
                evaluation_report = await trinity_bridge.run(
                    agent=eval_agent,
                    prompt=eval_script_text,
                    system_prompt=prompt_content,
                    role="brain",
                    per_model_timeout=35.0
                )
                
                # Lưu báo cáo đánh giá mới vào kịch bản
                model_data.evaluation = evaluation_report.model_dump()
                script.structured_script = model_data.model_dump()
                await db_session.commit()
            except Exception as e:
                logger.error(f"❌ [ScriptOptimization] Auto-evaluation failed: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Không thể tự động đánh giá kịch bản trước khi tối ưu: {str(e)}"
                )
        else:
            evaluation_report = ScriptEvaluationReport(**model_data.evaluation)
        
        script_text = f"TIÊU ĐỀ: {model_data.title}\n"
        script_text += f"PHONG CÁCH: {model_data.style_name}\n"
        script_text += f"ĐỐI TƯỢNG: {model_data.target_audience}\n"
        if model_data.target_duration:
            script_text += f"THỜI LƯỢNG MỤC TIÊU: {model_data.target_duration} giây\n"
            script_text += f"TỔNG THỜI LƯỢNG THỰC TẾ: {model_data.total_duration} giây\n"
            
        script_text += "DANH SÁCH PHÂN CẢNH HIỆN TẠI:\n"
        for scene in model_data.scenes:
            script_text += f"--- CẢNH {scene.scene_number} ({scene.duration}s) ---\n"
            script_text += f"Visual: {scene.visual_description}\n"
            script_text += f"Voiceover: {scene.voiceover}\n"
            if scene.scene_notes:
                script_text += f"Notes: {scene.scene_notes}\n"
                
        # Thêm phần báo cáo lỗi
        error_context = "BÁO CÁO LỖI KỸ THUẬT PHÁT HIỆN:\n"
        for field in ["hook_retention", "audio_visual_harmony", "ai_generation_viability", "platform_optimization", "brand_integrity", "duration_compliance"]:
            crit = getattr(evaluation_report, field)
            if crit.score < 8:
                error_context += f"- Tiêu chí '{field}' (Điểm: {crit.score}/10):\n"
                error_context += f"  + Lỗi: {', '.join(crit.cons)}\n"
                error_context += f"  + Đề xuất sửa: {', '.join(crit.suggestions)}\n"
        
        input_prompt = f"{script_text}\n\n{error_context}"
        
        try:
            # 2. Gọi AI để tối ưu hóa
            prompt_content = composer.compose("video_script_optimization")
            opt_agent = Agent(
                output_type=VideoScriptModel,
                retries=2
            )
            from backend.services.video_marketing.script_generator_service import strict_duration_var
            token = strict_duration_var.set(True)
            try:
                optimized_script = await trinity_bridge.run(
                    agent=opt_agent,
                    prompt=input_prompt,
                    system_prompt=prompt_content,
                    role="brain",
                    per_model_timeout=35.0
                )
            finally:
                strict_duration_var.reset(token)
            
            # Tự động cập nhật thuộc tính bổ sung
            optimized_script.competitor_analysis = model_data.competitor_analysis
            optimized_script.aspect_ratio = model_data.aspect_ratio
            if optimized_script.target_duration is None:
                optimized_script.target_duration = model_data.target_duration
            
            # 3. Chạy lại đánh giá tự động trên kịch bản mới này để cập nhật điểm mới luôn!
            eval_prompt_content = composer.compose("video_script_evaluation")
            eval_agent = Agent(
                output_type=ScriptEvaluationReport,
                retries=2
            )
            
            new_script_text = f"TIÊU ĐỀ: {optimized_script.title}\n"
            new_script_text += f"PHONG CÁCH: {optimized_script.style_name}\n"
            new_script_text += f"ĐỐI TƯỢNG: {optimized_script.target_audience}\n"
            
            target_dur = optimized_script.target_duration or 30
            new_script_text += f"THỜI LƯỢNG MỤC TIÊU: {target_dur} giây\n"
            new_script_text += f"TỔNG THỜI LƯỢNG THỰC TẾ: {optimized_script.total_duration} giây\n"
            
            new_script_text += "DANH SÁCH PHÂN CẢNH:\n"
            for scene in optimized_script.scenes:
                new_script_text += f"--- CẢNH {scene.scene_number} ({scene.duration}s) ---\n"
                new_script_text += f"Visual: {scene.visual_description}\n"
                new_script_text += f"Voiceover: {scene.voiceover}\n"
                if scene.scene_notes:
                    new_script_text += f"Notes: {scene.scene_notes}\n"
            
            new_report = await trinity_bridge.run(
                agent=eval_agent,
                prompt=new_script_text,
                system_prompt=eval_prompt_content,
                role="brain",
                per_model_timeout=35.0
            )
            
            optimized_script.evaluation = new_report.model_dump()
            
            # 4. Lưu vào database
            script.title = optimized_script.title
            script.structured_script = optimized_script.model_dump()
            await db_session.commit()
            
            # Refresh to populate relationships
            stmt_refresh = select(VideoScript).options(
                selectinload(VideoScript.product),
                selectinload(VideoScript.style)
            ).where(VideoScript.id == script_id)
            res_refresh = await db_session.execute(stmt_refresh)
            script_refreshed = res_refresh.scalar_one()
            
            result = VideoScriptResponse(
                id=script_refreshed.id,
                product_id=script_refreshed.product_id,
                product_name=script_refreshed.product.name if script_refreshed.product else None,
                style_id=script_refreshed.style_id,
                style_name=script_refreshed.style.name if script_refreshed.style else None,
                style_platform=script_refreshed.style.platform if script_refreshed.style else None,
                title=script_refreshed.title,
                structured_script=optimized_script,
                created_at=script_refreshed.created_at.isoformat()
            )
            
            return SuccessResponse(
                message="Tối ưu kịch bản và tự động cập nhật điểm số mới thành công!",
                data=result
            )
        except Exception as e:
            logger.error(f"❌ [ScriptOptimization] Error: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi khi tối ưu hóa kịch bản: {str(e)}")



