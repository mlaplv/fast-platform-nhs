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
  
    // Phase 44: Patient Queue (R109.2) - Refined for high-frequency race conditions
    private hasUserInteracted = false;
    private pendingQueue: { text: string; resolve: (val: boolean) => void }[] = [];
    private isDrainingQueue = false;
    private audioCtx: AudioContext | null = null;
  
    constructor(onFinished: () => void) {
      this.tts = new TTSSpeaker(
        () => vuiState.isActive,
        (text, signal) => vuiService.fetchTtsBlob(text, signal),
        async (blob) => this.playAudio(blob),
        () => onFinished()
      );
  
      // CNS V71.0: Permanent/Resilient Unlocker (Premium Continuous Support)
      if (typeof window !== 'undefined') {
        const silentUnlock = async () => {
           // If AC is already running and nothing in queue, we don't need to do expensive context warm
           if (this.hasUserInteracted && this.pendingQueue.length === 0) return;
           
           await this.unlock(); 
           
           if (this.pendingQueue.length > 0 && !this.isDrainingQueue) {
             this.isDrainingQueue = true;
             
             let index = 0;
             while(this.pendingQueue.length > 0) {
                const item = this.pendingQueue.shift();
                if (item) {
                   index++;
                   const success = await this.speak(item.text);
                   item.resolve(success);
                }
             }
             this.isDrainingQueue = false;
           }
        };
        window.addEventListener('click', silentUnlock, { capture: true });
        window.addEventListener('touchstart', silentUnlock, { capture: true });
      }
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
    this.pendingQueue = [];
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
   * Play a standalone text via TTS
   */
  async speak(text: string): Promise<boolean> {
    if (!vuiState.isActive) return false;

    // CNS V71.1: Auto-Queueing on block logic
    const attemptPlay = async () => {
        const signal = this.getSignal();
        try {
          const blob = await vuiService.fetchTtsBlob(text, signal);
          return await this.playAudio(blob);
        } catch (e) {
          console.warn("[AudioEngine] speak attempt failed", e);
          return false;
        }
    };

    // If we think we are unlocked, try it
    if (this.hasUserInteracted) {
        const success = await attemptPlay();
        if (success) return true;
        
        this.hasUserInteracted = false;
        vuiState.setAudioBlocked(true);
    }

    // Always queue if blocked or previous attempt failed
    return new Promise((resolve) => {
      this.pendingQueue.push({ text, resolve });
    });
  }

  /**
   * Check if the audio context is suspended or likely blocked
   */
  checkAudioBlocked(): boolean {
    if (typeof window === 'undefined') return false;
    if (this.pendingQueue.length > 0) return true;
    if (!this.hasUserInteracted) return false;
    
    try {
      if (!this.audioCtx) return true;
      return this.audioCtx.state === "suspended";
    } catch (e) {
      return true;
    }
  }

  /**
   * Internal routine to play an audio blob and manage cleanup
   */
  private async playAudio(blob: Blob): Promise<boolean> {
    if (!vuiState.isActive) return false;

    return new Promise((resolve) => {
      try {
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        
        let isResolved = false;
        const finalize = (success = true) => {
          if (isResolved) return;
          isResolved = true;
          setTimeout(() => {
            resolve(success);
            if (this.currentUrl === url) {
              URL.revokeObjectURL(url);
              this.currentUrl = null;
            }
          }, 500);
        };

        audio.onended = () => finalize(true);
        audio.onpause = () => finalize(true); 
        audio.onabort = () => finalize(false);
        audio.onerror = () => finalize(false);
        
        if (this.currentAudio) {
           this.currentAudio.onended = null;
           this.currentAudio.onpause = null;
           this.currentAudio.onabort = null;
           this.currentAudio.onerror = null;
           this.currentAudio.pause();
        }
        
        this.currentAudio = audio;
        this.currentUrl = url;
        
        audio.play().then(() => {
          // Playback started successfully
        }).catch(e => {
          console.warn("[AudioEngine] playback blocked", e);
          if (e.name === 'NotAllowedError' && this.hasUserInteracted) {
            vuiState.setAudioBlocked(true);
            this.hasUserInteracted = false;
          }
          finalize(false);
        });
      } catch (e) {
        resolve(false);
      }
    });
  }

  /**
   * Play system notification sounds (Mic Beeps)
   */
  playSystemSound(type: 'start' | 'stop') {
    if (!this.hasUserInteracted || !this.audioCtx) return;
    
    try {
      const ctx = this.audioCtx;
      if (ctx.state === 'suspended') return;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.connect(gain);
      gain.connect(ctx.destination);

      if (type === 'start') {
        osc.frequency.setValueAtTime(880, ctx.currentTime); 
        gain.gain.setValueAtTime(0, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.05, ctx.currentTime + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.1);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.1);
      } else {
        osc.frequency.setValueAtTime(440, ctx.currentTime); 
        gain.gain.setValueAtTime(0, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.05, ctx.currentTime + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.15);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.15);
      }
    } catch (e) {
      console.warn("[AudioEngine] System sound failed", e);
    }
  }

   /**
    * playNotificationPing: Professional stealth alert sound
    */
   async playNotificationPing() {
     if (typeof window === 'undefined') return;

     // Attempt to warm and unlock AudioContext if user has interacted
     if (!this.audioCtx && this.hasUserInteracted) {
       await this.unlock();
     }

     if (!this.audioCtx) return;

     try {
       const ctx = this.audioCtx;
       if (ctx.state === 'suspended' || ctx.state === 'interrupted') {
         await ctx.resume().catch(() => {});
       }

       // Final safe exit if still blocked by browser policy
       if (ctx.state === 'suspended') return;

       const osc = ctx.createOscillator();
       const gain = ctx.createGain();
       osc.connect(gain);
       gain.connect(ctx.destination);
       
       osc.frequency.setValueAtTime(880, ctx.currentTime);
       osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.1);
       gain.gain.setValueAtTime(0, ctx.currentTime);
       gain.gain.linearRampToValueAtTime(0.04, ctx.currentTime + 0.01);
       gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.4);
       
       osc.start();
       osc.stop(ctx.currentTime + 0.4);
     } catch(e) {
       console.warn("[VuiAudioEngine] playNotificationPing failed:", e);
     }
   }

  /**
   * Unlock AudioContext on User Gesture (R109: Browser Compliance)
   */
  async unlock() {
    try {
      const AC = (window as { AudioContext?: typeof AudioContext; webkitAudioContext?: typeof AudioContext }).AudioContext || (window as { AudioContext?: typeof AudioContext; webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (AC) {
        if (!this.audioCtx) {
          this.audioCtx = new AC();
        }
        
        // V71.3: Enhanced Safari/Firefox Waking
        if (this.audioCtx!.state === 'suspended' || this.audioCtx!.state === 'interrupted') {
           await this.audioCtx!.resume();
        }
        
        // Phase 46: Keep context alive with a short-lived silent oscillator
        const osc = this.audioCtx!.createOscillator();
        const gain = this.audioCtx!.createGain();
        gain.gain.value = 0;
        osc.connect(gain);
        gain.connect(this.audioCtx!.destination);
        osc.start(0);
        osc.stop(0.001);
      }
      
      // Safari specific: Playing a bone-dry silent buffer is often more reliable than just resume()
      const dummy = new Audio();
      dummy.src = "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhAAQACABAAAABkYXRhAgAAAAEA";
      await dummy.play().catch(() => {});
      
      this.hasUserInteracted = true;
      vuiState.setAudioBlocked(false);
    } catch (e) {
      console.warn("[AudioEngine] Unlock failed", e);
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
