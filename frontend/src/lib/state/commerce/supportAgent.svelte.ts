import { apiClient } from "$lib/utils/apiClient";
import { browser } from "$app/environment";
import { getNotificationState } from "$lib/state/notification.svelte";
import { authStore } from "$lib/state/authStore.svelte";
import { logger } from "$lib/utils/logger";
import { getGlobalCart } from "./cart.svelte";

export interface SupportProductInfo {
    id: string;
    name: string;
    price: number;
    price_display: string;
    slug: string;
}

export interface SupportPricingContext {
    items: Array<{
        product_id: string;
        name: string;
        quantity: number;
        unit_price: number;
        total_price: number;
    }>;
    subtotal: number;
    combo_discount: number;
    voucher_discount: number;
    base_shipping_fee: number;
    shipping_discount: number;
    final_shipping_fee: number;
    max_point_discount_allowed: number;
    points_redeemed: number;
    point_discount_amount: number;
    final_payable: number;
    points_to_earn: number;
    applied_voucher_ids: string[];
    applied_combo_ids: string[];
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
    ui_metadata?: Record<string, unknown>;
    metadata?: Record<string, unknown>;
}

class SupportAgentState {
    // Reactive State Variables (Svelte 5 Runes)
    isOpen = $state(false);
    isTyping = $state(false);
    isHistoryLoading = $state(false);
    hasMoreHistory = $state(true);
    messages = $state<SupportMessage[]>([]);
    sessionId = $state("");

    // Elite V2.2: AI Toggle State
    helenEnabled = $state(true);
    offlineMessage = $state("");
    optimalPriceNotice = $state(false);

    // Elite V2.2: Context & Pulse Intelligence
    currentPath = $state("");
    pageType = $state("unknown");
    currentProductName = $state(""); // Elite V6.3: Track current product name for greeting
    currentArticleTitle = $state(""); // Elite V7.5: Track current article title for greeting
    aiPulse = $state(false);

    // Derived context computed from path and pageType
    currentContext = $derived.by(() => {
        if (this.pageType === "product") return "product";
        if (this.pageType === "article") return "article";
        if (this.pageType === "category") return "category";
        if (this.pageType === "news") return "news";
        if (!this.currentPath) return "default";
        if (this.currentPath === "/" || this.currentPath === "") return "home";
        // Handle both clean URLs and potential product prefixes
        if (this.currentPath.includes("-sua-rua-mat-") ||
            this.currentPath.includes("-kem-duong-") ||
            this.currentPath.includes("-serum-") ||
            (this.currentPath.split("/").length >= 2 && this.currentPath.length > 20 && !this.currentPath.endsWith(".html") && !this.currentPath.includes("/bai-viet"))) {
            return "product";
        }
        if (this.currentPath.startsWith("/cart")) return "cart";
        if (this.currentPath.startsWith("/checkout")) return "checkout";
        return "default";
    });

    // Pulse Lifecycle Manager
    private _pulseSource: EventSource | null = null;
    private _pulseTimeout: ReturnType<typeof setTimeout> | null = null;


    // Elite V3.1/V6.3: Persona Intelligence — Dynamic Welcome Based on Identity & Context
    welcomeMessage = $derived.by(() => {
        const user = authStore.user;
        const agentName = this.config.agentName || "Helen";
        const isProductPage = this.currentContext === "product";
        const pName = this.currentProductName;

        if (!this.helenEnabled) {
            return this.offlineMessage || "Chào mừng Quý khách! Hiện tại em đang tạm nghỉ, chuyên viên trực sẽ sớm hỗ trợ mình qua Zalo OA ạ. 🌸";
        }

        const nameLabel = user?.name || "mình";
        const greeting = user?.name ? `Dạ Helen chào ${user.name}!` : `Chào mừng Quý khách đến với osmo!`;

        if (isProductPage) {
            const prodHook = pName ? `siêu phẩm **${pName}**` : "sản phẩm này";
            return `${greeting} Rất vui được gặp lại mình. Em thấy mình đang quan tâm đến ${prodHook} - đây là dòng sản phẩm cao cấp nhà osmo đó ạ. ${nameLabel} có muốn Helen tư vấn kỹ hơn không? ✨💄`;
        }

        if (this.currentContext === "article") {
            const artTitle = this.currentArticleTitle || "bài viết này";
            return `${greeting} Em thấy mình đang đọc bài viết **${artTitle}** — nếu mình cần Helen tóm tắt nội dung chính, giải đáp thắc mắc hay tư vấn sản phẩm liên quan, cứ nhắn em nhé! 📖✨`;
        }

        if (user?.name) {
            return `Dạ Helen chào ${user.name}! Rất vui được gặp lại mình. Helen đang đợi để chăm sóc làn da của mình đây ạ. ${user.name} muốn nhận ưu đãi đặc quyền gì hôm nay không? ✨💄`;
        }

        return `Chào mừng Quý khách đến với osmo! Mình là ${agentName}, chuyên gia tư vấn Mỹ phẩm cao cấp chuẩn Nhật Bản. Quý khách cần mình giúp gì ạ? 🌸`;
    });

    // Config initialized once
    public config: SupportConfig = {
        agentName: "Helen",
        welcomeMessage: ""
    };

    /**
     * Elite V2.2: Haptic Feedback (Vibration API)
     */
    vibrate(pattern: number | number[] = 10) {
        if (browser && "vibrate" in navigator) {
            try {
                const nav = navigator as Navigator & { userActivation?: { isActive: boolean } };
                if (!nav.userActivation || nav.userActivation.isActive) {
                    navigator.vibrate(pattern);
                }
            } catch (error: unknown) {
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
        if (!browser) return;
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
        if (!browser) return;
        if (this.currentPath && this.currentPath !== path) {
            // Elite V2.2: History Ghosting Fix - Context Segregation
            const isProductToProduct = this.currentPath.length > 20 && path.length > 20;
            if (isProductToProduct && this.messages.length > 0) {
                this.messages = [...this.messages, {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content: `*[Hệ thống: Khách vừa chuyển sang xem sản phẩm mới]*`,
                    timestamp: new Date()
                }];
            }
        }

        if (this.currentPath !== path) {
            this.currentPath = path;
            // Optionally trigger a subtle pulse on significant context changes (e.g. checkout)
            if (path.includes("/checkout")) {
                this.triggerPulse();
            }
        }
    }

    /**
     * Update current page type context reactively from SvelteKit page store
     */
    setPageType(type: string) {
        if (!browser) return;
        this.pageType = type;
    }

    /**
     * Fetch Helen AI global status & offline message
     */
    async fetchStatus(): Promise<void> {
        if (!browser) return;
        try {
            const res = await apiClient.get<SupportStatusResponse>("/api/v1/client/support/status");
            if (res) {
                this.helenEnabled = res.helen_enabled ?? true;
                this.offlineMessage = res.offline_message || "";
            }
        } catch (error: unknown) {
            logger.warn("[SupportAgent] Failed to fetch status:", error);
        }
    }

    /**
     * Elite V2.2: Proactive Rehydration & Synchronization
     * Ensures history is loaded if missing, avoiding the "welcome message only" trap.
     */
    async ensureHistoryLoaded(limit: number = 20) {
        if (!browser) return;
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
            const self = this; // Capture context for getter
            this.messages = [
                {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    get content() { return self.welcomeMessage; },
                    timestamp: new Date()
                } as SupportMessage
            ];
        }
    }

    /**
     * Call this inside a root +layout.svelte or onMount to initialize config and load history
     */
    async init(envAgentName?: string) {
        if (!browser) return;
        if (this.sessionId) return;
        // Elite V2.2 (R03): Secure Cookie Initialization
        try {
            const res = await apiClient.get<{ ok: boolean; session_id?: string }>("/api/v1/client/support/init", { withCredentials: true });
            if (res && res.session_id) {
                this.sessionId = res.session_id;
            }
        } catch (error: unknown) {
            logger.warn("[SupportAgent] Failed to init secure session cookie:", error);
        }

        // Elite V2.2: Fetch global AI toggle state first
        await this.fetchStatus();

        if (envAgentName) {
            this.config.agentName = envAgentName;
        }
    }

    /**
     * Paginated history loader (Zalo-style)
     */
    async loadHistory(limit: number = 20) {
        if (!browser) return;
        if (this.isHistoryLoading || !this.hasMoreHistory) return;

        this.isHistoryLoading = true;
        try {
            const firstMsgId = this.messages[0]?.id;
            const params: { limit: number; before_id?: string } = {
                limit
            };

            // Only attach cursor if we actually have messages
            if (firstMsgId) {
                params.before_id = firstMsgId;
            }

            const res = await apiClient.get<SupportHistoryItem[]>("/api/v1/client/support/history", { params, withCredentials: true });

            if (Array.isArray(res)) {
                const history: SupportMessage[] = res.map((m: SupportHistoryItem) => ({
                    id: m.id || crypto.randomUUID(),
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
        } catch (error: unknown) {
            logger.error("[SupportAgent] History load error:", error);
            getNotificationState().addPendingSignal({
                id: crypto.randomUUID(),
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
        if (!browser) return;
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            // Re-sync with backend to catch Admin changes without refresh
            await this.fetchStatus();

            // Proactive rehydration on open (The Fix)
            await this.ensureHistoryLoaded();

            // Sync config if it changed
            if (!this.helenEnabled) {
                this.config.agentName = "Chuyên viên Tư vấn";
            }
            
            // Connect to Pulse SSE permanently when chat is open thưa sếp!
            this._connectPulse();
        } else {
            this._disconnectPulse();
        }
    }

    async open() {
        if (!browser) return;
        if (!this.isOpen) {
            this.isOpen = true;
            await this.fetchStatus();
            await this.ensureHistoryLoaded();

            if (!this.helenEnabled) {
                this.config.agentName = "Chuyên viên Tư vấn";
            }
            
            // Connect to Pulse SSE permanently when chat is open thưa sếp!
            this._connectPulse();
        }
    }

    close() {
        if (!browser) return;
        this.isOpen = false;
        this._disconnectPulse();
    }

    /**
     * Elite V2.2: Neural Sync - Unified Pulse Listener
     * Listens for AI responses and administrative updates (Revoke/Delete).
     */
    private _connectPulse() {
        if (!browser) return;

        // Elite V2.2: Reset/Clear any existing timeout since we are actively requesting/refreshing
        if (this._pulseTimeout) {
            clearTimeout(this._pulseTimeout);
            this._pulseTimeout = null;
        }

        if (!this._pulseSource) {
            // Elite V2.2: Support both cookie and query_param for maximum resilience
            const url = this.sessionId 
                ? `/api/v1/client/support/pulse?session_id=${encodeURIComponent(this.sessionId)}`
                : `/api/v1/client/support/pulse`;
            this._pulseSource = new EventSource(url, { withCredentials: true });

            // 🟢 1. AI Response Ready / Admin Manual Reply thưa sếp!
            this._pulseSource.addEventListener("SUPPORT_RESPONSE_READY", (event: MessageEvent) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    // Case A: Manual representative reply from Admin Inbox thưa sếp!
                    if (data.message && data.role === "assistant") {
                        const isDuplicate = this.messages.some(m => m.content === data.message && m.role === "assistant" && (new Date().getTime() - m.timestamp.getTime() < 3000));
                        if (!isDuplicate) {
                            this.messages = [
                                ...this.messages,
                                {
                                    id: data.id || crypto.randomUUID(),
                                    role: "assistant",
                                    content: data.message,
                                    intent: "MANUAL",
                                    timestamp: new Date()
                                }
                            ];
                            this.vibrate([10, 50, 10]);
                        }
                        this.isTyping = false;
                        return;
                    }

                    // Case B: AI response (from Trinity/Helen brain)
                    if (data.status === "DONE") {
                        const fallbackReply = "Dạ Helen xin lỗi, hệ thống AI đang hơi quá tải một chút. Anh/Chị vui lòng thử lại hoặc để lại lời nhắn để chuyên viên hỗ trợ nhé! 🌸";
                        const actualReply = data.reply || fallbackReply;
                        
                        const messages = [...this.messages];
                        const lastAssistantIdx = messages.findLastIndex(m => m.role === "assistant");

                        if (lastAssistantIdx !== -1) {
                            messages[lastAssistantIdx] = {
                                ...messages[lastAssistantIdx],
                                content: actualReply,
                                intent: data.intent || messages[lastAssistantIdx].intent,
                                timestamp: new Date()
                            };
                            this.messages = messages;
                        } else {
                            this.messages = [
                                ...this.messages,
                                {
                                    id: crypto.randomUUID(),
                                    role: "assistant",
                                    content: actualReply,
                                    intent: data.intent,
                                    timestamp: new Date()
                                }
                            ];
                        }

                        logger.log("🧩 [Helen Pulse] Received AI Response:", data);

                        if (data.ui_metadata) {
                            logger.log("📊 [Helen UI Meta] Pulse Metadata:", data.ui_metadata);
                            if (data.ui_metadata.is_optimal_price !== undefined) {
                                this.optimalPriceNotice = data.ui_metadata.is_optimal_price;
                            }
                            if (data.ui_metadata.order_draft) {
                                logger.log("📝 [Order Draft] Current State:", data.ui_metadata.order_draft);
                            }
                        }
                        if (data.metadata) logger.log("🧠 [Helen Thoughts]:", data.metadata);

                        this.vibrate([10, 50, 10]);
                        this.isTyping = false;
                        // Note: We keep the SSE channel active permanently thưa sếp!
                    }
                } catch (error: unknown) {
                    logger.error("[Pulse] Error parsing response data:", error);
                }
            });

            // 🔴 2. Message Updated (Revoked/Deleted) OR Admin Manual Reply
            this._pulseSource.addEventListener("SUPPORT_INBOX_UPDATE", (event: MessageEvent) => {
                try {
                    const data = JSON.parse(event.data);

                    // Case A: Admin manual reply — display it in the client chat widget
                    if (data.message && data.role === "assistant") {
                        const isDuplicate = this.messages.some(
                            m => m.content === data.message && m.role === "assistant"
                                && (new Date().getTime() - m.timestamp.getTime() < 5000)
                        );
                        if (!isDuplicate) {
                            this.messages = [
                                ...this.messages,
                                {
                                    id: data.id || crypto.randomUUID(),
                                    role: "assistant",
                                    content: data.message,
                                    intent: "MANUAL",
                                    timestamp: new Date()
                                }
                            ];
                            this.vibrate([10, 50, 10]);
                            this.isTyping = false;
                        }
                        return;
                    }

                    // Case B: Message revoked/deleted
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
                } catch (error: unknown) {
                    logger.error("[Pulse] Error parsing update data:", error);
                }
            });

            this._pulseSource.onerror = (err: Event) => {
                logger.warn("[Pulse] SSE connection state changed, auto-recovering...", err);
                // If there's a permanent error or we have no session, disconnect to prevent infinite loop thưa sếp!
                if (!this.sessionId) {
                    this._disconnectPulse();
                }
            };
        }

        // Guard: Extend timeout to 10 min for takeover sessions (user waits for human admin reply)
        // For AI response sessions, 60s is safer to support heavy RAG/cascade logic thêu sếp!
        const pulseTimeout = this.helenEnabled ? 60000 : 600000;
        this._pulseTimeout = setTimeout(() => {
            this.isTyping = false;
            this._disconnectPulse();
        }, pulseTimeout);
    }

    private _disconnectPulse() {
        if (this._pulseTimeout) {
            clearTimeout(this._pulseTimeout);
            this._pulseTimeout = null;
        }
        if (this._pulseSource) {
            logger.log("[SupportAgent] Pulse infrastructure disposed.");
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

    async sendMessage(
        text: string,
        productSlug?: string,
        customerName?: string,
        customerPhone?: string,
        userId?: string,
        cartItems?: Array<{ product_id: string; quantity: number;[key: string]: unknown }>,
        selectedVouchers?: string[],
        pricingContext?: SupportPricingContext,
        displayText?: string
    ) {
        if (!browser) return;
        if (!text.trim() || this.isTyping) return;

        // Elite V3.6: Client-side duplicate message check — 30s window only (không block vĩnh viễn)
        const lastUserMsg = this.messages.filter(m => m.role === "user").slice(-1)[0];
        const normalizedInput = (displayText !== undefined ? displayText.trim() : text.trim()).toLowerCase();
        const isDuplicateWithinWindow = lastUserMsg
            && lastUserMsg.content.trim().toLowerCase() === normalizedInput
            && (new Date().getTime() - lastUserMsg.timestamp.getTime() < 30000);
        if (isDuplicateWithinWindow) {
             logger.warn("🛡️ [Client-Spam] Prevented duplicate message trigger (within 30s): ", text);
             return;
        }

        const userMsg: SupportMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content: displayText !== undefined ? displayText : text.trim(),
            timestamp: new Date()
        };

        this.messages = [...this.messages, userMsg];
        this.isTyping = true;

        try {
            const MAX_MSG_LEN = 2000;
            const rawMsg = text.trim();
            if (rawMsg.length > MAX_MSG_LEN) {
                logger.warn(`[SupportAgent] Message truncated: ${rawMsg.length} → ${MAX_MSG_LEN} chars`);
            }
            const res = await apiClient.post<SupportChatResponse>("/api/v1/client/support/chat", {
                message: rawMsg.slice(0, MAX_MSG_LEN),
                product_slug: productSlug || null,
                customer_name: customerName || "Khách ẩn danh",
                customer_phone: customerPhone || null,
                user_id: userId || null,
                cart_items: cartItems || null,
                selected_vouchers: selectedVouchers || null,
                pricing_context: pricingContext || null,
                cart_epoch: getGlobalCart().epoch
            }, { withCredentials: true });

            if (res && res.session_id) {
                this.sessionId = res.session_id;
            }

            if (res && res.status === "TAKEOVER") {
                this.isTyping = false;
                logger.log("👤 [Human Takeover] Chat taken over by human representative. Keeping Pulse alive for admin replies.");
                // CRITICAL: Must connect Pulse SSE so client receives admin messages in real-time
                this._connectPulse();
                return;
            }

            if (res && typeof res.reply === "string") {
                this.messages = [
                    ...this.messages,
                    {
                        id: crypto.randomUUID(),
                        role: "assistant",
                        content: res.reply || "Xin lỗi, mình tạm thời không phản hồi được ạ.",
                        intent: res.intent,
                        productInfo: res.product_info,
                        timestamp: new Date()
                    }
                ];

                logger.log("🧩 [Helen Chat] Received Response:", res);
                if (res.metadata) logger.log("🧠 [Helen Thoughts]:", res.metadata);
                if (res.ui_metadata) {
                    logger.log("📊 [Helen UI Meta]:", res.ui_metadata);
                    
                    if (res.ui_metadata.update_cart) {
                        const updateCart = res.ui_metadata.update_cart as {
                            items: Array<{
                                id: string;
                                product: {
                                    id: string;
                                    name: string;
                                    price: number;
                                    discountPrice: number;
                                    slug: string;
                                };
                                variant?: {
                                    id: string;
                                    sku: string;
                                    price: number;
                                    discountPrice: number;
                                    tierIndex: number[];
                                };
                                quantity: number;
                                selected: boolean;
                            }>;
                            epoch: number;
                        };
                        const cartStore = getGlobalCart();
                        if (updateCart.epoch >= cartStore.epoch) {
                            logger.log(`🔄 [CartSync] Syncing cart to epoch ${updateCart.epoch} (local: ${cartStore.epoch})`);
                            if (updateCart.items.length === 0) {
                                cartStore.clearCart();
                            } else {
                                cartStore.items = updateCart.items;
                                cartStore.save();
                            }
                            cartStore.epoch = updateCart.epoch;
                        } else {
                            logger.warn(`🛡️ [CartSync] Ignored stale cart sync epoch ${updateCart.epoch} (local: ${cartStore.epoch})`);
                        }
                    }
                }

                // Check for Async Protocol (Elite V2.2)
                if (res.status === "PROCESSING") {
                    this.isTyping = true;
                    this._connectPulse();
                } else {
                    this.isTyping = false;
                }
            } else {
                throw new Error("Empty response or missing reply field");
            }
        } catch (error: unknown) {
            logger.error("[SupportAgent] Chat error:", error);
            const status = (error as { status?: number; response?: { status: number } })?.status || (error as { response?: { status: number } })?.response?.status;
            const userFriendlyMsg = status === 429
                ? "Hệ thống đang xử lý nhiều luồng, bạn vui lòng đợi một lát rồi thử lại nhé!"
                : "Xin lỗi bạn, hệ thống kết nối đang bị gián đoạn. Bạn vui lòng thử lại sau nhé.";

            this.messages = [
                ...this.messages,
                {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content: userFriendlyMsg,
                    timestamp: new Date()
                }
            ];

            getNotificationState().addPendingSignal({
                id: crypto.randomUUID(),
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
