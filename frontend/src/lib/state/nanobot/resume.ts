import { apiClient } from "$lib/utils/apiClient";
import { normalizeAssets } from "./utils";
import { permissionState } from "../permissions.svelte";
import { isDev } from "./env";
import type { SystemLog, CampaignData } from "../types";
import { sanitizeId } from "../utils";
import { nanobot } from "../nanobot.svelte";

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
      routerTier?: number
    ) => void;
  };
  log: {
    activityLogs: SystemLog[];
    addLog: (msg: string, source?: string, type?: string, tier?: number, data?: Record<string, unknown>) => void;
    closeFullLog: () => void;
  };
  ui: {
    showToast: (msg: string, type: string) => void;
  };
}

export function createResumeManager(
  state: ResumeDeps["state"],
  voice: ResumeDeps["voice"],
  log: ResumeDeps["log"],
  ui: ResumeDeps["ui"],
  startSmartPolling: () => void
) {
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
    cleanupGreeting();
    if (isSilent) greetingActive = true;

    // Robust Extraction (Phase 4): Handle both LogEntry and raw Campaign object
    const campaignId = (logOrCampaign as SystemLog)?.data?.campaign_id || (logOrCampaign as CampaignData)?.id || (logOrCampaign as Record<string, unknown>)?.campaign_id as string;
    if (!campaignId) {
      console.warn("[Resume] Missing campaign_id in payload:", logOrCampaign);
      return;
    }

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
      console.warn("[Resume] Could not fetch campaign from API, using log data as fallback:", e);
    }

    voice.setVoiceResult(
      isSilent ? "Neural Link Restored" : "Khôi phục phiên làm việc",
      (logOrCampaign as SystemLog).message || (logOrCampaign as Record<string, unknown>).text as string || "Đang tiếp tục bài viết cũ...",
      "CONTENT_CREATE",
      { ...campaignData, isSilent },
      isSilent ? "text" : "voice",
      (logOrCampaign as SystemLog).routerTier || 2
    );

    if (isSilent && !state.isResumingManually) {
      greetingActive = true;
      const title = (campaignData?.keywords as Record<string, unknown>)?.title || (campaignData?.topic_data as Record<string, unknown>)?.title || (campaignData as Record<string, unknown>).title || 'bản thảo cũ';

      const trySpeak = async () => {
         if (!greetingActive) return;
         const currentUserName = (permissionState as Record<string, unknown>).userName as string || "Admin";

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
         }
      };

      setTimeout(trySpeak, 1500);
    } else {
      import("$lib/vui").then(({ vuiState }) => {
        vuiState.setActive(true);
        if (campaignData.status === "WAITING_FOR_REVIEW" || campaignData.category === "CONTENT_CREATE") {
          vuiState.setPhase("idle");
          vuiState.setIsWaitingForAction(true);
        } else {
          vuiState.setPhase("executing");
          startSmartPolling();
        }
      });
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
