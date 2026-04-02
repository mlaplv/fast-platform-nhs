<script lang="ts">
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';
  import { Sparkles, ScanSearch } from 'lucide-svelte';
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  import { SUPPORT_AGENT_UI } from '$lib/core/constants/support_agent_config';

  const { isMobile = false } = $props<{ isMobile?: boolean }>();

  let isScrolled = $state(false);

  function toggleAgent() {
    supportAgent.toggle();
  }

  function scrollToDiagnostics() {
    const el = document.getElementById('diagnostics-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  }

  // Scroll detection for shrinking
  function handleScroll() {
    if (browser) {
      isScrolled = window.scrollY > SUPPORT_AGENT_UI.SCROLL_SHRINK_THRESHOLD;
    }
  }

  onMount(() => {
    if (browser) {
      window.addEventListener('scroll', handleScroll, { passive: true });
      handleScroll();
    }
  });

  onDestroy(() => {
    if (browser) window.removeEventListener('scroll', handleScroll);
  });
</script>

<!-- Diagnostic Quick Access Mini-FAB -->
{#if !supportAgent.isOpen}
  <button
    class="diagnostic-mini-fab fixed flex items-center justify-center transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] z-[100]"
    style="
      bottom: {isMobile ? '185px' : '95px'};
      right: {isMobile ? '28px' : '40px'};
      width: 44px;
      height: 44px;
      opacity: {isScrolled ? '1' : '0'};
      transform: {isScrolled ? 'scale(1)' : 'scale(0) rotate(-45deg)'};
      pointer-events: {isScrolled ? 'auto' : 'none'};
    "
    onclick={scrollToDiagnostics}
    aria-label="Chẩn đoán nhanh"
    title="Chẩn đoán nhanh"
  >
    <div class="absolute inset-0 rounded-full bg-[#00A3FF] blur-[15px] opacity-20"></div>
    <div class="relative w-full h-full rounded-full flex items-center justify-center bg-black/40 backdrop-blur-xl border border-white/10 shadow-lg hover:border-[#00A3FF]/40 hover:bg-black/60 transition-all active:scale-90 group">
      <ScanSearch size={20} class="text-[#00A3FF] group-hover:scale-110 transition-transform" />
    </div>
  </button>
{/if}

<button
  class="agent-fab flex items-center justify-center transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] 
    {supportAgent.isOpen ? 'rotate-[135deg] scale-75 opacity-0 pointer-events-none' : 'rotate-0 opacity-100'}"
  style="
    z-index: {Z_INDEX_CLIENT.FAB};
    bottom: {isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_BOTTOM : SUPPORT_AGENT_UI.DESKTOP_FAB_BOTTOM};
    right: {isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_RIGHT : SUPPORT_AGENT_UI.DESKTOP_FAB_RIGHT};
    width: {isScrolled ? (isMobile ? '40px' : '48px') : (isMobile ? '56px' : '64px')};
    height: {isScrolled ? (isMobile ? '40px' : '48px') : (isMobile ? '56px' : '64px')};
    transform: {isScrolled ? 'translateY(8px)' : 'translateY(0)'};
    opacity: {isScrolled ? '0.8' : '1'};
  "
  onclick={toggleAgent}
  aria-label="Mở hệ thống tư vấn AI"
>
  <!-- Stealth Glow: Viral Liquid Aura -->
  <div class="absolute inset-[-10px] rounded-[40%] bg-[#00A3FF] blur-[25px] {isScrolled ? 'opacity-5' : 'opacity-20'} animate-pulse-slow transition-opacity"></div>
  
  <!-- Dark Liquid Drop Structure -->
  <div class="relative w-full h-full rounded-[40%] flex items-center justify-center overflow-hidden apple-glass-dark-drop transition-all duration-500 {isScrolled ? 'hover:scale-110' : 'hover:scale-105'} active:scale-90 group shadow-2xl">
    <!-- Fluid morphing gradient background for Dark Mode -->
    <div class="absolute inset-0 bg-gradient-to-tr from-[#000000]/90 via-[#0f172a]/80 to-[#00284d]/90 backdrop-blur-[40px] saturate-200"></div>
    
    <!-- Caustic highlight (Glass reflection) -->
    <div class="absolute top-0 left-0 right-0 h-[50%] bg-gradient-to-b from-white/20 to-transparent rounded-t-[40%]"></div>
    
    <!-- Inner shadow edge & High-end stroke -->
    <div class="absolute inset-0 rounded-[40%] shadow-[inset_0_-4px_12px_rgba(0,163,255,0.15),inset_0_1px_2px_rgba(255,255,255,0.25)] border border-white/10 group-hover:border-white/20 transition-colors"></div>

    <!-- Liquid Ripple Effect on Hover -->
    <div class="absolute inset-0 bg-[#00A3FF]/0 group-hover:bg-[#00A3FF]/5 transition-colors duration-500"></div>

    <!-- Iconography -->
    <Sparkles 
      size={isScrolled ? (isMobile ? 18 : 22) : (isMobile ? 26 : 32)} 
      class="text-[#00A3FF] relative z-10 drop-shadow-[0_0_10px_rgba(0,163,255,0.6)] transition-all duration-500 group-hover:rotate-12 group-active:scale-110" 
      strokeWidth={isScrolled ? 2 : 1.5} 
    />
  </div>

  {#if !supportAgent.isOpen && supportAgent.messages.length <= 1 && !isMobile && !isScrolled}
    <div 
      class="absolute right-[calc(100%+24px)] whitespace-nowrap bg-black/60 backdrop-blur-xl shadow-[0_12px_40px_rgba(0,0,0,0.6),inset_0_1px_1px_rgba(255,255,255,0.1)] border border-white/10 text-gray-200 px-6 py-3.5 rounded-full font-semibold text-[14px] tracking-tight tooltip-float flex items-center gap-3 transition-all animate-in fade-in slide-in-from-right-4"
    >
      <div class="relative flex h-2.5 w-2.5">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00A3FF] opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#00A3FF] shadow-[0_0_8px_#00A3FF]"></span>
      </div>
      <span class="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
        {supportAgent.helenEnabled ? 'Chuyên gia AI đang trực tuyến' : 'Nhân viên đang trực tuyến'}
      </span>
    </div>
  {/if}
</button>

<style>
  .agent-fab {
    position: fixed;
  }

  .apple-glass-dark-drop {
    box-shadow: 
      0 16px 40px rgba(0, 0, 0, 0.5),
      0 4px 16px rgba(0, 163, 255, 0.15);
    border-radius: 45% 55% 45% 55% / 55% 45% 55% 45%;
    animation: morphDrop 8s ease-in-out infinite alternate;
  }

  @keyframes morphDrop {
    0% { border-radius: 40% 60% 50% 50% / 40% 50% 60% 50%; }
    50% { border-radius: 55% 45% 55% 45% / 45% 55% 45% 55%; }
    100% { border-radius: 50% 40% 60% 40% / 60% 40% 50% 60%; }
  }

  .animate-pulse-slow {
    animation: slowPulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes slowPulse {
    0%, 100% { transform: scale(1); opacity: 0.2; }
    50% { transform: scale(1.15); opacity: 0.3; }
  }

  .tooltip-float {
    animation: airyFloat 6s ease-in-out infinite;
  }

  @keyframes airyFloat {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
  }
</style>
