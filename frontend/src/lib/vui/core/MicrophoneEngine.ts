export class MicrophoneEngine {
  private stream: MediaStream | null = null;
  private recorder: MediaRecorder | null = null;
  private maxTimer: ReturnType<typeof setTimeout> | null = null;
  private audioCtx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private dataArr: Uint8Array | null = null;
  private animationFrameId: number | null = null;

  /**
   * Khởi động Microphone và cấp luồng audio (MediaRecorder)
   * Lấy mức volume liên tục qua onVolume callback
   */
  async start(
    chunkDurationMs: number,
    onData: (blob: Blob) => void,
    onVolume: (vol: number) => void
  ): Promise<void> {
    this.stop(); // Safe guard (Idempotency)

    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Microphone API is not supported in this browser.");
    }

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true }
    });

    // 1. Setup MediaRecorder for chunks
    const mime =
      ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find((t) =>
        MediaRecorder.isTypeSupported(t)
      ) || "";
      
    this.recorder = new MediaRecorder(this.stream, mime ? { mimeType: mime } : undefined);
    
    console.log("[MicEngine] Started MediaRecorder with mimeType:", mime);
    
    this.recorder.ondataavailable = (e: BlobEvent) => {
      if (e.data.size > 0) {
        onData(e.data);
      }
    };
    this.recorder.start(chunkDurationMs);

    // 2. Setup AudioContext Analyser for Volume Monitoring
    const AC = window.AudioContext || (window as any).webkitAudioContext;
    this.audioCtx = new AC();
    this.analyser = this.audioCtx.createAnalyser();
    const source = this.audioCtx.createMediaStreamSource(this.stream);
    source.connect(this.analyser);
    this.dataArr = new Uint8Array(this.analyser.frequencyBinCount);

    const updateVolume = () => {
      if (!this.analyser || !this.dataArr) return;
      this.analyser.getByteTimeDomainData(this.dataArr as any);
      
      // 2026 Refactor: Switch from Frequency to Time domain for accurate Peak amplitude
      let maxAbs = 0;
      for (let i = 0; i < this.dataArr.length; i++) {
        const val = Math.abs(this.dataArr[i] - 128); 
        if (val > maxAbs) maxAbs = val;
      }
      let vol = maxAbs / 128; // Max offset is 128
      
      // DC Offset / Hardware Noise Correction 2026
      // Subtract a tiny floor (0.005) to clear low-level electric buzz
      vol = Math.max(0, vol - 0.005);

      onVolume(vol);
      this.animationFrameId = requestAnimationFrame(updateVolume);
    };
    updateVolume();
  }

  /**
   * Ngắt 100% mọi kết nối Mic một cách an toàn
   */
  stop() {
    if (this.maxTimer) clearTimeout(this.maxTimer);
    
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }

    try {
      this.recorder?.stop();
    } catch (e) {}
    this.recorder = null;

    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }

    if (this.audioCtx && this.audioCtx.state !== "closed") {
      this.audioCtx.close().catch(() => {});
    }
    this.audioCtx = null;
    this.analyser = null;
    this.dataArr = null;
  }

  isActive(): boolean {
    return !!this.recorder && this.recorder.state === "recording";
  }
}
