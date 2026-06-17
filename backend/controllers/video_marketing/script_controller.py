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

    async def _generate_clypra_project_files(
        self,
        db_session: AsyncSession,
        script_id: str,
        voice: str,
        clypra_projects_dir: Path
    ) -> Path:
        """Sinh ra các tệp dự án Clypra và assets trong thư mục clypra_projects_dir. Trả về project_file_path."""
        # 1. Tìm kịch bản trong DB
        stmt = select(VideoScript).options(
            selectinload(VideoScript.style),
            selectinload(VideoScript.product)
        ).where(VideoScript.id == script_id).where(VideoScript.deleted_at.is_(None))
        res = await db_session.execute(stmt)
        script = res.scalar_one_or_none()
        
        if not script:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy kịch bản với ID: {script_id}")
            
        data = script.structured_script
        scenes = data.get("scenes", [])
        
        # Lấy hình ảnh của sản phẩm thực tế để mapping tự động
        product_images = []
        if script.product and script.product.images:
            for img in script.product.images:
                if img:
                    product_images.append(img)
        
        # 2. Xác định tỷ lệ khung hình & kích thước canvas dựa trên thiết lập lưu trong kịch bản (hoặc fallback từ style)
        aspect_ratio = data.get("aspect_ratio")
        if not aspect_ratio:
            style_platform = ""
            if script.style and script.style.platform:
                style_platform = script.style.platform.lower()
            is_vertical = any(keyword in style_platform for keyword in ["tiktok", "reels", "shorts", "vertical"])
            aspect_ratio = "9:16" if is_vertical else "16:9"
            
        if aspect_ratio == "9:16":
            canvas_width = 1080
            canvas_height = 1920
        elif aspect_ratio == "1:1":
            canvas_width = 1080
            canvas_height = 1080
        else:  # default 16:9
            canvas_width = 1920
            canvas_height = 1080
        
        # 3. Tạo thư mục làm việc cục bộ của Clypra
        clypra_projects_dir = Path("/home/lv/.local/share/com.clypra.editor/projects")
        clypra_projects_dir.mkdir(parents=True, exist_ok=True)
        
        assets_dir = clypra_projects_dir / f"assets_{script_id}"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # 3.1. Copy brand logo watermark
        logo_filename = "brand_logo.png"
        logo_path = assets_dir / logo_filename
        logo_success = False
        
        logo_paths = [
            "/app/frontend/static/uploads/img/logo.png",
            "/app/frontend/static/uploads/img/Logo.png",
            "/app/frontend/static/uploads/img/logo_transparent.webp",
            "/app/frontend/static/favicon.svg",
            "/opt/fast-platform/frontend/static/favicon.svg",
            "/media/lv/data/fast-platform-core/frontend/static/favicon.svg"
        ]
        
        for lp in logo_paths:
            p = Path(lp)
            if p.exists():
                try:
                    shutil.copy2(str(p), str(logo_path))
                    logo_success = True
                    break
                except Exception as ex:
                    logger.warning(f"Failed to copy logo from {lp}: {ex}")
                    
        media_assets = []
        if logo_success:
            media_assets.append({
                "id": "asset_brand_logo",
                "name": "brand_logo.png",
                "path": f"assets_{script_id}/{logo_filename}",
                "type": "image",
                "duration": 3600.0,
                "width": 200,
                "height": 200,
                "size": os.path.getsize(logo_path)
            })
            
        clips = []
        start_time = 0.0
        
        # Thư mục chứa các tệp nhị phân tĩnh
        ffprobe_bin = "/media/lv/data/fast-platform-core/scripts/ffprobe"
        
        # 4. Xử lý từng phân cảnh
        for idx, scene in enumerate(scenes):
            scene_number = scene.get("scene_number", idx + 1)
            duration = float(scene.get("duration", 4.0))
            voiceover = scene.get("voiceover", "")
            image_url = scene.get("image_url", "")
            visual_description = scene.get("visual_description", "")
            
            # 4.1. Tạo tệp âm thanh TTS bằng edge_tts
            audio_filename = f"audio_scene_{scene_number}.mp3"
            audio_path = assets_dir / audio_filename
            audio_duration = duration
            
            if voiceover:
                try:
                    clean_voiceover = re.sub(r'[<>]', '', voiceover)
                    clean_voiceover = re.sub(r'<[^>]*>', '', clean_voiceover)
                    clean_voiceover = clean_voiceover[:20000]
                    clean_voiceover = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', clean_voiceover)
                    clean_voiceover = re.sub(r'([\.!\?,])([^\s\.!\?,])', r'\1 \2', clean_voiceover)
                    clean_voiceover = re.sub(r'\s+', ' ', clean_voiceover).strip()

                    communicate = edge_tts.Communicate(clean_voiceover, voice)
                    await communicate.save(str(audio_path))
                    
                    # Đo thời lượng thực tế của âm thanh bằng ffprobe
                    if audio_path.exists() and os.path.exists(ffprobe_bin):
                        cmd = [
                            ffprobe_bin, "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
                        ]
                        probe_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        if probe_res.returncode == 0:
                            audio_duration = float(probe_res.stdout.strip())
                except Exception as ex:
                    logger.warning(f"Failed to generate TTS audio for scene {scene_number}: {ex}")
            
            actual_duration = max(duration, audio_duration)
            
            # 4.2. Tải/Sao chép ảnh Storyboard hoặc sinh ảnh solid màu đen nếu không có
            image_filename = f"image_scene_{scene_number}.png"
            image_path = assets_dir / image_filename
            image_success = False
            
            # Nếu phân cảnh chưa có ảnh, tự động gán ảnh từ danh sách ảnh sản phẩm thực tế
            if not image_url and product_images:
                image_url = product_images[idx % len(product_images)]

            if image_url:
                local_source_path = None
                if image_url.startswith("/"):
                    paths_to_check = [
                        Path("/app/frontend/static") / image_url.lstrip("/"),
                        Path("/opt/fast-platform/frontend/static") / image_url.lstrip("/"),
                        Path(os.getcwd()) / "frontend/static" / image_url.lstrip("/"),
                        Path("/media/lv/data/fast-platform-core") / image_url.lstrip("/"),
                        Path("/media/lv/data/fast-platform-core/backend") / image_url.lstrip("/"),
                    ]
                    for p in paths_to_check:
                        if p.exists():
                            local_source_path = p
                            break
                            
                if local_source_path:
                    try:
                        shutil.copy2(str(local_source_path), str(image_path))
                        image_success = True
                    except Exception as ex:
                        logger.warning(f"Failed to copy local image for scene {scene_number}: {ex}")
                elif image_url.startswith("http"):
                    try:
                        req = urllib.request.Request(
                            image_url, 
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                        )
                        with urllib.request.urlopen(req, timeout=10) as response, open(image_path, 'wb') as out_file:
                            out_file.write(response.read())
                        image_success = True
                    except Exception as ex:
                        logger.warning(f"Failed to download remote image for scene {scene_number}: {ex}")
                        
            # Tạo ảnh solid nếu download/copy thất bại
            if not image_success:
                try:
                    img = PIL.Image.new("RGB", (canvas_width, canvas_height), color=(18, 18, 24))
                    draw = PIL.ImageDraw.Draw(img)
                    
                    text_title = f"PHÂN CẢNH {scene_number}"
                    text_desc = visual_description[:50] + "..." if len(visual_description) > 50 else visual_description
                    
                    # Vẽ text cơ bản lên ảnh
                    draw.text((canvas_width // 2, canvas_height // 2 - 40), text_title, fill=(255, 255, 255), anchor="mm")
                    draw.text((canvas_width // 2, canvas_height // 2 + 20), text_desc, fill=(160, 160, 160), anchor="mm")
                    img.save(image_path)
                    image_success = True
                except Exception as ex:
                    logger.error(f"Failed to draw PIL placeholder for scene {scene_number}: {ex}")
                    
            # 4.3. Đăng ký Media Assets cho Clypra
            media_assets.append({
                "id": f"asset_image_{scene_number}",
                "name": f"image_scene_{scene_number}.png",
                "path": f"assets_{script_id}/image_scene_{scene_number}.png",
                "type": "image",
                "duration": 3600.0,
                "width": canvas_width,
                "height": canvas_height,
                "size": os.path.getsize(image_path) if image_path.exists() else 0
            })
            
            if audio_path.exists():
                media_assets.append({
                    "id": f"asset_audio_{scene_number}",
                    "name": f"audio_scene_{scene_number}.mp3",
                    "path": f"assets_{script_id}/{audio_filename}",
                    "type": "audio",
                    "duration": audio_duration,
                    "size": os.path.getsize(audio_path) if audio_path.exists() else 0
                })
                
            # 4.4. Đăng ký Clips lên Timeline Tracks
            # Image Clip
            clips.append({
                "id": f"clip_image_{scene_number}",
                "trackId": "track_video",
                "mediaId": f"asset_image_{scene_number}",
                "startTime": start_time,
                "duration": actual_duration,
                "trimIn": 0.0,
                "trimOut": actual_duration,
                "x": 0.0,
                "y": 0.0,
                "width": canvas_width,
                "height": canvas_height,
                "opacity": 1.0,
                "rotation": 0.0,
                "aspectRatioLocked": True,
                "fitMode": "cover",
                "kind": "image"
            })
            
            # Audio Clip
            if audio_path.exists():
                clips.append({
                    "id": f"clip_audio_{scene_number}",
                    "trackId": "track_audio",
                    "mediaId": f"asset_audio_{scene_number}",
                    "startTime": start_time,
                    "duration": audio_duration,
                    "trimIn": 0.0,
                    "trimOut": audio_duration,
                    "x": 0.0,
                    "y": 0.0,
                    "width": 0.0,
                    "height": 0.0,
                    "opacity": 1.0,
                    "rotation": 0.0,
                    "volume": 1.0,
                    "kind": "audio"
                })
                
            # Subtitle (Text) Clip
            if voiceover:
                clips.append({
                    "id": f"clip_text_{scene_number}",
                    "trackId": "track_text",
                    "mediaId": "",
                    "startTime": start_time,
                    "duration": actual_duration,
                    "trimIn": 0.0,
                    "trimOut": actual_duration,
                    "x": 0.0,
                    "y": float(canvas_height - 220),
                    "width": float(canvas_width),
                    "height": 160.0,
                    "opacity": 1.0,
                    "rotation": 0.0,
                    "kind": "text",
                    "text": voiceover,
                    "fontFamily": "Inter",
                    "fontSize": 48 if aspect_ratio == "16:9" else 36,
                    "fontWeight": "bold",
                    "color": "#ffffff",
                    "align": "center",
                    "valign": "middle",
                    "lineHeight": 1.2,
                    "paddingX": 10.0,
                    "paddingY": 10.0,
                    "textRole": "caption",
                    "stroke": {
                        "color": "#000000",
                        "width": 4.0
                    }
                })
                
            start_time += actual_duration
            
        # Thêm clip logo watermark nếu có logo thành công
        if logo_success:
            clips.append({
                "id": "clip_brand_logo",
                "trackId": "track_logo",
                "mediaId": "asset_brand_logo",
                "startTime": 0.0,
                "duration": start_time,
                "trimIn": 0.0,
                "trimOut": start_time,
                "x": float(canvas_width - 150) if is_vertical else float(canvas_width - 220),
                "y": 40.0,
                "width": 100.0 if is_vertical else 160.0,
                "height": 100.0 if is_vertical else 160.0,
                "opacity": 0.85,
                "rotation": 0.0,
                "aspectRatioLocked": True,
                "fitMode": "contain",
                "kind": "image"
            })
            
        # 5. Ghi tệp dự án project.json của Clypra
        project_id = f"project-{script_id}"
        project_json = {
            "id": project_id,
            "name": script.title,
            "created_at": int(time.time() * 1000),
            "modified_at": int(time.time() * 1000),
            "aspect_ratio": aspect_ratio,
            "canvas_width": canvas_width,
            "canvas_height": canvas_height,
            "frame_rate": 30,
            "duration": start_time,
            "media_assets": media_assets,
            "tracks": [
                {
                    "id": "track_video",
                    "type": "video",
                    "name": "Storyboard Visuals",
                    "muted": False,
                    "locked": False,
                    "visible": True,
                    "height": 68
                },
                {
                    "id": "track_logo",
                    "type": "video",
                    "name": "Brand Logo Watermark",
                    "muted": False,
                    "locked": False,
                    "visible": True,
                    "height": 50
                },
                {
                    "id": "track_audio",
                    "type": "audio",
                    "name": "Voiceover TTS",
                    "muted": False,
                    "locked": False,
                    "visible": True,
                    "height": 52
                },
                {
                    "id": "track_text",
                    "type": "text",
                    "name": "Subtitles",
                    "muted": False,
                    "locked": False,
                    "visible": True,
                    "height": 30
                }
            ],
            "clips": clips,
            "transitions": [],
            "timeline_schema_version": 1
        }
        
        project_file_path = clypra_projects_dir / f"{project_id}.json"
        with open(project_file_path, "w", encoding="utf-8") as f:
            json.dump(project_json, f, ensure_ascii=False, indent=2)
            
        return project_file_path

    @post("/script/{script_id:str}/clypra/open")
    async def open_in_clypra(
        self,
        db_session: AsyncSession,
        script_id: str,
        voice: str = "vi-VN-HoaiMyNeural"
    ) -> SuccessResponse[dict]:
        """Tải các tài nguyên âm thanh/hình ảnh, tạo file dự án JSON cho Clypra và kích hoạt khởi chạy editor."""
        clypra_projects_dir = Path("/home/lv/Downloads")
        
        project_file_path = await self._generate_clypra_project_files(
            db_session=db_session,
            script_id=script_id,
            voice=voice,
            clypra_projects_dir=clypra_projects_dir
        )
        
        assets_dir = clypra_projects_dir / f"assets_{script_id}"
        project_id = f"project-{script_id}"
        
        # Khởi chạy Clypra trong môi trường nền có DISPLAY
        launched = False
        try:
            env = os.environ.copy()
            if "DISPLAY" not in env:
                env["DISPLAY"] = ":0"
            subprocess.Popen(["clypra", str(project_file_path)], env=env)
            launched = True
        except Exception as e:
            logger.error(f"Failed to launch Clypra with project: {e}")
            try:
                subprocess.Popen(["clypra"], env=env)
                launched = True
            except Exception as ex:
                logger.error(f"Failed to launch Clypra fallback: {ex}")
                
        # [QUY TẮC AN TOÀN VPS]: Nếu không thể khởi chạy (ví dụ trên VPS), xóa ngay các file rác vừa sinh
        if not launched:
            try:
                if project_file_path.exists():
                    os.remove(project_file_path)
                if assets_dir.exists():
                    shutil.rmtree(assets_dir)
            except Exception as clean_ex:
                logger.error(f"Failed to clean up unsaved Clypra files: {clean_ex}")
                
        return SuccessResponse(
            message="Đã đóng gói dự án và khởi chạy Clypra thành công!",
            data={
                "project_id": project_id,
                "project_path": str(project_file_path),
                "launched": launched
            }
        )

    @get("/script/{script_id:str}/clypra/download")
    async def download_clypra_project(
        self,
        db_session: AsyncSession,
        script_id: str,
        voice: str = "vi-VN-HoaiMyNeural"
    ) -> Response:
        """Đóng gói file project.json và toàn bộ assets của Clypra thành file ZIP để tải về máy cá nhân, xóa sạch dấu vết trên VPS."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            project_file_path = await self._generate_clypra_project_files(
                db_session=db_session,
                script_id=script_id,
                voice=voice,
                clypra_projects_dir=temp_path
            )
            
            assets_dir = temp_path / f"assets_{script_id}"
            zip_file_name = f"clypra_project_{script_id}.zip"
            temp_zip_path = Path(tempfile.gettempdir()) / zip_file_name
            
            try:
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.write(project_file_path, f"project-{script_id}.json")
                    
                    if assets_dir.exists():
                        for root, _, files in os.walk(assets_dir):
                            for file in files:
                                file_path = Path(root) / file
                                arcname = f"assets_{script_id}/{file}"
                                zip_file.write(file_path, arcname)
                                
                with open(temp_zip_path, "rb") as f:
                    zip_data = f.read()
                    
                return Response(
                    content=zip_data,
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename={zip_file_name}"
                    }
                )
            except Exception as e:
                logger.error(f"Failed to generate project zip: {e}")
                raise HTTPException(status_code=500, detail=f"Lỗi đóng gói file zip: {str(e)}")
            finally:
                try:
                    if temp_zip_path.exists():
                        os.remove(temp_zip_path)
                except Exception:
                    pass


