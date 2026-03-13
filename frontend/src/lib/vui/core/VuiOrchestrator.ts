import { vuiState } from "../store/vui.state.svelte";
import { MicrophoneEngine } from "./MicrophoneEngine";
import { WebSocketStream } from "./WebSocketStream";
import { VuiAudioEngine } from "./VuiAudioEngine";
import { VUI_CONFIG } from "./VuiConstants";
import { nanobot } from "$lib/state/nanobot.svelte";
import { VuiStreamManager } from "./VuiStreamManager";
import { VuiVadEngine } from "./VuiVadEngine";
import { isDev } from "$lib/state/nanobot/env";

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
  private stopAfterSpeech = false;
  
  // Phase 42: Neural Lifecycle Control (Premium Timer Management)
  private activeTimers = new Map<string, any>();

  private clearTimer(key: string) {
    if (this.activeTimers.has(key)) {
      clearTimeout(this.activeTimers.get(key));
      this.activeTimers.delete(key);
    }
  }

  private setManagedTimer(key: string, fn: () => void, ms: number) {
    this.clearTimer(key);
    this.activeTimers.set(key, setTimeout(() => {
      this.activeTimers.delete(key);
      fn();
    }, ms));
  }

  private clearAllTimers() {
    this.activeTimers.forEach(t => clearTimeout(t));
    this.activeTimers.clear();
  }

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
          this.clearTimer('initial');
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
      this.setManagedTimer('initial', () => {
        if (vuiState.phase === "listening" && !this.hasSpoken) {
          console.log("[VuiOrchestrator] Initial timeout: No speech detected. Clean exit.");
          this.interruptAll();
        }
      }, VUI_CONFIG.VAD.INITIAL_TIMEOUT_MS);

      // Step 5: Hard safety limit for recording duration
      this.setManagedTimer('max_duration', () => {
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
    this.clearTimer('initial');
    this.clearTimer('max_duration');
    
    this.ws.sendStopSignal();
    this.streamManager.startSttGuard();
    this.mic.stop();
    this.vadEngine.pause();
    this.audio.playSystemSound('stop');
    vuiState.setVolume(0);
    vuiState.setStartingLock(false);
  }

  interruptAll() {
    this.clearAllTimers();
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
    this.clearAllTimers();

    this.mic.stop();
    this.vadEngine.pause();
    vuiState.setSystemMessage("");
    vuiState.setIsWaitingForAction(false);
    vuiState.setPhase("executing");
    vuiState.setLiveText("Hệ thống đang chuyển pha...");
    this.streamManager.setLastAction("");

    this.setManagedTimer('phase_reset', () => {
      if (vuiState.phase === "executing") {
        this.resetToIdle();
      }
    }, 30000);
  }

  setStopAfterSpeech(val: boolean) { this.stopAfterSpeech = val; }

  private onTTSFinished() {
    if (vuiState.isWaitingForAction) {
      if (isDev()) console.log("[VuiOrchestrator] TTS Finished. Waiting for user action, going idle.");
      this.mic.stop();
      this.vadEngine.pause();
      vuiState.setPhase("idle");
      vuiState.setLiveText("Sẵn sàng thưa sếp...");
      return;
    }

    if (vuiState.phase === "executing" || vuiState.phase === "speaking") {
      if (isDev()) console.log(`[VuiOrchestrator] TTS Finished during ${vuiState.phase}. Clearing locks.`);
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
      this.setManagedTimer('resumption', () => {
        if (vuiState.isActive && nanobot.isVuiActive) {
          vuiState.setSystemMessage("");
          vuiState.setLiveText("");
          this.startRecording(false);
        } else {
          this.interruptAll();
        }
      }, delay);
    } else {
      this.setManagedTimer('interrupt', () => this.interruptAll(), 1000);
    }
  }

  async execTextCmd(query: string, source: "text" | "voice" = "text") {
    if (!query) return;
    this.audio.abort();
    this.ws.disconnect();

    // Unified VUI: Always active for both voice and text sources
    vuiState.setActive(true);
    nanobot.setVuiActive(true);
    
    vuiState.setPhase("thinking");
    vuiState.setTranscript(query);
    vuiState.setLiveText(query); // Ensure query is visible in VUI modal
    vuiState.setSystemMessage("");

    await this.streamManager.streamLLM(query, nanobot.currentData?.session_id || "", source);
  }

  async speak(text: string): Promise<boolean> {
    this.mic.stop();
    this.vadEngine.pause();
    if (vuiState.phase === "listening") vuiState.setPhase("thinking");
    
    if (!text || !vuiState.isActive) return false;
    if (vuiState.phase !== "executing") {
        vuiState.setPhase("speaking");
    }
    vuiState.setSystemMessage(text);
    
    return await this.audio.speak(text);
  }

  playNotificationPing() {
    this.audio.playNotificationPing();
  }

  checkAudioBlocked(): boolean {
    return this.audio.checkAudioBlocked();
  }

  async processGhost(cmd: string, source: "text" | "voice" = "text"): Promise<boolean> {
    if (source === "voice" || source === "text") {
       await this.execTextCmd(cmd, source);
       return true; 
    }
    return false; 
  }

  async unlockAudio() {
    await this.audio.unlock();
  }
}

export const vuiController = new VuiOrchestrator();
