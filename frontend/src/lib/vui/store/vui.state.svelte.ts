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
  speechProb: 0,
  transcript: "",
  liveText: "",
  isLiveTextStable: false,
  systemMessage: "",
  isStarting: false,
  errorMsg: "",
  activeTier: "",
  cmdBuffer: "",
  isAudioBlocked: false,

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
    if (val === "listening" || val === "idle") {
        this.errorMsg = "";
        this.speechProb = 0;
    }
  },
  setVolume(val: number) { this.volume = val; },
  setSpeechProb(val: number) { this.speechProb = val; },
  setTranscript(val: string) { this.transcript = val; },
  setLiveText(val: string, stable = false) {
    this.liveText = val;
    this.isLiveTextStable = stable;
  },
  setSystemMessage(val: string) { this.systemMessage = val; },
  setStartingLock(val: boolean) { this.isStarting = val; },
  setError(msg: string) {
    this.phase = "error";
    this.errorMsg = msg;
  },
  setActiveTier(val: string) { this.activeTier = val; },
  setCmdBuffer(val: string) { this.cmdBuffer = val; },
  setAudioBlocked(val: boolean) { this.isAudioBlocked = val; },

  /**
   * Phase 76.3.3: Visual Continuity Shield
   * Ensures that when we push to history, the UI doesn't "blink" due to clearing liveText too early.
   */
  finalizeInteraction() {
    const hasContent = this.transcript || this.liveText || this.systemMessage;
    if (hasContent) {
        // Use a stable ID for Svelte list diffing performance
        const interactionId = `vui_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`;

        this.history.push({
            id: interactionId,
            userQuery: (this.transcript || this.liveText || "").trim(),
            aiResponse: (this.systemMessage || "").trim(),
            duration: 0
        });

        // Rule: Limit history size to prevent memory leaks on 2GB RAM systems
        if (this.history.length > 30) {
          this.history.shift();
        }

        // Clear buffers
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
