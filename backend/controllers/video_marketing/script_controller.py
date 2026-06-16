import logging
from typing import List, Optional
from litestar import Controller, get, post, patch, delete, Response, Request
from litestar.exceptions import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models.video_marketing import VideoScript, VideoScriptStyle
from backend.database.models.commerce import ProductBase
from backend.services.video_marketing.product_resolver_service import product_resolver_service
from backend.services.video_marketing.script_generator_service import script_generator_service
from backend.services.video_marketing.schemas import (
    GenerateScriptRequest, CreateStyleRequest, VideoScriptResponse, VideoStyleResponse, VideoScriptListResponse, UpdateScriptRequest
)
from backend.schemas.common import SuccessResponse

logger = logging.getLogger("api-gateway")

class VideoScriptController(Controller):
    """API Controller quản lý kịch bản Video Marketing và Dynamic Styles."""
    path = "/api/v1/video"
    tags = ["Video Marketing"]

    @post("/script/generate")
    async def generate_script(self, db_session: AsyncSession, data: GenerateScriptRequest) -> SuccessResponse[VideoScriptResponse]:
        """Sinh kịch bản video từ sản phẩm và phong cách được chọn."""
        # 1. Tìm sản phẩm trong DB thực tế
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
            
        # 2. Giải quyết ngữ cảnh sản phẩm
        product_context = await product_resolver_service.get_product_context(product.id, db_session)
        if not product_context:
            raise HTTPException(status_code=400, detail="Không thể phân giải ngữ cảnh sản phẩm để sinh kịch bản.")
            
        # 3. Sinh kịch bản qua AI Core (tích hợp TrinityBridge & NPO Vault)
        try:
            generated_script = await script_generator_service.generate_script(
                product_context=product_context,
                style_id=data.style_id,
                db=db_session
            )
        except Exception as e:
            logger.error(f"❌ [VideoController] Script generation failed: {e}")
            raise HTTPException(status_code=400, detail=f"Lỗi khi gọi AI sinh kịch bản: {str(e)}")

        # 4. Lưu kịch bản vào cơ sở dữ liệu
        script_db = VideoScript(
            product_id=product.id,
            style_id=data.style_id,
            title=generated_script.title,
            structured_script=generated_script.model_dump(),
            tenant_id="smartshop"  # Tenant ID mặc định
        )
        db_session.add(script_db)
        await db_session.commit()
        
        # 5. Trả về kết quả chuẩn
        result = VideoScriptResponse(
            id=script_db.id,
            product_id=script_db.product_id,
            style_id=script_db.style_id,
            title=script_db.title,
            structured_script=generated_script,
            created_at=script_db.created_at.isoformat()
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
            
        from backend.services.video_marketing.script_generator_service import VideoScriptModel
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
        import datetime
        import json
        import urllib.parse

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
        md.append(f"exported_at: \"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\"")
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
        
        from backend.services.video_marketing.script_generator_service import VideoScriptModel
        
        data_list = []
        for script in scripts:
            # Safely parse structured script
            structured = script.structured_script
            if isinstance(structured, str):
                import json
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
        from datetime import datetime, timezone
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
        
        from backend.services.video_marketing.script_generator_service import VideoScriptModel
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

