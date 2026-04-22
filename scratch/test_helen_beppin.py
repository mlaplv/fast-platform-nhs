import asyncio
import json
from backend.services.commerce.operatives.support_agent import support_agent
from backend.schemas.support import SupportRequest

async def test_helen_beppin():
    request = SupportRequest(
        message="Sản phẩm Beppin này có bết dính không em? Công nghệ gì mà nghe lạ vậy?",
        product_slug="miccosmo-beppin-body-virgin-white-serum-30g"
    )
    # Note: We need a DB session. Since we are running in the container, we can use alchemy_config.
    from backend.database.alchemy_config import alchemy_config
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        response = await support_agent.chat(request, db=db)
        print(f"Helen's Reply: {response.reply}")

if __name__ == "__main__":
    asyncio.run(test_helen_beppin())
