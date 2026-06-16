import os
import sys
from pathlib import Path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path: sys.path.insert(0, project_root)

import asyncio
from sqlalchemy import select, delete
from dotenv import load_dotenv

load_dotenv(os.path.realpath(os.path.join(os.path.dirname(__file__), "../../.env")))

from backend.database import async_session_maker
from backend.database.models.video_marketing import VideoScriptStyle

INITIAL_STYLES = [
    {
        "id": "tiktok_drama",
        "name": "Drama Kịch Tính TikTok",
        "platform": "TikTok",
        "hook_template": "Bắt đầu bằng một câu hỏi sốc, một lời tuyên bố ngược đời hoặc một tình huống oái oăm trong 3 giây đầu để giữ chân người dùng.",
        "style_instruction": "Xây dựng câu chuyện kịch tính kịch bản nhịp cực nhanh (2-4 giây mỗi cảnh). Lời thoại (Voiceover) mang tính nhấn nhá mạnh mẽ, châm biếm hoặc tò mò. Sử dụng nhạc nền tiết tấu dồn dập và hiệu ứng âm thanh (SFX) giật mình ở các phân đoạn quan trọng. Kết thúc bằng CTA rõ ràng khích lệ mua ngay để giải quyết vấn đề.",
        "is_active": True
    },
    {
        "id": "reviewer_experience",
        "name": "Trải Nghiệm Thực Tế (Reviewer)",
        "platform": "TikTok/YouTube",
        "hook_template": "Bắt đầu trực tiếp bằng hành động đập hộp hoặc bôi/thử sản phẩm lên da/tay kèm lời thốt lên bất ngờ về hiệu quả thực sự.",
        "style_instruction": "Góc quay chân thực, cận cảnh bao bì và chất lượng sản phẩm (Texture/Spec). Lời thoại tự nhiên giống như đang chia sẻ lời khuyên chân thành với bạn thân. Nêu rõ ưu điểm và nhược điểm nhẹ để tăng tính khách quan (chuẩn E-E-A-T). CTA hướng tới việc xem giỏ hàng hoặc click link ở bio.",
        "is_active": True
    },
    {
        "id": "pain_point_solve",
        "name": "Giải Quyết Nỗi Đau (Pain-Agony-Relief)",
        "platform": "Shorts/Reels",
        "hook_template": "Đánh thẳng vào nỗi sợ hoặc nỗi đau lớn nhất của khách hàng (ví dụ: da mụn thâm đen, tóc rụng hói đầu) bằng hình ảnh và câu hỏi trực diện trong 3s đầu.",
        "style_instruction": "Phần đầu đồng cảm sâu sắc với sự đau khổ của khách hàng khi thử nhiều cách không hiệu quả. Phần giữa giới thiệu sản phẩm như là vị cứu tinh duy nhất có chứng chứng nhận rõ ràng. Phần cuối đưa ra bằng chứng trước/sau (Before/After) thuyết phục và CTA mua kèm ưu đãi giảm giá.",
        "is_active": True
    },
    {
        "id": "unboxing_asmr",
        "name": "Đập Hộp ASMR",
        "platform": "TikTok/Shorts",
        "hook_template": "Bắt đầu bằng âm thanh sắc nét thực tế (tiếng bóc seal nilon, tiếng cạy nắp chai nhựa) không nhạc nền trong 3s đầu.",
        "style_instruction": "Hạn chế tối đa lời thoại nói, tập trung vào tiếng động vật lý (ASMR) chất lượng cao. Visual cực kỳ sạch sẽ, tối giản và cao cấp. Chỉ thuyết minh hoặc chèn phụ đề chữ nhẹ nhàng khi cần giải thích cách dùng. Nhạc nền nhẹ nhàng, lo-fi thư giãn. Phù hợp cho các dòng sản phẩm cao cấp.",
        "is_active": True
    },
    {
        "id": "youtube_widescreen_review",
        "name": "Đánh Giá Chi Tiết (YouTube 16:9 Widescreen)",
        "platform": "YouTube",
        "hook_template": "Nêu trực tiếp giải pháp cho một vấn đề lớn và tóm tắt nhanh 3 nội dung chính của video trong 10 giây đầu để người xem không rời đi.",
        "style_instruction": "Kịch bản chi tiết chuyên sâu, nhịp độ vừa phải (5-8 giây mỗi cảnh) thiết kế chuẩn cho định dạng ngang 16:9 của YouTube. Lời thoại (Voiceover) mang tính phân tích, cung cấp thông tin hữu ích và trung thực. Visual mô tả các góc quay ngang rộng, cận cảnh sản phẩm, so sánh thông số kĩ thuật. Kết thúc bằng CTA đăng ký kênh và nhấp link mua hàng dưới phần mô tả.",
        "is_active": True
    }
]

async def seed_video_styles():
    print("🌟 Starting Video Script Styles Seeding...")
    async with async_session_maker() as session:
        try:
            # 1. Add or Update styles (Upsert logic to avoid FK violation)
            print(f"📦 Seeding/Updating {len(INITIAL_STYLES)} video styles...")
            for style_data in INITIAL_STYLES:
                stmt = select(VideoScriptStyle).where(VideoScriptStyle.id == style_data["id"])
                res = await session.execute(stmt)
                style_db = res.scalar_one_or_none()
                
                if style_db:
                    print(f"  🔄 Updating style: {style_data['id']}")
                    style_db.name = style_data["name"]
                    style_db.platform = style_data["platform"]
                    style_db.hook_template = style_data["hook_template"]
                    style_db.style_instruction = style_data["style_instruction"]
                    style_db.is_active = style_data["is_active"]
                else:
                    print(f"  🆕 Inserting new style: {style_data['id']}")
                    style_db = VideoScriptStyle(
                        id=style_data["id"],
                        name=style_data["name"],
                        platform=style_data["platform"],
                        hook_template=style_data["hook_template"],
                        style_instruction=style_data["style_instruction"],
                        is_active=style_data["is_active"]
                    )
                    session.add(style_db)
            
            await session.commit()
            print("✨ Successfully seeded Video Script Styles into database!")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_video_styles())
