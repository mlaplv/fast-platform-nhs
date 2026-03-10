import { vuiState } from "../store/vui.state.svelte";
import { MicrophoneEngine } from "./MicrophoneEngine";
import { WebSocketStream } from "./WebSocketStream";
import { VuiAudioEngine } from "./VuiAudioEngine";
import { VUI_CONFIG } from "./VuiConstants";
import { nanobot } from "$lib/state/nanobot.svelte";
import { VuiStreamManager } from "./VuiStreamManager";

/**
 * VuiOrchestrator 2026: The "Neural Conductor"
 * Orchestrates Mic, WS Stream, Audio Engine, and Stream Manager.
 * COMPLIANCE: Rule 1.3 (< 300 LOC).
 */
class VuiOrchestrator {
  private mic = new MicrophoneEngine();
  private ws = new WebSocketStream(VUI_CONFIG.ENDPOINTS.STT_WS);
  private audio = new VuiAudioEngine(() => this.onTTSFinished());
  private streamManager: VuiStreamManager;
  
  private silenceTimer: ReturnType<typeof setTimeout> | null = null;
  private hasSpoken = false;
  private sessionStartTime = 0;
  private resumptionTimer: any = null;
  private stopAfterSpeech = false;
  private recordingMaxTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.streamManager = new VuiStreamManager(this.audio, {
      interruptAll: () => this.interruptAll(),
      stopRecording: () => this.stopRecording(),
      onTTSFinished: () => this.onTTSFinished(),
      speak: (text: string) => this.speak(text)
    });
  }

  async startRecording(autoBypassAudio = true) {
    if (vuiState.isStarting || vuiState.phase === 'thinking') return;
    
    vuiState.setStartingLock(true);
    vuiState.setActive(true);
    nanobot.setVuiActive(true);
    
    if (autoBypassAudio) this.audio.abort();
    this.audio.reset();
    
    this.hasSpoken = false;
    this.streamManager.setLastAction("");
    this.sessionStartTime = Date.now();
    
    vuiState.setTranscript("");
    vuiState.setLiveText("");
    vuiState.setSystemMessage("");
    vuiState.setActiveTier("");
    vuiState.setPhase("listening");

    try {
      await this.ws.connect((data) => this.streamManager.handleWsMessage(data, this.hasSpoken));
      this.mic.start(VUI_CONFIG.MIC.CHUNK_DURATION_MS,
        (blob) => {
          if (vuiState.phase !== "listening") return;
          this.ws.sendBinary(blob);
          if (!this.hasSpoken) vuiState.setLiveText(VUI_CONFIG.NEURAL.STT_FEEDBACK_DOTS);
        },
        (vol) => {
          vuiState.setVolume(vol);
          this.handleSilenceDetection(vol);
        }
      );
      
      // Phase 71: Hard safety limit for recording duration
      this.recordingMaxTimer = setTimeout(() => {
        if (vuiState.phase === "listening") {
           console.warn("[VuiOrchestrator] Recording exceeded MAX_DURATION. Auto-finalizing.");
           this.stopRecording();
        }
      }, VUI_CONFIG.VAD.MAX_RECORDING_DURATION_MS);
    } catch (e: any) {
      vuiState.setError(e.message || "Lỗi truy cập Microphone");
      this.interruptAll();
    } finally {
      vuiState.setStartingLock(false);
    }
  }

  private handleSilenceDetection(volume: number) {
    if (vuiState.phase !== "listening") return;
    if (Date.now() - this.sessionStartTime < VUI_CONFIG.MIC.BOOT_IGNORE_MS) return;

    if (volume > VUI_CONFIG.VAD.SILENCE_THRESHOLD) {
      if (!this.hasSpoken) {
        this.hasSpoken = true;
        vuiState.setHasSpoken(true);
      }
      if (this.silenceTimer) { clearTimeout(this.silenceTimer); this.silenceTimer = null; }
    } else {
      if (!this.silenceTimer && !vuiState.isStarting) {
        const timeout = this.hasSpoken ? VUI_CONFIG.VAD.SILENCE_DURATION_MS : VUI_CONFIG.VAD.INITIAL_TIMEOUT_MS;
        if (timeout > 0) {
          this.silenceTimer = setTimeout(() => this.stopRecording(), timeout);
        }
      }
    }
  }

  stopRecording() {
    if (vuiState.phase !== "listening") return;
    vuiState.setPhase("thinking");
    if (this.silenceTimer) { clearTimeout(this.silenceTimer); this.silenceTimer = null; }
    if (this.recordingMaxTimer) { clearTimeout(this.recordingMaxTimer); this.recordingMaxTimer = null; }
    this.ws.sendStopSignal();
    this.streamManager.startSttGuard();
    this.mic.stop();
    vuiState.setVolume(0);
  }

  interruptAll() {
    if (this.resumptionTimer) { clearTimeout(this.resumptionTimer); this.resumptionTimer = null; }
    if (this.silenceTimer) { clearTimeout(this.silenceTimer); this.silenceTimer = null; }
    if (this.recordingMaxTimer) { clearTimeout(this.recordingMaxTimer); this.recordingMaxTimer = null; }
    this.streamManager.clearSttGuard();
    this.audio.abort();
    this.mic.stop();
    this.ws.disconnect();
    vuiState.setActive(false);
    vuiState.reset();
    vuiState.setStartingLock(false);
    nanobot.setVuiActive(false);
    this.streamManager.setLastAction("");
  }

  /**
   * Surgical Interruption: Stop current reading/text but keep VUI modal active.
   * Used during "Power Approval" to clear the stage for next phase.
   */
  private phaseResetTimer: any = null;

  resetToIdle() {
    if (this.phaseResetTimer) clearTimeout(this.phaseResetTimer);
    vuiState.setPhase("idle");
    vuiState.setLiveText("");
    vuiState.setSystemMessage("");
  }

  interruptSpeech() {
    this.audio.abort();
    if (this.resumptionTimer) { clearTimeout(this.resumptionTimer); this.resumptionTimer = null; }
    if (this.phaseResetTimer) { clearTimeout(this.phaseResetTimer); this.phaseResetTimer = null; }

    this.mic.stop();
    vuiState.setSystemMessage("");
    vuiState.setIsWaitingForAction(false);
    // Move to executing phase to show transition status
    vuiState.setPhase("executing");
    vuiState.setLiveText("Hệ thống đang chuyển pha...");
    this.streamManager.setLastAction("");

    // Rule R82.5: Safety Reset — If nothing happens in 30s, go back to idle
    this.phaseResetTimer = setTimeout(() => {
      if (vuiState.phase === "executing") {
        this.resetToIdle();
      }
    }, 30000);
  }

  setStopAfterSpeech(val: boolean) { this.stopAfterSpeech = val; }

  private onTTSFinished() {
    if (vuiState.isWaitingForAction) {
      if (import.meta.env.DEV) console.log("[VuiOrchestrator] TTS Finished. Waiting for user action, going idle.");
      this.mic.stop(); // Phase 61: Quiet mic but keep UI open
      vuiState.setPhase("idle");
      vuiState.setLiveText("Sẵn sàng thưa sếp...");
      return;
    }

    if (vuiState.phase === "executing" || vuiState.phase === "speaking") {
      // General actions or speech must not freeze VUI. Exiting to idle.
      if (import.meta.env.DEV) console.log(`[VuiOrchestrator] TTS Finished during ${vuiState.phase}. Clearing locks.`);
      vuiState.setPhase("idle");
      vuiState.setActiveTier("");
    }

    if (this.stopAfterSpeech) {
      this.stopAfterSpeech = false;
      this.interruptAll();
      return;
    }

    if (VUI_CONFIG.UX.CONTINUOUS_CONVERSATION && vuiState.isActive) {
      const delay = this.streamManager.getLastAction() ? VUI_CONFIG.UX.POST_ACTION_DELAY_MS : VUI_CONFIG.UX.POST_SPEECH_DELAY_MS;
      if (this.resumptionTimer) clearTimeout(this.resumptionTimer);
      this.resumptionTimer = setTimeout(() => {
        this.resumptionTimer = null;
        if (vuiState.isActive && nanobot.isVuiActive) {
          vuiState.setSystemMessage("");
          vuiState.setLiveText("");
          this.startRecording(false);
        } else {
          this.interruptAll();
        }
      }, delay);
    } else {
      setTimeout(() => this.interruptAll(), 1000);
    }
  }

  async execTextCmd(query: string, source: "text" | "voice" = "text") {
    if (!query) return;
    this.audio.abort();
    this.ws.disconnect();

    const isVoice = source === "voice";
    vuiState.setActive(isVoice);
    nanobot.setVuiActive(isVoice);
    
    vuiState.setPhase("thinking");
    vuiState.setTranscript(query);
    vuiState.setSystemMessage("");

    await this.streamManager.streamLLM(query, nanobot.currentData?.session_id || "", source);
  }

  async speak(text: string) {
    // Phase 6: Half-Duplex Enforcer (R4.1)
    this.mic.stop();
    if (vuiState.phase === "listening") vuiState.setPhase("thinking");
    
    if (!text || !vuiState.isActive) return;
    if (vuiState.phase !== "executing") {
        vuiState.setPhase("speaking");
    }
    vuiState.setSystemMessage(text);
    
    // Neural Streaming: Break down formal messages into chunks to bypass full-blob latency
    // This solves the "1/2 delay" by letting the AudioEngine queue smaller fragments
    const sentences = text.split(/([.?!]|\n)/);
    for (const s of sentences) {
      if (s.trim()) this.audio.processChunk(s);
    }
    this.audio.flush();
    // onTTSFinished is called by AudioEngine/TTSSpeaker when the queue clears
  }

  async processGhost(cmd: string, source: "text" | "voice" = "text"): Promise<boolean> {
    if (source === "voice" || source === "text") {
       await this.execTextCmd(cmd, source);
       return true; 
    }
    return false; 
  }
}

export const vuiController = new VuiOrchestrator();
