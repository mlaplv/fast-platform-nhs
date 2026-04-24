from lxml import html
import re

html_str = """
<h3><strong><em>Thành phần nổi bật:</em></strong></h3>
<ul><li><p>Vitamin C dẫn xuất &amp; Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p></li></ul>
<h3><strong>Công dụng của Miccosmo Beppin Body Virgin White Serum</strong></h3>
<ul><li><p>Serum dưỡng sáng hồng và làm đều màu da.</p></li></ul>

<h3><strong><em>Thành phần nổi bật:</em></strong></h3>
<ul><li><p>Vitamin C dẫn xuất &amp; Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p></li></ul>
<h3><strong>Công dụng của Miccosmo Beppin Body Virgin White Serum</strong></h3>
<ul><li><p>Serum dưỡng sáng hồng và làm đều màu da.</p></li></ul>
"""
fragment = html.fragment_fromstring(f"<div>{html_str}</div>", create_parent=False)

def get_text(el):
    return re.sub(r'\s+', ' ', "".join(el.itertext()).strip().lower())

# Sibling-level Deduplication
to_drop = set()
for parent in fragment.iter():
    children = list(parent)
    if not children: continue
    
    texts = [get_text(child) for child in children]
    
    # Sequence Dedup (Window size 2)
    seen_seqs = set()
    for i in range(len(texts) - 1):
        if not texts[i] or not texts[i+1]: continue
        seq = (texts[i], texts[i+1])
        if seq in seen_seqs:
            to_drop.add(children[i])
            to_drop.add(children[i+1])
        else:
            seen_seqs.add(seq)
            
    # Single element Dedup (for long paragraphs > 30 chars)
    seen_long = set()
    for i, t in enumerate(texts):
        if len(t) > 30:
            if t in seen_long:
                to_drop.add(children[i])
            else:
                seen_long.add(t)

for el in to_drop:
    if el.getparent() is not None:
        el.drop_tree()

print("Result:")
print(html.tostring(fragment, encoding='unicode', method='html'))
