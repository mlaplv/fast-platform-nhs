import { untrack, setContext, getContext } from "svelte";
import { NANOBOT_KEY } from "./context_keys";
import { apiClient } from "$lib/utils/apiClient";
import { createChatState } from "./chat.svelte";
import { goto } from "$app/navigation";
import { getNotificationState } from "./notification.svelte";
import { createVaultState } from "./vault.svelte";
import { createVoiceState } from "./voice.svelte";
import { createUiState } from "./ui.svelte";
import { createLogState } from "./log.svelte";
import { createTrainingState } from "./training_state.svelte";
import { createIntentManager } from "./intent_manager.svelte";
import { vuiState, vuiController } from "$lib/vui";
import { permissionState } from "./permissions.svelte";
import { normalizeVn } from "$lib/utils/text";

import { normalizeAssets, SIGNAL_THROTTLE_MS, THINKING_TIMEOUT_MS } from "./nanobot/utils";
import { sanitizeId } from "./utils";
import { createAudioThrottle } from "./nanobot/audio_throttle";
import { isAdminDomain } from "./nanobot/env";
import { createResumeManager } from "./nanobot/resume";
import { createPulseManager } from "./nanobot/pulse";

import { createSyncManager } from "./nanobot/sync";
import { playTacticalPurge } from "$lib/utils/sfx";

export * from "./types";
import type { WidgetType, Suggestion, CommandAction, ToastType, ChatSettings, CommandVerb, CommandEntity, SystemLog, CampaignData } from "./types";


// Elite V2.2: Context Isolation Protocol
export type NanobotState = ReturnType<typeof createNanobotState>;
let _globalNanobotState: NanobotState | null = null;

export function createNanobotState() {
  const log = createLogState();
  const ui = createUiState();
  const voice = createVoiceState(log.addLog);
  const chat = createChatState(log.addLog, ui.showToast);
  const notification = getNotificationState();
  const vault = createVaultState(log.addLog);
  const training = createTrainingState(voice);

  const state = $state({
    activeWidget: "NONE" as WidgetType,
    commandAction: null as CommandAction | null,
    showMobileSidebar: false,
    nanoBotStatus: "IDLE" as NanoBotState,
    modality: "text" as "text" | "voice",
    currentData: null as CampaignData | null,
    isBusy: false,
    godModeUser: undefined as string | undefined,
    wakeWords: ["xohi"] as string[],
    sleepWords: ["tạm biệt"] as string[],
    isCampaignMode: false,
    isTogglingCampaign: false,
    isHydrated: false,
    chatSettings: {
      selective_persistence: true,
      save_ai_responses: false,
      auto_purge_days: 30,
      cache_limit: 10
    } as ChatSettings,
    agenticSuggestions: [
      { label: "Quản lý User", command: "manage users" },
      { label: "Quản lý Quyền", command: "manage permissions" },
      { label: "Tạo sản phẩm", command: "tạo sản phẩm mới" },
      { label: "Thêm danh mục", command: "thêm danh mục" },
      { label: "Xem đơn hàng", command: "mở đơn hàng" },
      { label: "Viết Bài viết", command: "tạo Bài viết" },
      { label: "Đào tạo Helen", command: "mở tri thức helen" },
      { label: "Quản lý Voucher", command: "mở voucher" },
      { label: "Quản lý CTV", command: "manage ctv" },
    ] as Suggestion[],
    mobileScrollPosition: 0,
    isExpanded: false,
    sttAnchors: [] as string[],
    micSensitivity: 0.6,
    audioUnlocked: false,
    signalQueue: [] as string[],
    isResumingManually: false,
    lastMessageHash: "" as string,
    discoveredModels: ["gemini-2.0-flash", "gemini-2.0-flash-lite-preview-02-05", "gemini-1.5-pro", "gemini-1.5-flash"] as string[],
    dynamicIntentMap: {} as Record<string, string>,
    // IntentManager Tracking
    lastProcessedCommand: "",
    lastProcessedTime: 0,
    lastSpokenText: "",
    lastSpokenTime: 0,
    commandEpoch: 0,
    lastSuggestedWidget: undefined as WidgetType | undefined,
    // Support Inbox Sync State (Elite V2.2)
    supportSearchTerm: "",
    supportRefreshToggle: 0,
    activeSupportSessionCount: 0,
    // Brain Hub Control State (V2.2)
    isBrainSyncing: false,
    brainActionTrigger: "NONE" as "NONE" | "SYNC" | "PURGE",
    brainTotalNodes: 0,
    brainVectorHealth: 0,
    brainDuplicatesCount: 0,
    brainUptime: 0,
    brainLastSync: 0,
    brainVectorEngine: "trinity_core_v2.2",
    brainStabilityScore: 100,
    brainCoverage: 0,
    brainManualOpen: false,
    liveStreamBuffer: "" as string, // CNS V86.5: Real-time neural stream buffer
    watermarkEditor: {
      show: false,
      asset: null as MediaAsset | null,
      assetId: null as string | null,
      onApply: null as ((params: Record<string, unknown>) => void) | null,
      logoEnabled: true,
      textEnabled: false,
      text: "",
      textColor: "#FFFFFF"
    }
  });

  const audioThrottle = createAudioThrottle(state);

  let thinkingWatchdog: ReturnType<typeof setTimeout> | undefined;
  const resetVui = () => { state.nanoBotStatus = "IDLE"; state.isBusy = false; voice.resetVui(); };
  const softReset = () => { if (state.nanoBotStatus !== "ERROR") state.nanoBotStatus = "IDLE"; state.isBusy = false; voice.softReset(); };

  const setThinking = (val: boolean, source: "text" | "voice" = "text") => {
    if (val) {
      if (source === "voice") state.nanoBotStatus = "THINKING";
      clearTimeout(thinkingWatchdog);
      thinkingWatchdog = setTimeout(() => {
        if (state.nanoBotStatus === "THINKING") {
          state.nanoBotStatus = "ERROR";
          voice.setStatus("ERROR");
          setTimeout(() => resetVui(), 4000);
        }
      }, THINKING_TIMEOUT_MS);
    } else { clearTimeout(thinkingWatchdog); }
  };

  const setDynamicIntentMap = (val: Record<string, string>) => { state.dynamicIntentMap = val; };

  const intent = createIntentManager(state, voice, log, ui, chat, resetVui, softReset, setThinking);
  const resumeManager = createResumeManager(state, intent, { ...log, setActivityLogs: log.setActivityLogs }, ui, chat, () => sync.startSmartPolling());
  const pulseManager = createPulseManager(state, voice, log, ui, vuiState, notification, chat, () => sync.startSmartPolling());
  const sync = createSyncManager(state, log, chat, notification, ui, setDynamicIntentMap, resumeManager, pulseManager);

  // Lifecycle
  if (typeof window !== "undefined") {
    window.addEventListener('mousedown', () => {
      if (!state.audioUnlocked) {
        state.audioUnlocked = true;
        audioThrottle.flushSignalQueue();
      }
    }, { once: true });

    $effect.root(() => {
      if (!isAdminDomain()) return;

      // $effect for automatic hydration removed for P1 Optimization (Lazy Load)
      // Hydration is now explicitly called via nanobot.forceHydration() in Shell components (DesktopLayout / MobileShell)

      $effect(() => {
        const isBusy = state.isBusy || state.nanoBotStatus !== "IDLE" || state.isCampaignMode || voice.isVuiActive;
        const hasAuth = !!permissionState.user;
        untrack(() => {
          if (hasAuth) {
            pulseManager.handleBusyState(isBusy);
          } else {
            pulseManager.disconnectPulse();
          }
        });
      });
    });
  }

  return {
    get activityLogs() { return log?.activityLogs || []; },
    get chatHistory() { return chat?.history || []; },
    get activeWidget() { return state?.activeWidget || "NONE"; },
    get currentData() { return state?.currentData || {}; },
    get nanoBotStatus() { return state?.nanoBotStatus || "IDLE"; },
    get isCampaignMode() { return state?.isCampaignMode || false; },
    get isTogglingCampaign() { return state?.isTogglingCampaign || false; },
    get isBusy() { return state?.isBusy || false; },
    get godModeUser() { return state?.godModeUser || null; },
    get modality() { return state?.modality || "text"; },
    get wakeWords() { return state?.wakeWords || ["xohi"]; },
    get sleepWords() { return state?.sleepWords || ["tạm biệt"]; },
    get sttAnchors() { return state?.sttAnchors || []; },
    get micSensitivity() { return state?.micSensitivity || 0.6; },
    get agenticSuggestions() { return state.agenticSuggestions; },
    get chatPagination() { return chat.pagination; },
    get commandAction() { return state.commandAction; },
    get dynamicIntentMap() { return state.dynamicIntentMap; },
    get supportSearchTerm() { return state.supportSearchTerm; },
    setSupportSearchTerm: (val: string) => { state.supportSearchTerm = val; },
    get supportRefreshToggle() { return state.supportRefreshToggle; },
    triggerSupportRefresh: () => { state.supportRefreshToggle++; },
    get activeSupportSessionCount() { return state.activeSupportSessionCount; },
    setActiveSupportSessionCount: (val: number) => { state.activeSupportSessionCount = val; },

    // Brain Hub Getters/Setters
    get brainTotalNodes() { return state.brainTotalNodes; },
    set brainTotalNodes(val: number) { state.brainTotalNodes = val; },
    get brainVectorHealth() { return state.brainVectorHealth; },
    set brainVectorHealth(val: number) { state.brainVectorHealth = val; },
    get brainDuplicatesCount() { return state.brainDuplicatesCount; },
    set brainDuplicatesCount(val: number) { state.brainDuplicatesCount = val; },
    get brainUptime() { return state.brainUptime; },
    set brainUptime(val: number) { state.brainUptime = val; },
    get brainLastSync() { return state.brainLastSync; },
    set brainLastSync(val: number) { state.brainLastSync = val; },
    get brainVectorEngine() { return state.brainVectorEngine; },
    set brainVectorEngine(val: string) { state.brainVectorEngine = val; },
    get brainStabilityScore() { return state.brainStabilityScore; },
    set brainStabilityScore(val: number) { state.brainStabilityScore = val; },
    get brainCoverage() { return state.brainCoverage; },
    set brainCoverage(val: number) { state.brainCoverage = val; },
    get brainManualOpen() { return state.brainManualOpen; },
    setBrainManualOpen: (val: boolean) => { state.brainManualOpen = val; },
    get isBrainSyncing() { return state.isBrainSyncing; },
    set isBrainSyncing(val: boolean) { state.isBrainSyncing = val; },
    get brainActionTrigger() { return state.brainActionTrigger; },
    set brainActionTrigger(val: "NONE" | "SYNC" | "PURGE") { state.brainActionTrigger = val; },

    processCommand: (command: string, source: "text" | "voice" = "text", intentData?: Record<string, unknown>) => intent.processCommand(command, source, intentData),
    setVoiceResult: intent.setVoiceResult,
    resetVui,
    setThinking,
    setModality: (val: "text" | "voice") => { state.modality = val; },
    setGodModeUser: (val: string | undefined) => { state.godModeUser = sanitizeId(val) || undefined; },
    clearCurrentData: () => { state.currentData = null; },
    updateCurrentData: (newData: Partial<CampaignData>) => {
      if (state.currentData) {
        state.currentData = { ...state.currentData, ...newData } as CampaignData;
      } else {
        state.currentData = newData as CampaignData;
      }
    },
    clearCommandAction: () => { state.commandAction = null; },
    consumeCommand: (verb: CommandVerb, entity: CommandEntity | "media") => {
      if (state.commandAction && state.commandAction.verb === verb && state.commandAction.entity === entity) {
        state.commandAction = { ...state.commandAction, consumed: true };
        // Tự động xóa sau 500ms để tránh UI nhấp nháy hoặc xử lý lại khi component re-render
        setTimeout(() => {
          if (state.commandAction?.consumed) state.commandAction = null;
        }, 500);
        return true;
      }
      return false;
    },
    forceHydration: () => {
      // V70.2 Fix: Manual trigger for soft navigation (goto)
      state.isHydrated = true;
      sync.initHydration();
    },

    // Auth & Identity
    get userName() { return permissionState.userName || "Khách hàng"; },
    get userEmail() { return permissionState.user; },
    setUserEmail: (val: string) => { permissionState.user = val; },
    setUserName: (val: string) => { permissionState.userName = val; },
    setUserRole: (val: string) => { permissionState.roles = [val]; },
    // Voice, UI & Chat
    get voice() { return voice; },
    get ui() { return ui; },
    get chat() { return chat; },
    get isVuiActive() { return voice.isVuiActive; },
    get isSpeaking() { return voice.isProcessingSpeech; },
    get vuiResponse() { return voice.vuiResponse; },
    get vuiUserQuery() { return voice.vuiUserQuery; },
    get voiceTrigger() { return voice.voiceTrigger; },
    setVuiActive: voice.setVuiActive,
    clearVuiResponse: voice.clearVuiResponse,

    startRecording: (auto?: boolean) => vuiController.startRecording(auto),
    stopRecording: () => vuiController.stopRecording(),
    interruptAll: () => vuiController.interruptAll(),
    speak: (text: string) => vuiController.speak(text),

    softClose: () => {
      voice.setVuiActive(false);
      ui.setUniversalModalOpen(false);
      state.activeWidget = "NONE";
      voice.clearVuiResponse();
      // Optional: small tick SFX here if needed, but usually UI close is enough
    },

    hardKill: async (campaignId?: string) => {
      // CNS V86.3: Type-safe campaign ID extraction
      const vuiData = voice.vuiResponse?.data as CampaignData | undefined;
      const cid = campaignId || vuiData?.campaign_id || vuiData?.id;

      // 1. Play tactical purge SFX immediately for instant feedback
      playTacticalPurge();

      // 2. Hide UI
      voice.setVuiActive(false);
      ui.setUniversalModalOpen(false);
      state.activeWidget = "NONE";
      state.isBusy = false;
      state.nanoBotStatus = "IDLE";
      voice.clearVuiResponse();

      // 3. Signal backend if we have a campaign ID
      if (typeof cid === 'string') {
        try {
          await apiClient.post(`/api/v1/content/campaigns/${cid}/cancel`);
          ui.showToast("Tiến trình đã được ngắt khẩn cấp.", "success");
        } catch (e) {
          console.error("[HardKill] Signal failed:", e);
        }
      }

      // 4. Full Reset
      voice.clearVuiResponse();
      resetVui();
    },

    // 5. Total Disposal (CNS V82.11 Root Cause Fix)
    fullPurge: (campaignId?: string) => {
      // CNS V86.3: Type-safe currentData extraction
      const currentData = state.currentData;
      const activeCid = (currentData as CampaignData)?.campaign_id || (currentData as CampaignData)?.id;

      // If a specific ID is provided and it doesn't match active, we just clear logs (handled by Pulse)
      // If no ID or it matches, we Wipe Everything.
      if (!campaignId || campaignId === activeCid) {
        state.currentData = null;
        state.activeWidget = "NONE";
        ui.setUniversalModalOpen(false);
        voice.clearVuiResponse();
        state.liveStreamBuffer = "";
        resetVui();

        // CNS V82.11: Hard Purge Global Image Store
        import("$lib/state/xohiImage.svelte").then(({ xohiImageStore }) => {
          if (xohiImageStore && typeof xohiImageStore.clearAll === 'function') {
            xohiImageStore.clearAll();
          }
        });
      }
    },

    // 6. Neural Stream Management (Elite V2.2)
    get liveStreamBuffer() { return state.liveStreamBuffer; },
    appendStreamChunk: (text: string) => { state.liveStreamBuffer += text; },
    clearStreamBuffer: () => { state.liveStreamBuffer = ""; },
    
    // Watermark Control
    get watermarkEditor() { return state.watermarkEditor; },
    openWatermarkEditor: (asset: MediaAsset, onApply: (params: Record<string, unknown>) => void) => {
      state.watermarkEditor.asset = asset;
      state.watermarkEditor.assetId = asset?.id || null;
      state.watermarkEditor.onApply = onApply;
      state.watermarkEditor.show = true;
    },
    closeWatermarkEditor: () => {
      state.watermarkEditor.show = false;
    },

    get universalModalOpen() { return ui.universalModalOpen; },
    get confirmDialog() { return ui.confirmDialog; },
    get toasts() { return ui.toasts; },
    showToast: (message: string, type: ToastType = "info", duration = 4000) => {
      ui.showToast(message, type, duration);
      if (type !== "success" && message !== state.lastMessageHash) {
        state.lastMessageHash = message;
        setTimeout(() => { if (state.lastMessageHash === message) state.lastMessageHash = ""; }, SIGNAL_THROTTLE_MS);
        if (state.audioUnlocked && (Date.now() - audioThrottle.lastSpeakTime > SIGNAL_THROTTLE_MS) && state.signalQueue.length === 0) {
          audioThrottle.setLastSpeakTime(Date.now());
          import("$lib/vui").then(({ vuiController }) => vuiController.speak(`Dạ, em đang báo cáo ${type} cho ${permissionState.userName} đây ạ.`));
        } else {
          state.signalQueue = [...state.signalQueue, message];
          audioThrottle.scheduleFlush();
        }
      }
    },
    removeToast: ui.removeToast,
    showConfirm: ui.showConfirm,
    setUniversalModalOpen: ui.setUniversalModalOpen,
    showUniversalModal: () => ui.setUniversalModalOpen(true),
    closeUniversalModal: () => { ui.setUniversalModalOpen(false); state.activeWidget = "NONE"; },
    openWidget: (widget: WidgetType, data?: CampaignData) => {
      state.activeWidget = widget;
      if (data) state.currentData = data;
      ui.setUniversalModalOpen(true);
    },

    // HUD & Tips
    get activeHudPopup() { return ui.activeHudPopup; },
    get showQuickTips() { return ui.showQuickTips; },
    toggleHudPopup: (val: string) => { ui.activeHudPopup = ui.activeHudPopup === val ? null : val; },
    toggleQuickTips: () => { ui.showQuickTips = !ui.showQuickTips; },

    // Training
    get training() { return training; },
    get isTraining() { return training.isTraining; },
    get trainingType() { return training.trainingType; },
    get trainingResult() { return training.trainingResult; },
    setTraining: training.setTraining,
    cancelTraining: training.cancelTraining,

    // Vault
    get vault() { return vault; },
    get pendingApprovals() { return vault.pendingApprovals; },
    approveAction: vault.approveAction,
    denyAction: vault.denyAction,

    // Notifications
    get notification() { return notification; },
    get notifications() { return notification.notifications; },
    get unreadNotificationsCount() { return notification.unreadCount; },
    markNotificationAsRead: notification.markNotificationAsRead,
    fetchNotifications: notification.fetchNotifications,

    // Logs & Chat
    addLog: log.addLog,
    get expandedLog() { return log.expandedLog; },
    showFullLog: log.showFullLog,
    closeFullLog: log.closeFullLog,
    startPolling: () => sync.startSmartPolling(),
    stopPolling: () => sync.stopSmartPolling(),
    get latestResumeableLog() { return resumeManager.latestResumeableLog; },

    loadMoreMessages: () => chat.loadMoreMessages((logs: SystemLog[]) => {
      log.upsertLogs(logs);
    }, "account", state.godModeUser || undefined),
    syncSessionFromDb: async () => {
      log.setActivityLogs([]);
      await chat.hydrateHistory("account", (logs: SystemLog[]) => {
        log.upsertLogs(logs);
      }, state.godModeUser || undefined);
      ui.showToast(state.godModeUser ? `Đồng bộ log [V69.0]: ${state.godModeUser}` : "Đã đồng bộ dữ liệu V69.0 (Unified)", "success");
    },
    clearChatLogs: async () => { if (await chat.clearHistory("account", state.godModeUser || undefined)) { log.setActivityLogs([]); ui.showToast("Dữ liệu đã được quét sạch", "success"); } },

    // Layout Context
    get screenContext() {
      return {
        current_route: typeof window !== "undefined" ? window.location.pathname : "/",
        active_widget: state.activeWidget,
        active_data: state.currentData
      } as import("./types").ScreenContext & { active_data: CampaignData | Record<string, unknown> | null };
    },
    get heartbeatCollapsed() { return ui.heartbeatCollapsed; },
    toggleHeartbeat: () => {
      if (typeof window === "undefined") return;
      ui.heartbeatCollapsed = !ui.heartbeatCollapsed;
    },
    get showMobileSidebar() { return state.showMobileSidebar; },
    get showMobileDrawer() { return state.showMobileSidebar; },
    toggleMobileSidebar: () => { state.showMobileSidebar = !state.showMobileSidebar; },
    toggleMobileDrawer: () => { state.showMobileSidebar = !state.showMobileSidebar; },
    get mobileScrollPosition() { return state.mobileScrollPosition; },
    setMobileScrollPosition: (val: number) => { state.mobileScrollPosition = val; },
    get isExpanded() { return state.isExpanded; },
    toggleExpand: (val?: boolean) => { state.isExpanded = val !== undefined ? val : !state.isExpanded; if (typeof window !== "undefined") document.body.style.overflow = state.isExpanded ? "hidden" : ""; },

    // Settings
    updateVoiceSettings: (wake: string[], sleep: string[], greeting: string, farewell: string, campaign: boolean, chatSettings?: Record<string, unknown>, sttAnchors?: string[], micSensitivity?: number) => {
      state.wakeWords = wake; state.sleepWords = sleep; voice.setGreetingTemplate(greeting); voice.setFarewellTemplate(farewell); state.isCampaignMode = campaign;
      if (chatSettings) state.chatSettings = { ...state.chatSettings, ...chatSettings }; if (sttAnchors) state.sttAnchors = sttAnchors; if (micSensitivity !== undefined) state.micSensitivity = micSensitivity;
    },
    toggleCampaignMode: async () => {
      if (state.isTogglingCampaign) return;
      state.isTogglingCampaign = true;
      const originalMode = state.isCampaignMode;
      try {
        state.isCampaignMode = !originalMode;
        await apiClient.post("/api/v1/settings/voice", { is_campaign_mode: state.isCampaignMode });
        ui.showToast(state.isCampaignMode ? "Fortress Mode: ENGAGED" : "Fortress Mode: STANDBY", "success");
      } catch (e) { state.isCampaignMode = originalMode; ui.showToast("Neural link sync failed", "error"); }
      finally { state.isTogglingCampaign = false; }
    },
    get discoveredModels() { return state.discoveredModels; },
    setDiscoveredModels: (val: string[]) => { state.discoveredModels = val; },
    setDynamicIntentMap: (val: Record<string, string>) => { state.dynamicIntentMap = val; },
    resumeCampaign: (logEntry: SystemLog | CampaignData) => resumeManager.internalResumeCampaign(logEntry, false)
  };
}



export function setNanobotContext() {
  const state = createNanobotState();
  _globalNanobotState = state;
  return setContext(NANOBOT_KEY, state);
}

export function useNanobot(): NanobotState {
  try {
    const state = getContext(NANOBOT_KEY) as NanobotState;
    if (state) return state;
  } catch (e) {
    // Suppress lifecycle_outside_component
  }
  
  if (_globalNanobotState) return _globalNanobotState;

  // Elite V2.2: Placeholder Proxy to prevent crashes during module evaluation
  return new Proxy({} as NanobotState, {
    get: (target, prop) => {
      if (_globalNanobotState) return _globalNanobotState[prop as keyof NanobotState];
      console.warn(`[Nanobot] Accessing property '${String(prop)}' before initialization.`);
      return undefined;
    }
  });
}

export function getNanobot(): NanobotState {
  if (!_globalNanobotState) {
    // Elite V2.2: Resilience check — If called during module eval, return proxy or throw descriptive error
    console.warn("[Nanobot] getNanobot called before initialization. This may be a circular dependency.");
    return {} as NanobotState; 
  }
  return _globalNanobotState;
}
