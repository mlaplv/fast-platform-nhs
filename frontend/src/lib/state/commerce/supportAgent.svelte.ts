// Support Agent State — Svelte 5 Runes (Elite V2.2 Persistent Memory)
import { apiClient } from "$lib/utils/apiClient";
import { browser } from "$app/environment";

// Helper để render UUID native
function randomId() {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
        return crypto.randomUUID();
    }
    return Math.random().toString(36).substring(2, 15);
}

export interface SupportProductInfo {
    id: string;
    name: string;
    price: number;
    price_display: string;
    slug: string;
}

export interface SupportMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
    intent?: string;
    productInfo?: SupportProductInfo; // Elite V2.2: Explicit typing
}

export interface SupportConfig {
    agentName: string;
    welcomeMessage: string;
}

const STORAGE_KEY = "fp_helen_sid";

class SupportAgentState {
    // Reactive State Variables (Svelte 5 Runes)
    isOpen = $state(false);
    isTyping = $state(false);
    isHistoryLoading = $state(false);
    hasMoreHistory = $state(true);
    messages = $state<SupportMessage[]>([]);
    
    // Persistent Session UUID
    private _sessionId: string = "";

    // Config initialized once
    public config: SupportConfig = {
        agentName: "Chuyên viên Tư vấn",
        welcomeMessage: "Chào bạn! Mình có thể hỗ trợ gì cho bạn hôm nay ạ?"
    };

    constructor() {
        if (browser) {
            const savedSid = localStorage.getItem(STORAGE_KEY);
            if (savedSid) {
                this._sessionId = savedSid;
            } else {
                this._sessionId = randomId();
                localStorage.setItem(STORAGE_KEY, this._sessionId);
            }
        } else {
            this._sessionId = randomId();
        }
    }

    get sessionId() {
        return this._sessionId;
    }

    /**
     * Call this inside a root +layout.svelte or onMount to initialize config and load history
     */
    async init(envAgentName?: string) {
        if (envAgentName) {
            this.config.agentName = envAgentName;
            this.config.welcomeMessage = `Dạ chào bạn, mình là ${envAgentName}. Bạn cần hỗ trợ thông tin gì về sản phẩm hay chính sách ạ?`;
        }

        // Only load history once or if empty
        if (this.messages.length === 0) {
            await this.loadHistory(20);
            
            // If still no messages after loading history, add welcome message
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
    }

    /**
     * Paginated history loader (Zalo-style)
     */
    async loadHistory(limit: number = 20) {
        if (this.isHistoryLoading || !this.hasMoreHistory) return;

        this.isHistoryLoading = true;
        try {
            const firstMsgId = this.messages[0]?.id;
            const params: Record<string, any> = {
                session_id: this._sessionId,
                limit
            };
            
            // Only attach cursor if we actually have messages
            if (firstMsgId) {
                params.before_id = firstMsgId;
            }

            const res = await apiClient.get(`/api/v1/client/support/history`, { params });

            if (Array.isArray(res)) {
                const history = res.map((m: any) => ({
                    id: m.id,
                    role: m.role,
                    content: m.content,
                    intent: m.intent,
                    timestamp: new Date(m.timestamp)
                }));

                if (history.length < limit) {
                    this.hasMoreHistory = false;
                }

                if (history.length > 0) {
                    // Prepend history to current thread
                    this.messages = [...history, ...this.messages];
                }
            }
        } catch (error) {
            console.error("[SupportAgent] History load error:", error);
            this.hasMoreHistory = false; // Stop trying on error
        } finally {
            this.isHistoryLoading = false;
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

        const userMsg: SupportMessage = {
            id: randomId(),
            role: "user",
            content: text.trim(),
            timestamp: new Date()
        };

        this.messages = [...this.messages, userMsg];
        this.isTyping = true;

        try {
            const res = await apiClient.post("/api/v1/client/support/chat", {
                message: text.trim(),
                session_id: this._sessionId,
                product_slug: productSlug || null
            });

            if (res && typeof (res as any).reply === "string") {
                const data = res as any;
                this.messages = [
                    ...this.messages,
                    {
                        id: randomId(),
                        role: "assistant",
                        content: data.reply || "Xin lỗi, mình tạm thời không phản hồi được ạ.",
                        intent: data.intent,
                        productInfo: data.product_info,
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
