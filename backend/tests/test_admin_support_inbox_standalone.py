import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4

from backend.controllers.admin_support_inbox import AdminSupportInboxController
from backend.database.models.system import SupportChatHistory
from backend.schemas.support_inbox import SupportManualMessageRequest
from litestar.exceptions import NotFoundException

class TestAdminSupportInbox(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.controller = AdminSupportInboxController()
        # Mocking db_session (AsyncSession)
        self.mock_db = AsyncMock()

    async def test_admin_list_sessions(self):
        """Test listing sessions with pagination and search."""
        # Mock data
        mock_row = MagicMock()
        mock_row.session_id = "sess_1"
        mock_row.customer_name = "Test User"
        mock_row.customer_phone = "0123456789"
        mock_row.product_slug = "test-prod"
        mock_row.intent = "PURCHASE"
        mock_row.created_at = datetime.now()
        
        mock_agg = MagicMock()
        mock_agg.session_id = "sess_1"
        mock_agg.message_count = 5
        mock_agg.last_message_at = datetime.now()
        mock_agg.any_phone = "0123456789"

        # Mock execute results
        mock_result_total = MagicMock()
        mock_result_total.scalar_one_or_none.return_value = 1
        
        mock_result_rows = MagicMock()
        mock_result_rows.scalars.return_value.all.return_value = [mock_row]
        
        mock_result_agg = MagicMock()
        mock_result_agg.all.return_value = [mock_agg]

        # Side effects for multiple db_session.execute calls
        self.mock_db.execute.side_effect = [
            mock_result_total,  # count_q
            mock_result_rows,   # paged
            mock_result_agg     # subq
        ]

        with patch("backend.services.xohi_memory.xohi_memory.client.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "0" # Not takeover
            
            res = await self.controller.list_sessions(self.mock_db)
            
            self.assertEqual(res.total, 1)
            self.assertEqual(len(res.data), 1)
            self.assertEqual(res.data[0].session_id, "sess_1")
            self.assertTrue(res.data[0].is_high_intent) # Because of PURCHASE intent

    async def test_admin_get_session(self):
        """Test retrieving full chat history for a session."""
        session_id = "sess_1"
        
        mock_msg = MagicMock()
        mock_msg.id = uuid4()
        mock_msg.role = "user"
        mock_msg.content = "Encrypted Content"
        mock_msg.intent = "QUERY"
        mock_msg.created_at = datetime.now()
        mock_msg.customer_name = "Test User"
        mock_msg.customer_phone = "0123"
        mock_msg.product_slug = "prod"
        mock_msg.is_revoked = False

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_msg]
        self.mock_db.execute.return_value = mock_result

        with patch("backend.utils.security.GeminiSecurity.decrypt") as mock_decrypt:
            mock_decrypt.return_value = "Decrypted Content"
            with patch("backend.services.xohi_memory.xohi_memory.client.get", new_callable=AsyncMock) as mock_redis:
                mock_redis.return_value = "1" # Takeover active
                
                res = await self.controller.get_session(self.mock_db, session_id)
                
                self.assertEqual(res.session_id, session_id)
                self.assertEqual(len(res.messages), 1)
                self.assertEqual(res.messages[0].content, "Decrypted Content")
                self.assertTrue(res.is_takeover)

    async def test_admin_takeover_toggle(self):
        """Test switching AI takeover state in Redis."""
        session_id = "sess_1"
        
        with patch("backend.services.xohi_memory.xohi_memory.client.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "0"
            with patch("backend.services.xohi_memory.xohi_memory.client.set", new_callable=AsyncMock) as mock_set:
                res = await self.controller.toggle_takeover(session_id)
                self.assertTrue(res["is_takeover"])
                mock_set.assert_called_once()

    async def test_admin_send_manual_message(self):
        """Test sending manual message as admin."""
        session_id = "sess_1"
        payload = SupportManualMessageRequest(message="Hello from admin")
        
        # Mock session metadata lookup
        mock_meta = MagicMock()
        mock_meta.customer_name = "User"
        mock_meta.customer_phone = "0123"
        mock_meta.product_slug = "prod"
        
        mock_result_meta = MagicMock()
        mock_result_meta.scalar_one_or_none.return_value = mock_meta
        self.mock_db.execute.return_value = mock_result_meta

        with patch("backend.utils.security.GeminiSecurity.encrypt") as mock_encrypt:
            mock_encrypt.return_value = "Encrypted"
            with patch("backend.services.event_bus.event_bus.emit", new_callable=AsyncMock) as mock_emit:
                res = await self.controller.send_manual_message(self.mock_db, session_id, payload)
                
                self.assertEqual(res.content, "Hello from admin")
                self.assertEqual(res.role, "assistant")
                self.assertEqual(res.intent, "MANUAL")
                mock_emit.assert_called_with("SUPPORT_INBOX_UPDATE", {
                    "session_id": session_id,
                    "message": payload.message,
                    "role": "assistant"
                })

    async def test_admin_revoke_message(self):
        """Test toggling the revocation status of a message."""
        session_id = "sess_1"
        message_id = "msg_123"
        
        mock_msg = MagicMock()
        mock_msg.id = message_id
        mock_msg.is_revoked = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_msg
        self.mock_db.execute.return_value = mock_result

        with patch("backend.services.event_bus.event_bus.emit", new_callable=AsyncMock) as mock_emit:
            # Revoke
            res = await self.controller.revoke_message(self.mock_db, session_id, message_id)
            self.assertTrue(res["is_revoked"])
            self.assertTrue(mock_msg.is_revoked)
            
            # Pulse check
            mock_emit.assert_called_with("SUPPORT_INBOX_UPDATE", {
                "session_id": session_id,
                "message_id": message_id,
                "is_revoked": True
            })
            
            # Un-revoke (mocking retrieval again)
            mock_result.scalar_one_or_none.return_value = mock_msg
            res2 = await self.controller.revoke_message(self.mock_db, session_id, message_id)
            self.assertFalse(res2["is_revoked"])
            self.assertFalse(mock_msg.is_revoked)

if __name__ == "__main__":
    unittest.main()
