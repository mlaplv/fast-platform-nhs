<script lang="ts">
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';
  import { Sparkles, ScanSearch, ShoppingCart, CreditCard, Home, PackageSearch } from 'lucide-svelte';
  import HelenIcon from './HelenIcon.svelte';
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { page } from '$app/state';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { SUPPORT_AGENT_UI } from '$lib/core/constants/support_agent_config';

  const { isMobile = false } = $props<{ isMobile?: boolean }>();

  let isScrolled = $state(false);

  // Elite V2.2: Contextual UI Mapping
  const contextUI = $derived.by(() => {
    switch (supportAgent.currentContext) {
      case 'home':
        return { color: '#00A3FF', icon: Home, label: 'Khám phá SmartShop' };
      case 'product':
        return { color: '#8B5CF6', icon: PackageSearch, label: 'Tư vấn sản phẩm' };
      case 'cart':
        return { color: '#10B981', icon: ShoppingCart, label: 'Kiểm tra giỏ hàng' };
      case 'checkout':
        return { color: '#F59E0B', icon: CreditCard, label: 'Hỗ trợ thanh toán' };
      default:
        return { color: '#00A3FF', icon: HelenIcon, label: 'Trợ giúp AI' };
    }
  });

  function toggleAgent() {
    supportAgent.vibrate(15);
    supportAgent.toggle();
  }

  function scrollToDiagnostics() {
    supportAgent.vibrate(10);
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

  // Elite V2.2: Sync path with state
  $effect(() => {
    if (page?.url?.pathname) {
      supportAgent.setPath(page.url.pathname);
    }
  });

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
    class="diagnostic-mini-fab fixed flex items-center justify-center transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] group"
    style="
      --theme-color: {contextUI.color};
      z-index: {Z_INDEX_CLIENT.FAB};
      bottom: {isScrolled ? 'calc(' + (isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_BOTTOM : SUPPORT_AGENT_UI.DESKTOP_FAB_BOTTOM) + ' + 60px)' : 'calc(' + (isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_BOTTOM : SUPPORT_AGENT_UI.DESKTOP_FAB_BOTTOM) + ' + 80px)'};
      right: {isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_RIGHT : SUPPORT_AGENT_UI.DESKTOP_FAB_RIGHT};
      width: 44px;
      height: 44px;
      opacity: {isScrolled ? '1' : '0'};
      transform: {isScrolled ? 'scale(1) translateY(0)' : 'scale(0.5) translateY(40px)'};
      pointer-events: {isScrolled ? 'auto' : 'none'};
      filter: blur({isScrolled ? '0' : '10px'});
    "
    onclick={scrollToDiagnostics}
    aria-label="Chẩn đoán nhanh"
    title="Chẩn đoán nhanh"
  >
    <div class="absolute inset-0 rounded-full bg-[var(--theme-color)] blur-[15px] opacity-20 group-hover:opacity-40 transition-opacity"></div>
    <div class="relative w-full h-full rounded-full flex items-center justify-center bg-black/40 backdrop-blur-xl border border-white/10 shadow-lg hover:border-[var(--theme-color)]/60 hover:bg-black/60 transition-all active:scale-90 group">
      <ScanSearch size={20} class="text-[var(--theme-color)] group-hover:scale-110 transition-transform" />
    </div>
    
    <!-- Mini Tooltip on Hover -->
    <div class="absolute right-full mr-4 px-3 py-1.5 bg-black/80 backdrop-blur-md rounded-lg text-[11px] font-bold text-white uppercase tracking-widest opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0 transition-all pointer-events-none whitespace-nowrap border border-white/5 shadow-xl">
      System health
    </div>
  </button>
{/if}

<button
  id="support-agent-fab"
  class="agent-fab flex items-center justify-center transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] 
    {supportAgent.isOpen ? 'rotate-[135deg] scale-75 opacity-0 pointer-events-none' : 'rotate-0 opacity-100'}
    {supportAgent.aiPulse ? 'neural-pulse-active' : ''}"
  style="
    --theme-color: {contextUI.color};
    z-index: {Z_INDEX_CLIENT.FAB};
    bottom: {isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_BOTTOM : SUPPORT_AGENT_UI.DESKTOP_FAB_BOTTOM};
    right: {isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_RIGHT : SUPPORT_AGENT_UI.DESKTOP_FAB_RIGHT};
    width: {isScrolled ? (isMobile ? '40px' : '48px') : (isMobile ? '56px' : '64px')};
    height: {isScrolled ? (isMobile ? '40px' : '48px') : (isMobile ? '56px' : '64px')};
    transform: {isScrolled ? 'translateY(8px)' : 'translateY(0)'};
    opacity: {isScrolled ? '0.8' : '1'};
  "
  onclick={toggleAgent}
  aria-label={contextUI.label}
>
  <!-- Stealth Glow: Viral Liquid Aura -->
  <div 
    class="absolute inset-[-15px] rounded-full blur-[30px] transition-all duration-1000"
    style="
      background: radial-gradient(circle, var(--theme-color) 0%, transparent 70%);
      opacity: {supportAgent.aiPulse ? '0.4' : (isScrolled ? '0.05' : '0.2')};
      transform: scale({supportAgent.aiPulse ? '1.5' : '1'});
    "
  ></div>
  
  <!-- Dark Liquid Drop Structure -->
  <div class="relative w-full h-full rounded-[40%] flex items-center justify-center overflow-hidden apple-glass-dark-drop transition-all duration-500 {isScrolled ? 'hover:scale-110' : 'hover:scale-105'} active:scale-90 group shadow-2xl">
    <!-- Fluid morphing gradient background for Dark Mode -->
    <div 
      class="absolute inset-0 transition-colors duration-1000 saturate-200"
      style="background: linear-gradient(135deg, #000000 0%, #0f172a 50%, var(--theme-color) 150%);"
    ></div>
    
    <!-- Caustic highlight (Glass reflection) -->
    <div class="absolute top-0 left-0 right-0 h-[50%] bg-gradient-to-b from-white/20 to-transparent rounded-t-[40%]"></div>
    
    <!-- Inner shadow edge & High-end stroke -->
    <div class="absolute inset-0 rounded-[40%] shadow-[inset_0_-4px_12px_rgba(0,0,0,0.5),inset_0_1px_2px_rgba(255,255,255,0.25)] border border-white/10 group-hover:border-white/20 transition-colors"></div>

    <!-- Liquid Ripple Effect on Hover -->
    <div class="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors duration-500"></div>

    <!-- Iconography -->
    <svelte:component 
      this={contextUI.icon}
      size={isScrolled ? (isMobile ? 18 : 22) : (isMobile ? 26 : 32)} 
      class="relative z-10 transition-all duration-700 group-hover:rotate-12 group-active:scale-110" 
      style="
        color: var(--theme-color);
        filter: drop-shadow(0 0 12px var(--theme-color));
      "
      strokeWidth={isScrolled ? 2 : 1.5} 
    />
  </div>

  {#if !supportAgent.isOpen && supportAgent.messages.length <= 1 && !isMobile && !isScrolled}
    <div 
      class="absolute right-[calc(100%+24px)] whitespace-nowrap bg-black/60 backdrop-blur-xl shadow-[0_12px_40px_rgba(0,0,0,0.6),inset_0_1px_1px_rgba(255,255,255,0.1)] border border-white/10 text-gray-200 px-6 py-3.5 rounded-full font-semibold text-[14px] tracking-tight tooltip-float flex items-center gap-3 transition-all animate-in fade-in slide-in-from-right-8"
    >
      <div class="relative flex h-2.5 w-2.5">
        <span 
          class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
          style="background-color: var(--theme-color);"
        ></span>
        <span 
          class="relative inline-flex rounded-full h-2.5 w-2.5 shadow-[0_0_8px_var(--theme-color)]"
          style="background-color: var(--theme-color);"
        ></span>
      </div>
      <span class="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
        {supportAgent.helenEnabled ? contextUI.label : 'Nhân viên đang trực tuyến'}
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
      0 4px 16px rgba(0, 0, 0, 0.2);
    border-radius: 45% 55% 45% 55% / 55% 45% 55% 45%;
    animation: morphDrop 8s ease-in-out infinite alternate;
  }

  @keyframes morphDrop {
    0% { border-radius: 40% 60% 50% 50% / 40% 50% 60% 50%; }
    50% { border-radius: 55% 45% 55% 45% / 45% 55% 45% 55%; }
    100% { border-radius: 50% 40% 60% 40% / 60% 40% 50% 60%; }
  }

  .neural-pulse-active {
    animation: neuralPulseShake 0.5s cubic-bezier(.36,.07,.19,.97) both;
  }

  @keyframes neuralPulseShake {
    10%, 90% { transform: translate3d(-1px, 0, 0); }
    20%, 80% { transform: translate3d(2px, 0, 0); }
    30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
    40%, 60% { transform: translate3d(4px, 0, 0); }
  }

  .tooltip-float {
    animation: airyFloat 6s ease-in-out infinite;
  }

  @keyframes airyFloat {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
  }
</style>
