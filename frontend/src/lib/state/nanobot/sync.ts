import { apiClient } from "$lib/utils/apiClient";
import { untrack } from "svelte";
import { permissionState } from "../permissions.svelte";
import type { CampaignData, SystemLog, ToastType } from "../types";

interface SyncDeps {
  state: {
    godModeUser?: string;
  };
  log: {
    activityLogs: SystemLog[];
    upsertLogs: (logs: SystemLog[]) => void;
  };
  chat: {
    hydrateHistory: (
      sessionId: string,
      callback: (logs: SystemLog[]) => void,
      userId?: string,
      sinceId?: string
    ) => Promise<void>;
  };
  notification: {
    fetchNotifications: () => Promise<void>;
  };
  ui: {
    showToast: (msg: string, type: ToastType) => void;
  };
  setDynamicIntentMap: (val: Record<string, string>) => void;
  resumeManager: {
    internalResumeCampaign: (log: SystemLog, isSilent: boolean) => Promise<void>;
  };
  pulseManager: {
    isConnected: boolean;
  };
}

export function createSyncManager(
  state: SyncDeps["state"],
  log: SyncDeps["log"],
  chat: SyncDeps["chat"],
  notification: SyncDeps["notification"],
  ui: SyncDeps["ui"],
  setDynamicIntentMap: SyncDeps["setDynamicIntentMap"],
  resumeManager: SyncDeps["resumeManager"],
  pulseManager: SyncDeps["pulseManager"]
) {
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
      const hasActiveCampaign = log.activityLogs.some((l: SystemLog) =>
        l.data?.category === "CONTENT_CREATE" && l.data?.status === "PROCESSING"
      );
      if (!hasActiveCampaign) { stopSmartPolling(); return; }

      // V12: Avoid polling if pulse is active unless forced
      const interval = pulseManager.isConnected ? 30000 : 5000;

      // Node.js vs Browser interval check workaround
      const currentInterval = (pollingInterval as unknown as { _idleTimeout?: number })._idleTimeout;
      if (currentInterval !== undefined && currentInterval !== interval) {
        stopSmartPolling();
        startSmartPolling();
        return;
      }

      const lastLog = log.activityLogs[log.activityLogs.length - 1];
      const sinceId = lastLog?.id?.split("_")[0]; // Remove _text suffix if present

      await chat.hydrateHistory("account", (logs: SystemLog[]) => {
        log.upsertLogs(logs);
      }, state.godModeUser || undefined, sinceId);
    }, pulseManager.isConnected ? 30000 : 5000);
  };

  const fetchDynamicIntents = async () => {
    try {
      const mapping = await apiClient.get<Record<string, string>>("/api/v1/intent/map");
      if (mapping) {
        setDynamicIntentMap(mapping);
      }
    } catch (e) {
      console.error("[Sync] Failed to fetch dynamic intent map:", e);
    }
  };

  const initHydration = () => {
    if (typeof window === "undefined") return;

    fetchDynamicIntents();
    notification.fetchNotifications();
    chat.hydrateHistory("account", (logs: SystemLog[]) => {
      log.upsertLogs(logs);
      
      const justLoggedIn = sessionStorage.getItem("xohi_just_logged_in") === "true";
      sessionStorage.removeItem("xohi_just_logged_in");

      if (justLoggedIn) {
        const uniqueLogs = log.activityLogs;
        const pending = [...uniqueLogs].reverse().find((l: SystemLog) =>
          l.data?.campaign_id &&
          l.data?.status !== "COMPLETED" &&
          (l.data?.status === "WAITING_FOR_REVIEW" || l.data?.status === "PROCESSING" || (parseInt(String(l.data?.step || 0)) < 6))
        );

        if (pending) {
          setTimeout(() => resumeManager.internalResumeCampaign(pending, true), 1200);
        } else {
          setTimeout(() => {
            import("$lib/vui").then(({ vuiController, vuiState }) => {
              const userName = (permissionState as { userName?: string })?.userName || "Bạn";
              vuiState.setActive(true);
              vuiState.setPhase("idle");
              vuiController.playNotificationPing();
              setTimeout(() => vuiController.speak(`Chào mừng ${userName} trở lại. Hệ thống đã sẵn sàng.`), 800);
            }).catch(() => {});
          }, 1500);
        }
      }

      if (logs.some((l: SystemLog) => l.data?.status === "PROCESSING")) startSmartPolling();
    }, state.godModeUser || undefined);
  };

  return {
    startSmartPolling,
    stopSmartPolling,
    initHydration
  };
}
