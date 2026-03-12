import { normalizeAssets } from "./utils";
import { isDev } from "./env";

// CNS V70: Voice Discipline — maps server severity to frontend action
const VOICE_DISCIPLINE = {
  CRITICAL: "interrupt",  // Speaks immediately
  ACTION:   "patient",   // Waits for idle, then speaks
  PROGRESS: "ping",      // Silent 808 neural ping only
  INFO:     "silent"     // Bell count only, no audio
} as const;

type VoiceDiscipline = typeof VOICE_DISCIPLINE[keyof typeof VOICE_DISCIPLINE];

export function createPulseManager(state: any, voice: any, log: any, ui: any, vuiState: any, notification: any, startSmartPolling: () => void) {
  let eventSource: EventSource | null = null;
  let pulseRetryTimeout: ReturnType<typeof setTimeout> | null = null;
  let idleDisconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  let retryCount = 0;

  const connectPulse = () => {
    if (typeof window === "undefined" || eventSource) return;

    if (isDev()) console.log("[Pulse] Connecting to Native Agent Pulse SSE...");
    eventSource = new EventSource("/api/v1/pulse/stream");

    eventSource.onopen = () => {
      retryCount = 0;
      if (isDev()) console.log("[Pulse] Connection established. Pulse Active.");
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { event: eventName, payload } = data;

        if (eventName === "CONTENT_PROGRESS") {
          if (voice?.vuiResponse?.data?.campaign_id === payload.campaign_id) {
            vuiState.setActive(true);
            vuiState.setPhase("executing");
            vuiState.setSystemMessage(payload.message); // CNS V71.6: Keep VUI alive with heartbeat text
            
            if (voice.vuiResponse && voice.vuiResponse.data) {
              const current = voice.vuiResponse.data;
              const newData = payload.data || {};
              
              voice.vuiResponse.data = {
                  ...current,
                  progress_msg: payload.message,
                  status: "PROCESSING",
                  step: payload.step,
                  keywords: newData.keywords || newData.topic_data || current.keywords,
                  assets: normalizeAssets(newData.assets || newData.assets_data || current.assets),
                  outline: newData.outline || newData.outline_data || current.outline,
                  draft_content: newData.draft_content || current.draft_content,
                  selectedAvatarUrl: newData.gold_metadata?.avatar || (current as any).selectedAvatarUrl || null,
                  selectedAssetIndex: newData.gold_metadata?.selected_index ?? (current as any).selectedAssetIndex ?? 0,
                  creation_config: newData.gold_metadata?.creation_config || newData.topic_data?.creation_config || newData.keywords?.creation_config || (current as any).creation_config || {}
              };
            }
          }

          const existingLogs = [...log.activityLogs];
          const logIdx = existingLogs.findIndex(l => 
            l.data?.campaign_id === payload.campaign_id && 
            String(l.data?.step ?? "") === String(payload.step ?? "")
          );
          if (logIdx !== -1) {
            const current = (existingLogs[logIdx].data || {}) as any;
            const newData = payload.data || {};
            existingLogs[logIdx].data = { 
              ...current, 
              step: payload.step, 
              status: "PROCESSING",
              progress_msg: payload.message,
              keywords: newData.keywords || newData.topic_data || current.keywords,
              assets: normalizeAssets(newData.assets || newData.assets_data || current.assets),
              outline: newData.outline || newData.outline_data || current.outline,
              draft_content: newData.draft_content || current.draft_content
            };
            log.setActivityLogs(existingLogs);
          }
          startSmartPolling();
        } else if (eventName === "BACKTRACK") {
          // CNS V70: BACKTRACK = PROGRESS level — log-only, no toast spam
          log.addLog(`🔄 AI: ${payload.reason || 'Đang sửa lại nội dung...'}`, "XOHI", "warning", 2, {
            campaign_id: payload.campaign_id, step: payload.step
          });
          if (voice.vuiResponse?.data?.campaign_id === payload.campaign_id) {
            vuiState.setPhase("executing");
            if (voice.vuiResponse && voice.vuiResponse.data) {
              voice.vuiResponse.data = {
                ...voice.vuiResponse.data,
                status: "PROCESSING",
                step: payload.step,
                progress_msg: "🔄 Hệ thống đang tự động sửa lại bản thảo..."
              };
            }
          }
          startSmartPolling();
        } else if (eventName === "CONTENT_STEP_COMPLETED") {
          if (voice?.vuiResponse?.data?.campaign_id === payload.campaign_id) {
              vuiState.setActive(true);
              vuiState.setPhase("idle"); 
              vuiState.setIsWaitingForAction(true);
              
              // R82.1.1: Intelligent Sync — Ensure modal data is fresh
              if (!voice.vuiResponse) {
                // Initialize if null to allow modal to trigger
                voice.setVoiceResult("Neural Update", "Cập nhật từ hệ thống...", "CONTENT_CREATE", { campaign_id: payload.campaign_id }, "text");
              }

              if (voice.vuiResponse && voice.vuiResponse.data) {
                const current = voice.vuiResponse.data;
                const newData = payload.data || {};
                
                voice.vuiResponse.data = {
                    ...current,
                    status: payload.status,
                    step: payload.step,
                    progress_msg: "", // CNS V71.10: Clear heartbeat msg on success
                    keywords: newData.keywords || newData.topic_data || current.keywords,
                    assets: normalizeAssets(newData.assets || newData.assets_data || current.assets),
                    outline: newData.outline || newData.outline_data || current.outline,
                    draft_content: newData.draft_content || current.draft_content,
                    final_html: newData.final_html || current.final_html,
                    unique_score: newData.unique_score || current.unique_score,
                    analysis_cache: newData.gold_metadata?.analysis_cache || current.analysis_cache || {},
                    analysis_metrics: newData.gold_metadata?.analysis_metrics || current.analysis_metrics || {},
                    selectedAvatarUrl: newData.gold_metadata?.avatar || (current as any).selectedAvatarUrl || null,
                    selectedAssetIndex: newData.gold_metadata?.selected_index ?? (current as any).selectedAssetIndex ?? 0,
                    creation_config: newData.gold_metadata?.creation_config || newData.topic_data?.creation_config || newData.keywords?.creation_config || (current as any).creation_config || {}
                };
              }
          }

          const existingLogs = [...log.activityLogs];
          const logIdx = existingLogs.findIndex(l => l.data?.campaign_id === payload.campaign_id && l.data?.step === payload.step);
          if (logIdx !== -1) {
            existingLogs[logIdx].data = { ...existingLogs[logIdx].data, status: payload.status, ...(payload.data || {}) };
            log.setActivityLogs(existingLogs);
          } else {
            log.addLog(payload.message || `Bước ${payload.step} hoàn tất.`, "XOHI", "info", 2, {
              category: "CONTENT_CREATE",
              campaign_id: payload.campaign_id,
              step: payload.step,
              status: payload.status,
              ...(payload.data || {}),
              assets: normalizeAssets(payload.data?.assets)
            });
          }
          startSmartPolling();
        } else if (eventName === "SYSTEM_SIGNAL") {
          // CNS V70: SignalDistributor — hub for all system alerts
          const { message, severity, notification_id } = payload;
          const discipline: VoiceDiscipline = VOICE_DISCIPLINE[severity as keyof typeof VOICE_DISCIPLINE] ?? "silent";

          if (isDev()) console.log(`[CNS] SYSTEM_SIGNAL [${severity}] -> Voice: ${discipline}`);

          // 1. Real-time Bell sync (no fetch needed)
          if (typeof (notification as any).addPendingSignal === "function") {
            (notification as any).addPendingSignal({ id: notification_id, message, severity, isRead: false });
          }

          // 2. Toast for CRITICAL + ACTION only
          if (discipline === "interrupt") ui.showToast(message, "error", 7000);
          else if (discipline === "patient") ui.showToast(message, "warning", 7000);

          // 3. Voice Discipline
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
          // "silent" = do nothing
        }
      } catch (err) {
        if (isDev()) console.warn("[Pulse] Error parsing data:", err);
      }
    };

    eventSource.onerror = (err) => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
        // Rules R82.36: Hardened Exponential Backoff
        const delay = Math.min(30000, 5000 * Math.pow(1.5, retryCount));
        retryCount++;
        if (isDev()) console.error(`[Pulse] SSE failed. Retrying in ${delay}ms...`);
        pulseRetryTimeout = setTimeout(connectPulse, delay);
      }
    };
  };

  const disconnectPulse = () => {
    if (pulseRetryTimeout) clearTimeout(pulseRetryTimeout);
    if (eventSource) {
      if (isDev()) console.log("[Pulse] Auto-Disconnecting SSE (Idle Mode)...");
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
