import asyncio
import logging
import re
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from backend.database.alchemy_config import alchemy_config
from backend.database.models.commerce import ProductBase, ProductVariant
from backend.database.models.content import Category, Article, ContentCampaign
from backend.database.models.system import SystemReview, SupportKnowledge, SupportChatHistory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scrub-placenta")

PLACENTA_PATTERN = re.compile(r"nhau\s+thai", re.IGNORECASE)

def scrub_text(text: str) -> str:
    if not text:
        return text
    return PLACENTA_PATTERN.sub("Placenta", text)

def scrub_json(val):
    if isinstance(val, str):
        return scrub_text(val)
    elif isinstance(val, dict):
        return {scrub_json(k): scrub_json(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [scrub_json(x) for x in val]
    return val

async def scrub_database():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        logger.info("Starting historical database scrubbing for legacy term 'nhau thai'...")

        # 1. Categories
        logger.info("Scrubbing Categories...")
        cat_stmt = select(Category).where(Category.deleted_at.is_(None))
        cat_res = await session.execute(cat_stmt)
        categories = cat_res.scalars().all()
        cat_count = 0
        for cat in categories:
            dirty = False
            for attr in ["name", "description", "seo_title", "seo_description"]:
                val = getattr(cat, attr, None)
                if val:
                    new_val = scrub_text(val)
                    if new_val != val:
                        setattr(cat, attr, new_val)
                        dirty = True
            if cat.category_metadata:
                new_meta = scrub_json(cat.category_metadata)
                if new_meta != cat.category_metadata:
                    cat.category_metadata = new_meta
                    flag_modified(cat, "category_metadata")
                    dirty = True
            if dirty:
                cat_count += 1
        logger.info(f"Updated {cat_count} Category records.")

        # 2. ProductBase
        logger.info("Scrubbing ProductBases...")
        prod_stmt = select(ProductBase).where(ProductBase.deleted_at.is_(None))
        prod_res = await session.execute(prod_stmt)
        products = prod_res.scalars().all()
        prod_count = 0
        for prod in products:
            dirty = False
            for attr in ["name", "short_description", "description", "seo_title", "seo_description", "seo_keywords"]:
                val = getattr(prod, attr, None)
                if val:
                    new_val = scrub_text(val)
                    if new_val != val:
                        setattr(prod, attr, new_val)
                        dirty = True
            for json_attr in ["attributes", "tier_variations", "product_metadata", "analysis_report", "market_data"]:
                val = getattr(prod, json_attr, None)
                if val:
                    new_val = scrub_json(val)
                    if new_val != val:
                        setattr(prod, json_attr, new_val)
                        flag_modified(prod, json_attr)
                        dirty = True
            if dirty:
                prod_count += 1
        logger.info(f"Updated {prod_count} ProductBase records.")

        # 3. ProductVariant
        logger.info("Scrubbing ProductVariants...")
        var_stmt = select(ProductVariant).where(ProductVariant.deleted_at.is_(None))
        var_res = await session.execute(var_stmt)
        variants = var_res.scalars().all()
        var_count = 0
        for var in variants:
            dirty = False
            if var.attributes:
                new_attr = scrub_json(var.attributes)
                if new_attr != var.attributes:
                    var.attributes = new_attr
                    flag_modified(var, "attributes")
                    dirty = True
            if dirty:
                var_count += 1
        logger.info(f"Updated {var_count} ProductVariant records.")

        # 4. Article
        logger.info("Scrubbing Articles...")
        art_stmt = select(Article).where(Article.deleted_at.is_(None))
        art_res = await session.execute(art_stmt)
        articles = art_res.scalars().all()
        art_count = 0
        for art in articles:
            dirty = False
            for attr in ["title", "excerpt", "content", "seo_title", "seo_description", "seo_keywords"]:
                val = getattr(art, attr, None)
                if val:
                    new_val = scrub_text(val)
                    if new_val != val:
                        setattr(art, attr, new_val)
                        dirty = True
            for json_attr in ["article_metadata", "analysis_report"]:
                val = getattr(art, json_attr, None)
                if val:
                    new_val = scrub_json(val)
                    if new_val != val:
                        setattr(art, json_attr, new_val)
                        flag_modified(art, json_attr)
                        dirty = True
            if dirty:
                art_count += 1
        logger.info(f"Updated {art_count} Article records.")

        # 5. ContentCampaign
        logger.info("Scrubbing ContentCampaigns...")
        camp_stmt = select(ContentCampaign).where(ContentCampaign.deleted_at.is_(None))
        camp_res = await session.execute(camp_stmt)
        campaigns = camp_res.scalars().all()
        camp_count = 0
        for camp in campaigns:
            dirty = False
            for attr in ["source_input", "draft_content", "final_html"]:
                val = getattr(camp, attr, None)
                if val:
                    new_val = scrub_text(val)
                    if new_val != val:
                        setattr(camp, attr, new_val)
                        dirty = True
            for json_attr in ["gold_metadata", "topic_data", "assets_data", "outline_data", "analysis_report"]:
                val = getattr(camp, json_attr, None)
                if val:
                    new_val = scrub_json(val)
                    if new_val != val:
                        setattr(camp, json_attr, new_val)
                        flag_modified(camp, json_attr)
                        dirty = True
            if dirty:
                camp_count += 1
        logger.info(f"Updated {camp_count} ContentCampaign records.")

        # 6. SystemReview
        logger.info("Scrubbing SystemReviews...")
        rev_stmt = select(SystemReview).where(SystemReview.deleted_at.is_(None))
        rev_res = await session.execute(rev_stmt)
        reviews = rev_res.scalars().all()
        rev_count = 0
        for rev in reviews:
            dirty = False
            for attr in ["content", "customer_name", "customer_location"]:
                val = getattr(rev, attr, None)
                if val:
                    new_val = scrub_text(val)
                    if new_val != val:
                        setattr(rev, attr, new_val)
                        dirty = True
            for json_attr in ["attributes", "attachments"]:
                val = getattr(rev, json_attr, None)
                if val:
                    new_val = scrub_json(val)
                    if new_val != val:
                        setattr(rev, json_attr, new_val)
                        flag_modified(rev, json_attr)
                        dirty = True
            if dirty:
                rev_count += 1
        logger.info(f"Updated {rev_count} SystemReview records.")

        # 7. SupportKnowledge
        logger.info("Scrubbing SupportKnowledge...")
        sk_stmt = select(SupportKnowledge).where(SupportKnowledge.deleted_at.is_(None))
        sk_res = await session.execute(sk_stmt)
        knowledges = sk_res.scalars().all()
        sk_count = 0
        for sk in knowledges:
            dirty = False
            for attr in ["question", "answer"]:
                val = getattr(sk, attr, None)
                if val:
                    new_val = scrub_text(val)
                    if new_val != val:
                        setattr(sk, attr, new_val)
                        dirty = True
            if sk.tags:
                new_tags = scrub_json(sk.tags)
                if new_tags != sk.tags:
                    sk.tags = new_tags
                    flag_modified(sk, "tags")
                    dirty = True
            if dirty:
                sk_count += 1
        logger.info(f"Updated {sk_count} SupportKnowledge records.")

        # 8. SupportChatHistory
        logger.info("Scrubbing SupportChatHistory...")
        sc_stmt = select(SupportChatHistory).where(SupportChatHistory.deleted_at.is_(None))
        sc_res = await session.execute(sc_stmt)
        chats = sc_res.scalars().all()
        sc_count = 0
        for chat in chats:
            dirty = False
            for attr in ["content", "customer_name"]:
                val = getattr(chat, attr, None)
                if val:
                    new_val = scrub_text(val)
                    if new_val != val:
                        setattr(chat, attr, new_val)
                        dirty = True
            if dirty:
                sc_count += 1
        logger.info(f"Updated {sc_count} SupportChatHistory records.")

        total_updated = cat_count + prod_count + var_count + art_count + camp_count + rev_count + sk_count + sc_count
        if total_updated > 0:
            logger.info("Committing changes to database...")
            await session.commit()
            logger.info("Database scrubbing completed successfully.")
        else:
            logger.info("No legacy entries of 'nhau thai' found. Database is clean.")

if __name__ == "__main__":
    asyncio.run(scrub_database())
