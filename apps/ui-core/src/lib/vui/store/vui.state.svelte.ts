export type VuiPhase = "idle" | "listening" | "thinking" | "executing" | "speaking" | "error";

export const vuiState = $state({
  isActive: false,
  phase: "idle" as VuiPhase,
  volume: 0,
  transcript: "",
  liveText: "",
  systemMessage: "",
  isStarting: false,
  errorMsg: "",
  activeTier: "",
  cmdBuffer: "",
  hasSpoken: false,

  // VUI 2026: Helper methods for unified state transitions
  setActive(val: boolean) { this.isActive = val; },
  setPhase(val: VuiPhase) { 
    this.phase = val; 
    if (val === "listening" || val === "idle") this.errorMsg = "";
  },
  setVolume(val: number) { this.volume = val; },
  setTranscript(val: string) { this.transcript = val; },
  setLiveText(val: string) { this.liveText = val; },
  setSystemMessage(val: string) { this.systemMessage = val; },
  setStartingLock(val: boolean) { this.isStarting = val; },
  setError(msg: string) {
    this.phase = "error";
    this.errorMsg = msg;
  },
  setActiveTier(val: string) { this.activeTier = val; },
  setCmdBuffer(val: string) { this.cmdBuffer = val; },
  setHasSpoken(val: boolean) { this.hasSpoken = val; },

  reset() {
    this.isActive = false;
    this.phase = "idle";
    this.volume = 0;
    this.transcript = "";
    this.liveText = "";
    this.systemMessage = "";
    this.activeTier = "";
    this.isStarting = false;
    this.errorMsg = "";
    this.hasSpoken = false;
    this.cmdBuffer = "";
  }
});
