import { safeRandomUUID } from "./utils";

export type VoiceStatus = "IDLE" | "VOICE" | "THINKING" | "ERROR" | "SUCCESS";

export function createVoiceState(
  addLog: (msg: string, source?: string, type?: string, routerTier?: number, data?: Record<string, any>) => void,
) {
  const state = $state({
    isVuiActive: false,
    vuiResponse: null as {
      text: string;
      type: "greeting" | "answer" | "action" | "error";
      data?: Record<string, any>;
    } | null,
    vuiUserQuery: "",
    voiceTrigger: 0,
    status: "IDLE" as VoiceStatus,
    isProcessingSpeech: false,
    routerTier: undefined as number | undefined,
    greetingTemplate: "Tôi đây thưa bạn ✨", // V57.5
    farewellTemplate: "Tạm biệt",
  });

  function resetVui() {
    state.status = "IDLE";
    state.vuiResponse = null;
    state.vuiUserQuery = "";
    state.isVuiActive = false;
    state.isProcessingSpeech = false;
    state.routerTier = undefined;
    
    // Rule R82.12: Nuclear Reset Cleanup
    import("$lib/vui").then(({ vuiState, vuiController }) => {
      vuiState.reset();
      vuiController.interruptAll();
    });
    console.warn("[VoiceState] Nuclear Reset complete.");
  }

  function softReset() {
    // Phase 61: Surgical cleanup without aggressive logs/interrupts
    state.vuiResponse = null;
    state.vuiUserQuery = "";
    if (state.status !== "IDLE") state.status = "IDLE";
    
    // Only interrupt if actually active to avoid SSE/Pulse flapping
    if (state.isVuiActive || state.isProcessingSpeech) {
       resetVui();
    }
  }

  function setVoiceResult(
    transcript: string,
    responseText: string,
    uiAction: string,
    data?: Record<string, any>,
    source: "text" | "voice" = "text",
    routerTier?: number,
  ) {
    state.vuiUserQuery = transcript;
    state.vuiResponse = {
      text: responseText,
      type: uiAction ? "action" : "answer",
      data,
    };
    state.routerTier = routerTier;

    // R51: CHỈ kích hoạt VUI khi là voice
    if (source === "voice") {
      state.status = "VOICE";
      state.isVuiActive = true;
    } else {
      state.status = "SUCCESS";
      state.isVuiActive = false;
    }
  }

  async function handleWakeWord(source: "text" | "voice" = "voice") {
    if (source === "text") {
      addLog(state.greetingTemplate, "XOHI");
      state.status = "SUCCESS";
      state.vuiResponse = { text: state.greetingTemplate, type: "greeting" };
    } else {
      state.isVuiActive = true;
      const { vuiController } = await import("$lib/vui");
      vuiController.speak(state.greetingTemplate);
      state.voiceTrigger += 1;
    }
  }

  function hard_sleep() {
    import("$lib/vui").then(({ vuiController }) => {
      vuiController.interruptAll();
      resetVui();
      addLog(
        "TERMINATE_SESSION: Hardware lock released.",
        "Nanobot-Core",
        "warning",
      );
    });
  }

  return {
    get isVuiActive() {
      return state.isVuiActive;
    },
    get vuiResponse() {
      return state.vuiResponse;
    },
    get vuiUserQuery() {
      return state.vuiUserQuery;
    },
    get voiceTrigger() {
      return state.voiceTrigger;
    },
    get status() {
      return state.status;
    },
    get isProcessingSpeech() {
      return state.isProcessingSpeech;
    },
    get routerTier() {
      return state.routerTier;
    },

    setVuiActive: (val: boolean) => (state.isVuiActive = val),
    setVuiUserQuery: (val: string) => (state.vuiUserQuery = val),
    setProcessingSpeech: (val: boolean) => {
      state.isProcessingSpeech = val;
      if (val) state.status = "VOICE";
    },
    setStatus: (val: VoiceStatus) => (state.status = val),
    clearVuiResponse: () => {
      state.vuiResponse = null;
      state.vuiUserQuery = "";
    },
    resetVui,
    softReset,
    setVoiceResult,
    handleWakeWord,
    hard_sleep,
    get greetingTemplate() {
      return state.greetingTemplate;
    },
    setGreetingTemplate: (val: string) => (state.greetingTemplate = val),
    get farewellTemplate() {
      return state.farewellTemplate;
    },
    setFarewellTemplate: (val: string) => (state.farewellTemplate = val),
    triggerVoice: (showVui: boolean = false) => {
      if (showVui) state.isVuiActive = true;
      state.voiceTrigger += 1;
    },
  };
}
