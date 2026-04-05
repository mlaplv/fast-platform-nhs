import type { components as CoreComponents } from './core';

export interface paths {
    "/api/v1/chat/sessions/{session_id}/messages": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["ChatHistoryResponse"]; }; }; }; };
        post: {
            requestBody: { content: { "application/json": components["schemas"]["CreateChatMessageRequest"]; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["ChatMessageSchema"]; }; }; };
        };
    };
    "/api/v1/intent/map": {
        get: { responses: { 200: { content: { "application/json": Record<string, any>; }; }; }; };
        post: {
            requestBody: { content: { "application/json": Record<string, any>; }; };
            responses: { 201: { content: { "application/json": Record<string, any>; }; }; };
        };
    };
    "/api/v1/tts/stream": {
        get: { responses: { 200: { content: { "application/json": Record<string, any>; }; }; }; };
    };
}

export interface components {
    schemas: {
        ChatHistoryResponse: { session_id: string; messages: components["schemas"]["ChatMessageSchema"][]; next_cursor?: string; has_more: boolean; };
        ChatMessageSchema: { id: string; sessionId: string; userId: string; role: string; content: unknown; modality: string; createdAt: string; updatedAt: string; };
        CreateChatMessageRequest: { role: string; content: unknown; modality?: string; };
        IntentRequest: { query: string; user_id?: string; session_id?: string; modality?: string; context?: unknown; screen_context?: unknown; };
        IntentResponse: { status: string; message: string; action?: unknown; router_tier?: unknown; data?: unknown; semantic_results?: unknown; vui_context?: unknown; cost_tokens: number; };
        IntentAction: "READ" | "MUTATE" | "ANALYZE" | string;
        RouterTier: number | string;
        ToolCallRequest: { name: string; arguments: Record<string, any>; };
    };
}
