import asyncio
import os
import sys
import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete

# Set test environment flag
os.environ["FAST_PLATFORM_TEST"] = "true"

from litestar.testing import AsyncTestClient
from backend.main import app
from backend.database import async_session_maker, engine
from backend.database.models import User
from backend.database.models.video_marketing import VideoScript, VideoScriptStyle

SECRET_KEY = os.environ.get("ENCRYPTION_SALT", "osmo_Elite_Standard_Salt_2026")
ALGORITHM = "HS256"

async def get_real_user_credentials():
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.status == "ACTIVE").limit(1)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user.id, user.security_stamp
    except Exception:
        pass
    return "test-user-id", "VALID_STAMP_2026"

def generate_token(user_id="test-user-id", stamp="VALID_STAMP_2026"):
    payload = {
        "id": user_id,
        "sub": "user@osmo.vn",
        "roles": [],
        "perms": ["content:write"],
        "stamp": stamp,
        "name": "Test User",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def create_test_script(style_id: str) -> str:
    # Inserts a script with abstract terms and audio-visual mismatches to trigger bugs
    async with async_session_maker() as session:
        bad_script = {
            "title": "Kịch bản lỗi để kiểm thử AI",
            "style_name": "TikTok Drama",
            "target_audience": "Người tiêu dùng trẻ",
            "notes": "Đây là kịch bản cố tình viết sai quy chuẩn",
            "target_duration": 30,
            "total_duration": 5.0,
            "scenes": [
                {
                    "scene_number": 1,
                    "duration": 2.0,
                    "visual_description": "Khách hàng cảm thấy vô cùng hạnh phúc khi nhìn thấy bao bì cao cấp của sản phẩm", # Abstract term: "hạnh phúc", "cao cấp"
                    "voiceover": "Sản phẩm của chúng tôi có chất lượng cực kỳ vượt trội, tốt nhất thế giới, giá cả vô cùng rẻ và mang lại cảm giác cực kỳ sang trọng quý tộc khi cầm trên tay.", # 30 words in 2s
                    "scene_notes": "Cầm sản phẩm"
                }
            ]
        }
        script_db = VideoScript(
            style_id=style_id,
            title="Kịch bản Test Đạo Diễn AI",
            structured_script=bad_script,
            tenant_id="osmo.vn"
        )
        session.add(script_db)
        await session.commit()
        return script_db.id

async def run_test():
    print("=== STARTING AI EVALUATION ENGINE INTEGRATION TEST ===")
    
    # 1. Credentials
    user_id, stamp = await get_real_user_credentials()
    token = generate_token(user_id, stamp)
    headers = {
        "Host": "admin.osmo.vn",
        "Authorization": f"Bearer {token}"
    }

    # 2. Get style ID
    async with async_session_maker() as session:
        stmt = select(VideoScriptStyle).limit(1)
        res = await session.execute(stmt)
        style = res.scalar_one_or_none()
        if not style:
            print("❌ No video styles found in DB! Seed database first.")
            sys.exit(1)
        style_id = style.id

    # 3. Create bad test script
    script_id = await create_test_script(style_id)
    print(f"Created bad test script with ID: {script_id}")

    try:
        async with AsyncTestClient(app=app) as client:
            # 4. Trigger AI Evaluation
            print("Evaluating script...")
            response = await client.post(f"/api/v1/video/script/{script_id}/evaluate", headers=headers)
            print(f"Evaluation Response Status: {response.status_code}")
            assert response.status_code in (200, 201), f"Evaluation failed: {response.text}"
            
            eval_data = response.json().get("data", {})
            print("AI Evaluation scores:")
            for key in ["hook_retention", "audio_visual_harmony", "ai_generation_viability", "platform_optimization", "brand_integrity", "duration_compliance"]:
                crit = eval_data.get(key, {})
                print(f" - {key}: {crit.get('score')}/10 (Pros: {len(crit.get('pros', []))}, Cons: {len(crit.get('cons', []))})")
                if crit.get('cons'):
                    print(f"   * Cons detected: {crit.get('cons')}")
            
            # 5. Trigger AI Optimization (Auto-Fix)
            print("\nTriggering AI Auto-Fix (Optimization)...")
            opt_response = await client.post(f"/api/v1/video/script/{script_id}/optimize", headers=headers)
            print(f"Optimization Response Status: {opt_response.status_code}")
            assert opt_response.status_code in (200, 201), f"Optimization failed: {opt_response.text}"
            
            opt_data = opt_response.json().get("data", {})
            opt_script = opt_data.get("structured_script", {})
            print(f"Optimized Script Title: {opt_script.get('title')}")
            
            # Show differences in scenes
            print("Optimized scenes preview:")
            for scene in opt_script.get("scenes", []):
                print(f" - Scene #{scene.get('scene_number')} ({scene.get('duration')}s):")
                print(f"   * Visual: {scene.get('visual_description')}")
                print(f"   * Voiceover: {scene.get('voiceover')}")
                
            # Verify new evaluation exists after optimization
            new_eval = opt_script.get("evaluation", {})
            print("\nNew AI Evaluation scores after Auto-Fix:")
            for key in ["hook_retention", "audio_visual_harmony", "ai_generation_viability", "platform_optimization", "brand_integrity", "duration_compliance"]:
                crit = new_eval.get(key, {})
                print(f" - {key}: {crit.get('score')}/10")
                
            print("\n✅ === INTEGRATION TEST SUCCESSFUL ===")
    
    finally:
        # Cleanup
        async with async_session_maker() as session:
            await session.execute(delete(VideoScript).where(VideoScript.id == script_id))
            await session.commit()
        print("Cleaned up test script.")
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_test())
