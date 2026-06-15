import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4
from typing import Generator, Dict, Any, List

from litestar import Litestar
from litestar.testing import TestClient
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED

from backend.controllers.admin_support_inbox import AdminSupportInboxController
from backend.database.models.system import SupportChatHistory
from backend.schemas.support_inbox import SupportSessionListResponse, SupportSessionDetailResponse

# Elite V2.2: Isolated Integration Test Suite for Admin Support Inbox

@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()

@pytest.fixture
def test_client(mock_db: AsyncMock) -> Generator[TestClient, None, None]:
    # Elite V2.2: Clean guard bypass by clearing the controller's guards for the test
    AdminSupportInboxController.guards = []
    
    # Isolated app that only contains the target controller
    app: Litestar = Litestar(
        route_handlers=[AdminSupportInboxController],
        dependencies={"db_session": lambda: mock_db}
    )
    
    # Provide a mock admin user in the scope for all requests
    with TestClient(app=app) as client:
        yield client

@pytest.mark.asyncio
async def test_api_list_sessions(test_client: TestClient, mock_db: AsyncMock) -> None:
    """Test GET /api/v1/admin/support/inbox/sessions"""
    # Mocking DB results
    mock_row: MagicMock = MagicMock()
    mock_row.session_id = "s1"
    mock_row.customer_name = "User 1"
    mock_row.customer_phone = "090"
    mock_row.product_slug = "p1"
    mock_row.intent = "PURCHASE"
    mock_row.created_at = datetime.now()
    
    mock_agg: MagicMock = MagicMock()
    mock_agg.session_id = "s1"
    mock_agg.message_count = 5
    mock_agg.last_message_at = datetime.now()
    mock_agg.any_phone = "090"

    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=1)),  # Total count
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_row])))), # Rows
        MagicMock(all=MagicMock(return_value=[mock_agg])), # Aggregated subquery
    ]

    with patch("backend.services.xohi_memory.xohi_memory.client.get", new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = "0"
        
        resp = test_client.get("/api/v1/admin/support/inbox/sessions")
        
        assert resp.status_code == HTTP_200_OK
        data: Dict[str, object] = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["session_id"] == "s1"
        assert data["data"][0]["is_high_intent"] is True

@pytest.mark.asyncio
async def test_api_get_session(test_client: TestClient, mock_db: AsyncMock) -> None:
    """Test GET /api/v1/admin/support/inbox/sessions/{session_id}"""
    session_id: str = "s1"
    
    mock_msg: MagicMock = MagicMock()
    mock_msg.id = str(uuid4())
    mock_msg.role = "user"
    mock_msg.content = "Encrypted"
    mock_msg.intent = "QUERY"
    mock_msg.created_at = datetime.now()
    mock_msg.customer_name = "User 1"
    mock_msg.customer_phone = "090"
    mock_msg.product_slug = "p1"
    mock_msg.is_revoked = False

    mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_msg]))))

    with patch("backend.utils.security.GeminiSecurity.decrypt", return_value="Decrypted"):
        with patch("backend.services.xohi_memory.xohi_memory.client.get", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = "1"
            
            resp = test_client.get(f"/api/v1/admin/support/inbox/sessions/{session_id}")
            
            assert resp.status_code == HTTP_200_OK
            data: Dict[str, object] = resp.json()
            assert data["session_id"] == session_id
            assert data["is_takeover"] is True
            assert data["messages"][0]["content"] == "Decrypted"

@pytest.mark.asyncio
async def test_api_revoke_message(test_client: TestClient, mock_db: AsyncMock) -> None:
    """Test POST /api/v1/admin/support/inbox/sessions/{sid}/messages/{mid}/revoke"""
    session_id: str = "s1"
    msg_id: str = "m1"
    
    mock_msg: MagicMock = MagicMock(spec=SupportChatHistory)
    mock_msg.is_revoked = False
    
    mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_msg))

    with patch("backend.services.event_bus.event_bus.emit", new_callable=AsyncMock) as mock_emit:
        resp = test_client.post(f"/api/v1/admin/support/inbox/sessions/{session_id}/messages/{msg_id}/revoke")
        
        assert resp.status_code == HTTP_201_CREATED
        assert resp.json()["is_revoked"] is True
        assert mock_msg.is_revoked is True
        mock_emit.assert_called_once()
