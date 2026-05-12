// [Elite V3.0] SSR Stealth: Dynamic imports to prevent server-side crash
// We only load these heavy/non-SSR libraries in the browser context.
let MicVAD: any;
let utils: any;

import { VUI_CONFIG } from "./VuiConstants";

export class VuiVadEngine {
  private vad: any = null;
  private _isSpeaking = false;
  private _probability = 0;

  get isSpeaking() { return this._isSpeaking; }
  get probability() { return this._probability; }

  /**
   * Start the Neural VAD engine.
   * @param onSpeechStart - Called when human voice is detected.
   * @param onSpeechEnd - Called when speech ends. Provides a WAV Blob of ONLY the speech audio.
   * @param onFrameProcessed - Called per frame with speech probability (for UI volume indicator).
   */
  async start(
    onSpeechStart: () => void,
    onSpeechEnd: (audioBlob: Blob) => void,
    onFrameProcessed: (probability: number) => void
  ): Promise<void> {
    // Lazy load the AI modules (Browser-only)
    if (!MicVAD) {
        const mod = await import("@ricky0123/vad-web");
        MicVAD = mod.MicVAD;
        utils = mod.utils;
        
        // [Elite V3.0] Neural Runtime Hardening
        // We use the pre-loaded window.ort injected via app.html
        if (typeof window !== 'undefined' && (window as any).ort) {
            const ort = (window as any).ort;
            const apiBase = `${window.location.protocol}//api.${window.location.hostname.split('.').slice(-2).join('.')}`;
            const wasmBase = `${apiBase}/wasm`;
            
            ort.env.wasm.wasmPaths = {
                'ort-wasm-simd-threaded.wasm': `${wasmBase}/ort-wasm-simd-threaded.wasm`,
                'ort-wasm-simd-threaded.jsep.wasm': `${wasmBase}/ort-wasm-simd-threaded.jsep.wasm`,
                'ort-wasm-simd.wasm': `${wasmBase}/ort-wasm-simd.wasm`,
                'ort-wasm.wasm': `${wasmBase}/ort-wasm.wasm`,
                'ort-wasm-simd-threaded.jsep.mjs': `${wasmBase}/ort-wasm-simd-threaded.jsep.mjs`,
                'ort-wasm-simd-threaded.mjs': `${wasmBase}/ort-wasm-simd-threaded.mjs`,
            };
            ort.env.wasm.numThreads = 1;
            ort.env.wasm.proxy = false;
        }
    }
    
    await this.stop(); // Idempotency guard

    const apiBase = `${window.location.protocol}//api.${window.location.hostname.split('.').slice(-2).join('.')}`;

    this.vad = await MicVAD.new({
      positiveSpeechThreshold: VUI_CONFIG.VAD.THRESHOLD,
      minSpeechMs: VUI_CONFIG.VAD.MIN_SPEECH_MS,
      redemptionMs: VUI_CONFIG.VAD.REDEMPTION_MS,
      preSpeechPadMs: VUI_CONFIG.VAD.PRE_SPEECH_PAD_MS,
      // Use API Gateway URLs for VAD-specific models (Silero)
      baseAssetPath: `${apiBase}/vad/`, 
      onnxWASMBasePath: `${apiBase}/wasm/`, // Force use the central WASM
      modelURL: `${apiBase}/vad/silero_vad_v5.onnx`,
      workletURL: `${apiBase}/vad/vad.worklet.bundle.min.js`,
      startOnLoad: true,

      onSpeechStart: () => {
        this._isSpeaking = true;
        onSpeechStart();
      },

      onSpeechEnd: (audio: Float32Array) => {
        this._isSpeaking = false;
        // Convert Float32Array (16kHz PCM) to WAV Blob for STT
        const wavBuffer = utils.encodeWAV(audio);
        const blob = new Blob([wavBuffer], { type: "audio/wav" });
        onSpeechEnd(blob);
      },

      onFrameProcessed: (probs) => {
        this._probability = probs.isSpeech;
        onFrameProcessed(probs.isSpeech);
      },

      onVADMisfire: () => {
        console.debug("[VuiVadEngine] VAD misfire (too short to be speech)");
        this._isSpeaking = false;
      },
    });
  }

  /**
   * Pause the VAD without destroying resources.
   */
  async pause(): Promise<void> {
    if (this.vad) {
      await this.vad.pause();
      this._isSpeaking = false;
    }
  }

  /**
   * Stop and clean up all VAD resources.
   */
  async stop(): Promise<void> {
    if (this.vad) {
      try {
        await this.vad.pause();
        this.vad.destroy();
      } catch (e) {
        console.debug("[VuiVadEngine] Cleanup error (safe to ignore):", e);
      }
      this.vad = null;
      this._isSpeaking = false;
      this._probability = 0;
    }
  }
}
