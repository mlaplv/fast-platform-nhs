import asyncio
import logging
from backend.services.xohi.prompts import composer
from backend.services.xohi.creative_studio.operatives.neural_rewriter import run_neural_rewrite

async def test_review_rewrite():
    content = "Sản phẩm dùng rất tốt, mình rất thích."
    print(f"--- GỐC ---\n{content}")
    
    try:
        # Giả lập call từ API
        result = await run_neural_rewrite(
            content=content,
            content_type="review",
            topic="Test Review",
            feedback="Viết lại cho viral và chuyên nghiệp"
        )
        print(f"\n--- KẾT QUẢ ---\n{result}")
    except Exception as e:
        print(f"\n❌ LỖI: {e}")

if __name__ == "__main__":
    asyncio.run(test_review_rewrite())
