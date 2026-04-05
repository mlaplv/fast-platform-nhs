import asyncio
import json
import os
import pytest

# Elite V2.2: Test environment flag (skips heavy AI warmup in lifespan)
os.environ["FAST_PLATFORM_TEST"] = "true"

from litestar.testing import AsyncTestClient
from backend.main import app
from backend.services.event_bus import event_bus

# Elite V2.2: Neural Sync Protocol Test Suite
# Focus: Real-time Message Revocation (is_revoked) via SSE Pulse

@pytest.mark.asyncio
async def test_neural_sync_revoke_protocol():
    """
    Verify the 'Giao thức Neural Sync' (Message Revocation Sync).
    Ensures that when a message is revoked in Admin, the Client's SSE Pulse
    receives the SUPPORT_INBOX_UPDATE event immediately.
    """
    session_id = "test_sync_sid_888"
    message_id = "msg_revoke_999"
    
    async with AsyncTestClient(app=app) as client:
        # 1. Establish SSE Connection for the client session
        async with client.stream("GET", f"/api/v1/client/support/pulse/{session_id}") as response:
            assert response.status_code == 200
            
            # 2. Simulate Admin Revocation Event in background
            async def trigger_revoke():
                print(f"\n[Test] Waiting for SSE stream to stabilize...")
                await asyncio.sleep(1.5) # Increased for Redis/Docker stability
                print(f"[Test] Emitting SUPPORT_INBOX_UPDATE for {session_id}...")
                await event_bus.emit("SUPPORT_INBOX_UPDATE", {
                    "session_id": session_id,
                    "message_id": message_id,
                    "is_revoked": True
                })
                print(f"[Test] Event emitted.")
            
            task = asyncio.create_task(trigger_revoke())
            
            event_name = None
            data_payload = None
            
            # 3. Read and verify the Pulse stream with 10s timeout
            try:
                async with asyncio.timeout(10.0):
                    async for line in response.aiter_lines():
                        if line.startswith("event:"):
                            event_name = line.replace("event:", "").strip()
                        elif line.startswith("data:"):
                            data_payload = json.loads(line.replace("data:", "").strip())
                            print(f"[Test] Received data: {data_payload}")
                            break # Success
            except asyncio.TimeoutError:
                pytest.fail("Timed out waiting for SSE event from Redis Pulse.")
            
            await task # Cleanup
            
            # 4. Neural Sync Verification
            assert event_name == "SUPPORT_INBOX_UPDATE"
            assert data_payload is not None
            assert data_payload["session_id"] == session_id
            assert data_payload["message_id"] == message_id

@pytest.mark.asyncio
async def test_sync_isolation_protocol():
    """
    Verify that Revocation Sync is isolated per session.
    Admin revoking session A must NOT be pushed to session B.
    """
    sid_client = "sid_listening"
    sid_other = "sid_other_admin_target"
    
    async with AsyncTestClient(app=app) as client:
        async with client.stream("GET", f"/api/v1/client/support/pulse/{sid_client}") as response:
            
            async def trigger_cross_session_events():
                await asyncio.sleep(1.5)
                # 1. Revoke in OTHER session
                await event_bus.emit("SUPPORT_INBOX_UPDATE", {
                    "session_id": sid_other,
                    "message_id": "other_msg",
                    "is_revoked": True
                })
                await asyncio.sleep(0.5)
                # 2. Revoke in CLIENT'S session
                await event_bus.emit("SUPPORT_INBOX_UPDATE", {
                    "session_id": sid_client,
                    "message_id": "client_msg",
                    "is_revoked": True
                })
            
            task = asyncio.create_task(trigger_cross_session_events())
            
            received_payloads = []
            try:
                async with asyncio.timeout(10.0):
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            data = json.loads(line.replace("data:", "").strip())
                            received_payloads.append(data)
                            break 
            except asyncio.TimeoutError:
                pytest.fail("Timed out waiting for Isolation Protocol SSE event.")
            
            await task # Cleanup
            
            # 5. Isolation Verification
            assert len(received_payloads) == 1
            assert received_payloads[0]["session_id"] == sid_client
