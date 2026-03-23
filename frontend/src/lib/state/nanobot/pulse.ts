import { normalizeAssets } from "./utils";
import { isDev } from "./env";
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
  CampaignStatus
} from "../types";

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
  state: Record<string, unknown>;
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
    addPendingSignal?: (signal: { id: string; message: string; severity: string; isRead: boolean }) => void;
  };
}

export function createPulseManager(
  state: PulseDeps["state"],
  voice: PulseDeps["voice"],
  log: PulseDeps["log"],
  ui: PulseDeps["ui"],
  vuiState: PulseDeps["vuiState"],
  notification: PulseDeps["notification"],
  startSmartPolling: () => void
) {
  let eventSource: EventSource | null = null;
  let pulseRetryTimeout: ReturnType<typeof setTimeout> | null = null;
  let retryCount = 0;
  
  // Phase 82: Sync Guard — Prevent DB sync from overwriting fresh SSE data
  let liveCampaigns = new Map<string, number>(); // campaign_id -> last_sse_completed_timestamp

  const handleVisibilityChange = () => {
    if (document.visibilityState === "visible" && !eventSource) {
      connectPulse();
    }
  };

  const connectPulse = () => {
    if (typeof window === "undefined" || eventSource) return;

    eventSource = new EventSource("/api/v1/pulse/stream");

    if (typeof window !== "undefined") {
      window.removeEventListener("visibilitychange", handleVisibilityChange);
      window.addEventListener("visibilitychange", handleVisibilityChange);
    }

    eventSource.onopen = () => {
      retryCount = 0;
    };

    eventSource.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        const { event: eventName, payload }: { event: string; payload: any } = data;
        const activeData = (state.currentData as unknown as CampaignData);
        console.log(`[Pulse] Received event: ${eventName} for CID: ${payload?.campaign_id}`);
        if (activeData) {
          console.log(`[Pulse] Active CID: ${activeData.campaign_id || (activeData as any).id}`);
          const match = activeData.campaign_id === payload?.campaign_id || (activeData as any).id === payload?.campaign_id;
          console.log(`[Pulse] CID Match: ${match}`);
        }

        if (eventName === "CONTENT_PROGRESS") {
          const contentPayload = payload as CampaignData & { message: string; data?: Record<string, any> };
          const newData = (contentPayload.data || {}) as Record<string, any>;
          const goldMeta = (newData.gold_metadata || {}) as Record<string, any>;

          if (voice?.vuiResponse?.data && (voice.vuiResponse.data as any).campaign_id === contentPayload.campaign_id) {
            vuiState.setActive(true);
            vuiState.setPhase("executing");
            vuiState.setSystemMessage(contentPayload.message);
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

          if (voice.vuiResponse?.data && (voice.vuiResponse.data as any).campaign_id === contentPayload.campaign_id) {
            syncTarget(voice.vuiResponse.data as unknown as CampaignData);
          }
          if (activeData && (activeData.campaign_id === contentPayload.campaign_id || (activeData as any).id === contentPayload.campaign_id)) {
            syncTarget(activeData);
          }

          const existingLogs = [...log.activityLogs];
          const logIdx = existingLogs.findIndex(l =>
            l.data?.campaign_id === contentPayload.campaign_id &&
            String(l.data?.step ?? "") === String(contentPayload.step ?? "")
          );
          if (logIdx !== -1) {
            const current = (existingLogs[logIdx].data || {}) as Record<string, any>;
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
          
          if (voice.vuiResponse?.data && (voice.vuiResponse.data as any).campaign_id === backtrackPayload.campaign_id) {
            vuiState.setPhase("executing");
            const d = voice.vuiResponse.data as unknown as CampaignData;
            d.status = "PROCESSING"; d.step = backtrackPayload.step;
            d.progress_msg = "🔄 Hệ thống đang tự động sửa lại bản thảo...";
          }
          if (activeData && (activeData.campaign_id === backtrackPayload.campaign_id || (activeData as any).id === backtrackPayload.campaign_id)) {
             activeData.status = "PROCESSING"; activeData.step = backtrackPayload.step;
             activeData.progress_msg = "🔄 Hệ thống đang tự động sửa lại bản thảo...";
          }
          startSmartPolling();
        } else if (eventName === "CONTENT_STEP_COMPLETED") {
          const completedPayload = payload as CampaignData & { message: string; data?: any };
          const rawData = (completedPayload.data || completedPayload || {}) as CampaignData;
          const goldMeta = (rawData.gold_metadata || {}) as Record<string, any>;

          if (completedPayload.campaign_id) {
            liveCampaigns.set(completedPayload.campaign_id, Date.now());
          }

          // Ensure voice response exists if this is the active campaign
          if (!voice.vuiResponse && (activeData?.campaign_id === completedPayload.campaign_id || (activeData as any)?.id === completedPayload.campaign_id)) {
             voice.setVoiceResult("Neural Update", "Cập nhật từ hệ thống...", "CONTENT_CREATE", { campaign_id: completedPayload.campaign_id }, "text");
          }

          if (voice.vuiResponse?.data && (voice.vuiResponse.data as any).campaign_id === completedPayload.campaign_id) {
            vuiState.setActive(true); vuiState.setPhase("idle");
            vuiState.setIsWaitingForAction(true);
          }
          console.log(`[Pulse] STEP_COMPLETED Syncing assets: ${completedPayload.data?.assets?.length || 0}, Reserves: ${completedPayload.data?.gold_metadata?.reserve_assets?.length || 0}`);

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
            console.log(`[Pulse] Successfully re-assigned currentData for Step ${updated.step}`);
          };

          if (voice.vuiResponse?.data && (voice.vuiResponse.data as any).campaign_id === completedPayload.campaign_id) {
            syncCompleted(voice.vuiResponse.data as unknown as CampaignData);
          }
          if (activeData && (activeData.campaign_id === completedPayload.campaign_id || (activeData as any).id === completedPayload.campaign_id)) {
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

          if (voice.vuiResponse?.data && (voice.vuiResponse.data as any).campaign_id === chunkPayload.campaign_id) {
             syncChunk(voice.vuiResponse.data as unknown as CampaignData);
             liveCampaigns.set(chunkPayload.campaign_id, Date.now());
          }
          if (activeData && (activeData.campaign_id === chunkPayload.campaign_id || (activeData as any).id === chunkPayload.campaign_id)) {
             syncChunk(activeData);
             liveCampaigns.set(chunkPayload.campaign_id, Date.now());
          }
        } else if (eventName === "SYSTEM_SIGNAL") {
          const signalPayload = payload as PulseSignal;
          const { message, severity, notification_id } = signalPayload;
          const discipline: VoiceDiscipline = VOICE_DISCIPLINE[severity as keyof typeof VOICE_DISCIPLINE] ?? "silent";

          if (typeof notification.addPendingSignal === "function") {
            notification.addPendingSignal({ id: notification_id, message, severity, isRead: false });
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
          const purgePayload = payload as { campaign_id: string; type?: string; action?: string };
          const cid = purgePayload.campaign_id;
          const logs = [...log.activityLogs];
          const filtered = logs.filter(l => l.data?.campaign_id !== cid);
          if (filtered.length !== logs.length) log.setActivityLogs(filtered);
          
          if (voice.vuiResponse?.data && (voice.vuiResponse.data as any).campaign_id === cid) {
            voice.clearVuiResponse(); vuiState.setActive(false); vuiState.setPhase("idle");
          }
          if (activeData && (activeData.campaign_id === cid || (activeData as any).id === cid)) {
             state.currentData = null;
          }
          ui.showToast("Chiến dịch đã được quét sạch khỏi hệ thống.", "success");
        }
      } catch (err) {
        // Fallback error
      }
    };

    eventSource.onerror = (err) => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
        const delay = Math.min(30000, 5000 * Math.pow(1.5, retryCount));
        retryCount++;
        pulseRetryTimeout = setTimeout(connectPulse, delay);
      }
    };
  };

  const disconnectPulse = () => {
    if (pulseRetryTimeout) clearTimeout(pulseRetryTimeout);
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  };

  const handleBusyState = (isBusy: boolean) => {
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
