import asyncio
import json
import pytest
from litestar.testing import AsyncTestClient
from backend.main import app
from backend.services.event_bus import event_bus

# Elite V2.2: Pulse SSE Protocol Test Suite (Real-time Async)

@pytest.mark.asyncio
async def test_pulse_sse_stream():
    """Verify that ClientPulseController streams events via SSE using AsyncTestClient."""
    session_id = "1234567890abcdef1234567890abcdef"
    
    async with AsyncTestClient(app=app) as client:
        # 1. Connect to Pulse SSE via async stream
        async with client.stream("GET", f"/api/v1/client/support/pulse/{session_id}") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            
            # 2. Emit the event via InternalBus
            async def trigger_event():
                await asyncio.sleep(0.5)  # Wait for connection to settle
                await event_bus.emit("SUPPORT_RESPONSE_READY", {
                    "session_id": session_id,
                    "payload": {
                        "status": "DONE",
                        "reply": "Chào Sếp, em đã sẵn sàng!"
                    }
                })
            
            event_task = asyncio.create_task(trigger_event())
            
            # 3. Read the stream asynchronously
            lines = []
            async for line in response.iter_lines():
                if line:
                    lines.append(line)
                    if len(lines) >= 4:
                        break
            
            await event_task
            
            # Verify SSE format
            assert any("data:" in l for l in lines)
            data_line = [l for l in lines if l.startswith("data:")][0]
            data = json.loads(data_line.replace("data: ", ""))
            
            assert data["payload"]["reply"] == "Chào Sếp, em đã sẵn sàng!"

@pytest.mark.asyncio
async def test_pulse_unauthorized_session():
    """Verify that Pulse correctly filters sessions."""
    session_id_correct = "11111111111111111111111111111111"
    session_id_wrong = "22222222222222222222222222222222"
    
    async with AsyncTestClient(app=app) as client:
        async with client.stream("GET", f"/api/v1/client/support/pulse/{session_id_correct}") as response:
            assert response.status_code == 200
            
            async def trigger_wrong_event():
                await asyncio.sleep(0.5)
                # Emit event for a DIFFERENT session
                await event_bus.emit("SUPPORT_RESPONSE_READY", {
                    "session_id": session_id_wrong,
                    "payload": {"status": "DONE", "reply": "Nội dung riêng tư"}
                })
                # Emit event for correct session to end the test
                await event_bus.emit("SUPPORT_RESPONSE_READY", {
                    "session_id": session_id_correct,
                    "payload": {"status": "DONE", "reply": "Nội dung đúng"}
                })
            
            event_task = asyncio.create_task(trigger_wrong_event())
            
            results = []
            async for line in response.iter_lines():
                if line.startswith("data:"):
                    data = json.loads(line.replace("data: ", ""))
                    results.append(data)
                    if len(results) >= 1:
                        break
            
            await event_task
            
            # Should NOT receive session_B's data
            assert results[0]["payload"]["reply"] == "Nội dung đúng"
