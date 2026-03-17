import { apiClient } from "$lib/utils/apiClient";
import type { Notification } from "./types";

export function createNotificationState() {
  const state = $state({
    notifications: [] as Notification[],
    isLoading: false,
  });

  async function fetchNotifications() {
    if (state.isLoading) return;
    state.isLoading = true;
    try {
      const res = await apiClient.get<{ data: Notification[] }>(
        "/api/v1/notifications",
      );
      state.notifications = res.data || [];
    } catch {
      state.notifications = [];
    } finally {
      state.isLoading = false;
    }
  }

  async function markNotificationAsRead(id: string) {
    try {
      await apiClient.patch(`/api/v1/notifications/${id}/read`, {});
      const note = state.notifications.find((n) => n.id === id);
      if (note) note.isRead = true;
    } catch (e) {
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
    },
    fetchNotifications,
    markNotificationAsRead,
  };
}
