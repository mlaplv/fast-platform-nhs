<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { scale, fly } from 'svelte/transition';
  import { 
    Send, X, ShieldCheck, PhoneCall, 
    PackageSearch, Sparkles, UserRound,
    Maximize2, Minimize2 
  } from 'lucide-svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  
  const { productSlug = '' } = $props<{ productSlug?: string }>();
  const shopStore = getShopStore();
  
  let chatContainer: HTMLDivElement;
  let userInput = $state('');
  let isExpanded = $state(false);

  const quickActions = [
    { label: 'Đơn hàng', icon: PackageSearch, prompt: 'Tôi cần kiểm tra đơn hàng' },
    { label: 'Chính sách', icon: ShieldCheck, prompt: 'Quy định bảo hành và đổi trả' }
  ];

  function closeChat() {
    supportAgent.isOpen = false;
    isExpanded = false;
  }

  function toggleExpand() {
    isExpanded = !isExpanded;
  }

  async function handleSend() {
    if (!userInput.trim() || supportAgent.isTyping) return;
    const text = userInput;
    userInput = ''; 
    
    // Elite V2.2: Pass customer info for Zalo OA Bridge
    const customer = shopStore.customerData;
    const name = customer?.nameMasked || 'Khách ẩn danh';
    
    await supportAgent.sendMessage(text, productSlug, name);
    scrollToBottom();
  }

  async function handleQuickAction(prompt: string) {
    if (supportAgent.isTyping) return;
    await supportAgent.sendMessage(prompt, productSlug);
    scrollToBottom();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  $effect(() => {
    if (supportAgent.messages.length > 0) {
      scrollToBottom();
    }
  });

  async function scrollToBottom() {
    await tick();
    if (chatContainer) {
      chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
    }
  }
</script>

{#if supportAgent.isOpen}
  <!-- Hyper Drop Container (Viral 2026 Aggressive Asymmetric Shape) -->
  <div 
    class="support-chat-container fixed transform-gpu origin-bottom-right transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] {isExpanded ? 'bottom-8 right-8 w-[90vw] h-[85vh] rounded-[48px]' : 'bottom-[110px] right-8 w-[440px] h-[680px] max-h-[85vh] hyper-drop-shape'}"
    style="z-index: {Z_INDEX_CLIENT.MODAL};"
    transition:scale={{ start: 0.8, opacity: 0, duration: 500, easing: (t) => 1 - Math.pow(1 - t, 5) }}
  >
    <!-- Ultra-Glass Background Layer -->
    <div class="absolute inset-0 apple-glass-dark-modal pointer-events-none transition-all duration-500 {isExpanded ? 'rounded-[48px]' : 'hyper-drop-shape'}"></div>

    <!-- Interface Contents -->
    <div class="relative z-10 flex flex-col h-full">
      <!-- Blended Ghost Header -->
      <header class="flex-shrink-0 pt-8 px-10 pb-6 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="relative group/avatar">
            <div class="w-14 h-14 rounded-full bg-gradient-to-br from-[#00A3FF] to-[#005B99] flex items-center justify-center shadow-[0_8px_24px_rgba(0,163,255,0.4)] border border-white/20 transition-transform group-hover/avatar:scale-105">
              <UserRound class="text-white w-7 h-7 drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]" />
            </div>
            <div class="absolute bottom-0 right-0 w-4 h-4 bg-[#34C759] rounded-full ring-[3px] ring-[#0a0a0a] shadow-[0_0_12px_#34C759]"></div>
          </div>
          <div>
            <h3 class="font-black text-white tracking-tight text-[19px] leading-tight">{supportAgent.config.agentName}</h3>
            <div class="flex items-center gap-2 mt-1">
               <span class="relative flex h-2 w-2">
                 <span class="animate-ping absolute inline-flex h-full w-full rounded-full {supportAgent.helenEnabled ? 'bg-[#00A3FF]' : 'bg-[#34C759]'} opacity-75"></span>
                 <span class="relative inline-flex rounded-full h-2 w-2 {supportAgent.helenEnabled ? 'bg-[#00A3FF]' : 'bg-[#34C759]'}"></span>
               </span>
               <p class="text-[11px] {supportAgent.helenEnabled ? 'text-[#00A3FF]' : 'text-[#34C759]'} font-black uppercase tracking-[0.2em] opacity-90">
                 {supportAgent.helenEnabled ? 'Chuyên gia trực tuyến' : 'Nhân viên trực'}
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
        class="flex-1 overflow-y-auto px-6 py-4 space-y-12 hide-scrollbar relative"
      >
        <div class="flex flex-col items-center justify-center mb-10 opacity-30 hover:opacity-100 transition-opacity">
          <div class="flex items-center gap-2.5 px-5 py-2 bg-white/5 border border-white/10 rounded-full backdrop-blur-xl">
             <ShieldCheck size={14} class="text-[#00A3FF]" />
             <span class="text-[10px] text-white/60 tracking-[0.2em] uppercase font-black italic">SmartShop Neural Link v2.2</span>
          </div>
        </div>

        <!-- Viral Lazy Memory: Zalo-style pagination -->
        {#if supportAgent.hasMoreHistory}
          <div class="flex justify-center pb-8">
            <button 
              onclick={() => supportAgent.loadHistory()}
              disabled={supportAgent.isHistoryLoading}
              class="px-8 py-2.5 bg-white/5 hover:bg-[#00A3FF]/10 border border-white/5 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-[#00A3FF] transition-all active:scale-95 disabled:opacity-30"
            >
              {supportAgent.isHistoryLoading ? 'Đang đồng bộ dữ liệu...' : 'Tải thêm tin nhắn cũ'}
            </button>
          </div>
        {/if}
  
        {#each supportAgent.messages as msg (msg.id)}
          <div class="flex {msg.role === 'user' ? 'justify-end text-right' : 'justify-start text-left'} w-full group animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div class="max-w-full relative flex flex-col {msg.role === 'user' ? 'items-end' : 'items-start'}">
              
              <div class="px-2 py-1 text-[17px] leading-[1.8] break-words transition-all
                {msg.role === 'user' 
                  ? 'text-white font-bold drop-shadow-[0_2px_12px_rgba(255,255,255,0.25)]' 
                  : 'text-gray-200 font-medium'}">
                
                {#if msg.role === 'assistant' && msg.intent === 'ORDER_STATUS'}
                  <div class="inline-flex items-center gap-3 px-4 py-2 mb-4 bg-[#00A3FF]/10 text-[#00A3FF] rounded-2xl border border-[#00A3FF]/20 font-black text-[15px] uppercase tracking-wider">
                    <PackageSearch size={18} /> Tra cứu vận đơn
                  </div>
                  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                  <div class="text-[16px] mb-6">{@html msg.content.replace(/\n/g, '<br/>')}</div>
                  <div class="w-full max-w-[340px] p-1 bg-white/5 rounded-[32px] border border-white/10 shadow-2xl backdrop-blur-3xl overflow-hidden focus-within:ring-2 focus-within:ring-[#00A3FF]/40 transition-all">
                    <div class="flex items-center">
                        <input type="tel" placeholder="Số điện thoại / Mã đơn" class="flex-1 px-6 py-4 bg-transparent text-white placeholder-gray-600 outline-none text-[15px]" />
                        <button class="mr-1 w-12 h-12 bg-[#00A3FF] text-white rounded-full flex items-center justify-center shadow-lg active:scale-95 transition-all">
                            <Send size={18} />
                        </button>
                    </div>
                  </div>
                {:else if msg.role === 'assistant' && msg.intent === 'PRICE_QUERY'}
                  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                  <div class="text-[17px]">{@html msg.content.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-black">$1</strong>').replace(/\n/g, '<br/>')}</div>
                  
                  <button 
                    onclick={() => shopStore.openCheckout()}
                    class="mt-6 px-10 py-4 bg-gradient-to-r from-[#00A3FF] to-[#005B99] text-white text-[16px] font-black rounded-full shadow-[0_12px_32px_rgba(0,163,255,0.4)] hover:shadow-[0_16px_40px_rgba(0,163,255,0.5)] transition-all active:scale-[0.98] uppercase tracking-wider animate-pulse-subtle"
                  >
                     NHẬN ƯU ĐÃI NGAY →
                  </button>
                {:else if msg.role === 'assistant'}
                  <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                  <div class="text-[17px]">{@html msg.content.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-black">$1</strong>').replace(/\n/g, '<br/>')}</div>
                {:else}
                  <span class="inline-block relative">
                    {msg.content}
                    <span class="absolute -bottom-1 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#00A3FF]/40 to-transparent"></span>
                  </span>
                {/if}
              </div>
              
              <div class="text-[9px] text-white/20 mt-4 px-2 font-black uppercase tracking-[0.3em] opacity-0 group-hover:opacity-100 transition-all duration-300">
                {msg.timestamp.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        {/each}
  
        {#if supportAgent.isTyping}
          <div class="flex justify-start w-full">
            <div class="flex items-center gap-3 px-5 py-2.5 bg-white/5 rounded-full border border-white/5 backdrop-blur-xl">
              <div class="w-1.5 h-1.5 bg-[#00A3FF] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
              <div class="w-1.5 h-1.5 bg-[#00A3FF] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
              <div class="w-1.5 h-1.5 bg-[#00A3FF] rounded-full animate-bounce"></div>
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
              onclick={() => handleQuickAction(action.prompt)}
            >
              <Icon size={12} class="text-[#00A3FF] opacity-30 group-hover/action:opacity-100 transition-opacity" /> {action.label}
            </button>
          {/each}
        </div>

        <div class="relative bg-white/5 border border-white/10 rounded-[44px] flex items-end shadow-2xl focus-within:ring-2 focus-within:ring-[#00A3FF]/40 transition-all backdrop-blur-[80px]">
          <textarea
            bind:value={userInput}
            onkeydown={handleKeyDown}
            placeholder="Nói chuyện với chuyên gia..."
            class="block w-full bg-transparent border-0 py-7 pl-9 pr-24 text-white placeholder-gray-600 focus:ring-0 resize-none outline-none text-[16px] max-h-[220px] font-medium"
            style="min-height: 80px;"
            disabled={supportAgent.isTyping}
          ></textarea>
          
          <button 
            onclick={handleSend}
            disabled={!userInput.trim() || supportAgent.isTyping}
            class="absolute right-4 bottom-4 w-16 h-16 flex items-center justify-center rounded-full {userInput.trim() && !supportAgent.isTyping ? 'bg-[#00A3FF] text-white shadow-[0_8px_32px_rgba(0,163,255,0.4)]' : 'bg-white/5 text-gray-700'} transition-all scale-100 active:scale-90"
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
    background: linear-gradient(165deg, rgba(16, 24, 39, 0.8) 0%, rgba(3, 7, 18, 0.98) 100%);
    backdrop-filter: blur(100px) saturate(210%);
    -webkit-backdrop-filter: blur(100px) saturate(210%);
    box-shadow: 
      0 60px 120px rgba(0, 0, 0, 0.9),
      inset 0 1px 1px rgba(255, 255, 255, 0.1),
      inset 0 0 0 1px rgba(255, 255, 255, 0.05);
  }

  /* Dramatic Asymmetric Water Drop Shape */
  .hyper-drop-shape {
      border-radius: 85% 15% 45% 55% / 65% 35% 65% 35%;
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
  @keyframes pulse-subtle {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.02); opacity: 0.95; }
  }

  .animate-pulse-subtle {
    animation: pulse-subtle 2s infinite ease-in-out;
  }
</style>
