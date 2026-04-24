import asyncio
from lxml import html
import re
from rapidfuzz import fuzz

async def main():
    html_content = """<h3><strong><em>Thành phần nổi bật:</em></strong></h3><ul><li><p>Vitamin C dẫn xuất &amp; Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p></li><li><p>Chiết xuất lá hoa anh đào: Làm dịu, giảm sạm, giúp da sáng hồng.</p></li><li><p>Chiết xuất đậu nành: Tăng đàn hồi, dưỡng mềm vùng da nhạy cảm.</p></li><li><p>Chiết xuất sâm tố nữ: Nuôi dưỡng, phục hồi da sau cạo hoặc waxing.</p></li></ul><h3><strong>Công dụng của Miccosmo Beppin Body Virgin White Serum</strong></h3><ul><li><p>Serum dưỡng sáng hồng và làm đều màu da vùng nhạy cảm như bikini, nách, nhũ hoa, đùi trong. Sản phẩm hỗ trợ cải thiện 40% tình trạng da không đều màu do ma sát, nội tiết tố hoặc phương pháp loại bỏ lông cơ học, mang lại làn da sáng mịn chuyên nghiệp.</p></li><li><p>Dưỡng mềm và tăng độ đàn hồi cho vùng da nhạy cảm.</p></li><li><p>Làm dịu, phục hồi và duy trì làn da sáng khỏe tự nhiên.</p></li></ul><h3><strong>Đối tượng sử dụng của Miccosmo Beppin Body Virgin White Serum</strong></h3><ul><li><p>Người có vùng da nhạy cảm bị sạm, thâm do ma sát, cạo hoặc waxing.</p></li><li><p>Phụ nữ sau sinh có vùng da thâm sạm, tối màu do thay đổi nội tiết tố.</p></li><li><p>Người mong muốn dưỡng sáng hồng an toàn cho vùng bikini, nách, nhũ hoa và đùi trong, giúp da đều màu và mềm mịn tự nhiên.</p></li></ul><h3><strong>Cách sử dụng của Miccosmo Beppin Body Virgin White Serum</strong></h3><ul><li><p>Làm sạch và lau khô vùng da cần chăm sóc.</p></li><li><p>Lấy một lượng serum vừa đủ, thoa nhẹ và massage đều để dưỡng chất thấm nhanh.</p></li><li><p>Sử dụng 2 lần mỗi ngày, sáng và tối, đặc biệt sau khi tắm để đạt hiệu quả tối ưu.</p></li></ul><h3><strong>Lưu ý khi sử dụng Miccosmo Beppin Body Virgin White Serum</strong></h3><ul><li><p>Chỉ dùng ngoài da, tránh tiếp xúc với vùng da bị tổn thương hoặc trầy xước.</p></li><li><p>Bảo quản nơi khô ráo, tránh ánh nắng trực tiếp và nhiệt độ cao.</p></li><li><p>Ngưng sử dụng nếu có dấu hiệu kích ứng và tham khảo ý kiến chuyên gia da liễu.</p></li></ul><h3><strong>Bảo quản</strong></h3><ul><li><p>Bảo quản nơi khô ráo thoáng mát, tránh ánh nắng trực tiếp và nhiệt độ cao.</p></li><li><p>Tránh xa tầm tay trẻ em.</p></li></ul><p>.</p><h3><strong><em>Thành phần nổi bật:</em></strong></h3><ul><li><p>Vitamin C dẫn xuất &amp; Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p></li><li><p>Chiết xuất lá hoa anh đào: Làm dịu, giảm sạm, giúp da sáng hồng.</p></li><li><p>Chiết xuất đậu nành: Tăng đàn hồi, dưỡng mềm vùng da nhạy cảm.</p></li><li><p>Chiết xuất sâm tố nữ: Nuôi dưỡng, phục hồi da sau cạo hoặc waxing.</p></li></ul><h3><strong>Công dụng của Miccosmo Beppin Body Virgin White Serum</strong></h3><ul><li><p>Serum dưỡng sáng hồng và làm đều màu da vùng nhạy cảm như bikini, nách, nhũ hoa, đùi trong, Sản phẩm hỗ trợ cải thiện tình trạng da không đều màu do tác động ma sát, thay đổi nội tiết tố hoặc các phương pháp loại bỏ lông cơ học. Công thức đặc biệt giúp làm mờ các vùng thâm sạm, nuôi dưỡng làn da trở nên sáng mịn và đều màu hơn theo thời gian, được thiết kế chuyên biệt để đáp ứng nhu cầu chăm sóc da nhạy cảm của phụ nữ hiện đại..</p></li><li><p>Dưỡng mềm và tăng độ đàn hồi cho vùng da nhạy cảm.</p></li><li><p>Làm dịu, phục hồi và duy trì làn da sáng khỏe tự nhiên.</p></li></ul><h3><strong>Đối tượng sử dụng của Miccosmo Beppin Body Virgin White Serum</strong></h3><ul><li><p>Người có vùng da nhạy cảm bị sạm, thâm do ma sát, cạo hoặc waxing.</p></li><li><p>Phụ nữ sau sinh có vùng da thâm sạm, tối màu do thay đổi nội tiết tố.</p></li><li><p>Người mong muốn dưỡng sáng hồng an toàn cho vùng bikini, nách, nhũ hoa và đùi trong, giúp da đều màu và mềm mịn tự nhiên.</p></li></ul><h3><strong>Cách sử dụng của Miccosmo Beppin Body Virgin White Serum</strong></h3><ul><li><p>Làm sạch và lau khô vùng da cần chăm sóc.</p></li><li><p>Lấy một lượng serum vừa đủ, thoa nhẹ và massage đều để dưỡng chất thấm nhanh.</p></li><li><p>Sử dụng 2 lần mỗi ngày, sáng và tối, đặc biệt sau khi tắm để đạt hiệu quả tối ưu.</p></li></ul><h3><strong>Lưu ý khi sử dụng Miccosmo Beppin Body Virgin White Serum</strong></h3><ul><li><p>Chỉ dùng ngoài da, tránh tiếp xúc với vùng da bị tổn thương hoặc trầy xước.</p></li><li><p>Bảo quản nơi khô ráo, tránh ánh nắng trực tiếp và nhiệt độ cao.</p></li><li><p>Ngưng sử dụng nếu có dấu hiệu kích ứng và tham khảo ý kiến chuyên gia da liễu.</p></li></ul><h3><strong>Bảo quản</strong></h3><ul><li><p>Bảo quản nơi khô ráo thoáng mát, tránh ánh nắng trực tiếp và nhiệt độ cao.</p></li><li><p>Tránh xa tầm tay trẻ em.</p></li></ul><p></p>"""
    
    fragment = html.fragment_fromstring(f"<div>{html_content}</div>", create_parent=False)

    dedup_tags = ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li')
    all_blocks = [el for el in list(fragment.iter()) if el.tag in dedup_tags]
    
    blocks = []
    for el in all_blocks:
        has_block_child = any(child.tag in dedup_tags for child in el.iterdescendants())
        if not has_block_child:
            blocks.append(el)

    signatures = []
    for el in blocks:
        text = "".join(el.itertext()).strip().lower()
        text = re.sub(r'\s+', ' ', text)
        signatures.append((el.tag, text))

    to_drop = set()
    
    # 1. Single-element dedup (for long paragraphs > 30 chars) with Fuzzy Matching
    seen_long = []
    for i, (tag, text) in enumerate(signatures):
        if len(text) > 30:
            is_dup = False
            for seen in seen_long:
                if text == seen:
                    is_dup = True
                    break
                # Partial ratio catches when one text is a modified substring of another
                if fuzz.partial_ratio(text, seen) >= 85:
                    is_dup = True
                    break
                    
            if is_dup:
                to_drop.add(blocks[i])
            else:
                seen_long.append(text)

    # 2. Sequence-level dedup (Window size 2) for structure
    seen_seqs = set()
    for i in range(len(signatures) - 1):
        tag1, t1 = signatures[i]
        tag2, t2 = signatures[i+1]
        if not t1 or not t2: continue
        seq = ((tag1, t1), (tag2, t2))
        if seq in seen_seqs:
            to_drop.add(blocks[i])
            to_drop.add(blocks[i+1])
        else:
            seen_seqs.add(seq)

    for el in to_drop:
        if el.getparent() is not None:
            el.drop_tree()
            
    # CLEANUP PASS
    for element in reversed(list(fragment.iter())):
        if element == fragment: continue
        if element.tag in ('ul', 'ol', 'li', 'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            has_text = bool((element.text or "").replace('\u00A0', '').strip())
            if not has_text and len(element) == 0:
                element.drop_tree()
            
    result = html.tostring(fragment, encoding='unicode', method='html')
    if result.startswith('<div>'): result = result[5:]
    if result.endswith('</div>'): result = result[:-6]
    
    print(result)

asyncio.run(main())
