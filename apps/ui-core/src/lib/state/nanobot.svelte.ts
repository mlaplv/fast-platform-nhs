import { apiClient } from "$lib/utils/apiClient";
import {
  type SystemLog,
  type WidgetType,
  type NanoBotState,
  type HudPopupType,
  type Suggestion,
  type CommandAction,
  type IntentResponse,
} from "./types";
import { createChatState, persistMessage } from "./chat.svelte";
import { createNotificationState } from "./notification.svelte";
import { createVaultState } from "./vault.svelte";
import { createVoiceState } from "./voice.svelte";
import { createUiState } from "./ui.svelte";
import { createLogState } from "./log.svelte";
import { permissionState } from "./permissions.svelte";
import { normalizeVn } from "$lib/utils/text";

export * from "./types";

export function createNanobotState() {
  const ui = createUiState();
  const log = createLogState();

  const state = $state({
    activeWidget: "NONE" as WidgetType,
    commandAction: null as CommandAction | null,
    showMobileSidebar: false,
    nanoBotStatus: "IDLE" as "IDLE" | "THINKING" | "ERROR" | "SUCCESS",
    showMobileDrawer: false,
    showQuickTips: false,
    stateStartedAt: Date.now(),
    modality: "text" as "text" | "voice",
    userEmail: "",
    userName: "",
    userRole: "",
    activeHudPopup: "NONE" as HudPopupType,
    currentData: null as Record<string, unknown> | null,
    lastSuggestedWidget: "NONE" as WidgetType,
    lastProcessedCommand: "",
    lastProcessedTime: 0,
    lastSpokenText: "",
    lastSpokenTime: 0,
    commandEpoch: 0,
    isBusy: false,
    isTraining: false,
    trainingType: null as "wake" | "sleep" | null,
    trainingResult: null as string | string[] | null,
    agenticSuggestions: [
      { label: "Quản lý User", command: "manage users" },
      { label: "Quản lý Quyền", command: "manage permissions" },
      { label: "Tạo sản phẩm", command: "tạo sản phẩm mới" },
      { label: "Thêm danh mục", command: "thêm danh mục" },
      { label: "Xem đơn hàng", command: "mở đơn hàng" },
      { label: "Viết tin tức", command: "tạo tin tức" },
    ] as Suggestion[],
    godModeUser: null as string | null, // Added for God-Mode UI
    // Wake/Sleep word registry (hydrated from backend)
    wakeWords: ["xohi", "hey xohi", "oi xohi"] as string[],
    sleepWords: ["tạm biệt", "ngủ đi"] as string[],

    pendingMutationApproval: null as {
      transcript: string;
      replyText: string;
      uiAction: string;
      actionData: any;
      source: "voice";
      routerTier?: number;
    } | null,
    mobileScrollPosition: 0,
  });

  // INITIAL HYDRATION: Sync with RBAC state (V47.0)
  if (permissionState.isInitialized) {
    state.userEmail = permissionState.user || "";
    state.userName = permissionState.userName || "";
    state.userRole = permissionState.roles[0] || "";
  }

  const voice = createVoiceState(log.addLog);
  const chat = createChatState(log.addLog);
  const notification = createNotificationState();
  const vault = createVaultState(log.addLog);

  const THINKING_TIMEOUT_MS = 30_000;
  let thinkingWatchdog: ReturnType<typeof setTimeout> | undefined;

  if (typeof window !== "undefined") {
    // THIẾT QUÂN LUẬT: Dừng mọi nỗ lực fetch lúc chưa login để tránh loop 401
    const isLoginPage = window.location.pathname.includes("/login");
    if (!isLoginPage && permissionState.isInitialized) {
      notification.fetchNotifications();
      // Hydrate wake/sleep words from backend settings
      apiClient
        .get<any>("/api/v1/settings/voice")
        .then((res) => {
          if (res?.wake_words)
            state.wakeWords = res.wake_words.map((w: string) => normalizeVn(w));
          if (res?.sleep_words)
            state.sleepWords = res.sleep_words.map((w: string) =>
              normalizeVn(w),
            );
          if (res?.greeting_template)
            voice.setGreetingTemplate(res.greeting_template);
        })
        .catch(() => {
          /* Keep defaults */
        });
    }
  }

  function updateVoiceSettings(
    wake: string[],
    sleep: string[],
    greeting?: string,
  ) {
    state.wakeWords = wake.map((w: string) => normalizeVn(w));
    state.sleepWords = sleep.map((w: string) => normalizeVn(w));
    if (greeting) voice.setGreetingTemplate(greeting);
  }

  function setTraining(val: boolean, type: "wake" | "sleep" | null = null) {
    state.isTraining = val;
    state.trainingType = type;
    if (val) state.trainingResult = null; // Reset on start
  }

  function completeTraining(result: string | string[]) {
    state.trainingResult = result;
    state.isTraining = false;
    // NOTE: trainingType is NOT cleared here — the $effect in VoiceSettings reads it
    // CRITICAL: Reset VUI so VoiceModal doesn't appear after Neural Capture closes
    voice.resetVui();
    import("./omni.svelte").then(({ omni }) => omni.stopTrainingRec());
  }

  function cancelTraining() {
    state.isTraining = false;
    state.trainingType = null;
    state.trainingResult = null;
    // CRITICAL: Reset VUI to prevent VoiceModal from appearing
    voice.resetVui();
    import("./omni.svelte").then(({ omni }) => omni.stopTrainingRec());
  }

  function resetVui() {
    state.nanoBotStatus = "IDLE";
    state.isBusy = false;
    voice.resetVui();
  }

  function setVoiceResult(
    transcript: string,
    responseText: string,
    uiAction: string,
    data: Record<string, unknown>,
    source: "text" | "voice" = "text",
    routerTier?: number,
  ) {
    state.lastSpokenText = responseText.toLowerCase();
    state.lastSpokenTime = Date.now();

    if (
      responseText &&
      responseText !== "NONE" &&
      responseText.trim().length > 0
    ) {
      log.addLog(responseText, "XOHI", "info", routerTier);
    }

    voice.setVoiceResult(
      transcript,
      responseText,
      uiAction,
      source,
      routerTier,
    );
    state.nanoBotStatus = voice.status === "VOICE" ? "IDLE" : "SUCCESS";

    if (uiAction) {
      const ACTION_WIDGET_MAP: Record<string, WidgetType> = {
        show_revenue_chart: "REVENUE_CHART",
        show_revenue: "SHOW_REVENUE",
        show_product_edit: "SHOW_PRODUCT_EDIT",
        show_user_table: "USER_TABLE",
        show_user_management: "USER_MANAGEMENT",
        show_category_management: "CATEGORY_MANAGEMENT",
        show_product_management: "PRODUCT_MANAGEMENT",
        show_order_management: "ORDER_MANAGEMENT",
        show_news_management: "NEWS_MANAGEMENT",
        show_permission_management: "PERMISSION_MANAGEMENT",
        show_voice_settings: "VOICE_SETTINGS",
        show_skills: "VOICE_SETTINGS",
      };
      const targetWidget = ACTION_WIDGET_MAP[uiAction];
      if (targetWidget) {
        state.currentData = data;
        const intentType = (data?.intent_type as string) || "";

        // Helper to check if voice mutation needs modal
        const requiresConfirmationForVoice = (d: any) => {
          return (
            source === "voice" &&
            (d?.action === "MUTATE" ||
              d?.requires_confirmation === true ||
              d?.intent_type === "MUTATE")
          );
        };

        // V22: MUTATE always opens modal to ensure human-in-the-loop review.
        // V26 (Contextual Split View): News Management ALWAYS opens widget to show the 2026 Editor layout
        if (
          intentType === "UI_NAV" ||
          uiAction.includes("edit") ||
          uiAction === "show_news_management" ||
          data?.restricted === false ||
          requiresConfirmationForVoice(data)
        ) {
          // Mở widget bình thường
          state.activeWidget = targetWidget;
          ui.setUniversalModalOpen(true);
          log.addLog(
            uiAction.replace("show_", "").replace(/_/g, " "),
            "[ACTION]",
          );
        } else if (source === "voice") {
          // Voice mode query: KHÔNG mở modal che mặt giao tiếp. Chỉ log + speak.
        } else {
          // Text + DATA_QUERY / DEEP_ANALYSIS: Lưu widget gợi ý, chỉ log
          state.lastSuggestedWidget = targetWidget;
          log.addLog("Sếp gõ 'mở' nếu muốn xem chi tiết.", "SYS");
        }
      }
    }
  }

  function setThinking(val: boolean, source: "text" | "voice" = "text") {
    if (val) {
      if (source === "voice") state.nanoBotStatus = "THINKING";
      state.stateStartedAt = Date.now();
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
  }

  async function processCommand(
    command: string,
    source: "text" | "voice" = "text",
  ) {
    const now = Date.now();
    let cmd = command.toLowerCase().trim();
    if (!cmd) {
      resetVui();
      return;
    }

    const isFragment =
      state.lastProcessedCommand &&
      (cmd.includes(state.lastProcessedCommand) ||
        state.lastProcessedCommand.includes(cmd));
    if (
      state.lastProcessedCommand &&
      now - state.lastProcessedTime < 3000 &&
      (isFragment || (cmd.length < 5 && cmd !== "mở"))
    )
      return;
    if (
      now - state.lastSpokenTime < 3000 &&
      (state.lastSpokenText.includes(cmd) || cmd.includes(state.lastSpokenText))
    )
      return;

    state.isBusy = true;
    state.lastProcessedCommand = cmd;
    state.lastProcessedTime = now;
    log.addLog(command, "[ADMIN]");
    setThinking(true, source);
    const myEpoch = ++state.commandEpoch;

    if (source === "voice") voice.setVuiActive(true);

    try {
      if (cmd === "clear" || cmd === "reset") {
        state.activeWidget = "NONE";
        if (!voice.isVuiActive) log.addLog("Đã dọn dẹp không gian", "[ACTION]");
        resetVui();
        return;
      }

      // ═══ "MỞ" COMMAND: Mở widget đã gợi ý từ DATA_QUERY trước đó ═══
      if (cmd === "mở" && state.lastSuggestedWidget !== "NONE") {
        state.activeWidget = state.lastSuggestedWidget;
        ui.setUniversalModalOpen(true);
        log.addLog(`Đã mở chi tiết cho sếp.`, "XOHI");
        state.lastSuggestedWidget = "NONE";
        state.nanoBotStatus = "SUCCESS";
        state.isBusy = false;
        return;
      }
      // ═══ "ĐÓNG" COMMAND: Close current widget ═══
      if (cmd.startsWith("đóng")) {
        if (state.activeWidget !== "NONE") {
          state.activeWidget = "NONE";
          ui.setUniversalModalOpen(false);
          log.addLog("Đã đóng cho sếp.", "XOHI");
        } else {
          log.addLog("Hiện không có gì đang mở ạ.", "XOHI");
        }
        state.nanoBotStatus = "SUCCESS";
        state.isBusy = false;
        return;
      }

      // ═══ INSTANT WIDGET SHORTCUTS (Bypass AI for known management commands) ═══
      const COMMAND_WIDGET_MAP: Record<string, WidgetType> = {
        "manage orders": "ORDER_MANAGEMENT",
        "mở đơn hàng": "ORDER_MANAGEMENT",
        "đơn hàng": "ORDER_MANAGEMENT",
        "manage products": "PRODUCT_MANAGEMENT",
        "mở sản phẩm": "PRODUCT_MANAGEMENT",
        "sản phẩm": "PRODUCT_MANAGEMENT",
        "manage categories": "CATEGORY_MANAGEMENT",
        "mở danh mục": "CATEGORY_MANAGEMENT",
        "danh mục": "CATEGORY_MANAGEMENT",
        "manage users": "USER_MANAGEMENT",
        "mở người dùng": "USER_MANAGEMENT",
        "người dùng": "USER_MANAGEMENT",
        "manage permissions": "PERMISSION_MANAGEMENT",
        "mở phân quyền": "PERMISSION_MANAGEMENT",
        "phân quyền": "PERMISSION_MANAGEMENT",
        "manage news": "NEWS_MANAGEMENT",
        "mở tin tức": "NEWS_MANAGEMENT",
        "tin tức": "NEWS_MANAGEMENT",
        skill: "VOICE_SETTINGS",
        "voice settings": "VOICE_SETTINGS",
        "mở cài đặt giọng": "VOICE_SETTINGS",
      };
      // Widget-to-Vietnamese label map for Xohi response
      const WIDGET_VI_LABEL: Record<string, string> = {
        ORDER_MANAGEMENT: "Quản lý Đơn hàng",
        PRODUCT_MANAGEMENT: "Quản lý Sản phẩm",
        CATEGORY_MANAGEMENT: "Quản lý Danh mục",
        USER_MANAGEMENT: "Quản lý Người dùng",
        PERMISSION_MANAGEMENT: "Phân quyền Hệ thống",
        NEWS_MANAGEMENT: "Quản lý Tin tức",
        VOICE_SETTINGS: "Cài đặt Giọng nói",
      };
      const matchedWidget =
        COMMAND_WIDGET_MAP[cmd] ||
        Object.entries(COMMAND_WIDGET_MAP).find(([k]) => {
          // Strict match: "mở sản phẩm" or very short command like "sản phẩm"
          const words = cmd.split(" ");
          return cmd === k || (words.length <= 4 && cmd.includes(k));
        })?.[1];
      if (matchedWidget) {
        const viLabel =
          WIDGET_VI_LABEL[matchedWidget] || matchedWidget.replace(/_/g, " ");
        const xohiReply = `Dạ, em mở ${viLabel} cho sếp ạ.`;
        log.addLog(xohiReply, "XOHI");

        if (source === "voice") {
          // Voice mode: KHÔNG mở modal che mặt. Chỉ speak xác nhận.
          persistMessage("account", "user", command, source);
          persistMessage("account", "assistant", xohiReply, source, {
            ui_action: `show_${matchedWidget.toLowerCase()}`,
          });
          const { omni } = await import("./omni.svelte");
          await omni.speak(xohiReply);
        } else {
          // Text mode: Mở widget bình thường (lệnh tường minh)
          state.activeWidget = matchedWidget;
          ui.setUniversalModalOpen(true);
          persistMessage("account", "user", command, source);
          persistMessage("account", "assistant", xohiReply, source, {
            ui_action: `show_${matchedWidget.toLowerCase()}`,
          });
        }
        state.nanoBotStatus = "SUCCESS";
        state.isBusy = false;
        return;
      }

      const { omni } = await import("./omni.svelte");
      await omni.processGhost(cmd, source);
      state.isBusy = false;
    } catch (e: any) {
      state.nanoBotStatus = "ERROR";
      log.addLog(`Command failed: ${e.message}`, "Nanobot-Core");
      setTimeout(() => resetVui(), 4000);
    } finally {
      clearTimeout(thinkingWatchdog);
      if (state.commandEpoch === myEpoch) state.isBusy = false;
    }
  }

  return {
    // State Getters
    get activityLogs() {
      return log.activityLogs;
    },
    get chatHistory() {
      return chat.history;
    },
    get chatPagination() {
      return chat.pagination;
    },
    get activeWidget() {
      return state.activeWidget;
    },
    get commandAction() {
      return state.commandAction;
    },
    get pendingApprovals() {
      return vault.pendingApprovals;
    },
    get currentData() {
      return state.currentData;
    },
    get showMobileSidebar() {
      return state.showMobileSidebar;
    },
    get nanoBotStatus() {
      return state.nanoBotStatus;
    },
    get showMobileDrawer() {
      return state.showMobileDrawer;
    },
    get showQuickTips() {
      return state.showQuickTips;
    },
    get agenticSuggestions() {
      return state.agenticSuggestions;
    },
    get userEmail() {
      return state.userEmail;
    },
    get userName() {
      return state.userName;
    },
    get userRole() {
      return state.userRole;
    },
    get modality() {
      return state.modality;
    },
    get activeHudPopup() {
      return state.activeHudPopup;
    },
    get commandEpoch() {
      return state.commandEpoch;
    },
    get notifications() {
      return notification.notifications;
    },
    get isBusy() {
      return state.isBusy;
    },
    get unreadNotificationsCount() {
      return notification.unreadCount;
    },
    get confirmDialog() {
      return ui.confirmDialog;
    },
    get toasts() {
      return ui.toasts;
    },
    get expandedLog() {
      return log.expandedLog;
    },
    get pendingMutationApproval() {
      return state.pendingMutationApproval;
    },
    get universalModalOpen() {
      return ui.universalModalOpen;
    },
    get isTraining() {
      return state.isTraining;
    },
    get trainingType() {
      return state.trainingType;
    },
    get trainingResult() {
      return state.trainingResult;
    },
    get godModeUser() {
      return state.godModeUser;
    },
    get mobileScrollPosition() {
      return state.mobileScrollPosition;
    },
    get isMobileHeaderMinimized() {
      return state.mobileScrollPosition > 20;
    },

    // Voice Delegation
    get isVuiActive() {
      return voice.isVuiActive;
    },
    get isSpeaking() {
      return voice.isProcessingSpeech;
    },
    get vuiResponse() {
      return voice.vuiResponse;
    },
    get vuiUserQuery() {
      return voice.vuiUserQuery;
    },
    get voiceTrigger() {
      return voice.voiceTrigger;
    },
    get isProcessingSpeech() {
      return voice.isProcessingSpeech;
    },
    get voice() {
      return voice;
    },

    // Actions
    setUserEmail(val: string) {
      state.userEmail = val;
    },
    setUserName(val: string) {
      state.userName = val;
    },
    setUserRole(val: string) {
      state.userRole = val;
    },
    setVuiActive(val: boolean) {
      voice.setVuiActive(val);
    },
    clearVuiResponse() {
      voice.clearVuiResponse();
    },
    setModality(val: "text" | "voice") {
      state.modality = val;
    },
    setTraining,
    completeTraining,
    cancelTraining,
    updateVoiceSettings,
    setActiveHudPopup(val: HudPopupType) {
      state.activeHudPopup = val;
    },
    setGodModeUser(val: string | null) {
      state.godModeUser = val;
    },
    toggleMobileSidebar() {
      state.showMobileSidebar = !state.showMobileSidebar;
    },
    toggleMobileDrawer() {
      state.showMobileDrawer = !state.showMobileDrawer;
    },
    toggleQuickTips() {
      state.showQuickTips = !state.showQuickTips;
    },
    toggleHudPopup(type: HudPopupType) {
      state.activeHudPopup = state.activeHudPopup === type ? "NONE" : type;
    },

    // Core Logic
    resetVui,
    setVoiceResult,
    setThinking,
    setPendingMutationApproval: (val: any) =>
      (state.pendingMutationApproval = val),
    processCommand,
    setProcessingSpeech: (val: boolean) => voice.setProcessingSpeech(val),
    addLog: log.addLog,
    showFullLog: log.showFullLog,
    closeFullLog: log.closeFullLog,
    clearCurrentData: () => {
      state.currentData = null;
    },
    clearCommandAction: () => {
      state.commandAction = null;
    },

    // UI Logic
    showConfirm: ui.showConfirm,
    showToast: ui.showToast,
    removeToast: ui.removeToast,
    openWidget(widget: WidgetType, data?: Record<string, unknown>) {
      state.activeWidget = widget;
      if (data) state.currentData = data;
      ui.setUniversalModalOpen(true);
      log.addLog(`Opening ${widget.replace(/_/g, " ")}`, "[ACTION]");
    },
    showUniversalModal: () => ui.setUniversalModalOpen(true),
    closeUniversalModal: () => {
      ui.setUniversalModalOpen(false);
      state.activeWidget = "NONE";
    },
    setMobileScrollPosition(val: number) {
      state.mobileScrollPosition = val;
    },

    // Sub-state proxies
    approveAction: vault.approveAction,
    denyAction: vault.denyAction,
    fetchNotifications: notification.fetchNotifications,
    markNotificationAsRead: notification.markNotificationAsRead,
    hydrateHistory: (sid: string) =>
      chat.hydrateHistory(
        sid,
        (logs) => {
          const existingIds = new Set(
            log.activityLogs.map((l: SystemLog) => l.id),
          );
          const uniqueNew = logs.filter(
            (l: SystemLog) => !existingIds.has(l.id),
          );
          log.setActivityLogs(
            [...log.activityLogs, ...uniqueNew].sort(
              (a: SystemLog, b: SystemLog) =>
                a.timestamp.getTime() - b.timestamp.getTime(),
            ),
          );
        },
        state.godModeUser || undefined,
      ),
    loadMoreMessages: () =>
      chat.loadMoreMessages(
        (logs) => {
          const existingIds = new Set(
            log.activityLogs.map((l: SystemLog) => l.id),
          );
          const uniqueNew = logs.filter(
            (l: SystemLog) => !existingIds.has(l.id),
          );
          log.setActivityLogs(
            [...uniqueNew, ...log.activityLogs].sort(
              (a: SystemLog, b: SystemLog) =>
                a.timestamp.getTime() - b.timestamp.getTime(),
            ),
          );
        },
        "account",
        state.godModeUser || undefined,
      ),
    syncSessionFromDb: async () => {
      log.setActivityLogs([]);
      await chat.hydrateHistory(
        "account",
        (logs) => {
          log.setActivityLogs(
            [...logs].sort(
              (a, b) => a.timestamp.getTime() - b.timestamp.getTime(),
            ),
          );
        },
        state.godModeUser || undefined,
      );
      ui.showToast(
        state.godModeUser
          ? `ĐÃ ĐỒNG BỘ LOG CỦA USER: ${state.godModeUser}`
          : "ĐÃ ĐỒNG BỘ DỮ LIỆU TỪ DATABASE VÀO PHIÊN",
        "success",
        3000,
      );
    },
    clearChatLogs: async () => {
      if (await chat.clearHistory("account")) {
        log.setActivityLogs([]);
        ui.showToast(
          "DỮ LIỆU ĐÃ ĐƯỢC QUÉT SẠCH KHỎI DATABASE",
          "success",
          5000,
        );
      }
    },
  };
}
export const nanobot = createNanobotState();
if (typeof window !== "undefined") {
  const isLoginPage = window.location.pathname.includes("/login");
  if (!isLoginPage && permissionState.isInitialized) {
    nanobot.hydrateHistory("account");
  }
}
