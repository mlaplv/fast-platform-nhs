import { apiClient } from "$lib/utils/apiClient";
import type { Notification } from "./types";
import { authStore } from "./authStore.svelte";
import { vuiController } from "$lib/vui";

export function createNotificationState() {
  const state = $state({
    notifications: [] as Notification[],
    isLoading: false,
    hasInit: false,
  });

  async function fetchNotifications() {
    if (!authStore.isAuthenticated) {
      state.notifications = [];
      state.hasInit = false;
      return;
    }
    // Prevent overlapping requests
    if (state.isLoading) return;

    state.isLoading = true;
    try {
      const res = await apiClient.get<{ data: Notification[] }>(
        "/api/v1/client/notifications",
      );
      state.notifications = res.data || [];
      state.hasInit = true; // CNS V90.1: Successfully loaded at least once
    } catch (e: unknown) {
      // Ignore 409 Conflict as it might be a temporary state or duplicate fetch
      if (e && typeof e === 'object' && 'status' in e && (e as { status: number }).status !== 409) {
        console.error("Failed to fetch notifications", e);
      }
      state.notifications = [];
    } finally {
      state.isLoading = false;
    }
  }

  async function markNotificationAsRead(id: string) {
    try {
      await apiClient.patch(`/api/v1/client/notifications/${id}/read`, {});
      const note = state.notifications.find((n) => n.id === id);
      if (note) note.isRead = true;
    } catch (e: unknown) {
      console.error("Failed to mark notification as read", e);
    }
  }

  return {
    get notifications() {
      return state.notifications;
    },
    get unreadCount() {
      return state.notifications.filter((n) => !n.isRead).length;
    },
    setNotifications: (val: Notification[]) => {
      state.notifications = val;
    },
    // CNS V70: Real-time Bell sync — add from SSE without API round-trip
    addPendingSignal: (signal: { id: string; message: string; severity: string; isRead: boolean }) => {
      const notif: Notification = {
        id: signal.id,
        message: signal.message,
        isRead: signal.isRead,
        type: signal.severity,
        created_at: new Date().toISOString()
      };
      state.notifications = [notif, ...state.notifications].slice(0, 200);

      // 🔈 REAL-TIME TACTICAL AUDIO: "Ting" sound for the Boss (Elite V2.2)
      if (signal.severity === "ACTION" || signal.severity === "CRITICAL") {
        try {
          vuiController.playNotificationPing();
        } catch (e) {
          console.warn("[NotificationState] playNotificationPing failed:", e);
        }
      }
    },
    fetchNotifications,
    markNotificationAsRead,
  };
}
// CNS V88.3: Ultimate Global Singleton Instance
// Using a simple object reference to ensure 100% same instance across all imports
let _instance: ReturnType<typeof createNotificationState> | null = null;

export function getNotificationState() {
  if (!_instance) {
    _instance = createNotificationState();
  }
  return _instance;
}
