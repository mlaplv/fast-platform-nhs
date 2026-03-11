import { vuiState } from "../store/vui.state.svelte";
import { MicrophoneEngine } from "./MicrophoneEngine";
import { WebSocketStream } from "./WebSocketStream";
import { VuiAudioEngine } from "./VuiAudioEngine";
import { VUI_CONFIG } from "./VuiConstants";
import { nanobot } from "$lib/state/nanobot.svelte";
import { VuiStreamManager } from "./VuiStreamManager";
import { VuiVadEngine } from "./VuiVadEngine";

/**
 * VuiOrchestrator 2026: The "Neural Conductor"
 * Orchestrates VAD Engine, Mic, WS Stream, Audio Engine, and Stream Manager.
 * Phase 15: Silero VAD Integration — Neural Voice Activity Detection.
 */
class VuiOrchestrator {
  private mic = new MicrophoneEngine();
  private ws = new WebSocketStream(VUI_CONFIG.ENDPOINTS.STT_WS);
  private audio = new VuiAudioEngine(() => this.onTTSFinished());
  private streamManager: VuiStreamManager;
  private vadEngine = new VuiVadEngine();
  
  private hasSpoken = false;
  private resumptionTimer: any = null;
  private stopAfterSpeech = false;
  private recordingMaxTimer: ReturnType<typeof setTimeout> | null = null;
  private initialTimeoutTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.streamManager = new VuiStreamManager(this.audio, {
      interruptAll: () => this.interruptAll(),
      stopRecording: () => this.stopRecording(),
      onTTSFinished: () => this.onTTSFinished(),
      speak: (text: string) => this.speak(text),
      hasSpoken: () => this.hasSpoken
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
    
    vuiState.setTranscript("");
    vuiState.setLiveText("");
    vuiState.setSystemMessage("");
    vuiState.setActiveTier("");
    vuiState.setPhase("listening");

    try {
      this.audio.playSystemSound('start');
      
      // Step 1: Connect WebSocket for STT streaming
      await this.ws.connect((data) => this.streamManager.handleWsMessage(data));
      
      // Step 2: Start MicrophoneEngine for sending WebM chunks to WS
      if (this.mic.isActive()) this.mic.stop();
      this.mic.start(VUI_CONFIG.MIC.CHUNK_DURATION_MS,
        (blob) => {
          if (vuiState.phase !== "listening") return;
          this.ws.sendBinary(blob);
        },
        (vol) => {
          // Volume is now ONLY used for UI animation, NOT for VAD
          vuiState.setVolume(vol);
        }
      );
      
      // Step 3: Start Silero VAD Engine (Neural Voice Detection)
      await this.vadEngine.start(
        // onSpeechStart: Neural network confirmed human voice
        () => {
          if (vuiState.phase !== "listening") return;
          this.hasSpoken = true;
          // Clear initial timeout — user is speaking
          if (this.initialTimeoutTimer) {
            clearTimeout(this.initialTimeoutTimer);
            this.initialTimeoutTimer = null;
          }
        },
        // onSpeechEnd: Neural network confirmed silence after speech
        (audioBlob) => {
          if (vuiState.phase !== "listening") return;
          if (this.hasSpoken) {
            console.log("[VuiOrchestrator] VAD: Speech ended. Auto-finalizing.");
            this.stopRecording();
          }
        },
        // onFrameProcessed: Per-frame probability for UI feedback
        (probability) => {
          // Can be used for advanced Orb/Mic UI animations
        }
      );

      // Step 4: Initial timeout — if no speech detected within 7s, clean exit
      this.initialTimeoutTimer = setTimeout(() => {
        if (vuiState.phase === "listening" && !this.hasSpoken) {
          console.log("[VuiOrchestrator] Initial timeout: No speech detected. Clean exit.");
          this.interruptAll();
        }
      }, VUI_CONFIG.VAD.INITIAL_TIMEOUT_MS);

      // Step 5: Hard safety limit for recording duration
      this.recordingMaxTimer = setTimeout(() => {
        if (vuiState.phase === "listening") {
           console.warn("[VuiOrchestrator] Recording exceeded MAX_DURATION. Auto-finalizing.");
           this.stopRecording();
        }
      }, VUI_CONFIG.VAD.MAX_RECORDING_DURATION_MS);
    } catch (e: any) {
      console.error("[VuiOrchestrator] MIC_START_FAIL:", e);
      vuiState.setError(e.message || "Lỗi truy cập Microphone");
      this.interruptAll();
    } finally {
      vuiState.setStartingLock(false);
    }
  }

  stopRecording() {
    if (vuiState.phase !== "listening") return;

    // ROOT FIX: If VAD never confirmed speech, there is nothing to transcribe.
    // Clean exit immediately — don't enter thinking phase or send STOP to WS.
    if (!this.hasSpoken) {
      this.interruptAll();
      return;
    }

    vuiState.setPhase("thinking");
    if (this.initialTimeoutTimer) { clearTimeout(this.initialTimeoutTimer); this.initialTimeoutTimer = null; }
    if (this.recordingMaxTimer) { clearTimeout(this.recordingMaxTimer); this.recordingMaxTimer = null; }
    this.ws.sendStopSignal();
    this.streamManager.startSttGuard();
    this.mic.stop();
    this.vadEngine.pause();
    this.audio.playSystemSound('stop');
    vuiState.setVolume(0);
    vuiState.setStartingLock(false);
  }

  interruptAll() {
    if (this.resumptionTimer) { clearTimeout(this.resumptionTimer); this.resumptionTimer = null; }
    if (this.initialTimeoutTimer) { clearTimeout(this.initialTimeoutTimer); this.initialTimeoutTimer = null; }
    if (this.recordingMaxTimer) { clearTimeout(this.recordingMaxTimer); this.recordingMaxTimer = null; }
    this.streamManager.clearSttGuard();
    this.audio.abort();
    this.mic.stop();
    this.vadEngine.stop();
    this.ws.disconnect();
    vuiState.reset();
    vuiState.setStartingLock(false);
    nanobot.setVuiActive(false);
    this.streamManager.setLastAction("");
  }

  /**
   * Surgical Interruption: Stop current reading/text but keep VUI modal active.
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
    this.vadEngine.pause();
    vuiState.setSystemMessage("");
    vuiState.setIsWaitingForAction(false);
    vuiState.setPhase("executing");
    vuiState.setLiveText("Hệ thống đang chuyển pha...");
    this.streamManager.setLastAction("");

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
      this.mic.stop();
      this.vadEngine.pause();
      vuiState.setPhase("idle");
      vuiState.setLiveText("Sẵn sàng thưa sếp...");
      return;
    }

    if (vuiState.phase === "executing" || vuiState.phase === "speaking") {
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
    this.mic.stop();
    this.vadEngine.pause();
    if (vuiState.phase === "listening") vuiState.setPhase("thinking");
    
    if (!text || !vuiState.isActive) return;
    if (vuiState.phase !== "executing") {
        vuiState.setPhase("speaking");
    }
    vuiState.setSystemMessage(text);
    
    const sentences = text.split(/([.?!]|\n)/);
    for (const s of sentences) {
      if (s.trim()) this.audio.processChunk(s);
    }
    this.audio.flush();
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
