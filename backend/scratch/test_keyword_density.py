import asyncio
import sys
from typing import Optional

# Setup import path
sys.path.append("/app")

from backend.services.xohi.creative_studio.models.schemas import ContentCampaign
from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer

class MockCampaign(ContentCampaign):
    id: str = "adhoc"
    draft_content: Optional[str] = "Tiêu đề bài viết hay"
    gold_metadata: Optional[dict] = {"topic": "Kem trị nám Miccosmo 20 g: Dưỡng trắng sâu nhờ Platinum Placenta"}

    def get_gold_val(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.gold_metadata.get(key, default)

async def test_run():
    analyzer = SeoAnalyzer()
    campaign = MockCampaign()
    print("Testing _audit_keyword_density...")
    
    # 1. Test when keyword is missing
    draft = "<h1>Tiêu đề bài viết hay</h1><p>Đây là nội dung bài viết.</p>"
    plain_text = "Tiêu đề bài viết hay Đây là nội dung bài viết."
    primary = "Kem trị nám Miccosmo 20 g: Dưỡng trắng sâu nhờ Platinum Placenta"
    
    annotations = analyzer._audit_keyword_density(plain_text, primary, draft=draft)
    
    print(f"Number of annotations: {len(annotations)}")
    for a in annotations:
        print(f"Type: {a.type}")
        print(f"Text: '{a.text}'")
        print(f"Message: {a.message}")
        assert a.type == "keyword_missing"
        assert len(a.text) > 5
        assert a.text == "<h1>Tiêu đề bài viết hay</h1>"
        print("Test 1 (H1 extracted) passed!")

    # 2. Test fallback when no H1 exists
    draft_no_h1 = "<p>Đây là đoạn văn đầu tiên.</p>"
    plain_text_no_h1 = "Đây là đoạn văn đầu tiên."
    annotations_no_h1 = analyzer._audit_keyword_density(plain_text_no_h1, primary, draft=draft_no_h1)
    for a in annotations_no_h1:
        assert a.type == "keyword_missing"
        assert a.text == "<p>Đây là đoạn văn đầu tiên.</p>"
        print("Test 2 (P extracted) passed!")

if __name__ == "__main__":
    asyncio.run(test_run())
