import pytest
import asyncio
from backend.services.prompt_entropy import (
    get_dynamic_prompt_context, build_entropy_system_prompt,
    TONE_SEEDS, STRUCTURE_SEEDS,
)
from backend.services.lexical_sanitizer import sanitize_ai_text

@pytest.mark.asyncio
async def test_lexical_sanitizer_removes_buzzwords():
    # Giả lập đoạn text do AI sinh ra chứa nhiều từ "cấm"
    raw_ai_text = (
        "Nhìn chung, sản phẩm này rất tốt. "
        "Thật không ngoa khi nói rằng đây là một bước tiến lớn. "
        "Tóm lại, hãy sử dụng nó."
    )
    
    # Chạy hàm làm sạch
    cleaned_text = sanitize_ai_text(raw_ai_text)
    
    # Kiểm tra xem các từ cấm đã bị loại bỏ chưa
    assert "Thật không ngoa khi nói" not in cleaned_text
    assert "Tóm lại" not in cleaned_text
    assert "sản phẩm này rất tốt" in cleaned_text

@pytest.mark.asyncio
async def test_lexical_sanitizer_removes_extended_buzzwords():
    """SGE Shield V2.0: Test extended Vietnamese AI buzzwords."""
    raw_ai_text = (
        "Nhìn chung, đây là một trong những sản phẩm tốt nhất. "
        "Qua bài viết này, chúng ta có thể thấy hiệu quả rõ rệt. "
        "Như vậy, sản phẩm cung cấp cho bạn giải pháp toàn diện."
    )
    
    cleaned_text = sanitize_ai_text(raw_ai_text)
    
    assert "Nhìn chung" not in cleaned_text
    assert "Qua bài viết" not in cleaned_text
    assert "Như vậy" not in cleaned_text
    assert "cung cấp cho bạn" not in cleaned_text

@pytest.mark.asyncio
async def test_prompt_entropy_deterministic_seed():
    # Cùng 1 seed thì phải ra cùng 1 tone và structure
    seed = "campaign_123"
    ctx1 = get_dynamic_prompt_context(product_id=seed)
    ctx2 = get_dynamic_prompt_context(product_id=seed)
    
    assert ctx1["tone_id"] == ctx2["tone_id"]
    assert ctx1["structure_id"] == ctx2["structure_id"]

@pytest.mark.asyncio
async def test_prompt_entropy_random_seed():
    # Không có seed thì sẽ ngẫu nhiên (chỉ test hàm chạy ổn không lỗi)
    ctx = get_dynamic_prompt_context()
    assert "tone_instruction" in ctx
    assert "structure_instruction" in ctx

@pytest.mark.asyncio
async def test_build_entropy_system_prompt():
    base_prompt = "Bạn là một AI."
    final_prompt = build_entropy_system_prompt(base_prompt, product_id="test_1")
    
    assert "Bạn là một AI." in final_prompt
    assert "[WRITING STYLE]" in final_prompt
    assert "[CONTENT STRUCTURE]" in final_prompt


def test_tone_seeds_count():
    """SGE Shield V2.0: Verify 10 tone personas are configured."""
    assert len(TONE_SEEDS) == 10
    ids = [t["id"] for t in TONE_SEEDS]
    # Verify new osmo-specific personas exist
    assert "beauty_editor" in ids
    assert "nutrition_consultant" in ids


def test_structure_seeds_count():
    """SGE Shield V2.0: Verify 10 structure templates are configured."""
    assert len(STRUCTURE_SEEDS) == 10
    ids = [s["id"] for s in STRUCTURE_SEEDS]
    # Verify new structures exist
    assert "inverted_pyramid" in ids
    assert "myth_busting" in ids
    assert "timeline_journey" in ids


def test_structure_seeds_have_detailed_instructions():
    """SGE Shield V2.0: Verify each structure instruction is detailed (>100 chars)."""
    for seed in STRUCTURE_SEEDS:
        assert len(seed["instruction"]) >= 100, (
            f"Structure '{seed['id']}' instruction too short: {len(seed['instruction'])} chars"
        )


def test_tone_seeds_have_detailed_instructions():
    """SGE Shield V2.0: Verify each tone instruction is detailed (>100 chars)."""
    for seed in TONE_SEEDS:
        assert len(seed["instruction"]) >= 100, (
            f"Tone '{seed['id']}' instruction too short: {len(seed['instruction'])} chars"
        )


def test_all_seeds_have_unique_ids():
    """SGE Shield V2.0: Verify no duplicate IDs in tone or structure seeds."""
    tone_ids = [t["id"] for t in TONE_SEEDS]
    structure_ids = [s["id"] for s in STRUCTURE_SEEDS]
    assert len(tone_ids) == len(set(tone_ids)), "Duplicate tone IDs found"
    assert len(structure_ids) == len(set(structure_ids)), "Duplicate structure IDs found"
