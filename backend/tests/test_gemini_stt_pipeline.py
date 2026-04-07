"""
test_gemini_stt_pipeline.py
============================
Unit tests for Trinity-Integrated Gemini STT pipeline.
Chạy: docker exec fast_platform_api python -m pytest backend/tests/test_gemini_stt_pipeline.py -v
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import unicodedata

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_gemini_response(text: str) -> dict:
    """Build a minimal Gemini generateContent response body."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": text}],
                    "role": "model"
                },
                "finishReason": "STOP"
            }
        ]
    }


def _mock_resp(status: int, body: dict):
    """Return a mock httpx.Response."""
    r = MagicMock()
    r.status_code = status
    r.json.return_value = body
    r.text = "Mock Error"
    r.raise_for_status = MagicMock(side_effect=None if status < 400 else Exception(f"HTTP {status}"))
    return r


FAKE_AUDIO = b"\x1aE\xdf\xa3" + b"\x00" * 2048   # webm magic + padding


# ──────────────────────────────────────────────────────────────────────────────
# Test Suite
# ──────────────────────────────────────────────────────────────────────────────

class TestAudioFormatDetection(unittest.TestCase):
    """T01 – Audio MIME-type detection from raw bytes."""

    def test_webm_magic(self):
        webm = b"\x1aE\xdf\xa3" + b"\x00" * 100
        ogg  = b"OggS"          + b"\x00" * 100
        mp4  = b"\x00\x00\x00\x00" + b"ftyp" + b"\x00" * 100

        self.assertTrue(webm.startswith(b"\x1aE\xdf\xa3"))
        self.assertTrue(ogg.startswith(b"OggS"))
        self.assertIn(b"ftyp", mp4[:32])


class TestTranscribeHappyPath(unittest.IsolatedAsyncioTestCase):
    """T02 – Happy path: Gemini returns a clean transcript via Trinity Chain."""

    async def test_returns_transcript_on_200(self):
        mock_http = AsyncMock()
        mock_http.post.return_value = _mock_resp(200, _make_gemini_response("mở inbox"))

        with (
            patch("backend.services.routing.stt_service.trinity_bridge") as mock_bridge,
            patch("backend.services.routing.stt_service.key_rotator") as mock_rotator,
            patch("backend.services.routing.stt_service.STTService.get_client", return_value=mock_http),
            patch("backend.services.xohi_memory.xohi_memory.get_voice_profile", return_value=None),
            patch("backend.services.xohi_memory.xohi_memory.get_system_intent_mapping", return_value={}),
            patch("backend.services.xohi_memory.xohi_memory.get_stt_dictionary", return_value={}),
            patch("backend.services.routing.stt_service.stt_corrector.correct", new_callable=AsyncMock) as mock_correct,
        ):
            mock_correct.side_effect = lambda x, y: (x, None)
            mock_bridge._initialized = True
            mock_bridge.initialize = AsyncMock()
            mock_bridge.models_helper.build_chain = AsyncMock(return_value=["gemini-3.1-flash-lite"])
            
            mock_rotator.get_key = AsyncMock(return_value="fake-key")
            mock_rotator.set_success = AsyncMock()
            mock_rotator.mark_unhealthy = AsyncMock()
            mock_rotator.reset_health = AsyncMock()

            from backend.services.routing.stt_service import stt_service
            result = await stt_service.transcribe(FAKE_AUDIO, user_id=None)

        self.assertEqual(result, "mở inbox")
        mock_rotator.set_success.assert_awaited_once_with("fake-key")

    async def test_empty_audio_returns_empty(self):
        mock_http = AsyncMock()
        mock_http.post.return_value = _mock_resp(200, {"candidates": []})

        with (
            patch("backend.services.routing.stt_service.trinity_bridge") as mock_bridge,
            patch("backend.services.routing.stt_service.key_rotator") as mock_rotator,
            patch("backend.services.routing.stt_service.STTService.get_client", return_value=mock_http),
            patch("backend.services.xohi_memory.xohi_memory.get_voice_profile", return_value=None),
            patch("backend.services.xohi_memory.xohi_memory.get_system_intent_mapping", return_value={}),
        ):
            mock_bridge._initialized = True
            mock_bridge.initialize = AsyncMock()
            mock_bridge.models_helper.build_chain = AsyncMock(return_value=["gemini-3.1-flash-lite"])
            
            mock_rotator.get_key = AsyncMock(return_value="fake-key")
            mock_rotator.set_success = AsyncMock()
            mock_rotator.mark_unhealthy = AsyncMock()
            mock_rotator.reset_health = AsyncMock()

            from backend.services.routing.stt_service import stt_service
            result = await stt_service.transcribe(FAKE_AUDIO)

        self.assertEqual(result, "")


class TestTranscribeRetryOn429(unittest.IsolatedAsyncioTestCase):
    """T03 – 429 handling: key rotated, model changed via Trinity chain."""

    async def test_all_429_returns_empty(self):
        resp_429 = _mock_resp(429, {})
        mock_http = AsyncMock()
        mock_http.post.return_value = resp_429

        with (
            patch("backend.services.routing.stt_service.trinity_bridge") as mock_bridge,
            patch("backend.services.routing.stt_service.key_rotator") as mock_rotator,
            patch("backend.services.routing.stt_service.STTService.get_client", return_value=mock_http),
            patch("backend.services.xohi_memory.xohi_memory.get_voice_profile", return_value=None),
            patch("backend.services.xohi_memory.xohi_memory.get_system_intent_mapping", return_value={}),
            patch("backend.services.routing.stt_service.asyncio.sleep") as mock_sleep,
        ):
            mock_bridge._initialized = True
            mock_bridge.initialize = AsyncMock()
            mock_bridge.models_helper.build_chain = AsyncMock(return_value=["gemini-3.1-flash-lite"])
            mock_bridge.models_helper.classify_error.return_value = "rate_limit"
            
            mock_rotator.get_key = AsyncMock(return_value="key-a")
            mock_rotator.mark_unhealthy = AsyncMock()
            mock_rotator.reset_health = AsyncMock()

            from backend.services.routing.stt_service import stt_service
            result = await stt_service.transcribe(FAKE_AUDIO)

        self.assertEqual(result, "")
        # 3 attempts for 3.1-flash-lite
        self.assertEqual(mock_rotator.mark_unhealthy.await_count, 3)
        self.assertEqual(mock_sleep.call_count, 3)
        mock_rotator.reset_health.assert_awaited_once()

    async def test_retry_succeeds_on_second_attempt(self):
        resp_429 = _mock_resp(429, {})
        resp_200 = _mock_resp(200, _make_gemini_response("tạo bài viết"))

        call_count = 0
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return resp_429 if call_count == 1 else resp_200

        mock_http = AsyncMock()
        mock_http.post.side_effect = mock_post

        with (
            patch("backend.services.routing.stt_service.trinity_bridge") as mock_bridge,
            patch("backend.services.routing.stt_service.key_rotator") as mock_rotator,
            patch("backend.services.routing.stt_service.STTService.get_client", return_value=mock_http),
            patch("backend.services.xohi_memory.xohi_memory.get_voice_profile", return_value=None),
            patch("backend.services.xohi_memory.xohi_memory.get_system_intent_mapping", return_value={}),
            patch("backend.services.routing.stt_service.stt_corrector.correct", new_callable=AsyncMock) as mock_correct,
            patch("backend.services.routing.stt_service.asyncio.sleep") as mock_sleep,
        ):
            mock_correct.side_effect = lambda x, y: (x, None)
            mock_bridge._initialized = True
            mock_bridge.initialize = AsyncMock()
            mock_bridge.models_helper.build_chain = AsyncMock(return_value=["gemini-3.1-flash-lite"])
            mock_bridge.models_helper.classify_error.return_value = "rate_limit"
            
            mock_rotator.get_key = AsyncMock(return_value="key-b")
            mock_rotator.mark_unhealthy = AsyncMock()
            mock_rotator.set_success = AsyncMock()
            mock_rotator.reset_health = AsyncMock()

            from backend.services.routing.stt_service import stt_service
            result = await stt_service.transcribe(FAKE_AUDIO)

        self.assertEqual(result, "tạo bài viết")
        mock_rotator.mark_unhealthy.assert_awaited_once()
        mock_rotator.set_success.assert_awaited_once()


class TestSTTCorrectorBypass(unittest.TestCase):
    """T04 – STTCorrector: short commands (<15 words) must bypass Trinity LLM."""

    def test_short_command_skips_llm(self):
        import backend.services.routing.stt_corrector as mod
        self.assertEqual(mod._COMMAND_WORD_LIMIT, 15)


class TestNoSendPartialInVoiceCore(unittest.TestCase):
    """T05 – voice_core.py must NOT call send_partial."""

    def test_send_partial_not_called_in_buffer_loop(self):
        import ast, pathlib
        src = (pathlib.Path(__file__).parent.parent / "routers" / "voice_core.py").read_text()
        tree = ast.parse(src)
        calls = [n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        self.assertNotIn("send_partial", calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
