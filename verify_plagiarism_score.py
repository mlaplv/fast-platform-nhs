import sys
import os
import asyncio
import json

# Set up project path
PROJECT_ROOT = "/app"
sys.path.insert(0, PROJECT_ROOT)

from backend.services.xohi.creative_studio.handlers.analyst import AdHocContent
from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop

async def main():
    # Read the saved article content
    with open("/app/last_article_content.txt", "r") as f:
        content = f.read().strip()

    # Create ad-hoc campaign
    topic = "Cơ chế chống lão hóa của kem dưỡng trắng da từ chuyên gia"
    campaign = AdHocContent(content=content, topic=topic, category="CREATIVE_CONTENT")

    # Run PlagiarismCop analysis
    cop = PlagiarismCop()
    print("Running PlagiarismCop.analyze...")
    result = await cop.analyze(campaign, force=True)

    print("\n--- RESULTS ---")
    print(f"Uniqueness Score: {result.uniqueness_score}")
    print(f"Risk Level: {result.risk_level}")
    print("\nAnnotations:")
    for i, ann in enumerate(result.annotations):
        print(f"[{i+1}] {ann.type} - Severity: {ann.severity}")
        print(f"    Text: {repr(ann.text)}")
        print(f"    Reason: {ann.reason}")
        print(f"    Source URL: {ann.source_url}")
    
    print("\nSimilar Sources:")
    for src in result.similar_sources:
        print(f"- {src}")

if __name__ == "__main__":
    asyncio.run(main())
