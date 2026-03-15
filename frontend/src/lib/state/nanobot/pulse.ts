import { normalizeAssets } from "./utils";
import { isDev } from "./env";
import type { CampaignData, PulseSignal, SystemLog, IntentResponse, ToastType } from "../types";

// CNS V70: Voice Discipline — maps server severity to frontend action
const VOICE_DISCIPLINE = {
  CRITICAL: "interrupt",  // Speaks immediately
  ACTION:   "patient",   // Waits for idle, then speaks
  PROGRESS: "ping",      // Silent 808 neural ping only
  INFO:     "silent"     // Bell count only, no audio
} as const;

type VoiceDiscipline = typeof VOICE_DISCIPLINE[keyof typeof VOICE_DISCIPLINE];

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
    setPhase: (phase: string) => void;
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
  let idleDisconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  let retryCount = 0;

  const connectPulse = () => {
    if (typeof window === "undefined" || eventSource) return;

    eventSource = new EventSource("/api/v1/pulse/stream");

    eventSource.onopen = () => {
      retryCount = 0;
    };

    eventSource.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        const { event: eventName, payload }: { event: string; payload: unknown } = data;

        if (eventName === "CONTENT_PROGRESS") {
          const contentPayload = payload as CampaignData & { message: string; data?: Record<string, unknown> };
          if (voice?.vuiResponse?.data?.campaign_id === contentPayload.campaign_id) {
            vuiState.setActive(true);
            vuiState.setPhase("executing");
            vuiState.setSystemMessage(contentPayload.message);

              const current = voice.vuiResponse.data as unknown as CampaignData;
              const newData = (contentPayload.data || {}) as Record<string, unknown>;
              const goldMeta = (newData.gold_metadata || {}) as Record<string, unknown>;
              const topicData = (newData.topic_data || {}) as Record<string, unknown>;
              const keywordsData = (newData.keywords || {}) as Record<string, unknown>;

              voice.vuiResponse.data = {
                  ...current,
                  progress_msg: contentPayload.message,
                  status: "PROCESSING",
                  step: contentPayload.step,
                  keywords: (newData.keywords || newData.topic_data || current.keywords) as CampaignData["keywords"],
                  assets: normalizeAssets(newData.assets || newData.assets_data || current.assets),
                  outline: (newData.outline || newData.outline_data || current.outline) as CampaignData["outline"],
                  draft_content: (newData.draft_content || current.draft_content) as string,
                  selectedAvatarUrl: (goldMeta.avatar as string) || current.selectedAvatarUrl || null,
                  selectedAssetIndex: (goldMeta.selected_index as number) ?? current.selectedAssetIndex ?? 0,
                  reserve_assets: normalizeAssets((goldMeta.reserve_assets as string[]) || current.reserve_assets),
                  creation_config: (goldMeta.creation_config as Record<string, unknown>) ||
                                   (topicData.creation_config as Record<string, unknown>) ||
                                   (keywordsData.creation_config as Record<string, unknown>) ||
                                   current.creation_config || {}
              } as unknown as Record<string, unknown>;
            }

            const existingLogs = [...log.activityLogs];
            const logIdx = existingLogs.findIndex(l =>
              l.data?.campaign_id === contentPayload.campaign_id &&
              String(l.data?.step ?? "") === String(contentPayload.step ?? "")
            );
            if (logIdx !== -1) {
              const current = (existingLogs[logIdx].data || {}) as Record<string, unknown>;
              const newData = contentPayload.data || {};
              existingLogs[logIdx].data = {
                ...current,
                step: contentPayload.step,
                status: "PROCESSING",
                progress_msg: contentPayload.message,
                keywords: newData.keywords || newData.topic_data || current.keywords,
                assets: normalizeAssets(newData.assets || newData.assets_data || current.assets),
                outline: newData.outline || newData.outline_data || current.outline,
                draft_content: newData.draft_content || current.draft_content
              };
              log.setActivityLogs(existingLogs);
            }
            startSmartPolling();
        } else if (eventName === "BACKTRACK") {
          const backtrackPayload = payload as { campaign_id: string; step: number; reason: string };
          log.addLog(`🔄 AI: ${backtrackPayload.reason || 'Đang sửa lại nội dung...'}`, "XOHI", "warning", 2, {
            campaign_id: backtrackPayload.campaign_id, step: backtrackPayload.step
          });
          if (voice.vuiResponse?.data?.campaign_id === backtrackPayload.campaign_id) {
            vuiState.setPhase("executing");
            if (voice.vuiResponse?.data) {
              voice.vuiResponse.data = {
                ...voice.vuiResponse.data,
                status: "PROCESSING",
                step: backtrackPayload.step,
                progress_msg: "🔄 Hệ thống đang tự động sửa lại bản thảo..."
              };
            }
          }
          startSmartPolling();
        } else if (eventName === "CONTENT_STEP_COMPLETED") {
          const completedPayload = payload as CampaignData & { message: string };
          if (voice?.vuiResponse?.data?.campaign_id === completedPayload.campaign_id) {
              vuiState.setActive(true);
              vuiState.setPhase("idle");
              vuiState.setIsWaitingForAction(true);

              if (!voice.vuiResponse) {
                voice.setVoiceResult("Neural Update", "Cập nhật từ hệ thống...", "CONTENT_CREATE", { campaign_id: completedPayload.campaign_id }, "text");
              }

              if (voice.vuiResponse?.data) {
                const current = voice.vuiResponse.data;
                const newData = completedPayload.data || {};

                voice.vuiResponse.data = {
                    ...current,
                    status: completedPayload.status,
                    step: completedPayload.step,
                    progress_msg: "",
                    keywords: newData.keywords || newData.topic_data || current.keywords,
                    assets: normalizeAssets(newData.assets || newData.assets_data || current.assets),
                    outline: newData.outline || newData.outline_data || current.outline,
                    draft_content: newData.draft_content || current.draft_content,
                    final_html: newData.final_html || current.final_html,
                    unique_score: newData.unique_score || current.unique_score,
                    analysis_cache: newData.gold_metadata?.analysis_cache || current.analysis_cache || {},
                    analysis_metrics: newData.gold_metadata?.analysis_metrics || current.analysis_metrics || {},
                    selectedAvatarUrl: (newData.gold_metadata?.avatar as string) || (current as CampaignData).selectedAvatarUrl || null,
                    selectedAssetIndex: (newData.gold_metadata?.selected_index as number) ?? (current as CampaignData).selectedAssetIndex ?? 0,
                    reserve_assets: normalizeAssets((newData.gold_metadata?.reserve_assets as string[]) || (current as CampaignData).reserve_assets),
                    creation_config: (newData.gold_metadata?.creation_config as Record<string, unknown>) || (newData.topic_data?.creation_config as Record<string, unknown>) || (newData.keywords?.creation_config as Record<string, unknown>) || (current as CampaignData).creation_config || {}
                } as unknown as Record<string, unknown>;
              }
          }

          const existingLogs = [...log.activityLogs];
          const logIdx = existingLogs.findIndex(l => l.data?.campaign_id === completedPayload.campaign_id && l.data?.step === completedPayload.step);
          if (logIdx !== -1) {
            existingLogs[logIdx].data = { ...existingLogs[logIdx].data, status: completedPayload.status, ...(completedPayload.data || {}) };
            log.setActivityLogs(existingLogs);
          } else {
            log.addLog(completedPayload.message || `Bước ${completedPayload.step} hoàn tất.`, "XOHI", "info", 2, {
              category: "CONTENT_CREATE",
              campaign_id: completedPayload.campaign_id,
              step: completedPayload.step,
              status: completedPayload.status,
              ...(completedPayload.data || {}),
              assets: normalizeAssets(completedPayload.data?.assets)
            });
          }
          startSmartPolling();
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
              vuiController.interruptSpeech();
              vuiState.setActive(true);
              vuiState.setPhase("idle");
              vuiController.speak(message);
            }).catch(() => {});
          } else if (discipline === "patient") {
            import("$lib/vui").then(({ vuiController, vuiState }) => {
              vuiState.setActive(true);
              vuiState.setPhase("idle");
              vuiController.playNotificationPing();
              setTimeout(() => vuiController.speak(message), 800);
            }).catch(() => {});
          } else if (discipline === "ping") {
            import("$lib/vui").then(({ vuiController }) => {
              vuiController.playNotificationPing();
            }).catch(() => {});
          }
        }
      } catch (err) {
        // Fallback error handling if structure is broken
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
    if (isBusy) {
      if (idleDisconnectTimeout) clearTimeout(idleDisconnectTimeout);
      connectPulse();
    } else {
      if (idleDisconnectTimeout) clearTimeout(idleDisconnectTimeout);
      idleDisconnectTimeout = setTimeout(() => {
        disconnectPulse();
      }, 15000);
    }
  };

  return {
    handleBusyState,
    disconnectPulse,
    get isConnected() { return !!eventSource; }
  };
}
