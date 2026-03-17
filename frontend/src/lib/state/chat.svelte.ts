import { apiClient } from "$lib/utils/apiClient";
import type { SystemLog } from "./types";
import { safeRandomUUID, sanitizeId } from "./utils";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: { text: string; [key: string]: unknown };
  modality: string;
  timestamp: Date;
}

interface ChatApiMessage {
  id: string;
  role: "user" | "assistant";
  content: { text: string; [key: string]: unknown };
  modality: string;
  created_at: string;
}

interface ChatApiResponse {
  messages: ChatApiMessage[];
  next_cursor: string | null;
  has_more: boolean;
}

/**
 * Fire-and-forget: persist a single message to DB via POST /api/v1/chat/sessions/{sid}/messages.
 * Non-blocking — errors are logged but never bubble up to the UI.
 */
export function persistMessage(
  sessionId: string,
  role: "user" | "assistant",
  text: string,
  modality: string = "text",
  extra?: Record<string, unknown>,
) {
  const content: Record<string, unknown> = { text, ...extra };
  apiClient
    .post(`/api/v1/chat/sessions/${sessionId}/messages`, {
      role,
      content,
      modality,
    })
    .catch((e: unknown) => console.warn("[Persist] Save failed:", (e as Error).message));
}

export function createChatState(
  addLogFn: (msg: string, src?: string) => void,
  showToastFn?: (msg: string, type: "success" | "error" | "info") => void,
) {
  const cache = new Map<string, { data: ChatApiResponse; timestamp: number }>();
  const CHAT_CACHE_TTL = 60_000; // 60 seconds

  const state = $state({
    history: [] as ChatMessage[],
    pagination: {
      cursor: null as string | null,
      hasMore: true,
      isLoading: false,
    },
  });

  // Internal helper to avoid code duplication and satisfy SWR
  function _processLogs(hydrated: ChatMessage[]): SystemLog[] {
    const logsToAppend: SystemLog[] = [];
    for (const m of hydrated) {
      if (m.role === "user") {
        logsToAppend.push({
          id: m.id,
          message: m.content.text,
          source: "SẾP",
          timestamp: m.timestamp,
          type: "info",
        });
      } else if (m.role === "assistant") {
        const textContent = m.content.text || (m.content.message as string) || "";
        if (textContent && textContent !== "NONE" && textContent.trim().length > 0) {
          // Flatten nested data if present (Rule R86: Persistence Hardening)
          const metadata = (m.content.data ? { ...m.content, ...(m.content.data as Record<string, unknown>) } : m.content) as Record<string, unknown>;

          logsToAppend.push({
            id: m.id + "_text",
            message: textContent,
            source: "XÔ-HỈ",
            timestamp: m.timestamp,
            type: "info",
            routerTier: metadata.router_tier as string | undefined,
            data: { ...metadata, role: "assistant" }, // Flat metadata structure for consistency
          });
        }
      }
    }
    return logsToAppend;
  }

  async function hydrateHistory(
    sessionId: string,
    appendLogsCallback?: (logs: SystemLog[]) => void,
    userId?: string, // Added for God-Mode
    sinceId?: string, // R82.35: Delta Polling support
    forceRefresh = false,
  ) {
    const targetSessionId = sessionId || "account";
    const cleanUserId = sanitizeId(userId);
    const cacheKey = cleanUserId ? `${targetSessionId}:${cleanUserId}` : targetSessionId;

    if (forceRefresh) cache.delete(cacheKey);

    // ═══════════════════════════════════════════════════════
    // SWR Strategy (Stale-While-Revalidate)
    // ═══════════════════════════════════════════════════════
    const cached = cache.get(cacheKey);
    const now = Date.now();

    // Delta polling bypasses standard cache TTL because it's additive
    if (!sinceId && cached && (now - cached.timestamp < CHAT_CACHE_TTL)) {
       // Return cached data immediately to UI (Zero Latency)
       state.history = cached.data.messages.map((m: ChatApiMessage) => ({
         id: m.id,
         role: m.role,
         content: m.content,
         modality: m.modality,
         timestamp: new Date(m.created_at),
       }));
       state.pagination.cursor = cached.data.next_cursor;
       state.pagination.hasMore = cached.data.has_more;

       if (appendLogsCallback) {
         // Process logs from cache
         const logs = _processLogs(state.history);
         appendLogsCallback(logs);
       }
       return;
    }

    if (state.pagination.isLoading) return;
    state.pagination.isLoading = true;
    try {
      let url = cleanUserId
        ? `/api/v1/chat/sessions/${targetSessionId}/messages?limit=35&user_id_query=${cleanUserId}`
        : `/api/v1/chat/sessions/${targetSessionId}/messages?limit=35`;

      if (sinceId) {
        url += (url.includes("?") ? "&" : "?") + `since_id=${sinceId}`;
      }

      const data = await apiClient.get<ChatApiResponse>(url);

      // Update Cache
      cache.set(cacheKey, { data, timestamp: now });

      const hydrated = data.messages.map((m: ChatApiMessage) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        modality: m.modality,
        timestamp: new Date(m.created_at),
      }));

      state.history = sinceId ? [...state.history, ...hydrated] : hydrated;
      state.pagination.cursor = sinceId ? state.pagination.cursor : data.next_cursor;
      state.pagination.hasMore = sinceId ? state.pagination.hasMore : data.has_more;

      // Update Cache with merged data if it's a delta sync
      if (sinceId && cached) {
        cached.data.messages = [...cached.data.messages, ...data.messages];
        cached.timestamp = now;
      } else {
        cache.set(cacheKey, { data, timestamp: now });
      }

      if (appendLogsCallback) {
        const logs = _processLogs(hydrated);
        appendLogsCallback(logs);
      }
    } catch (e: unknown) {
      const err = e as { status?: number };
      if (err?.status === 429) {
        showToastFn?.("Truy cập quá nhanh, vui lòng thử lại sau giây lát.", "error");
      } else {
        showToastFn?.("Không thể tải lịch sử trò chuyện.", "error");
      }
    } finally {
      state.pagination.isLoading = false;
    }
  }

  async function loadMoreMessages(
    appendLogsCallback?: (logs: SystemLog[]) => void,
    sessionId: string = "account",
    userId?: string, // Added for God-Mode
  ) {
    if (!state.pagination.hasMore || state.pagination.isLoading) return;

    state.pagination.isLoading = true;
    const cleanUserId = sanitizeId(userId);
    try {
      const url = cleanUserId
        ? `/api/v1/chat/sessions/${sessionId}/messages?cursor=${state.pagination.cursor}&limit=20&user_id_query=${cleanUserId}`
        : `/api/v1/chat/sessions/${sessionId}/messages?cursor=${state.pagination.cursor}&limit=20`;

      const data = await apiClient.get<ChatApiResponse>(url);

      const olderMessages = data.messages.map((m: ChatApiMessage) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        modality: m.modality,
        timestamp: new Date(m.created_at),
      }));

      state.history = [...olderMessages, ...state.history];
      state.pagination.cursor = data.next_cursor;
      state.pagination.hasMore = data.has_more;

      if (appendLogsCallback) {
        const logs = _processLogs(olderMessages);
        appendLogsCallback(logs);
      }
    } catch (e: unknown) {
      const err = e as { status?: number };
      if (err?.status === 429) {
        showToastFn?.("Yêu cầu quá dồn dập, hãy thử lại sau.", "error");
      }
    } finally {
      state.pagination.isLoading = false;
    }
  }

  async function clearHistory(sessionId: string) {
    if (!sessionId) return;
    state.pagination.isLoading = true;
    try {
      await apiClient.delete(`/api/v1/chat/sessions/${sessionId}/messages`);
      state.history = [];
      state.pagination.cursor = null;
      state.pagination.hasMore = false;
      addLogFn("Chat history has been permanently cleared.", "System");
      return true;
    } catch (e: unknown) {
      addLogFn("Failed to clear chat history.", "Err");
      return false;
    } finally {
      state.pagination.isLoading = false;
    }
  }

  return {
    get history() {
      return state.history;
    },
    get pagination() {
      return state.pagination;
    },
    hydrateHistory,
    loadMoreMessages,
    clearHistory,
  };
}
