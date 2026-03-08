/**
 * NEURAL PULSE ENGINE 2026 - Unified Voice Sync Algorithm
 * Deals with sentence tokenization, queuing, and sequential playback via browser TTS/Audio.
 */
export class TTSSpeaker {
  private sentenceBuffer = "";
  private speechQueue: string[] = [];
  private prefetchedBlobs = new Map<string, Blob>();
  private isProcessingQueue = false;
  private hasFirstSpeechStarted = false;
  private lastSentencesSpoken = new Set<string>();
  private abortController: AbortController | null = null;
  
  private checkIsActive: () => boolean;
  private fetchAudio: (text: string, signal: AbortSignal) => Promise<Blob>;
  private playAudio: (blob: Blob) => Promise<void>;
  private onFinishedCallback: () => void;

  constructor(
    checkIsActive: () => boolean,
    fetchAudio: (text: string, signal: AbortSignal) => Promise<Blob>,
    playAudio: (blob: Blob) => Promise<void>,
    onFinishedCallback: () => void
  ) {
    this.checkIsActive = checkIsActive;
    this.fetchAudio = fetchAudio;
    this.playAudio = playAudio;
    this.onFinishedCallback = onFinishedCallback;
  }

  reset() {
    this.sentenceBuffer = "";
    this.speechQueue = [];
    this.prefetchedBlobs.clear();
    this.isProcessingQueue = false;
    this.hasFirstSpeechStarted = false;
    this.lastSentencesSpoken.clear();
    this.abortController?.abort();
    this.abortController = null;
  }

  getSignal() {
    this.abortController?.abort();
    this.abortController = new AbortController();
    return this.abortController.signal;
  }

  abort() {
    this.abortController?.abort();
    this.abortController = null;
    this.speechQueue = [];
    this.prefetchedBlobs.clear();
    this.isProcessingQueue = false;
  }

  processChunk(chunk: string, updateUIText: (text: string) => void) {
    if (!this.checkIsActive()) return;
    this.sentenceBuffer += chunk;
    updateUIText(chunk);

    if (!this.hasFirstSpeechStarted) {
      const fastParts = this.sentenceBuffer.split(/([,.?!]|\n)/);
      if (fastParts.length > 2) {
        const seg = fastParts[0] + fastParts[1];
        this.enqueue(seg.trim());
        this.hasFirstSpeechStarted = true;
        this.sentenceBuffer = fastParts.slice(2).join("");
        return;
      }
    }

    const parts = this.sentenceBuffer.split(/([.?!]|\n)/);
    while (parts.length > 2) {
      const sentence = parts[0] + parts[1];
      this.enqueue(sentence.trim());
      this.sentenceBuffer = parts.slice(2).join("");
    }
  }

  flush() {
    if (this.sentenceBuffer.trim()) {
      this.enqueue(this.sentenceBuffer.trim());
      this.sentenceBuffer = "";
    }
  }

  private enqueue(text: string) {
    if (!text || text.length < 2 || !this.checkIsActive()) return;
    if (this.lastSentencesSpoken.has(text)) return;
    this.lastSentencesSpoken.add(text);
    this.speechQueue.push(text);
    
    // Trigger prefetch for the newly added item
    this.prefetch(text);
    
    if (!this.isProcessingQueue) this.processQueue();
  }

  private async prefetch(text: string) {
    if (this.prefetchedBlobs.has(text)) return;
    try {
      const signal = this.abortController?.signal || new AbortController().signal;
      const blob = await this.fetchAudio(text, signal);
      this.prefetchedBlobs.set(text, blob);
    } catch (e) {
      console.warn("[TTSSpeaker] Prefetch failed", text, e);
    }
  }

  private async processQueue() {
    if (this.speechQueue.length === 0 || !this.checkIsActive()) {
      this.isProcessingQueue = false;
      if (this.checkIsActive()) this.onFinishedCallback();
      return;
    }
    
    this.isProcessingQueue = true;
    const sentence = this.speechQueue.shift();
    if (sentence) {
      try {
        // 1. Get blob (from prefetch or fresh fetch)
        let blob = this.prefetchedBlobs.get(sentence);
        if (!blob) {
          const signal = this.abortController?.signal || new AbortController().signal;
          blob = await this.fetchAudio(sentence, signal);
        }
        this.prefetchedBlobs.delete(sentence);

        // 2. Prefetch the NEXT one(s) if not already done
        if (this.speechQueue[0]) {
          this.prefetch(this.speechQueue[0]);
        }

        // 3. Play
        if (blob) {
          await this.playAudio(blob);
        }
      } catch (e) {
        console.error("[TTSSpeaker] Playback failed", e);
      }
    }
    this.processQueue();
  }
}
