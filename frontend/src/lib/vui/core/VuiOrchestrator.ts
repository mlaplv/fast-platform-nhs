import { vuiState } from "../store/vui.state.svelte";
import { MicrophoneEngine } from "./MicrophoneEngine";
import { WebSocketStream } from "./WebSocketStream";
import { VuiAudioEngine } from "./VuiAudioEngine";
import { VUI_CONFIG } from "./VuiConstants";
import { getNanobot } from "$lib/state/nanobot.svelte";
const getBot = () => getNanobot();
import { VuiStreamManager } from "./VuiStreamManager";
import { VuiVadEngine } from "./VuiVadEngine";
import { VuiSpeechEngine } from "./VuiSpeechEngine";
import { isDev, isAdminDomain } from "$lib/state/nanobot/env";

/**
 * VuiOrchestrator 2026: The "Neural Conductor"
 * Orchestrates VAD Engine, Mic, WS Stream, Audio Engine, and Stream Manager.
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

  private getCookie(name: string): string {
    if (typeof document === 'undefined') return "";
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() || "";
    return "";
  }

  constructor() {
    if (typeof window === 'undefined' || !isAdminDomain()) return;

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

    // Elite 2026: Root Cause Fix - Sanitize state to prevent "Resume" hijack
    // When starting from idle, we force clear any previous VUI response data
    // to ensure the microphone only focuses on the new conversation.
    if (vuiState.phase === 'idle') {
      getBot().clearVuiResponse();
      getBot().clearCommandAction();
    }
    
    vuiState.setStartingLock(true);
    vuiState.setActive(true);
    getBot().setVuiActive(true);
    
    if (autoBypassAudio) {
      try { this.audio?.abort(); } catch(e) { console.debug("[VUI] Audio abort suppressed:", e); }
    }
    this.audio?.reset();
    
    this.hasSpoken = false;
    this.streamManager!.setLastAction("");
    
    vuiState.setTranscript("");
    vuiState.setLiveText("");
    vuiState.setSystemMessage("");
    vuiState.setActiveTier("");
    vuiState.setPhase("listening");

    try {
      try {
        await this.audio!.unlock();
        this.audio!.playSystemSound('start');
      } catch(e) {
        console.warn("[VUI] Audio unlock/ping failed, but continuing:", e);
      }
      
      const sessionId = getBot().currentData?.session_id || vuiState.history[0]?.id || `vui_${Date.now()}`;
      
      let token = "";
      if (typeof localStorage !== 'undefined') {
        token = localStorage.getItem("admin_token") || localStorage.getItem("access_token") || "";
      }
      if (!token && typeof document !== 'undefined') {
        token = this.getCookie("admin_token") || this.getCookie("access_token");
      }

      await this.ws!.connect(
        (data) => this.streamManager!.handleWsMessage(data),
        undefined, undefined, undefined,
        { session_id: sessionId, token: token || "" }
      );
      
      if (this.mic!.isActive()) this.mic!.stop();
      this.mic!.start(VUI_CONFIG.MIC.CHUNK_DURATION_MS,
        (blob) => {
          if (vuiState.phase !== "listening") return;
          this.ws!.sendBinary(blob);
        },
        (vol) => {
          vuiState.setVolume(vol);
        }
      );
      
      await this.vadEngine!.start(
        () => {
          if (vuiState.phase !== "listening") return;
          this.hasSpoken = true;
          this.clearTimer('initial');
        },
        (audioBlob) => {
          if (vuiState.phase !== "listening") return;
          if (this.hasSpoken) {
            this.stopRecording();
          }
        },
        (probability) => {
          if (vuiState.phase === "listening") {
            vuiState.setSpeechProb(probability);
          }
        }
      );

      this.speechEngine!.start((text) => {
        if (vuiState.phase !== "listening") return;
        vuiState.setLiveText(text);
      });

      this.setManagedTimer('initial', () => {
        if (vuiState.phase === "listening" && !this.hasSpoken) {
          this.interruptAll();
        }
      }, VUI_CONFIG.VAD.INITIAL_TIMEOUT_MS);

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
    getBot().setVuiActive(false);
    this.streamManager!.setLastAction("");
  }

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
      vuiState.setLiveText("Sẵn sàng...");
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
        if (vuiState.isActive && getBot().isVuiActive) {
          vuiState.setLiveText("");
          this.startRecording(false);
          vuiState.requiresListening = false;
          vuiState.behavior = 'sleep';
        }
      }, delay);
    } else if (vuiState.isActive) {
      console.info("[VUI] AI requested sleep or no behavior defined. Standing by.");
      this.setManagedTimer('interrupt_check', () => {
      }, 5000);
    }
  }

  async execTextCmd(query: string, source: "text" | "voice" = "text", intentData?: Record<string, unknown>) {
    if (!query) return;
    this.audio!.abort();
    this.ws!.disconnect();

    vuiState.setActive(true);
    getBot().setVuiActive(true);

    vuiState.setPhase("thinking");
    vuiState.setTranscript(query);
    vuiState.setLiveText(query);
    vuiState.setSystemMessage("");

    await this.streamManager!.streamLLM(query, getBot().currentData?.session_id || "", source, intentData);
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
    this.onTTSFinished();
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

export const vuiController = (typeof window !== 'undefined' && isAdminDomain()) ? new VuiOrchestrator() : {} as unknown as VuiOrchestrator;
