<script lang="ts">
  import type { ComponentType, SvelteComponent } from "svelte";
  import { tick } from "svelte";
  import { fade, fly } from "svelte/transition";
  import Send from "@lucide/svelte/icons/send";
  import X from "@lucide/svelte/icons/x";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import UserRound from "@lucide/svelte/icons/user-round";
  import Beaker from "@lucide/svelte/icons/beaker";
  import Target from "@lucide/svelte/icons/target";
  import Lock from "@lucide/svelte/icons/lock";
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
  let isInputFocused = $state(false);
  let consultantCTAVisible = $state(true);

  interface QuickAction {
    label: string;
    icon: ComponentType<SvelteComponent>;
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
    isInputFocused = false;
  }

  function handleInputFocus() {
    isInputFocused = true;
  }

  function handleInputBlur() {
    isInputFocused = false;
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
    const userId = user?.id || null;

    // Elite V2.2: Pass Ground Truth pricing if on checkout page
    // [FIX] Explicitly read from singleton for precision sync
    const pricingContext = checkoutState.breakdown || cartStore.breakdown;

    await supportAgent.sendMessage(
      text,
      productSlug,
      name,
      undefined,
      userId,
      cartStore.items,
      cartStore.selectedVoucherIds,
      pricingContext,
    );
    scrollToNewestMessage();
  }

  async function handleQuickAction(action: QuickAction) {
    if (supportAgent.isTyping) return;
    if (action.action) {
      action.action();
      return;
    }
    const pricingContext = checkoutState.breakdown || cartStore.breakdown;
    await supportAgent.sendMessage(
      action.prompt,
      productSlug,
      undefined,
      undefined,
      undefined,
      cartStore.items,
      cartStore.selectedVoucherIds,
      pricingContext,
      action.displayPrompt,
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
      if (!isTyping) {
        inputElement.focus();
      }

      if (messages.length > 0) {
        scrollToNewestMessage();
      } else {
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
    const lastMessageEl = messageElements[messageElements.length - 1] as HTMLElement;

    if (lastMessageEl) {
      const role = lastMessageEl.getAttribute("data-role");
      if (role === "assistant") {
        // Calculate relative top position of the assistant bubble to align it with a safe padding thưa sếp
        const containerRect = chatContainer.getBoundingClientRect();
        const bubbleRect = lastMessageEl.getBoundingClientRect();
        const relativeTop = bubbleRect.top - containerRect.top + chatContainer.scrollTop;

        chatContainer.scrollTo({
          top: relativeTop - 16,
          behavior: "smooth",
        });
      } else {
        chatContainer.scrollTo({
          top: chatContainer.scrollHeight,
          behavior: "smooth",
        });
      }
    } else {
      chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: "smooth",
      });
    }
  }

  // Option 1: Chat trực tiếp ngay tại box
  async function requestInboxChat() {
    consultantCTAVisible = false;
    const user = authStore.user;
    const customer = shopStore?.customerData;
    const name = user?.name || customer?.nameMasked || "Khách ẩn danh";
    const userId = user?.id || null;
    const pricingContext = checkoutState.breakdown || cartStore.breakdown;
    await supportAgent.sendMessage(
      "[chat_inbox] Tôi muốn chat trực tiếp với chuyên viên tư vấn ngay tại đây",
      productSlug,
      name,
      undefined,
      userId,
      cartStore.items,
      cartStore.selectedVoucherIds,
      pricingContext,
      "💬 Yêu cầu chat trực tiếp với chuyên viên",
    );
    scrollToNewestMessage();
  }

  // Option 2: Mở Zalo OA
  async function requestZaloChat() {
    consultantCTAVisible = false;
    const oaId = "71197756917084615";
    window.open(`https://zalo.me/${oaId}`, "_blank");
    const user = authStore.user;
    const customer = shopStore?.customerData;
    const name = user?.name || customer?.nameMasked || "Khách ẩn danh";
    const userId = user?.id || null;
    const pricingContext = checkoutState.breakdown || cartStore.breakdown;
    await supportAgent.sendMessage(
      "[zalo_oa] Tôi muốn chat với chuyên viên qua Zalo OA",
      productSlug,
      name,
      undefined,
      userId,
      cartStore.items,
      cartStore.selectedVoucherIds,
      pricingContext,
      "💙 Yêu cầu kết nối qua Zalo OA",
    );
    scrollToNewestMessage();
  }
</script>

{#if supportAgent.isOpen}
  <!-- Minimal Backdrop Overlay (Elite V2.2: Transparent Refinement) -->
  <div
    class="fixed inset-0 bg-transparent transition-opacity"
    onclick={supportAgent.close}
    onkeydown={(e) => e.key === "Escape" && supportAgent.close()}
    role="button"
    tabindex="0"
    aria-label="Đóng Chat"
  ></div>

  <!-- Bottom Sheet (Liquid Glass - Viral 2026) -->
  <div
    class="support-chat-container fixed inset-x-0 bottom-0 flex flex-col apple-glass-dark-mobile helen-box-v2 overflow-hidden {isInputFocused
      ? 'pause-animations'
      : ''}"
    style="z-index: {Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET}; height: 95svh; will-change: transform, opacity;"
    transition:fly={{
      y: 800,
      duration: 500,
      easing: (t) => 1 - Math.pow(1 - t, 5),
    }}
  >
    <!-- Specular Highlight Layer (Mobile Liquid Glass) -->
    <div
      class="absolute top-[5%] left-[10%] w-[50%] h-[15%] bg-gradient-to-br from-white/10 to-transparent blur-2xl pointer-events-none z-0"
    ></div>
    <div
      class="absolute top-10 left-8 w-1.5 h-1.5 bg-white/30 blur-[1px] rounded-full pointer-events-none z-0"
    ></div>
    <!-- iOS Style Drag Handle -->
    <div
      class="absolute top-0 left-0 right-0 h-12 flex justify-center items-start pt-[18px] z-20 pointer-events-none"
    >
      <div class="w-14 h-[6px] bg-white/20 rounded-full"></div>
    </div>

    <header
      class="flex-shrink-0 pt-[40px] px-4 pb-6 flex items-center justify-between relative z-10 border-b border-white/5 bg-transparent"
    >
      <div class="flex items-center gap-4">
        <div class="relative">
          <div
            class="w-14 h-14 rounded-full bg-black/40 flex items-center justify-center shadow-[0_4px_16px_rgba(255,183,197,0.4)] border border-white/20 overflow-hidden"
          >
            <HelenIcon size={56} color="#FFB7C5" isPaused={isInputFocused} />
          </div>
          <div
            class="absolute bottom-0 right-0 w-4 h-4 bg-[#FFB7C5] rounded-full ring-[3px] ring-[#0a0a0a] shadow-[0_0_12px_#FFB7C5]"
          ></div>
        </div>
        <div>
          <h3
            class="font-black text-white tracking-[-0.02em] leading-tight text-[21px] flex items-center gap-3"
          >
            {supportAgent.config.agentName}
            <div
              class="flex items-center gap-1.5 px-2 py-0.5 bg-white/5 border border-white/10 rounded-md"
            >
              <Lock size={10} class="text-white/30" />
              <span class="text-[8px] text-white/40 font-black tracking-widest"
                >AES_256</span
              >
            </div>
          </h3>
          <div class="flex items-center gap-2 mt-1.5">
            <div
              class="w-1.5 h-1.5 rounded-full bg-[#FFB7C5] shadow-[0_0_8px_#FFB7C5] animate-pulse"
            ></div>
            <p
              class="text-[11px] text-[#FFB7C5] font-black tracking-[0.3em] opacity-90"
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
          onclick={closeChat}
          class="w-11 h-11 flex items-center justify-center rounded-full bg-white/5 active:bg-white/15 text-white/80 transition-all border border-white/5 backdrop-blur-3xl"
        >
          <X size={24} />
        </button>
      </div>
    </header>

    {#if supportAgent.optimalPriceNotice}
      <div
        transition:fly={{ y: -20, duration: 600 }}
        class="flex-shrink-0 px-6 pb-4 -mt-1 relative z-20"
      >
        <div
          class="relative w-full p-4 bg-gradient-to-br from-[#FFB7C5]/20 to-black/40 border border-[#FFB7C5]/30 rounded-[24px] shadow-xl overflow-hidden"
        >
          <div class="flex items-center gap-3">
            <div
              class="w-8 h-8 rounded-full bg-[#FFB7C5] flex items-center justify-center shadow-[0_0_10px_rgba(255,183,197,0.5)] flex-shrink-0"
            >
              <Sparkles size={16} class="text-slate-950" />
            </div>
            <div class="flex flex-col">
              <p class="text-[12px] text-white font-black tracking-tight">
                Mức giá tối ưu cho liệu trình
              </p>
              <p
                class="text-[11px] text-white/80 leading-tight font-medium mt-0.5"
              >
                Tuyệt vời! Đơn hàng của bạn đã đạt mức giá tối ưu.
              </p>
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Chat Thread: Zero-Background Floating Text -->
    <div
      bind:this={chatContainer}
      class="flex-1 overflow-y-auto px-4 py-6 flex flex-col justify-start space-y-10 hide-scrollbar relative z-10"
    >
      <!-- Viral Lazy Memory: Zalo-style pagination -->
      {#if supportAgent.hasMoreHistory}
        <div class="flex justify-center pb-10">
          <button
            onclick={() => supportAgent.loadHistory()}
            disabled={supportAgent.isHistoryLoading}
            class="px-8 py-3 bg-white/5 active:bg-[#FFB7C5]/10 border border-white/5 rounded-full text-[10px] font-black tracking-[0.2em] text-[#FFB7C5] transition-all active:scale-95 disabled:opacity-30"
          >
            {supportAgent.isHistoryLoading
              ? "ĐANG TẢI..."
              : "TẢI THÊM TIN NHẮN CŨ"}
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
            Đang đồng bộ dữ liệu...
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
            class="flex items-center gap-2 mb-2 px-12 {msg.role === 'user'
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
            <span class="text-[9px] text-white/30 font-medium tracking-normal">
              {msg.timestamp.toLocaleTimeString("vi-VN", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
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

            <!-- Message Content -->
            <div
              class="flex-1 max-w-[85%] {msg.role === 'user'
                ? 'text-right'
                : 'text-left'}"
            >
              <div
                class="px-2 py-1 text-[17px] leading-[1.7] break-words transition-all
                {msg.role === 'user'
                  ? 'text-white font-bold drop-shadow-[0_2px_8px_rgba(255,255,255,0.1)]'
                  : 'text-gray-100 font-medium'}"
              >
                {#if msg.is_revoked}
                  <div
                    class="px-2 py-1 text-[17px] italic text-white/40 line-through select-none"
                  >
                    [Tin nhắn đã bị thu hồi]
                  </div>
                {:else if msg.role === "assistant" && msg.intent === "ORDER_STATUS"}
                  <div
                    class="inline-flex items-center gap-3 px-4 py-2 mb-4 bg-[#FFB7C5]/10 text-[#FFB7C5] rounded-2xl border border-[#FFB7C5]/20 font-black text-[15px] tracking-wider"
                  >
                    <PackageSearch size={18} /> Tra cứu vận đơn
                  </div>
                  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                  <div class="opacity-90 mb-6">
                    {@html msg.content.replace(/\n/g, "<br/>")}
                  </div>
                  <div
                    class="w-full p-1 bg-black/40 rounded-[28px] border border-white/10 shadow-2xl overflow-hidden focus-within:ring-2 focus-within:ring-[#FFB7C5]/40 transition-all"
                  >
                    <div class="flex items-center">
                      <input
                        type="tel"
                        placeholder="Số điện thoại / Mã đơn"
                        class="flex-1 px-6 py-4 bg-transparent text-white placeholder-gray-600 outline-none text-[16px]"
                      />
                      <button
                        class="mr-1 w-12 h-12 bg-[#FFB7C5] text-slate-950 rounded-full flex items-center justify-center shadow-lg active:scale-92 transition-all"
                      >
                        <Send size={20} />
                      </button>
                    </div>
                  </div>
                {:else if msg.role === "assistant" && msg.intent === "PRICE_QUERY"}
                  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                  <div class="text-[17px]">
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
                    class="mt-6 w-full py-5 bg-gradient-to-r from-[#FFB7C5] to-[#FF8FA3] text-slate-950 text-[16px] font-black rounded-[24px] shadow-[0_12px_32px_rgba(255,183,197,0.4)] active:scale-[0.98] transition-all tracking-wider animate-pulse-subtle"
                  >
                    NHẬN ƯU ĐÃI NGAY →
                  </button>
                {:else if msg.role === "assistant"}
                  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                  <div class="text-[17px]">
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
                {:else}
                  <div class="px-2 py-1 text-[17px]">
                    {msg.content}
                  </div>
                {/if}
              </div>
            </div>
          </div>
        </div>
      {/each}

      <!-- ══════════════════════════════════════════════════════
           Consultant CTA — standalone, luôn hiển thị bên dưới
           toàn bộ tin nhắn, không phụ thuộc lịch sử chat
      ══════════════════════════════════════════════════════ -->
      {#if consultantCTAVisible && supportAgent.helenEnabled && supportAgent.messages.length > 0}
        <div class="px-2 pb-2 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <!-- Divider label -->
          <div class="flex items-center gap-3 mb-4">
            <div class="flex-1 h-px bg-white/8"></div>
            <span class="text-[10px] text-white/30 font-black tracking-[0.3em] uppercase whitespace-nowrap">
              Kết nối chuyên viên
            </span>
            <div class="flex-1 h-px bg-white/8"></div>
          </div>

          <div class="flex flex-col gap-2.5">
            <!-- Option 1: Chat trong box -->
            <button
              onclick={requestInboxChat}
              class="group relative flex items-center gap-4 w-full px-5 py-4 rounded-2xl overflow-hidden text-left transition-all duration-200 active:scale-[0.97]"
              style="background: linear-gradient(135deg, rgba(255,183,197,0.08) 0%, rgba(255,183,197,0.03) 100%); border: 1px solid rgba(255,183,197,0.15);"
            >
              <!-- Glow on press -->
              <div class="absolute inset-0 opacity-0 group-active:opacity-100 transition-opacity"
                style="background: radial-gradient(circle at 30% 50%, rgba(255,183,197,0.15) 0%, transparent 70%);"></div>
              <!-- Icon -->
              <div class="relative w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
                style="background: rgba(255,183,197,0.12); border: 1px solid rgba(255,183,197,0.2);">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="#FFB7C5" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <!-- Text -->
              <div class="relative flex flex-col min-w-0">
                <span class="text-[14px] font-black text-white tracking-tight leading-snug">Chat với nhân viên ngay tại đây</span>
                <span class="text-[11px] font-medium mt-0.5" style="color: rgba(255,183,197,0.55);">Chuyên viên phản hồi trong khung chat này</span>
              </div>
              <!-- Arrow -->
              <svg class="ml-auto flex-shrink-0 w-4 h-4 text-white/20 group-active:text-white/50 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>

            <!-- Option 2: Zalo OA -->
            <button
              onclick={requestZaloChat}
              class="group relative flex items-center gap-4 w-full px-5 py-4 rounded-2xl overflow-hidden text-left transition-all duration-200 active:scale-[0.97]"
              style="background: linear-gradient(135deg, rgba(0,104,255,0.10) 0%, rgba(0,104,255,0.04) 100%); border: 1px solid rgba(0,104,255,0.22);"
            >
              <div class="absolute inset-0 opacity-0 group-active:opacity-100 transition-opacity"
                style="background: radial-gradient(circle at 30% 50%, rgba(0,132,255,0.18) 0%, transparent 70%);"></div>
              <!-- Icon -->
              <div class="relative w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
                style="background: rgba(0,104,255,0.15); border: 1px solid rgba(0,104,255,0.25);">
                <svg class="w-5 h-5" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 3C10.611 3 3 10.164 3 19c0 4.884 2.21 9.267 5.707 12.277L7.5 35l4.215-2.192A18.14 18.14 0 0020 35c9.389 0 17-7.164 17-16S29.389 3 20 3z" fill="#0068FF"/>
                  <path d="M28.5 22.6c-.3-.15-1.767-.87-2.04-.97-.273-.097-.472-.146-.67.147-.2.293-.77.97-.944 1.168-.173.2-.347.22-.646.074-.3-.147-1.263-.465-2.406-1.485-.888-.793-1.488-1.772-1.663-2.072-.175-.3-.019-.462.132-.61.135-.135.3-.35.45-.525.148-.175.197-.3.296-.498.098-.2.05-.374-.025-.523-.074-.147-.67-1.614-.918-2.21-.242-.578-.487-.5-.67-.51-.173-.008-.372-.01-.57-.01-.2 0-.523.074-.797.37-.273.297-1.04 1.016-1.04 2.48 0 1.463 1.065 2.877 1.213 3.076.148.2 2.096 3.2 5.08 4.487.71.307 1.264.49 1.695.627.713.227 1.362.195 1.876.118.572-.086 1.767-.722 2.016-1.42.25-.7.25-1.298.175-1.42-.075-.123-.273-.197-.572-.347z" fill="white"/>
                </svg>
              </div>
              <!-- Text -->
              <div class="relative flex flex-col min-w-0">
                <span class="text-[14px] font-black tracking-tight leading-snug" style="color: #5BA4FF;">Chat qua Zalo OA</span>
                <span class="text-[11px] font-medium mt-0.5" style="color: rgba(91,164,255,0.55);">Mở Zalo, chuyên viên cũng được thông báo</span>
              </div>
              <!-- Arrow -->
              <svg class="ml-auto flex-shrink-0 w-4 h-4 text-white/20 group-active:text-white/50 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
          </div>
        </div>
      {/if}

      {#if supportAgent.isTyping}

        <div class="flex justify-start w-full">
          <div
            class="flex items-center gap-3 px-5 py-3 bg-black/40 rounded-full border border-white/5"
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
      <div class="h-[100px]"></div>
    </div>

    <!-- Pinned Bottom Area -->
    <div
      class="flex-shrink-0 safe-area-bottom w-full relative z-20 px-4 pt-1 pb-4"
    >
      <!-- Quick Actions (Optimized: Tiny, Borderless, Icon-free & Right Aligned) -->
      {#if productSlug && productSlug.trim() !== ""}
        <div class="w-full flex justify-end gap-1.5 pb-2.5">
          {#each quickActions as action}
            <div class="relative">
              {#if action.label === "An toàn da" && supportAgent.messages.length <= 1}
                <div class="helen-tip-bubble">
                  Kiểm tra sản phẩm có phù hợp cho da của bạn không ✨
                </div>
              {/if}
              <button
                class="px-2.5 py-1 bg-white/5 active:bg-white/10 text-white/60 border border-white/5 rounded-full text-[10px] font-black tracking-wide transition-all active:scale-95 {action.label ===
                'An toàn da'
                  ? 'ring-1 ring-[#FFB7C5]/30 text-white'
                  : ''} disabled:opacity-20 disabled:pointer-events-none disabled:cursor-not-allowed"
                disabled={supportAgent.isTyping}
                onclick={() => handleQuickAction(action)}
              >
                {action.label}
              </button>
            </div>
          {/each}
        </div>
      {/if}

      <!-- Sleek 2026 Premium Chat Input Bar (Ultra-Slim & Sleek) -->
      <div
        class="relative bg-[#121212]/90 border border-white/10 rounded-[22px] focus-within:border-[#FFB7C5]/30 focus-within:bg-[#1a1a1a] flex items-end shadow-xl transition-all px-3.5 py-1"
      >
        <textarea
          bind:this={inputElement}
          bind:value={userInput}
          onkeydown={handleKeyDown}
          placeholder="Nhập tin nhắn..."
          onfocus={handleInputFocus}
          onblur={handleInputBlur}
          class="block w-full bg-transparent border-0 py-2 pl-1 pr-10 text-white placeholder-white/35 focus:ring-0 resize-none outline-none text-[14px] max-h-[120px] font-medium animate-none"
          style="min-height: 36px; line-height: 1.4;"
          disabled={supportAgent.isTyping}
        ></textarea>

        <button
          onclick={handleSend}
          disabled={!userInput.trim() || supportAgent.isTyping}
          class="absolute right-2 bottom-1.5 w-8 h-8 flex items-center justify-center rounded-full transition-all {userInput.trim() &&
          !supportAgent.isTyping
            ? 'bg-[#FFB7C5] text-slate-950 shadow-md active:scale-90'
            : 'bg-white/5 text-white/20'}"
        >
          <Send size={14} />
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .apple-glass-dark-mobile {
    background: rgba(10, 10, 10, 0.95);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    transition: backdrop-filter 0.3s ease;
    will-change: transform, opacity;
  }

  .pause-animations.apple-glass-dark-mobile {
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    background: rgba(8, 12, 21, 0.99) !important;
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

  .helen-box-v2 {
    border-radius: 40px 40px 0 0;
    animation: mobile-morph 10s infinite alternate ease-in-out;
  }

  @keyframes mobile-morph {
    0% {
      border-radius: 48px 48px 0 0;
    }
    33% {
      border-radius: 64px 32px 0 0;
    }
    66% {
      border-radius: 40px 60px 0 0;
    }
    100% {
      border-radius: 48px 48px 0 0;
    }
  }

  .safe-area-bottom {
    padding-bottom: calc(env(safe-area-inset-bottom, 24px) + 8px);
  }
  @keyframes pulse-subtle {
    0%,
    100% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.02);
      opacity: 0.95;
    }
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
    min-width: 220px;
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

  /* Premium Liquid Glass - Helen Safe Skin Tip Bubble */
  .helen-tip-bubble {
    position: absolute;
    bottom: calc(100% + 14px);
    left: -20px;
    white-space: nowrap;
    background: linear-gradient(90deg, #ffb7c5, #ff8fa3);
    color: #0a0a0a;
    padding: 6px 12px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.025em;
    box-shadow: 0 4px 16px rgba(255, 183, 197, 0.4);
    animation: helen-bounce-tip 2s infinite ease-in-out;
    z-index: 50;
    pointer-events: none;
  }

  .helen-tip-bubble::before {
    content: "";
    position: absolute;
    bottom: -4px;
    left: 68px;
    transform: translateX(-50%) rotate(45deg);
    width: 8px;
    height: 8px;
    background: #ff8fa3;
  }

  @keyframes helen-bounce-tip {
    0%,
    100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-6px);
    }
  }
</style>
