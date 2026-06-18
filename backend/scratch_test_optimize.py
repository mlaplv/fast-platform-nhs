import asyncio
import sys
import os
import json
import logging

# Thêm root path vào python path để import được backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.database.models.video_marketing import VideoScript
from backend.services.video_marketing.script_generator_service import VideoScriptModel
from backend.controllers.video_marketing.script_controller import ScriptPatchResponse
from backend.services.video_marketing.schemas import ScriptEvaluationReport, VideoScriptResponse
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.prompts import composer
from pydantic_ai import Agent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-optimize")

# Thiết lập Tenant Context
from backend.database import current_tenant_id
current_tenant_id.set("osmo.vn")

async def test_run():
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:OsmoSecureDBPass2026Secure@postgres:5432/fast_platform")
    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    script_id = "019ed8f3-8b1d-70ad-8bf0-8f60deb23524"
    print(f"🧬 [Test] Đang tải kịch bản từ database với ID: {script_id}...")
    
    async with async_session() as session:
        # 1. Tải kịch bản gốc
        stmt = select(VideoScript).where(VideoScript.id == script_id)
        res = await session.execute(stmt)
        script = res.scalar_one_or_none()
        
        if not script:
            print(f"❌ Không tìm thấy kịch bản với ID: {script_id}")
            return
            
        model_data = VideoScriptModel(**script.structured_script)
        
        # 1.1 Khôi phục lại bản gốc để kiểm tra tối ưu từ đầu (loại bỏ exfoliated skin của pre-clean trước đó)
        # Thay thế các từ 'exfoliated skin' trong voiceover của bản gốc để giả lập kịch bản khi chưa bị pre-clean lỗi
        for scene in model_data.scenes:
            if "exfoliated skin" in (scene.voiceover or "").lower():
                scene.voiceover = scene.voiceover.replace("exfoliated skin", "lột tẩy")
        
        # Đóng session ngay lập tức để giải phóng kết nối DB
        await session.close()
        
        print("\n--- KỊCH BẢN GỐC TRƯỚC KHI TỐI ƯU ---")
        for scene in model_data.scenes:
            print(f"Cảnh {scene.scene_number}:")
            print(f"  Visual: {scene.visual_description}")
            print(f"  Voiceover: {scene.voiceover}")

        # Chuẩn bị input prompt và eval report cũ
        evaluation_report = ScriptEvaluationReport(**model_data.evaluation) if model_data.evaluation else None
        
        script_text = f"TIÊU ĐỀ: {model_data.title}\n"
        script_text += f"PHONG CÁCH: {model_data.style_name}\n"
        script_text += f"ĐỐI TƯỢNG: {model_data.target_audience}\n"
        script_text += f"THỜI LƯỢNG MỤC TIÊU: {model_data.target_duration or 30} giây\n"
        script_text += "\nDANH SÁCH CÁC CẢNH HIỆN TẠI:\n"
        for scene in model_data.scenes:
            script_text += f"--- CẢNH {scene.scene_number} ({scene.duration}s) ---\n"
            script_text += f"Visual: {scene.visual_description}\n"
            script_text += f"Voiceover: {scene.voiceover}\n"
            if scene.scene_notes:
                script_text += f"Notes: {scene.scene_notes}\n"
        
        error_context = ""
        if evaluation_report:
            error_context = "\nBÁO CÁO LỖI KỊCH BẢN CẦN CHỈNH SỬA:\n"
            pre_violations = []
            for field, value in evaluation_report.model_dump().items():
                if isinstance(value, dict) and "cons" in value:
                    for err in value["cons"]:
                        pre_violations.append(f"{field.upper()}: {err}")
            for v in pre_violations:
                error_context += f"  ✗ {v}\n"
            error_context += "\nHƯỚNG DẪN THAY THẾ:\n"
            error_context += "- 'beautiful/đẹp' → 'soft warm light on dewy skin, visible pore texture'\n"
            error_context += "- 'hạnh phúc/happy' → 'woman smiling with eyes crinkling, teeth visible, warm backlight halo'\n"
            error_context += "- 'sang trọng/luxury' → 'gold foil label with embossed typography, sharp focus'\n"
            error_context += "- 'năng lượng tích cực' → 'woman walking briskly with upright posture, bright outdoor sunlight'\n"
            error_context += "- 'tự tin/rạng rỡ' → 'woman looking directly at camera with relaxed smile, chin slightly raised'\n"
        
        input_prompt = f"{script_text}\n\n{error_context}"
        
        # 1.2 Hàm Guarantee Engine
        def apply_guarantee_engine(script_model: VideoScriptModel) -> list[str]:
            import re
            visual_cleanup_map = {
                "nụ cười rạng rỡ bừng sáng": "warm golden hour backlight on face, natural smile, bright bokeh lights",
                "nụ cười rạng rỡ": "warm golden hour backlight on face, natural smile, bright bokeh lights",
                "cảm giác hạnh phúc": "smiling with eyes crinkling, teeth visible, warm backlight halo",
                "hài lòng tận hưởng": "smiling with eyes closed, relaxed facial muscles, soft lighting",
                "stressed expression": "stressed expression with dry, slightly darkened and damaged skin patches on cheeks",
                "lột tẩy làm da sạm đi": "exfoliated skin with dry, red, and slightly darkened skin patches",
                "năng lượng tích cực": "upright posture, brisk walking, bright outdoor sunlight",
                "chất lượng cao": "macro close-up texture, sharp 4K detail",
                "sang trọng": "gold foil label, embossed typography, studio light",
                "tinh tế": "clean minimal composition, soft rim light",
                "cao cấp": "premium matte packaging, precise edge lighting",
                "tuyệt vời": "sharp detail, professional studio setup",
                "hoàn hảo": "flawless skin texture under diffused soft light",
                "đặc biệt": "unique texture close-up, selective focus",
                "nổi bật": "subject isolated against clean background, sharp focus",
                "ấn tượng": "dramatic low-angle shot, strong shadow contrast",
                "tận hưởng": "relaxed, smiling face",
                "cảm giác": "",
                "bừng sáng": "bright, glowing",
                "lột tẩy": "exfoliated skin",
                "sạm": "slightly darkened, dry skin patch",
                "đẹp": "soft warm light on dewy skin, visible pore texture",
                "hạnh phúc": "smiling with eyes crinkling, teeth visible, warm backlight halo",
                "vui vẻ": "genuine laugh, slight head tilt, warm side light",
                "tự tin": "direct eye contact with camera, chin slightly raised",
                "rạng rỡ": "warm golden hour backlight on face, natural smile",
                "lung linh": "soft bokeh highlights, warm ambient glow",
                "lộng lẫy": "dramatic rim light, high contrast silhouette",
                "exfoliated skin": "exfoliated skin patch",
                "crisp edges": "high contrast details, sharp definition on edges, studio lighting",
                "luxurious skincare commercial aesthetic": "clean product shot on pedestal, soft rim light, reflection on glass, high-end commercial style",
                "smiling with eyes closed, relaxed facial": "smiling with eyes closed, cheeks slightly raised, relaxed facial muscles, soft lighting",
            }
            voiceover_cleanup_map = {
                "nụ cười rạng rỡ bừng sáng": "nụ cười tươi rạng ngời",
                "nụ cười rạng rỡ": "nụ cười tươi tắn",
                "cảm giác hạnh phúc": "niềm hạnh phúc ngập tràn",
                "hài lòng tận hưởng": "thư giãn tận hưởng",
                "stressed expression": "khuôn mặt đầy mệt mỏi",
                "lột tẩy làm da sạm đi": "lột tẩy khiến làn da bị xỉn màu",
                "năng lượng tích cực": "sự tươi trẻ",
                "chất lượng cao": "chất lượng vượt trội",
                "sang trọng": "tinh tế",
                "tinh tế": "nhẹ nhàng",
                "cao cấp": "chất lượng",
                "tuyệt vời": "hiệu quả",
                "hoàn hảo": "tối ưu",
                "đặc biệt": "khác biệt",
                "nổi bật": "rõ rệt",
                "ấn tượng": "đáng nhớ",
                "tận hưởng": "cảm nhận",
                "cảm giác": "cảm nhận",
                "bừng sáng": "rạng ngời",
                "lột tẩy": "tẩy da quá đà",
                "sạm": "xỉn màu",
                "đẹp": "mịn màng",
                "hạnh phúc": "vui tươi",
                "vui vẻ": "tươi vui",
                "tự tin": "an tâm",
                "rạng rỡ": "tươi tắn",
                "lung linh": "tươi sáng",
                "lộng lẫy": "xinh đẹp",
                "exfoliated skin": "tẩy da chết",
                "crisp edges": "độ sắc nét",
                "luxurious skincare commercial aesthetic": "chuẩn spa cao cấp",
                "smiling with eyes closed, relaxed facial": "thư giãn tươi cười",
            }
            
            sorted_visual_banned = sorted(visual_cleanup_map.keys(), key=len, reverse=True)
            sorted_voiceover_banned = sorted(voiceover_cleanup_map.keys(), key=len, reverse=True)
            fixes = []
            
            for scene in script_model.scenes:
                scene_num = scene.scene_number
                for banned in sorted_visual_banned:
                    if banned.lower() in (scene.visual_description or "").lower():
                        replacement = visual_cleanup_map[banned]
                        if replacement and replacement.lower() in (scene.visual_description or "").lower():
                            continue
                        scene.visual_description = re.sub(
                            re.escape(banned), replacement,
                            scene.visual_description, flags=re.IGNORECASE
                        )
                        fixes.append(f"Cảnh {scene_num}: visual '{banned}' → '{replacement}'")
                for banned in sorted_voiceover_banned:
                    if banned.lower() in (scene.voiceover or "").lower():
                        replacement = voiceover_cleanup_map[banned]
                        if replacement and replacement.lower() in (scene.voiceover or "").lower():
                            continue
                        scene.voiceover = re.sub(
                            re.escape(banned), replacement,
                            scene.voiceover, flags=re.IGNORECASE
                        )
                        fixes.append(f"Cảnh {scene_num}: voiceover '{banned}' → '{replacement}'")
                        
                # ── FIX C: Aspect Ratio Hint ──
                aspect = script_model.aspect_ratio or "9:16"
                ar_hints = {"9:16": "9:16 vertical frame", "16:9": "16:9 horizontal frame", "1:1": "1:1 square frame"}
                ar_hint = ar_hints.get(aspect, "9:16 vertical frame")
                if scene.visual_description and ar_hint.lower() not in scene.visual_description.lower():
                    scene.visual_description = scene.visual_description.rstrip(". ") + f", {ar_hint}"
                    fixes.append(f"Cảnh {scene_num}: thêm aspect ratio hint")
                    
                # ── FIX D: Label Guard ──
                label_guard = "keep the product label and logo completely static and sharp"
                if scene.visual_description and label_guard not in scene.visual_description.lower():
                    scene.visual_description = scene.visual_description.rstrip(". ") + f", {label_guard}"
                    fixes.append(f"Cảnh {scene_num}: thêm label guard")
                    
                # ── FIX E: TTS Speed limiter (tối đa 3.5 từ/giây) ──
                if scene.voiceover and scene.duration > 0:
                    words = scene.voiceover.split()
                    wps = len(words) / scene.duration
                    if wps > 3.5:
                        max_words = int(scene.duration * 3.5)
                        if max_words < len(words):
                            scene.voiceover = " ".join(words[:max_words])
                            if not scene.voiceover.endswith((".", "!", "?")):
                                scene.voiceover = scene.voiceover.rstrip(",;: ") + "."
                            fixes.append(f"Cảnh {scene_num}: TTS quá nhanh ({wps:.1f} từ/s) → giới hạn {max_words} từ")
                            
            # ── FIX F: CTA khẩn cấp ở cảnh cuối ──
            if script_model.scenes:
                last_scene = script_model.scenes[-1]
                urgency_keywords = ["hôm nay", "giới hạn", "chỉ còn", "ngay", "cuối cùng", "duy nhất", "suất", "24h", "48h"]
                has_urgency = any(kw in (last_scene.voiceover or "").lower() for kw in urgency_keywords)
                if not has_urgency:
                    urgency_phrase = " Ưu đãi giới hạn, chỉ còn hôm nay!"
                    if last_scene.voiceover:
                        last_scene.voiceover = last_scene.voiceover.rstrip("!.? ") + "." + urgency_phrase
                    fixes.append(f"Cảnh {last_scene.scene_number}: thêm CTA khẩn cấp")
                    
                # Ép Text Overlay vào scene_notes
                cta_keywords = ["text overlay", "cta", "nút", "button"]
                has_cta_note = any(kw in (last_scene.scene_notes or "").lower() for kw in cta_keywords)
                if not has_cta_note:
                    cta_note = " | Text Overlay: CTA button nổi bật, countdown timer, màu tương phản."
                    last_scene.scene_notes = (last_scene.scene_notes or "") + cta_note
                    fixes.append(f"Cảnh {last_scene.scene_number}: thêm Text Overlay note")
                    
            return fixes

        # Chạy Pre-clean
        pre_fixes = apply_guarantee_engine(model_data)
        print(f"\n🔧 [Guarantee Engine] Pre-cleaned: {pre_fixes}")

        # 2. Gọi AI để lấy các phần sửa đổi
        print("\n🤖 Đang gọi AI (Trinity Bridge) để sinh Patch kịch bản...")
        prompt_content = composer.compose("video_script_optimization")
        opt_agent = Agent(
            output_type=ScriptPatchResponse,
            retries=2
        )
        
        patch_data = await trinity_bridge.run(
            agent=opt_agent,
            prompt=input_prompt,
            system_prompt=prompt_content,
            role="brain",
            per_model_timeout=35.0
        )
        
        print("\n📦 AI Patch Data trả về:")
        print(patch_data.model_dump_json(indent=2))

        # 3. Áp dụng Patch
        optimized_script = VideoScriptModel(**model_data.model_dump())
        patched_scenes_count = 0
        for patch in patch_data.scenes_to_update:
            for scene in optimized_script.scenes:
                if scene.scene_number == patch.scene_number:
                    scene.visual_description = patch.visual_description
                    scene.voiceover = patch.voiceover
                    if patch.scene_notes is not None:
                        scene.scene_notes = patch.scene_notes
                    patched_scenes_count += 1
        
        print(f"\n🧬 [ScriptOptimization] Đã patch {patched_scenes_count} phân cảnh.")
        
        # Chạy Post-clean
        opt_fixes = apply_guarantee_engine(optimized_script)
        print(f"🔧 [Guarantee Engine] Post-cleaned: {opt_fixes}")
        
        # 4. Đánh giá lại kịch bản đã tối ưu
        print("\n📡 Đang gửi kịch bản đã sửa cho AI Evaluator chấm điểm...")
        eval_prompt_content = composer.compose("video_script_evaluation")
        eval_agent = Agent(
            output_type=ScriptEvaluationReport,
            retries=2
        )
        
        opt_target_dur = optimized_script.target_duration or 30
        opt_aspect = optimized_script.aspect_ratio or "9:16"
        opt_platform = "TikTok/Reels/Shorts (dọc)"
        
        new_script_text = f"TIÊU ĐỀ: {optimized_script.title}\n"
        new_script_text += f"PHONG CÁCH: {optimized_script.style_name}\n"
        new_script_text += f"ĐỐI TƯỢNG: {optimized_script.target_audience}\n"
        new_script_text += f"TỶ LỆ KHUNG HÌNH: {opt_aspect} — NỀN TẢNG: {opt_platform}\n"
        new_script_text += f"THỜI LƯỢNG MỤC TIÊU: {opt_target_dur} giây\n"
        new_script_text += f"TỔNG THỜI LƯỢNG THỰC TẾ: {optimized_script.total_duration} giây\n"
        new_script_text += "\nDANH SÁCH PHÂN CẢNH (KÈM KIỂM TRA TTS):\n"
        for scene in optimized_script.scenes:
            word_count = len(scene.voiceover.split()) if scene.voiceover else 0
            wps = word_count / scene.duration if scene.duration > 0 else 0
            tts_status = "✓ OK" if wps <= 3.5 else f"⚠️ QUÁ NHANH"
            new_script_text += f"--- CẢNH {scene.scene_number} ({scene.duration}s | TTS: {tts_status}) ---\n"
            new_script_text += f"Visual: {scene.visual_description}\n"
            new_script_text += f"Voiceover: {scene.voiceover}\n"
        
        new_report = await trinity_bridge.run(
            agent=eval_agent,
            prompt=new_script_text,
            system_prompt=eval_prompt_content,
            role="brain",
            per_model_timeout=35.0
        )
        
        old_score = evaluation_report.overall_score if evaluation_report else 0
        new_score = new_report.overall_score
        
        print("\n================ KẾT QUẢ TỐI ƯU ==================")
        print(f"Điểm cũ: {old_score}/10")
        print(f"Điểm mới: {new_score}/10")
        print(f"Chênh lệch điểm: {new_score - old_score:+.1f}")
        
        print("\n--- CHI TIẾT KỊCH BẢN SAU KHI SỬA ---")
        for scene in optimized_script.scenes:
            print(f"Cảnh {scene.scene_number}:")
            print(f"  Visual: {scene.visual_description}")
            print(f"  Voiceover: {scene.voiceover}")
            
        print("\n--- CÁC LỖI CÒN SÓT LẠI (TỪ AI EVALUATOR MỚI) ---")
        for field, value in new_report.model_dump().items():
            if isinstance(value, dict) and "cons" in value and value["cons"]:
                print(f"❌ {field.upper()}: {value['cons']}")
                
        # Lưu vào database nếu điểm tốt hơn bằng session mới ngắn hạn
        if new_score >= old_score:
            print("\n💾 [DB] Điểm tốt hơn hoặc bằng! Đang lưu kịch bản đã sửa vào database...")
            optimized_script.evaluation = new_report.model_dump()
            async with async_session() as write_session:
                stmt_write = select(VideoScript).where(VideoScript.id == script_id)
                res_write = await write_session.execute(stmt_write)
                script_db = res_write.scalar_one()
                script_db.structured_script = optimized_script.model_dump()
                await write_session.commit()
            print("✓ [DB] Lưu thành công.")
        else:
            print("\n⚠️ [DB] Điểm mới thấp hơn! Không lưu kịch bản đã sửa.")

if __name__ == "__main__":
    asyncio.run(test_run())
