import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("v61_qa_test")

class MockOrchestrator:
    def __init__(self, limit=3):
        self.semaphore = asyncio.Semaphore(limit)

async def simulate_campaign(orchestrator, campaign_id):
    start_wait = datetime.now()
    logger.info(f"[{start_wait.strftime('%H:%M:%S.%f')}] [WAIT] Campaign {campaign_id} queueing...")
    
    async with orchestrator.semaphore:
        start_exec = datetime.now()
        wait_duration = (start_exec - start_wait).total_seconds()
        logger.info(f"[{start_exec.strftime('%H:%M:%S.%f')}] [EXEC] SEMAPHORE ACQUIRED for {campaign_id} (Waited {wait_duration:.2f}s)")
        
        # Simulate operative work (e.g., LLM call or hunting)
        await asyncio.sleep(2) 
        
        end_exec = datetime.now()
        logger.info(f"[{end_exec.strftime('%H:%M:%S.%f')}] [DONE] SEMAPHORE RELEASED for {campaign_id}")

async def main():
    # Proof of Concept for R101: Concurrency Guard
    orchestrator = MockOrchestrator(limit=3)
    
    logger.info("=== V61.0 ARCHITECTURE GUARD: SEMAPHORE STRESS TEST ===")
    logger.info(f"Configuration: Concurrency Limit = 3 | Total Incoming Tasks = 5")
    logger.info("-" * 65)
    
    tasks = [simulate_campaign(orchestrator, f"CAMP-{i}") for i in range(1, 6)]
    await asyncio.gather(*tasks)
    
    logger.info("-" * 65)
    logger.info("=== TEST COMPLETED: Observe only 3 tasks running at any time ===")

if __name__ == "__main__":
    asyncio.run(main())
