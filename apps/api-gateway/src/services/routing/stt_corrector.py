import os
import asyncio
import logging
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict
from src.utils.text import normalize_vn
from pydantic import BaseModel, Field
from litellm import RateLimitError, AuthenticationError, ServiceUnavailableError, Timeout as LiteLLMTimeout, NotFoundError
from ai_engine.core.key_rotator import SmartKeyRotator
import unicodedata
from rapidfuzz import fuzz

logger = logging.getLogger("api-gateway")

@dataclass
class STTCorrectorDeps:
    """Dependencies for STT Corrector."""
    user_dictionary: Dict[str, str] = field(default_factory=dict)

class STTCorrectionOutput(BaseModel):
    cleaned_text: str = Field(description="The corrected transcript. If no correction is needed, return the original.")
    suspected_correction: Optional[Dict[str, str]] = Field(
        default=None, 
        description="If you made a correction that is NOT in the user's dictionary and you are not 100% sure, return the mapping of {wrong_word: right_word}."
    )

# We are using an extremely focused prompt.
# It MUST NOT answer the user's question. 
# It ONLY corrects the vocabulary based on the context of an e-commerce admin system.
STT_CORRECTOR_PROMPT = """[ROLE] STT PRE-PROCESSOR (Hệ thống E-commerce Admin)
Nhiệm vụ của bạn là nhận một câu văn bản (transcript) được chuyển từ giọng nói (Speech-to-Text), 
phát hiện và sửa lỗi chính tả/từ vựng do quá trình nhận diện giọng nói gây ra, 
MÀ KHÔNG thay đổi ý nghĩa hay trả lời câu hỏi đó.

[NGỮ CẢNH HỆ THỐNG]
Người dùng là một "Sếp" (Quản trị viên) đang dùng giọng nói để ra lệnh cho hệ thống quản lý bán hàng (SmartShop). 
Các khái niệm có trong hệ thống:
- Doanh thu, doanh số, tiền, thu nhập
- Đơn hàng, bill, hóa đơn
- Sản phẩm, hàng hóa, tồn kho, kho
- Khách hàng, người dùng, user, nhân viên, tài khoản
- Bài viết, tin tức, danh mục

[QUY TẮC CỐT LÕI]
1. NHẬN DIỆN LỖI PHÁT ÂM: STT Tiếng Việt hay sai những từ nghe giống nhau.
   Ví dụ: 
   - "dân số", "nhân số" -> sửa thành "doanh số"
   - "giang sách xăng phẩm" -> sửa thành "danh sách sản phẩm"
   - "đau hàng" -> sửa thành "đơn hàng"
   - "báo cáo danh tu" -> sửa thành "báo cáo doanh thu"
   
2. CHỈ SỬA LỖI, KHÔNG TRẢ LỜI: Nếu input là "doanh số tháng này bao nhiêu", output CHỈ LÀ "doanh số tháng này bao nhiêu". Không được thêm câu trả lời (kiểu "Doanh số là 10 triệu").

3. GIỮ NGUYÊN NẾU KHÔNG CÓ LỖI: Nếu câu nghe có vẻ đã đúng chuyên ngành, xuất lại y nguyên.

5. TỪ ĐIỂN MẶC ĐỊNH TRANH CÃI (THƯỜNG NHẦM): 
   - "dân số" -> LUÔN sửa thành "doanh số" (Đây là hệ thống bán lẻ, không có dân số).
   - "doanh tu" -> LUÔN sửa thành "doanh thu".

6. NẾU BẠN SỬA MỘT TỪ, và từ đó KHÔNG CÓ TRONG [USER_DICTIONARY_CONTEXT], hãy điền cặp từ đó vào trường `suspected_correction` để hệ thống hỏi lại người dùng.

7. TRẢ VỀ JSON: Kết quả bắt buộc dưới định dạng JSON theo schema đã chỉ định.
"""

class STTCorrector:
    """
    Intelligent layer that runs BEFORE router.
    Cleans transcript using LLM to fix Vietnamese homophone/STT issues (e.g. "nhân số" -> "doanh số").
    """
    def __init__(self):
        import json as _json
        # Kill GOOGLE_API_KEY immediately — LiteLLM prefers it over GEMINI_API_KEY
        # but the .env GOOGLE_API_KEY is stale/broken (403). Must pop BEFORE Agent init.
        os.environ.pop("GOOGLE_API_KEY", None)
        # Always prioritize fastest/cheapest model for pre-processing.
        self.primary_model = os.getenv("TIER2_MODEL", "gemini-2.5-flash")
        self.fallback_model = os.getenv("TIER2_FALLBACK_MODEL", "gemini-2.5-flash")
        self.rotator = SmartKeyRotator()
        
        self.agent = Agent(
            deps_type=STTCorrectorDeps,
            output_type=STTCorrectionOutput,
            system_prompt=STT_CORRECTOR_PROMPT
        )
        
        # Register dynamic prompt AFTER agent is created
        @self.agent.system_prompt
        def inject_user_dict(ctx: RunContext[STTCorrectorDeps]) -> str:
            if ctx.deps.user_dictionary:
                return f"\n[USER_DICTIONARY_CONTEXT]\n{_json.dumps(ctx.deps.user_dictionary, ensure_ascii=False)}"
            return "\n[USER_DICTIONARY_CONTEXT]\n{}"

    async def correct(self, transcript: str, user_dictionary: Optional[Dict[str, str]] = None) -> Tuple[str, Optional[Dict[str, str]]]:
        """
        Takes raw STT transcript, returns (cleaned transcript, suspected_corrections).
        Optimized flow: Local Memory -> Global Patterns -> Clear Check -> LLM Fallback.
        """
        # 0. NORMALIZE (NFC for Vietnamese consistency)
        transcript = unicodedata.normalize('NFC', transcript.strip())
        norm_trans = transcript.lower()
        if not norm_trans:
            return "", None

        # Inject system overrides first to avoid LLM trip for known bad words
        # CTO Point: These are system-wide defaults, user-dictionary can override.
        system_overrides = {
            "dân số": "doanh số",
            "nhân số": "doanh số",
            "dan so": "doanh so",
            "nhan so": "doanh so",
            "doanh tu": "doanh thu",
            "doanh tuu": "doanh thu",
            "zanh sach": "danh sach",
            "danh sách": "danh sách",
            "săng phẩm": "sản phẩm",
            "đau hàng": "đơn hàng"
        }
        effective_dict = {**system_overrides, **(user_dictionary or {})}

        # 1. SEMANTIC BYPASS (LOCAL-FIRST) (Sub-5ms)
        # Check learned vocabulary first. If 'dân số' -> 'doanh số' is in memory, fix it now.
        local_cleaned, score = self.local_correct(transcript, effective_dict)
        if score >= 90:
            logger.debug(f"[STT Corrector] Local Memory HIT (score={score:.1f}): '{local_cleaned}'")
            # Continue to check patterns with the CLEANED text
            transcript = local_cleaned
            norm_trans = transcript.lower()

        # 2. GLOBAL PATTERN BYPASS (Sub-1ms)
        # Common navigation / session commands that don't need AI.
        # CTO R2.1: Normalized-only patterns for simplicity
        NAV_PATTERNS = [
            "mo bieu do", "xem bieu do",
            "doanh so thang nay", "doanh thu hom nay", 
            "xem don hang", "danh sach san pham",
            "ok", "dung", "vang", "phai", "thoat", "cut", "chao xohi", "tam biet"
        ]
        
        normalized_query = normalize_vn(transcript)
        
        if normalized_query in NAV_PATTERNS or (len(normalized_query.split()) <= 2 and len(normalized_query) < 15):
            logger.debug(f"[STT Corrector] Pattern/Short Bypass HIT: '{transcript}'")
            return transcript, None

        # 3. CORE KEYWORD "CLEAR" CHECK (Sub-1ms)
        # If it contains core keywords and isn't caught by memory, it's likely already correct.
        CLEAR_KEYWORDS = ["doanh so", "doanh thu", "don hang", "san pham", "bieu do"]
        if any(kw in normalized_query for kw in CLEAR_KEYWORDS):
            logger.debug(f"[STT Corrector] Clear Check HIT: '{transcript}'")
            return transcript, None

        # 4. LLM FALLBACK (The expensive 2-4s path)
        all_keys = self.rotator.get_all_keys()
        max_tries = min(len(all_keys), 2)
        model_names = [self.primary_model, self.fallback_model]
        deps = STTCorrectorDeps(user_dictionary=user_dictionary or {})

        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider

        for model_name in model_names:
            for attempt in range(max_tries):
                api_key = self.rotator.get_next_key()
                # Local env update is fast
                os.environ["GEMINI_API_KEY"] = api_key
                os.environ.pop("GOOGLE_API_KEY", None)
                
                try:
                    provider = GoogleProvider(api_key=api_key)
                    model_instance = GoogleModel(model_name, provider=provider)
                    result = await self.agent.run(transcript, model=model_instance, deps=deps)
                    
                    logger.debug(f"[STT Corrector] Cleaned: '{transcript}' -> '{result.output.cleaned_text}' | Suspect: {result.output.suspected_correction}")
                    return result.output.cleaned_text, result.output.suspected_correction

                except (ServiceUnavailableError, RateLimitError, LiteLLMTimeout, AuthenticationError, NotFoundError) as e:
                    logger.warning(f"[STT Corrector] {model_name} attempt {attempt+1} failed ({type(e).__name__}). Rotating...")
                    if attempt < max_tries - 1:
                        await asyncio.sleep(0.3 * (attempt + 1))
                    continue
                except Exception as e:
                    logger.warning(f"[STT Corrector] Unexpected error: {e}. Returning raw.")
                    return transcript, None

        # Absolute Fallback: LLM completely dead, just return raw
        logger.warning(f"[STT Corrector] Exhausted keys/models. Falling back to raw STT: '{transcript}'")
        return transcript, None

# Provide singleton instance
    def local_correct(self, transcript: str, user_dict: Dict[str, str]) -> Tuple[str, float]:
        """
        Attempts to fix transcript using high-confidence fuzzy matching against learned vocabulary.
        Supports multi-word phrase matching via sliding window.
        Returns (output_text, max_confidence_score).
        """
        if not user_dict:
            return transcript, 0.0
            
        current_text = transcript
        max_score = 0.0
        
        # Sort keys by length (descending) to match longer phrases first
        sorted_keys = sorted(user_dict.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            # We use a sliding window approach for phrases
            key_word_count = len(key.split())
            transcript_words = current_text.split()
            
            for i in range(len(transcript_words) - key_word_count + 1):
                window = " ".join(transcript_words[i : i + key_word_count])
                # Normalize both for comparison
                norm_window = normalize_vn(window)
                norm_key = normalize_vn(key)
                
                score = fuzz.ratio(norm_window, norm_key)
                
                if score >= 90:
                    replacement = user_dict[key]
                    # Case-sensitive replace if possible, else just replace
                    current_text = current_text.replace(window, replacement)
                    max_score = max(max_score, score)
                    logger.debug(f"[STT Local] Match: '{window}' -> '{replacement}' (score={score:.1f})")
                    
        return current_text, max_score

stt_corrector = STTCorrector()
