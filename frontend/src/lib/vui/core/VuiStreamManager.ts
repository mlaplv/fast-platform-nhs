import { vuiState } from "../store/vui.state.svelte";
import { vuiService } from "./VuiService";
import { nanobot } from "$lib/state/nanobot.svelte";
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
    // V76: Reduced log noise in production
    if (import.meta.env.DEV) console.debug(`[VUI] WS Incoming:`, data);
    const text = (data?.text || data?.transcript || "").trim();
    if (data?.tier) vuiState.setActiveTier(data.tier);

    // Phase 43: Emotional Live Streaming - Show progress but smooth the friction
    const isFinal = data?.is_final || data?.event?.includes("final");
    
    // Phase 44: Echo Shield - Filter out system instructions leaking from Whisper
    const isEcho = VUI_CONFIG.NEURAL.ECHO_FILTERS.some(f => text.includes(f));
    if (hasSpoken && isEcho) {
       console.warn("[VUI] Prompt Echo suppressed:", text);
       if (isFinal) { this.callbacks.interruptAll(); return; }
       return;
    }
    
    if (text.length > 0) {
      const currentLive = vuiState.liveText;
      // Phase 16: Hybrid Priority
      // If we get text from WS (Groq), it's likely more accurate.
      // We only update if it's different OR if it's the final verdict.
      if (isFinal || text !== currentLive) {
        // Optimization: If the new text is shorter than currentLive (and not final),
        // it might be a partial Groq result catching up. We only overwrite if it's "significant".
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
    
    // Phase 82.2: De-duplication Shield
    // If text is like "A A" or "A. A.", common in Whisper glitches
    let cleanedText = text;
    const mid = Math.floor(text.length / 2);
    const firstHalf = text.substring(0, mid).trim();
    const secondHalf = text.substring(mid).trim();
    if (firstHalf === secondHalf && firstHalf.length > 5) {
      console.warn("[VUI] De-duplication triggered:", text, "->", firstHalf);
      cleanedText = firstHalf;
    }

    if (!hasSpoken || cleanedText.trim().length < 1) {
      // If VAD hasn't detected speech or text is empty, ignore it but don't close.
      // E.g., Whisper hallucinates "..." on mic open noise.
      return;
    }

    // Ignore hallucinated dot-only sequences entirely even after speech
    if (cleanedText.replace(/\./g, "").trim().length === 0) {
      console.warn("[VUI] Dropped hallucinated dots:", cleanedText);
      return;
    }

    this.clearSttGuard();
    this.callbacks.stopRecording();
    
    vuiState.setTranscript(cleanedText);
    vuiState.setPhase("thinking");
    vuiState.setLiveText(cleanedText);
    
    try {
      await this.streamLLM(cleanedText, nanobot.currentData?.session_id || "");
    } finally {
      this.isProcessingFinal = false;
    }
  }

  public async streamLLM(query: string, session_id: string, source: "text" | "voice" = "voice", intentData?: Record<string, unknown>) {
    vuiState.setPhase("thinking");
    // Leave the STT text as liveText so the user can read it.
    // vuiState.setLiveText("");
    vuiState.setSystemMessage(""); // Clear previous AI text
    this.lastActionType = "";
    let txtResult = "";
    let lastData: IntentStreamEvent | null = null;
    let receivedAny = false;

    // Phase 76.3.4: Throttled State Updates (Sub-100ms batching)
    let lastUpdateAt = 0;
    const UPDATE_THRESHOLD_MS = 64; // ~15fps for text deltas to save CPU on 2GB RAM devices

    try {
      const stream = vuiService.streamIntent(query, session_id, source, nanobot.screenContext as Record<string, unknown>, intentData);

      for await (const parsed of stream) {
        receivedAny = true;
        this.clearSttGuard();
        if (parsed.router_tier) vuiState.setActiveTier(parsed.router_tier.toUpperCase());

        if (parsed.phase === "transcript" && parsed.text) {
          // Phase 76.3.2: Immediate Feedback from Backend
          vuiState.setLiveText(parsed.text);
          vuiState.setTranscript(parsed.text);
        } else if (parsed.phase === "text_delta" && parsed.text) {
          txtResult += parsed.text;

          if (source === "voice") {
            vuiState.setPhase("speaking");
            this.audio.processChunk(parsed.text);
          }

          // Throttle UI updates for systemMessage
          const now = Date.now();
          if (now - lastUpdateAt > UPDATE_THRESHOLD_MS) {
            vuiState.setSystemMessage(txtResult);
            lastUpdateAt = now;
          }
        } else if (parsed.phase === "done") {
          lastData = parsed;
          if (parsed.ui_action) this.lastActionType = parsed.ui_action;

          // Phase 76.3: Hardware Signal Listener (Aligned with Orchestrator)
          const isSleep = (parsed.category === "SESSION_CTRL" && (parsed.type === "SLEEP" || parsed.action === "HARDWARE_SLEEP"));
          if (isSleep) {
             console.warn("[VUI] Hardware SLEEP signal received.");
             nanobot.voice.hard_sleep();
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

      const dataPkg = { ...lastData?.data, session_id: lastData?.session_id || lastData?.data?.session_id || "" };
      if (dataPkg.category === "CONTENT_CREATE") {
        vuiState.setIsWaitingForAction(true);
      }
      
      // Phase 63: Selective Pop-up for Chat
      const isCreationTask = dataPkg.category === "CONTENT_CREATE" || 
                            lastData?.action === "CONTENT_CREATE" ||
                            this.lastActionType === "CONTENT_CREATE";

      const shouldPopUp = source === "voice" || 
                         isCreationTask || 
                         this.lastActionType !== "";
      
      if (shouldPopUp && source === "text") {
        console.debug("[VUI] Intent-based pop-up triggered for source=text");
        nanobot.setVuiActive(true);
        vuiState.setActive(true);
      }

      nanobot.setVoiceResult(query, finalMsg, this.lastActionType, dataPkg, source, lastData?.router_tier);

      if (source === "text") {
        // Phase 82: Graceful transition - give modal time to mount/animate
        setTimeout(() => {
          vuiState.setPhase("idle");
          vuiState.setLiveText("");
        }, 300);
        return;
      }

      // Phase 57: Ensure voice responses are spoken even if no streaming deltas came
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
