import json
from backend.services.xohi.creative_studio.utils.stitcher import surgical_stitch

content = json.dumps({
    "hero_headline": "Xin chào thế giới!",
    "benefits": ["Giúp da sáng mịn.", "Chống lão hóa nhanh chóng."]
}, ensure_ascii=False)

new_content = surgical_stitch(content, "Giúp da sáng mịn", "Giúp da trắng sáng mịn màng", label="test")
print("Original:", content)
print("New:", new_content)

