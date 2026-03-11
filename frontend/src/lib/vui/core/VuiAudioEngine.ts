import { vuiState } from "../store/vui.state.svelte";
import { TTSSpeaker } from "./TTSSpeaker";
import { vuiService } from "./VuiService";

/**
 * VuiAudioEngine: Dedicated engine for TTS and Raw Audio playback.
 * Complies with Rule 1.3 (Separation of Concerns) and 1.3.1 (Memory Discipline).
 */
export class VuiAudioEngine {
  private currentAudio: HTMLAudioElement | null = null;
  private currentUrl: string | null = null;
  private tts: TTSSpeaker;

  constructor(onFinished: () => void) {
    this.tts = new TTSSpeaker(
      () => vuiState.isActive,
      (text, signal) => vuiService.fetchTtsBlob(text, signal),
      async (blob) => this.playAudio(blob),
      () => onFinished()
    );
  }

  /**
   * Process a text chunk for TTS playback
   */
  processChunk(text: string) {
    this.tts.processChunk(text, () => {});
  }

  /**
   * Flush TTS queue and finish current speech
   */
  flush() {
    this.tts.flush();
  }

  /**
   * Abort all current speech and audio
   */
  abort() {
    this.tts.abort();
    this.interruptAudio();
  }

  /**
   * Reset TTS state
   */
  reset() {
    this.tts.reset();
  }

  /**
   * Get abort signal for TTS requests
   */
  getSignal() {
    return this.tts.getSignal();
  }

  /**
   * Play a standalone text via TTS (Legacy support/Direct speak)
   */
  async speak(text: string): Promise<void> {
    if (!vuiState.isActive) return;
    const signal = this.getSignal();
    try {
      const blob = await vuiService.fetchTtsBlob(text, signal);
      await this.playAudio(blob);
    } catch (e) {
      console.warn("[AudioEngine] speak failed", e);
    }
  }

  /**
   * Internal routine to play an audio blob and manage cleanup
   */
  private async playAudio(blob: Blob): Promise<void> {
    if (!vuiState.isActive) return;

    return new Promise((resolve) => {
      try {
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        
        let isResolved = false;
        const finalize = () => {
          if (isResolved) return;
          isResolved = true;
          // Phase 6: 500ms Anti-Death Loop Lock to prevent mic feedback
          setTimeout(() => {
            resolve();
            if (this.currentUrl === url) {
              URL.revokeObjectURL(url);
              this.currentUrl = null;
            }
          }, 500);
        };

        audio.onended = finalize;
        audio.onpause = finalize;
        audio.onabort = finalize;
        audio.onerror = () => { 
          if (isResolved) return; 
          isResolved = true; 
          resolve(); 
          URL.revokeObjectURL(url); 
        };
        
        // Phase 85: Optimized Switching - only pause previous if it's still alive
        if (this.currentAudio) {
           this.currentAudio.onended = null;
           this.currentAudio.onpause = null;
           this.currentAudio.onabort = null;
           this.currentAudio.onerror = null;
           this.currentAudio.pause();
        }
        
        this.currentAudio = audio;
        this.currentUrl = url;
        
        audio.play().catch(e => {
          console.warn("[AudioEngine] playback blocked", e);
          if (!isResolved) {
             isResolved = true;
             resolve();
          }
        });
      } catch (e) {
        resolve();
      }
    });
  }

  /**
   * Play system notification sounds (Mic Beeps)
   * Using Web Audio API to avoid external asset dependency (Rule 1.3)
   */
  playSystemSound(type: 'start' | 'stop') {
    try {
      const AC = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AC();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.connect(gain);
      gain.connect(ctx.destination);

      // GPT-style Beep: Short, soft, high-pitched
      if (type === 'start') {
        osc.frequency.setValueAtTime(880, ctx.currentTime); // A5
        gain.gain.setValueAtTime(0, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.05, ctx.currentTime + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.1);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.1);
      } else {
        osc.frequency.setValueAtTime(440, ctx.currentTime); // A4
        gain.gain.setValueAtTime(0, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.05, ctx.currentTime + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.15);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.15);
      }

      // Cleanup context
      setTimeout(() => ctx.close(), 500);
    } catch (e) {
      console.warn("[AudioEngine] System sound failed", e);
    }
  }

  /**
   * Decoupled audio interruption to prevent memory leaks (Rule 1.3)
   */
  private interruptAudio() {
    if (this.currentAudio) {
      this.currentAudio.onended = null;
      this.currentAudio.onpause = null;
      this.currentAudio.onabort = null;
      this.currentAudio.onerror = null;
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    if (this.currentUrl) {
      URL.revokeObjectURL(this.currentUrl);
      this.currentUrl = null;
    }
  }
}
