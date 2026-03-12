import { apiClient } from "$lib/utils/apiClient";
import { untrack } from "svelte";
import { permissionState } from "../permissions.svelte";

export function createSyncManager(state: any, log: any, chat: any, notification: any, ui: any, resumeManager: any, pulseManager: any) {
  let pollingInterval: ReturnType<typeof setInterval> | undefined;

  const stopSmartPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = undefined;
    }
  };

  const startSmartPolling = () => {
    if (pollingInterval) return;
    pollingInterval = setInterval(async () => {
      const hasActiveCampaign = log.activityLogs.some((l: any) => 
        l.data?.category === "CONTENT_CREATE" && (l.data?.status === "PROCESSING" || (l.data?.step || 0) < 6)
      );
      if (!hasActiveCampaign) { stopSmartPolling(); return; }

      const interval = pulseManager.isConnected ? 30000 : 5000;
      if (pollingInterval && (pollingInterval as any)._idleTimeout !== interval) {
        stopSmartPolling();
        startSmartPolling();
        return;
      }

      await chat.hydrateHistory("account", (logs: any) => {
        log.upsertLogs(logs);
      }, state.godModeUser || undefined);
    }, pulseManager.isConnected ? 30000 : 5000);
  };

  const initHydration = () => {
    if (typeof window === "undefined") return;

    notification.fetchNotifications();
    chat.hydrateHistory("account", (logs: any) => {
      log.upsertLogs(logs);
      const uniqueLogs = log.activityLogs;
      const pending = [...uniqueLogs].reverse().find((l: any) => l.data?.campaign_id && (l.data?.status === "WAITING_FOR_REVIEW" || l.data?.status === "PROCESSING" || (parseInt(String(l.data?.step || 0)) < 6)));
      
      if (pending) {
        ui.showToast(`Phát hiện bản thảo cũ. Đang khôi phục...`, "info", 5000);
        setTimeout(() => resumeManager.internalResumeCampaign(pending, true), 1200);
      } else {
        // CNS V70.1: Default Voice Greeting on Login if nothing is pending
        setTimeout(() => {
          import("$lib/vui").then(({ vuiController, vuiState }) => {
            const userName = (permissionState as any)?.userName || "Bạn";
            vuiState.setActive(true);
            vuiState.setPhase("idle");
            vuiController.playNotificationPing();
            setTimeout(() => vuiController.speak(`Chào mừng ${userName} trở lại. Hệ thống đã sẵn sàng.`), 800);
          }).catch(() => {});
        }, 1500);
      }

      if (logs.some((l: any) => l.data?.status === "PROCESSING")) startSmartPolling();
    }, state.godModeUser || undefined);
  };

  return {
    startSmartPolling,
    stopSmartPolling,
    initHydration
  };
}
