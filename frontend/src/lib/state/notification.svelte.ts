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
      state.notifications = await apiClient.get<Notification[]>(
        "/api/v1/notifications",
      );
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
    fetchNotifications,
    markNotificationAsRead,
  };
}
