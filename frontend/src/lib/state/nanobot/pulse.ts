import { normalizeAssets } from "./utils";
import { isDev, isAdminDomain } from "./env";
import type { 
  CampaignData, 
  PulseSignal, 
  SystemLog, 
  IntentResponse, 
  ToastType,
  CampaignKeywords,
  CampaignOutline,
  CampaignMetrics,
  MediaAsset,
  CampaignStatus,
  PulsePayload,
  CampaignLogMetadata
} from "../types";

interface PulseMessage {
  event: string;
  payload: unknown; // Replace any with unknown for safer casting
}

// CNS V70: Voice Discipline — maps server severity to frontend action
const VOICE_DISCIPLINE = {
  CRITICAL: "interrupt",  // Speaks immediately
  ACTION:   "patient",   // Waits for idle, then speaks
  PROGRESS: "ping",      // Silent 808 neural ping only
  INFO:     "silent"     // Bell count only, no audio
} as const;

type VoiceDiscipline = typeof VOICE_DISCIPLINE[keyof typeof VOICE_DISCIPLINE];

// CNS V82.8: Partial Payload Protection - Prevents overwriting valid data with empty server defaults
const hasContent = (v: unknown): boolean => {
  if (v === null || v === undefined) return false;
  if (typeof v === 'string') return v.trim().length > 0;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === 'object') return Object.keys(v).length > 0;
  return true;
};

interface PulseDeps {
  state: {
    currentData: CampaignData | Record<string, unknown> | null;
    liveStreamBuffer: string;
  };
  voice: {
    vuiResponse: IntentResponse | null;
    setVoiceResult: (
      transcript: string,
      responseText: string,
      uiAction: string,
      data?: Record<string, unknown>,
      source?: "text" | "voice",
      routerTier?: number
    ) => void;
    clearVuiResponse: () => void;
  };
  log: {
    activityLogs: SystemLog[];
    setActivityLogs: (logs: SystemLog[]) => void;
    addLog: (msg: string, source?: string, type?: string, tier?: number, data?: Record<string, unknown>) => void;
  };
  ui: {
    showToast: (msg: string, type: ToastType, duration?: number) => void;
  };
  vuiState: {
    setActive: (val: boolean) => void;
    setPhase: (phase: "idle" | "executing" | "thinking" | "done") => void;
    setSystemMessage: (msg: string) => void;
    setIsWaitingForAction: (val: boolean) => void;
  };
  notification: {
    addPendingSignal?: (signal: { id: string; message: string; severity: string; isRead: boolean; payload?: Record<string, any>; signal_type?: string }) => void;
  };
  chat: {
    clearHistory: (sessionId: string) => Promise<boolean>;
    clearLocalSession: (sessionId: string, userId?: string) => void;
    sweepCampaignFromCache: (campaignId: string) => void;
  };
}

export function createPulseManager(
  state: PulseDeps["state"],
  voice: PulseDeps["voice"],
  log: PulseDeps["log"],
  ui: PulseDeps["ui"],
  vuiState: PulseDeps["vuiState"],
  notification: PulseDeps["notification"],
  chat: PulseDeps["chat"],
  startSmartPolling: () => void
) {
  let eventSource: EventSource | null = null;
  let pulseRetryTimeout: ReturnType<typeof setTimeout> | null = null;
  let retryCount = 0;
  let lastHeartbeat = Date.now();
  let heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  
  // Phase 82: Sync Guard — Prevent DB sync from overwriting fresh SSE data
  let liveCampaigns = new Map<string, number>(); // campaign_id -> last_sse_completed_timestamp

  const handleVisibilityChange = () => {
    if (document.visibilityState === "visible" && !eventSource) {
      connectPulse();
    }
  };

  const connectPulse = () => {
    if (typeof window === "undefined" || eventSource || !isAdminDomain()) return;

    const token = localStorage.getItem("admin_token") || localStorage.getItem("access_token");
    const url = token ? `/api/v1/pulse/stream?token=${encodeURIComponent(token)}` : "/api/v1/pulse/stream";
    eventSource = new EventSource(url, { withCredentials: true });

    if (typeof window !== "undefined") {
      window.removeEventListener("visibilitychange", handleVisibilityChange);
      window.addEventListener("visibilitychange", handleVisibilityChange);
    }

    eventSource.onopen = () => {
      retryCount = 0;
      lastHeartbeat = Date.now();
      
      if (!heartbeatInterval) {
        heartbeatInterval = setInterval(() => {
          const sinceLast = Date.now() - lastHeartbeat;
          if (sinceLast > 45000) { // 45s threshold (3 pulses + buffer)
            console.warn(`[Pulse] ⚠️ Heartbeat lost (${sinceLast}ms). Force reconnecting...`);
            connectPulse();
          }
        }, 10000);
      }
    };

    eventSource.addEventListener("HEARTBEAT", () => {
      // console.debug("[Pulse] 💓 Heartbeat received.");
      lastHeartbeat = Date.now();
    });

    eventSource.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as PulseMessage;
        const { event: eventName, payload } = data;
        const activeData = (state.currentData as unknown as CampaignData);
        const cid = (payload as { campaign_id?: string })?.campaign_id;
        if (activeData) {
          const match = activeData.campaign_id === cid || (activeData as unknown as {id: string}).id === cid;
        }

        if (eventName === "MEDIA_ANALYZED") {
          import("$lib/state/media.svelte").then((module: unknown) => {
            const m = module as { mediaStore?: { handleMediaAnalyzed: (p: unknown) => void } };
            if (m && m.mediaStore) {
                m.mediaStore.handleMediaAnalyzed(payload);
            }
          }).catch((err) => {
             console.error("[Pulse] Media Analyzed forward error:", err);
          });
          return;
        }

        if (eventName === "CONTENT_PROGRESS") {
          const contentPayload = payload as CampaignData & { message: string; data?: Record<string, unknown> };
          const newData = (contentPayload.data || {}) as Record<string, unknown>;
          const goldMeta = (newData.gold_metadata || {}) as Record<string, unknown>;

          if (voice?.vuiResponse?.data && (voice.vuiResponse.data as unknown as {campaign_id: string}).campaign_id === contentPayload.campaign_id) {
            vuiState.setActive(true);
            vuiState.setPhase("executing");
            vuiState.setSystemMessage(contentPayload.message);
          }

          // CNS V86.5: Clear stream buffer when starting a new step or a major progress pulse
          if (contentPayload.status === "PROCESSING" && state.liveStreamBuffer) {
             state.liveStreamBuffer = "";
          }

          const syncTarget = (target: CampaignData) => {
            if (!target) return;
            target.progress_msg = contentPayload.message;
            // V82.12: Respect incoming status (like ERROR) instead of hardcoding PROCESSING
            target.status = contentPayload.status || "PROCESSING";
            target.step = contentPayload.step;
            
            if (hasContent(newData.keywords) || hasContent(newData.topic_data)) target.keywords = (newData.keywords || newData.topic_data) as CampaignKeywords;
            if (hasContent(newData.assets) || hasContent(newData.assets_data)) target.assets = normalizeAssets((newData.assets || newData.assets_data) as (MediaAsset | string)[]);
            if (hasContent(newData.outline) || hasContent(newData.outline_data)) target.outline = (newData.outline || newData.outline_data) as CampaignOutline;
            if (hasContent(newData.draft_content)) target.draft_content = newData.draft_content as string;
            
            if (hasContent(goldMeta.avatar)) target.selectedAvatarUrl = goldMeta.avatar as string;
            if (goldMeta.selected_index !== undefined) target.selectedAssetIndex = Number(goldMeta.selected_index);
            if (hasContent(goldMeta.reserve_assets)) target.reserve_assets = normalizeAssets(goldMeta.reserve_assets as (MediaAsset | string)[]);
            if (hasContent(goldMeta.creation_config)) target.creation_config = goldMeta.creation_config as Record<string, unknown>;
            if (hasContent(goldMeta.analysis_cache)) target.analysis_cache = goldMeta.analysis_cache as Record<string, unknown>;
            if (hasContent(goldMeta.analysis_metrics)) target.analysis_metrics = goldMeta.analysis_metrics as CampaignMetrics;
          };

          if (voice.vuiResponse?.data && (voice.vuiResponse.data as unknown as {campaign_id: string}).campaign_id === contentPayload.campaign_id) {
            syncTarget(voice.vuiResponse.data as unknown as CampaignData);
          }
          if (activeData && (activeData.campaign_id === contentPayload.campaign_id || (activeData as unknown as {id: string}).id === contentPayload.campaign_id)) {
            syncTarget(activeData);
            // CNS V82.9: Force re-assignment to trigger reactivity for deep observers
            state.currentData = { ...activeData };
          }

          const existingLogs = [...log.activityLogs];
          const logIdx = existingLogs.findIndex(l =>
            l.data?.campaign_id === contentPayload.campaign_id &&
            String(l.data?.step ?? "") === String(contentPayload.step ?? "")
          );
          if (logIdx !== -1) {
            const current = (existingLogs[logIdx].data || {}) as Record<string, unknown>;
            existingLogs[logIdx].data = {
              ...current,
              step: contentPayload.step,
              status: contentPayload.status || "PROCESSING",
              progress_msg: contentPayload.message,
              keywords: (newData.keywords || newData.topic_data || current.keywords) as CampaignKeywords,
              assets: normalizeAssets((newData.assets || newData.assets_data || current.assets) as (MediaAsset | string)[]),
              outline: (newData.outline || newData.outline_data || current.outline) as CampaignOutline,
              draft_content: (newData.draft_content || current.draft_content) as string
            };
            log.setActivityLogs(existingLogs);
          }
          startSmartPolling();
        } else if (eventName === "BACKTRACK") {
          const backtrackPayload = payload as { campaign_id: string; step: number; reason: string };
          log.addLog(`🔄 AI: ${backtrackPayload.reason || 'Đang sửa lại nội dung...'}`, "XOHI", "warning", 2, {
            campaign_id: backtrackPayload.campaign_id, step: backtrackPayload.step
          });
          
          if (voice.vuiResponse?.data && (voice.vuiResponse.data as unknown as {campaign_id: string}).campaign_id === backtrackPayload.campaign_id) {
            vuiState.setPhase("executing");
            const d = voice.vuiResponse.data as unknown as CampaignData;
            d.status = "PROCESSING"; d.step = backtrackPayload.step;
            d.progress_msg = "🔄 Hệ thống đang tự động sửa lại bản thảo...";
          }
          if (activeData && (activeData.campaign_id === backtrackPayload.campaign_id || (activeData as unknown as {id: string}).id === backtrackPayload.campaign_id)) {
             activeData.status = "PROCESSING"; activeData.step = backtrackPayload.step;
             activeData.progress_msg = "🔄 Hệ thống đang tự động sửa lại bản thảo...";
          }
          startSmartPolling();
        } else if (eventName === "CONTENT_STEP_COMPLETED") {
          const completedPayload = payload as CampaignData & { message: string; data?: unknown };
          const rawData = (completedPayload.data || completedPayload || {}) as CampaignData;
          const goldMeta = (rawData.gold_metadata || {}) as Record<string, unknown>;

          if (completedPayload.campaign_id) {
            liveCampaigns.set(completedPayload.campaign_id, Date.now());
          }

          // Ensure voice response exists if this is the active campaign
          if (!voice.vuiResponse && (activeData?.campaign_id === completedPayload.campaign_id || (activeData as unknown as {id: string})?.id === completedPayload.campaign_id)) {
             voice.setVoiceResult("Neural Update", "Cập nhật từ hệ thống...", "CONTENT_CREATE", { campaign_id: completedPayload.campaign_id }, "text");
          }

          if (voice.vuiResponse?.data && (voice.vuiResponse.data as unknown as { campaign_id: string }).campaign_id === completedPayload.campaign_id) {
            vuiState.setActive(true); vuiState.setPhase("idle");
            vuiState.setIsWaitingForAction(true);
          }

          const syncCompleted = (target: CampaignData) => {
            if (!target) return;
            const updated = { ...target };
            
            updated.status = (completedPayload.status || rawData.status || "WAITING_FOR_REVIEW") as CampaignStatus;
            updated.step = (completedPayload.step || rawData.step || updated.step) as number;
            updated.progress_msg = "";
            
            if (hasContent(rawData.keywords) || hasContent(rawData.topic_data)) updated.keywords = (rawData.keywords || rawData.topic_data) as CampaignKeywords;
            if (hasContent(rawData.assets) || hasContent(rawData.assets_data)) updated.assets = normalizeAssets((rawData.assets || rawData.assets_data) as (MediaAsset | string)[]);
            if (hasContent(rawData.outline) || hasContent(rawData.outline_data)) updated.outline = (rawData.outline || rawData.outline_data) as CampaignOutline;
            if (hasContent(rawData.draft_content)) updated.draft_content = rawData.draft_content;
            if (hasContent(rawData.final_html)) updated.final_html = rawData.final_html;
            if (rawData.unique_score !== undefined) updated.unique_score = rawData.unique_score;
            
            if (hasContent(goldMeta.analysis_cache)) updated.analysis_cache = goldMeta.analysis_cache as Record<string, unknown>;
            if (hasContent(goldMeta.analysis_metrics)) updated.analysis_metrics = goldMeta.analysis_metrics as CampaignMetrics;
            if (hasContent(goldMeta.avatar)) updated.selectedAvatarUrl = goldMeta.avatar as string;
            if (goldMeta.selected_index !== undefined) updated.selectedAssetIndex = Number(goldMeta.selected_index);
            if (hasContent(goldMeta.reserve_assets)) updated.reserve_assets = normalizeAssets(goldMeta.reserve_assets as (MediaAsset | string)[]);
            if (hasContent(goldMeta.creation_config)) updated.creation_config = goldMeta.creation_config as Record<string, unknown>;
            
            // Re-assign to state.currentData to force reactivity
            state.currentData = updated;
          };

          if (voice.vuiResponse?.data && (voice.vuiResponse.data as unknown as {campaign_id: string}).campaign_id === completedPayload.campaign_id) {
            syncCompleted(voice.vuiResponse.data as unknown as CampaignData);
          }
          if (activeData && (activeData.campaign_id === completedPayload.campaign_id || (activeData as unknown as {id: string}).id === completedPayload.campaign_id)) {
            syncCompleted(activeData);
          }

          const existingLogs = [...log.activityLogs];
          const logIdx = existingLogs.findIndex(l => l.data?.campaign_id === completedPayload.campaign_id && l.data?.step === completedPayload.step);
          if (logIdx !== -1) {
            existingLogs[logIdx].data = { ...existingLogs[logIdx].data, status: completedPayload.status, ...(completedPayload.data || {}) };
            log.setActivityLogs(existingLogs);
          } else {
            log.addLog(completedPayload.message || `Bước ${completedPayload.step} hoàn tất.`, "XOHI", "info", 2, {
              category: "CONTENT_CREATE", campaign_id: completedPayload.campaign_id,
              step: completedPayload.step, status: completedPayload.status,
              ...(completedPayload.data || {}),
              assets: normalizeAssets(completedPayload.data?.assets)
            });
          }
          startSmartPolling();
        } else if (eventName === "CONTENT_CHUNK") {
          const chunkPayload = payload as { campaign_id: string; text: string; step: number };
          const syncChunk = (target: CampaignData) => {
             if (!target) return;
             target.draft_content = (target.draft_content || "") + chunkPayload.text;
             target.step = chunkPayload.step || target.step;
             target.status = "PROCESSING";
          };

          if (voice.vuiResponse?.data && (voice.vuiResponse.data as unknown as {campaign_id: string}).campaign_id === chunkPayload.campaign_id) {
             syncChunk(voice.vuiResponse.data as unknown as CampaignData);
             liveCampaigns.set(chunkPayload.campaign_id, Date.now());
          }
           if (activeData && (activeData.campaign_id === chunkPayload.campaign_id || (activeData as unknown as {id: string}).id === chunkPayload.campaign_id)) {
              syncChunk(activeData);
              liveCampaigns.set(chunkPayload.campaign_id, Date.now());
              // CNS V86.5: Pipe to neural glass
              state.liveStreamBuffer = (state.liveStreamBuffer || "") + chunkPayload.text;
           }
        } else if (eventName === "SYSTEM_SIGNAL") {
          const signalPayload = payload as PulseSignal & { signal_type?: string; payload?: Record<string, any> };
          const { message, severity, notification_id, signal_type, payload: signalMeta } = signalPayload;
          const discipline: VoiceDiscipline = VOICE_DISCIPLINE[severity as keyof typeof VOICE_DISCIPLINE] ?? "silent";

          if (typeof notification.addPendingSignal === "function") {
            notification.addPendingSignal({
              id: notification_id,
              message,
              severity,
              isRead: false,
              payload: signalMeta,
              signal_type
            });
          }

          if (discipline === "interrupt") ui.showToast(message, "error", 7000);
          else if (discipline === "patient") ui.showToast(message, "warning", 7000);

          if (discipline === "interrupt") {
            import("$lib/vui").then(({ vuiController, vuiState }) => {
              vuiController.interruptSpeech(); vuiState.setActive(true);
              vuiState.setPhase("idle"); vuiController.speak(message);
            }).catch(() => {});
          } else if (discipline === "patient") {
            import("$lib/vui").then(({ vuiController, vuiState }) => {
              vuiState.setActive(true); vuiState.setPhase("idle");
              vuiController.playNotificationPing();
              setTimeout(() => vuiController.speak(message), 800);
            }).catch(() => {});
          } else if (discipline === "ping") {
             import("$lib/vui").then(({ vuiController }) => {
               vuiController.playNotificationPing();
             }).catch(() => {});
          }
        } else if (eventName === "CAMPAIGN_PURGED") {
          interface PurgeEventPayload { campaign_id: string; type?: string; action?: string; user_id?: string }
          const { campaign_id: cid } = payload as PurgeEventPayload;
          
          // CNS V82.11: Perform deep-state sweep to prevent ghost resurrections in log streams
          const logs = [...log.activityLogs];
          const filtered = logs.filter(l => {
            const m = l.data as CampaignLogMetadata;
            return (m?.campaign_id !== cid && m?.id !== cid);
          });
          if (filtered.length !== logs.length) log.setActivityLogs(filtered);
          
          // Cleanup VUI and Active Data States
          if (voice.vuiResponse?.data && (voice.vuiResponse.data as CampaignLogMetadata).campaign_id === cid) {
            voice.clearVuiResponse(); 
            import("$lib/vui").then(({ vuiState }) => {
              vuiState.setActive(false); vuiState.setPhase("idle");
            }).catch(() => {});
          }
          
          if (activeData && (activeData.campaign_id === cid || (activeData as unknown as {id: string}).id === cid)) {
             state.currentData = null;
          }
          
          chat.sweepCampaignFromCache(cid);
          // [Elite V2.2] Silenced background toast to avoid double-notification (API already notified)
        } else if (eventName === "SUPPORT_INBOX_UPDATE") {
          // CNS V86.1: Neural Refresh Pulse (Elite V2.2)
          // Increment toggle to trigger re-fetch in SupportInbox.svelte
           const updatePayload = payload as { session_id: string; message?: string; role?: string };
           if (state && typeof state.supportRefreshToggle !== 'undefined') {
             state.supportRefreshToggle++;
             // Signal a silent, premium successful update
             ui.showToast("Hộp thư Helen vừa được cập nhật 🟢", "info", 2000);
            
            // 🔈 REAL-TIME TACTICAL AUDIO: "Ting" sound for the Boss (Elite V2.2)
            import("$lib/vui").then(({ vuiController }) => {
              vuiController.playNotificationPing();
            }).catch(() => {});
          }

          // [CNS V92.5] Push notifications to Bell on client chat
          if (updatePayload && updatePayload.role === 'user') {
            if (typeof notification.addPendingSignal === "function") {
              notification.addPendingSignal({
                id: `chat-${updatePayload.session_id}-${Date.now()}`,
                message: `Khách mới nhắn tin: "${updatePayload.message || 'Tin nhắn mới'}"`,
                severity: "ACTION",
                isRead: false,
                payload: { session_id: updatePayload.session_id },
                signal_type: "CHAT"
              });
            }
          }
        }
      } catch (err) {
        // Fallback error
      }
    };

    eventSource.onerror = (err) => {
      console.error("[Pulse] 🔴 SSE Connection Error:", err);
      if (eventSource) {
        eventSource.close();
        eventSource = null;
        
        // CNS V82.15: Elite V2.2 Jittered Exponential Backoff (Hardened)
        const baseDelay = 5000;
        const maxDelay = 60000;
        const delay = Math.min(maxDelay, baseDelay * Math.pow(2, Math.min(retryCount, 5))) + (Math.random() * 2000);
        
        retryCount++;
        pulseRetryTimeout = setTimeout(connectPulse, delay);
      }
    };
  };

  const disconnectPulse = () => {
    if (pulseRetryTimeout) clearTimeout(pulseRetryTimeout);
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  };

  const handleBusyState = (isBusy: boolean) => {
    // Elite V2.2: Luôn luôn kết nối Pulse Stream khi Admin Panel có phiên đăng nhập hợp lệ thêu sếp!
    // Không ngắt kết nối khi rỗi (IDLE) để đảm bảo nhận các sự kiện hệ thống (Khách chat, Đơn hàng mới, Gọi lại khẩn...)
    connectPulse();
  };

  const shouldSkipSync = (campaign_id: string): boolean => {
    if (!campaign_id) return false;
    const lastTime = liveCampaigns.get(campaign_id);
    if (!lastTime) return false;
    return (Date.now() - lastTime) < 5000;
  };

  return {
    handleBusyState,
    disconnectPulse,
    shouldSkipSync,
    get isConnected() { return !!eventSource; }
  };
}
