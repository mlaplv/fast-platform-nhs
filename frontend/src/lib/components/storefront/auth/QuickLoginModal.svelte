<script lang="ts">
  import AuthForm from '$lib/components/storefront/auth/AuthForm.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { X } from 'lucide-svelte';
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';

  const ui = getClientUi();
  let mode = $derived(ui.authModal.mode);
</script>

<!-- Standardized Modal/Sheet (Sync with Cart System) -->
<div class="fixed inset-0 z-[var(--z-modal-overlay)] flex items-end md:items-center justify-center bg-black/60 backdrop-blur-md p-0 md:p-6" 
     in:fade={{ duration: 300 }}
     onclick={(e) => e.target === e.currentTarget && ui.closeModal()}>
  
  <div class="bg-white w-full max-w-lg md:max-w-6xl md:h-[700px] rounded-t-[24px] md:rounded-none shadow-[0_-8px_40px_rgba(0,0,0,0.2)] md:shadow-[0_40px_100px_rgba(0,0,0,0.5)] overflow-hidden relative flex flex-col md:grid md:grid-cols-[1.2fr_1fr] max-h-[92vh] md:max-h-[85vh]"
       in:fly={{ y: '100%', duration: 600, easing: cubicOut }}>
    
    <!-- Left Pane: Branded Visual (Desktop Only) -->
    <div class="hidden md:flex relative flex-col justify-end p-16 overflow-hidden bg-[#0f172a]">
        <img 
            src="/home/lv/.gemini/antigravity/brain/9ea17a17-8f07-46fd-b120-9823cc68a3a5/micsmo_login_visual_1776681550776.png" 
            alt="Micsmo Branding" 
            class="absolute inset-0 w-full h-full object-cover opacity-60 scale-110 hover:scale-100 transition-transform duration-[10s]"
        />
        <div class="absolute inset-0 bg-gradient-to-t from-[#0f172a] via-transparent to-transparent"></div>
        
        <div class="relative z-10 space-y-4">
            <div class="w-16 h-1 w-1 bg-[#C18F7E]"></div>
            <h1 class="text-6xl font-black text-white tracking-tighter uppercase italic leading-none">
                Micsmo.com<br/>
                <span class="text-[#C18F7E]">2026 Elite</span>
            </h1>
            <p class="text-[12px] font-black text-white/50 uppercase tracking-[0.4em] pt-4">
                Hành trình tối ưu làn da Việt
            </p>
        </div>
    </div>

    <!-- Right Pane: Functional Form Area -->
    <div class="flex flex-col relative h-full bg-white">
        <!-- Close Button (Standard System Style) -->
        <button onclick={() => ui.closeModal()} class="absolute right-2 top-2 md:right-6 md:top-6 w-12 h-12 flex items-center justify-center text-gray-400 hover:text-black transition-all active:scale-95 z-20">
          <X class="w-7 h-7 md:w-8 md:h-8" strokeWidth={1.5} />
        </button>

        <!-- Grab Handle (Mobile Only) -->
        <div class="w-full h-8 flex items-center justify-center shrink-0 md:hidden touch-none">
          <div class="w-12 h-1.5 bg-gray-200 rounded-full"></div>
        </div>

        <!-- Header Section (Standardized Topology) -->
        <div class="relative flex items-center justify-center md:justify-start px-8 pt-2 pb-6 md:pt-20 md:px-14 border-b border-gray-50 md:border-none shrink-0 text-center md:text-left">
          <h2 class="text-[14px] md:text-5xl font-black text-black tracking-[0.3em] md:tracking-tighter uppercase italic leading-none">
            {mode === 'login' ? 'TRUY CẬP' : (mode === 'register' ? 'GIA NHẬP' : 'TÀI KHOẢN')}
            <span class="block md:inline text-[#C18F7E] md:ml-1">ELITE</span>
          </h2>
        </div>

        <!-- Form Content Area -->
        <div class="flex-1 overflow-y-auto overscroll-contain px-0 md:px-4 pb-safe custom-scrollbar">
          <AuthForm onClose={() => ui.closeModal()} />
        </div>
    </div>
  </div>
</div>

<style>
  /* Elite 2026: Hide scrollbar for auth form inside bottom sheet */
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  
  .pb-safe {
    padding-bottom: calc(env(safe-area-inset-bottom, 20px) + 20px);
  }
</style>
