import { apiClient } from "$lib/utils/apiClient";
import type { Notification } from "./types";
import { authStore } from "./authStore.svelte";
import { permissionState } from "./permissions.svelte";
import { vuiController } from "$lib/vui";
import { isAdminDomain } from "./nanobot/env";

export function createNotificationState() {
  const state = $state({
    notifications: [] as Notification[],
    isLoading: false,
    hasInit: false,
    nextCursor: null as string | null,
    hasMore: false,
    
    // Trash Bin State
    trashNotifications: [] as Notification[],
    isTrashLoading: false,
    trashHasInit: false,
    trashNextCursor: null as string | null,
    trashHasMore: false,
  });


  async function fetchNotifications(reset: boolean = true) {
    // CNS V92: Auth guard — admin panel uses osmo:auth:user_info (authStore purges legacy keys on login)
    // authStore.svelte.ts line 84-86: removes admin_token & access_token → must check user_info key
    const hasAdminToken = typeof window !== 'undefined' &&
      !!(localStorage.getItem('osmo:auth:user_info'));
    const hasAuth = authStore.isAuthenticated || hasAdminToken || !!permissionState.user;

    if (!hasAuth) {
      state.notifications = [];
      state.hasInit = false;
      state.nextCursor = null;
      state.hasMore = false;
      return;
    }
    // Prevent overlapping requests
    if (state.isLoading) return;

    state.isLoading = true;
    try {
      let parsedData: Notification[] = [];
      if (isAdminDomain()) {
        const cursor = reset ? null : state.nextCursor;
        const url = cursor
          ? `/api/v1/notifications/paginated?cursor=${encodeURIComponent(cursor)}&limit=20`
          : `/api/v1/notifications/paginated?limit=20`;
        const res = await apiClient.get<{ data: any[], next_cursor: string | null, has_more: boolean }>(url);
        
        parsedData = (res.data || []).map((note: Record<string, any>) => {
          let msg = (note.message || "") as string;
          let payload: Record<string, unknown> = {};
          if (msg.includes(" |metadata:")) {
            const parts = msg.split(" |metadata:");
            msg = parts[0];
            try {
              payload = JSON.parse(parts[1]);
            } catch (e) {
              console.error("Failed to parse metadata", e);
            }
          }
          // CNS V92: Normalize API camelCase → snake_case (Pydantic alias sends createdAt, type expects created_at)
          return {
            id: note.id as string,
            type: (note.type || "INFO") as string,
            message: msg,
            isRead: !!(note.isRead ?? note.is_read),
            created_at: (note.createdAt || note.created_at || new Date().toISOString()) as string,
            payload,
            signal_type: note.signal_type as string | undefined,
          } satisfies Notification;
        });
        
        state.nextCursor = res.next_cursor || null;
        state.hasMore = !!res.has_more;
      } else {
        // Client side simple fetch
        const res = await apiClient.get<{ data: any[] }>("/api/v1/client/notifications");
        parsedData = (res.data || []).map((note: Record<string, any>) => {
          let msg = (note.message || "") as string;
          let payload: Record<string, unknown> = {};
          if (msg.includes(" |metadata:")) {
            const parts = msg.split(" |metadata:");
            msg = parts[0];
            try {
              payload = JSON.parse(parts[1]);
            } catch (e) {
              console.error("Failed to parse metadata", e);
            }
          }
          return {
            id: note.id as string,
            type: (note.type || "INFO") as string,
            message: msg,
            isRead: !!(note.isRead ?? note.is_read),
            created_at: (note.createdAt || note.created_at || new Date().toISOString()) as string,
            payload,
            signal_type: note.signal_type as string | undefined,
          } satisfies Notification;
        });
        state.nextCursor = null;
        state.hasMore = false;
      }

      if (reset) {
        // CNS V91: MERGE strategy — preserve SSE-added items not yet persisted to DB
        const dbIds = new Set(parsedData.map((n: Notification) => n.id));
        const sseOnly = state.notifications.filter(n => !dbIds.has(n.id) && n.id.startsWith("sse-"));
        state.notifications = [...sseOnly, ...parsedData].slice(0, 200);
      } else {
        // Merge and deduplicate for pagination loading
        const existingIds = new Set(state.notifications.map(n => n.id));
        const uniqueNew = parsedData.filter(n => !existingIds.has(n.id));
        state.notifications = [...state.notifications, ...uniqueNew];
      }
      state.hasInit = true;
    } catch (e: unknown) {
      // CNS V91: On error — do NOT wipe existing state
      if (e && typeof e === 'object' && 'status' in e && (e as { status: number }).status !== 409) {
        console.error("[NotificationState] fetch failed — keeping existing state", e);
      }
    } finally {
      state.isLoading = false;
    }
  }

  async function markNotificationAsRead(id: string) {
    try {
      const endpoint = isAdminDomain()
        ? `/api/v1/notifications/${id}/read`
        : `/api/v1/client/notifications/${id}/read`;
      await apiClient.patch(endpoint, {});
      const note = state.notifications.find((n) => n.id === id);
      if (note) note.isRead = true;
    } catch (e: unknown) {
      console.error("Failed to mark notification as read", e);
    }
  }

  async function bulkDeleteNotifications(ids: string[]) {
    try {
      await apiClient.post("/api/v1/notifications/bulk-delete", { ids });
      state.notifications = state.notifications.filter((n) => !ids.includes(n.id));
    } catch (e: unknown) {
      console.error("Failed to bulk delete notifications", e);
    }
  }

  async function clearNotifications(filterType: string) {
    try {
      await apiClient.post("/api/v1/notifications/clear", { filter_type: filterType });
      if (filterType === "ALL") {
        state.notifications = [];
      } else {
        state.notifications = state.notifications.filter(n => {
          const type = (n.type || "").toUpperCase();
          if (filterType === "ORDER") {
            return !(type.includes("ORDER") || type.includes("COMMERCE"));
          }
          if (filterType === "CHAT") {
            return !(type === "CHAT" || type.includes("SUPPORT"));
          }
          if (filterType === "SECURITY") {
            return !(type.includes("SECURITY") || type.includes("SYSTEM") || type.includes("ANOMALY"));
          }
          if (filterType === "URGENT") {
            return !(type.includes("URGENT") || type === "CRITICAL");
          }
          return true;
        });
      }
    } catch (e: unknown) {
      console.error("Failed to clear notifications", e);
    }
  }

  return {
    get notifications() {
      return state.notifications;
    },
    get unreadCount() {
      return state.notifications.filter((n) => !n.isRead).length;
    },
    get isLoading() {
      return state.isLoading;
    },
    get nextCursor() {
      return state.nextCursor;
    },
    get hasMore() {
      return state.hasMore;
    },
    setNotifications: (val: Notification[]) => {
      state.notifications = val;
    },
    // CNS V91: Real-time Bell sync — add from SSE, dedup by ID, no API round-trip
    addPendingSignal: (signal: { id: string; message: string; severity: string; isRead: boolean; payload?: Record<string, any>; signal_type?: string }): boolean => {
      // Dedup gate: skip if this notification_id already in state (double SSE delivery)
      if (signal.id && state.notifications.some(n => n.id === signal.id)) {
        console.debug(`[NotificationState] Skipped duplicate signal: ${signal.id}`);
        return false;
      }

      const notif: Notification = {
        id: signal.id.startsWith("sse-") ? signal.id : `sse-${signal.id}`,
        message: signal.message,
        isRead: signal.isRead,
        type: signal.signal_type || signal.severity,
        created_at: new Date().toISOString(),
        payload: signal.payload
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
      return true;
    },
    fetchNotifications,
    markNotificationAsRead,
    bulkDeleteNotifications,
    clearNotifications,
    
    // Trash Bin Methods and Getters
    get trashNotifications() {
      return state.trashNotifications;
    },
    get isTrashLoading() {
      return state.isTrashLoading;
    },
    get trashNextCursor() {
      return state.trashNextCursor;
    },
    get trashHasMore() {
      return state.trashHasMore;
    },
    get trashHasInit() {
      return state.trashHasInit;
    },
    fetchTrashNotifications: async (reset: boolean = true) => {
      const hasAdminToken = typeof window !== 'undefined' &&
        !!(localStorage.getItem('osmo:auth:user_info'));
      const hasAuth = authStore.isAuthenticated || hasAdminToken || !!permissionState.user;

      if (!hasAuth) {
        state.trashNotifications = [];
        state.trashHasInit = false;
        state.trashNextCursor = null;
        state.trashHasMore = false;
        return;
      }
      if (state.isTrashLoading) return;

      state.isTrashLoading = true;
      try {
        if (isAdminDomain()) {
          const cursor = reset ? null : state.trashNextCursor;
          const url = cursor
            ? `/api/v1/notifications/trash?cursor=${encodeURIComponent(cursor)}&limit=20`
            : `/api/v1/notifications/trash?limit=20`;
          const res = await apiClient.get<{ data: any[], next_cursor: string | null, has_more: boolean }>(url);
          
          const parsedData = (res.data || []).map((note: Record<string, any>) => {
            let msg = (note.message || "") as string;
            let payload: Record<string, unknown> = {};
            if (msg.includes(" |metadata:")) {
              const parts = msg.split(" |metadata:");
              msg = parts[0];
              try {
                payload = JSON.parse(parts[1]);
              } catch (e) {
                console.error("Failed to parse metadata", e);
              }
            }
            return {
              id: note.id as string,
              type: (note.type || "INFO") as string,
              message: msg,
              isRead: !!(note.isRead ?? note.is_read),
              created_at: (note.createdAt || note.created_at || new Date().toISOString()) as string,
              payload,
              signal_type: note.signal_type as string | undefined,
            } satisfies Notification;
          });

          state.trashNextCursor = res.next_cursor || null;
          state.trashHasMore = !!res.has_more;

          if (reset) {
            state.trashNotifications = parsedData;
          } else {
            const existingIds = new Set(state.trashNotifications.map(n => n.id));
            const uniqueNew = parsedData.filter(n => !existingIds.has(n.id));
            state.trashNotifications = [...state.trashNotifications, ...uniqueNew];
          }
          state.trashHasInit = true;
        }
      } catch (e: unknown) {
        console.error("[NotificationState] fetch trash failed", e);
      } finally {
        state.isTrashLoading = false;
      }
    },
    restoreNotifications: async (ids: string[]) => {
      try {
        await apiClient.post("/api/v1/notifications/trash/restore", { ids });
        state.trashNotifications = state.trashNotifications.filter((n) => !ids.includes(n.id));
        // Reload active notifications
        await fetchNotifications(true);
      } catch (e: unknown) {
        console.error("Failed to restore notifications", e);
      }
    },
    hardDeleteNotifications: async (ids: string[]) => {
      try {
        await apiClient.post("/api/v1/notifications/trash/hard-delete", { ids });
        if (ids.length === 0) {
          state.trashNotifications = [];
        } else {
          state.trashNotifications = state.trashNotifications.filter((n) => !ids.includes(n.id));
        }
      } catch (e: unknown) {
        console.error("Failed to hard delete notifications", e);
      }
    }
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
