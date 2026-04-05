import { apiClient } from "$lib/utils/apiClient";
import { normalizeAssets } from "./utils";
import { permissionState } from "../permissions.svelte";
import { isDev } from "./env";
import type { SystemLog, CampaignData, ToastType } from "../types";
import { sanitizeId } from "../utils";
import { useNanobot } from "../nanobot.svelte";

interface ResumeDeps {
  state: {
    isResumingManually: boolean;
  };
  voice: {
    setVoiceResult: (
      transcript: string,
      responseText: string,
      uiAction: string,
      data?: Record<string, unknown>,
      source?: "text" | "voice",
      routerTier?: string | number
    ) => void;
  };
  log: {
    activityLogs: SystemLog[];
    setActivityLogs: (logs: SystemLog[]) => void;
    addLog: (msg: string, source?: string, type?: string, tier?: string | number, data?: Record<string, unknown>) => void;
    closeFullLog: () => void;
  };
  ui: {
    showToast: (msg: string, type: ToastType) => void;
  };
  chat: {
    clearLocalSession: (sessionId: string, userId?: string) => void;
    sweepCampaignFromCache: (campaignId: string) => void;
  };
}

export function createResumeManager(
  state: ResumeDeps["state"],
  voice: ResumeDeps["voice"],
  log: ResumeDeps["log"],
  ui: ResumeDeps["ui"],
  chat: ResumeDeps["chat"],
  startSmartPolling: () => void
) {
  const processingCids = new Set<string>();
  const staleCids = new Set<string>();
  let greetingActive = false;
  let pendingGreetingUnlock: (() => void) | null = null;

  const cleanupGreeting = () => {
    greetingActive = false;
    if (pendingGreetingUnlock) {
      window.removeEventListener('click', pendingGreetingUnlock);
      pendingGreetingUnlock = null;
    }
  };

  const internalResumeCampaign = async (logOrCampaign: SystemLog | CampaignData, isSilent = false) => {
    const nanobot = useNanobot();
    cleanupGreeting();
    if (isSilent) greetingActive = true;

    // Robust Extraction (Phase 4): Handle both LogEntry and raw Campaign object
    const campaignId = (logOrCampaign as SystemLog)?.data?.campaign_id || (logOrCampaign as CampaignData)?.id || (logOrCampaign as Record<string, unknown>)?.campaign_id as string;
    if (!campaignId) {
      console.warn("[Resume] Missing campaign_id in payload:", logOrCampaign);
      return;
    }

    // CNS V82.12: Neural Lock & Stale Cache Check
    if (processingCids.has(campaignId)) return;
    if (staleCids.has(campaignId)) {
       ui.showToast("Chiến dịch này đã được xác nhận là không còn tồn tại.", "error");
       return;
    }

    processingCids.add(campaignId);

    let campaignData: Record<string, unknown> = ((logOrCampaign as SystemLog)?.data || logOrCampaign) as Record<string, unknown>;
    try {
      const cleanUserId = sanitizeId(nanobot.godModeUser);
      const url = cleanUserId
        ? `/api/v1/content/campaigns/${campaignId}?user_id_query=${cleanUserId}`
        : `/api/v1/content/campaigns/${campaignId}`;
      const campaign = await apiClient.get<Record<string, unknown>>(url);
      
      if (campaign?.id) {
        campaignData = {
          category: "CONTENT_CREATE",
          campaign_id: campaign.id,
          step: campaign.current_step,
          status: campaign.status,
          keywords: campaign.topic_data,
          assets: normalizeAssets(campaign.assets_data),
          outline: campaign.outline_data,
          draft_content: campaign.draft_content,
          final_html: campaign.final_html,
          selectedAvatarUrl: (campaign.gold_metadata as Record<string, unknown>)?.avatar || null,
          selectedAssetIndex: (campaign.gold_metadata as Record<string, unknown>)?.selected_index ?? 0,
          reserve_assets: normalizeAssets((campaign.gold_metadata as Record<string, unknown>)?.reserve_assets),
          creation_config: (campaign.gold_metadata as Record<string, unknown>)?.creation_config || {},
          analysis_cache: (campaign.gold_metadata as Record<string, unknown>)?.analysis_cache || {},
          analysis_metrics: (campaign.gold_metadata as Record<string, unknown>)?.analysis_metrics || {}
        };
      }
    } catch (e) {
      const err = e as { status?: number; message?: string };
      if (err?.status === 404) {
        ui.showToast("Dạ thưa Sếp, chiến dịch này đã được xóa khỏi hệ thống rồi ạ.", "error");
        
        // CNS V82.12: Permanently mark as stale to block ghost re-fetches
        staleCids.add(campaignId);

        // CNS V82.11: Proactive cleanup of stale log entry
        const logs = [...log.activityLogs];
        const filtered = logs.filter(l => l.data?.campaign_id !== campaignId);
        if (filtered.length !== logs.length) log.setActivityLogs(filtered);
        
        // Signal chat to perform deep-state sweep for this ghost CID
        chat.sweepCampaignFromCache(campaignId);
        return;
      }
      console.warn("[Resume] Could not fetch campaign from API, using log data as fallback:", e);
    } finally {
      processingCids.delete(campaignId);
    }

    voice.setVoiceResult(
      isSilent ? "Neural Link Restored" : "Khôi phục phiên làm việc",
      (logOrCampaign as SystemLog).message || (logOrCampaign as Record<string, unknown>).text as string || "Đang tiếp tục bài viết cũ...",
      "CONTENT_CREATE",
      { ...campaignData, isSilent },
      "text", // Force "text" so the backend does not mistakenly open VUI thinking it was a voice command
      (logOrCampaign as SystemLog).routerTier || "2"
    );

    if (isSilent && !state.isResumingManually) {
      greetingActive = true;
      const title = (campaignData?.keywords as Record<string, unknown>)?.title || (campaignData?.topic_data as Record<string, unknown>)?.title || (campaignData as Record<string, unknown>).title || 'bản thảo cũ';

      const trySpeak = async () => {
         if (!greetingActive) return;
         const currentUserName = permissionState.userName || "Admin";

         // V71.5: Rich Voice Notification
         const step = parseInt(String(campaignData?.step || 1));
         const stepNames: Record<number, string> = {
            1: "Ý tưởng",
            2: "Hình ảnh",
            3: "Dàn bài",
            4: "Nội dung",
            5: "Xuất bản"
         };
         const currentStepName = stepNames[step] || "Sáng tạo";
         const nextStepName = stepNames[step + 1] || "Hoàn tất";

         let greeting = `Chào mừng ${currentUserName} trở lại! Bạn đang ở bước ${currentStepName} cho bản thảo "${title}".`;

         // Scores extraction
         const scores: string[] = [];
         const copyright = (campaignData?.analysis_cache as Record<string, unknown>)?.copyright ? ((((campaignData.analysis_cache as Record<string, unknown>).copyright as Record<string, unknown>).data as Record<string, unknown>)?.uniqueness_score) : (campaignData as Record<string, unknown>).uniqueness_score;
         if (copyright !== undefined && copyright !== null) {
            scores.push(`COPYRIGHT ${Math.round(Number(copyright) * 100)}%`);
         }

         const seoScore = ((campaignData?.analysis_cache as Record<string, unknown>)?.seo as Record<string, unknown>) ? (((((campaignData.analysis_cache as Record<string, unknown>).seo as Record<string, unknown>).data as Record<string, unknown>))?.total_score) : undefined;
         if (seoScore !== undefined && seoScore !== null) {
            scores.push(`SEO ${seoScore} điểm`);
         }

         const aiScore = ((campaignData?.analysis_cache as Record<string, unknown>)?.ai_inspect as Record<string, unknown>) ? (((((campaignData.analysis_cache as Record<string, unknown>).ai_inspect as Record<string, unknown>).data as Record<string, unknown>))?.geo_score) : undefined;
         if (aiScore !== undefined && aiScore !== null) {
            scores.push(`AI score ${aiScore}%`);
         }

         if (scores.length > 0) {
            greeting += ` Điểm số hiện tại: ${scores.join(", ")}.`;
         }

         greeting += ` Bước tiếp theo là ${nextStepName}.`;

         const { vuiState, vuiController } = await import("$lib/vui");
         vuiController.interruptSpeech();
         vuiState.setActive(true);
         vuiState.setPhase("idle");

         // Phase 46: Signal presence with a subtle ping before the greeting
         vuiController.playNotificationPing();

         const success = await vuiController.speak(greeting);
         if (success) {
           log.addLog(`Neural Link Restored: Đã khôi phục bản thảo cho ${currentUserName}.`, "SYS", "success");
           cleanupGreeting();
           vuiState.setActive(false); // Decouple: Close VUI immediately after welcoming the user!
         }
      };

      setTimeout(trySpeak, 1500);
    } else {
      if (campaignData.status === "WAITING_FOR_REVIEW" || campaignData.category === "CONTENT_CREATE" || campaignData.campaign_id) {
         // Decoupled from VUI: Mở độc lập UniversalModal, KHÔNG dính dáng vuiState
         import("$lib/vui").then(({ vuiState }) => {
            vuiState.setActive(false);
         });
      } else {
         import("$lib/vui").then(({ vuiState }) => {
            vuiState.setActive(true);
            vuiState.setPhase("executing");
            startSmartPolling();
         });
      }
    }
    state.isResumingManually = false;
    log.closeFullLog();
  };

  return {
    cleanupGreeting,
    internalResumeCampaign,
    get latestResumeableLog(): SystemLog | null {
      if (!log.activityLogs.length) return null;
      const actionable = log.activityLogs
        .filter((l: SystemLog) => (l.data?.campaign_id || l.data?.keywords || l.data?.assets) && (parseInt(String(l.data?.step || 0)) < 6))
        .sort((a: SystemLog, b: SystemLog) => b.timestamp.getTime() - a.timestamp.getTime());

      if (actionable.length === 0) return null;
      const latestCampaignId = actionable[0].data?.campaign_id;
      if (!latestCampaignId) return actionable[0];

      const campaignLogs = actionable.filter(l => l.data?.campaign_id === latestCampaignId);
      campaignLogs.sort((a: SystemLog, b: SystemLog) => {
          const stepA = parseInt(String(a.data?.step || 0));
          const stepB = parseInt(String(b.data?.step || 0));
          return stepB - stepA;
      });
      return campaignLogs[0];
    }
  };
}
