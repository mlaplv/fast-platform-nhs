import { vuiState } from "../store/vui.state.svelte";
import { MicrophoneEngine } from "./MicrophoneEngine";
import { WebSocketStream } from "./WebSocketStream";
import { VuiAudioEngine } from "./VuiAudioEngine";
import { VUI_CONFIG } from "./VuiConstants";
import { nanobot } from "$lib/state/nanobot.svelte";
import { VuiStreamManager } from "./VuiStreamManager";
import { VuiVadEngine } from "./VuiVadEngine";
import { VuiSpeechEngine } from "./VuiSpeechEngine";
import { isDev } from "$lib/state/nanobot/env";

/**
 * VuiOrchestrator 2026: The "Neural Conductor"
 * Orchestrates VAD Engine, Mic, WS Stream, Audio Engine, and Stream Manager.
 * Phase 15: Silero VAD Integration — Neural Voice Activity Detection.
 * Phase 16: Hybrid STT Layer — Native Speech API for sub-100ms Preview.
 */
class VuiOrchestrator {
  private mic: MicrophoneEngine | null = null;
  private ws: WebSocketStream | null = null;
  private audio: VuiAudioEngine | null = null;
  private streamManager: VuiStreamManager | null = null;
  private vadEngine: VuiVadEngine | null = null;
  private speechEngine: VuiSpeechEngine | null = null;

  private hasSpoken = false;
  private stopAfterSpeech = false;
  
  // Phase 42: Neural Lifecycle Control (Premium Timer Management)
  private activeTimers = new Map<string, ReturnType<typeof setTimeout>>();

  private clearTimer(key: string) {
    const timer = this.activeTimers.get(key);
    if (timer) {
      clearTimeout(timer);
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
    if (typeof window === 'undefined') return;

    this.mic = new MicrophoneEngine();
    this.ws = new WebSocketStream(VUI_CONFIG.ENDPOINTS.STT_WS);
    this.audio = new VuiAudioEngine(() => this.onTTSFinished());
    this.vadEngine = new VuiVadEngine();
    this.speechEngine = new VuiSpeechEngine();

    this.streamManager = new VuiStreamManager(this.audio, {
      interruptAll: () => this.interruptAll(),
      stopRecording: () => this.stopRecording(),
      onTTSFinished: () => this.onTTSFinished(),
      speak: (text: string) => this.speak(text),
      hasSpoken: () => this.hasSpoken
    });
  }

  async startRecording(autoBypassAudio = true) {
    if (vuiState.isStarting) return;
    if (vuiState.phase === 'thinking' || vuiState.phase === 'error') {
       vuiState.setPhase('idle');
    }
    
    vuiState.setStartingLock(true);
    vuiState.setActive(true);
    nanobot.setVuiActive(true);
    
    if (autoBypassAudio) this.audio?.abort();
    this.audio?.reset();
    
    this.hasSpoken = false;
    this.streamManager!.setLastAction("");
    
    vuiState.setTranscript("");
    vuiState.setLiveText("");
    vuiState.setSystemMessage("");
    vuiState.setActiveTier("");
    vuiState.setPhase("listening");

    try {
      // V71.4: Multi-Browser Warmup. Proactively ensure context is unlocked.
      await this.audio!.unlock();
      this.audio!.playSystemSound('start');
      
      // Step 1: Connect WebSocket for STT streaming
      const sessionId = nanobot.currentData?.session_id || "";
      await this.ws!.connect(
        (data) => this.streamManager!.handleWsMessage(data),
        undefined, undefined, undefined,
        { session_id: sessionId }
      );
      
      // Step 2: Start MicrophoneEngine for sending WebM chunks to WS
      if (this.mic!.isActive()) this.mic!.stop();
      this.mic!.start(VUI_CONFIG.MIC.CHUNK_DURATION_MS,
        (blob) => {
          if (vuiState.phase !== "listening") return;
          this.ws!.sendBinary(blob);
        },
        (vol) => {
          // Volume is now ONLY used for UI animation, NOT for VAD
          vuiState.setVolume(vol);
        }
      );
      
      // Step 3: Start Silero VAD Engine (Neural Voice Detection)
      await this.vadEngine!.start(
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
            this.stopRecording();
          }
        },
        // onFrameProcessed: Per-frame probability for UI feedback
        (probability) => {
          if (vuiState.phase === "listening") {
            vuiState.setSpeechProb(probability);
          }
        }
      );

      // Step 4: Hybrid STT Preview (Live Word-by-Word)
      this.speechEngine!.start((text) => {
        if (vuiState.phase !== "listening") return;
        // Native preview updates the UI immediately
        vuiState.setLiveText(text);
      });

      // Step 5: Initial timeout — if no speech detected within 7s, clean exit
      this.setManagedTimer('initial', () => {
        if (vuiState.phase === "listening" && !this.hasSpoken) {
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
    } catch (e: unknown) {
      const err = e as Error;
      console.error("[VuiOrchestrator] MIC_START_FAIL:", err);
      vuiState.setError(err.message || "Lỗi truy cập Microphone");
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

    this.ws!.sendStopSignal();
    this.streamManager!.startSttGuard();
    this.mic!.stop();
    this.vadEngine!.pause();
    this.speechEngine!.stop();
    this.audio!.playSystemSound('stop');
    vuiState.setVolume(0);
    vuiState.setStartingLock(false);
  }

  interruptAll() {
    this.clearAllTimers();
    this.streamManager!.clearSttGuard();
    this.audio!.abort();
    this.mic!.stop();
    this.vadEngine!.stop();
    this.speechEngine!.stop();
    this.ws!.disconnect();
    vuiState.reset();
    vuiState.setStartingLock(false);
    nanobot.setVuiActive(false);
    this.streamManager!.setLastAction("");
  }

  /**
   * Surgical Interruption: Stop current reading/text but keep VUI modal active.
   */
  private phaseResetTimer: ReturnType<typeof setTimeout> | null = null;

  resetToIdle() {
    if (this.phaseResetTimer) {
       clearTimeout(this.phaseResetTimer);
       this.phaseResetTimer = null;
    }
    vuiState.setPhase("idle");
    vuiState.setLiveText("");
    vuiState.setSystemMessage("");
  }

  interruptSpeech() {
    this.audio!.abort();
    this.clearAllTimers();

    this.mic!.stop();
    this.vadEngine!.pause();
    this.speechEngine!.stop();
    vuiState.setSystemMessage("");
    vuiState.setIsWaitingForAction(false);
    vuiState.setPhase("executing");
    vuiState.setLiveText("Hệ thống đang chuyển pha...");
    this.streamManager!.setLastAction("");

    this.setManagedTimer('phase_reset', () => {
      if (vuiState.phase === "executing") {
        this.resetToIdle();
      }
    }, 30000);
  }

  setStopAfterSpeech(val: boolean) { this.stopAfterSpeech = val; }

  private onTTSFinished() {
    if (vuiState.isWaitingForAction) {
      this.mic?.stop();
      this.vadEngine?.pause();
      vuiState.setPhase("idle");
      vuiState.setLiveText("Sẵn sàng thưa sếp...");
    }

    if (vuiState.phase !== "idle") {
      vuiState.setPhase("idle");
      vuiState.setActiveTier("");
    }

    if (this.stopAfterSpeech) {
      this.stopAfterSpeech = false;
      this.interruptAll();
      return;
    }

    if (vuiState.requiresListening && vuiState.isActive) {
      console.info("[VUI] AI requested listening. Re-opening mic.");
      const delay = VUI_CONFIG.UX.POST_SPEECH_DELAY_MS;
      this.setManagedTimer('resumption', () => {
        if (vuiState.isActive && nanobot.isVuiActive) {
          vuiState.setLiveText("");
          this.startRecording(false);
          vuiState.requiresListening = false;
          vuiState.behavior = 'sleep';
        }
      }, delay);
    } else if (vuiState.isActive) {
      console.info("[VUI] AI requested sleep or no behavior defined. Standing by.");
      this.setManagedTimer('interrupt_check', () => {
         // Auto-cleanup if idle too long and not listening
         // this.interruptAll(); // Optional: user might want it kept open
      }, 5000);
    }
  }

  async execTextCmd(query: string, source: "text" | "voice" = "text", intentData?: Record<string, unknown>) {
    if (!query) return;
    this.audio!.abort();
    this.ws!.disconnect();

    // Unified VUI: Always active for both voice and text sources
    vuiState.setActive(true);
    nanobot.setVuiActive(true);

    vuiState.setPhase("thinking");
    vuiState.setTranscript(query);
    vuiState.setLiveText(query); // Ensure query is visible in VUI modal
    vuiState.setSystemMessage("");

    await this.streamManager!.streamLLM(query, nanobot.currentData?.session_id || "", source, intentData);
  }

  async speak(text: string): Promise<boolean> {
    this.mic!.stop();
    this.vadEngine!.pause();
    this.speechEngine!.stop();
    if (vuiState.phase === "listening") vuiState.setPhase("thinking");

    if (!text || !vuiState.isActive) return false;
    if (vuiState.phase !== "executing") {
        vuiState.setPhase("speaking");
    }
    vuiState.setSystemMessage(text);

    const result = await this.audio!.speak(text);
    this.onTTSFinished(); // V87.5 Fix: Re-open mic after manual/error speech
    return result;
  }

  playNotificationPing() {
    this.audio!.playNotificationPing();
  }

  checkAudioBlocked(): boolean {
    return this.audio!.checkAudioBlocked();
  }

  async processGhost(cmd: string, source: "text" | "voice" = "text", intentData?: Record<string, unknown>): Promise<boolean> {
    if (source === "voice" || source === "text") {
       await this.execTextCmd(cmd, source, intentData);
       return true;
    }
    return false;
  }

  async unlockAudio() {
    await this.audio!.unlock();
  }
}

export const vuiController = (typeof window !== 'undefined') ? new VuiOrchestrator() : {} as unknown as VuiOrchestrator;
