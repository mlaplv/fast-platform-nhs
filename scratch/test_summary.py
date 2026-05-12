import sys
import os
import asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

# Add the workspace to sys.path
sys.path.append("/home/lv/Desktop/fast-platform-core")

from backend.services.ads_protection.fraud_analytics_service import FraudAnalyticsService

async def test_get_summary():
    # Mock Session
    session = AsyncMock()
    
    # Mock result for totals
    mock_result_totals = MagicMock()
    mock_result_totals.all.return_value = [("FRAUD", 10), ("CLEAN", 90)]
    
    # Mock result for Top IPs
    mock_result_ips = MagicMock()
    mock_result_ips.all.return_value = [("1.2.3.4", 5)]
    
    # Mock result for Hourly Breakdown
    mock_result_hourly = MagicMock()
    mock_result_hourly.all.return_value = [(datetime.now(UTC), 100, 10)]
    
    session.execute.side_effect = [
        mock_result_totals,
        mock_result_ips,
        mock_result_hourly
    ]
    
    service = FraudAnalyticsService(session)
    try:
        summary = await service.get_summary(hours=24)
        print("Summary generated successfully:")
        print(summary)
    except Exception as e:
        print(f"Failed to generate summary: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_get_summary())
