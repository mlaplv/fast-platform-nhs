from backend.services.xohi.creative_studio.operatives.neural_rewriter import NeuralRewriter
from backend.services.xohi.creative_studio.operatives.plagiarism_refiner import PlagiarismRefiner

def test_markdown_table_conversion():
    input_html = """
<p>Dưới đây là bảng so sánh:</p>

| Tiêu chí so sánh | Phương pháp lột tẩy thông thường | Cơ chế phục hồi Beppin Body |
| :--- | :--- | :--- |
| Cách thức tác động | Bào mòn bề mặt, dễ gây kích ứng, khô rát | Làm dịu phản ứng viêm, tái tạo màng lipid |
| Độ ổn định của Vitamin C | Dạng nước dễ bị oxy hóa, gây đỏ da | Dạng ester dầu bền vững, thẩm thấu sâu |
| Cảm giác trên da | Bết dính, dễ gây bít tắc lỗ chân lông | Kem lỏng (light cream) mỏng nhẹ, thoáng mịn |

<p>Hết bảng.</p>
"""

    rewriter = NeuralRewriter()
    output_html_rewriter = rewriter.clean_ai_html(input_html)

    # Assert that markdown table markers are gone
    assert "| Tiêu chí so sánh |" not in output_html_rewriter
    assert "| :--- |" not in output_html_rewriter
    
    # Assert that HTML table elements are present
    assert '<table class="table-auto w-full">' in output_html_rewriter
    assert '<thead>' in output_html_rewriter
    assert '<th>Tiêu chí so sánh</th>' in output_html_rewriter
    assert '<td>Cách thức tác động</td>' in output_html_rewriter
    assert '<td>Bào mòn bề mặt, dễ gây kích ứng, khô rát</td>' in output_html_rewriter
    assert '<td>Làm dịu phản ứng viêm, tái tạo màng lipid</td>' in output_html_rewriter

    refiner = PlagiarismRefiner()
    output_html_refiner = refiner.clean_ai_html(input_html)
    assert '<table class="table-auto w-full">' in output_html_refiner
    assert '<th>Tiêu chí so sánh</th>' in output_html_refiner
    print("test_markdown_table_conversion: PASSED")

def test_no_markdown_table():
    input_html = "<p>Không có bảng nào ở đây.</p>"
    rewriter = NeuralRewriter()
    output = rewriter.clean_ai_html(input_html)
    assert output == "<p>Không có bảng nào ở đây.</p>"
    print("test_no_markdown_table: PASSED")

if __name__ == '__main__':
    test_markdown_table_conversion()
    test_no_markdown_table()
    print("All tests passed successfully!")
