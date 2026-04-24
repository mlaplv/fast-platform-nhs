from lxml import html
import re

html_content = """
<div>
  <h3>Thành phần nổi bật:</h3>
  <p>Vitamin C dẫn xuất & Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p>
  <p>Chiết xuất lá hoa anh đào: Làm dịu, giảm sạm, giúp da sáng hồng.</p>
  <h3>Bảo quản</h3>
  <p>Bảo quản nơi khô ráo thoáng mát, tránh ánh nắng trực tiếp và nhiệt độ cao.</p>
  <p>Tránh xa tầm tay trẻ em.</p>

  <h3>Thành phần nổi bật:</h3>
  <p>Vitamin C dẫn xuất & Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p>
  <p>Chiết xuất lá hoa anh đào: Làm dịu, giảm sạm, giúp da sáng hồng.</p>
  <h3>Bảo quản</h3>
  <p>Bảo quản nơi khô ráo thoáng mát, tránh ánh nắng trực tiếp và nhiệt độ cao.</p>
  <p>Tránh xa tầm tay trẻ em.</p>
</div>
"""

fragment = html.fragment_fromstring(f"<div>{html_content}</div>", create_parent=False)

seen_texts = set()
for element in list(fragment.iter()):
    if element.tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'):
        text = "".join(element.itertext()).strip().lower()
        text = re.sub(r'\s+', ' ', text)
        if len(text) > 20:
            if text in seen_texts:
                print(f"DROPPING: {text}")
                element.drop_tree()
            else:
                seen_texts.add(text)

result = html.tostring(fragment, encoding='unicode', method='html')
print("RESULT:")
print(result)
