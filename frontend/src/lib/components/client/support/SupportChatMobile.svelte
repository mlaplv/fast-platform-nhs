<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { Send, X, ShieldCheck, PhoneCall, PackageSearch, Sparkles, UserRound } from 'lucide-svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  
  const { productSlug = '' } = $props<{ productSlug?: string }>();
  
  let chatContainer: HTMLElement | undefined = $state();
  let userInput = $state('');
  
  const quickActions = [
    { label: 'Tình trạng đơn', icon: PackageSearch, prompt: 'Tôi cần kiểm tra đơn hàng' },
    { label: 'Đổi trả', icon: ShieldCheck, prompt: 'Quy định bảo hành và đổi trả' },
    { label: 'Dược sĩ', icon: PhoneCall, prompt: 'Gặp chuyên gia hỗ trợ' }
  ];

  function closeChat() {
    supportAgent.close();
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
  <!-- Backdrop Blur overlay iOS Style -->
  <div 
    class="fixed inset-0 bg-black/70 backdrop-blur-md transition-opacity"
    style="z-index: {Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET - 1}"
    transition:fade={{ duration: 300, easing: (t) => t * t }}
    onclick={closeChat}
    aria-hidden="true"
  ></div>

  <!-- Bottom Sheet (Liquid Glass Dark Mode - Viral 2026 organic) -->
  <div 
    class="fixed inset-x-0 bottom-0 flex flex-col apple-glass-dark-mobile shadow-[0_-32px_80px_rgba(0,0,0,0.6)] rounded-t-[48px] overflow-hidden"
    style="z-index: {Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET}; height: 94svh;"
    transition:fly={{ y: '100%', duration: 500, opacity: 1, easing: (t) => 1 - Math.pow(1 - t, 5) }}
  >
    <!-- Drag Handle Area -->
    <div class="absolute top-0 left-0 right-0 h-10 flex justify-center items-start pt-[14px] z-20 pointer-events-none">
      <div class="w-14 h-[6px] bg-white/20 rounded-full"></div>
    </div>

    <!-- Header (iOS Blended Frost) -->
    <header class="flex-shrink-0 pt-[32px] px-7 pb-4 flex items-center justify-between relative z-10 border-b border-white/5 bg-transparent">
      <div class="flex items-center gap-3.5">
        <div class="relative">
          <div class="w-13 h-13 rounded-full bg-gradient-to-b from-[#00A3FF] to-[#005B99] flex items-center justify-center shadow-[0_4px_16px_rgba(0,163,255,0.4)] border border-white/20">
            <UserRound class="text-white w-[26px] h-[26px] drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]" />
          </div>
          <!-- Tiny Apple-style online dot -->
          <div class="absolute bottom-0 right-0 w-4 h-4 bg-[#34C759] rounded-full ring-[3px] ring-[#0f172a] shadow-[0_0_8px_#34C759]"></div>
        </div>
        <div>
          <h3 class="font-bold text-white tracking-tight leading-tight text-[18px]">{supportAgent.config.agentName}</h3>
          <p class="text-[13px] text-[#00A3FF] font-semibold tracking-wide flex items-center gap-1.5 opacity-90 mt-0.5">
             Chuyên gia trực tuyến
          </p>
        </div>
      </div>
      <button 
        onclick={closeChat}
        class="w-[38px] h-[38px] flex items-center justify-center rounded-full bg-white/5 hover:bg-white/15 text-white/80 transition-all backdrop-blur-md shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] border border-white/5"
      >
        <X size={22} strokeWidth={2} class="opacity-90" />
      </button>
    </header>

    <!-- Chat Thread -->
    <div 
      bind:this={chatContainer}
      class="flex-1 overflow-y-auto px-6 py-5 space-y-8 hide-scrollbar relative z-10"
    >
      <div class="flex flex-col items-center justify-center mb-8 mt-1 relative">
        <div class="flex items-center gap-2.5 px-4.5 py-2 bg-[#00A3FF]/10 border border-[#00A3FF]/20 rounded-full backdrop-blur-sm">
          <ShieldCheck size={14} class="text-[#00A3FF]" />
          <span class="text-[11px] text-[#00A3FF] tracking-[0.08em] uppercase font-bold">SmartShop AI Shield       {#each supportAgent.messages as msg (msg.id)}
        <div class="flex {msg.role === 'user' ? 'justify-end text-right' : 'justify-start text-left'} w-full group animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div class="max-w-[90%] relative flex flex-col {msg.role === 'user' ? 'items-end' : 'items-start'}">
            
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
                      <input type="tel" placeholder="Số điện thoại / Mã đơn" class="flex-1 px-5 py-4 bg-transparent text-white placeholder-gray-600 outline-none text-[16px]" />
                      <button class="mr-1 w-12 h-12 bg-[#00A3FF] text-white rounded-full flex items-center justify-center shadow-lg active:scale-92 transition-all">
                          <Send size={20} />
                      </button>
                  </div>
                </div>
              {:else if msg.role === 'assistant' && msg.intent === 'PRICE_QUERY'}
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                <div class="text-[17px]">{@html msg.content.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-black">$1</strong>').replace(/\n/g, '<br/>')}</div>
                <button class="mt-6 w-full py-4.5 bg-gradient-to-r from-[#00A3FF] to-[#005B99] text-white text-[16px] font-black rounded-full shadow-[0_10px_28px_rgba(0,163,255,0.4)] active:scale-95 transition-all">
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
        <div class="flex justify-start w-full animate-pulse">
          <div class="flex items-center gap-3 px-5 py-3 bg-white/5 rounded-full border border-white/5 backdrop-blur-xl">
            <div class="w-1.5 h-1.5 bg-[#00A3FF] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
            <div class="w-1.5 h-1.5 bg-[#00A3FF] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
            <div class="w-1.5 h-1.5 bg-[#00A3FF] rounded-full animate-bounce"></div>
          </div>
        </div>
      {/if}
      <div class="h-[80px]"></div>
    </div>

    <!-- Pinned Bottom Area with SafeArea/Keyboard Awareness -->
    <div class="flex-shrink-0 bg-transparent safe-area-bottom w-full relative z-20 px-6 pt-0 pb-6">
      
      <!-- iOS Lockscreen-like Transparent Quick Actions -->
      <div class="w-full overflow-x-auto hide-scrollbar flex items-center gap-3 pb-4 pt-1">
        {#each quickActions as action}
          {@const Icon = action.icon}
          <button 
            class="flex-shrink-0 flex items-center gap-2 px-5 py-3 bg-white/10 active:bg-white/20 text-gray-200 border border-white/5 rounded-full text-[15px] font-bold shadow-[0_4px_16px_rgba(0,0,0,0.5),inset_0_1px_1px_rgba(255,255,255,0.05)] transition-all active:scale-95"
            onclick={() => handleQuickAction(action.prompt)}
          >
            <Icon size={16} class="opacity-80 text-[#00A3FF]" /> {action.label}
          </button>
        {/each}
      </div>

      <!-- Capsule Dynamic Island Input -->
      <div class="relative bg-black/50 border border-white/5 rounded-[36px] flex items-end shadow-2xl focus-within:ring-2 focus-within:ring-[#00A3FF]/30 transition-all backdrop-blur-2xl">
        <textarea
          bind:value={userInput}
          onkeydown={handleKeyDown}
          placeholder="Tư vấn với chuyên gia AI..."
          class="block w-full bg-transparent border-0 py-[20px] pl-[26px] pr-18 text-white placeholder-gray-500 focus:ring-0 resize-none outline-none text-[17px] max-h-[160px] rounded-[36px] font-medium"
          style="min-height: 64px;"
          disabled={supportAgent.isTyping}
        ></textarea>
        
        <button 
          onclick={handleSend}
          disabled={!userInput.trim() || supportAgent.isTyping}
          class="absolute right-2 bottom-2 w-[52px] h-[52px] flex items-center justify-center rounded-full {userInput.trim() && !supportAgent.isTyping ? 'bg-[#00A3FF] text-white shadow-[0_6px_20px_rgba(0,163,255,0.4)] scale-100' : 'bg-white/5 text-gray-700 scale-95'} transition-all duration-300"
        >
          <Send size={22} class={userInput.trim() && !supportAgent.isTyping ? 'translate-x-[1px]' : ''} />
        </button>
      </div>

    </div>
  </div>
{/if}

<style>
  .apple-glass-dark-mobile {
    background: linear-gradient(165deg, rgba(8, 12, 21, 0.75) 0%, rgba(2, 4, 10, 0.98) 100%);
    backdrop-filter: blur(80px) saturate(210%);
    -webkit-backdrop-filter: blur(80px) saturate(210%);
    box-shadow: 
      0 -32px 100px rgba(0,0,0,0.7),
      inset 0 1px 1px rgba(255, 255, 255, 0.08),
      inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  }

  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .hide-scrollbar {
    -ms-overflow-style: none;  
    scrollbar-width: none;  
    scroll-behavior: smooth;
  }
  
  .safe-area-bottom {
    padding-bottom: env(safe-area-inset-bottom, 24px);
  }
</style>
