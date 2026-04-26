import asyncio
from backend.services.xohi.prompts import composer

async def test_npo():
    print("Testing NPO Templates...")
    templates = [
        "rewriter_product", "rewriter_article",
        "copyright_analysis", "copyright_surgeon",
        "seo_analysis", "seo_surgeon",
        "inspector_analysis", "inspector_surgeon",
        "pen_outline_article", "pen_draft_article",
        "pen_outline_product", "pen_draft_product",
        "booster_enrich", "booster_surgeon",
        "media_analysis", "insight_discovery"
    ]
    
    for t in templates:
        try:
            prompt = composer.compose(t)
            print(f"✅ {t}: Success (Length: {len(prompt)})")
        except Exception as e:
            print(f"❌ {t}: Failed - {e}")

if __name__ == "__main__":
    asyncio.run(test_npo())
