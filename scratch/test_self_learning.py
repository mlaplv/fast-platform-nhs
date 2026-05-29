import asyncio
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.alchemy_config import alchemy_config
from backend.services.commerce.self_learning import helen_self_learning
from backend.database.models.system import SupportKnowledge, SupportChatHistory
from backend.utils.uid import new_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-learning")

async def test_self_learning():
    async_session = alchemy_config.create_session_maker()
    
    async with async_session() as db:
        # Create a mock high-quality customer conversation to learn from
        session_id = f"test_learn_{new_id()[:8]}"
        logger.info(f"🧪 Creating mock chat history in session: {session_id}")
        
        m1 = SupportChatHistory(
            id=new_id(),
            session_id=session_id,
            role="user",
            content="Sản phẩm White Label Placenta Cream có trị được thâm mụn sẹo rỗ lâu năm không shop?",
            product_slug="miccosmo-white-label-placenta-rich-gold-cream-60g-kem-ho-tro-duong-sang-ngua-lao-hoa",
            customer_name="Chị Hoa"
        )
        m2 = SupportChatHistory(
            id=new_id(),
            session_id=session_id,
            role="assistant",
            content="Dạ Chị Hoa ơi, siêu phẩm kem dưỡng White Label Placenta Rich Gold Cream chứa tinh chất nhau thai đậm đặc kết hợp Hyaluronic Acid và Collagen. Sản phẩm cực kỳ hiệu quả trong việc tái tạo tế bào da, làm sáng các vết thâm mụn và lấp đầy các sẹo rỗ nhẹ sau 14 ngày sử dụng đều đặn đấy ạ! 🌸",
            product_slug="miccosmo-white-label-placenta-rich-gold-cream-60g-kem-ho-tro-duong-sang-ngua-lao-hoa",
            customer_name="Chị Hoa"
        )
        m3 = SupportChatHistory(
            id=new_id(),
            session_id=session_id,
            role="user",
            content="Hay quá shop, vậy hướng dẫn mình cách thoa làm sao hiệu quả nhất nhé.",
            product_slug="miccosmo-white-label-placenta-rich-gold-cream-60g-kem-ho-tro-duong-sang-ngua-lao-hoa",
            customer_name="Chị Hoa"
        )
        m4 = SupportChatHistory(
            id=new_id(),
            session_id=session_id,
            role="assistant",
            content="Dạ chị thoa một lượng bằng hạt đậu vào mỗi buổi sáng và tối sau bước rửa mặt sạch và toner, vỗ nhẹ 30 giây để dưỡng chất thẩm thấu sâu nhất vào vùng sẹo thâm ạ! ✨",
            product_slug="miccosmo-white-label-placenta-rich-gold-cream-60g-kem-ho-tro-duong-sang-ngua-lao-hoa",
            customer_name="Chị Hoa"
        )
        
        db.add_all([m1, m2, m3, m4])
        await db.commit()
        
        logger.info("🧪 Triggering Helen AI Self-Learning Core...")
        res = await helen_self_learning.run_auto_learning(db, limit_sessions=5)
        
        logger.info(f"📊 Auto-learning execution results: {res}")
        assert res["scanned"] > 0, "Should scan the newly inserted mock conversation"
        
        # Verify that candidate items are created in sandbox (is_active=False)
        stmt = select(SupportKnowledge).where(
            and_(
                SupportKnowledge.source_url == f"chat_session:{session_id}",
                SupportKnowledge.is_active == False
            )
        )
        db_res = await db.execute(stmt)
        sandbox_items = db_res.scalars().all()
        
        logger.info(f"📦 Sandbox candidate items count: {len(sandbox_items)}")
        for idx, item in enumerate(sandbox_items):
            logger.info(f"  Candidate {idx+1}: Q: '{item.question}' | A: '{item.answer}'")
            logger.info(f"  Reasoning: {item.tags.get('reasoning')}")
            
            # Test sandbox approval workflow
            logger.info(f"⚡ Testing Sandbox Approval for item: {item.id}")
            ok = await helen_self_learning.approve_sandbox_item(db, item.id)
            assert ok is True, "Approval should succeed and trigger pgvector re-indexing"
            
            # Verify it is now active in DB
            refreshed = (await db.execute(select(SupportKnowledge).where(SupportKnowledge.id == item.id))).scalar_one()
            assert refreshed.is_active is True, "Item should be active after approval"
            assert refreshed.tags.get("status") == "APPROVED", "Status metadata tag should be updated"
            
        logger.info("\n🟢 HELEN AI SELF-LEARNING CORE PIPELINE TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_self_learning())
