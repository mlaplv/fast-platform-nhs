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
    try {
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
                // Phase 22.1: Ignore comments and empty lines
                if (!trimmedLine || trimmedLine.startsWith(":")) continue;

                if (trimmedLine.startsWith("data:")) {
                  const jsonStr = trimmedLine.substring(5).trim();
                  if (!jsonStr) continue;
                  try {
                    const event = JSON.parse(jsonStr);
                    // R04: Ignore sync events in UI but keep connection alive
                    if (event.phase === "sync") continue;
                    yield event;
                  } catch (e) {
                    console.warn("[VuiService] JSON Parse Error", jsonStr);
                  }
                }
              }
            }
          } catch (e) {
            const err = e instanceof Error ? e : new Error(String(e));
            // R02: Silent Protocol Recovery for HTTP/2 issues
            if (err.name === 'AbortError' || err.message?.includes('network error')) {
                console.debug("[VUI] Connection closed normally by browser/proxy.");
                return;
            }
            console.error("[VUI] Stream Read Error:", err);
            yield { phase: "error", message: "Kết nối gián đoạn, Sếp thử lại nhé." };
          } finally {
            reader.releaseLock();
            await reader.cancel().catch(() => {});
          }
    } catch (e) {
      console.error("[VUI] Network Error:", e);
      yield { phase: "error", message: "Lỗi mạng hoặc máy chủ bận, Sếp thử lại nhé." };
    }
  }

  /**
   * Bước 3: Lấy Audio Blob từ TTS Engine
   */
  async fetchTtsBlob(text: string, signal?: AbortSignal): Promise<Blob> {
    const res = await fetch(VUI_CONFIG.ENDPOINTS.TTS_STREAM, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal
    });
    if (!res.ok) throw new Error("TTS Engine fail");
    return res.blob();
  }
}

export const vuiService = new VuiService();
