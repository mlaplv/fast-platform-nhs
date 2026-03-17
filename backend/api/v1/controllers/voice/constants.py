# backend/api/v1/controllers/voice/constants.py
import os
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
WHISPER_MODEL = "groq/whisper-large-v3-turbo"

# Minimum audio size to avoid sending silence/noise (bytes)
MIN_AUDIO_BYTES = 1500
# Maximum buffer before force-transcribe (25MB Groq limit)
MAX_AUDIO_BYTES = 20_000_000

# Zero-Hallucination 2026: Blacklist for common Whisper phantoms in silence/noise
HALLUCINATION_BLACKLIST = [
    "cám ơn các bạn", "subscribe", "đăng ký kênh", "ghiền mì gõ",
    "chào các bạn", "phimmoichill", "website chính thức",
    "liên hệ với chúng tôi", "video", "youtube", "mọi người",
    "ủng hộ", "bình luận", "zalo", "facebook", "website", "chào mừng",
    "tập trung vào ngữ cảnh"
]

SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')
DOT_HALLUCINATION_RE = re.compile(r'^\.+$')
