import asyncio
import os
import sys
import logging

# Configure logging to show all logs in stdout
logging.basicConfig(level=logging.INFO)

# Ensure backend is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.agent_monitor import AgentMonitor
from backend.services.xohi_memory import xohi_memory

async def run_test():
    # Wait a tiny bit for any background connections to establish
    await asyncio.sleep(0.5)
    
    print("🧹 Cleaning up initial shutdown state...")
    await AgentMonitor.reset_shutdown()
    
    # Check initial shutdown status
    is_sd = await AgentMonitor.is_shutdown()
    print(f"Initial shutdown state (should be False): {is_sd}")
    assert not is_sd, "Failed to reset shutdown state initially"
    
    # 1. Trigger $5 threshold limit (exceeds $5 equivalent to 66,666,666 input tokens)
    print("\n👉 Recording 70,000,000 input tokens (exceeds $5 limit)...")
    await AgentMonitor.record_token_usage(70000000, 0)
    is_sd = await AgentMonitor.is_shutdown()
    print(f"Shutdown state after $5: {is_sd} (should be False)")
    
    # Check if $5 alert sent flag is in Redis
    r = xohi_memory.client
    alert_5 = await r.get("agent:metrics:alert_sent:5.0")
    print(f"Alert sent flag for $5 in Redis (should be 1): {alert_5}")
    assert alert_5 == "1" or alert_5 == b"1", "Alert flag for $5 was not set in Redis"
    
    # 2. Trigger $20 threshold limit (exceeds $20 equivalent to 266,666,666 input tokens)
    print("\n👉 Recording another 200,000,000 input tokens (total 270,000,000, exceeds $20 limit)...")
    await AgentMonitor.record_token_usage(200000000, 0)
    is_sd = await AgentMonitor.is_shutdown()
    print(f"Shutdown state after $20: {is_sd} (should be True)")
    assert is_sd, "Gateway did not shutdown when budget exceeded $20"
    
    # Check if $20 alert sent flag is in Redis
    alert_20 = await r.get("agent:metrics:alert_sent:20.0")
    print(f"Alert sent flag for $20 in Redis (should be 1): {alert_20}")
    assert alert_20 == "1" or alert_20 == b"1", "Alert flag for $20 was not set in Redis"
    
    # 3. Test Reset / Reopen
    print("\n👉 Resetting and reopening the gateway...")
    await AgentMonitor.reset_shutdown()
    is_sd = await AgentMonitor.is_shutdown()
    print(f"Shutdown state after reopen (should be False): {is_sd}")
    assert not is_sd, "Failed to reopen gateway"
    
    print("\n✨ ALL BUDGET SHUTDOWN INTEGRATION TESTS PASSED SUCCESSFULLY! ✨")

if __name__ == "__main__":
    asyncio.run(run_test())
