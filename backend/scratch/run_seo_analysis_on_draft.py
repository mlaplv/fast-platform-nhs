import sys
import os
import asyncio

# Setup sys.path to find backend module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load .env variables
def load_env():
    env_path = "/app/.env" if os.path.exists("/app/.env") else os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env'))
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        os.environ[key] = val

load_env()

from backend.services.xohi.creative_studio.handlers.analyst import AdHocContent
from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer

DRAFT_HTML = """<p>Đôi bàn tay không chỉ là công cụ lao động mà còn là "tấm gương" phản chiếu trung thực nhất về tuổi tác của bạn, thậm chí còn rõ nét hơn cả khuôn mặt. Trong khi chúng ta đầu tư hàng giờ và hàng triệu đồng vào quy trình chăm sóc da mặt, đôi tay – bộ phận phải hoạt động liên tục và chịu đựng hàng trăm lượt tiếp xúc với hóa chất, ánh nắng mỗi ngày – lại thường xuyên bị bỏ quên. Thực tế, nhiều chuyên gia da liễu chỉ ra rằng da tay có thể lão hóa nhanh hơn da mặt tới 5-10 năm nếu không được chăm sóc đúng cách, đặc biệt do tiếp xúc liên tục với các tác nhân gây hại mà không có lớp bảo vệ tương xứng. Sự xuất hiện của các <strong>dấu hiệu lão hóa da tay sớm</strong> như da khô sạm, mất độ đàn hồi, nếp nhăn sâu, hay đồi mồi không chỉ làm giảm thẩm mỹ mà còn là lời cảnh báo về tổn thương tế bào nghiêm trọng. Đã đến lúc chúng ta cần hành động để tìm hiểu chi tiết các <strong>dấu hiệu lão hóa da tay sớm và cách khắc phục hiệu quả</strong>, giúp đôi tay không chỉ mềm mại, khỏe mạnh mà còn giữ mãi vẻ thanh xuân, xứng đáng với sự quan tâm mà chúng ta dành cho các bộ phận khác.</p>
<p>Dấu Hiệu Lão Hóa Sớm Của Da Tay: Khi Nào Cần Hành Động?</p>
<p>Nhận biết sớm các dấu hiệu lão hóa là bước đầu tiên để chúng ta có thể can thiệp kịp thời và hiệu quả. Đừng bỏ qua những tín hiệu mà đôi tay đang cố gắng gửi đến bạn nhé!</p>
<p>Da tay khô ráp, mất độ ẩm là gì?</p>
<p><strong>Trả lời:</strong> Da tay khô ráp, sần sùi là dấu hiệu phổ biến nhất của sự thiếu hụt độ ẩm, khiến bề mặt da trở nên thô cứng, thiếu mịn màng và dễ bị bong tróc. Tình trạng này không chỉ gây khó chịu mà còn làm giảm đi vẻ tươi trẻ của đôi tay, khiến chúng trông kém sức sống và già hơn tuổi thật.</p>
<ul>
  <li><strong>Lưu ý:</strong> Điều này thường xảy ra do tiếp xúc quá nhiều với nước, xà phòng, chất tẩy rửa hoặc môi trường khô lạnh, làm mất đi lớp dầu tự nhiên bảo vệ da.</li>
</ul>
<p>Nếp nhăn và vết chân chim xuất hiện trên mu bàn tay?</p>
<p><strong>Trả lời:</strong> Sự xuất hiện của các nếp nhăn li ti và vết chân chim trên mu bàn tay là một dấu hiệu rõ ràng của việc da đang mất dần collagen và elastin – hai protein quan trọng giúp da săn chắc và đàn hồi. Khi collagen và elastin suy giảm, da sẽ trở nên mỏng hơn, chùng nhão và dễ hình thành các đường rãnh, nếp gấp, đặc biệt khi bạn cử động hoặc nắm tay lại.</p>
<ul>
  <li><strong>Lưu ý:</strong> Da tay vốn mỏng và ít mô mỡ hơn các vùng da khác, nên nếp nhăn có thể xuất hiện sớm và rõ rệt hơn.</li>
</ul>
<p>Da tay mỏng, lộ gân xanh và mạch máu rõ hơn?</p>
<p><strong>Trả lời:</strong> Khi da tay lão hóa, lớp mỡ dưới da bị tiêu biến và da trở nên mỏng hơn đáng kể, làm cho các gân xanh, mạch máu, và xương bàn tay trở nên nổi rõ ràng hơn. Điều này không chỉ ảnh hưởng đến tính thẩm mỹ mà còn khiến da tay dễ bị tổn thương, bầm tím hơn khi có va chạm nhẹ.</p>
<ul>
  <li><strong>Lưu ý:</strong> Đây là một đặc điểm của lão hóa tự nhiên, nhưng có thể tăng tốc độ bởi các yếu tố môi trường và thiếu chăm sóc.</li>
</ul>
<p>Xuất hiện đốm nâu, đồi mồi trên da tay?</p>
<p><strong>Trả lời:</strong> Các đốm nâu, hay còn gọi là đồi mồi, là những mảng tăng sắc tố da có màu nâu nhạt đến nâu đậm, thường xuất hiện ở những vùng da tiếp xúc nhiều với ánh nắng mặt trời, trong đó có mu bàn tay. Chúng là kết quả của việc tích tụ melanin quá mức do tác động của tia UV và quá trình lão hóa, khiến đôi tay trông mất thẩm mỹ và già cỗi.</p>
<ul>
  <li><strong>Lưu ý:</strong> Đồi mồi khác với tàn nhang ở chỗ chúng thường lớn hơn, không đều màu và có xu hướng tăng lên theo tuổi tác.</li>
</ul>
<p>Tại Sao Da Tay Lại Dễ Bị Lão Hóa Sớm Hơn Các Vùng Da Khác?</p>
<p>Hiểu rõ nguyên nhân giúp chúng ta có thể chủ động phòng ngừa và chăm sóc da tay một cách hiệu quả hơn.</p>
<p>Tiếp xúc thường xuyên với môi trường khắc nghiệt?</p>
<p><strong>Trả lời:</strong> Đôi tay chúng ta phải đối mặt hàng ngày với nhiều tác nhân gây hại từ môi trường như nước, xà phòng, hóa chất tẩy rửa trong công việc nhà, ánh nắng mặt trời, gió và sự thay đổi nhiệt độ. Những yếu tố này không ngừng bào mòn lớp màng bảo vệ tự nhiên của da, khiến da mất đi độ ẩm và các dưỡng chất thiết yếu, đẩy nhanh quá trình lão hóa.</p>
<ul>
  <li><strong>Lưu ý:</strong> Ngay cả việc rửa tay thường xuyên với xà phòng kháng khuẩn cũng có thể làm khô da nếu không được dưỡng ẩm đầy đủ.</li>
</ul>
<p>Thiếu lớp bảo vệ tự nhiên và ít tuyến bã nhờn?</p>
<p><strong>Trả lời:</strong> So với da mặt hoặc các vùng da khác trên cơ thể, da tay có cấu trúc mỏng hơn và ít tuyến bã nhờn hơn đáng kể. Lớp lipid bảo vệ tự nhiên mỏng manh khiến da tay dễ bị mất nước, khô ráp và tổn thương bởi các tác nhân bên ngoài. Sự thiếu hụt dầu tự nhiên cũng làm cho da tay ít được nuôi dưỡng và tái tạo, dẫn đến lão hóa nhanh chóng.</p>
<ul>
  <li><strong>Lưu ý:</strong> Đây là lý do tại sao da tay thường cảm thấy căng rít và khô hơn sau khi rửa, trong khi da mặt có thể vẫn giữ được độ ẩm nhất định.</li>
</ul>
<p>Bị bỏ quên trong quy trình chăm sóc da hàng ngày?</p>
<p><strong>Trả lời:</strong> Mặc dù là bộ phận hoạt động nhiều nhất, đôi tay lại thường bị lãng quên trong chu trình chăm sóc da hàng ngày. Chúng ta có thể kỹ lưỡng với kem chống nắng cho mặt, serum chống lão hóa cho cổ, nhưng lại bỏ qua việc thoa kem dưỡng hay kem chống nắng cho đôi tay. Sự thiếu hụt chăm sóc này khiến da tay trở nên yếu ớt, dễ bị tổn thương và lão hóa nhanh hơn dự kiến.</p>
<ul>
  <li><strong>Lưu ý:</strong> Hãy coi da tay như một phần mở rộng của khuôn mặt, cần được chăm sóc tương tự.</li>
</ul>
<p>Giải Pháp Toàn Diện Để Chống Lão Hóa Và Phục Hồi Da Tay</p>
<p>Đã đến lúc chúng ta hành động để bảo vệ và trẻ hóa đôi bàn tay của mình. Hãy bắt đầu từ những thói quen nhỏ nhất mỗi ngày!</p>
<p>Làm sạch và bảo vệ da tay đúng cách?</p>
<p><strong>Trả lời:</strong> Hãy chọn loại xà phòng rửa tay có công thức dịu nhẹ, không chứa quá nhiều chất tẩy rửa mạnh để tránh làm mất đi độ ẩm tự nhiên của da. Khi thực hiện các công việc nhà như rửa bát, giặt giũ hoặc tiếp xúc với hóa chất, việc đeo găng tay bảo hộ là vô cùng cần thiết để tạo một lớp màng chắn vật lý, giảm thiểu tối đa tác động tiêu cực lên da tay.</p>
<ul>
  <li><strong>Lưu ý:</strong> Tránh rửa tay bằng nước quá nóng hoặc quá lạnh vì cả hai đều có thể gây khô da.</li>
</ul>
<p>Cấp ẩm sâu và nuôi dưỡng da tay thường xuyên?</p>
<p><strong>Trả lời:</strong> Việc cấp ẩm là yếu tố then chốt để duy trì sự mềm mại, mịn màng và ngăn ngừa lão hóa cho đôi tay. Sử dụng kem dưỡng ẩm chuyên sâu không chỉ giúp bổ sung độ ẩm tức thì mà còn tạo lớp màng bảo vệ, khóa ẩm và cung cấp dưỡng chất thiết yếu cho da. Đây chính là lúc bạn cần một sản phẩm chăm sóc đặc biệt như <strong>Miccosmo Hurry Harry Premium Hand Balm 40g là giải pháp chuyên biệt cho đôi tay lão hóa sớm. Công thức cao cấp của sản phẩm này chứa Retinol, hoạt chất chống lão hóa mạnh mẽ, giúp thúc đẩy tái tạo tế bào, Niacinamide, dưỡng chất thiết yếu cho da tay, tăng cường hàng rào bảo vệ da, cùng Peptide, chuỗi axit amin tăng cường độ đàn hồi, giúp cải thiện độ đàn hồi rõ rệt. Kem không chỉ cấp ẩm sâu, phục hồi làn da khô ráp do tác động môi trường và chất tẩy rửa, mà còn tập trung ngăn ngừa lão hóa. Các hoạt chất dưỡng chất ưu việt này nuôi dưỡng, làm mềm mịn và bảo vệ da tay khỏi tác nhân gây hại, mang lại đôi tay mềm mại, căng mượt, và khỏe mạnh. Để đạt hiệu quả tối ưu, hãy thoa kem ngay sau mỗi lần rửa tay và đặc biệt là trước khi đi ngủ, giúp da tái tạo và hấp thụ dưỡng chất tốt nhất..</strong></p>
<ul>
  <li><strong>Lưu ý: Thoa kem dưỡng da tay đều đặn mỗi ngày, ít nhất 2-3 lần hoặc sau mỗi lần rửa tay, là khóa để duy trì làn da tay mềm mịn và ngăn ngừa lão hóa hiệu quả.</strong></li>
</ul>
<p><strong>Bảo vệ da tay khỏi tác hại của ánh nắng mặt trời?</strong></p>
<p><strong>Trả lời: Ánh nắng mặt trời là một trong những nguyên nhân hàng đầu gây ra các đốm nâu, nếp nhăn và sự mất đàn hồi của da tay. Hãy luôn thoa kem chống nắng có chỉ số SPF từ 30 trở lên cho mu bàn tay mỗi khi ra ngoài, ngay cả trong những ngày trời râm mát. Ngoài ra, việc đeo găng tay chống nắng hoặc găng tay vải khi lái xe hay làm việc ngoài trời cũng là một biện pháp bảo vệ hiệu quả.</strong></p>
<ul>
  <li><strong>Lưu ý: Tia UV có thể xuyên qua kính cửa sổ, vì vậy hãy bảo vệ tay ngay cả khi bạn ở trong xe hơi hoặc gần cửa sổ.</strong></li>
</ul>
<p><strong>Chế độ dinh dưỡng và lối sống lành mạnh?</strong></p>
<p><strong>Trả lời: Sức khỏe của làn da, bao gồm cả da tay, phản ánh tình trạng sức khỏe tổng thể từ bên trong. Một chế độ ăn uống giàu chất chống oxy hóa (từ rau xanh, trái cây mọng, các loại hạt), vitamin C và E sẽ giúp bảo vệ tế bào da khỏi tổn thương của các gốc tự do. Đồng thời, uống đủ nước mỗi ngày là yếu tố cực kỳ quan trọng để duy trì độ ẩm tự nhiên và sự đàn hồi của da từ sâu bên trong.</strong></p>
<ul>
  <li><strong>Lưu ý: Hạn chế hút thuốc lá và uống rượu bia, vì chúng là những yếu tố đẩy nhanh quá trình lão hóa da.</strong></li>
</ul>
<p><strong>Chăm sóc đôi bàn tay là một hành trình dài và cần sự kiên trì. Với những bước nhỏ được thực hiện đều đặn mỗi ngày, bạn hoàn toàn có thể ngăn ngừa và cải thiện tình trạng lão hóa sớm, giữ cho đôi tay luôn là niềm tự hào của mình. Bạn đã sẵn sàng lắng nghe và yêu thương đôi tay mình nhiều hơn mỗi ngày chưa?</strong></p>"""

async def run():
    print("Initializing SeoAnalyzer...")
    analyzer = SeoAnalyzer()
    
    # AdHocContent shim
    campaign = AdHocContent(
        content=DRAFT_HTML,
        topic="Dấu hiệu lão hóa da tay sớm và cách khắc phục hiệu quả",
        category="CREATIVE_CONTENT"
    )
    
    print("Running analyze...")
    result = await analyzer.analyze(campaign, force=True)
    
    print("\n================== RESULT ==================")
    print(f"Total Score: {result.total_score}")
    print(f"Grade: {result.grade}")
    print("\n--- Signals ---")
    for sig in result.signals:
        print(f"[{sig.status.upper()}] {sig.label}: {sig.score}")
    
    print("\n--- Quick Wins ---")
    for qw in result.quick_wins:
        print(f"- {qw}")
        
    print("\n--- SEO Annotations ---")
    for ann in result.seo_annotations:
        print(f"[{ann.severity.upper()}] {ann.type} | Msg: {ann.message} | Text: {ann.text[:80]}...")
        
    print("\n--- Summary ---")
    print(result.summary)

if __name__ == "__main__":
    asyncio.run(run())
