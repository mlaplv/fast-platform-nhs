import logging
import os
import json
import subprocess
import time
import shutil
import re
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import PIL.Image
import PIL.ImageDraw
import edge_tts
from litestar import Controller, get, post, patch, delete, Response, Request
from litestar.exceptions import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models.video_marketing import VideoScript, VideoScriptStyle
from backend.database.models.commerce import ProductBase
from backend.database.models.content import Article
from backend.services.video_marketing.product_resolver_service import product_resolver_service
from backend.services.video_marketing.script_generator_service import script_generator_service, VideoScriptModel
from backend.services.video_marketing.schemas import (
    GenerateScriptRequest, CreateStyleRequest, VideoScriptResponse, VideoStyleResponse, VideoScriptListResponse, UpdateScriptRequest
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

        # 2. Phân tích đối thủ cạnh tranh bằng Google Search & AI phản biện
        competitor_analysis = None
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
        async with alchemy_config.create_session_maker()() as new_session:
            script_db = VideoScript(
                product_id=product_id,
                style_id=data.style_id,
                title=generated_script.title,
                structured_script=generated_script.model_dump(),
                tenant_id="smartshop"
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
        stmt = select(VideoScript).where(VideoScript.id == script_id).where(VideoScript.deleted_at == None)
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
        
        # Tạo danh sách phân cảnh đã nâng cấp đường dẫn tuyệt đối cho ảnh và audio
        updated_scenes = []
        for scene in scenes:
            scene_copy = dict(scene)
            
            # Chuyển đổi image_url tương đối thành tuyệt đối
            img_url = scene_copy.get("image_url")
            if img_url:
                if img_url.startswith("/"):
                    img_url = f"{base_url}{img_url}"
                scene_copy["image_url"] = img_url
            else:
                scene_copy["image_url"] = ""
                
            # Tạo đường dẫn tải file âm thanh TTS trực tiếp cho phân cảnh (cả giọng Nam và Nữ)
            voiceover_text = scene_copy.get("voiceover", "")
            if voiceover_text:
                encoded_text = urllib.parse.quote(voiceover_text)
                scene_copy["voiceover_audio_hoaimy"] = f"{base_url}/api/v1/client/tts/stream?text={encoded_text}&voice=vi-VN-HoaiMyNeural"
                scene_copy["voiceover_audio_namminh"] = f"{base_url}/api/v1/client/tts/stream?text={encoded_text}&voice=vi-VN-NamMinhNeural"
            else:
                scene_copy["voiceover_audio_hoaimy"] = ""
                scene_copy["voiceover_audio_namminh"] = ""
                
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
            if scene.get("voiceover_audio_hoaimy"):
                md.append(f"- **Tải Voice Hoài Mỹ (Nữ)**: [Link Audio MP3]({scene.get('voiceover_audio_hoaimy')})")
                md.append(f"- **Tải Voice Nam Minh (Nam)**: [Link Audio MP3]({scene.get('voiceover_audio_namminh')})")
            if scene.get("audio_cue"):
                md.append(f"- **Âm thanh/SFX**: {scene.get('audio_cue')}")
            if scene.get("image_url"):
                md.append(f"- **Link ảnh phân cảnh**: [Link Ảnh Storyboard]({scene.get('image_url')})")
            if scene.get("image_prompt"):
                md.append(f"- **AI Image Prompt**: `{scene.get('image_prompt')}`")
            if scene.get("scene_notes"):
                md.append(f"- **Ghi chú phân cảnh**: *{scene.get('scene_notes')}*")
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
        stmt = select(VideoScript).options(
            selectinload(VideoScript.product),
            selectinload(VideoScript.style)
        ).where(VideoScript.deleted_at.is_(None))
        
        if search:
            stmt = stmt.where(VideoScript.title.ilike(f"%{search}%"))
            
        stmt = stmt.order_by(VideoScript.created_at.desc())
        
        # Query total count
        count_stmt = select(func.count()).select_from(VideoScript).where(VideoScript.deleted_at.is_(None))
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
        stmt = select(VideoScript).where(VideoScript.id == script_id).where(VideoScript.deleted_at.is_(None))
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
        stmt = select(VideoScript).where(VideoScript.id == script_id).where(VideoScript.deleted_at.is_(None))
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



