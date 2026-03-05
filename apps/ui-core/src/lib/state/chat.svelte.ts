import { apiClient } from "$lib/utils/apiClient";
import type { SystemLog } from "./types";
import { safeRandomUUID } from "./utils";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: { text: string };
  modality: string;
  timestamp: Date;
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
    .catch((e: any) => console.warn("[Persist] Save failed:", e?.message));
}

export function createChatState(addLogFn: (msg: string, src?: string) => void) {
  const state = $state({
    history: [] as ChatMessage[],
    pagination: {
      cursor: null as string | null,
      hasMore: true,
      isLoading: false,
    },
  });

  async function hydrateHistory(
    sessionId: string,
    appendLogsCallback?: (logs: SystemLog[]) => void,
    userId?: string, // Added for God-Mode
  ) {
    const targetSessionId = sessionId || "account";
    if (state.pagination.isLoading) return;
    state.pagination.isLoading = true;
    try {
      const url = userId
        ? `/api/v1/chat/sessions/${targetSessionId}/messages?limit=35&user_id_query=${userId}`
        : `/api/v1/chat/sessions/${targetSessionId}/messages?limit=35`;

      const data = await apiClient.get<any>(url);

      const hydrated = data.messages.map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        modality: m.modality,
        timestamp: new Date(m.created_at),
      }));

      state.history = hydrated;
      state.pagination.cursor = data.next_cursor;
      state.pagination.hasMore = data.has_more;

      if (appendLogsCallback) {
        const logsToAppend: any[] = [];
        for (const m of hydrated) {
          if (m.role === "user") {
            logsToAppend.push({
              id: m.id,
              message: m.content.text,
              source: "[ADMIN]",
              timestamp: m.timestamp,
              type: "info",
            });
          } else if (m.role === "assistant") {
            if (
              m.content.text &&
              m.content.text !== "NONE" &&
              m.content.text.trim().length > 0
            ) {
              logsToAppend.push({
                id: m.id + "_text",
                message: m.content.text,
                source: "XOHI",
                timestamp: m.timestamp,
                type: "info",
                routerTier: m.content.router_tier,
              });
            }
          }
        }
        appendLogsCallback(logsToAppend);
      }
    } catch (e) {
      console.error("Failed to hydrate history", e);
      // Fallback or retry logic could go here
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
    try {
      const url = userId
        ? `/api/v1/chat/sessions/${sessionId}/messages?cursor=${state.pagination.cursor}&limit=20&user_id_query=${userId}`
        : `/api/v1/chat/sessions/${sessionId}/messages?cursor=${state.pagination.cursor}&limit=20`;

      const data = await apiClient.get<any>(url);

      const olderMessages = data.messages.map((m: any) => ({
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
        const logsToAppend: any[] = [];
        for (const m of olderMessages) {
          if (m.role === "user") {
            logsToAppend.push({
              id: m.id,
              message: m.content.text,
              source: "[ADMIN]",
              timestamp: m.timestamp,
              type: "info",
            });
          } else if (m.role === "assistant") {
            if (
              m.content.text &&
              m.content.text !== "NONE" &&
              m.content.text.trim().length > 0
            ) {
              logsToAppend.push({
                id: m.id + "_text",
                message: m.content.text,
                source: "XOHI",
                timestamp: m.timestamp,
                type: "info",
              });
            }
          }
        }
        appendLogsCallback(logsToAppend);
      }
    } catch (e) {
      console.error("Failed to load more messages", e);
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
    } catch (e) {
      console.error("Failed to clear history", e);
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
