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
import { vuiState, vuiController } from "$lib/vui";

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
    nanoBotStatus: "IDLE" as "IDLE" | "THINKING" | "ERROR" | "SUCCESS" | "VOICE" | "PROCESSING",
    modality: "text" as "text" | "voice",
    currentData: null as Record<string, unknown> | null,
    lastSuggestedWidget: "NONE" as WidgetType,
    lastProcessedCommand: "",
    lastProcessedTime: 0,
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
    isExpanded: false,
    sttAnchors: [] as string[],
    micSensitivity: 0.6,
  });

  const THINKING_TIMEOUT_MS = 30_000;
  let thinkingWatchdog: ReturnType<typeof setTimeout> | undefined;

  const resetVui = () => {
    state.nanoBotStatus = "IDLE";
    state.isBusy = false;
    voice.resetVui();
  };

  const softReset = () => {
    // Only drop busy/status if we aren't in a terminal state
    if (state.nanoBotStatus !== "ERROR") state.nanoBotStatus = "IDLE";
    state.isBusy = false;
    voice.softReset();
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

  const intent = createIntentManager(state, voice, log, ui, chat, resetVui, softReset, setThinking);

  let isHydratingSettings = false;
  const hydrateGlobalSettings = async () => {
    if (typeof window === "undefined" || window.location.pathname.includes("/login") || !permissionState.isInitialized || state.isHydrated || isHydratingSettings) return;
    try {
      isHydratingSettings = true;
      state.isHydrated = true;
      const res = await apiClient.get<any>("/api/v1/settings/voice");
      if (res?.wake_words) state.wakeWords = res.wake_words.map((w: string) => normalizeVn(w));
      if (res?.sleep_words) state.sleepWords = res.sleep_words.map((w: string) => normalizeVn(w));
      if (res?.greeting_template) voice.setGreetingTemplate(res.greeting_template);
      if (res?.farewell_template) voice.setFarewellTemplate(res.farewell_template);
      if (res?.is_campaign_mode !== undefined) state.isCampaignMode = res.is_campaign_mode;
      if (res?.chat_settings) state.chatSettings = { ...state.chatSettings, ...res.chat_settings };
      if (res?.stt_anchors) state.sttAnchors = res.stt_anchors;
      if (res?.mic_sensitivity !== undefined) state.micSensitivity = res.mic_sensitivity;
    } catch (e) {
      state.isHydrated = false;
    } finally {
      isHydratingSettings = false;
    }
  };

  const internalResumeCampaign = async (logEntry: any) => {
    if (!logEntry?.data?.campaign_id) return;
    const campaignId = logEntry.data.campaign_id;
    
    if (import.meta.env.DEV) console.log("[Nanobot] Fetching campaign for resume:", campaignId);
    
    let campaignData: any = logEntry.data; // Fallback to log data if API fails
    try {
      // Fetch full campaign data from Single Source of Truth
      const campaign = await apiClient.get<any>(`/api/v1/content/campaigns/${campaignId}`);
      if (campaign?.id) {
        campaignData = {
          category: "CONTENT_CREATE",
          campaign_id: campaign.id,
          step: campaign.current_step,
          status: campaign.status,
          keywords: campaign.topic_data,
          assets: campaign.assets_data,
          outline: campaign.outline_data,
        };
        if (import.meta.env.DEV) console.log("[Nanobot] Resume data fetched from API. Step:", campaign.current_step);
      }
    } catch (e) {
      console.warn("[Nanobot] Could not fetch campaign from API, using log data as fallback:", e);
    }
    
    // Restore VUI state with full data
    voice.setVoiceResult(
      "Khôi phục phiên làm việc",
      logEntry.text || logEntry.message || "Đang tiếp tục bài viết cũ...",
      "CONTENT_CREATE",
      campaignData,
      "voice",
      logEntry.routerTier || 2
    );
    
    vuiState.setActive(true);
    if (campaignData.status === "WAITING_FOR_REVIEW" || campaignData.category === "CONTENT_CREATE") {
      vuiState.setPhase("idle");
      vuiState.setIsWaitingForAction(true);
    } else {
      vuiState.setPhase("executing");
      startSmartPolling();
    }
    
    log.closeFullLog();
  };

  let pollingInterval: ReturnType<typeof setInterval> | undefined;

  const startSmartPolling = () => {
    if (pollingInterval) return;
    if (import.meta.env.DEV) console.log("[Nanobot] Starting Smart Polling...");
    
    pollingInterval = setInterval(async () => {
      // Rule R82.24: Deep Sync — Poll if any campaign is NOT finished (Step < 6)
      // or if we recently triggered an action.
      const hasActiveCampaign = log.activityLogs.some(l => 
        l.data?.category === "CONTENT_CREATE" && 
        (l.data?.status === "PROCESSING" || (l.data?.step || 0) < 6)
      );
      
      if (hasActiveCampaign) {
        await chat.hydrateHistory("account", (logs: any) => {
          const combined = [...log.activityLogs];
          let changed = false;
          logs.forEach((newL: any) => {
            const idx = combined.findIndex(ex => 
              ex.id === newL.id || 
              (ex.data?.campaign_id && 
               ex.data.campaign_id === newL.data?.campaign_id && 
               String(ex.data?.step ?? "") === String(newL.data?.step ?? ""))
            );
            if (idx === -1) {
              combined.push(newL);
              changed = true;
            } else {
              // Rule R86: Prefer the one with more data/content
              const existingDataStr = JSON.stringify(combined[idx].data || {});
              const newDataStr = JSON.stringify(newL.data || {});
              
              if (newDataStr.length > existingDataStr.length || combined[idx].id !== newL.id) {
                combined[idx] = { ...combined[idx], ...newL };
                changed = true;
              }
            }
          });

          if (changed) {
            const updatedLogs = combined.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
            log.setActivityLogs(updatedLogs as any);

            const resumeCount = updatedLogs.filter((l: any) => l.data?.campaign_id).length;
            if (import.meta.env.DEV && resumeCount > 0) {
              console.log(`[Nanobot] Hydration complete. Found ${resumeCount} resumeable campaign logs.`);
            }

            // Rule R82.10: Reactive UI Sync — Update the active VUI card if it exists
            if (voice.isVuiActive && voice.vuiResponse?.data?.campaign_id) {
              const activeId = voice.vuiResponse.data.campaign_id;
              const latestLog = (updatedLogs as any[]).slice().reverse().find((l: any) => 
                l.data?.category === "CONTENT_CREATE" && l.data?.campaign_id === activeId
              );
              
              if (latestLog && JSON.stringify(latestLog.data) !== JSON.stringify(voice.vuiResponse.data)) {
                voice.setVoiceResult(
                  voice.vuiUserQuery,
                  voice.vuiResponse.text,
                  (latestLog.data as any).action || "CONTENT_CREATE",
                  latestLog.data as any,
                  "voice",
                  voice.routerTier
                );
                if (import.meta.env.DEV) console.debug("[Nanobot] Reactive sync: UI Card updated.");
              }
            }
          }
        }, state.godModeUser || undefined);
      } else {
        stopSmartPolling();
      }
    }, 5000); // 5s polling for stability R82.11
  };

  const stopSmartPolling = () => {
    if (pollingInterval) {
      if (import.meta.env.DEV) console.log("[Nanobot] Stopping Smart Polling.");
      clearInterval(pollingInterval);
      pollingInterval = undefined;
    }
  };

  if (typeof window !== "undefined") {
    $effect.root(() => {
      $effect(() => {
        if (permissionState.isInitialized) {
          untrack(() => {
            if (state.isHydrated && !window.location.pathname.includes("/login")) return; // Rule R82.45: Hydration Lock
            
            hydrateGlobalSettings();
            if (!window.location.pathname.includes("/login")) {
              state.isHydrated = true; // Mark as hydrated globally
              notification.fetchNotifications();
              chat.hydrateHistory("account", (logs: any) => {
                const combined = [...log.activityLogs];
                logs.forEach((newL: any) => {
                  // Plan D: Use campaign_id + step as composite key so B1 and B2 coexist
                  const newStep = String(newL.data?.step ?? "");
                  const newCid = newL.data?.campaign_id ?? "";
                  const idx = combined.findIndex(ex => {
                    if (ex.id === newL.id) return true;
                    if (!newCid) return false;
                    const exStep = String(ex.data?.step ?? "");
                    const exCid = ex.data?.campaign_id ?? "";
                    return exCid === newCid && exStep === newStep;
                  });
                  if (idx === -1) combined.push(newL);
                  // Prefer the log with more data (e.g. assets vs empty placeholder)
                  else if (JSON.stringify(newL.data || {}).length > JSON.stringify(combined[idx].data || {}).length) {
                    combined[idx] = { ...combined[idx], ...newL };
                  }
                });
                log.setActivityLogs(combined.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime()));
                
                // Rule R81: Continuity — Auto-Resume active/pending sessions on load
                const pending = combined.slice().reverse().find((l: any) => 
                  l.data?.category === "CONTENT_CREATE" && 
                  (l.data?.status === "WAITING_FOR_REVIEW" || l.data?.status === "PROCESSING")
                );
                
                if (pending) {
                  // Instant recovery for Zero-Friction UX
                  const title = pending.data?.keywords?.title || pending.data?.topic_data?.title || 'Bản thảo cũ';
                  ui.showToast(`Đang khôi phục bài viết: ${title}`, "info", 5000);
                  // Wrap in timeout to ensure Svelte 5 state stabilizes after hydration
                  setTimeout(() => {
                    internalResumeCampaign(pending);
                  }, 200);
                }

                // Rule R82.24: Deep Sync — Start polling if any campaign is PROCESSING
                if (logs.some((l: any) => l.data?.status === "PROCESSING")) {
                  startSmartPolling();
                }
              }, state.godModeUser || undefined);
            }
          });
        }
      });
    });
  }

  /**
   * Rule R82.36: Native Agent Pulse Listener
   * Replaces Pusher with a lightweight EventSource connection.
   */
  let eventSource: EventSource | null = null;
  let pulseRetryTimeout: ReturnType<typeof setTimeout> | null = null;
  let idleDisconnectTimeout: ReturnType<typeof setTimeout> | null = null;

  const connectPulse = () => {
    if (typeof window === "undefined" || eventSource) return;

    if (import.meta.env.DEV) console.log("[Pulse] Connecting to Native Agent Pulse SSE...");
    eventSource = new EventSource("/api/v1/pulse/stream");

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { event: eventName, payload } = data;

        if (eventName === "CONTENT_PROGRESS") {
          if (import.meta.env.DEV) console.log("[Pulse] Progress update:", payload.message);
          
          // Instant Reaction: Update active card & Ensure Orb is visible (Rule R82.40)
          if (voice?.vuiResponse?.data?.campaign_id === payload.campaign_id) {
            vuiState.setActive(true);
            vuiState.setPhase("executing");
            
            if (voice.vuiResponse) {
              voice.vuiResponse.data = {
                  ...voice.vuiResponse.data,
                  progress_msg: payload.message,
                  status: "PROCESSING",
                  step: payload.step,
                  ...(payload.data || {})
              };
            }
          }

          // Surgical Log Sync: Update existing log entry in RAM immediately
          const existingLogs = [...log.activityLogs];
          const logIdx = existingLogs.findIndex(l => l.data?.campaign_id === payload.campaign_id);
          if (logIdx !== -1) {
            existingLogs[logIdx].data = { 
              ...existingLogs[logIdx].data, 
              step: payload.step, 
              status: "PROCESSING",
              progress_msg: payload.message,
              ...(payload.data || {})
            };
            log.setActivityLogs(existingLogs);
            if (import.meta.env.DEV) console.log("[Pulse] ActivityLog synced (Progress).");
          }
          
          // Trigger sync to ensure logs are consistent
          startSmartPolling();
        } else if (eventName === "BACKTRACK") {
          if (import.meta.env.DEV) console.log("[Pulse] Backtrack detected:", payload.reason);
          
          // R108: Explicit UI Feedback for Agentic Backtracking
          ui.showToast(`🤖 AI: ${payload.reason || 'Đang sửa lại nội dung do yêu cầu chất lượng...'}`, "warning", 8000);
          
          if (voice.vuiResponse?.data?.campaign_id === payload.campaign_id) {
            vuiState.setPhase("executing");
            voice.vuiResponse.data = {
              ...voice.vuiResponse.data,
              status: "PROCESSING",
              step: payload.step,
              progress_msg: "🔄 Hệ thống đang tự động sửa lại bản thảo..."
            };
          }
          startSmartPolling();
        } else if (eventName === "CONTENT_STEP_COMPLETED") {
          if (import.meta.env.DEV) console.log("[Pulse] Step completed:", payload.step);
          
          // Rule R82.41: Final Step Data Sync (Force reactivity & UI State)
          if (voice?.vuiResponse?.data?.campaign_id === payload.campaign_id) {
              vuiState.setActive(true);
              vuiState.setPhase("idle"); 
              vuiState.setIsWaitingForAction(true);
              
              if (voice.vuiResponse) {
                voice.vuiResponse.data = {
                    ...voice.vuiResponse.data,
                    status: payload.status,
                    step: payload.step,
                    ...(payload.data || {})
                };
              }
          }

          // Surgical Log Sync: Update/Add completed step log
          const existingLogs = [...log.activityLogs];
          const logIdx = existingLogs.findIndex(l => l.data?.campaign_id === payload.campaign_id && l.data?.step === payload.step);
          if (logIdx !== -1) {
            existingLogs[logIdx].data = { ...existingLogs[logIdx].data, status: payload.status, ...(payload.data || {}) };
            log.setActivityLogs(existingLogs);
          } else {
            // Rule R82.9: Create a new log if it doesn't exist to ensure history is rich
            log.addLog(payload.message || `Bước ${payload.step} hoàn tất.`, "XOHI", "info", 2, {
              category: "CONTENT_CREATE",
              campaign_id: payload.campaign_id,
              step: payload.step,
              status: payload.status,
              ...(payload.data || {})
            });
          }
          if (import.meta.env.DEV) console.log("[Pulse] ActivityLog synced (Step Completed).");
          startSmartPolling(); // Force full heavy sync
        }
      } catch (err) {
        if (import.meta.env.DEV) console.warn("[Pulse] Error parsing data:", err);
      }
    };

    eventSource.onerror = (err) => {
      if (eventSource) {
        if (import.meta.env.DEV) console.error("[Pulse] SSE Connection failed, retrying...");
        eventSource.close();
        eventSource = null;
        pulseRetryTimeout = setTimeout(connectPulse, 5000);
      }
    };
  };

  const disconnectPulse = () => {
    if (pulseRetryTimeout) clearTimeout(pulseRetryTimeout);
    if (eventSource) {
      if (import.meta.env.DEV) console.log("[Pulse] Auto-Disconnecting SSE (Idle Mode)...");
      eventSource.close();
      eventSource = null;
    }
  };

  // Rule R82.35: Smart Auto-Connection Lifecycle
  $effect.root(() => {
    $effect(() => {
      const isBusy = 
        state.isBusy || 
        state.nanoBotStatus !== "IDLE" || 
        state.isCampaignMode || 
        voice.isVuiActive;

      untrack(() => {
        if (isBusy) {
          if (idleDisconnectTimeout) clearTimeout(idleDisconnectTimeout);
          connectPulse();
        } else {
          // Graceful disconnect after 15 seconds of idle
          if (idleDisconnectTimeout) clearTimeout(idleDisconnectTimeout);
          idleDisconnectTimeout = setTimeout(() => {
            disconnectPulse();
          }, 15000);
        }
      });
    });
  });

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
    get vuiResponse() { return voice.vuiResponse; },
    get vuiUserQuery() { return voice.vuiUserQuery; },
    get voiceTrigger() { return voice.voiceTrigger; },
    setVuiActive: voice.setVuiActive,
    clearVuiResponse: voice.clearVuiResponse,
    setProcessingSpeech: voice.setProcessingSpeech,

    // Orchestrator Proxies (Rule 4.2 Compliance)
    get latestResumeableLog() {
      // Rule R81: Resilience — Find the latest interrupted campaign
      if (!log.activityLogs.length) return null;
      // Rule R81.40: Smart Identity Resume — Find the LATEST active campaign sếp touched.
      const actionable = log.activityLogs
        .filter((l: any) => 
          (l.data?.campaign_id || l.data?.keywords || l.data?.assets) && 
          (parseInt(String(l.data?.step || 0)) < 6)
        )
        .sort((a: any, b: any) => b.timestamp.getTime() - a.timestamp.getTime());
      
      if (actionable.length === 0) return null;
      
      // Step 2: Grab the campaign_id of the most recently touched log
      const latestCampaignId = actionable[0].data?.campaign_id;
      if (!latestCampaignId) return actionable[0]; // Fallback to absolute latest if no camp_id
      
      // Step 3: From all logs of THIS campaign, pick the one with the highest step
      const campaignLogs = actionable.filter(l => l.data?.campaign_id === latestCampaignId);
      campaignLogs.sort((a: any, b: any) => {
          const stepA = parseInt(String(a.data?.step || 0));
          const stepB = parseInt(String(b.data?.step || 0));
          return stepB - stepA;
      });

      return campaignLogs[0];
    },
    startRecording: (auto?: boolean) => vuiController.startRecording(auto),
    stopRecording: () => vuiController.stopRecording(),
    interruptAll: () => vuiController.interruptAll(),
    speak: (text: string) => vuiController.speak(text),

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
    startPolling: startSmartPolling,
    stopPolling: stopSmartPolling,
    
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
    get screenContext() {
      return {
        current_route: typeof window !== "undefined" ? window.location.pathname : "/",
        active_widget: state.activeWidget,
        active_data: state.currentData,
      };
    },
    get heartbeatCollapsed() { return ui.heartbeatCollapsed; },
    toggleHeartbeat: () => {
      if (typeof window === "undefined") return;
      if (ui.heartbeatCollapsed === null) {
        ui.heartbeatCollapsed = window.innerWidth >= 1280;
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
    updateVoiceSettings: (wake: string[], sleep: string[], greeting: string, farewell: string, campaign: boolean, chatSettings?: Record<string, any>, sttAnchors?: string[], micSensitivity?: number) => {
      state.wakeWords = wake;
      state.sleepWords = sleep;
      voice.setGreetingTemplate(greeting);
      voice.setFarewellTemplate(farewell);
      state.isCampaignMode = campaign;
      if (chatSettings) state.chatSettings = { ...state.chatSettings, ...chatSettings };
      if (sttAnchors) state.sttAnchors = sttAnchors;
      if (micSensitivity !== undefined) state.micSensitivity = micSensitivity;
    },

    toggleCampaignMode: async () => {
      if (state.isTogglingCampaign) return;
      state.isTogglingCampaign = true;
      const originalMode = state.isCampaignMode;
      try {
        const nextMode = !originalMode;
        state.isCampaignMode = nextMode;
        await apiClient.post("/api/v1/settings/voice", { is_campaign_mode: nextMode });
        ui.showToast(nextMode ? "Fortress Mode: ENGAGED" : "Fortress Mode: STANDBY", "success");
        log.addLog(`Neural Grid: ${nextMode ? 'RESTRICTED' : 'OPEN'}`, "SYS", "success");
      } catch (e) {
        state.isCampaignMode = originalMode;
        ui.showToast("Neural link sync failed", "error");
      } finally {
        state.isTogglingCampaign = false;
      }
    },

    get isExpanded() { return state.isExpanded; },
    toggleExpand: (val?: boolean) => {
      state.isExpanded = val !== undefined ? val : !state.isExpanded;
      if (typeof window !== "undefined") {
        document.body.style.overflow = state.isExpanded ? "hidden" : "";
      }
    },

    resumeCampaign: (logEntry: any) => internalResumeCampaign(logEntry)
  };
}

export const nanobot = createNanobotState();
