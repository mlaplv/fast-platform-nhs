import type { MicVAD as MicVADClass, utils as utilsNamespace } from "@ricky0123/vad-web";

let MicVAD: typeof MicVADClass | null = null;
let utils: typeof utilsNamespace | null = null;

import { VUI_CONFIG } from "./VuiConstants";

export class VuiVadEngine {
  private vad: MicVADClass | null = null;
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
        interface OrtEnv {
          wasm: {
            wasmPaths: Record<string, string>;
            numThreads: number;
            proxy: boolean;
          };
        }
        interface CustomWindow {
          ort?: {
            env: OrtEnv;
          };
        }
        const customWindow = window as unknown as CustomWindow;
        if (typeof window !== 'undefined') {
            if (!customWindow.ort) {
                console.log("[VUI] Loading AI Core (ort.min.js) dynamically for VAD...");
                try {
                    await new Promise<void>((resolve, reject) => {
                        const script = document.createElement('script');
                        script.src = '/wasm/ort.min.js';
                        script.async = true;
                        script.onload = () => resolve();
                        script.onerror = reject;
                        document.head.appendChild(script);
                    });
                } catch (e) {
                    console.warn("[VUI] Dynamic load of ort.min.js failed:", e);
                }
            }
            if (customWindow.ort) {
                const ort = customWindow.ort;
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
    }
    
    await this.stop(); // Idempotency guard

    const apiBase = `${window.location.protocol}//api.${window.location.hostname.split('.').slice(-2).join('.')}`;

    if (!MicVAD || !utils) {
      throw new Error("VAD engine or utils not initialized");
    }

    const currentUtils = utils;
    const options = {
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
        const wavBuffer = currentUtils.encodeWAV(audio);
        const blob = new Blob([wavBuffer], { type: "audio/wav" });
        onSpeechEnd(blob);
      },

      onFrameProcessed: (probs: { isSpeech: number }) => {
        this._probability = probs.isSpeech;
        onFrameProcessed(probs.isSpeech);
      },

      onVADMisfire: () => {
        console.debug("[VuiVadEngine] VAD misfire (too short to be speech)");
        this._isSpeaking = false;
      },
    };

    this.vad = await MicVAD.new(options as unknown as Parameters<typeof MicVADClass.new>[0]);
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
