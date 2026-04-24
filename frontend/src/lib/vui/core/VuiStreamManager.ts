import { vuiState } from "../store/vui.state.svelte";
import { vuiService, type IntentStreamEvent } from "./VuiService";
import { getNanobot } from "$lib/state/nanobot.svelte";
const getBot = () => getNanobot();
import { VUI_CONFIG } from "./VuiConstants";
import type { VuiAudioEngine } from "./VuiAudioEngine";

interface VuiWsMessage {
  text?: string;
  transcript?: string;
  tier?: string;
  is_final?: boolean;
  event?: string;
}

/**
 * VuiStreamManager: Logic for LLM Streaming & STT Response Handling
 * COMPLIANCE: Rule 1.3 (< 300 LOC)
 */
export class VuiStreamManager {
  private sttGuardTimer: ReturnType<typeof setTimeout> | null = null;
  private lastActionType = "";
  private isProcessingFinal = false; // Phase 82: Race Condition Guard

  constructor(
    private audio: VuiAudioEngine,
    private callbacks: {
      interruptAll: () => void;
      stopRecording: () => void;
      onTTSFinished: () => void;
      speak: (text: string) => Promise<boolean>;
      hasSpoken: () => boolean;
    }
  ) {}

  public async handleWsMessage(data: VuiWsMessage) {
    const hasSpoken = this.callbacks.hasSpoken();
    if (import.meta.env.DEV) console.debug(`[VUI] WS Incoming:`, data);
    const text = (data?.text || data?.transcript || "").trim();
    if (data?.tier) vuiState.setActiveTier(data.tier);

    const isFinal = data?.is_final || data?.event?.includes("final");
    
    const isEcho = VUI_CONFIG.NEURAL.ECHO_FILTERS.some(f => text.includes(f));
    if (hasSpoken && isEcho) {
       console.warn("[VUI] Prompt Echo suppressed:", text);
       if (isFinal) { this.callbacks.interruptAll(); return; }
       return;
    }
    
    if (text.length > 0) {
      const currentLive = vuiState.liveText;
      if (isFinal || text !== currentLive) {
        if (isFinal || text.length >= currentLive.length || data?.tier === "NEURAL_SYNC") {
          vuiState.setLiveText(text, isFinal);
        }
      }
    } else if (!hasSpoken) {
      vuiState.setLiveText(""); 
    }

    if (!text || !isFinal) return;

    if (vuiState.transcript || this.isProcessingFinal) {
       console.warn("[VUI] Ignored duplicate final event (Processing in progress):", text);
       return;
    }

    this.isProcessingFinal = true;
    
    let cleanedText = text;
    const mid = Math.floor(text.length / 2);
    const firstHalf = text.substring(0, mid).trim();
    const secondHalf = text.substring(mid).trim();
    if (firstHalf === secondHalf && firstHalf.length > 5) {
      console.warn("[VUI] De-duplication triggered:", text, "->", firstHalf);
      cleanedText = firstHalf;
    }

    if (!hasSpoken || cleanedText.trim().length < 1) {
      this.isProcessingFinal = false;
      return;
    }

    if (cleanedText.replace(/\./g, "").trim().length === 0) {
      console.warn("[VUI] Dropped hallucinated dots:", cleanedText);
      this.isProcessingFinal = false;
      return;
    }

    this.clearSttGuard();
    this.callbacks.stopRecording();
    
    vuiState.setTranscript(cleanedText);
    vuiState.setPhase("thinking");
    vuiState.setLiveText(cleanedText);
    
    try {
      await this.streamLLM(cleanedText, getBot().currentData?.session_id || "");
    } finally {
      this.isProcessingFinal = false;
    }
  }

  public async streamLLM(query: string, session_id: string, source: "text" | "voice" = "voice", intentData?: Record<string, unknown>) {
    vuiState.setIsWaitingForAction(false);
    vuiState.setPhase("thinking");
    vuiState.setSystemMessage("");
    this.lastActionType = "";
    let txtResult = "";
    let lastData: IntentStreamEvent | null = null;
    let receivedAny = false;

    let lastUpdateAt = 0;

    try {
      const stream = vuiService.streamIntent(query, session_id, source, getBot().screenContext as Record<string, unknown>, intentData);

      for await (const parsed of stream) {
        receivedAny = true;
        this.clearSttGuard();
        if (parsed.router_tier) vuiState.setActiveTier(parsed.router_tier.toUpperCase());

        if (parsed.phase === "transcript" && parsed.text) {
          vuiState.setLiveText(parsed.text);
          vuiState.setTranscript(parsed.text);
        } else if (parsed.phase === "text_delta" && parsed.text) {
          txtResult += parsed.text;

          // Unified Chat: Cả voice và text đều set speaking để VoiceStatusCaption render live
          vuiState.setPhase("speaking");
          if (source === "voice") {
            this.audio.processChunk(parsed.text);
          }

          const now = Date.now();
          if (now - lastUpdateAt > 32) {
            vuiState.setSystemMessage(txtResult);
            lastUpdateAt = now;
          }
        } else if (parsed.phase === "done") {
          lastData = parsed;
          if (parsed.ui_action) this.lastActionType = parsed.ui_action;
          if (parsed.behavior) {
            vuiState.behavior = parsed.behavior;
            vuiState.requiresListening = parsed.behavior === 'listen';
          }
          if (parsed.requires_confirmation !== undefined) {
            vuiState.requiresConfirmation = parsed.requires_confirmation;
          }

          const isSleep = (parsed.category === "SESSION_CTRL" && (parsed.type === "SLEEP" || parsed.action === "HARDWARE_SLEEP"));
          if (isSleep) {
             console.warn("[VUI] Hardware SLEEP signal received.");
             getBot().voice.hard_sleep();
             return;
          }
        } else if (parsed.phase === "error") {
          throw new Error(parsed.message || "Neural Gateway Error");
        }
      }

      this.audio.flush();
      
      const finalMsg = lastData?.message || txtResult;
      vuiState.setSystemMessage(finalMsg);

      if (this.lastActionType) {
        vuiState.setPhase("executing");
        vuiState.setLiveText(`Action: ${this.lastActionType.toUpperCase().replace("_", " ")}`);
      }

      
      const isCreationTask = lastData?.category === "CONTENT_CREATE" || 
                            lastData?.action === "CONTENT_CREATE" ||
                            this.lastActionType === "CONTENT_CREATE";

      const shouldPopUp = source === "voice" || 
                         isCreationTask || 
                         this.lastActionType !== "";
      
      if (shouldPopUp && source === "text") {
        getBot().setVuiActive(true);
        vuiState.setActive(true);
      }

      getBot().setVoiceResult(query, finalMsg, this.lastActionType, lastData || {}, source, lastData?.router_tier);

      if (source === "text") {
        // Unified Chat: Finalize interaction để push vào history (phương án A: giữ modal mở)
        vuiState.finalizeInteraction();
        vuiState.setPhase("idle");
        vuiState.setLiveText("");
        return;
      }

      if (source === "voice" && finalMsg && !txtResult) {
        await this.callbacks.speak(finalMsg);
      } else if (!finalMsg && this.lastActionType) {
        await new Promise(r => setTimeout(r, VUI_CONFIG.UX.ACTION_WAIT_TIMEOUT_MS));
        await this.callbacks.speak(VUI_CONFIG.UX.POLITE_FALLBACK);
      } else if (!finalMsg) {
        if (!receivedAny) throw new Error("Stream Timeout/Empty");
        this.callbacks.onTTSFinished();
      }
    } catch (e: unknown) {
      console.error("[VUI] Stream Execution Error:", e);
      vuiState.setError("Neural Connection Stall");
      vuiState.setActiveTier("");
      this.audio.flush();
      await this.callbacks.speak(VUI_CONFIG.NEURAL.FALLBACK_ERROR_VOICE);
    }
  }

  public startSttGuard() {
    this.clearSttGuard();
    this.sttGuardTimer = setTimeout(() => {
      if (vuiState.phase === "thinking" && !vuiState.systemMessage) {
        vuiState.setError("AI Timeout");
        this.callbacks.interruptAll();
      }
    }, VUI_CONFIG.VAD.STT_GUARD_TIMEOUT_MS);
  }

  public clearSttGuard() {
    if (this.sttGuardTimer) { clearTimeout(this.sttGuardTimer); this.sttGuardTimer = null; }
  }

  public getLastAction() { return this.lastActionType; }
  public setLastAction(val: string) { this.lastActionType = val; }
}
