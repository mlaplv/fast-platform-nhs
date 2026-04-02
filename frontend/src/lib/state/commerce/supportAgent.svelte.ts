// Support Agent State — Svelte 5 Runes (Zero-Barrier Client Strategy)
import { apiClient } from "$lib/utils/apiClient";

// Helper để render UUID native, tránh lỗi "Cannot find module 'uuid'" trên SSR/Docker
function randomId() {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
        return crypto.randomUUID();
    }
    // Fallback cho môi trường cũ
    return Math.random().toString(36).substring(2, 15);
}

export interface SupportMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
    intent?: string;
}

export interface SupportConfig {
    agentName: string;
    welcomeMessage: string;
}

class SupportAgentState {
    // Reactive State Variables (Svelte 5 Runes)
    isOpen = $state(false);
    isTyping = $state(false);
    messages = $state<SupportMessage[]>([]);
    
    // Persistent Session UUID for Rate Limiting & Telemetry
    private sessionId: string;
    // Config initialized once
    public config: SupportConfig = {
        agentName: "Chuyên viên Tư vấn",
        welcomeMessage: "Chào bạn! Mình có thể hỗ trợ gì cho bạn hôm nay ạ?"
    };

    constructor() {
        // Generate stateless session ID on load
        this.sessionId = randomId();
    }

    /**
     * Call this inside a root +layout.svelte or onMount to initialize config
     */
    init(envAgentName?: string) {
        if (envAgentName) {
            this.config.agentName = envAgentName;
            this.config.welcomeMessage = `Dạ chào bạn, mình là ${envAgentName}. Bạn cần hỗ trợ thông tin gì về sản phẩm hay chính sách ạ?`;
        }
        if (this.messages.length === 0) {
            this.messages = [
                {
                    id: randomId(),
                    role: "assistant",
                    content: this.config.welcomeMessage,
                    timestamp: new Date()
                }
            ];
        }
    }

    toggle() {
        this.isOpen = !this.isOpen;
    }

    close() {
        this.isOpen = false;
    }

    async sendMessage(text: string, productSlug?: string) {
        if (!text.trim() || this.isTyping) return;

        // 1. Append user message optimistically
        const userMsgId = randomId();
        this.messages = [
            ...this.messages,
            {
                id: userMsgId,
                role: "user",
                content: text.trim(),
                timestamp: new Date()
            }
        ];

        this.isTyping = true;

        try {
            // 2. Call secure backend endpoint (Zero-Auth mode)
            const res = await apiClient.post("/api/v1/client/support/chat", {
                message: text.trim(),
                session_id: this.sessionId,
                product_slug: productSlug || null
            });

            // 3. Append assistant reply
            if (res && typeof (res as any).reply === "string") {
                const data = res as any;
                this.messages = [
                    ...this.messages,
                    {
                        id: randomId(),
                        role: "assistant",
                        content: data.reply || "Xin lỗi, mình tạm thời không phản hồi được ạ.",
                        intent: data.intent,
                        timestamp: new Date()
                    }
                ];
            } else {
                throw new Error("Empty response or missing reply field");
            }
        } catch (error: any) {
            console.error("[SupportAgent] Chat error:", error);
            const userFriendlyMsg = error?.status === 429 
                ? "Hệ thống đang xử lý nhiều luồng, bạn vui lòng đợi một lát rồi thử lại nhé!" 
                : "Xin lỗi bạn, hệ thống kết nối đang bị gián đoạn. Bạn vui lòng thử lại sau nhé.";
                
            this.messages = [
                ...this.messages,
                {
                    id: randomId(),
                    role: "assistant",
                    content: userFriendlyMsg,
                    timestamp: new Date()
                }
            ];
        } finally {
            this.isTyping = false;
        }
    }
}

// Global Singleton (Zero-Hydration friendly)
export const supportAgent = new SupportAgentState();
