import { apiClient } from "$lib/utils/apiClient";
import { normalizeAssets } from "./utils";
import { permissionState } from "../permissions.svelte";
import { isDev } from "./env";

export function createResumeManager(state: any, voice: any, log: any, ui: any, startSmartPolling: () => void) {
  let greetingActive = false;
  let pendingGreetingUnlock: (() => void) | null = null;

  const cleanupGreeting = () => {
    greetingActive = false;
    if (pendingGreetingUnlock) {
      if (isDev()) console.log("[Resume] Cleaning up pending subtle greeting listener.");
      window.removeEventListener('click', pendingGreetingUnlock);
      pendingGreetingUnlock = null;
    }
  };

  const internalResumeCampaign = async (logEntry: any, isSilent = false) => {
    cleanupGreeting();
    if (isSilent) greetingActive = true;
    if (!logEntry?.data?.campaign_id) return;
    const campaignId = logEntry.data.campaign_id;
    
    let campaignData: any = logEntry.data; 
    try {
      const campaign = await apiClient.get<any>(`/api/v1/content/campaigns/${campaignId}`);
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
          selectedAvatarUrl: campaign.gold_metadata?.avatar || null,
          selectedAssetIndex: campaign.gold_metadata?.selected_index ?? 0,
          creation_config: campaign.gold_metadata?.creation_config || {}
        };
      }
    } catch (e) {
      console.warn("[Resume] Could not fetch campaign from API, using log data as fallback:", e);
    }
    
    voice.setVoiceResult(
      isSilent ? "Neural Link Restored" : "Khôi phục phiên làm việc",
      logEntry.text || logEntry.message || "Đang tiếp tục bài viết cũ...",
      "CONTENT_CREATE",
      { ...campaignData, isSilent }, 
      isSilent ? "text" : "voice", 
      logEntry.routerTier || 2
    );
    
    if (isSilent && !state.isResumingManually) {
      greetingActive = true;
      const title = campaignData?.keywords?.title || campaignData?.topic_data?.title || campaignData?.title || 'bản thảo cũ';
      
      const trySpeak = async () => {
         if (!greetingActive) return;
         const currentUserName = permissionState.userName || "Admin";
         const greeting = `Chào mừng ${currentUserName} trở lại! Tôi đã khôi phục bản thảo "${title}".`;
         
         const { vuiState, vuiController } = await import("$lib/vui");
         vuiController.interruptSpeech(); 
         vuiState.setActive(true);
         vuiState.setPhase("idle");
         
         // Phase 46: Signal presence with a subtle ping before the greeting
         vuiController.playNotificationPing();
         
         // Phase 44/46: Leverage the AudioEngine's "Patient Mode". 
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
    get latestResumeableLog() {
      if (!log.activityLogs.length) return null;
      const actionable = log.activityLogs
        .filter((l: any) => (l.data?.campaign_id || l.data?.keywords || l.data?.assets) && (parseInt(String(l.data?.step || 0)) < 6))
        .sort((a: any, b: any) => b.timestamp.getTime() - a.timestamp.getTime());
      
      if (actionable.length === 0) return null;
      const latestCampaignId = actionable[0].data?.campaign_id;
      if (!latestCampaignId) return actionable[0];
      
      const campaignLogs = actionable.filter(l => l.data?.campaign_id === latestCampaignId);
      campaignLogs.sort((a: any, b: any) => {
          const stepA = parseInt(String(a.data?.step || 0));
          const stepB = parseInt(String(b.data?.step || 0));
          return stepB - stepA;
      });
      return campaignLogs[0];
    }
  };
}
