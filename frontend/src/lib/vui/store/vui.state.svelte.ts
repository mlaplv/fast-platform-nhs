export type VuiPhase = "idle" | "listening" | "thinking" | "executing" | "speaking" | "error";

export interface VuiInteraction {
  id: string;
  userQuery: string;
  aiResponse: string;
  duration: number;
}

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

  isWaitingForAction: false,
  history: [] as VuiInteraction[],

  // VUI 2026: Helper methods for unified state transitions
  setActive(val: boolean) { this.isActive = val; },
  setIsWaitingForAction(val: boolean) { this.isWaitingForAction = val; },
  setPhase(val: VuiPhase) { 
    // Logic: If transitioning AWAY from speaking/executing or error
    if ((this.phase === "speaking" || this.phase === "executing" || this.phase === "error") && 
        (val === "listening" || val === "idle" || val === "thinking")) {
      this.finalizeInteraction();
    }
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

  
  finalizeInteraction() {
    if (this.transcript || this.systemMessage) {
        this.history.push({
            id: Math.random().toString(36).substr(2, 9),
            userQuery: this.transcript || this.liveText,
            aiResponse: this.systemMessage,
            duration: 0 
        });
        // Clear buffers to prevent double-saving or ghost text in next turn
        this.transcript = "";
        this.systemMessage = "";
        this.liveText = "";
    }
  },

  reset() {
    this.finalizeInteraction();
    this.isActive = false;
    this.phase = "idle";
    this.volume = 0;
    this.transcript = "";
    this.liveText = "";
    this.systemMessage = "";
    this.activeTier = "";
    this.isStarting = false;
    this.errorMsg = "";

    this.cmdBuffer = "";
    this.isWaitingForAction = false;
  },

  clearHistory() {
    this.history = [];
    // If we're not speaking/thinking, just reset everything
    if (this.phase !== "speaking" && this.phase !== "thinking") {
       this.reset();
    }
  },

  newChat() {
    this.reset(); // Finalize current first
    this.clearHistory(); // Then wipe everything clean
    this.isActive = false;
  }
});
