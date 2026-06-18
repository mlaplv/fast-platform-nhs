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
        "style_instruction": "Tạo kịch tính cực cao, nhịp dựng cực nhanh (1.5 - 3 giây mỗi phân cảnh). Lời thoại (Voiceover) mang tính đối thoại trực diện, có xung đột nhẹ ở phần đầu, sau đó giải quyết vấn đề bằng sản phẩm. Sử dụng hiệu ứng âm thanh dồn dập (Dramatic swoosh, vinyl scratch, record scratch). Kêu gọi hành động (CTA) khẩn cấp với số lượng có hạn.",
        "is_active": True
    },
    {
        "id": "reviewer_experience",
        "name": "Trải Nghiệm Thực Tế (E-E-A-T Reviewer)",
        "platform": "TikTok/Reels",
        "hook_template": "Cận cảnh trải nghiệm thực tế với biểu cảm sửng sốt: 'U là trời, bỏ túi ngay em này nếu không muốn hối hận cả đời!', hoặc đập hộp trực quan không cắt ghép.",
        "style_instruction": "Tập trung vào tính khách quan và khoa học (E-E-A-T). Lời thoại như một người bạn thân chia sẻ bí kíp, giọng điệu tự nhiên, chân thành. Nêu rõ 3 điểm vượt trội của sản phẩm và chỉ ra 1 nhược điểm nhỏ không đáng kể để tăng độ uy tín. Visual cận cảnh chất kem/chi tiết kỹ thuật, hiệu ứng âm thanh lofi nhẹ nhàng.",
        "is_active": True
    },
    {
        "id": "pain_point_solve",
        "name": "Giải Quyết Nỗi Đau Sâu Sắc (PAS Framework)",
        "platform": "Shorts/Reels",
        "hook_template": "Đánh thẳng vào nỗi ám ảnh tồi tệ nhất của khách hàng kèm câu hỏi tu từ: 'Mặt sần sùi mụn thâm làm bạn mất tự tin trước đám đông đúng không?', hiển thị hình ảnh so sánh cực kỳ tương phản.",
        "style_instruction": "Áp dụng công thức PAS (Problem - Agitate - Solve). 30% thời lượng đầu đồng cảm sâu sắc với nỗi sợ hãi hoặc đau đớn của khách hàng. 40% tiếp theo giới thiệu cơ chế hoạt động khoa học của sản phẩm (USP vượt trội so với đối thủ). 30% cuối đưa ra bằng chứng trước/sau (Before/After) thuyết phục và CTA ưu đãi giới hạn.",
        "is_active": True
    },
    {
        "id": "unboxing_asmr",
        "name": "Đập Hộp ASMR Sang Trọng",
        "platform": "TikTok/Shorts",
        "hook_template": "Tập trung 100% vào âm thanh vật lý chất lượng cao (tiếng bóc seal, tiếng cạy nắp sản phẩm thủy tinh kịch tính) trong 3s đầu không nhạc nền.",
        "style_instruction": "Kịch bản đậm chất nghệ thuật và tối giản. Không dùng nhiều lời thoại, tập trung mô tả chi tiết tiếng động vật lý (ASMR) sắc nét. Visual cực kỳ sạch sẽ, tinh tế, sử dụng tone màu pastel/dark sang trọng. Phụ đề xuất hiện chậm rãi, thanh lịch. Nhạc nền lofi/ambient thư thái.",
        "is_active": True
    },
    {
        "id": "product_closeup",
        "name": "Quảng Cáo Cận Cảnh (Không Mặt / Chỉ Cận Cảnh Da & Tay)",
        "platform": "TikTok/Reels/Shorts",
        "hook_template": "Cận cảnh khoảnh khắc ấn tượng nhất của sản phẩm tác động lên da (nhấn đầu xịt sương mịn, giọt serum chảy chậm trên vùng da xỉn màu...) gây kích thích thị giác cực mạnh trong 3 giây đầu.",
        "style_instruction": "Tập trung 100% vào sản phẩm, kết cấu và hiệu quả sử dụng thực tế trên da. KỊCH BẢN KHÔNG ĐƯỢC XUẤT HIỆN GƯƠNG MẶT người, chỉ được phép sử dụng bàn tay thao tác mở nắp, nhấn vòi, và thoa nhẹ chất kem/serum lên vùng da nhạy cảm cần chăm sóc (như nách, bẹn, cánh tay). Visual sử dụng góc quay siêu cận (Extreme Close-up), quay chậm (Slow Motion) từng khoảnh khắc chất kem thẩm thấu nhanh chóng, không để lại vết bết dính. Lời thoại (Voiceover) ngắn gọn, giọng đọc nhẹ nhàng, mô tả chân thực cảm giác mát mịn, khô thoáng và sự thay đổi độ sáng khỏe của làn da tức thì. Nhạc nền hiện đại, êm dịu, tinh tế.",
        "is_active": True
    },
    {
        "id": "closeup_usage_guide",
        "name": "Hướng Dẫn Sử Dụng Cận Cảnh (Closeup Product Guide)",
        "platform": "TikTok/Reels/Shorts",
        "hook_template": "Cận cảnh thao tác bôi/thoa sản phẩm lên vùng da thực tế: 'Dùng sản phẩm này bao lâu rồi nhưng bạn đã chắc bôi đúng cách chưa?', hoặc 'Hướng dẫn dùng sản phẩm chuẩn spa tại nhà để đạt hiệu quả gấp 3 lần!'",
        "style_instruction": "Tập trung vào trải nghiệm hướng dẫn sử dụng sản phẩm cận cảnh và trực quan. Visual mô tả hành động bôi, thoa hoặc massage nhẹ nhàng chất kem, serum, dung dịch lên vùng da/tay. Lưu ý đặc biệt: để bảo vệ tính văn minh và thẩm mỹ của video quảng cáo, đối với các vùng da nhạy cảm (như vùng bikini, nách, bẹn), kịch bản tuyệt đối KHÔNG ĐƯỢC chỉ định quay vùng nhạy cảm thực tế, mà bắt buộc phải hướng dẫn thao tác tượng trưng trên vùng mu bàn tay (ví dụ: bôi thử và massage nhẹ nhàng trên mu bàn tay để mô tả kết cấu, độ thẩm thấu và cách thoa). Lời thoại (Voiceover) chi tiết, hướng dẫn từng bước rõ ràng, khoa học, chỉ ra tần suất và lưu ý khi sử dụng. Nhạc nền lofi nhẹ nhàng, tạo cảm giác thư giãn, uy tín và chuyên nghiệp.",
        "is_active": True
    },
    {
        "id": "scientific_ingredients",
        "name": "Show Thành Phần Khoa Học & Tính Năng Chuyên Nghiệp (Brand Spotlight)",
        "platform": "TikTok/Reels/YouTube",
        "hook_template": "Cận cảnh kết cấu zoom cực cận (Extreme Close-up) hoặc hiệu ứng hoạt cảnh tách phân tử thành phần: 'Đây là lý do tại sao [Thành phần A] lại có thể cứu rỗi làn da của bạn chỉ sau 7 ngày!', hoặc hình ảnh trực quan mô tả tính năng nổi bật của sản phẩm.",
        "style_instruction": "Tập trung giới thiệu các thành phần cốt lõi (key ingredients) và công nghệ/tính năng độc quyền của sản phẩm theo phong cách chuyên nghiệp của các thương hiệu lớn toàn cầu. Visual kết hợp mô tả góc quay cận cảnh sang trọng, ánh sáng studio chuẩn High-Key, cận cảnh chất kem/serum dưới dạng các phân tử hoặc giọt dưỡng chất cô đặc rơi chậm. Có thể mô tả các biểu đồ khoa học, mô hình phân tử 3D hoặc cơ chế tác động trực quan lên lớp biểu bì da để làm nổi bật tính chuyên sâu. Lời thoại (Voiceover) súc tích, chuyên nghiệp, sử dụng ngôn ngữ khoa học đáng tin cậy nhưng dễ hiểu, nhấn mạnh USP độc quyền của sản phẩm so với thị trường. Nhạc nền hiện đại, mang hơi hướng công nghệ (corporate tech hoặc futuristic electronic) nhưng vẫn tinh tế, sang trọng.",
        "is_active": True
    },
    {
        "id": "youtube_widescreen_review",
        "name": "Đánh Giá Chi Tiết Chuyên Sâu (YouTube Widescreen)",
        "platform": "YouTube",
        "hook_template": "Đặt vấn đề thời sự hoặc nhu cầu cấp thiết của thị trường và tóm tắt nhanh 3 bài học đắt giá người xem sẽ nhận được ở video trong 10s đầu.",
        "style_instruction": "Kịch bản chuyên sâu chuẩn định dạng ngang 16:9. Nhịp điệu phân tích vừa phải, chắc chắn (4 - 6 giây mỗi cảnh). Lời thoại cung cấp thông tin giá trị cao, giải thích nguyên lý khoa học đằng sau sản phẩm. Phân tích đối thủ cạnh tranh một cách khách quan để làm nổi bật USP của sản phẩm ta. CTA đăng ký kênh và nhấp link mua hàng.",
        "is_active": True
    },
    {
        "id": "tiktok_viral_trend",
        "name": "⚡ TikTok Viral Trend (POV / Trend Format / Sound Sync)",
        "platform": "TikTok",
        "hook_template": "3 giây đầu PHẢI là một trong các format viral đang trending: 'POV: Bạn vừa phát hiện ra...', 'Dừng scroll! Nếu bạn đang [vấn đề], đây là thứ bạn cần ngay', hoặc bắt đầu bằng khoảnh khắc cao trào/kết quả gây shock rồi mới kể lại câu chuyện (Hook bằng kết quả). Visual cảnh 1 PHẢI có chuyển động đột ngột hoặc zoom punch vào mặt sản phẩm.",
        "style_instruction": """[PHONG CÁCH TIKTOK VIRAL TREND — CHUẨN PRODUCTION 2025]

MỤC TIÊU: Kịch bản tạo ra video có khả năng viral tự nhiên trên TikTok bằng cách tận dụng tâm lý người xem, format trend và kỹ thuật giữ chân tối ưu thuật toán.

━━━ NHỊP ĐỘ & CẤU TRÚC CẢNH ━━━
• Mỗi cảnh: 1.5 - 2.5 giây (không được quá 3s, thuật toán TikTok phạt video nhịp chậm).
• Luật 3-Cut: Cứ mỗi 3 cảnh liên tiếp PHẢI đổi góc máy hoàn toàn (Close-up → Medium → Overhead hoặc ngược lại).
• scene_notes BẮT BUỘC ghi: loại transition (Jump Cut / Whip Pan / Smash Cut / Zoom Punch) và timing (on-beat / off-beat).

━━━ GIỌNG NÓI (VOICEOVER / TTS) ━━━
• Tốc độ đọc: 3.0 - 3.5 từ/giây, giọng trẻ trung, nhiều năng lượng.
• Câu cực ngắn: 4-8 từ/câu. Dùng câu hỏi tu từ, dừng ngắt đột ngột ("Và bạn biết điều gì không?", "Đúng vậy.", "Không phải thế đâu.").
• KHÔNG dùng câu dài dòng, mệnh đề phụ lồng nhau.
• Kỹ thuật Pattern Interrupt: Mỗi 5-7 giây PHẢI có 1 thay đổi về giọng nói hoặc câu gây bất ngờ để chặn swipe.

━━━ ÂM THANH & NHẠC NỀN ━━━
scene_notes PHẢI ghi rõ loại âm thanh cho từng cảnh:
• Cảnh HOOK: Trending sound on TikTok (ghi: "Sử dụng trending audio hiện tại trên FYP / viral sound week") + hiệu ứng "whoosh" hoặc "record scratch" đồng bộ với visual cut.
• Cảnh PAIN: Nhạc lo-fi căng thẳng nhẹ + tiếng heartbeat SFX ở điểm nhấn.
• Cảnh SOLUTION: Upbeat transition music, âm thanh "ding!" khi reveal sản phẩm.
• Cảnh PROOF: Nhạc nền hype nhẹ, không lấn át voiceover.
• Cảnh CTA: Hard cut âm thanh + text pop SFX.
• Toàn bộ: Beat sync — các cut chuyển cảnh PHẢI rơi vào nhịp phách (on-beat cut).

━━━ TEXT OVERLAY & CAPTION ━━━
scene_notes PHẢI ghi rõ text overlay cho mỗi cảnh:
• Cảnh 1 (Hook): Text lớn, màu trắng bold viền đen, xuất hiện cùng lúc với visual: "[Câu hook dạng keyword ngắn]". Font: TikTok default heavy hoặc Impact.
• Cảnh Pain/Solution: Text nhỏ hơn, highlight từ khóa chính (màu vàng hoặc cyan), xuất hiện 0.3s sau visual.
• Cảnh CTA: Text CTA nhấp nháy hoặc bounce animation, màu đỏ/vàng nổi bật: "NHẤN VÀO LINK 👆" hoặc "MUA NGAY ⬇️".
• Auto Caption: Ghi "Full caption auto-sync with voiceover" trong scene_notes cảnh cuối.

━━━ HIỆU ỨNG VIDEO (EFFECTS) ━━━
scene_notes nên đề xuất effect cụ thể:
• Zoom Punch: Zoom nhanh vào sản phẩm/kết quả ở cảnh reveal. Ghi: "Zoom punch 150% tốc độ 0.2s, on-beat".
• Green Screen: Nếu cần background thay đổi. Ghi: "Green screen background: [mô tả background cụ thể]".
• Slow Motion: Dùng cho cảnh highlight sản phẩm. Ghi: "Slow motion 0.3x — [hành động cụ thể]".
• Text-to-screen animation: Pop-in text, typewriter effect cho các từ khóa.
• Transition hiệu ứng: Whip Pan (quay nhanh camera), Smash Cut, POV Shake.

━━━ VISUAL DESCRIPTION — CHUẨN AI PROMPT ━━━
Mỗi visual_description PHẢI là prompt AI đầy đủ theo công thức:
[Góc máy 9:16] + [Chủ thể + hành động vật lý cụ thể] + [Ánh sáng] + [Màu/Texture] + [Phong cách render] + [Effect gợi ý]

Ví dụ chuẩn:
"Vertical 9:16 close-up POV shot, female hand holding skincare bottle at eye level, soft ring light from front creating catchlight, white minimal studio background, slight motion blur on entry, TikTok-native vertical composition, cinematic commercial grade, photorealistic 4K"

━━━ FORMAT TREND ĐỀ XUẤT ━━━
Tùy theo nội dung, chọn 1 format trend:
• POV Format: "POV: Bạn vừa thử [sản phẩm] lần đầu..." — toàn bộ video quay từ góc nhìn người dùng.
• Before/After Reveal: Cảnh 1-3: Vấn đề → Cảnh 4-6: Dùng sản phẩm → Cảnh 7-10: Kết quả wow.
• "Wait for it" Format: Build-up dần với voiceover "Và đây là điều bạn không ngờ tới..." trước cảnh reveal.
• Stitch/Duet Bait: Thiết kế cảnh đầu có yếu tố câu hỏi bỏ lửng để khuyến khích người dùng stitch.
• Day-in-life Integration: Lồng ghép sản phẩm vào routine hàng ngày tự nhiên.

━━━ THUẬT TOÁN TIKTOK — ĐIỂM GIỮ CHÂN ━━━
• Loop Trigger: Cảnh cuối PHẢI loop được về cảnh đầu (cùng âm thanh hoặc visual) để tạo re-watch.
• Completion Rate: Chia kịch bản thành 3 "cliffhanger nhỏ" để người xem xem hết: giây 0-5 (Hook), giây 5-15 (Reveal bất ngờ), giây 15-hết (Kết quả + CTA).
• Comment Bait: scene_notes cảnh cuối ghi thêm: "Text overlay: '[Câu hỏi mở để comment]' — ví dụ: 'Bạn đã thử chưa? Comment 👇'".""",
        "is_active": True
    },
    {
        "id": "tiktok_storytelling_viral",
        "name": "📖 TikTok Story-Time Viral (Dẫn Chuyện Kéo Dài 60s)",
        "platform": "TikTok",
        "hook_template": "Mở đầu bằng câu chuyện gây sốc/bất ngờ ở ngôi thứ nhất, đặt người xem vào tình huống khó xử hoặc tò mò cực cao: 'Tôi đã mất tự tin trong 2 năm vì điều này cho đến khi...', 'Đây là sai lầm đắt giá nhất của tôi với [vấn đề]...', 'Không ai nói cho tôi biết điều này trước đây và tôi ước...'",
        "style_instruction": """[PHONG CÁCH TIKTOK STORY-TIME VIRAL — DẠNG KỂ CHUYỆN LÔI CUỐN]

MỤC TIÊU: Kịch bản kể chuyện ở ngôi thứ nhất, tạo cảm giác authentic và personal, khiến người xem đồng cảm sâu sắc và cảm thấy câu chuyện là của chính mình. Video dài 45-60 giây, tỷ lệ xem hết (completion rate) cao nhờ narrative arc mạnh.

━━━ CẤU TRÚC NARRATIVE (STORY ARC) ━━━
Kịch bản PHẢI đi theo đúng 5 Act cảm xúc:
• Act 1 — HOOK (0-5s): Câu mở đầu gây shock/tò mò ở ngôi thứ nhất. Không giới thiệu sản phẩm.
• Act 2 — SETUP/CONFLICT (5-20s): Kể câu chuyện nỗi đau cụ thể, chi tiết cảm xúc (không nói chung chung). Người xem phải thấy mình trong đó.
• Act 3 — TURNING POINT (20-35s): Moment khám phá sản phẩm/giải pháp. Kể tự nhiên như kể chuyện bạn bè.
• Act 4 — TRANSFORMATION (35-50s): Kết quả cụ thể, số liệu thực, cảm xúc thay đổi. Before vs After.
• Act 5 — CTA + LOOP (50-60s): Lời khuyên chân thành + CTA + câu kết có thể loop về đầu.

━━━ GIỌNG KỂ CHUYỆN ━━━
• Ngôi thứ nhất hoàn toàn: "Tôi", "Mình", "Bạn và tôi", không nói "sản phẩm này".
• Dùng chi tiết cụ thể tạo hình ảnh: Không "Tôi mất tự tin", mà "Hôm đó tôi mặc áo trắng đi họp, 10 phút sau đã vết ố vàng nách, tôi phải cả buổi che tay vào người".
• Tạo Pattern Interrupt mỗi 8-10s: "Nhưng điều kỳ lạ là...", "Và bạn biết không...", "Đây mới là phần hay..."
• Tốc độ đọc: 2.8 - 3.2 từ/giây, giọng tâm tình, chân thật, không theatrical.

━━━ NHỊP ĐỘ CẢNH ━━━
• Act 1-2: Cảnh 3-4s, hơi chậm để build cảm xúc. Visual POV hoặc medium shot.
• Act 3: Cut nhanh 2s khi reveal sản phẩm — zoom punch vào sản phẩm.
• Act 4-5: Cảnh 2-3s, nhịp tăng dần, kết thúc bằng shot energetic.
• Transition: Dùng Cross Dissolve cho Act 1-2, Jump Cut cho Act 3-4.

━━━ ÂM THANH ━━━
• Act 1-2: Nhạc nền tâm tình, lo-fi hoặc acoustic guitar nhẹ nhàng. Volume thấp để không lấn tiếng kể.
• Act 3 (reveal): Beat drop nhẹ hoặc uplifting transition sound + ding SFX.
• Act 4-5: Upbeat pop/electronic nhẹ, tạo cảm giác chiến thắng.
• Toàn video: Voiceover > music (music chỉ 20-30% volume).

━━━ TEXT OVERLAY ━━━
• Act 1: Text lớn highlight câu hook — chữ trắng nền đen hoặc không nền, font bold.
• Act 2: Text phụ nhỏ bổ sung chi tiết. Ví dụ: "[Tên vấn đề] — [Thời gian khổ sở]".
• Act 3: Text reveal: "Cho đến khi tôi tìm ra [tên sản phẩm]" — xuất hiện đồng thời với zoom punch.
• Act 4: Text kết quả số liệu: "Sau 7 ngày: [Kết quả cụ thể]" — font bold, màu nổi bật.
• Act 5: Text CTA bounce: "Mình để link ở bio / Nhấn giỏ hàng bên dưới 🛒".

━━━ VISUAL DESCRIPTION — CHUẨN AI PROMPT ━━━
Act 1-2: "Vertical 9:16 medium shot, young Vietnamese woman sitting at desk, slightly anxious expression, natural daylight from window left, realistic skin texture, no makeup look, contemporary home setting, shallow depth of field, cinema vérité style"
Act 3: "Vertical 9:16 extreme close-up product shot, [product name] bottle/tube in hand, soft studio key light from top-right, clean white or minimal background, sharp label in focus, slight motion coming into frame (product reveal), photorealistic commercial grade"
Act 4-5: "Vertical 9:16 medium shot, same woman now confident and bright, warm golden hour light, clear skin visible, product in background shelf, relaxed natural smile, lifestyle commercial aesthetic"

━━━ COMMENT BAIT & VIRALITY ━━━
• Cuối video (scene_notes Act 5): "Text overlay: '[Câu hỏi mở liên quan nỗi đau của họ]' — VD: 'Ai đang gặp vấn đề tương tự? Comment ⬇️' hoặc 'Tag bạn cần biết điều này 👇'".
• Loop setup: Câu cuối cùng của voiceover phải connect về câu đầu (vòng tròn cảm xúc).
• Stitch bait: Scene đầu đặt câu hỏi bỏ lửng có thể dùng làm stitch.""",
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
