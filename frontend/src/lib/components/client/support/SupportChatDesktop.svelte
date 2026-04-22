<script lang="ts">
  import type { ComponentType, SvelteComponent } from 'svelte';
  import { onMount, tick } from 'svelte';
  import { scale, fly } from 'svelte/transition';
  import { 
    Send, X, ShieldCheck, PhoneCall, 
    PackageSearch, Sparkles, UserRound,
    Maximize2, Minimize2, ScanSearch, Lock
  } from 'lucide-svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';
  import { authStore } from '$lib/state/authStore.svelte.ts';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getCartStore } from '$lib/state/commerce/cart.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { checkoutState } from '$lib/state/commerce/checkout.svelte';
  import HelenIcon from './HelenIcon.svelte';
  
  const { productSlug = '' } = $props<{ productSlug?: string }>();
  const shopStore = getShopStore();
  const cartStore = getCartStore();
  
  let chatContainer = $state<HTMLDivElement>();
  let inputElement = $state<HTMLTextAreaElement>();
  let userInput = $state('');
  let isExpanded = $state(false);
  let isInputFocused = $state(false);

  interface QuickAction {
    label: string;
    icon: ComponentType<SvelteComponent>; // Elite V2.2: Explicit Svelte 5 Component Type
    prompt?: string;
    action?: () => void;
  }

  const quickActions: QuickAction[] = [
    { label: 'Chẩn đoán', icon: ScanSearch, action: scrollToDiagnostics },
    { label: 'Đơn hàng', icon: PackageSearch, prompt: 'Tôi cần kiểm tra đơn hàng' },
    { label: 'Chính sách', icon: ShieldCheck, prompt: 'Quy định bảo hành và đổi trả' }
  ];

  function scrollToDiagnostics() {
    const el = document.getElementById('diagnostics-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
      // Logic optionally close chat or keep it open
    } else {
       // Fallback for mobile landing if any
       const mobileEl = document.querySelector('[data-section-idx="2"]');
       if (mobileEl) mobileEl.scrollIntoView({ behavior: 'smooth' });
    }
  }

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
    // [FIX] Explicitly read from singleton and provide fallback for diagnostic tracing
    const pricingContext = checkoutState.breakdown || undefined;
    if (!pricingContext && window.location.pathname.includes('/checkout')) {
      console.warn('⚠️ [SupportChat] Ground Truth Missing on Checkout page! Helen will use Fallback Brain.');
    }
    
    await supportAgent.sendMessage(text, productSlug, name, undefined, userId, cartStore.items, cartStore.selectedVoucherIds, pricingContext);
    scrollToNewestMessage();
  }

  async function handleQuickAction(action: QuickAction) {
    if (action.action) {
      action.action();
      return;
    }
    const pricingContext = checkoutState.breakdown || undefined;
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
  <!-- Hyper Drop Container (Viral 2026 Aggressive Asymmetric Shape) -->
  <div 
    class="support-chat-container fixed transform-gpu origin-bottom-right transition-all duration-700 ease-[cubic-bezier(0.34,1.56,0.64,1)] {isExpanded ? 'bottom-8 right-8 w-[90vw] h-[85vh] rounded-[48px] overflow-hidden bg-[#0a0a0a]' : 'bottom-[110px] right-8 w-[450px] h-[740px] max-h-[85vh] helen-box-v2 helen-float-v3'} {isInputFocused ? 'pause-animations' : ''}"
    style="z-index: {Z_INDEX_CLIENT.MODAL}; will-change: transform, opacity;"
    transition:scale={{ start: 0.7, opacity: 0, duration: 600, easing: (t) => 1 - Math.pow(1 - t, 5) }}
  >
    <!-- Liquid Neural Border (Optimized for No-GPU) -->
    <div class="absolute inset-[-1px] border border-white/10 {isExpanded ? 'rounded-[48px]' : 'helen-box-v2'} pointer-events-none z-[100]"></div>

    <!-- Specular Highlight (The "Refraction" layer that makes it viral) -->
    <div class="absolute top-[10%] left-[10%] w-[40%] h-[20%] bg-gradient-to-br from-white/20 to-transparent blur-xl {isExpanded ? 'hidden' : 'helen-box-v2'} pointer-events-none z-20"></div>
    <div class="absolute top-4 left-10 w-2 h-2 bg-white/40 blur-[2px] rounded-full {isExpanded ? 'hidden' : ''} pointer-events-none z-20"></div>

    <!-- Ultra-Glass Background Layer -->
    <div class="absolute inset-0 apple-glass-dark-modal pointer-events-none transition-all duration-700 {isExpanded ? 'rounded-[48px] is-expanded' : 'helen-box-v2'} border border-white/5 shadow-2xl"></div>

    <!-- Interface Contents -->
    <div class="relative z-10 flex flex-col h-full">
      <!-- Blended Ghost Header -->
      <header class="flex-shrink-0 pt-10 px-12 pb-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <div class="relative group/avatar">
            <div class="w-16 h-16 rounded-full bg-black/40 flex items-center justify-center shadow-[0_8px_32px_rgba(255,183,197,0.3)] border border-white/20 transition-transform group-hover/avatar:scale-105 overflow-hidden">
              <HelenIcon size={64} color="#FFB7C5" isPaused={isInputFocused} />
            </div>
            <div class="absolute bottom-0 right-0 w-4 h-4 bg-[#FFB7C5] rounded-full ring-[3px] ring-[#0a0a0a] shadow-[0_0_12px_#FFB7C5]"></div>
          </div>
          <div class="flex flex-col gap-1">
            <div class="flex items-center gap-3">
              <h3 class="font-black text-white tracking-[-0.03em] text-[24px] leading-none uppercase">
                {supportAgent.config.agentName}
              </h3>
              <div class="apple-glass-badge px-2 py-0.5 rounded-md flex items-center gap-1.5 border border-white/10">
                <Lock size={9} class="text-white/30" />
                <span class="text-[8px] text-white/40 font-black tracking-widest uppercase">AES_256</span>
              </div>
            </div>
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-[#FFB7C5] shadow-[0_0_8px_#FFB7C5] animate-pulse"></div>
                <p class="text-[10px] text-[#FFB7C5] font-black uppercase tracking-[0.35em] opacity-90">
                  {supportAgent.helenEnabled ? 'ĐANG HOẠT ĐỘNG' : 'CHUYÊN VIÊN TRỰC'}
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
              <Minimize2 size={20} class="group-hover/expand:scale-110 transition-transform" />
            {:else}
              <Maximize2 size={20} class="group-hover/expand:scale-110 transition-transform" />
            {/if}
          </button>
          <button 
            onclick={closeChat}
            class="w-11 h-11 flex items-center justify-center rounded-full bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all border border-red-500/10 group/close"
          >
            <X size={24} class="group-hover/close:rotate-90 transition-transform duration-300" />
          </button>
        </div>
      </header>
  
      <!-- Thread: Zero-Background Floating Text Aesthetic -->
      <div 
        bind:this={chatContainer}
        class="flex-1 overflow-y-auto px-6 py-4 flex flex-col justify-start space-y-12 hide-scrollbar relative"
      >
        <div class="flex flex-col items-center justify-center mb-10 opacity-30 hover:opacity-100 transition-opacity">
          <div class="flex items-center gap-2.5 px-5 py-2 bg-black/40 border border-white/10 rounded-full">
             <ShieldCheck size={14} class="text-[#FFB7C5]" />
             <span class="text-[10px] text-white/60 tracking-[0.2em] uppercase font-black italic">Hệ thống chuyên gia Helen v3.2</span>
          </div>
        </div>

        <!-- Viral Lazy Memory: Zalo-style pagination -->
        {#if supportAgent.hasMoreHistory}
          <div class="flex justify-center pb-8">
            <button 
              onclick={() => supportAgent.loadHistory()}
              disabled={supportAgent.isHistoryLoading}
              class="px-8 py-2.5 bg-white/5 hover:bg-[#FFB7C5]/10 border border-white/5 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-[#FFB7C5] transition-all active:scale-95 disabled:opacity-30"
            >
              {supportAgent.isHistoryLoading ? 'Đang đồng bộ dữ liệu...' : 'Tải thêm tin nhắn cũ'}
            </button>
          </div>
        {/if}
        {#if supportAgent.messages.length === 0 && supportAgent.isHistoryLoading}
          <div class="flex flex-col items-center justify-center py-20 opacity-40 animate-pulse">
            <div class="w-12 h-12 rounded-full border-2 border-t-[#FFB7C5] border-white/5 animate-spin"></div>
            <p class="text-[11px] font-black uppercase tracking-[0.2em] text-white mt-6">Đang đồng bộ dữ liệu giao tiếp...</p>
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

              <!-- Message Content (Minimalist Floating Text) -->
              <div class="flex-1 max-w-[85%] {msg.role === 'user' ? 'text-right' : 'text-left'}">
                <div class="text-[17px] leading-[1.7] break-words transition-all
                  {msg.role === 'user' 
                    ? 'text-white font-bold drop-shadow-[0_2px_8px_rgba(255,255,255,0.1)]' 
                    : 'text-gray-200 font-medium'}">
                
                {#if msg.is_revoked}
                  <div class="text-[17px] italic text-white/40 line-through select-none">
                    [Tin nhắn đã bị thu hồi]
                  </div>
                {:else if msg.role === 'assistant' && msg.intent === 'ORDER_STATUS'}
                  <div class="inline-flex items-center gap-3 px-4 py-2 mb-4 bg-[#FFB7C5]/10 text-[#FFB7C5] rounded-2xl border border-[#FFB7C5]/20 font-black text-[15px] uppercase tracking-wider">
                    <PackageSearch size={18} /> Tra cứu vận đơn
                  </div>
                  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                  <div class="text-[16px] mb-6">{@html msg.content.replace(/\n/g, '<br/>')}</div>
                  <div class="w-full max-w-[340px] p-1 bg-black/40 rounded-[32px] border border-white/10 shadow-2xl overflow-hidden focus-within:ring-2 focus-within:ring-[#FFB7C5]/40 transition-all">
                    <div class="flex items-center">
                        <input type="tel" placeholder="Số điện thoại / Mã đơn" class="flex-1 px-6 py-4 bg-transparent text-white placeholder-gray-600 outline-none text-[15px]" />
                        <button class="mr-1 w-12 h-12 bg-[#FFB7C5] text-slate-950 rounded-full flex items-center justify-center shadow-lg active:scale-95 transition-all">
                            <Send size={18} />
                        </button>
                    </div>
                  </div>
                {:else if msg.role === 'assistant' && msg.intent === 'PRICE_QUERY'}
                  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                  <div class="text-[17px]">{@html msg.content.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-black">$1</strong>').replace(/\n/g, '<br/>')}</div>
                  
                  <button 
                    onclick={() => shopStore?.openCheckout(cartStore, shopStore.product!)}
                    class="mt-6 px-10 py-4 bg-gradient-to-r from-[#FFB7C5] to-[#FF8FA3] text-slate-950 text-[16px] font-black rounded-full shadow-[0_12px_32px_rgba(255,183,197,0.4)] hover:shadow-[0_16px_40px_rgba(255,183,197,0.5)] transition-all active:scale-[0.98] uppercase tracking-wider animate-pulse-subtle"
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
                  {msg.content}
                {/if}
              </div>

              <!-- Timestamp -->
              <div class="text-[9px] text-white/10 mt-3 font-black uppercase tracking-[0.3em] opacity-0 group-hover:opacity-100 transition-all duration-300">
                {msg.timestamp.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>
      </div>
      {/each}
  
        {#if supportAgent.isTyping}
          <div class="flex justify-start w-full">
            <div class="flex items-center gap-3 px-5 py-2.5 bg-black/40 rounded-full border border-white/5">
              <div class="w-1.5 h-1.5 bg-[#FFB7C5] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
              <div class="w-1.5 h-1.5 bg-[#FFB7C5] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
              <div class="w-1.5 h-1.5 bg-[#FFB7C5] rounded-full animate-bounce"></div>
            </div>
          </div>
        {/if}
        <div class="h-20"></div>
      </div>
  
      <!-- Input Area: Optimized Padding -->
      <div class="p-6 px-10 pb-8 flex flex-col gap-5">
        <!-- Quick Actions (Optimized: Right Aligned & Tiny) -->
        <div class="flex justify-end gap-2 px-1">
          {#each quickActions as action}
            {@const Icon = action.icon}
            <button 
              class="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white/50 hover:text-white rounded-full text-[11px] font-bold transition-all active:scale-95 group/action"
              onclick={() => handleQuickAction(action)}
            >
              <Icon size={12} class="text-[#FFB7C5] opacity-30 group-hover/action:opacity-100 transition-opacity" /> {action.label}
            </button>
          {/each}
        </div>

        <div class="relative bg-black/60 border border-white/10 rounded-[44px] flex items-end shadow-2xl focus-within:ring-2 focus-within:ring-[#FFB7C5]/40 transition-all">
          <textarea
            bind:this={inputElement}
            bind:value={userInput}
            onkeydown={handleKeyDown}
            placeholder="Nói chuyện với chuyên gia..."
            onfocus={handleInputFocus}
            onblur={handleInputBlur}
            class="block w-full bg-transparent border-0 py-7 pl-14 pr-24 text-white placeholder-gray-600 focus:ring-0 resize-none outline-none text-[16px] max-h-[220px] font-medium"
            style="min-height: 80px;"
            disabled={supportAgent.isTyping}
          ></textarea>
          
          <div class="absolute left-6 top-7 pointer-events-none opacity-20 group-focus-within:opacity-50 transition-opacity">
            <Lock size={18} class="text-white" />
          </div>
          
          <button 
            onclick={handleSend}
            disabled={!userInput.trim() || supportAgent.isTyping}
            class="absolute right-4 bottom-4 w-16 h-16 flex items-center justify-center rounded-full {userInput.trim() && !supportAgent.isTyping ? 'bg-[#FFB7C5] text-slate-950 shadow-[0_8px_32px_rgba(255,183,197,0.4)]' : 'bg-white/5 text-gray-700'} transition-all scale-100 active:scale-90"
          >
            <Send size={28} />
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

  /* Liquid Hyper-Drop Shape V3 (Strict Aesthetic Morphing) */
  .helen-box-v2 {
      border-radius: 42% 58% 70% 30% / 45% 45% 55% 55%;
      animation: morph-blob-v3 12s infinite alternate cubic-bezier(0.445, 0.05, 0.55, 0.95);
  }

  @keyframes morph-blob-v3 {
    0% { border-radius: 42% 58% 70% 30% / 45% 45% 55% 55%; }
    33% { border-radius: 70% 30% 50% 50% / 30% 30% 70% 70%; }
    66% { border-radius: 50% 50% 30% 70% / 50% 30% 70% 50%; }
    100% { border-radius: 42% 58% 70% 30% / 45% 45% 55% 55%; }
  }

  .apple-glass-badge {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.02);
  }

  @keyframes liquid-float {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    33% { transform: translateY(-8px) rotate(0.5deg); }
    66% { transform: translateY(4px) rotate(-0.5deg); }
  }

  .helen-float-v3 {
    animation: liquid-float 12s infinite ease-in-out;
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
