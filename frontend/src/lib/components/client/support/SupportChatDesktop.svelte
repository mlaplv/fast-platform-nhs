<script lang="ts">
  import type { ComponentType, SvelteComponent, Component } from "svelte";
  import { tick } from "svelte";
  import { scale, fly } from "svelte/transition";
  import Send from "@lucide/svelte/icons/send";
  import X from "@lucide/svelte/icons/x";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import UserRound from "@lucide/svelte/icons/user-round";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import Beaker from "@lucide/svelte/icons/beaker";
  import Target from "@lucide/svelte/icons/target";
  import Lock from "@lucide/svelte/icons/lock";
  import PackageSearch from "@lucide/svelte/icons/package-search";
  import { supportAgent } from "$lib/state/commerce/supportAgent.svelte";
  import { authStore } from "$lib/state/authStore.svelte";
  import { getShopStore } from "$lib/state/commerce/shop.svelte";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { checkoutState } from "$lib/state/commerce/checkout.svelte";
  import HelenIcon from "./HelenIcon.svelte";

  const { productSlug = "" } = $props<{ productSlug?: string }>();
  const shopStore = getShopStore();
  const cartStore = getCartStore();

  let chatContainer = $state<HTMLDivElement>();
  let inputElement = $state<HTMLTextAreaElement>();
  let userInput = $state("");
  let isExpanded = $state(false);
  let isInputFocused = $state(false);
  let consultantCTAVisible = $state(true);

  interface QuickAction {
    label: string;
    icon: ComponentType<SvelteComponent> | Component<any>; // Elite V2.2: Svelte 5 Component Type Compatibility
    prompt?: string;
    displayPrompt?: string;
    action?: () => void;
    title?: string;
  }

  const quickActions: QuickAction[] = [
    {
      label: "An toàn da",
      icon: ShieldCheck,
      prompt:
        '[system_skin_barrier] QUY TRÌNH KIỂM TRA HÀNG RÀO BẢO VỆ DA (SKIN BARRIER):\n1. ĐÓNG VAI LÀ HELEN - CHUYÊN GIA DA LIỄU AI ÂN CẦN.\n2. KHOAN TƯ VẤN SẢN PHẨM NGAY. Hãy chào khách và CHỦ ĐỘNG hỏi thăm tình trạng da hiện tại của họ (ví dụ: da có đang mẩn đỏ, nhạy cảm, hay đang dùng treatment nặng như BHA/Retinol không?).\n3. GIẢI THÍCH NGẮN GỌN rằng Helen cần thông tin này để đối chiếu với Bảng Thành Phần (Ingredients) của sản phẩm, nhằm đánh giá xem sản phẩm có an toàn tuyệt đối cho "hàng rào bảo vệ da" của riêng khách hay không.\n4. CẤM BÁO GIÁ HAY CHỐT SALE Ở BƯỚC NÀY. Chỉ tập trung hỏi thăm và chờ khách hàng trả lời.',
      displayPrompt: "Kiểm tra an toàn cho da",
      title: "Kiểm tra sản phẩm có phù hợp cho da của bạn không.",
    },
    {
      label: "Xuất xứ",
      icon: Sparkles,
      prompt: "Sản phẩm này có chính hãng không? Nguồn gốc ở đâu?",
    },
    {
      label: "Công dụng",
      icon: Beaker,
      prompt: "Sản phẩm này có thành phần gì và công dụng như thế nào?",
    },
    {
      label: "Tư vấn",
      icon: Target,
      prompt:
        '[system_consult] Hãy tư vấn bán hàng chuyên sâu cho sản phẩm này theo cấu trúc chi tiết sau nhưng CẤM ghi tên các tiêu đề kỹ thuật:\n1. Đồng cảm sâu sắc với nỗi lo thầm kín nhất của khách hàng về làn da/vấn đề sản phẩm giải quyết.\n2. Liệt kê và phân tích chi tiết cơ chế khoa học của các thành phần nổi bật chuẩn Nhật dưới dạng danh sách (bullet points) rõ ràng.\n3. Vẽ ra bức tranh sinh động về sự tự tin rạng rỡ sau khi sử dụng.\n4. Đưa ra báo giá chi tiết (giá niêm yết, khuyến mãi), tồn kho thực tế (FOMO), chương trình KM và Kêu Gọi Hành Động (CTA) xin SĐT + Địa chỉ nhận hàng để chốt đơn ngay.\nCHÚ Ý: CẤM viết các tiêu đề thô kệch như "Điểm đau", "Giải pháp", "Viễn cảnh tự do", "Lời khuyên mua sắm từ Helen". Hãy chia đoạn tự nhiên bằng các emoji sang trọng.',
      displayPrompt: "Tư vấn chuyên sâu về sản phẩm này",
    },
  ];

  function closeChat() {
    supportAgent.isOpen = false;
    isExpanded = false;
  }

  function toggleExpand() {
    isExpanded = !isExpanded;
  }

  function handleInputFocus() {
    isInputFocused = true;
  }

  function handleInputBlur() {
    isInputFocused = false;
  }

  function getCartItemsMapped() {
    return cartStore.items.map(item => ({
      product_id: item.product.id,
      quantity: item.quantity,
      name: item.product.name,
      unit_price: item.variant?.price || item.product.price || 0,
      total_price: (item.variant?.price || item.product.price || 0) * item.quantity,
    }));
  }

  function getPricingContextMapped() {
    const cb = checkoutState.breakdown;
    const cartB = cartStore.breakdown;
    if (cb) {
      return {
        items: cartB.items,
        subtotal: cb.subtotal,
        combo_discount: cb.combo_discount,
        voucher_discount: cb.voucher_discount,
        base_shipping_fee: cb.shipping_fee,
        shipping_discount: cb.shipping_discount,
        final_shipping_fee: Math.max(0, cb.shipping_fee - cb.shipping_discount),
        max_point_discount_allowed: cb.subtotal * 0.01,
        points_redeemed: cb.points_redeemed,
        point_discount_amount: cb.point_discount,
        final_payable: cb.final_total,
        points_to_earn: Math.floor(cb.final_total / 100000),
        applied_voucher_ids: cb.applied_vouchers?.map(v => v.id) || [],
        applied_combo_ids: []
      };
    }
    return cartB;
  }

  async function handleSend() {
    if (!userInput.trim() || supportAgent.isTyping) return;
    const text = userInput;
    userInput = "";

    // Elite V2.2: Pass customer info for Zalo OA Bridge
    // Elite V3.1: Priority Auth Persistence — use real name if logged in
    const user = authStore.user;
    const customer = shopStore?.customerData;

    const name = user?.name || customer?.nameMasked || "Khách ẩn danh";
    const userId = user?.id || undefined;

    // Elite V2.2: Pass Ground Truth pricing if on checkout page
    // [FIX] Explicitly read from singleton for precision sync
    const pricingContext = getPricingContextMapped();

    await supportAgent.sendMessage(
      text,
      productSlug,
      name,
      undefined,
      userId,
      getCartItemsMapped(),
      cartStore.selectedVoucherIds,
      pricingContext,
    );
    scrollToNewestMessage();
  }

  async function handleQuickAction(action: QuickAction) {
    if (action.action) {
      action.action();
      return;
    }
    const pricingContext = getPricingContextMapped();
    await supportAgent.sendMessage(
      action.prompt || "",
      productSlug,
      undefined,
      undefined,
      undefined,
      getCartItemsMapped(),
      cartStore.selectedVoucherIds,
      pricingContext,
      action.displayPrompt,
    );
    scrollToNewestMessage();
  }

  // Option 1: Chat trực tiếp ngay tại box (không mở Zalo)
  async function requestInboxChat() {
    consultantCTAVisible = false;
    const user = authStore.user;
    const customer = shopStore?.customerData;
    const name = user?.name || customer?.nameMasked || "Khách ẩn danh";
    const userId = user?.id || undefined;
    const pricingContext = getPricingContextMapped();
    await supportAgent.sendMessage(
      "[chat_inbox] Tôi muốn chat trực tiếp với chuyên viên tư vấn ngay tại đây",
      productSlug,
      name,
      undefined,
      userId,
      getCartItemsMapped(),
      cartStore.selectedVoucherIds,
      pricingContext,
      "💬 Yêu cầu chat trực tiếp với chuyên viên",
    );
    scrollToNewestMessage();
  }

  // Option 2: Mở Zalo OA (synchronous window.open trước, async notify sau)
  async function requestZaloChat() {
    consultantCTAVisible = false;
    const oaId = "71197756917084615";
    window.open(`https://zalo.me/${oaId}`, "_blank");
    const user = authStore.user;
    const customer = shopStore?.customerData;
    const name = user?.name || customer?.nameMasked || "Khách ẩn danh";
    const userId = user?.id || undefined;
    const pricingContext = getPricingContextMapped();
    await supportAgent.sendMessage(
      "[zalo_oa] Tôi muốn chat với chuyên viên qua Zalo OA",
      productSlug,
      name,
      undefined,
      userId,
      getCartItemsMapped(),
      cartStore.selectedVoucherIds,
      pricingContext,
      "💙 Yêu cầu kết nối qua Zalo OA",
    );
    scrollToNewestMessage();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // Elite V2.2: Unified UX State Monitor (Focus & Scroll Manager)
  $effect(() => {
    const { isOpen, isTyping, messages } = supportAgent;

    if (isOpen && inputElement) {
      // 1. Handle auto-focus
      if (!isTyping) {
        inputElement.focus();
      }

      // 2. Handle scrolling
      if (messages.length > 0) {
        scrollToNewestMessage();
      } else {
        // Initial open: Immediate anchor to bottom
        setTimeout(() => {
          if (chatContainer) {
            chatContainer.scrollTo({
              top: chatContainer.scrollHeight,
              behavior: "instant",
            });
          }
        }, 150);
      }
    }
  });

  async function scrollToNewestMessage() {
    await tick();
    if (!chatContainer) return;

    const messageElements = chatContainer.querySelectorAll(
      ".message-bubble-container",
    );
    const lastMessageEl = messageElements[messageElements.length - 1];

    if (lastMessageEl) {
      const role = lastMessageEl.getAttribute("data-role");
      if (role === "assistant") {
        // Align to top of message if it's long, ensuring 'Helen' is visible
        lastMessageEl.scrollIntoView({ behavior: "smooth", block: "start" });
      } else {
        // Scroll to bottom for user's own message
        chatContainer.scrollTo({
          top: chatContainer.scrollHeight,
          behavior: "smooth",
        });
      }
    }
  }
</script>

{#if supportAgent.isOpen}
  <!-- Hyper Drop Container (Elite V2.2: Premium Glassmorphic Symmetric Card) -->
  <div
    class="support-chat-container fixed transform-gpu origin-bottom-right transition-all duration-700 ease-[cubic-bezier(0.34,1.56,0.64,1)] {isExpanded
      ? 'bottom-8 right-8 w-[90vw] h-[85vh] rounded-[48px] overflow-hidden bg-[#0a0a0a]'
      : 'bottom-[110px] right-8 w-[450px] h-[740px] max-h-[85vh] helen-box-premium helen-float-premium'} {isInputFocused
      ? 'pause-animations'
      : ''}"
    style="z-index: {Z_INDEX_CLIENT.MODAL}; will-change: transform, opacity;"
    transition:scale={{
      start: 0.7,
      opacity: 0,
      duration: 600,
      easing: (t) => 1 - Math.pow(1 - t, 5),
    }}
  >
    <!-- Premium Symmetric Border Overlay (Optimized for No-GPU Paint) -->
    <div
      class="absolute inset-[-1px] border border-white/10 {isExpanded
        ? 'rounded-[48px]'
        : 'helen-box-premium'} pointer-events-none z-[100]"
    ></div>

    <!-- Specular Highlight (Sophisticated Static Glow) -->
    <div
      class="absolute top-[5%] left-[5%] w-[45%] h-[25%] bg-gradient-to-br from-[#FFB7C5]/10 via-[#FFB7C5]/3 to-transparent blur-2xl {isExpanded
        ? 'hidden'
        : 'helen-box-premium'} pointer-events-none z-20"
    ></div>
    <div
      class="absolute top-4 left-10 w-2 h-2 bg-white/30 blur-[2px] rounded-full {isExpanded
        ? 'hidden'
        : ''} pointer-events-none z-20"
    ></div>

    <!-- Ultra-Glass Background Layer -->
    <div
      class="absolute inset-0 apple-glass-dark-modal pointer-events-none transition-all duration-700 {isExpanded
        ? 'rounded-[48px] is-expanded'
        : 'helen-box-premium'} border border-white/5 shadow-2xl"
    ></div>

    <!-- Interface Contents -->
    <div class="relative z-10 flex flex-col h-full">
      <!-- Blended Ghost Header -->
      <header
        class="flex-shrink-0 pt-10 px-12 pb-6 flex items-center justify-between"
      >
        <div class="flex items-center gap-6">
          <div class="relative group/avatar">
            <div
              class="w-16 h-16 rounded-full bg-black/40 flex items-center justify-center shadow-[0_8px_32px_rgba(255,183,197,0.3)] border border-white/20 transition-transform group-hover/avatar:scale-105 overflow-hidden"
            >
              <HelenIcon size={64} color="#FFB7C5" isPaused={isInputFocused} />
            </div>
            <div
              class="absolute bottom-0 right-0 w-4 h-4 bg-[#FFB7C5] rounded-full ring-[3px] ring-[#0a0a0a] shadow-[0_0_12px_#FFB7C5]"
            ></div>
          </div>
          <div class="flex flex-col gap-1">
            <div class="flex items-center gap-3">
              <h3
                class="font-black text-white tracking-[-0.03em] text-[24px] leading-none"
              >
                {supportAgent.config.agentName}
              </h3>
              <div
                class="apple-glass-badge px-2 py-0.5 rounded-md flex items-center gap-1.5 border border-white/10"
              >
                <Lock size={9} class="text-white/30" />
                <span
                  class="text-[8px] text-white/40 font-black tracking-widest"
                  >AES_256</span
                >
              </div>
            </div>
            <div class="flex items-center gap-2">
              <div
                class="w-1.5 h-1.5 rounded-full bg-[#FFB7C5] shadow-[0_0_8px_#FFB7C5] animate-pulse"
              ></div>
              <p
                class="text-[10px] text-[#FFB7C5] font-black tracking-[0.35em] opacity-90"
              >
                {supportAgent.helenEnabled
                  ? "Đang hoạt động"
                  : "Chuyên viên trực"}
              </p>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button
            onclick={toggleExpand}
            class="w-11 h-11 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/15 text-white/60 hover:text-white transition-all border border-white/5 group/expand"
            title={isExpanded ? "Thu nhỏ" : "Toàn màn hình"}
          >
            {#if isExpanded}
              <Minimize2
                size={20}
                class="group-hover/expand:scale-110 transition-transform"
              />
            {:else}
              <Maximize2
                size={20}
                class="group-hover/expand:scale-110 transition-transform"
              />
            {/if}
          </button>
          <button
            onclick={closeChat}
            class="w-11 h-11 flex items-center justify-center rounded-full bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all border border-red-500/10 group/close"
          >
            <X
              size={24}
              class="group-hover/close:rotate-90 transition-transform duration-300"
            />
          </button>
        </div>
      </header>

      {#if supportAgent.optimalPriceNotice}
        <div
          transition:fly={{ y: -20, duration: 600 }}
          class="flex-shrink-0 px-10 pb-6 -mt-2 animate-in fade-in zoom-in duration-700"
        >
          <div
            class="relative w-full p-5 bg-gradient-to-br from-[#FFB7C5]/20 to-black/40 border border-[#FFB7C5]/30 rounded-[32px] shadow-[0_12px_40px_rgba(255,183,197,0.15)] overflow-hidden group"
          >
            <div
              class="absolute -top-12 -right-12 w-24 h-24 bg-[#FFB7C5]/10 blur-3xl rounded-full group-hover:scale-150 transition-transform duration-1000"
            ></div>
            <div class="flex items-center gap-4">
              <div
                class="w-10 h-10 rounded-full bg-[#FFB7C5] flex items-center justify-center shadow-[0_0_15px_rgba(255,183,197,0.5)] flex-shrink-0"
              >
                <Sparkles size={20} class="text-slate-950" />
              </div>
              <div class="flex flex-col">
                <p
                  class="text-[13px] text-white font-black leading-tight tracking-tight"
                >
                  Mức giá tối ưu cho liệu trình
                </p>
                <p
                  class="text-[11px] text-white/70 leading-snug font-medium mt-1"
                >
                  Tuyệt vời! Đơn hàng của bạn đã đạt mức giá tối ưu. Helen cam
                  kết bảo vệ quyền lợi cho bạn.
                </p>
              </div>
            </div>
          </div>
        </div>
      {/if}

      <!-- Thread: Beautifully Grouped Glassmorphic Conversations -->
      <div
        bind:this={chatContainer}
        class="flex-1 overflow-y-auto px-6 py-4 flex flex-col justify-start space-y-6 hide-scrollbar relative"
      >
        {#if !supportAgent.optimalPriceNotice}
          <div
            class="flex flex-col items-center justify-center mb-6 opacity-30 hover:opacity-100 transition-opacity"
          >
            <div
              class="flex items-center gap-2.5 px-5 py-2 bg-black/40 border border-white/10 rounded-full"
            >
              <ShieldCheck size={14} class="text-[#FFB7C5]" />
              <span
                class="text-[10px] text-white/60 tracking-[0.2em] font-black italic"
                >Hệ thống chuyên gia Helen v3.2</span
              >
            </div>
          </div>
        {/if}

        <!-- Zalo-style pagination -->
        {#if supportAgent.hasMoreHistory}
          <div class="flex justify-center pb-4">
            <button
              onclick={() => supportAgent.loadHistory()}
              disabled={supportAgent.isHistoryLoading}
              class="px-8 py-2.5 bg-white/5 hover:bg-[#FFB7C5]/10 border border-white/5 rounded-full text-[10px] font-black tracking-[0.2em] text-[#FFB7C5] transition-all active:scale-95 disabled:opacity-30"
            >
              {supportAgent.isHistoryLoading
                ? "Đang đồng bộ dữ liệu..."
                : "Tải thêm tin nhắn cũ"}
            </button>
          </div>
        {/if}
        {#if supportAgent.messages.length === 0 && supportAgent.isHistoryLoading}
          <div
            class="flex flex-col items-center justify-center py-20 opacity-40 animate-pulse"
          >
            <div
              class="w-12 h-12 rounded-full border-2 border-t-[#FFB7C5] border-white/5 animate-spin"
            ></div>
            <p class="text-[11px] font-black tracking-[0.2em] text-white mt-6">
              Đang đồng bộ dữ liệu giao tiếp...
            </p>
          </div>
        {/if}

        {#each supportAgent.messages as msg, msgIdx (msg.id)}
          <div
            class="flex flex-col w-full group animate-in fade-in slide-in-from-bottom-4 duration-500 message-bubble-container"
            data-role={msg.role}
          >
            <!-- Name Label (Elite V3.1: Professional Identity) -->
            <div
              class="flex items-center gap-2 mb-1.5 px-14 {msg.role === 'user'
                ? 'flex-row-reverse'
                : 'flex-row'}"
            >
              <span
                class="text-[10px] font-black tracking-[0.2em] {msg.role ===
                'user'
                  ? 'text-[#FFB7C5]'
                  : 'text-white/40'}"
              >
                {msg.role === "assistant"
                  ? supportAgent.config.agentName
                  : authStore.user?.name || "Quý khách"}
              </span>
              {#if msg.role === "assistant"}
                <div
                  class="w-1.5 h-1.5 rounded-full bg-[#FFB7C5] shadow-[0_0_8px_#FFB7C5] animate-pulse"
                ></div>
              {/if}
            </div>

            <div
              class="flex items-start gap-4 w-full {msg.role === 'user'
                ? 'flex-row-reverse'
                : 'flex-row'}"
            >
              <!-- Identity Icon -->
              <div class="flex-shrink-0 mt-1">
                {#if msg.role === "assistant"}
                  <div
                    class="w-8 h-8 rounded-full bg-black/40 flex items-center justify-center border border-white/10 shadow-lg overflow-hidden"
                  >
                    <HelenIcon
                      size={28}
                      color="#FFB7C5"
                      isPaused={isInputFocused}
                    />
                  </div>
                {:else}
                  <div
                    class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center border border-white/5 shadow-md overflow-hidden"
                  >
                    {#if authStore.user?.avatar_url}
                      <img
                        src={authStore.user.avatar_url}
                        alt="User"
                        class="w-full h-full object-cover"
                      />
                    {:else}
                      <UserRound size={16} class="text-white/60" />
                    {/if}
                  </div>
                {/if}
              </div>

              <!-- Message Content (Premium Glassmorphic Bubble Wrapper) -->
              <div
                class="flex-1 max-w-[85%] {msg.role === 'user'
                  ? 'text-right'
                  : 'text-left'}"
              >
                {#if msg.is_revoked}
                  <div
                    class="inline-block text-[15px] italic text-white/40 line-through select-none bg-white/[0.02] border border-white/5 rounded-2xl px-4 py-2.5"
                  >
                    [Tin nhắn đã bị thu hồi]
                  </div>
                {:else if msg.role === "assistant" && msg.intent === "ORDER_STATUS"}
                  <div
                    class="inline-block text-[15px] leading-[1.6] break-words text-left bg-white/[0.04] border border-white/5 rounded-2xl rounded-tl-none px-4.5 py-3.5 text-gray-200 max-w-full shadow-lg"
                  >
                    <div
                      class="inline-flex items-center gap-2 px-3 py-1.5 mb-3 bg-[#FFB7C5]/10 text-[#FFB7C5] rounded-xl border border-[#FFB7C5]/20 font-black text-[13px] tracking-wider"
                    >
                      <PackageSearch size={14} /> Tra cứu vận đơn
                    </div>
                    <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                    <div class="text-[15px] mb-4">
                      {@html msg.content.replace(/\n/g, "<br/>")}
                    </div>
                    <div
                      class="w-full max-w-[300px] p-1 bg-black/40 rounded-2xl border border-white/10 shadow-2xl overflow-hidden focus-within:ring-2 focus-within:ring-[#FFB7C5]/40 transition-all"
                    >
                      <div class="flex items-center">
                        <input
                          type="tel"
                          placeholder="Số điện thoại / Mã đơn"
                          class="flex-1 px-4 py-2 bg-transparent text-white placeholder-gray-600 outline-none text-[14px]"
                        />
                        <button
                          class="w-8 h-8 bg-[#FFB7C5] text-slate-950 rounded-lg flex items-center justify-center shadow-lg active:scale-95 transition-all"
                        >
                          <Send size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                {:else if msg.role === "assistant" && msg.intent === "PRICE_QUERY"}
                  <div
                    class="inline-block text-[15px] leading-[1.6] break-words text-left bg-white/[0.04] border border-white/5 rounded-2xl rounded-tl-none px-4.5 py-3.5 text-gray-200 max-w-full shadow-lg"
                  >
                    <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                    <div class="text-[15px]">
                      {@html msg.content
                        .replace(
                          /\*\*(.*?)\*\*/g,
                          '<strong class="text-white font-black">$1</strong>',
                        )
                        .replace(/\n/g, "<br/>")}
                    </div>

                    <button
                      onclick={() =>
                        shopStore?.openCheckout(cartStore, shopStore.product!)}
                      class="mt-4 px-6 py-2.5 bg-gradient-to-r from-[#FFB7C5] to-[#FF8FA3] text-slate-950 text-[13px] font-black rounded-full shadow-[0_6px_20px_rgba(255,183,197,0.3)] hover:shadow-[0_10px_28px_rgba(255,183,197,0.4)] transition-all active:scale-[0.98] tracking-wider animate-pulse-subtle"
                    >
                      NHẬN ƯU ĐÃI NGAY →
                    </button>
                  </div>
                {:else if msg.role === "assistant"}
                  <div
                    class="inline-block text-[15px] leading-[1.6] break-words text-left bg-white/[0.04] border border-white/5 rounded-2xl rounded-tl-none px-4.5 py-3.5 text-gray-200 max-w-full shadow-lg"
                  >
                    <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                    <div class="text-[15px]">
                      {@html msg.content
                        .replace(
                          /\*\*(.*?)\*\*/g,
                          '<strong class="text-white font-black">$1</strong>',
                        )
                        .replace(
                          /\[(.*?)\]\((.*?)\)/g,
                          '<a href="$2" target="_blank" class="helen-cta-btn">$1</a>',
                        )
                        .replace(/\n/g, "<br/>")}
                    </div>
                  </div>
                {:else}
                  <div
                    class="inline-block text-[15px] leading-[1.6] break-words text-left bg-gradient-to-br from-[#FFB7C5]/15 to-[#FF8FA3]/5 border border-[#FFB7C5]/10 rounded-2xl rounded-tr-none px-4 py-2.5 text-white max-w-full shadow-md"
                  >
                    {msg.content}
                  </div>
                {/if}

                <!-- Timestamp -->
                <div
                  class="text-[9px] text-white/10 mt-2.5 font-black tracking-[0.3em] opacity-0 group-hover:opacity-100 transition-all duration-300"
                >
                  {msg.timestamp.toLocaleTimeString("vi-VN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
              </div>
            </div>
          </div>
        {/each}

        <!-- ══════════════════════════════════════════════════════
             Consultant CTA — standalone, always visible below all messages
        ══════════════════════════════════════════════════════ -->
        {#if consultantCTAVisible && supportAgent.helenEnabled && supportAgent.messages.length > 0}
          <div class="px-4 pb-2 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <!-- Divider -->
            <div class="flex items-center gap-4 mb-5">
              <div class="flex-1 h-px" style="background: rgba(255,255,255,0.06);"></div>
              <span class="text-[10px] font-black tracking-[0.3em] uppercase" style="color: rgba(255,255,255,0.2);">Kết nối chuyên viên</span>
              <div class="flex-1 h-px" style="background: rgba(255,255,255,0.06);"></div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <!-- Option 1: Chat trong box -->
              <button
                onclick={requestInboxChat}
                class="group relative flex flex-col items-start gap-3 p-4 rounded-2xl overflow-hidden text-left transition-all duration-200 hover:scale-[1.02] active:scale-[0.97]"
                style="background: linear-gradient(135deg, rgba(255,183,197,0.09) 0%, rgba(255,183,197,0.03) 100%); border: 1px solid rgba(255,183,197,0.18);"
              >
                <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  style="background: radial-gradient(ellipse at top left, rgba(255,183,197,0.12) 0%, transparent 60%);"></div>
                <div class="relative w-10 h-10 rounded-xl flex items-center justify-center"
                  style="background: rgba(255,183,197,0.12); border: 1px solid rgba(255,183,197,0.22);">
                  <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="#FFB7C5" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                </div>
                <div class="relative flex flex-col gap-0.5">
                  <span class="text-[13px] font-black text-white tracking-tight leading-snug">Chat ngay tại đây</span>
                  <span class="text-[10px] font-medium leading-snug" style="color: rgba(255,183,197,0.5);">Chuyên viên phản hồi trong khung chat này</span>
                </div>
              </button>
              <!-- Option 2: Zalo OA -->
              <button
                onclick={requestZaloChat}
                class="group relative flex flex-col items-start gap-3 p-4 rounded-2xl overflow-hidden text-left transition-all duration-200 hover:scale-[1.02] active:scale-[0.97]"
                style="background: linear-gradient(135deg, rgba(0,104,255,0.11) 0%, rgba(0,104,255,0.04) 100%); border: 1px solid rgba(0,104,255,0.24);"
              >
                <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  style="background: radial-gradient(ellipse at top left, rgba(0,132,255,0.15) 0%, transparent 60%);"></div>
                <div class="relative w-10 h-10 rounded-xl flex items-center justify-center"
                  style="background: rgba(0,104,255,0.15); border: 1px solid rgba(0,104,255,0.28);">
                  <svg class="w-5 h-5" viewBox="0 0 40 40" fill="none">
                    <path d="M20 3C10.611 3 3 10.164 3 19c0 4.884 2.21 9.267 5.707 12.277L7.5 35l4.215-2.192A18.14 18.14 0 0020 35c9.389 0 17-7.164 17-16S29.389 3 20 3z" fill="#0068FF"/>
                    <path d="M28.5 22.6c-.3-.15-1.767-.87-2.04-.97-.273-.097-.472-.146-.67.147-.2.293-.77.97-.944 1.168-.173.2-.347.22-.646.074-.3-.147-1.263-.465-2.406-1.485-.888-.793-1.488-1.772-1.663-2.072-.175-.3-.019-.462.132-.61.135-.135.3-.35.45-.525.148-.175.197-.3.296-.498.098-.2.05-.374-.025-.523-.074-.147-.67-1.614-.918-2.21-.242-.578-.487-.5-.67-.51-.173-.008-.372-.01-.57-.01-.2 0-.523.074-.797.37-.273.297-1.04 1.016-1.04 2.48 0 1.463 1.065 2.877 1.213 3.076.148.2 2.096 3.2 5.08 4.487.71.307 1.264.49 1.695.627.713.227 1.362.195 1.876.118.572-.086 1.767-.722 2.016-1.42.25-.7.25-1.298.175-1.42-.075-.123-.273-.197-.572-.347z" fill="white"/>
                  </svg>
                </div>
                <div class="relative flex flex-col gap-0.5">
                  <span class="text-[13px] font-black tracking-tight leading-snug" style="color: #5BA4FF;">Chat qua Zalo OA</span>
                  <span class="text-[10px] font-medium leading-snug" style="color: rgba(91,164,255,0.5);">Mở Zalo, chuyên viên cũng được thông báo</span>
                </div>
              </button>
            </div>
          </div>
        {/if}

        {#if supportAgent.isTyping}
          <div class="flex justify-start w-full">
            <div
              class="flex items-center gap-3 px-5 py-2.5 bg-black/40 rounded-full border border-white/5"
            >
              <div
                class="w-1.5 h-1.5 bg-[#FFB7C5] rounded-full animate-bounce [animation-delay:-0.3s]"
              ></div>
              <div
                class="w-1.5 h-1.5 bg-[#FFB7C5] rounded-full animate-bounce [animation-delay:-0.15s]"
              ></div>
              <div
                class="w-1.5 h-1.5 bg-[#FFB7C5] rounded-full animate-bounce"
              ></div>
            </div>
          </div>
        {/if}
        <div class="h-20"></div>
      </div>

      <!-- Input Area: Optimized Padding & Highly Compact Frame -->
      <div class="p-6 px-10 pb-8 flex flex-col gap-4">
        <!-- Quick Actions (Optimized: Right Aligned & Tiny) -->
        {#if productSlug && productSlug.trim() !== ""}
          <div class="flex justify-end gap-2 px-1">
            {#each quickActions as action}
              {@const Icon = action.icon}
              <div class="relative group/action">
                {#if action.label === "An toàn da" && supportAgent.messages.length <= 1}
                  <div
                    class="absolute -top-[36px] left-1/2 -translate-x-1/2 whitespace-nowrap bg-gradient-to-r from-[#FFB7C5] to-[#FF8FA3] text-slate-950 px-3 py-1 rounded-xl text-[9px] font-black tracking-wide shadow-[0_4px_12px_rgba(255,183,197,0.3)] animate-bounce z-50 pointer-events-none before:content-[''] before:absolute before:-bottom-1 before:left-1/2 before:-translate-x-1/2 before:w-2 before:h-2 before:bg-[#FF8FA3] before:rotate-45"
                  >
                    Kiểm tra sản phẩm có phù hợp cho da của bạn không ✨
                  </div>
                {/if}
                <button
                  class="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-[#FFB7C5]/10 hover:border-[#FFB7C5]/30 hover:text-white border border-white/10 text-white/50 rounded-full text-[11px] font-bold transition-all active:scale-95 {action.label ===
                  'An toàn da'
                    ? 'ring-1 ring-[#FFB7C5]/30'
                    : ''}"
                  onclick={() => handleQuickAction(action)}
                >
                  <Icon
                    size={11}
                    class="text-[#FFB7C5] opacity-35 group-hover/action:opacity-100 transition-opacity"
                  />
                  {action.label}
                </button>
              </div>
            {/each}
          </div>
        {/if}

        <div
          class="relative bg-black/60 border border-white/10 rounded-2xl flex items-end shadow-2xl focus-within:ring-2 focus-within:ring-[#FFB7C5]/40 transition-all"
        >
          <textarea
            bind:this={inputElement}
            bind:value={userInput}
            onkeydown={handleKeyDown}
            placeholder="Nói chuyện với chuyên gia..."
            onfocus={handleInputFocus}
            onblur={handleInputBlur}
            class="block w-full bg-transparent border-0 py-4 pl-12 pr-14 text-white placeholder-gray-600 focus:ring-0 resize-none outline-none text-[15px] max-h-[160px] font-medium"
            style="min-height: 58px;"
            disabled={supportAgent.isTyping}
          ></textarea>

          <div
            class="absolute left-4 top-4.5 pointer-events-none opacity-25 group-focus-within:opacity-60 transition-opacity"
          >
            <Lock size={15} class="text-white" />
          </div>

          <button
            onclick={handleSend}
            disabled={!userInput.trim() || supportAgent.isTyping}
            class="absolute right-2 bottom-2 w-10 h-10 flex items-center justify-center rounded-xl {userInput.trim() &&
            !supportAgent.isTyping
              ? 'bg-[#FFB7C5] text-slate-950 shadow-[0_4px_12px_rgba(255,183,197,0.3)]'
              : 'bg-white/5 text-gray-700'} transition-all scale-100 active:scale-90"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .apple-glass-dark-modal {
    background: rgba(10, 10, 10, 0.95);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    transition: all 0.7s cubic-bezier(0.34, 1.56, 0.64, 1);
    will-change: backdrop-filter, background, opacity;
    box-shadow: 0 32px 64px rgba(0, 0, 0, 0.4);
  }

  /* Full-View Optimization: Prevent background bleed-through with 100% opacity layer */
  .apple-glass-dark-modal.is-expanded {
    background: #030712 !important;
    backdrop-filter: blur(60px) saturate(210%);
    -webkit-backdrop-filter: blur(60px) saturate(210%);
  }

  .pause-animations .apple-glass-dark-modal {
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    background: rgba(8, 12, 21, 0.98) !important;
  }

  /* Premium Frame Architecture (Elite V2.2) */
  .helen-box-premium {
    border-radius: 36px;
    box-shadow: 
      0 24px 64px rgba(0, 0, 0, 0.6), 
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .apple-glass-badge {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.02);
  }

  @keyframes float-premium {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-6px);
    }
  }

  .helen-float-premium {
    animation: float-premium 6s infinite ease-in-out;
  }

  .hide-scrollbar::-webkit-scrollbar {
    width: 0;
    display: none;
  }
  .hide-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
    scroll-behavior: smooth;
  }
  .animate-pulse-subtle {
    animation: pulse-subtle 2s infinite ease-in-out;
  }

  .pause-animations,
  .pause-animations * {
    animation-play-state: paused !important;
  }

  /* Elite V2.2: Helen CTA Button (Viral 2026 Aesthetic) */
  :global(.helen-cta-btn) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-top: 1.5rem;
    padding: 1.25rem 2.5rem;
    background: linear-gradient(135deg, #ffb7c5 0%, #ff8fa3 100%);
    color: #000 !important;
    font-weight: 900;
    letter-spacing: 0.1em;
    border-radius: 9999px;
    box-shadow: 0 10px 25px rgba(255, 183, 197, 0.3);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    text-decoration: none !important;
    width: fit-content;
    min-width: 240px;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  :global(.helen-cta-btn:hover) {
    transform: scale(1.03) translateY(-2px);
    box-shadow: 0 15px 35px rgba(255, 183, 197, 0.4);
    filter: brightness(1.1);
  }

  :global(.helen-cta-btn:active) {
    transform: scale(0.98);
  }
</style>
