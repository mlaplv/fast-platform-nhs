import asyncio
import logging
import re
import hashlib
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.content import Article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup-sge-links")

# Regex to capture the tag and keep the text content inside
# Target: <a class="sge-contextual-link" ...>Anchor Text</a> -> Anchor Text
SGE_LINK_PATTERN = re.compile(
    r'<a\s+[^>]*class=["\'][^"\']*sge-contextual-link[^"\']*["\'][^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL
)

async def cleanup_injected_links():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        logger.info("Fetching all active articles...")
        stmt = select(Article).where(Article.deleted_at.is_(None))
        result = await session.execute(stmt)
        articles = result.scalars().all()

        total_cleaned_articles = 0
        total_removed_links = 0

        for article in articles:
            if not article.content:
                continue

            content = article.content
            # Run regex substitution
            new_content, count = SGE_LINK_PATTERN.subn(r'\1', content)

            if count > 0:
                logger.info(
                    f"Article '{article.title}' (ID: {article.id}) contains {count} SGE link(s). Cleaning..."
                )
                article.content = new_content
                
                # Mark dirty for SQLAlchemy
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(article, "content")

                total_cleaned_articles += 1
                total_removed_links += count

        if total_cleaned_articles > 0:
            logger.info("Committing changes to database...")
            await session.commit()
            logger.info(
                f"Successfully cleaned {total_cleaned_articles} article(s) and removed {total_removed_links} SGE link(s)."
            )
        else:
            logger.info("No articles with injected SGE links found. Database is already clean.")

if __name__ == "__main__":
    asyncio.run(cleanup_injected_links())
