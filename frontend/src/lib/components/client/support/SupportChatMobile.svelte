<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { Send, X, ShieldCheck, PhoneCall, PackageSearch, Sparkles, UserRound } from 'lucide-svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  
  const { productSlug = '' } = $props<{ productSlug?: string }>();
  const shopStore = getShopStore();
  
  let chatContainer: HTMLDivElement;
  let userInput = $state('');
  
  const quickActions = [
    { label: 'Tình trạng đơn', icon: PackageSearch, prompt: 'Tôi muốn kiểm tra đơn hàng' },
    { label: 'Chính sách', icon: ShieldCheck, prompt: 'Cam kết bảo hành và đổi trả' }
  ];

  function closeChat() {
    supportAgent.isOpen = false;
  }

  async function handleSend() {
    if (!userInput.trim() || supportAgent.isTyping) return;
    const text = userInput;
    userInput = ''; 
    await supportAgent.sendMessage(text, productSlug);
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
  <!-- Backdrop Blur Overlay -->
  <div 
    class="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity"
    style="z-index: {Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET - 1}"
    transition:fade={{ duration: 300 }}
    onclick={closeChat}
    aria-hidden="true"
  ></div>

  <!-- Bottom Sheet (Liquid Glass - Viral 2026) -->
  <div 
    class="support-chat-container fixed inset-x-0 bottom-0 flex flex-col apple-glass-dark-mobile rounded-t-[48px] overflow-hidden shadow-[0_-32px_100px_rgba(0,0,0,0.8)]"
    style="z-index: {Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET}; height: 95svh;"
    transition:fly={{ y: '100%', duration: 500, easing: (t) => 1 - Math.pow(1 - t, 5) }}
  >
    <!-- iOS Style Drag Handle -->
    <div class="absolute top-0 left-0 right-0 h-12 flex justify-center items-start pt-[18px] z-20 pointer-events-none">
      <div class="w-14 h-[6px] bg-white/20 rounded-full"></div>
    </div>

    <!-- Header (iOS Blended Frost) -->
    <header class="flex-shrink-0 pt-[40px] px-8 pb-6 flex items-center justify-between relative z-10 border-b border-white/5 bg-transparent">
      <div class="flex items-center gap-4">
        <div class="relative">
          <div class="w-14 h-14 rounded-full bg-gradient-to-br from-[#00A3FF] to-[#005B99] flex items-center justify-center shadow-[0_4px_16px_rgba(0,163,255,0.4)] border border-white/20">
            <UserRound class="text-white w-7 h-7 drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]" />
          </div>
          <div class="absolute bottom-0 right-0 w-4 h-4 bg-[#34C759] rounded-full ring-[3px] ring-[#0a0a0a] shadow-[0_0_12px_#34C759]"></div>
        </div>
        <div>
          <h3 class="font-black text-white tracking-tight leading-tight text-[19px]">{supportAgent.config.agentName}</h3>
          <div class="flex items-center gap-2 mt-1">
             <span class="relative flex h-2 w-2">
               <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00A3FF] opacity-75"></span>
               <span class="relative inline-flex rounded-full h-2 w-2 bg-[#00A3FF]"></span>
             </span>
             <p class="text-[11px] text-[#00A3FF] font-black uppercase tracking-[0.2em] opacity-90">Chuyên gia trực tuyến</p>
          </div>
        </div>
      </div>
      <button 
        onclick={closeChat}
        class="w-11 h-11 flex items-center justify-center rounded-full bg-white/5 active:bg-white/15 text-white/80 transition-all border border-white/5 backdrop-blur-3xl"
      >
        <X size={24} />
      </button>
    </header>

    <!-- Chat Thread: Zero-Background Floating Text -->
    <div 
      bind:this={chatContainer}
      class="flex-1 overflow-y-auto px-5 py-6 space-y-10 hide-scrollbar relative z-10"
    >
      <div class="flex flex-col items-center justify-center mb-10 opacity-30">
        <div class="flex items-center gap-2.5 px-5 py-2 bg-white/5 border border-white/10 rounded-full backdrop-blur-xl">
           <ShieldCheck size={14} class="text-[#00A3FF]" />
           <span class="text-[10px] text-white/60 tracking-[0.2em] uppercase font-black">Secure Neural Link Established</span>
        </div>
      </div>

      <!-- Viral Lazy Memory: Zalo-style pagination -->
      {#if supportAgent.hasMoreHistory}
        <div class="flex justify-center pb-10">
          <button 
            onclick={() => supportAgent.loadHistory()}
            disabled={supportAgent.isHistoryLoading}
            class="px-8 py-3 bg-white/5 active:bg-[#00A3FF]/10 border border-white/5 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-[#00A3FF] transition-all active:scale-95 disabled:opacity-30"
          >
            {supportAgent.isHistoryLoading ? 'ĐANG TẢI...' : 'TẢI THÊM TIN NHẮN CŨ'}
          </button>
        </div>
      {/if}

      {#each supportAgent.messages as msg (msg.id)}
        <div class="flex {msg.role === 'user' ? 'justify-end text-right' : 'justify-start text-left'} w-full group animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div class="max-w-full relative flex flex-col {msg.role === 'user' ? 'items-end' : 'items-start'}">
            
            <div class="px-2 py-1 text-[17px] leading-[1.8] break-words transition-all
              {msg.role === 'user' 
                ? 'text-white font-bold drop-shadow-[0_2px_8px_rgba(255,255,255,0.2)]' 
                : 'text-gray-100 font-medium'}">
              
              {#if msg.role === 'assistant' && msg.intent === 'ORDER_STATUS'}
                <div class="inline-flex items-center gap-3 px-4 py-2 mb-4 bg-[#00A3FF]/10 text-[#00A3FF] rounded-2xl border border-[#00A3FF]/20 font-black text-[15px] uppercase tracking-wider">
                  <PackageSearch size={18} /> Tra cứu vận đơn
                </div>
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                <div class="opacity-90 mb-6">{@html msg.content.replace(/\n/g, '<br/>')}</div>
                <div class="w-full p-1 bg-white/5 rounded-[28px] border border-white/10 shadow-2xl backdrop-blur-3xl overflow-hidden focus-within:ring-2 focus-within:ring-[#00A3FF]/40 transition-all">
                  <div class="flex items-center">
                      <input type="tel" placeholder="Số điện thoại / Mã đơn" class="flex-1 px-6 py-4 bg-transparent text-white placeholder-gray-600 outline-none text-[16px]" />
                      <button class="mr-1 w-12 h-12 bg-[#00A3FF] text-white rounded-full flex items-center justify-center shadow-lg active:scale-92 transition-all">
                          <Send size={20} />
                      </button>
                  </div>
                </div>
              {:else if msg.role === 'assistant' && msg.intent === 'PRICE_QUERY'}
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                <div class="text-[17px]">{@html msg.content.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-black">$1</strong>').replace(/\n/g, '<br/>')}</div>
                
                <button 
                  onclick={() => shopStore.openCheckout()}
                  class="mt-6 w-full py-5 bg-gradient-to-r from-[#00A3FF] to-[#005B99] text-white text-[16px] font-black rounded-[24px] shadow-[0_12px_32px_rgba(0,163,255,0.4)] active:scale-[0.98] transition-all uppercase tracking-wider animate-pulse-subtle"
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
            
            <div class="text-[10px] text-white/20 mt-4 px-2 font-black uppercase tracking-[0.3em] opacity-0 group-hover:opacity-100 transition-all duration-300">
              {msg.timestamp.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>
      {/each}

      {#if supportAgent.isTyping}
        <div class="flex justify-start w-full">
          <div class="flex items-center gap-3 px-5 py-3 bg-white/5 rounded-full border border-white/5 backdrop-blur-xl">
            <div class="w-1.5 h-1.5 bg-[#00A3FF] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
            <div class="w-1.5 h-1.5 bg-[#00A3FF] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
            <div class="w-1.5 h-1.5 bg-[#00A3FF] rounded-full animate-bounce"></div>
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
            onclick={() => handleQuickAction(action.prompt)}
          >
            <Icon size={12} class="text-[#00A3FF] opacity-50" /> {action.label}
          </button>
        {/each}
      </div>

      <!-- Capsule Dynamic Island Input -->
      <div class="relative bg-black/60 border border-white/5 rounded-[40px] flex items-end shadow-2xl focus-within:ring-2 focus-within:ring-[#00A3FF]/40 transition-all backdrop-blur-[100px]">
        <textarea
          bind:value={userInput}
          onkeydown={handleKeyDown}
          placeholder="Nói chuyện với chuyên gia..."
          class="block w-full bg-transparent border-0 py-[22px] pl-[30px] pr-20 text-white placeholder-gray-600 focus:ring-0 resize-none outline-none text-[17px] max-h-[160px] rounded-[40px] font-medium"
          style="min-height: 72px;"
          disabled={supportAgent.isTyping}
        ></textarea>
        
        <button 
          onclick={handleSend}
          disabled={!userInput.trim() || supportAgent.isTyping}
          class="absolute right-3 bottom-3 w-14 h-14 flex items-center justify-center rounded-full {userInput.trim() && !supportAgent.isTyping ? 'bg-[#00A3FF] text-white shadow-[0_8px_24px_rgba(0,163,255,0.4)]' : 'bg-white/5 text-gray-700'} transition-all scale-100 active:scale-90"
        >
          <Send size={24} />
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .apple-glass-dark-mobile {
    background: linear-gradient(165deg, rgba(8, 12, 21, 0.8) 0%, rgba(2, 4, 10, 0.99) 100%);
    backdrop-filter: blur(100px) saturate(210%);
    -webkit-backdrop-filter: blur(100px) saturate(210%);
    box-shadow: 
      0 -40px 120px rgba(0,0,0,0.8),
      inset 0 1px 1px rgba(255, 255, 255, 0.1),
      inset 0 0 0 1px rgba(255, 255, 255, 0.05);
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
</style>
