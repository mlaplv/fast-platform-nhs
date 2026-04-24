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

blocks = [el for el in list(fragment.iter()) if el.tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li')]
texts = []
for el in blocks:
    t = "".join(el.itertext()).strip().lower()
    texts.append(re.sub(r'\s+', ' ', t))

to_drop = set()
seen_long = set()

for i, text in enumerate(texts):
    if len(text) > 30:
        if text in seen_long:
            to_drop.add(blocks[i])
        else:
            seen_long.add(text)

seen_seqs = set()
for i in range(len(texts) - 1):
    if not texts[i] or not texts[i+1]: continue
    seq = (texts[i], texts[i+1])
    if seq in seen_seqs:
        to_drop.add(blocks[i])
        to_drop.add(blocks[i+1])
    else:
        seen_seqs.add(seq)

for el in to_drop:
    if el.getparent() is not None:
        el.drop_tree()

print(html.tostring(fragment, encoding='unicode', method='html'))
