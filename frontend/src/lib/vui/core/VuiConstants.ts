/**
 * VUI NEURAL CONSTANTS 2026
 * Centralized configuration for all VUI parameters.
 */
export const VUI_CONFIG = {
  // API Endpoints
  ENDPOINTS: {
    STT_WS: "/ws/stt",
    INTENT: "/api/v1/intent",
    INTENT_STREAM: "/api/v1/intent/stream",
    TTS_STREAM: "/api/v1/tts/stream",
  },

  // Voice Activity Detection (VAD)
  VAD: {
    SILENCE_THRESHOLD: 0.015,   // Tăng từ 0.010 lên 0.015 để bớt nhạy cảm với tiếng ồn (Phase 61/71)
    SILENCE_DURATION_MS: 600,  // Giảm từ 800ms xuống 600ms để dứt khoát hơn (Phase 71)
    INITIAL_TIMEOUT_MS: 7000,  
    SPEECH_CONFIRM_MS: 100,    
    STT_GUARD_TIMEOUT_MS: 20000, 
    MAX_RECORDING_DURATION_MS: 15000, // Chốt chặn 15s tự động ngắt nếu quá ồn (Phase 71)
  },

  // Microphone
  MIC: {
    CHUNK_DURATION_MS: 500,
    BOOT_IGNORE_MS: 200, // Phase 56: Ignore initial pop
  },

  // LLM / STT
  NEURAL: {
    ECHO_FILTERS: ["ngữ cảnh quản trị", "SmartShop", "chuỗi rỗng"],
    STT_FEEDBACK_DOTS: "...",
    FALLBACK_ERROR_VOICE: "Dạ vâng Sếp, đường truyền đang gặp sự cố, em xin lỗi Sếp và đã khởi động lại hệ thống ạ.",
  },

  // UI / UX
  ANIMATION: {
    TYPEWRITER_SPEED: 45,
  },
  UX: {
    CONTINUOUS_CONVERSATION: true,
    POST_SPEECH_DELAY_MS: 800, 
    POST_ACTION_DELAY_MS: 2500, 
    ACTION_WAIT_TIMEOUT_MS: 1000, 
    POLITE_FALLBACK: "Dạ vâng Sếp, em đã sẵn sàng thưa Sếp.",
    PHASE_LABELS: {
      listening: "Đang lắng nghe...",
      thinking: "Đang xử lý...",
      executing: "Đang thực thi...",
      speaking: "Đang truyền đạt...",
      idle: "Neural Core Ready",
    }
  }
};
