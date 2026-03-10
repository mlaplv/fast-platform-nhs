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
        
        audio.onended = () => { 
          resolve(); 
          if (this.currentUrl === url) {
            URL.revokeObjectURL(url);
            this.currentUrl = null;
          }
        };
        audio.onerror = () => { resolve(); URL.revokeObjectURL(url); };
        
        // Phase 85: Optimized Switching - only pause previous if it's still alive
        if (this.currentAudio) {
           this.currentAudio.pause();
           this.currentAudio.onended = null;
        }
        
        this.currentAudio = audio;
        this.currentUrl = url;
        
        audio.play().catch(e => {
          console.warn("[AudioEngine] playback blocked", e);
          resolve(); 
        });
      } catch (e) {
        resolve();
      }
    });
  }

  /**
   * Decoupled audio interruption to prevent memory leaks (Rule 1.3)
   */
  private interruptAudio() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.onended = null;
      this.currentAudio.onerror = null;
      this.currentAudio = null;
    }
    if (this.currentUrl) {
      URL.revokeObjectURL(this.currentUrl);
      this.currentUrl = null;
    }
  }
}
