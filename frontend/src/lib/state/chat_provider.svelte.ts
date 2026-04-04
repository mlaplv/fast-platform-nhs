import { setContext, getContext } from 'svelte';
import { apiClient } from '$lib/utils/apiClient';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    status: 'DONE' | 'PROCESSING' | 'FAILED';
    task_id?: string;
    timestamp: Date;
}

export class ChatState {
    messages = $state<ChatMessage[]>([]);
    isTyping = $state(false);
    sessionId = $state<string | null>(null);
    pulseEventSource = $state<EventSource | null>(null);
    reconnectAttempts = 0;
    maxReconnects = 3;

    constructor(initialSessionId?: string) {
        this.sessionId = initialSessionId || null;
    }

    async sendMessage(text: string, productSlug?: string) {
        if (!text.trim()) return;

        // 1. Optimistic Update (User Message)
        const userMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: 'user',
            content: text,
            status: 'DONE',
            timestamp: new Date()
        };
        this.messages.push(userMsg);
        this.isTyping = true;

        try {
            // 2. Call the Triage API (Sync)
            const response = await apiClient.post<any>('/api/v1/client/support/chat', {
                message: text,
                session_id: this.sessionId,
                product_slug: productSlug
            });

            this.sessionId = response.session_id;

            // 3. Handle Immediate Response (Tier 1) vs Async (Tier 2/3)
            if (response.status === 'DONE') {
                this.messages.push({
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: response.reply,
                    status: 'DONE',
                    timestamp: new Date()
                });
                this.isTyping = false;
            } else {
                // 🚀 Tier 2/3: Async Task tracking
                const placeholderId = crypto.randomUUID();
                this.messages.push({
                    id: placeholderId,
                    role: 'assistant',
                    content: response.reply, // "Helen đang xử lý..."
                    status: 'PROCESSING',
                    task_id: response.task_id,
                    timestamp: new Date()
                });

                // 🚀 Tier 2/3: Elite Pulse Integration (V2.2 SSE Real-time)
                // The actual update will come through the ClientPulseController.
                this.connectPulse(this.sessionId!);
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.messages.push({
                id: crypto.randomUUID(),
                role: 'assistant',
                content: 'Dạ hệ thống đang bận, sếp vui lòng thử lại sau nhé! 🌸',
                status: 'FAILED',
                timestamp: new Date()
            });
            this.isTyping = false;
        }
    }

    // 🚀 Elite Pulse Integration: SSE Handler (Viral 2026 Proto)
    connectPulse(sessionId: string) {
        if (this.pulseEventSource) {
            this.pulseEventSource.close();
        }

        const url = `/api/v1/client/support/pulse/${sessionId}`;
        this.pulseEventSource = new EventSource(url);

        this.pulseEventSource.onopen = () => {
            console.log('[Pulse] Connection established');
            this.reconnectAttempts = 0; // Reset on success
        };

        this.pulseEventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.event === 'SUPPORT_RESPONSE_READY') {
                    this.handlePulseUpdate(data.payload);
                }
            } catch (error) {
                console.error('[Pulse] Content parse error:', error);
            }
        };

        this.pulseEventSource.onerror = (error) => {
            console.error('[Pulse] Connection lost:', error);
            if (this.pulseEventSource) {
                this.pulseEventSource.close();
                this.pulseEventSource = null;
            }

            // 🚀 Auto-Reconnect Logic (R00/V2.2)
            if (this.reconnectAttempts < this.maxReconnects) {
                this.reconnectAttempts++;
                console.log(`[Pulse] Retrying connection (${this.reconnectAttempts}/${this.maxReconnects})...`);
                setTimeout(() => this.connectPulse(sessionId), 3000);
            } else {
                console.warn('[Pulse] Max reconnect attempts reached.');
                this.isTyping = false; // Stop spinner if we can't connect
            }
        };
    }

    handlePulseUpdate(payload: any) {
        if (payload.status === 'DONE') {
            // Find the placeholder message for this session
            const index = this.messages.findLastIndex(m => m.status === 'PROCESSING');
            if (index !== -1) {
                this.messages[index].content = payload.reply;
                this.messages[index].status = 'DONE';
                this.isTyping = false;
            }
            
            // Auto-close Pulse connection once response is fully delivered (R00 RAM check)
            if (this.pulseEventSource) {
                this.pulseEventSource.close();
                this.pulseEventSource = null;
            }
        }
    }
}

const CHAT_KEY = Symbol('CHAT_STATE');

export function setChatContext(initialSessionId?: string) {
    const state = new ChatState(initialSessionId);
    setContext(CHAT_KEY, state);
    return state;
}

export function getChatContext(): ChatState {
    return getContext(CHAT_KEY);
}
