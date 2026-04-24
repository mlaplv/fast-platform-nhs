import asyncio
from backend.utils.noise_cleaner import noise_cleaner

async def main():
    html = """
    <ul>
        <li><p>Vitamin C dẫn xuất & Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p></li>
    </ul>
    """
    options = {
        "stripFont": True,
        "stripAlign": True,
        "stripRedundantWrappers": True,
        "stripEmpty": True,
        "deduplicateContent": True
    }
    
    # Let's monkey patch the structural pruning logic here just for testing
    from lxml import html as lxml_html
    import re
    fragment = lxml_html.fragment_fromstring(f"<div>{html}</div>", create_parent=False)
    
    dedup_tags = ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li')
    all_blocks = [el for el in list(fragment.iter()) if el.tag in dedup_tags]
    
    blocks = []
    for el in all_blocks:
        has_block_child = any(child.tag in dedup_tags for child in el.iterdescendants())
        if not has_block_child:
            blocks.append(el)
            
    print("Blocks to check:")
    for b in blocks:
        print(b.tag, b.text_content())

asyncio.run(main())
