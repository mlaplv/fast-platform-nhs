import asyncio
import json
import pytest
from litestar.testing import TestClient
from backend.main import app
from backend.services.event_bus import event_bus

# Elite V2.2: Pulse SSE Protocol Test Suite (Real-time)

@pytest.mark.asyncio
async def test_pulse_sse_stream():
    """Verify that ClientPulseController streams events via SSE."""
    session_id = "test_pulse_999"
    
    with TestClient(app=app) as client:
        # 1. Connect to Pulse SSE
        # Litestar TestClient.get with stream=True
        with client.get(f"/api/v1/client/support/pulse/{session_id}") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            
            # 2. In a background task, emit the event via InternalBus
            async def trigger_event():
                await asyncio.sleep(0.5) # Wait for connection to settle
                await event_bus.emit("SUPPORT_RESPONSE_READY", {
                    "session_id": session_id,
                    "payload": {
                        "status": "DONE",
                        "reply": "Chào Sếp, em đã sẵn sàng!"
                    }
                })
            
            asyncio.create_task(trigger_event())
            
            # 3. Read the stream
            # The stream should contain our event
            lines = []
            for line in response.iter_lines():
                if line:
                    lines.append(line.decode("utf-8"))
                    # Break after 2 lines (data and possibly id/event)
                    if len(lines) >= 2: break
            
            # Verify SSE format
            assert any("data:" in l for l in lines)
            data_line = [l for l in lines if l.startswith("data:")][0]
            data = json.loads(data_line.replace("data: ", ""))
            
            assert data["event"] == "SUPPORT_RESPONSE_READY"
            assert data["payload"]["reply"] == "Chào Sếp, em đã sẵn sàng!"

@pytest.mark.asyncio
async def test_pulse_unauthorized_session():
    """Verify that Pulse correctly filters sessions."""
    session_id_correct = "session_A"
    session_id_wrong = "session_B"
    
    with TestClient(app=app) as client:
        with client.get(f"/api/v1/client/support/pulse/{session_id_correct}") as response:
            
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
            
            asyncio.create_task(trigger_wrong_event())
            
            results = []
            for line in response.iter_lines():
                if line.startswith(b"data:"):
                    data = json.loads(line.decode("utf-8").replace("data: ", ""))
                    results.append(data)
                    if len(results) >= 1: break
            
            # Should NOT receive session_B's data
            assert results[0]["payload"]["reply"] == "Nội dung đúng"
