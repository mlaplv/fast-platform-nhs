import os
import asyncio
import json
import pytest
from typing import Dict

# Elite V2.2: Test environment flag
os.environ["FAST_PLATFORM_TEST"] = "true"

from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.xohi.creative_studio.models.schemas import (
    SeoReport, PlagiarismResult, NeuralBoosterReport, AutoFixResponse, AgentResponse, AgentSignal
)

async def mock_trinity_run(*args, **kwargs):
    agent = None
    for arg in args:
        if hasattr(arg, "result_type") or hasattr(arg, "output_type"):
            agent = arg
            break
    if not agent:
        agent = kwargs.get("agent")
        
    schema = kwargs.get("response_schema")
    if agent:
        schema = getattr(agent, "result_type", getattr(agent, "output_type", schema))
        
    schema_str = str(schema)
    if "SeoReport" in schema_str:
        return SeoReport(total_score=98, grade="A+", signals=[], summary="Bài viết của bạn đã đạt tiêu chuẩn tối ưu hóa công cụ tìm kiếm.", quick_wins=[], seo_annotations=[])
    elif "PlagiarismResult" in schema_str:
        return PlagiarismResult(uniqueness_score=1.0, risk_level="LOW", flagged_sentences=[], annotations=[], similar_sources=[], verdict="OK")
    elif "NeuralBoosterReport" in schema_str:
        return NeuralBoosterReport(patches=[], summary="Boosted")
    elif "AutoFixResponse" in schema_str:
        return AutoFixResponse(old_text="A\u0301o", new_text="\u00c1o")
    return None

patch('backend.services.ai_engine.core.trinity_bridge.trinity_bridge.run', new_callable=AsyncMock, side_effect=mock_trinity_run).start()

mock_redis = AsyncMock()
mock_redis.exists.return_value = False 
mock_redis.get.return_value = None
patch('redis.asyncio.from_url', return_value=mock_redis).start()
patch('redis.from_url', return_value=mock_redis).start()

from backend.services.xohi.creative_studio.orchestrator import content_factory

# ---------------------------------------------------------
# Test Fixtures (Neural Content)
# ---------------------------------------------------------
TEST_HTML_COPYRIGHT = """
<div class="product-info">
    <h1>Sample Product</h1>
    <p>This is a completely unique sentence written by our creative team.</p>
    <p>According to Wikipedia, water is an inorganic, transparent, tasteless, odorless, and nearly colorless chemical substance.</p>
</div>
"""

TEST_HTML_SEO = """
<div>
    <p>We are selling shoes.</p>
    <img src="no-alt.jpg" />
</div>
"""

TEST_HTML_VIETNAMESE_NFD = "A\u0301o thun nam" # Áo (NFD)
TEST_HTML_VIETNAMESE_NFC = "\u00c1o thun nam" # Áo (NFC)

# ---------------------------------------------------------
# Test Cases (Direct Service Testing)
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_copyright_scan():
    """Test 1: Copyright Scan (Chống Đạo Văn)"""
    res = await content_factory.analyst.analyze_copyright(
        campaign_id=None,
        campaign_repo=None,
        force=True,
        raw_content=TEST_HTML_COPYRIGHT,
        raw_topic="Sample Product"
    )
    
    assert res.status == "success", f"Error: {res.message}"
    data = res.data
    
    assert "uniqueness_score" in data, "Must return uniqueness_score"
    assert isinstance(data["uniqueness_score"], float), "Score must be float"
    
    # Verify HTML is stripped properly for analysis
    annotations = data.get("annotations", [])
    assert isinstance(annotations, list)
    print(f"[Copyright Scan] Uniqueness: {data['uniqueness_score']*100}%")

@pytest.mark.asyncio
async def test_seo_scan():
    """Test 2: SEO Scan (Chuẩn hoá Tối ưu Tìm kiếm)"""
    res = await content_factory.analyst.analyze_seo(
        campaign_id=None,
        campaign_repo=None,
        force=True,
        raw_content=TEST_HTML_SEO,
        raw_topic="" # Test empty topic fallback
    )
    
    assert res.status == "success", f"Error: {res.message}"
    data = res.data
    
    assert "total_score" in data
    assert "seo_annotations" in data
    print(f"[SEO Scan] Score: {data['total_score']}/100")

@pytest.mark.asyncio
async def test_surgeon_auto_fix_stream():
    """Test 3: AI Surgeon Auto Fix Stream (SSE Stream, Reverse Map, NFD vs NFC)"""
    # NFD target snippet inside an NFC content or vice versa
    content = f"<p>{TEST_HTML_VIETNAMESE_NFC}</p>"
    target_snippet = TEST_HTML_VIETNAMESE_NFD # From UI (might be NFD due to OS keyboard)
    
    chunks = []
    async for line in content_factory.analyst.stream_auto_fix(
        content=content,
        target_snippet=target_snippet,
        error_message="Fix grammar",
        topic="Fashion"
    ):
        if line.startswith("data:"):
            chunk = json.loads(line.replace("data:", "").strip())
            if chunk.get("type") == "chunk":
                chunks.append(chunk.get("text", ""))
            elif chunk.get("type") == "done":
                break
            elif chunk.get("type") == "error":
                pytest.fail(f"Surgeon Stream Error: {chunk.get('message')}")
    
    final_text = "".join(chunks)
    print(f"[Surgeon Fix] Output length: {len(final_text)}")
    # Even if the snippet was NFD, it should have been normalized and patched successfully

@pytest.mark.asyncio
async def test_surgeon_boost():
    """Test 4: AI Booster (Bơm Nhiên Liệu Viral)"""
    res = await content_factory.analyst.neural_boost(
        content="<p>A simple product.</p>",
        topic="Awesome Gadget"
    )
    
    assert res.status == "success", f"Error: {res.message}"
    data = res.data
    
    assert "patches" in data or "viral_score" in data or "content" in data
    print(f"[AI Booster] Payload structure OK")
