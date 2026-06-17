import asyncio
import os
import sys

# Set test environment flag
os.environ["FAST_PLATFORM_TEST"] = "true"

from backend.database import async_session_maker, engine
from backend.database.models.video_marketing import VideoScript, VideoScriptStyle
from sqlalchemy import select
from pydantic_ai import Agent
from backend.services.video_marketing.schemas import ScriptEvaluationReport, VideoScriptModel
from backend.services.video_marketing.prompts_registrar import composer

async def debug_main():
    print("Initializing components...")
    
    # Init database connection
    async with async_session_maker() as session:
        # Fetch first style
        res_style = await session.execute(select(VideoScriptStyle).limit(1))
        style = res_style.scalar_one_or_none()
        if not style:
            print("No style found.")
            return
            
        print(f"Using style: {style.name} ({style.id})")
        
        # Bad script test data
        bad_script = {
            "title": "Kịch bản lỗi để kiểm thử AI",
            "style_name": "TikTok Drama",
            "target_audience": "Người tiêu dùng trẻ",
            "notes": "Đây là kịch bản cố tình viết sai quy chuẩn",
            "total_duration": 5.0,
            "scenes": [
                {
                    "scene_number": 1,
                    "duration": 2.0,
                    "visual_description": "Khách hàng cảm thấy vô cùng hạnh phúc khi nhìn thấy bao bì cao cấp của sản phẩm",
                    "voiceover": "Sản phẩm cực tốt",
                    "scene_notes": "Cầm sản phẩm"
                }
            ]
        }
        
        model_data = VideoScriptModel(**bad_script)
        script_text = f"TIÊU ĐỀ: {model_data.title}\n"
        script_text += f"PHONG CÁCH: {model_data.style_name}\n"
        script_text += f"ĐỐI TƯỢNG: {model_data.target_audience}\n"
        script_text += "DANH SÁCH PHÂN CẢNH:\n"
        for scene in model_data.scenes:
            script_text += f"--- CẢNH {scene.scene_number} ({scene.duration}s) ---\n"
            script_text += f"Visual: {scene.visual_description}\n"
            script_text += f"Voiceover: {scene.voiceover}\n"
        
        print("Composing template...")
        try:
            prompt_content = composer.compose("video_script_evaluation")
            print(f"System Prompt: {prompt_content[:150]}...")
        except Exception as e:
            print(f"Error composing template: {e}")
            import traceback
            traceback.print_exc()
            return
            
        print("Initializing Agent & TrinityBridge...")
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
        try:
            # Need to initialize key rotator explicitly in script if lifespan hasn't run
            from backend.services.ai_engine.core.key_rotator import key_rotator
            await key_rotator.load_keys()
            
            eval_agent = Agent(
                output_type=ScriptEvaluationReport,
                retries=3
            )
            print("Agent initialized successfully.")
        except Exception as e:
            print(f"Error initializing Agent: {e}")
            import traceback
            traceback.print_exc()
            return
            
        print("Running Agent...")
        try:
            eval_res = await trinity_bridge.run(
                agent=eval_agent,
                prompt=script_text,
                system_prompt=prompt_content,
                role="brain"
            )
            print("Agent run complete!")
            print(f"Data: {eval_res}")
        except Exception as e:
            print(f"Error running Agent: {e}")
            import traceback
            traceback.print_exc()
            return

    await engine.dispose()
    print("Done debug!")

if __name__ == "__main__":
    asyncio.run(debug_main())
