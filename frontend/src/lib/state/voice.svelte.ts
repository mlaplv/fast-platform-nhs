import type { CampaignData } from "./types";
import { safeRandomUUID } from "./utils";
import { permissionState } from "./permissions.svelte";

export type VoiceStatus = "IDLE" | "VOICE" | "THINKING" | "ERROR" | "SUCCESS";

export function createVoiceState(
  addLog: (msg: string, source?: string, type?: string, routerTier?: string | number, data?: CampaignData | Record<string, unknown>) => void,
) {
  const state = $state({
    isVuiActive: false,
    vuiResponse: null as {
      text: string;
      type: "greeting" | "answer" | "action" | "error";
      data?: CampaignData | Record<string, unknown>;
    } | null,
    vuiUserQuery: "",
    voiceTrigger: 0,
    status: "IDLE" as VoiceStatus,
    isProcessingSpeech: false,
    routerTier: undefined as string | number | undefined,
    greetingTemplate: `Tôi đây thưa ${permissionState.userName || "bạn"} ✨`, // V57.5 Dynamic
    farewellTemplate: `Tạm biệt ${permissionState.userName || "bạn"}`,
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
    data?: Record<string, unknown>,
    source: "text" | "voice" = "text",
    routerTier?: string | number,
  ) {
    state.vuiUserQuery = transcript;

    // Phase 82: CNS Sanitization — Đảm bảo data cho ContentReview không bao giờ chứa undefined
    const cleanData = data || {};
    if (cleanData.category === "CONTENT_CREATE" || cleanData.campaign_id) {
      cleanData.step = cleanData.step ?? 1;
      cleanData.status = cleanData.status ?? "IDLE";
      cleanData.progress_msg = cleanData.progress_msg ?? "";
      cleanData.keywords = cleanData.keywords ?? {};
      cleanData.assets = cleanData.assets ?? [];
      cleanData.outline = cleanData.outline ?? {};
      cleanData.draft_content = cleanData.draft_content ?? "";
    }

    state.vuiResponse = {
      text: responseText,
      type: uiAction ? "action" : "answer",
      data: cleanData,
    };
    state.routerTier = routerTier;

    // Elite 2026: Centralized UI activation for campaign items
    if (cleanData.category === "CONTENT_CREATE" || cleanData.campaign_id) {
       import("$lib/vui").then(({ vuiState }) => vuiState.showCampaign = true);
    }

    // Phase 45/62: Deactivation Logic
    if (source === "voice" && !data?.isSilent) {
      state.status = "VOICE";
      state.isVuiActive = true;
    } else {
      state.status = "SUCCESS";
      // ONLY close if we are not already in a VUI session (Fix Flicker)
      if (source === "text" && !state.isVuiActive) {
         state.isVuiActive = false;
      }
      
      if (data?.isSilent) {
        import("$lib/vui").then(({ vuiState }) => vuiState.setActive(true));
      }
    }
  }

  async function handleWakeWord(source: "text" | "voice" = "voice") {
    // Phase 6: Race Condition Guard
    if (state.isVuiActive || state.status !== "IDLE" || state.isProcessingSpeech) return;
    
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
