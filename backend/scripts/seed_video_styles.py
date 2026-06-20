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
        "name": "Drama Kịch Tính TikTok (Chuyển Đổi Cao)",
        "platform": "TikTok",
        "hook_template": "Phát biểu ngược đời hoặc phủ nhận niềm tin cũ của khách hàng trong 3s đầu: 'Ngừng bôi kem chống nắng ngay nếu da bạn đang mụn bọc!', hoặc tạo cảnh cãi vã oái oăm về tình huống sử dụng sản phẩm.",
        "style_instruction": "Tạo kịch tính cực cao, nhịp dựng cực nhanh (1.5 - 3 giây mỗi phân cảnh). Lời thoại (Voiceover) mang tính đối thoại trực diện, có xung đột nhẹ ở phần đầu, sau đó giải quyết vấn đề bằng sản phẩm. Sử dụng hiệu ứng âm thanh dồn dập (Dramatic swoosh, vinyl scratch). CẢNH KẾT THÚC (ENDING): Áp dụng thiết kế Split Info Panel. Phân chia màn hình thành 2 phần: bên trái là sản phẩm xoay nhẹ thu hút thị giác, bên phải là bảng thông tin tối màu hiển thị Tên sản phẩm, Logo thương hiệu, Website osmo.vn và nút CTA khẩn cấp có giới hạn số lượng. Hiệu ứng âm thanh kết thúc dứt khoát dạng Hard Cut.",
        "is_active": True
    },
    {
        "id": "reviewer_experience",
        "name": "Trải Nghiệm Thực Tế (E-E-A-T Reviewer)",
        "platform": "TikTok/Reels",
        "hook_template": "Cận cảnh trải nghiệm thực tế với biểu cảm sửng sốt: 'U là trời, bỏ túi ngay em này nếu không muốn hối hận cả đời!', hoặc đập hộp trực quan không cắt ghép.",
        "style_instruction": "Tập trung vào tính khách quan và khoa học (E-E-A-T). Lời thoại tự nhiên như một người bạn thân chia sẻ bí kíp. Visual cận cảnh chất kem/chi tiết kỹ thuật, hiệu ứng âm thanh lofi nhẹ nhàng. CẢNH KẾT THÚC (ENDING): Áp dụng Before-After Recap + CTA. Chiếu nhanh 0.5s hình ảnh trước khi dùng (da xỉn màu/lỗi cũ), sau đó chuyển cảnh nhanh dạng Cross-Dissolve sang gương mặt tươi tắn của reviewer bên cạnh sản phẩm. Hiển thị chữ CTA to nổi bật kêu gọi hành động ngay: 'Click link bio để nhận ưu đãi độc quyền!' kèm hiệu ứng âm thanh Ding SFX.",
        "is_active": True
    },
    {
        "id": "pain_point_solve",
        "name": "Giải Quyết Nỗi Đau Sâu Sắc (PAS Framework)",
        "platform": "Shorts/Reels",
        "hook_template": "Đánh thẳng vào nỗi ám ảnh tồi tệ nhất của khách hàng kèm câu hỏi tu từ: 'Mặt sần sùi mụn thâm làm bạn mất tự tin trước đám đông đúng không?', hiển thị hình ảnh so sánh cực kỳ tương phản.",
        "style_instruction": "Áp dụng công thức PAS (Problem - Agitate - Solve). 30% thời lượng đầu đồng cảm sâu sắc với nỗi sợ hãi hoặc đau đớn. 40% tiếp theo giới thiệu cơ chế hoạt động khoa học của sản phẩm (USP vượt trội). CẢNH KẾT THÚC (ENDING): Áp dụng Feature Cards Cascade. Sản phẩm nằm ở vị trí trung tâm, 3 thẻ tính năng dạng kính mờ (Frosted Glass) trượt vào từ cạnh phải màn hình lần lượt mô tả các giải pháp cốt lõi. Kết thúc bằng việc hiển thị Logo thương hiệu và CTA ưu đãi giới hạn thời gian kèm hiệu ứng Text Pop SFX.",
        "is_active": True
    },
    {
        "id": "unboxing_asmr",
        "name": "Đập Hộp ASMR Sang Trọng",
        "platform": "TikTok/Shorts",
        "hook_template": "Tập trung 100% vào âm thanh vật lý chất lượng cao (tiếng bóc seal, tiếng cạy nắp sản phẩm thủy tinh kịch tính) trong 3s đầu không nhạc nền.",
        "style_instruction": "Kịch bản đậm chất nghệ thuật và tối giản. Tập trung mô tả chi tiết tiếng động vật lý (ASMR) sắc nét. Visual cực kỳ sạch sẽ, sử dụng tone màu pastel/dark sang trọng. Phụ đề xuất hiện chậm rãi, thanh lịch. Nhạc nền lofi/ambient thư thái. CẢNH KẾT THÚC (ENDING): Áp dụng Logo Reveal + Tagline. Sản phẩm từ từ đặt nhẹ lên bề mặt phản chiếu (như đá cẩm thạch đen hoặc gỗ sồi thô). Nhạc nền giảm âm lượng, Logo thương hiệu cùng Tagline tinh tế xuất hiện chính giữa màn hình với hiệu ứng phát sáng mờ ảo (Luminous Glow). Dòng chữ Website 'osmo.vn' xuất hiện nhỏ gọn ở phía dưới cùng.",
        "is_active": True
    },
    {
        "id": "product_closeup",
        "name": "Quảng Cáo Cận Cảnh (Không Mặt / Chỉ Cận Cảnh Da & Tay)",
        "platform": "TikTok/Reels/Shorts",
        "hook_template": "Cận cảnh khoảnh khắc ấn tượng nhất của sản phẩm tác động lên da (nhấn đầu xịt sương mịn, giọt serum chảy chậm trên vùng da xỉn màu...) gây kích thích thị giác cực mạnh trong 3 giây đầu.",
        "style_instruction": "Tập trung 100% vào sản phẩm, kết cấu và hiệu quả sử dụng thực tế trên da. KỊCH BẢN KHÔNG ĐƯỢC XUẤT HIỆN GƯƠNG MẶT người, chỉ sử dụng bàn tay thao tác mở nắp, nhấn vòi và thoa nhẹ chất kem/serum lên da. Visual góc quay siêu cận (Extreme Close-up), quay chậm (Slow Motion). CẢNH KẾT THÚC (ENDING): Áp dụng Split Info Panel. Màn hình chia đôi: bên trái cận cảnh bề mặt làn da mịn màng ngậm nước, bên phải là bảng thông tin tối giản hiển thị Tên sản phẩm, Logo, Website 'osmo.vn' và CTA 'Mua ngay tại giỏ hàng' với viền phát sáng nhẹ.",
        "is_active": True
    },
    {
        "id": "closeup_usage_guide",
        "name": "Hướng Dẫn Sử Dụng Cận Cảnh (Closeup Product Guide)",
        "platform": "TikTok/Reels/Shorts",
        "hook_template": "Cận cảnh thao tác bôi/thoa sản phẩm lên vùng da thực tế: 'Dùng sản phẩm này bao lâu rồi nhưng bạn đã chắc bôi đúng cách chưa?', hoặc 'Hướng dẫn dùng sản phẩm chuẩn spa tại nhà để đạt hiệu quả gấp 3 lần!'",
        "style_instruction": "Tập trung vào trải nghiệm hướng dẫn sử dụng sản phẩm cận cảnh và trực quan. Visual mô tả hành động bôi, thoa hoặc massage nhẹ nhàng chất kem, serum, dung dịch lên vùng da/tay (đối với vùng da nhạy cảm, hướng dẫn thao tác tượng trưng trên vùng mu bàn tay). Lời thoại (Voiceover) chi tiết, hướng dẫn từng bước rõ ràng. CẢNH KẾT THÚC (ENDING): Áp dụng Feature Cards Cascade. Đôi bàn tay giữ sản phẩm hướng về phía camera, 3 thẻ hướng dẫn sử dụng nhanh (Liều lượng, Tần suất, Lưu ý) trượt vào tuần tự. Kết thúc bằng việc hiển thị Logo thương hiệu và CTA kêu gọi hành động.",
        "is_active": True
    },
    {
        "id": "scientific_ingredients",
        "name": "Show Thành Phần Khoa Học & Tính Năng Chuyên Nghiệp (Brand Spotlight)",
        "platform": "TikTok/Reels/YouTube",
        "hook_template": "Cận cảnh kết cấu zoom cực cận (Extreme Close-up) hoặc hiệu ứng hoạt cảnh tách phân tử thành phần: 'Đây là lý do tại sao [Thành phần A] lại có thể cứu rỗi làn da của bạn chỉ sau 7 ngày!', hoặc hình ảnh trực quan mô tả tính năng nổi bật của sản phẩm.",
        "style_instruction": "Tập trung giới thiệu các thành phần cốt lõi và công nghệ/tính năng độc quyền của sản phẩm theo phong cách chuyên nghiệp của các thương hiệu lớn toàn cầu. Visual kết hợp mô tả góc quay cận cảnh sang trọng, ánh sáng studio chuẩn High-Key, chất kem/serum dưới dạng các phân tử hoặc giọt dưỡng chất cô đặc rơi chậm. CẢNH KẾT THÚC (ENDING): Áp dụng Logo Reveal + Tagline. Hoạt cảnh phân tử hoặc mô hình 3D chuyển động mượt mà hóa thân thành Logo thương hiệu sáng lấp lánh ở trung tâm màn hình. Hiển thị Tagline định vị thương hiệu và Website 'osmo.vn' ở bên dưới với font chữ sans-serif tinh xảo, chuyên nghiệp.",
        "is_active": True
    },
    {
        "id": "youtube_widescreen_review",
        "name": "Đánh Giá Chi Tiết Chuyên Sâu (YouTube Widescreen)",
        "platform": "YouTube",
        "hook_template": "Đặt vấn đề thời sự hoặc nhu cầu cấp thiết của thị trường và tóm tắt nhanh 3 bài học đắt giá người xem sẽ nhận được ở video trong 10s đầu.",
        "style_instruction": "Kịch bản chuyên sâu chuẩn định dạng ngang 16:9. Nhịp điệu phân tích vừa phải, chắc chắn (4 - 6 giây mỗi cảnh). Lời thoại cung cấp thông tin giá trị cao, giải thích nguyên lý khoa học đằng sau sản phẩm. CẢNH KẾT THÚC (ENDING): Áp dụng Split Info Panel ở định dạng ngang rộng. Phía bên trái hiển thị sản phẩm đứng tĩnh sang trọng trên bục studio, phía bên phải hiển thị bảng thông tin lớn chứa các kênh mạng xã hội, nút đăng ký kênh Youtube (Subscribe) nhấp nháy thu hút, kèm link mua hàng nổi bật trên màn hình.",
        "is_active": True
    },
    {
        "id": "tiktok_viral_trend",
        "name": "⚡ TikTok Viral Trend (POV / Trend Format / Sound Sync)",
        "platform": "TikTok",
        "hook_template": "3 giây đầu PHẢI là một trong các format viral đang trending: 'POV: Bạn vừa phát hiện ra...', 'Dừng scroll! Nếu bạn đang [vấn đề], đây là thứ bạn cần ngay'. Visual cảnh 1 PHẢI có chuyển động đột ngột hoặc zoom punch vào mặt sản phẩm.",
        "style_instruction": """[PHONG CÁCH TIKTOK VIRAL TREND — CHUẨN PRODUCTION 2025]
MỤC TIÊU: Kịch bản tạo ra video có khả năng viral tự nhiên trên TikTok bằng cách tận dụng tâm lý người xem, format trend và kỹ thuật giữ chân tối ưu thuật toán.
━━━ NHỊP ĐỘ & CẤU TRÚC CẢNH ━━━
• Mỗi cảnh: 1.5 - 2.5 giây.
• scene_notes BẮT BUỘC ghi: loại transition (Jump Cut / Whip Pan / Smash Cut / Zoom Punch) và timing (on-beat / off-beat).
━━━ GIỌNG NÓI & ÂM THANH ━━━
• Tốc độ đọc: 3.0 - 3.5 từ/giây. Dùng câu ngắn, câu hỏi tu từ.
• Cảnh HOOK: Trending sound + hiệu ứng "whoosh" hoặc "record scratch".
• Cảnh SOLUTION: Upbeat transition music, âm thanh "ding!" khi reveal sản phẩm.
━━━ CẢNH KẾT THÚC (ENDING) ━━━
• Áp dụng Before-After Recap + CTA. Chiếu nhanh chuyển đổi kết quả tóm tắt trong 1 giây, xuất hiện text CTA nhấp nháy nhịp nhàng theo nhạc nền: "NHẤN VÀO GIỎ HÀNG ⬇️" hoặc "MUA NGAY TẠI BIO 🛒" màu đỏ/vàng cực kỳ bắt mắt.
• Loop Trigger: Thiết kế câu cuối của voiceover kết nối trực tiếp với câu thoại/visual của giây đầu tiên tạo vòng lặp vô hạn.""",
        "is_active": True
    },
    {
        "id": "tiktok_storytelling_viral",
        "name": "📖 TikTok Story-Time Viral (Dẫn Chuyện Kéo Dài 60s)",
        "platform": "TikTok",
        "hook_template": "Mở đầu bằng câu chuyện gây sốc/bất ngờ ở ngôi thứ nhất, đặt người xem vào tình huống khó xử hoặc tò mò cực cao: 'Tôi đã mất tự tin trong 2 năm vì điều này cho đến khi...', 'Đây là sai lầm đắt giá nhất của tôi với [vấn đề]...'",
        "style_instruction": """[PHONG CÁCH TIKTOK STORY-TIME VIRAL — DẠNG KỂ CHUYỆN LÔI CUỐN]
MỤC TIÊU: Kịch bản kể chuyện ở ngôi thứ nhất, tạo cảm giác authentic và personal, khiến người xem đồng cảm sâu sắc.
━━━ CẤU TRÚC NARRATIVE (STORY ARC) ━━━
• Act 1 — HOOK (0-5s): Câu mở đầu gây shock/tò mò ở ngôi thứ nhất.
• Act 2 — SETUP/CONFLICT (5-20s): Kể câu chuyện nỗi đau cụ thể, chi tiết cảm xúc.
• Act 3 — TURNING POINT (20-35s): Moment khám phá sản phẩm/giải pháp tự nhiên.
• Act 4 — TRANSFORMATION (35-50s): Kết quả cụ thể, before/after thuyết phục.
━━━ CẢNH KẾT THÚC (ENDING) ━━━
• Áp dụng Feature Cards Cascade. Thể hiện tóm tắt hành trình chuyển đổi kỳ diệu của nhân vật thông qua các thẻ tính năng Frosted Glass trượt vào từ cạnh phải.
• Lời khuyên chân thành từ nhân vật chính, kết hợp hiển thị text CTA bounce nhẹ nhàng kêu gọi mua hàng để chấm dứt nỗi đau: 'Mình để link ở bio nhé 🛒' hoặc 'Nhấn mua ngay để cải thiện làn da như mình nha!'.""",
        "is_active": True
    },
    {
        "id": "product_animation",
        "name": "Sản Phẩm Animation Chuyên Nghiệp",
        "platform": "TikTok/Reels/YouTube",
        "hook_template": "Cảnh 1: Một góc quay cận cảnh cực kỳ độc đáo và không tưởng về sản phẩm (Ví dụ: sản phẩm bay lơ lửng trong không trung, xoay 360 độ mượt mà, hoặc các thành phần bùng nổ xung quanh chai sản phẩm). Nhạc nền chuyển động mạnh mẽ (upbeat / dynamic). Lời thoại cuốn hút, đi thẳng vào đặc tính nổi bật nhất của sản phẩm.",
        "style_instruction": """[PHONG CÁCH VIDEO SẢN PHẨM ANIMATION CHUYÊN NGHIỆP]
MỤC TIÊU: Kịch bản được thiết kế tối ưu cho việc sinh prompt hình ảnh và chuyển động AI (Luma/Kling/Runway Gen-3) để tạo ra video animation thương mại (Commercial Product Animation) đẳng cấp cao.
━━━ CẤU TRÚC KỊCH BẢN & MÔ TẢ VISUAL ━━━
• visual_description BẮT BUỘC mô tả rõ ràng: Góc quay camera (360° orbital spin, macro zoom, crane down), Chuyển động vật lý (floating, liquid splash, particles exploding), Ánh sáng (studio softbox, cinematic rim light, neon glowing border) và Môi trường xung quanh (bục đá cẩm thạch, mặt nước gợn sóng).
• Lời thoại (Voiceover): Mang tính dẫn dắt khoa học hoặc khơi gợi cảm xúc cao, nhịp điệu đọc khoan thai, sang trọng.
━━━ CẢNH KẾT THÚC (ENDING) ━━━
• Áp dụng Logo Reveal + Tagline hoặc Split Info Panel kết hợp hiệu ứng Animation phát sáng mượt mà.
• Text hiển thị rõ ràng thông tin sản phẩm và nút CTA (Ví dụ: Website osmo.vn, Logo thương hiệu nổi bật trên nền tối tối giản).""",
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
