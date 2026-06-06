import { logger } from '$lib/utils/logger';

/**
 * VuiSpeechEngine 2026: Native Browser STT Preview Layer
 * Provides sub-100ms word-by-word feedback using Web Speech API.
 * This acts as a "Fast Preview" before Gemini delivers the "Final Truth".
 */
export class VuiSpeechEngine {
  private recognition: SpeechRecognition | null = null;
  private isRunning = false;

  constructor() {
    if (typeof window === 'undefined') return;

    const SpeechRecognition = (window as { SpeechRecognition?: typeof window.SpeechRecognition; webkitSpeechRecognition?: typeof window.SpeechRecognition }).SpeechRecognition || (window as { SpeechRecognition?: typeof window.SpeechRecognition; webkitSpeechRecognition?: typeof window.SpeechRecognition }).webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition() as SpeechRecognition;
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'vi-VN';
    } else {
      logger.debug("[VuiSpeechEngine] Web Speech API not supported in this browser. Fallback to server-side transcription.");
    }
  }

  /**
   * Start capturing voice to text preview.
   * @param onResult - Callback for interim and final text.
   */
  start(onResult: (text: string, isFinal: boolean) => void) {
    if (!this.recognition || this.isRunning) return;

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      // Combine for the "Live" feel
      const fullText = (finalTranscript + interimTranscript).trim();
      if (fullText) {
        onResult(fullText, false);
      }
    };

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      logger.debug("[VuiSpeechEngine] Recognition error:", event.error);
      if (event.error === 'no-speech') return;
      this.stop();
    };

    this.recognition.onend = () => {
      if (this.isRunning) {
        try {
          this.recognition.start();
        } catch (e) {
          logger.warn('Failed to restart speech recognition', e);
        }
      }
    };

    try {
      this.recognition.start();
      this.isRunning = true;
      logger.debug("[VuiSpeechEngine] Native Preview started.");
    } catch (e) {
      logger.error("[VuiSpeechEngine] Failed to start:", e);
    }
  }

  stop() {
    this.isRunning = false;
    if (this.recognition) {
      try {
        this.recognition.stop();
        logger.debug("[VuiSpeechEngine] Native Preview stopped.");
      } catch (e) {
        logger.warn('Failed to stop speech recognition', e);
      }
    }
  }
}
