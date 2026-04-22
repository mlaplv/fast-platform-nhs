<script lang="ts">
  import type { ComponentType, SvelteComponent } from 'svelte';
  import { onMount, tick } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { Send, X, ShieldCheck, PhoneCall, PackageSearch, Sparkles, UserRound, ScanSearch, Lock } from 'lucide-svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';
  import { authStore } from '$lib/state/authStore.svelte.ts';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getCartStore } from '$lib/state/commerce/cart.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { checkoutState } from '$lib/state/commerce/checkout.svelte.ts';
  import HelenIcon from './HelenIcon.svelte';
  
  const { productSlug = '' } = $props<{ productSlug?: string }>();
  const shopStore = getShopStore();
  const cartStore = getCartStore();
  
  let chatContainer = $state<HTMLDivElement>();
  let inputElement = $state<HTMLTextAreaElement>();
  let userInput = $state('');
  let isInputFocused = $state(false);
  
  interface QuickAction {
    label: string;
    icon: ComponentType<SvelteComponent>;
    prompt?: string;
    action?: () => void;
  }

  const quickActions: QuickAction[] = [
    { label: 'Chẩn đoán', icon: ScanSearch, action: scrollToDiagnostics },
    { label: 'Tình trạng đơn', icon: PackageSearch, prompt: 'Tôi muốn kiểm tra đơn hàng' },
    { label: 'Chính sách', icon: ShieldCheck, prompt: 'Cam kết bảo hành và đổi trả' }
  ];

  function scrollToDiagnostics() {
    const el = document.getElementById('diagnostics-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
      // On mobile, we might want to close the chat to let the user see the scanner
      supportAgent.isOpen = false;
    }
  }

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
    userInput = ''; 
    
    // Elite V2.2: Pass customer info for Zalo OA Bridge
    // Elite V3.1: Priority Auth Persistence — use real name if logged in
    const user = authStore.user;
    const customer = shopStore?.customerData;
    
    const name = user?.name || customer?.nameMasked || 'Khách ẩn danh';
    const userId = user?.id || null;

    // Elite V2.2: Pass Ground Truth pricing if on checkout page
    // [FIX] Explicitly read from singleton for precision sync
    const pricingContext = checkoutState.breakdown || cartStore.breakdown;
    
    await supportAgent.sendMessage(text, productSlug, name, undefined, userId, cartStore.items, cartStore.selectedVoucherIds, pricingContext);
    scrollToNewestMessage();
  }

  async function handleQuickAction(action: QuickAction) {
    if (action.action) {
      action.action();
      return;
    }
    // [FIX] Precision sync for quick actions
    const pricingContext = checkoutState.breakdown || cartStore.breakdown;
    await supportAgent.sendMessage(action.prompt, productSlug, undefined, undefined, undefined, cartStore.items, cartStore.selectedVoucherIds, pricingContext);
    scrollToNewestMessage();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
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
            chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'instant' });
          }
        }, 150);
      }
    }
  });

  async function scrollToNewestMessage() {
    await tick();
    if (!chatContainer) return;
    
    const messageElements = chatContainer.querySelectorAll('.message-bubble-container');
    const lastMessageEl = messageElements[messageElements.length - 1];
    
    if (lastMessageEl) {
      const role = lastMessageEl.getAttribute('data-role');
      if (role === 'assistant') {
        // Align to top of message if it's long, ensuring 'Helen' is visible
        lastMessageEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else {
        // Scroll to bottom for user's own message
        chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
      }
    }
  }
</script>

{#if supportAgent.isOpen}
  <!-- Minimal Backdrop Overlay (Elite V2.2: Transparent Refinement) -->
  <div 
    class="fixed inset-0 bg-transparent transition-opacity"
    onclick={supportAgent.close}
    onkeydown={(e) => e.key === 'Escape' && supportAgent.close()}
    role="button"
    tabindex="0"
    aria-label="Đóng Chat"
  ></div>

  <!-- Bottom Sheet (Liquid Glass - Viral 2026) -->
    <div 
      class="support-chat-container fixed inset-x-0 bottom-0 flex flex-col apple-glass-dark-mobile helen-box-v2 overflow-hidden {isInputFocused ? 'pause-animations' : ''}"
      style="z-index: {Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET}; height: 95svh; will-change: transform, opacity;"
      transition:fly={{ y: 800, duration: 500, easing: (t) => 1 - Math.pow(1 - t, 5) }}
    >
    <!-- Specular Highlight Layer (Mobile Liquid Glass) -->
    <div class="absolute top-[5%] left-[10%] w-[50%] h-[15%] bg-gradient-to-br from-white/10 to-transparent blur-2xl pointer-events-none z-0"></div>
    <div class="absolute top-10 left-8 w-1.5 h-1.5 bg-white/30 blur-[1px] rounded-full pointer-events-none z-0"></div>
    <!-- iOS Style Drag Handle -->
    <div class="absolute top-0 left-0 right-0 h-12 flex justify-center items-start pt-[18px] z-20 pointer-events-none">
      <div class="w-14 h-[6px] bg-white/20 rounded-full"></div>
    </div>

    <header class="flex-shrink-0 pt-[40px] px-8 pb-6 flex items-center justify-between relative z-10 border-b border-white/5 bg-transparent">
      <div class="flex items-center gap-4">
        <div class="relative">
          <div class="w-14 h-14 rounded-full bg-black/40 flex items-center justify-center shadow-[0_4px_16px_rgba(255,183,197,0.4)] border border-white/20 overflow-hidden">
            <HelenIcon size={56} color="#FFB7C5" isPaused={isInputFocused} />
          </div>
          <div class="absolute bottom-0 right-0 w-4 h-4 bg-[#FFB7C5] rounded-full ring-[3px] ring-[#0a0a0a] shadow-[0_0_12px_#FFB7C5]"></div>
        </div>
        <div>
          <h3 class="font-black text-white tracking-[-0.02em] leading-tight text-[21px] flex items-center gap-3 uppercase">
            {supportAgent.config.agentName}
            <div class="flex items-center gap-1.5 px-2 py-0.5 bg-white/5 border border-white/10 rounded-md">
              <Lock size={10} class="text-white/30" />
              <span class="text-[8px] text-white/40 font-black uppercase tracking-widest">AES_256</span>
            </div>
          </h3>
          <div class="flex items-center gap-2 mt-1.5">
             <div class="w-1.5 h-1.5 rounded-full bg-[#FFB7C5] shadow-[0_0_8px_#FFB7C5] animate-pulse"></div>
             <p class="text-[11px] text-[#FFB7C5] font-black uppercase tracking-[0.3em] opacity-90">
               {supportAgent.helenEnabled ? 'ĐANG HOẠT ĐỘNG' : 'CHUYÊN VIÊN TRỰC'}
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
        <div class="relative w-full p-4 bg-gradient-to-br from-[#FFB7C5]/20 to-black/40 border border-[#FFB7C5]/30 rounded-[24px] shadow-xl overflow-hidden">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-[#FFB7C5] flex items-center justify-center shadow-[0_0_10px_rgba(255,183,197,0.5)] flex-shrink-0">
              <Sparkles size={16} class="text-slate-950" />
            </div>
            <div class="flex flex-col">
              <p class="text-[12px] text-white font-black uppercase tracking-tight">
                Mức giá tối ưu cho liệu trình
              </p>
              <p class="text-[11px] text-white/80 leading-tight font-medium mt-0.5">
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
      class="flex-1 overflow-y-auto px-5 py-6 flex flex-col justify-start space-y-10 hide-scrollbar relative z-10"
    >
      {#if !supportAgent.optimalPriceNotice}
        <div class="flex flex-col items-center justify-center mb-10 opacity-30">
          <div class="flex items-center gap-2.5 px-5 py-2 bg-black/40 border border-white/10 rounded-full">
             <ShieldCheck size={14} class="text-[#FFB7C5]" />
             <span class="text-[10px] text-white/60 tracking-[0.2em] uppercase font-black">Hệ thống chuyên gia Helen v3.2</span>
          </div>
        </div>
      {/if}

      <!-- Viral Lazy Memory: Zalo-style pagination -->
      {#if supportAgent.hasMoreHistory}
        <div class="flex justify-center pb-10">
          <button 
            onclick={() => supportAgent.loadHistory()}
            disabled={supportAgent.isHistoryLoading}
            class="px-8 py-3 bg-white/5 active:bg-[#FFB7C5]/10 border border-white/5 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-[#FFB7C5] transition-all active:scale-95 disabled:opacity-30"
          >
            {supportAgent.isHistoryLoading ? 'ĐANG TẢI...' : 'TẢI THÊM TIN NHẮN CŨ'}
          </button>
        </div>
      {/if}

      {#if supportAgent.messages.length === 0 && supportAgent.isHistoryLoading}
        <div class="flex flex-col items-center justify-center py-20 opacity-40 animate-pulse">
          <div class="w-12 h-12 rounded-full border-2 border-t-[#FFB7C5] border-white/5 animate-spin"></div>
          <p class="text-[11px] font-black uppercase tracking-[0.2em] text-white mt-6">Đang đồng bộ dữ liệu...</p>
        </div>
      {/if}

      {#each supportAgent.messages as msg (msg.id)}
        <div 
          class="flex flex-col w-full group animate-in fade-in slide-in-from-bottom-4 duration-500 message-bubble-container"
          data-role={msg.role}
        >
          <!-- Name Label (Elite V3.1: Professional Identity) -->
          <div class="flex items-center gap-2 mb-2 px-12 {msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}">
            <span class="text-[10px] font-black uppercase tracking-[0.2em] {msg.role === 'user' ? 'text-[#FFB7C5]' : 'text-white/40'}">
              {msg.role === 'assistant' ? supportAgent.config.agentName : (authStore.user?.name || 'Quý khách')}
            </span>
            {#if msg.role === 'assistant'}
              <div class="w-1.5 h-1.5 rounded-full bg-[#FFB7C5] shadow-[0_0_8px_#FFB7C5] animate-pulse"></div>
            {/if}
          </div>

          <div class="flex items-start gap-4 w-full {msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}">
            
            <!-- Identity Icon -->
            <div class="flex-shrink-0 mt-1">
              {#if msg.role === 'assistant'}
                <div class="w-8 h-8 rounded-full bg-black/40 flex items-center justify-center border border-white/10 shadow-lg overflow-hidden">
                  <HelenIcon size={28} color="#FFB7C5" isPaused={isInputFocused} />
                </div>
              {:else}
                <div class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center border border-white/5 shadow-md overflow-hidden">
                  {#if authStore.user?.avatar_url}
                    <img src={authStore.user.avatar_url} alt="User" class="w-full h-full object-cover" />
                  {:else}
                    <UserRound size={16} class="text-white/60" />
                  {/if}
                </div>
              {/if}
            </div>

            <!-- Message Content -->
            <div class="flex-1 max-w-[85%] {msg.role === 'user' ? 'text-right' : 'text-left'}">
              <div class="px-2 py-1 text-[17px] leading-[1.7] break-words transition-all
                {msg.role === 'user' 
                  ? 'text-white font-bold drop-shadow-[0_2px_8px_rgba(255,255,255,0.1)]' 
                  : 'text-gray-100 font-medium'}">
              
              {#if msg.is_revoked}
                <div class="px-2 py-1 text-[17px] italic text-white/40 line-through select-none">
                  [Tin nhắn đã bị thu hồi]
                </div>
              {:else if msg.role === 'assistant' && msg.intent === 'ORDER_STATUS'}
                <div class="inline-flex items-center gap-3 px-4 py-2 mb-4 bg-[#FFB7C5]/10 text-[#FFB7C5] rounded-2xl border border-[#FFB7C5]/20 font-black text-[15px] uppercase tracking-wider">
                  <PackageSearch size={18} /> Tra cứu vận đơn
                </div>
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                <div class="opacity-90 mb-6">{@html msg.content.replace(/\n/g, '<br/>')}</div>
                <div class="w-full p-1 bg-black/40 rounded-[28px] border border-white/10 shadow-2xl overflow-hidden focus-within:ring-2 focus-within:ring-[#FFB7C5]/40 transition-all">
                  <div class="flex items-center">
                      <input type="tel" placeholder="Số điện thoại / Mã đơn" class="flex-1 px-6 py-4 bg-transparent text-white placeholder-gray-600 outline-none text-[16px]" />
                      <button class="mr-1 w-12 h-12 bg-[#FFB7C5] text-slate-950 rounded-full flex items-center justify-center shadow-lg active:scale-92 transition-all">
                          <Send size={20} />
                      </button>
                  </div>
                </div>
              {:else if msg.role === 'assistant' && msg.intent === 'PRICE_QUERY'}
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                <div class="text-[17px]">{@html msg.content.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-black">$1</strong>').replace(/\n/g, '<br/>')}</div>
                
                <button 
                  onclick={() => shopStore?.openCheckout(cartStore, shopStore.product!)}
                  class="mt-6 w-full py-5 bg-gradient-to-r from-[#FFB7C5] to-[#FF8FA3] text-slate-950 text-[16px] font-black rounded-[24px] shadow-[0_12px_32px_rgba(255,183,197,0.4)] active:scale-[0.98] transition-all uppercase tracking-wider animate-pulse-subtle"
                >
                   NHẬN ƯU ĐÃI NGAY →
                </button>
              {:else if msg.role === 'assistant'}
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                <div class="text-[17px]">
                  {@html msg.content
                    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-black">$1</strong>')
                    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" class="helen-cta-btn">$1</a>')
                    .replace(/\n/g, '<br/>')
                  }
                </div>
              {:else}
                <div class="px-2 py-1 text-[17px]">
                  {msg.content}
                </div>
              {/if}
            </div>
            
            <div class="text-[10px] text-white/10 mt-3 px-2 font-black uppercase tracking-[0.3em] opacity-0 group-hover:opacity-100 transition-all duration-300">
              {msg.timestamp.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>
      </div>
      {/each}

      {#if supportAgent.isTyping}
        <div class="flex justify-start w-full">
          <div class="flex items-center gap-3 px-5 py-3 bg-black/40 rounded-full border border-white/5">
            <div class="w-1.5 h-1.5 bg-[#FFB7C5] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
            <div class="w-1.5 h-1.5 bg-[#FFB7C5] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
            <div class="w-1.5 h-1.5 bg-[#FFB7C5] rounded-full animate-bounce"></div>
          </div>
        </div>
      {/if}
      <div class="h-[100px]"></div>
    </div>

    <!-- Pinned Bottom Area -->
    <div class="flex-shrink-0 safe-area-bottom w-full relative z-20 px-7 pt-1 pb-4">
      <!-- Quick Actions (Optimized: Tiny & Right Aligned) -->
      <div class="w-full flex justify-end gap-2 pb-2">
        {#each quickActions as action}
          {@const Icon = action.icon}
          <button 
            class="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 active:bg-white/10 text-white/60 border border-white/5 rounded-full text-[11px] font-bold transition-all active:scale-95"
            onclick={() => handleQuickAction(action)}
          >
            <Icon size={12} class="text-[#FFB7C5] opacity-50" /> {action.label}
          </button>
        {/each}
      </div>

      <!-- Capsule Dynamic Island Input -->
      <div class="relative bg-black/80 border border-white/5 rounded-[40px] flex items-end shadow-2xl focus-within:ring-2 focus-within:ring-[#FFB7C5]/40 transition-all">
        <textarea
          bind:this={inputElement}
          bind:value={userInput}
          onkeydown={handleKeyDown}
          placeholder="Nói chuyện với chuyên gia..."
          onfocus={handleInputFocus}
          onblur={handleInputBlur}
          class="block w-full bg-transparent border-0 py-[22px] pl-[60px] pr-20 text-white placeholder-gray-600 focus:ring-0 resize-none outline-none text-[17px] max-h-[160px] rounded-[40px] font-medium"
          style="min-height: 72px;"
          disabled={supportAgent.isTyping}
        ></textarea>

        <div class="absolute left-7 top-[22px] pointer-events-none opacity-20 group-focus-within:opacity-50 transition-opacity">
          <Lock size={20} class="text-white" />
        </div>
        
        <button 
          onclick={handleSend}
          disabled={!userInput.trim() || supportAgent.isTyping}
          class="absolute right-3 bottom-3 w-14 h-14 flex items-center justify-center rounded-full {userInput.trim() && !supportAgent.isTyping ? 'bg-[#FFB7C5] text-slate-950 shadow-[0_8px_24px_rgba(255,183,197,0.4)]' : 'bg-white/5 text-gray-700'} transition-all scale-100 active:scale-90"
        >
          <Send size={24} />
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
    0% { border-radius: 48px 48px 0 0; }
    33% { border-radius: 64px 32px 0 0; }
    66% { border-radius: 40px 60px 0 0; }
    100% { border-radius: 48px 48px 0 0; }
  }
  
  .safe-area-bottom {
    padding-bottom: calc(env(safe-area-inset-bottom, 24px) + 8px);
  }
  @keyframes pulse-subtle {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.02); opacity: 0.95; }
  }

  .animate-pulse-subtle {
    animation: pulse-subtle 2s infinite ease-in-out;
  }

  .pause-animations, .pause-animations * {
    animation-play-state: paused !important;
  }

  /* Elite V2.2: Helen CTA Button (Viral 2026 Aesthetic) */
  :global(.helen-cta-btn) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-top: 1.5rem;
    padding: 1.25rem 2.5rem;
    background: linear-gradient(135deg, #FFB7C5 0%, #FF8FA3 100%);
    color: #000 !important;
    font-weight: 900;
    text-transform: uppercase;
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
</style>
