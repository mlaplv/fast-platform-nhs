// Support Agent State — Svelte 5 Runes (Elite V2.2 Persistent Memory)
import { apiClient } from "$lib/utils/apiClient";
import { browser } from "$app/environment";
import { getNotificationState } from "$lib/state/notification.svelte";

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
    productInfo?: SupportProductInfo;
    is_revoked?: boolean;
}

export interface SupportConfig {
    agentName: string;
    welcomeMessage: string;
}

// Elite V2.2: Explicit API Interface definitions (Constitutional Standard)
export interface SupportStatusResponse {
    helen_enabled: boolean;
    offline_message?: string;
}

export interface SupportHistoryItem {
    id: string;
    role: "user" | "assistant";
    content: string;
    intent?: string;
    timestamp: string;
    is_revoked?: boolean;
    customer_phone?: string;
}

export interface SupportChatResponse {
    reply: string;
    intent?: string;
    product_info?: SupportProductInfo;
    status: "DONE" | "PROCESSING" | "FAILED";
    task_id?: string;
    session_id?: string;
    processed_order_id?: string;
}

const STORAGE_KEY = "fp_helen_sid";

class SupportAgentState {
    // Reactive State Variables (Svelte 5 Runes)
    isOpen = $state(false);
    isTyping = $state(false);
    isHistoryLoading = $state(false);
    hasMoreHistory = $state(true);
    messages = $state<SupportMessage[]>([]);

    // Elite V2.2: AI Toggle State
    helenEnabled = $state(true);
    offlineMessage = $state("");
    
    // Elite V2.2: Context & Pulse Intelligence
    currentPath = $state("");
    aiPulse = $state(false);

    // Derived context computed from path
    currentContext = $derived.by(() => {
        if (!this.currentPath) return "default";
        if (this.currentPath === "/" || this.currentPath === "") return "home";
        if (this.currentPath.startsWith("/p/")) return "product";
        if (this.currentPath.startsWith("/cart")) return "cart";
        if (this.currentPath.startsWith("/checkout")) return "checkout";
        return "default";
    });
    
    // Pulse Lifecycle Manager
    private _pulseSource: EventSource | null = null;

    
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
     * Elite V2.2: Haptic Feedback (Vibration API)
     */
    vibrate(pattern: number | number[] = 10) {
        if (browser && "vibrate" in navigator) {
            // ELITE V2.2: Safely vibrate only if interaction is allowed
            try {
                // @ts-ignore - navigator.userActivation is experimental but helpful
                if (!navigator.userActivation || navigator.userActivation.isActive) {
                    navigator.vibrate(pattern);
                }
            } catch (e) {
                // Ignore if blocked
            }
        }
    }

    /**
     * Elite V2.2: ID-Deduplicated Merging Logic
     * Prevents race conditions from wiping messages during rehydration/sync.
     */
    private _mergeMessages(newMsgs: SupportMessage[]) {
        const existingIds = new Set(this.messages.map(m => m.id));
        const filtered = newMsgs.filter(m => !existingIds.has(m.id));
        
        if (filtered.length > 0) {
            // Sort combined set by timestamp to maintain chronological integrity
            const combined = [...this.messages, ...filtered];
            combined.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
            this.messages = combined;
        }
    }

    /**
     * Trigger a neural pulse for attention
     */
    triggerPulse() {
        this.aiPulse = true;
        this.vibrate([20, 30, 20]);
        setTimeout(() => {
            this.aiPulse = false;
        }, 3000);
    }

    /**
     * Update current navigation path for context awareness
     */
    setPath(path: string) {
        if (this.currentPath !== path) {
            this.currentPath = path;
            // Optionally trigger a subtle pulse on significant context changes (e.g. checkout)
            if (path.includes("/checkout")) {
                this.triggerPulse();
            }
        }
    }

    /**
     * Fetch Helen AI global status & offline message
     */
    async fetchStatus(): Promise<void> {
        try {
            const res = await apiClient.get<SupportStatusResponse>("/api/v1/client/support/status");
            if (res) {
                this.helenEnabled = res.helen_enabled ?? true;
                this.offlineMessage = res.offline_message || "";
            }
        } catch (error: unknown) {
            console.warn("[SupportAgent] Failed to fetch status:", error);
        }
    }

    /**
     * Elite V2.2: Proactive Rehydration & Synchronization
     * Ensures history is loaded if missing, avoiding the "welcome message only" trap.
     */
    async ensureHistoryLoaded(limit: number = 20) {
        // If we already have a real conversation (more than just the welcome message), skip
        if (this.messages.some((m: SupportMessage) => m.role === "user")) {
            return;
        }

        // Avoid double loading
        if (this.isHistoryLoading) return;

        // Try to fetch history from backend
        await this.loadHistory(limit);

        // If after fetch, we still have NO messages, then we inject the welcome message
        if (this.messages.length === 0) {
            this.messages = [
                {
                    id: randomId(),
                    role: "assistant",
                    content: this.config.welcomeMessage,
                    timestamp: new Date()
                }
            ];
        } else {
            // We have history, but maybe it only contains old messages. 
            // If the last message is very old, we could optionally add a nudge, but for now just keep as is.
        }
    }

    /**
     * Call this inside a root +layout.svelte or onMount to initialize config and load history
     */
    async init(envAgentName?: string) {
        // Elite V2.2: Fetch global AI toggle state first
        await this.fetchStatus();

        if (this.helenEnabled && envAgentName) {
            this.config.agentName = envAgentName;
            this.config.welcomeMessage = `Dạ chào bạn, mình là ${envAgentName}. Bạn cần hỗ trợ thông tin gì về sản phẩm hay chính sách ạ?`;
        } else if (!this.helenEnabled) {
            this.config.agentName = "Chuyên viên Tư vấn";
            this.config.welcomeMessage = this.offlineMessage || "Chào bạn! Hiện tại em đang tạm nghỉ, chuyên viên trực sẽ sớm hỗ trợ bạn qua Zalo OA ạ.";
        }

        // Proactive Rehydration
        await this.ensureHistoryLoaded(20);
    }

    /**
     * Paginated history loader (Zalo-style)
     */
    async loadHistory(limit: number = 20) {
        if (this.isHistoryLoading || !this.hasMoreHistory) return;

        this.isHistoryLoading = true;
        try {
            const firstMsgId = this.messages[0]?.id;
            const params: { session_id: string; limit: number; before_id?: string } = {
                session_id: this._sessionId,
                limit
            };
            
            // Only attach cursor if we actually have messages
            if (firstMsgId) {
                params.before_id = firstMsgId;
            }

            const res = await apiClient.get<SupportHistoryItem[]>("/api/v1/client/support/history", { params });

            if (Array.isArray(res)) {
                const history: SupportMessage[] = res.map((m: SupportHistoryItem) => ({
                    id: m.id,
                    role: m.role,
                    content: m.content,
                    intent: m.intent,
                    timestamp: new Date(m.timestamp),
                    is_revoked: m.is_revoked
                }));

                if (history.length < limit) {
                    this.hasMoreHistory = false;
                }

                if (history.length > 0) {
                    // Prepend history to current thread using deduplicated merge
                    this._mergeMessages(history);
                }
            }
        } catch (error) {
            console.error("[SupportAgent] History load error:", error);
            getNotificationState().addPendingSignal({
                id: randomId(),
                message: "Không thể tải lịch sử trò chuyện. Vui lòng kiểm tra kết nối.",
                severity: "warning",
                isRead: false
            });
            this.hasMoreHistory = false; // Stop trying on error
        } finally {
            this.isHistoryLoading = false;
        }
    }

    async toggle() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            // Re-sync with backend to catch Admin changes without refresh
            await this.fetchStatus();
            
            // Proactive rehydration on open (The Fix)
            await this.ensureHistoryLoaded();

            // Sync config if it changed
            if (!this.helenEnabled) {
                this.config.agentName = "Chuyên viên Tư vấn";
                // Only update welcome message if no history (avoid weird jumps)
                if (this.messages.length <= 1) {
                    this.config.welcomeMessage = this.offlineMessage || "Chào bạn! Hiện tại em đang tạm nghỉ, chuyên viên trực sẽ sớm hỗ trợ bạn qua Zalo OA ạ.";
                    if (this.messages.length === 1 && this.messages[0].role === "assistant") {
                        this.messages[0].content = this.config.welcomeMessage;
                    }
                }
            }
        }
    }

    close() {
        this.isOpen = false;
        this._disconnectPulse();
    }

    /**
     * Elite V2.2: Neural Sync - Unified Pulse Listener
     * Listens for AI responses and administrative updates (Revoke/Delete).
     */
    private _connectPulse(sessionId: string) {
        if (!browser || this._pulseSource) return;

        this._pulseSource = new EventSource(`/api/v1/client/support/pulse/${sessionId}`);

        // 🟢 1. AI Response Ready - Replaces 'typing' state with content
        this._pulseSource.addEventListener("SUPPORT_RESPONSE_READY", (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);
                if (data.status === "DONE" && data.reply) {
                    const messages = [...this.messages];
                    const lastAssistantIdx = messages.findLastIndex(m => m.role === "assistant");
                    
                    if (lastAssistantIdx !== -1) {
                        messages[lastAssistantIdx] = {
                            ...messages[lastAssistantIdx],
                            content: data.reply,
                            intent: data.intent || messages[lastAssistantIdx].intent,
                            timestamp: new Date()
                        };
                        this.messages = messages;
                    }
                    
                    this.vibrate([10, 50, 10]);
                    this.isTyping = false;
                    this._disconnectPulse();
                }
            } catch (e) {
                console.error("[Pulse] Error parsing response data:", e);
            }
        });

        // 🔴 2. Message Updated (Revoked/Deleted) - Elite V2.2 Professional Bridge
        this._pulseSource.addEventListener("SUPPORT_INBOX_UPDATE", (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);

                if (data.message_id) {
                    const messages = [...this.messages];
                    const msgIdx = messages.findIndex(m => m.id === data.message_id);
                    
                    if (msgIdx !== -1) {
                        // V2.2: Apply revocation state immediately
                        messages[msgIdx] = {
                            ...messages[msgIdx],
                            is_revoked: data.is_revoked ?? messages[msgIdx].is_revoked
                        };
                        this.messages = messages;
                        this.vibrate(20);
                    }
                }
            } catch (e) {
                console.error("[Pulse] Error parsing update data:", e);
            }
        });

        this._pulseSource.onerror = (err) => {
            console.warn("[Pulse] SSE connection state changed, auto-recovering...");
            // Elite V2.2: Release typing lock on connection error to ensure UI resilience
            this.isTyping = false;
        };

        // Guard: Kill pulse if it hangs (Reduced to 60s for better responsiveness)
        setTimeout(() => {
            this.isTyping = false;
            this._disconnectPulse();
        }, 60000);
    }

    private _disconnectPulse() {
        if (this._pulseSource) {
            console.log("[SupportAgent] Pulse infrastructure disposed.");
            this._pulseSource.close();
            this._pulseSource = null;
        }
    }

    /**
     * Elite V2.2: Universal Cleanup
     * Call this when the application or core component is unmounted.
     */
    dispose() {
        this._disconnectPulse();
        this.isOpen = false;
        this.isTyping = false;
    }

    async sendMessage(text: string, productSlug?: string, customerName?: string, customerPhone?: string) {
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
            const res = await apiClient.post<SupportChatResponse>("/api/v1/client/support/chat", {
                message: text.trim(),
                session_id: this._sessionId,
                product_slug: productSlug || null,
                customer_name: customerName || "Khách ẩn danh",
                customer_phone: customerPhone || null
            });

            if (res && typeof res.reply === "string") {
                this.messages = [
                    ...this.messages,
                    {
                        id: randomId(),
                        role: "assistant",
                        content: res.reply || "Xin lỗi, mình tạm thời không phản hồi được ạ.",
                        intent: res.intent,
                        productInfo: res.product_info,
                        timestamp: new Date()
                    }
                ];

                // Check for Async Protocol (Elite V2.2)
                if (res.status === "PROCESSING") {
                    this.isTyping = true;
                    this._connectPulse(this._sessionId);
                } else {
                    this.isTyping = false;
                }
            } else {
                throw new Error("Empty response or missing reply field");
            }
        } catch (error: unknown) {
            console.error("[SupportAgent] Chat error:", error);
            const status = (error as { status?: number })?.status;
            const userFriendlyMsg = status === 429
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

            getNotificationState().addPendingSignal({
                id: randomId(),
                message: "Lỗi kết nối Helen AI. Tin nhắn của bạn có thể chưa được lưu.",
                severity: "error",
                isRead: false
            });
            this.isTyping = false;
        } finally {
        }
    }
}

// Global Singleton (Zero-Hydration friendly)
export const supportAgent = new SupportAgentState();
