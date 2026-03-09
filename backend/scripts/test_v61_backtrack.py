import asyncio
import logging
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

# Mocking the signals and responses since we want a standalone proof
from enum import Enum

class AgentSignal(str, Enum):
    PROCEED_NEXT = "PROCEED_NEXT"
    REDO_PREVIOUS = "REDO_PREVIOUS"
    FAIL_GRACEFULLY = "FAIL_GRACEFULLY"

@dataclass
class AgentResponse:
    signal: AgentSignal
    message: str
    data: Optional[Dict[str, Any]] = None

# Mocking DB Models
@dataclass
class MockCampaign:
    id: str
    current_step: int
    status: str
    tenant_id: str = "test-tenant"
    topic_data: Dict = field(default_factory=dict)
    gold_metadata: Dict = field(default_factory=dict)
    assets_data: List = field(default_factory=list)

@dataclass
class MockEvent:
    id: str
    campaign_id: str
    event_type: str
    payload: Dict
    tenant_id: str

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("v61_backtrack_test")

class MockOrchestrator:
    def __init__(self):
        self.events = []
        self.campaign = MockCampaign(id="CAMP-99", current_step=3, status="PROCESSING")
        self.semaphore = asyncio.Semaphore(3)

    async def _log_error(self, cid, repo, status, msg):
        logger.error(f"   [ORCH] ERROR Logged: {msg}")
        self.campaign.status = status

    async def execute_step(self, step: int, mode: str = "NORMAL"):
        logger.info(f"--- EXECUTING STEP {step} (Mode: {mode}) ---")
        
        # Simulate Operative Logic
        if step == 3:
            if mode == "FAIL":
                logger.warning(f"   [AGENT 3] Result poor. Sending REDO_PREVIOUS signal.")
                return AgentResponse(signal=AgentSignal.REDO_PREVIOUS, message="Quality check failed")
            return AgentResponse(signal=AgentSignal.PROCEED_NEXT, message="Draft ready")
        
        return AgentResponse(signal=AgentSignal.PROCEED_NEXT, message="Success")

    async def broker_logic(self):
        """Standalone version of the Orchestrator brokerage logic."""
        step = self.campaign.current_step
        
        # Determine mode to simulate backtracking
        # We'll force a fail for Step 3 to test backtracking
        mode = "FAIL" if step == 3 else "NORMAL"
        
        response = await self.execute_step(step, mode=mode)
        
        if response.signal == AgentSignal.REDO_PREVIOUS:
            # Count backtracks in mock storage
            backtracks = [e for e in self.events if e.event_type == "BACKTRACK" and e.payload["step"] == step]
            count = len(backtracks)
            
            if count < 2:
                logger.warning(f"   [BROKER] BACKTRACK {count + 1}/2: {response.message}")
                self.events.append(MockEvent(
                    id=str(uuid.uuid4()),
                    campaign_id=self.campaign.id,
                    event_type="BACKTRACK",
                    payload={"step": step, "reason": response.message},
                    tenant_id="test"
                ))
                self.campaign.current_step = max(1, step - 1)
                logger.info(f"   [ORCH] Reverting to Step {self.campaign.current_step}")
                return "BACKTRACKED"
            else:
                logger.error(f"   [BROKER] MAX BACKTRACKS REACHED. Escalating.")
                response.signal = AgentSignal.FAIL_GRACEFULLY

        if response.signal == AgentSignal.FAIL_GRACEFULLY:
            await self._log_error(self.campaign.id, None, "ERROR", response.message)
            return "FAILED"

        logger.info(f"   [BROKER] Signal: {response.signal}. Proceeding.")
        self.campaign.current_step += 1
        return "SUCCESS"

async def run_test():
    logger.info("=== AGENTIC 2026: BACKTRACKING & SIGNAL BROKER TEST ===")
    logger.info(f"Starting at Step 3. Operative 3 is set to FAIL quality check.")
    logger.info("-" * 60)
    
    orchestrator = MockOrchestrator()
    
    # Run loop to simulate autonomous recovery
    max_loops = 10
    loops = 0
    while loops < max_loops:
        loops += 1
        result = await orchestrator.broker_logic()
        if result == "FAILED":
            logger.info("-" * 60)
            logger.info("RESULT: System failed gracefully after 2 retries (Loop Protection Active).")
            break
        if orchestrator.campaign.current_step > 4:
            logger.info("-" * 60)
            logger.info("RESULT: Process completed successfully.")
            break
        await asyncio.sleep(0.5)

    logger.info("=== TEST COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(run_test())
