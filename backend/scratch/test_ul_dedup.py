from lxml import html
import re

html_str = """
<h3><strong><em>Thành phần nổi bật:</em></strong></h3>
<ul>
    <li><p>Vitamin C dẫn xuất & Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p></li>
</ul>
<h3><strong><em>Thành phần nổi bật:</em></strong></h3>
<ul>
    <li><p>Vitamin C dẫn xuất & Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p></li>
</ul>
"""
fragment = html.fragment_fromstring(f"<div>{html_str}</div>", create_parent=False)

dedup_tags = ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol')
blocks = []
for el in list(fragment.iter()):
    if el.tag in dedup_tags:
        has_dedup_ancestor = False
        ancestor = el.getparent()
        while ancestor is not None:
            if ancestor.tag in dedup_tags:
                has_dedup_ancestor = True
                break
            ancestor = ancestor.getparent()
        
        if not has_dedup_ancestor:
            blocks.append(el)

texts = []
for el in blocks:
    t = "".join(el.itertext()).strip().lower()
    texts.append(re.sub(r'\s+', ' ', t))

to_drop = set()
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

print("\nResult:")
print(html.tostring(fragment, encoding='unicode', method='html'))
