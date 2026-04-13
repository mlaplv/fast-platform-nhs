import os
import sys
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Setup path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models import Article, User

TENANT_ID = "smartshop"

POLICIES = [
    {
        "id": "policy_privacy",
        "title": "Chính sách Bảo mật Thông tin",
        "slug": "chinh-sach-bao-mat",
        "excerpt": "Cam kết bảo mật tuyệt đối thông tin cá nhân của khách hàng khi tham gia mua sắm tại micsmo.com.",
        "content": """
            <h2>1. Mục đích thu thập thông tin cá nhân</h2>
            <p>Việc thu thập dữ liệu chủ yếu trên Website TMĐT micsmo.com bao gồm: email, điện thoại, tên đăng nhập, mật khẩu đăng nhập, địa chỉ khách hàng (thành viên). Đây là các thông tin mà micsmo.com cần thành viên cung cấp bắt buộc khi đăng ký sử dụng dịch vụ và để micsmo.com liên hệ xác nhận khi khách hàng đăng ký sử dụng dịch vụ trên website nhằm đảm bảo quyền lợi cho cho người tiêu dùng.</p>
            
            <h2>2. Phạm vi sử dụng thông tin</h2>
            <p>Website TMĐT micsmo.com sử dụng thông tin thành viên cung cấp để:</p>
            <ul>
                <li>Cung cấp các dịch vụ đến Thành viên.</li>
                <li>Gửi các thông báo về các hoạt động trao đổi thông tin giữa thành viên và Website TMĐT micsmo.com.</li>
                <li>Ngăn ngừa các hoạt động phá hủy tài khoản người dùng của thành viên hoặc các hoạt động giả mạo Thành viên.</li>
                <li>Liên lạc và giải quyết với thành viên trong những trường hợp đặc biệt.</li>
            </ul>

            <h2>3. Thời gian lưu trữ thông tin</h2>
            <p>Dữ liệu cá nhân của Thành viên sẽ được lưu trữ cho đến khi có yêu cầu hủy bỏ hoặc tự thành viên đăng nhập và thực hiện hủy bỏ. Còn lại trong mọi trường hợp thông tin cá nhân thành viên sẽ được bảo mật trên máy chủ của micsmo.com.</p>

            <h2>4. Những người hoặc tổ chức có thể được tiếp cận với thông tin đó</h2>
            <p>Chúng tôi không cung cấp thông tin cá nhân của bạn cho bất kỳ bên thứ ba nào trừ trường hợp có yêu cầu từ cơ quan nhà nước có thẩm quyền hoặc để phục vụ việc giao hàng (cung cấp tên, sđt, địa chỉ cho đơn vị vận chuyển).</p>

            <h2>5. Cam kết bảo mật thông tin cá nhân khách hàng</h2>
            <p>Thông tin cá nhân của thành viên trên micsmo.com được micsmo.com cam kết bảo mật tuyệt đối theo chính sách bảo vệ thông tin cá nhân của micsmo.com. Việc thu thập và sử dụng thông tin của mỗi thành viên chỉ được thực hiện khi có sự đồng ý của khách hàng đó trừ những trường hợp pháp luật có quy định khác.</p>
        """,
        "seo_title": "Chính sách Bảo mật Thông tin - micsmo.com",
        "seo_description": "Xem quy định về bảo mật dữ liệu và quyền riêng tư của khách hàng tại micsmo.com."
    },
    {
        "id": "policy_terms",
        "title": "Điều khoản Dịch vụ",
        "slug": "dieu-khoan-dich-vu",
        "excerpt": "Các quy định và thỏa thuận pháp lý khi khách hàng truy cập và mua sắm tại nền tảng micsmo.com.",
        "content": """
            <h2>1. Chấp nhận điều khoản</h2>
            <p>Bằng việc truy cập và sử dụng Website, bạn đồng ý bị ràng buộc bởi các điều khoản và điều kiện này. Chúng tôi có quyền thay đổi, chỉnh sửa các điều khoản này bất cứ lúc nào mà không cần thông báo trước.</p>
            
            <h2>2. Tài khoản người dùng</h2>
            <p>Khi đăng ký tài khoản, bạn phải cung cấp thông tin chính xác và đầy đủ. Bạn chịu trách nhiệm về việc bảo mật mật khẩu và tất cả các hoạt động diễn ra dưới tài khoản của mình.</p>

            <h2>3. Quyền sở hữu trí tuệ</h2>
            <p>Mọi nội dung trên website bao gồm văn bản, hình ảnh, logo đều thuộc sở hữu của HKD Văn Lập hoặc các đối tác. Nghiêm cấm mọi hành vi sao chép khi chưa được phép.</p>

            <h2>4. Giới hạn trách nhiệm</h2>
            <p>Chúng tôi nỗ lực cung cấp thông tin chính xác về sản phẩm nhưng không chịu trách nhiệm cho các sai sót kỹ thuật hoặc thông tin từ bên thứ ba cung cấp qua link liên kết.</p>
        """,
        "seo_title": "Điều khoản Dịch vụ và Quy định Chung - micsmo.com",
        "seo_description": "Tìm hiểu các quy định sử dụng dịch vụ, quyền và nghĩa vụ của người dùng tại micsmo.com."
    },
    {
        "id": "policy_refund",
        "title": "Chính sách Đổi trả & Hoàn tiền",
        "slug": "chinh-sach-doi-tra-hoan-tien",
        "excerpt": "Quy định chi tiết về thời hạn, điều kiện và quy trình đổi trả hàng hóa dành cho khách hàng.",
        "content": """
            <h2>1. Thời hạn đổi trả</h2>
            <p>Khách hàng có thể thực hiện đổi trả hàng trong vòng <b>07 ngày</b> kể từ ngày nhận hàng (theo vận đơn của đơn vị vận chuyển).</p>
            
            <h2>2. Điều kiện đổi trả</h2>
            <ul>
                <li>Sản phẩm còn nguyên tem mác, seals (nếu có).</li>
                <li>Sản phẩm chưa qua sử dụng, không bị hư hỏng do lỗi người dùng.</li>
                <li>Sản phẩm bị lỗi do nhà sản xuất hoặc bị hư hỏng trong quá trình vận chuyển.</li>
                <li>Giao sai mẫu mã, số lượng so với đơn đặt hàng.</li>
            </ul>

            <h2>3. Quy trình thực hiện</h2>
            <p>Bước 1: Liên hệ Hotline 0978785079 hoặc nhắn tin qua Zalo/Fanpage để thông báo lỗi.</p>
            <p>Bước 2: Cung cấp bằng chứng (Video mở hàng/Ảnh chụp lỗi).</p>
            <p>Bước 3: Gửi hàng về kho theo hướng dẫn của nhân viên tư vấn.</p>

            <h2>4. Phương thức hoàn tiền</h2>
            <p>Sau khi nhận được hàng trả về và kiểm tra hợp lệ, chúng tôi sẽ thực hiện hoàn tiền qua tài khoản ngân hàng của khách hàng trong vòng 3-5 ngày làm việc.</p>
        """,
        "seo_title": "Chính sách Đổi trả & Hoàn tiền trong 7 ngày - micsmo.com",
        "seo_description": "Hướng dẫn quy trình đổi trả hàng và hoàn tiền nhanh chóng tại micsmo.com."
    },
    {
        "id": "policy_shipping",
        "title": "Chính sách Vận chuyển & Giao nhận",
        "slug": "chinh-sach-van-chuyen",
        "excerpt": "Thông tin về phạm vi giao hàng, thời gian và cước phí vận chuyển toàn quốc.",
        "content": """
            <h2>1. Phạm vị giao hàng</h2>
            <p>Chúng tôi giao hàng trên toàn quốc (63 tỉnh thành) thông qua các đối tác vận chuyển uy tín (GHTK, Viettel Post, v.v.).</p>
            
            <h2>2. Thời gian giao hàng dự kiến</h2>
            <ul>
                <li>Khu vực TP.HCM: 1-2 ngày làm việc.</li>
                <li>Khu vực tỉnh/thành khác: 3-5 ngày làm việc tùy vùng sâu vùng xa.</li>
            </ul>

            <h2>3. Phí vận chuyển</h2>
            <p>Phí vận chuyển sẽ được hiển thị rõ ràng tại trang thanh toán trước khi khách hàng đặt hàng. Chúng tôi thường xuyên có các chương trình Freeship cho đơn hàng từ mức giá quy định.</p>

            <h2>4. Theo dõi đơn hàng</h2>
            <p>Mã vận đơn sẽ được gửi qua SMS hoặc email sau khi đơn hàng được đóng gói. Khách hàng có thể kiểm tra hành trình đơn hàng trực tiếp trên website micsmo.com.</p>
        """,
        "seo_title": "Chính sách Vận chuyển và Giao nhận Toàn quốc - micsmo.com",
        "seo_description": "Xem thời gian giao hàng và biểu phí vận chuyển từ HKD Văn Lập."
    },
    {
        "id": "policy_inspection",
        "title": "Chính sách Kiểm hàng",
        "slug": "chinh-sach-kiem-hang",
        "excerpt": "Quy định về việc kiểm tra hàng hóa trước khi thanh toán (Đồng kiểm) để đảm bảo quyền lợi khách hàng.",
        "content": """
            <h2>1. Quy định Đồng kiểm</h2>
            <p>Khi nhận hàng, khách hàng ĐƯỢC QUYỀN yêu cầu nhân viên giao hàng cho phép kiểm tra ngoại quan gói hàng (không dùng thử, không bôi thử sản phẩm mỹ phẩm).</p>
            
            <h2>2. Nội dung kiểm tra</h2>
            <p>Khách hàng kiểm tra xem sản phẩm có đúng mẫu mã, số lượng như trong đơn hàng không. Bao bì có bị móp méo hay rò rỉ tinh chất không.</p>

            <h2>3. Xử lý khi có lỗi</h2>
            <p>Nếu sản phẩm không đúng hoặc có dấu hiệu hư hại, khách hàng có quyền từ chối nhận hàng và không thanh toán. Vui lòng liên hệ lại micsmo.com để chúng tôi xử lý gửi lại đơn hàng mới.</p>

            <h2>4. Khuyến nghị</h2>
            <p>Khách hàng nên quay video quá trình mở hộp sản phẩm để làm căn cứ giải quyết khiếu nại sau này nếu có phát sinh thiếu sót bên trong.</p>
        """,
        "seo_title": "Chính sách Kiểm hàng (Đồng kiểm) - micsmo.com",
        "seo_description": "Khách hàng được quyền kiểm tra hàng trước khi thanh toán tại micsmo.com."
    },
    {
        "id": "policy_warranty",
        "title": "Chính sách Bảo hành",
        "slug": "chinh-sach-bao-hanh",
        "excerpt": "Cam kết chất lượng và chế độ bảo hành cho các dòng sản phẩm mỹ phẩm Nhật Bản phân phối chính hãng.",
        "content": """
            <h2>1. Đối tượng bảo hành</h2>
            <p>Sản phẩm mỹ phẩm, thiết bị làm đẹp do micsmo.com phân phối.</p>
            
            <h2>2. Điều kiện bảo hành</h2>
            <ul>
                <li>Sản phẩm còn hạn sử dụng.</li>
                <li>Hư hỏng do lỗi từ nhà sản xuất (biến chất, đổi màu, lỗi vòi xịt...).</li>
                <li>Còn nguyên hóa đơn hoặc dữ liệu mua hàng trong hệ thống.</li>
            </ul>

            <h2>3. Thời gian bảo hành</h2>
            <p>Tùy theo từng loại sản phẩm, thời gian bảo hành sẽ được ghi rõ trên trang chi tiết sản phẩm hoặc phiếu bảo hành đi kèm.</p>

            <h2>4. Trường hợp từ chối bảo hành</h2>
            <p>Sản phẩm đã quá hạn sử dụng, bảo quản sai cách (để nơi nắng nóng, quá ẩm), hoặc do can thiệp ngoại lực của người dùng.</p>
        """,
        "seo_title": "Chính sách Bảo hành Sản phẩm - micsmo.com",
        "seo_description": "Xem cam kết bảo hành và chất lượng sản phẩm từ micsmo.com."
    },
    {
        "id": "policy_payment",
        "title": "Phương thức Thanh toán",
        "slug": "phuong-thuc-thanh-toan",
        "excerpt": "Hướng dẫn các phương thức thanh toán linh hoạt và an toàn tại micsmo.com.",
        "content": """
            <h2>1. Thanh toán khi nhận hàng (COD)</h2>
            <p>Khách hàng thanh toán tiền mặt trực tiếp cho nhân viên giao hàng sau khi đã kiểm tra và nhận hàng.</p>
            
            <h2>2. Chuyển khoản ngân hàng</h2>
            <p>Khách hàng có thể thanh toán trước qua tài khoản ngân hàng của micsmo.com. Nội dung chuyển khoản ghi rõ: [Mã đơn hàng] - [Số điện thoại].</p>

            <h2>3. Thanh toán qua ví điện tử / Thẻ</h2>
            <p>Hỗ trợ thanh toán qua các cổng MoMo, ZaloPay (nếu có tích hợp) hoặc thẻ ATM nội địa/Visa qua đối tác thanh toán của chúng tôi.</p>

            <h2>4. Đảm bảo an toàn</h2>
            <p>Mọi thông tin giao dịch đều được mã hóa và bảo mật theo tiêu chuẩn SSL.</p>
        """,
        "seo_title": "Hướng dẫn các Phương thức Thanh toán - micsmo.com",
        "seo_description": "Chọn phương thức thanh toán phù hợp: COD hoặc Chuyển khoản tại micsmo.com."
    },
    {
        "id": "policy_about",
        "title": "Giới thiệu",
        "slug": "gioi-thieu",
        "excerpt": "Micsmo Elite - Biểu tượng của sự kết hợp giữa tri thức làm đẹp Nhật Bản và công nghệ AI 2026.",
        "content": """
            <h2>1. Tầm nhìn 2026</h2>
            <p>Micsmo Elite ra đời với sứ mệnh mang lại vẻ đẹp bền vững cho phụ nữ Việt Nam thông qua các sản phẩm cao cấp từ Nhật Bản, kết hợp với trải nghiệm mua sắm thông minh cá nhân hóa bởi AI.</p>
            
            <h2>2. Giá trị cốt lõi</h2>
            <ul>
                <li><b>Chất lượng Elite:</b> 100% sản phẩm được tuyển chọn kỹ lưỡng.</li>
                <li><b>Công nghệ dẫn đầu:</b> Ứng dụng AI trong tư vấn và chăm sóc khách hàng.</li>
                <li><b>Tận tâm phục vụ:</b> Helen - Trợ lý AI luôn sẵn sàng hỗ trợ bạn 24/7.</li>
            </ul>
        """,
        "seo_title": "Giới thiệu về Micsmo Elite 2026",
        "seo_description": "Tìm hiểu về hành trình và tầm nhìn của Micsmo Elite trong việc kiến tạo vẻ đẹp hiện đại."
    },
    {
        "id": "policy_careers",
        "title": "Tuyển dụng",
        "slug": "tuyen-dung",
        "excerpt": "Gia nhập đội ngũ Micsmo Elite - Nơi tài năng trẻ và công nghệ hội tụ để tạo nên tương lai.",
        "content": """
            <h2>1. Môi trường làm việc</h2>
            <p>Tại Micsmo Elite, chúng tôi xây dựng một môi trường làm việc Hybrid hiện đại, tập trung vào sự sáng tạo và làm chủ công nghệ AI.</p>
            
            <h2>2. Vị trí đang tuyển dụng</h2>
            <ul>
                <li>Chuyên viên Tư vấn Làm đẹp (Am hiểu sản phẩm Nhật).</li>
                <li>Hệ thống vận hành E-commerce (Quản trị Elite AI).</li>
                <li>Cộng tác viên nội dung & Reviewer.</li>
            </ul>
            
            <h2>3. Cách thức ứng tuyển</h2>
            <p>Gửi CV của bạn về email: admin@micsmo.com với tiêu đề [HỌ TÊN] - [VỊ TRÍ ỨNG TUYỂN].</p>
        """,
        "seo_title": "Cơ hội nghề nghiệp tại Micsmo Elite",
        "seo_description": "Khám phá các vị trí tuyển dụng hấp dẫn và gia nhập đội ngũ dẫn đầu xu hướng 2026."
    }
]

async def seed_policies():
    print(f"🚀 Starting Policy Seeding for tenant: {TENANT_ID}...")
    async with async_session_maker() as session:
        # Get admin user
        # Get admin user from env or default to 'mlap'
        admin_username = os.getenv("ADMIN_USERNAME", "mlap")
        res = await session.execute(select(User.id).where(User.username == admin_username))
        author_id = res.scalar_one_or_none()
        
        if not author_id:
            print("⚠️ Admin user not found. Using None as author_id.")
        
        added_count = 0
        skipped_count = 0
        
        for p_data in POLICIES:
            # Check if exists by ID (R00: Stable Identity)
            stmt = select(Article).where(Article.id == p_data["id"])
            existing = (await session.execute(stmt)).scalar_one_or_none()
            
            if existing:
                print(f"🔄 Updating existing article: {p_data['title']} (ID: {p_data['id']})")
                existing.title = p_data["title"]
                existing.slug = p_data["slug"] # Update slug if changed
                existing.excerpt = p_data["excerpt"]
                existing.content = p_data["content"]
                existing.author_id = author_id
                existing.seo_title = p_data.get("seo_title")
                existing.seo_description = p_data.get("seo_description")
                skipped_count += 1
                continue
            
            new_article = Article(
                id=p_data["id"],
                title=p_data["title"],
                slug=p_data["slug"],
                excerpt=p_data["excerpt"],
                content=p_data["content"],
                status="PUBLISHED",
                category="Chính sách",
                author_id=author_id,
                tenant_id=TENANT_ID,
                seo_title=p_data.get("seo_title"),
                seo_description=p_data.get("seo_description"),
                views=0,
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_article)
            added_count += 1
            print(f"✅ Added policy: {p_data['title']}")
            
        await session.commit()
        print(f"✨ Finished! Added: {added_count}, Skipped: {skipped_count}")

if __name__ == "__main__":
    asyncio.run(seed_policies())
