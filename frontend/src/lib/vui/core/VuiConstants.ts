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

  // Silero VAD (Neural Voice Activity Detection)
  VAD: {
    THRESHOLD: 0.5,              // Xác suất tối thiểu để xác nhận tiếng người (0.0 - 1.0)
    MIN_SPEECH_MS: 250,          // Thời gian nói tối thiểu (ms) để xác nhận "đang nói"
    REDEMPTION_MS: 600,          // Thời gian im lặng (ms) trước khi kết luận "ngừng nói"
    PRE_SPEECH_PAD_MS: 100,      // Thời gian đệm (ms) phía trước giọng nói
    INITIAL_TIMEOUT_MS: 5000,    // V87.0 Tuning: Chờ 5s thăng hoa (Sếp gợi ý 3-5s)
    STT_GUARD_TIMEOUT_MS: 15000, // Safety: Timeout nếu STT không trả kết quả
    MAX_RECORDING_DURATION_MS: 30000, // Nâng lên 30s vì VAD đã lọc sạch tiếng ồn
  },

  // Microphone
  MIC: {
    CHUNK_DURATION_MS: 500,
  },

  // LLM / STT
  NEURAL: {
    ECHO_FILTERS: ["ngữ cảnh quản trị", "SmartShop", "chuỗi rỗng"],
    FALLBACK_ERROR_VOICE: "Dạ vâng Sếp, đường truyền đang gặp sự cố, em xin lỗi Sếp và đã khởi động lại hệ thống ạ.",
  },

  // UI / UX
  ANIMATION: {
    TYPEWRITER_SPEED: 5,
  },
  UX: {
    CONTINUOUS_CONVERSATION: true,
    POST_SPEECH_DELAY_MS: 1000, // V87.0: Nghỉ 1s cho sếp "thở" trước khi nghe tiếp
    POST_ACTION_DELAY_MS: 100, // C.T.O Fix: Chuyển trang/Thực thi lệnh tức thời 
    ACTION_WAIT_TIMEOUT_MS: 1000, 
    POLITE_FALLBACK: "Dạ vâng Sếp, em đã sẵn sàng thưa Sếp.",
    PHASE_LABELS: {
      listening: "Start talking",
      thinking: "Đang xử lý...",
      executing: "Đang thực thi...",
      speaking: "",
      idle: "",
    },
    THEME: {
      USER_BUBBLE_BG: "#2F2F2F",
      USER_BUBBLE_TEXT: "rgba(255, 255, 255, 0.9)",
      AI_TEXT_COLOR: "rgba(255, 255, 255, 0.95)",
      ACTION_ICON_OPACITY_HISTORY: "0.3",
      ACTION_ICON_OPACITY_ACTIVE: "0.4",
      MAX_WIDTH: "1024px", // max-w-5xl
      HISTORY_SPACING: "4rem", // space-y-16
    }
  }
};
