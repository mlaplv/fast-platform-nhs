import { untrack } from "svelte";
import { apiClient } from "$lib/utils/apiClient";
import type { WidgetType, Suggestion, CommandAction } from "./types";
import { createChatState } from "./chat.svelte";
import { createNotificationState } from "./notification.svelte";
import { createVaultState } from "./vault.svelte";
import { createVoiceState } from "./voice.svelte";
import { createUiState } from "./ui.svelte";
import { createLogState } from "./log.svelte";
import { createTrainingState } from "./training_state.svelte";
import { createIntentManager } from "./intent_manager.svelte.ts";
import { permissionState } from "./permissions.svelte";
import { normalizeVn } from "$lib/utils/text";

export * from "./types";

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
    nanoBotStatus: "IDLE" as "IDLE" | "THINKING" | "ERROR" | "SUCCESS",
    modality: "text" as "text" | "voice",
    currentData: null as Record<string, unknown> | null,
    lastSuggestedWidget: "NONE" as WidgetType,
    lastProcessedCommand: "",
    lastProcessedTime: 0,
    lastSpokenText: "",
    lastSpokenTime: 0,
    commandEpoch: 0,
    isBusy: false,
    godModeUser: null as string | null,
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
    } as Record<string, any>,
    agenticSuggestions: [
      { label: "Quản lý User", command: "manage users" },
      { label: "Quản lý Quyền", command: "manage permissions" },
      { label: "Tạo sản phẩm", command: "tạo sản phẩm mới" },
      { label: "Thêm danh mục", command: "thêm danh mục" },
      { label: "Xem đơn hàng", command: "mở đơn hàng" },
      { label: "Viết tin tức", command: "tạo tin tức" },
    ] as Suggestion[],
    mobileScrollPosition: 0,
  });

  const THINKING_TIMEOUT_MS = 30_000;
  let thinkingWatchdog: ReturnType<typeof setTimeout> | undefined;

  const resetVui = () => {
    state.nanoBotStatus = "IDLE";
    state.isBusy = false;
    voice.resetVui();
  };

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
    } else {
      clearTimeout(thinkingWatchdog);
    }
  };

  const intent = createIntentManager(state, voice, log, ui, chat, resetVui, setThinking);

  const hydrateGlobalSettings = async () => {
    if (typeof window === "undefined" || window.location.pathname.includes("/login") || !permissionState.isInitialized || state.isHydrated) return;
    try {
      state.isHydrated = true;
      const res = await apiClient.get<any>("/api/v1/settings/voice");
      if (res?.wake_words) state.wakeWords = res.wake_words.map((w: string) => normalizeVn(w));
      if (res?.sleep_words) state.sleepWords = res.sleep_words.map((w: string) => normalizeVn(w));
      if (res?.greeting_template) voice.setGreetingTemplate(res.greeting_template);
      if (res?.farewell_template) voice.setFarewellTemplate(res.farewell_template);
      if (res?.is_campaign_mode !== undefined) state.isCampaignMode = res.is_campaign_mode;
      if (res?.chat_settings) state.chatSettings = { ...state.chatSettings, ...res.chat_settings };
    } catch (e) {
      state.isHydrated = false;
    }
  };

  if (typeof window !== "undefined") {
    $effect.root(() => {
      $effect(() => {
        if (permissionState.isInitialized) {
          untrack(() => {
            hydrateGlobalSettings();
            if (!window.location.pathname.includes("/login") && !state.isHydrated) {
                notification.fetchNotifications();
                chat.hydrateHistory("account", (logs: any) => {
                const existingIds = new Set(log.activityLogs.map((l: any) => l.id));
                log.setActivityLogs([...log.activityLogs, ...logs.filter((l: any) => !existingIds.has(l.id))].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime()));
              }, state.godModeUser || undefined);
            }
          });
        }
      });
    });
  }

  return {
    get activityLogs() { return log.activityLogs; },
    get chatHistory() { return chat.history; },
    get activeWidget() { return state.activeWidget; },
    get currentData() { return state.currentData; },
    get nanoBotStatus() { return state.nanoBotStatus; },
    get isCampaignMode() { return state.isCampaignMode; },
    get isTogglingCampaign() { return state.isTogglingCampaign; },
    get isBusy() { return state.isBusy; },
    get godModeUser() { return state.godModeUser; },
    get modality() { return state.modality; },
    get wakeWords() { return state.wakeWords; },
    get sleepWords() { return state.sleepWords; },
    get agenticSuggestions() { return state.agenticSuggestions; },
    get chatPagination() { return chat.pagination; },

    // Actions
    processCommand: intent.processCommand,
    setVoiceResult: intent.setVoiceResult,
    resetVui,
    setThinking,
    setModality: (val: "text" | "voice") => (state.modality = val),
    setGodModeUser: (val: string | null) => (state.godModeUser = val),
    clearCurrentData: () => (state.currentData = null),
    clearCommandAction: () => (state.commandAction = null),
    get commandAction() { return state.commandAction; },

    // Voice & UI
    get voice() { return voice; },
    get ui() { return ui; },
    get isVuiActive() { return voice.isVuiActive; },
    get isSpeaking() { return voice.isProcessingSpeech; },
    get isProcessingSpeech() { return voice.isProcessingSpeech; },
    get vuiResponse() { return voice.vuiResponse; },
    get vuiUserQuery() { return voice.vuiUserQuery; },
    get voiceTrigger() { return voice.voiceTrigger; },
    setVuiActive: voice.setVuiActive,
    clearVuiResponse: voice.clearVuiResponse,
    setProcessingSpeech: voice.setProcessingSpeech,

    get universalModalOpen() { return ui.universalModalOpen; },
    get confirmDialog() { return ui.confirmDialog; },
    get toasts() { return ui.toasts; },
    showToast: ui.showToast,
    removeToast: ui.removeToast,
    showConfirm: ui.showConfirm,
    setUniversalModalOpen: ui.setUniversalModalOpen,
    showUniversalModal: () => ui.setUniversalModalOpen(true),
    closeUniversalModal: () => { ui.setUniversalModalOpen(false); state.activeWidget = "NONE"; },
    openWidget: (widget: WidgetType, data?: any) => {
       state.activeWidget = widget;
       if (data) state.currentData = data;
       ui.setUniversalModalOpen(true);
    },

    // HUD & Tips Proxies
    get activeHudPopup() { return ui.activeHudPopup; },
    get showQuickTips() { return ui.showQuickTips; },
    toggleHudPopup: (val: string) => { ui.activeHudPopup = ui.activeHudPopup === val ? null : val; },
    toggleQuickTips: () => { ui.showQuickTips = !ui.showQuickTips; },

    // Neural Capture / Training
    get training() { return training; },
    get isTraining() { return training.isTraining; },
    get trainingType() { return training.trainingType; },
    get trainingResult() { return training.trainingResult; },
    setTraining: training.setTraining,
    cancelTraining: training.cancelTraining,

    // Vault & Notifications
    get vault() { return vault; },
    get pendingApprovals() { return vault.pendingApprovals; },
    approveAction: vault.approveAction,
    denyAction: vault.denyAction,

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
    
    loadMoreMessages: () => chat.loadMoreMessages((logs: any) => {
      const ids = new Set(log.activityLogs.map((l: any) => l.id));
      log.setActivityLogs([...logs.filter((l: any) => !ids.has(l.id)), ...log.activityLogs].sort((a,b) => a.timestamp.getTime() - b.timestamp.getTime()));
    }, "account", state.godModeUser || undefined),
    syncSessionFromDb: async () => {
      log.setActivityLogs([]);
      await chat.hydrateHistory("account", (logs: any) => {
        log.setActivityLogs([...logs].sort((a,b) => a.timestamp.getTime() - b.timestamp.getTime()));
      }, state.godModeUser || undefined);
      ui.showToast(state.godModeUser ? `Đồng bộ log: ${state.godModeUser}` : "Đã đồng bộ dữ liệu từ DB", "success");
    },
    clearChatLogs: async () => {
      if (await chat.clearHistory("account")) { log.setActivityLogs([]); ui.showToast("Dữ liệu đã được quét sạch", "success"); }
    },

    // Layout
    get heartbeatCollapsed() { return ui.heartbeatCollapsed; },
    toggleHeartbeat: () => {
      if (typeof window === "undefined") return;
      if (ui.heartbeatCollapsed === null) {
        // If in auto mode, toggle to manual state opposite of current width-based behavior
        ui.heartbeatCollapsed = window.innerWidth >= 1280; // If >= 1280 (Expanded), set to true (Collapse). Else expand.
      } else {
        ui.heartbeatCollapsed = !ui.heartbeatCollapsed;
      }
    },
    get showMobileSidebar() { return state.showMobileSidebar; },
    get showMobileDrawer() { return state.showMobileSidebar; },
    toggleMobileSidebar: () => (state.showMobileSidebar = !state.showMobileSidebar),
    toggleMobileDrawer: () => (state.showMobileSidebar = !state.showMobileSidebar),
    get mobileScrollPosition() { return state.mobileScrollPosition; },
    setMobileScrollPosition: (val: number) => (state.mobileScrollPosition = val),

    // Auth & Identity
    get userName() { return permissionState.userName; },
    get userEmail() { return permissionState.user; },
    setUserEmail: (val: string) => {},
    setUserName: (val: string) => {},
    setUserRole: (val: string) => {},

    // Settings Sync
    updateVoiceSettings: (wake: string[], sleep: string[], greeting: string, farewell: string, campaign: boolean, chatSettings?: Record<string, any>) => {
      state.wakeWords = wake;
      state.sleepWords = sleep;
      voice.setGreetingTemplate(greeting);
      voice.setFarewellTemplate(farewell);
      state.isCampaignMode = campaign;
      if (chatSettings) state.chatSettings = { ...state.chatSettings, ...chatSettings };
    },

    toggleCampaignMode: async () => {
      if (state.isTogglingCampaign) return;
      state.isTogglingCampaign = true;
      const originalMode = state.isCampaignMode;
      try {
        const nextMode = !originalMode;
        state.isCampaignMode = nextMode;
        
        await apiClient.post("/api/v1/settings/voice", {
          is_campaign_mode: nextMode
        });
        
        ui.showToast(nextMode ? "Fortress Mode: ENGAGED" : "Fortress Mode: STANDBY", "success");
        log.addLog(`Neural Grid: ${nextMode ? 'RESTRICTED' : 'OPEN'}`, "SYS", "success");
      } catch (e) {
        state.isCampaignMode = originalMode;
        ui.showToast("Neural link sync failed", "error");
      } finally {
        state.isTogglingCampaign = false;
      }
    },
  };
}

export const nanobot = createNanobotState();
