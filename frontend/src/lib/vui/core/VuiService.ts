import { VUI_CONFIG } from "./VuiConstants";

/**
 * VUI NEURAL SERVICE 2026
 * Handles all networking logic for Intent processing, SSE Streaming, and TTS.
 * Decoupled from Orchestrator for architectural purity.
 */
export interface IntentStreamEvent {
  phase: "classify" | "guard" | "execute" | "text_delta" | "done" | "error" | "transcript";
  text?: string;
  message?: string;
  status?: string;
  session_id?: string;
  router_tier?: string;
  category?: string;
  type?: string;
  action?: string;
  ui_action?: string;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

export class VuiService {
  /**
   * Stream SSE nhận phản hồi đa tầng từ Intent gateway.
   */
  async *streamIntent(
    query: string,
    sessionId: string,
    modality: "voice" | "text" = "voice",
    screenContext?: Record<string, unknown>,
    intentData?: Record<string, unknown>
  ): AsyncGenerator<IntentStreamEvent> {
    const res = await fetch(VUI_CONFIG.ENDPOINTS.INTENT_STREAM, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        query, 
        session_id: sessionId, 
        modality, 
        screen_context: screenContext,
        intent_data: intentData
      })
    });

    if (!res.body) throw new Error("Stream body missing");
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith("data:")) {
            const jsonStr = trimmedLine.substring(5).trim();
            if (!jsonStr) continue;
            try {
              yield JSON.parse(jsonStr);
            } catch (e) {
              console.warn("[VuiService] JSON Parse Error", jsonStr);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Bước 3: Lấy Audio Blob từ TTS Engine
   */
  async fetchTtsBlob(text: string, signal?: AbortSignal): Promise<Blob> {
    const encoded = encodeURIComponent(text);
    const res = await fetch(`${VUI_CONFIG.ENDPOINTS.TTS_STREAM}?text=${encoded}`, { signal });
    if (!res.ok) throw new Error("TTS Engine fail");
    return res.blob();
  }
}

export const vuiService = new VuiService();
