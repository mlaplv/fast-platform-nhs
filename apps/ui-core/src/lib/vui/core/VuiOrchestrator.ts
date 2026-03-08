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
    this.ws.sendStopSignal();
    this.streamManager.startSttGuard();
    this.mic.stop();
    vuiState.setVolume(0);
  }

  interruptAll() {
    if (this.resumptionTimer) { clearTimeout(this.resumptionTimer); this.resumptionTimer = null; }
    if (this.silenceTimer) { clearTimeout(this.silenceTimer); this.silenceTimer = null; }
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

  setStopAfterSpeech(val: boolean) { this.stopAfterSpeech = val; }

  private onTTSFinished() {
    if (vuiState.isWaitingForAction) {
      this.mic.stop(); // Phase 61: Quiet mic but keep UI open
      vuiState.setPhase("idle");
      vuiState.setLiveText("Waiting for review...");
      return;
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
      this.interruptAll();
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
    if (!text) return;
    vuiState.setPhase("speaking");
    vuiState.setSystemMessage(text);
    await this.audio.speak(text);
    this.onTTSFinished();
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
