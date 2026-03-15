/**
 * VuiSpeechEngine 2026: Native Browser STT Preview Layer
 * Provides sub-100ms word-by-word feedback using Web Speech API.
 * This acts as a "Fast Preview" before Groq Whisper delivers the "Final Truth".
 */
export class VuiSpeechEngine {
  private recognition: any = null;
  private isRunning = false;

  constructor() {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'vi-VN';
    } else {
      console.warn("[VuiSpeechEngine] Web Speech API not supported in this browser.");
    }
  }

  /**
   * Start capturing voice to text preview.
   * @param onResult - Callback for interim and final text.
   */
  start(onResult: (text: string, isFinal: boolean) => void) {
    if (!this.recognition || this.isRunning) return;

    this.recognition.onresult = (event: any) => {
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

    this.recognition.onerror = (event: any) => {
      console.debug("[VuiSpeechEngine] Recognition error:", event.error);
      if (event.error === 'no-speech') return;
      this.stop();
    };

    this.recognition.onend = () => {
      if (this.isRunning) {
        try { this.recognition.start(); } catch(e) {} // Auto-restart if still supposed to be running
      }
    };

    try {
      this.recognition.start();
      this.isRunning = true;
      console.debug("[VuiSpeechEngine] Native Preview started.");
    } catch (e) {
      console.error("[VuiSpeechEngine] Failed to start:", e);
    }
  }

  stop() {
    this.isRunning = false;
    if (this.recognition) {
      try {
        this.recognition.stop();
        console.debug("[VuiSpeechEngine] Native Preview stopped.");
      } catch (e) {}
    }
  }
}
