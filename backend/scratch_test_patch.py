import asyncio
import re
from sqlalchemy import select
from backend.database import alchemy_config, current_tenant_id
from backend.database.models.seo import SeoContextualLink, SeoContextualLinkStatus

async def test():
    token = current_tenant_id.set("osmo.vn")
    session_maker = alchemy_config.create_session_maker()
    try:
        async with session_maker() as db:
            # Lấy 1 link pending để test
            link = await db.scalar(
                select(SeoContextualLink).where(
                    SeoContextualLink.status == "pending"
                ).limit(1)
            )
            if not link:
                print("Không tìm thấy link pending nào!")
                return
            
            print(f"Thử duyệt link ID: {link.id}, Target URL: {link.target_url}")
            
            # Mô phỏng logic của controller
            new_status = "approved"
            link.status = SeoContextualLinkStatus(new_status)
            
            attrs = []
            if link.link_rel and link.link_rel.strip().lower() not in ["", "dofollow"]:
                attrs.append(f'rel="{link.link_rel.strip()}"')
            if link.link_title:
                attrs.append(f'title="{link.link_title.strip()}"')
            if link.link_target:
                attrs.append(f'target="{link.link_target.strip()}"')

            attr_str = " " + " ".join(attrs) if attrs else ""
            a_tag = f'<a href="{link.target_url}" class="sge-contextual-link" data-sge-source="ai"{attr_str}>{link.anchor_text}</a>'
            
            print(f"Original sentence: {link.original_sentence}")
            print(f"Anchor text: {link.anchor_text}")
            
            link.linked_sentence = link.original_sentence.replace(link.anchor_text, a_tag, 1)
            print(f"Linked sentence: {link.linked_sentence}")
            
            await db.commit()
            print("Cập nhật thành công vào DB!")
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        current_tenant_id.reset(token)

if __name__ == "__main__":
    asyncio.run(test())
