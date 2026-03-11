import { vuiState } from "../store/vui.state.svelte";
import { vuiService } from "./VuiService";
import { nanobot } from "$lib/state/nanobot.svelte";
import { VUI_CONFIG } from "./VuiConstants";
import type { VuiAudioEngine } from "./VuiAudioEngine";

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
      speak: (text: string) => Promise<void>;
      hasSpoken: () => boolean;
    }
  ) {}

  public async handleWsMessage(data: any) {
    const hasSpoken = this.callbacks.hasSpoken();
    console.debug(`[VUI] WS Incoming:`, data);
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
      if (isFinal || text !== currentLive) {
        vuiState.setLiveText(text);
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

  public async streamLLM(query: string, session_id: string, source: "text" | "voice" = "voice") {
    vuiState.setPhase("thinking");
    // Leave the STT text as liveText so the user can read it.
    // vuiState.setLiveText(""); 
    vuiState.setSystemMessage(""); // Clear previous AI text
    this.lastActionType = ""; 
    let txtResult = "";
    let lastData = null;
    let receivedAny = false;

    try {
      const stream = vuiService.streamIntent(query, session_id, source, nanobot.screenContext);
      
      for await (const parsed of stream) {
        receivedAny = true;
        this.clearSttGuard();
        if (parsed.router_tier) vuiState.setActiveTier(parsed.router_tier.toUpperCase());

        if (parsed.phase === "text_delta" && parsed.text) {
          txtResult += parsed.text;
          vuiState.setSystemMessage(txtResult);
          if (source === "voice") {
            vuiState.setPhase("speaking");
            this.audio.processChunk(parsed.text);
          }
        } else if (parsed.phase === "done") {
          lastData = parsed;
          if (parsed.ui_action) this.lastActionType = parsed.ui_action;
          
          // Phase 6: Hardware Signal Listener for SLEEP
          if (parsed.category === "SESSION_CTRL" && parsed.type === "SLEEP") {
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
      
      nanobot.setVoiceResult(query, finalMsg, this.lastActionType, dataPkg, source, lastData?.router_tier);

      if (source === "text") {
        vuiState.setPhase("idle");
        vuiState.setLiveText("");
        return;
      }

      // Phase 57: Ensure voice responses are spoken even if no streaming deltas came
      if (finalMsg && !txtResult) {
        await this.callbacks.speak(finalMsg);
      } else if (!finalMsg && this.lastActionType) {
        await new Promise(r => setTimeout(r, VUI_CONFIG.UX.ACTION_WAIT_TIMEOUT_MS));
        await this.callbacks.speak(VUI_CONFIG.UX.POLITE_FALLBACK);
      } else if (!finalMsg) {
        if (!receivedAny) throw new Error("Stream Timeout/Empty");
        this.callbacks.onTTSFinished();
      }
    } catch (e: any) {
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
