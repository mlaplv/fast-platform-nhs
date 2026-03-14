import { MicVAD, utils } from "@ricky0123/vad-web";
import { VUI_CONFIG } from "./VuiConstants";

/**
 * VuiVadEngine 2026: Neural Voice Activity Detection
 * Wraps @ricky0123/vad-web (Silero VAD) to provide clean speech detection.
 * Replaces the old volume-based VAD completely.
 */
export class VuiVadEngine {
  private vad: MicVAD | null = null;
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
    await this.stop(); // Idempotency guard

    this.vad = await MicVAD.new({
      positiveSpeechThreshold: VUI_CONFIG.VAD.THRESHOLD,
      minSpeechMs: VUI_CONFIG.VAD.MIN_SPEECH_MS,
      redemptionMs: VUI_CONFIG.VAD.REDEMPTION_MS,
      preSpeechPadMs: VUI_CONFIG.VAD.PRE_SPEECH_PAD_MS,
      // Use absolute URLs to prevent Vite from intercepting .mjs/wasm as dynamic imports
      baseAssetPath: `${window.location.origin}/vad/`, 
      onnxWASMBasePath: `${window.location.origin}/vad/`,
      modelURL: `${window.location.origin}/vad/silero_vad_v5.onnx`,
      workletURL: `${window.location.origin}/vad/vad.worklet.bundle.min.js`,
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
