import asyncio
from backend.utils.noise_cleaner import noise_cleaner

async def main():
    html = """
    <div>
        <h3>Thành phần nổi bật:</h3>
        <p>Vitamin C dẫn xuất & Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p>
        <p>Chiết xuất lá hoa anh đào: Làm dịu, giảm sạm, giúp da sáng hồng.</p>
        <p>Chiết xuất đậu nành: Tăng đàn hồi, dưỡng mềm vùng da nhạy cảm.</p>
        <p>Chiết xuất sâm tố nữ: Nuôi dưỡng, phục hồi da sau cạo hoặc waxing.</p>

        <h3>Công dụng của Miccosmo Beppin Body Virgin White Serum</h3>
        <p>Serum dưỡng sáng hồng và làm đều màu da vùng nhạy cảm như bikini, nách, nhũ hoa, đùi trong. Sản phẩm hỗ trợ cải thiện 40% tình trạng da không đều màu do ma sát, nội tiết tố hoặc phương pháp loại bỏ lông cơ học, mang lại làn da sáng mịn chuyên nghiệp.</p>
        <p>Dưỡng mềm và tăng độ đàn hồi cho vùng da nhạy cảm.</p>
        <p>Làm dịu, phục hồi và duy trì làn da sáng khỏe tự nhiên.</p>

        <h3>Đối tượng sử dụng của Miccosmo Beppin Body Virgin White Serum</h3>
        <p>Người có vùng da nhạy cảm bị sạm, thâm do ma sát, cạo hoặc waxing.</p>
        <p>Phụ nữ sau sinh có vùng da thâm sạm, tối màu do thay đổi nội tiết tố.</p>
        <p>Người mong muốn dưỡng sáng hồng an toàn cho vùng bikini, nách, nhũ hoa và đùi trong, giúp da đều màu và mềm mịn tự nhiên.</p>

        <h3>Cách sử dụng của Miccosmo Beppin Body Virgin White Serum</h3>
        <p>Làm sạch và lau khô vùng da cần chăm sóc.</p>
        <p>Lấy một lượng serum vừa đủ, thoa nhẹ và massage đều để dưỡng chất thấm nhanh.</p>
        <p>Sử dụng 2 lần mỗi ngày, sáng và tối, đặc biệt sau khi tắm để đạt hiệu quả tối ưu.</p>

        <h3>Lưu ý khi sử dụng Miccosmo Beppin Body Virgin White Serum</h3>
        <p>Chỉ dùng ngoài da, tránh tiếp xúc với vùng da bị tổn thương hoặc trầy xước.</p>
        <p>Bảo quản nơi khô ráo, tránh ánh nắng trực tiếp và nhiệt độ cao.</p>
        <p>Ngưng sử dụng nếu có dấu hiệu kích ứng và tham khảo ý kiến chuyên gia da liễu.</p>

        <h3>Bảo quản</h3>
        <p>Bảo quản nơi khô ráo thoáng mát, tránh ánh nắng trực tiếp và nhiệt độ cao.</p>
        <p>Tránh xa tầm tay trẻ em.</p>

        <p>.</p>

        <h3>Thành phần nổi bật:</h3>
        <p>Vitamin C dẫn xuất & Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p>
        <p>Chiết xuất lá hoa anh đào: Làm dịu, giảm sạm, giúp da sáng hồng.</p>
        <p>Chiết xuất đậu nành: Tăng đàn hồi, dưỡng mềm vùng da nhạy cảm.</p>
        <p>Chiết xuất sâm tố nữ: Nuôi dưỡng, phục hồi da sau cạo hoặc waxing.</p>

        <h3>Công dụng của Miccosmo Beppin Body Virgin White Serum</h3>
        <p>Serum dưỡng sáng hồng và làm đều màu da vùng nhạy cảm như bikini, nách, nhũ hoa, đùi trong. Sản phẩm hỗ trợ cải thiện tình trạng da không đều màu do tác động ma sát, thay đổi nội tiết tố hoặc các phương pháp loại bỏ lông cơ học. Công thức đặc biệt giúp làm mờ các vùng thâm sạm, nuôi dưỡng làn da trở nên sáng mịn và đều màu hơn theo thời gian, được thiết kế chuyên biệt để đáp ứng nhu cầu chăm sóc da nhạy cảm của phụ nữ hiện đại.</p>
        <p>Dưỡng mềm và tăng độ đàn hồi cho vùng da nhạy cảm.</p>
        <p>Làm dịu, phục hồi và duy trì làn da sáng khỏe tự nhiên.</p>

        <h3>Đối tượng sử dụng của Miccosmo Beppin Body Virgin White Serum</h3>
        <p>Người có vùng da nhạy cảm bị sạm, thâm do ma sát, cạo hoặc waxing.</p>
        <p>Phụ nữ sau sinh có vùng da thâm sạm, tối màu do thay đổi nội tiết tố.</p>
        <p>Người mong muốn dưỡng sáng hồng an toàn cho vùng bikini, nách, nhũ hoa và đùi trong, giúp da đều màu và mềm mịn tự nhiên.</p>

        <h3>Cách sử dụng của Miccosmo Beppin Body Virgin White Serum</h3>
        <p>Làm sạch và lau khô vùng da cần chăm sóc.</p>
        <p>Lấy một lượng serum vừa đủ, thoa nhẹ và massage đều để dưỡng chất thấm nhanh.</p>
        <p>Sử dụng 2 lần mỗi ngày, sáng và tối, đặc biệt sau khi tắm để đạt hiệu quả tối ưu.</p>

        <h3>Lưu ý khi sử dụng Miccosmo Beppin Body Virgin White Serum</h3>
        <p>Chỉ dùng ngoài da, tránh tiếp xúc với vùng da bị tổn thương hoặc trầy xước.</p>
        <p>Bảo quản nơi khô ráo, tránh ánh nắng trực tiếp và nhiệt độ cao.</p>
        <p>Ngưng sử dụng nếu có dấu hiệu kích ứng và tham khảo ý kiến chuyên gia da liễu.</p>

        <h3>Bảo quản</h3>
        <p>Bảo quản nơi khô ráo thoáng mát, tránh ánh nắng trực tiếp và nhiệt độ cao.</p>
        <p>Tránh xa tầm tay trẻ em.</p>
    </div>
    """
    options = {
        "stripFont": True,
        "stripAlign": True,
        "stripRedundantWrappers": True,
        "stripEmpty": True,
        "deduplicateContent": True
    }
    
    # Try aggressive mode
    cleaned = await noise_cleaner.clean(html, mode="aggressive", options=options)
    print(cleaned)

asyncio.run(main())
