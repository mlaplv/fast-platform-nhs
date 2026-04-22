import pytest
import asyncio
from backend.services.prompt_entropy import get_dynamic_prompt_context, build_entropy_system_prompt
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
