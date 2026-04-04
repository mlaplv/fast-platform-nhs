import asyncio
import sys
import argparse
import logging
import os

try:
    from dotenv import load_dotenv
    # Load .env before initializing DB-connected services
    load_dotenv()
except ImportError:
    # R1.2: Fallback for containers or environments where dotenv is not pre-installed
    # We log as warning since variables might be set via Docker ENV
    pass

from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.alchemy_config import alchemy_config
from backend.services.ai_engine.core.brain_manager import brain_manager
from backend.services.ai_engine.core.encoder_singleton import warmup_encoder

# Configure logging for CLI
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("helen-cli")

async def run_command(command: str, **kwargs):
    """
    Executes brain management commands within an async database session.
    """
    # R1.5: Pre-warm the encoder for semantic tasks
    await warmup_encoder()
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        if command == "status":
            logger.info("--- HELEN BRAIN DIAGNOSTICS ---")
            analytics = await brain_manager.get_node_analytics(db)
            duplicates = await brain_manager.get_semantic_duplicates(db)
            
            logger.info(f"Total Entities: {analytics['total_entities']}")
            logger.info(f"Coverage: {analytics['coverage']}%")
            logger.info(f"Health Score: {analytics['health']}")
            
            if duplicates:
                logger.warning(f"⚠️ Found {len(duplicates)} semantic collisions (>92% similarity)")
                for d in duplicates:
                    logger.warning(f"  - [{d['type']}] {d['name']} -> {d['reason']}")
            else:
                logger.info("✅ Neural pathways optimized (Zero Duplication detected).")
            
        elif command == "rebuild":
            logger.info("--- ⚠️ CRITICAL: REBUILDING NEURAL MATRIX ---")
            logger.info("Purging existing embeddings...")
            from sqlalchemy import text
            await db.execute(text("DELETE FROM product_embeddings"))
            await db.execute(text("DELETE FROM article_embeddings"))
            await db.commit()
            
            logger.info("Synchronizing and indexing entities...")
            await brain_manager.sync_all_embeddings(db)
            logger.info("✅ Neural Matrix reconstructed successfully.")
            
        elif command == "clean":
            logger.info("--- DEFRAGMENTING NEURAL MEMORY ---")
            await brain_manager.purge_orphans(db)
            logger.info("✅ Orphaned memories purged.")

def main():
    parser = argparse.ArgumentParser(description="Helen Brain Command Center CLI (Elite V2.2)")
    parser.add_argument("command", choices=["status", "rebuild", "clean"], help="Command to execute")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_command(args.command))
    except KeyboardInterrupt:
        logger.info("Aborted by user.")
    except Exception as e:
        logger.error(f"Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
