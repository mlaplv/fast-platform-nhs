from ..schema import PromptComponent, PromptCategory

GEMINI_ADAPTER = PromptComponent(
    id="adapter_gemini",
    category=PromptCategory.SHIELD,
    content="""[MODEL ADAPTER: GEMINI]
- Tối ưu hóa cho Multi-modal context.
- Tập trung vào tính logic và suy luận chuỗi (Chain-of-thought)."""
)

CLAUDE_ADAPTER = PromptComponent(
    id="adapter_claude",
    category=PromptCategory.SHIELD,
    content="""[MODEL ADAPTER: CLAUDE]
- Sử dụng cấu trúc rành mạch, phân cấp rõ ràng.
- Chấp nhận các chỉ dẫn phức tạp về sắc thái (nuance)."""
)

def register_adapters(composer_instance) -> None:
    composer_instance.register_component(GEMINI_ADAPTER)
    composer_instance.register_component(CLAUDE_ADAPTER)
