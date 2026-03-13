import { untrack } from "svelte";
import { apiClient } from "$lib/utils/apiClient";
import { createChatState } from "./chat.svelte";
import { createNotificationState } from "./notification.svelte";
import { createVaultState } from "./vault.svelte";
import { createVoiceState } from "./voice.svelte";
import { createUiState } from "./ui.svelte";
import { createLogState } from "./log.svelte";
import { createTrainingState } from "./training_state.svelte";
import { createIntentManager } from "./intent_manager.svelte.ts";
import { vuiState, vuiController } from "$lib/vui";
import { permissionState } from "./permissions.svelte";
import { normalizeVn } from "$lib/utils/text";

import { normalizeAssets, SIGNAL_THROTTLE_MS, THINKING_TIMEOUT_MS } from "./nanobot/utils";
import { createAudioThrottle } from "./nanobot/audio_throttle";
import { createResumeManager } from "./nanobot/resume";
import { createPulseManager } from "./nanobot/pulse";

import { createSyncManager } from "./nanobot/sync";

export * from "./types";
import type { WidgetType, Suggestion, CommandAction, ToastType } from "./types";

export function createNanobotState() {
  const log = createLogState();
  const ui = createUiState();
  const voice = createVoiceState(log.addLog);
  const chat = createChatState(log.addLog, ui.showToast);
  const notification = createNotificationState();
  const vault = createVaultState(log.addLog);
  const training = createTrainingState(voice);

  const state = $state({
    activeWidget: "NONE" as WidgetType,
    commandAction: null as CommandAction | null,
    showMobileSidebar: false,
    nanoBotStatus: "IDLE" as "IDLE" | "THINKING" | "ERROR" | "SUCCESS" | "VOICE" | "PROCESSING",
    modality: "text" as "text" | "voice",
    currentData: null as Record<string, unknown> | null,
    isBusy: false,
    godModeUser: null as string | null,
    wakeWords: ["xohi"] as string[],
    sleepWords: ["tạm biệt"] as string[],
    isCampaignMode: false,
    isTogglingCampaign: false,
    isHydrated: false,
    chatSettings: { selective_persistence: true, save_ai_responses: false, auto_purge_days: 30, cache_limit: 10 } as Record<string, any>,
    agenticSuggestions: [
      { label: "Quản lý User", command: "manage users" },
      { label: "Quản lý Quyền", command: "manage permissions" },
      { label: "Tạo sản phẩm", command: "tạo sản phẩm mới" },
      { label: "Thêm danh mục", command: "thêm danh mục" },
      { label: "Xem đơn hàng", command: "mở đơn hàng" },
      { label: "Viết tin tức", command: "tạo tin tức" },
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

  const intent = createIntentManager(state, voice, log, ui, chat, resetVui, softReset, setThinking);
  const resumeManager = createResumeManager(state, voice, log, ui, () => sync.startSmartPolling());
  const pulseManager = createPulseManager(state, voice, log, ui, vuiState, notification, () => sync.startSmartPolling());
  const sync = createSyncManager(state, log, chat, notification, ui, resumeManager, pulseManager);

  // Lifecycle
  if (typeof window !== "undefined") {
    window.addEventListener('mousedown', () => {
      if (!state.audioUnlocked) {
        state.audioUnlocked = true;
        audioThrottle.flushSignalQueue();
      }
    }, { once: true });

    $effect.root(() => {
      $effect(() => {
        if (permissionState.isInitialized) untrack(() => {
          if (window.location.pathname.includes("/login") || (state.isHydrated && log.activityLogs.length > 0)) return;
          state.isHydrated = true;
          sync.initHydration();
        });
      });

      $effect(() => {
        const isBusy = state.isBusy || state.nanoBotStatus !== "IDLE" || state.isCampaignMode || voice.isVuiActive;
        untrack(() => pulseManager.handleBusyState(isBusy));
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

    processCommand: intent.processCommand,
    setVoiceResult: intent.setVoiceResult,
    resetVui,
    setThinking,
    setModality: (val: "text" | "voice") => (state.modality = val),
    setGodModeUser: (val: string | null) => (state.godModeUser = val),
    clearCurrentData: () => (state.currentData = null),
    clearCommandAction: () => (state.commandAction = null),
    forceHydration: () => {
      // V70.2 Fix: Manual trigger for soft navigation (goto)
      state.isHydrated = true;
      sync.initHydration();
    },

    // Auth & Identity
    get userName() { return permissionState.userName || "Sếp"; },
    get userEmail() { return permissionState.user; },
    setUserEmail: (val: string) => { permissionState.user = val; },
    setUserName: (val: string) => { permissionState.userName = val; },
    setUserRole: (val: string) => { permissionState.roles = [val]; },
    // Voice & UI
    get voice() { return voice; },
    get ui() { return ui; },
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
    openWidget: (widget: WidgetType, data?: any) => { state.activeWidget = widget; if (data) state.currentData = data; ui.setUniversalModalOpen(true); },

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
    
    loadMoreMessages: () => chat.loadMoreMessages((logs: any) => {
      log.upsertLogs(logs);
    }, "account", state.godModeUser || undefined),
    syncSessionFromDb: async () => {
      log.setActivityLogs([]);
      await chat.hydrateHistory("account", (logs: any) => {
        log.upsertLogs(logs);
      }, state.godModeUser || undefined);
      ui.showToast(state.godModeUser ? `Đồng bộ log [V69.0]: ${state.godModeUser}` : "Đã đồng bộ dữ liệu V69.0 (Unified)", "success");
    },
    clearChatLogs: async () => { if (await chat.clearHistory("account")) { log.setActivityLogs([]); ui.showToast("Dữ liệu đã được quét sạch", "success"); } },

    // Layout Context
    get screenContext() { return { current_route: typeof window !== "undefined" ? window.location.pathname : "/", active_widget: state.activeWidget, active_data: state.currentData }; },
    get heartbeatCollapsed() { return ui.heartbeatCollapsed; },
    toggleHeartbeat: () => { if (typeof window === "undefined") return; if (ui.heartbeatCollapsed === null) ui.heartbeatCollapsed = window.innerWidth >= 1280; else ui.heartbeatCollapsed = !ui.heartbeatCollapsed; },
    get showMobileSidebar() { return state.showMobileSidebar; },
    get showMobileDrawer() { return state.showMobileSidebar; },
    toggleMobileSidebar: () => (state.showMobileSidebar = !state.showMobileSidebar),
    toggleMobileDrawer: () => (state.showMobileSidebar = !state.showMobileSidebar),
    get mobileScrollPosition() { return state.mobileScrollPosition; },
    setMobileScrollPosition: (val: number) => (state.mobileScrollPosition = val),
    get isExpanded() { return state.isExpanded; },
    toggleExpand: (val?: boolean) => { state.isExpanded = val !== undefined ? val : !state.isExpanded; if (typeof window !== "undefined") document.body.style.overflow = state.isExpanded ? "hidden" : ""; },

    // Settings
    updateVoiceSettings: (wake: string[], sleep: string[], greeting: string, farewell: string, campaign: boolean, chatSettings?: Record<string, any>, sttAnchors?: string[], micSensitivity?: number) => {
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
    setDiscoveredModels: (val: string[]) => (state.discoveredModels = val),
    resumeCampaign: (logEntry: any) => resumeManager.internalResumeCampaign(logEntry)
  };
}

export const nanobot = createNanobotState();
