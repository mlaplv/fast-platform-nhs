import sys
import os

# Setup sys.path to find backend module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer

def test_clean_ai_html():
    analyzer = SeoAnalyzer()
    
    html_input = """
    <p>Sản phẩm này chứa một phức hợp các dưỡng chất mạnh mẽ, được các nhà khoa học da liễu công nhận về hiệu quả:</p>
    <ul>
      <li><strong>Retinol (Dẫn xuất Vitamin A):</strong> Là thành phần vàng trong chống lão hóa, được chứng minh qua hàng trăm nghiên cứu lâm sàng về khả năng thúc đẩy quá trình tái tạo tế bào, kích thích sản sinh collagen và elastin mới. Theo nghiên cứu trên tạp chí "Journal of Cosmetic Dermatology", Retinol có thể giúp giảm nếp nhăn đến <strong>30-40%</strong> sau 12 tuần sử dụng đều đặn.</li>
      <li><strong>Vitamin C (dạng ổn định):</strong> Với khả năng chống oxy hóa mạnh mẽ, Vitamin C là "vệ sĩ" bảo vệ da khỏi gốc tự do gây hại (có thể trung hòa đến <strong>90%</strong> gốc tự do do tia UV gây ra) và là yếu tố then chốt trong quá trình tổng hợp collagen.</li>
      <li><strong>Hyaluronic Acid và Collagen thủy phân:</strong> Không thể thiếu trong việc duy trì độ ẩm và độ đàn hồi. Hyaluronic Acid có khả năng giữ nước gấp <strong>1000 lần</strong> trọng lượng phân tử của nó, cung cấp độ ẩm sâu.</li>
    </ul>
    <h2><strong>Cơ chế mờ nếp nhăn và làm sáng hiệu quả dựa trên khoa học</strong></h2>
    <p>Chúng tôi cam kết mang lại hiệu quả <strong>vượt trội</strong> cho làn da của bạn.</p>
    <p><strong>Lưu ý:</strong> Nên sử dụng vào ban đêm.</p>
    <p>Đây là <code>đoạn code mẫu</code> và <pre>khối pre mẫu</pre>.</p>
    """
    
    clean_html = analyzer.clean_ai_html(html_input)
    
    print("CLEANED HTML OUTPUT:")
    print(clean_html)
    
    # Assertions
    assert "<strong>Retinol (Dẫn xuất Vitamin A):</strong>" in clean_html, "Should keep list item header bolding"
    assert "<strong>Vitamin C (dạng ổn định):</strong>" in clean_html, "Should keep list item header bolding"
    assert "<strong>Hyaluronic Acid và Collagen thủy phân:</strong>" in clean_html, "Should keep list item header bolding"
    assert "<strong>Lưu ý:</strong>" in clean_html, "Should keep paragraph header bolding"
    assert "<strong>Cơ chế mờ nếp nhăn và làm sáng hiệu quả dựa trên khoa học</strong>" in clean_html or "<h2><strong>" in clean_html or "<strong>" not in clean_html, "Heading bolding checked"
    
    assert "<strong>30-40%</strong>" not in clean_html, "Should strip statistical bolding"
    assert "30-40%" in clean_html, "Should preserve text of statistical bolding"
    
    assert "<strong>90%</strong>" not in clean_html, "Should strip statistical bolding"
    assert "90%" in clean_html, "Should preserve text"
    
    assert "<strong>1000 lần</strong>" not in clean_html, "Should strip statistical bolding"
    assert "1000 lần" in clean_html, "Should preserve text"
    
    assert "<strong>vượt trội</strong>" not in clean_html, "Should strip indiscriminate bolding in the middle of sentences"
    assert "vượt trội" in clean_html, "Should preserve text"
    
    assert "<code>" not in clean_html, "Should strip code tags"
    assert "đoạn code mẫu" in clean_html, "Should keep text inside code tags"
    
    assert "<pre>" not in clean_html, "Should strip pre tags"
    assert "khối pre mẫu" in clean_html, "Should keep text inside pre tags"
    
    print("\n✅ All assertions passed successfully!")

if __name__ == "__main__":
    test_clean_ai_html()
