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
        return { color: '#FFB7C5', icon: HelenIcon, label: 'Trợ giúp AI' };
      case 'product':
        return { color: '#FFB7C5', icon: HelenIcon, label: 'Tư vấn sản phẩm' };
      case 'cart':
        return { color: '#FFB7C5', icon: HelenIcon, label: 'Kiểm tra giỏ hàng' };
      case 'checkout':
        return { color: '#E8D5B0', icon: HelenIcon, label: 'Hỗ trợ thanh toán' };
      default:
        return { color: '#FFB7C5', icon: HelenIcon, label: 'Trợ giúp AI' };
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
  class="agent-fab hidden md:flex items-center justify-center transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] 
    {supportAgent.isOpen ? 'rotate-[135deg] scale-75 opacity-0 pointer-events-none' : 'rotate-0 opacity-100 !important'}
    {supportAgent.aiPulse ? 'neural-pulse-active' : ''}"
  style="
    --theme-color: {contextUI.color};
    z-index: {Z_INDEX_CLIENT.FAB};
    bottom: {isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_BOTTOM : SUPPORT_AGENT_UI.DESKTOP_FAB_BOTTOM};
    right: {isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_RIGHT : SUPPORT_AGENT_UI.DESKTOP_FAB_RIGHT};
    width: {isScrolled ? (isMobile ? '40px' : '48px') : (isMobile ? '56px' : '64px')};
    height: {isScrolled ? (isMobile ? '40px' : '48px') : (isMobile ? '56px' : '64px')};
    transform: {isScrolled ? 'translateY(8px)' : 'translateY(0)'};
    opacity: {supportAgent.isOpen ? '0' : '1 !important'};
  "
  onclick={toggleAgent}
  aria-label={contextUI.label}
>
  <!-- Stealth Glow: Viral Liquid Aura -->
  <div 
    class="absolute inset-[-15px] rounded-full blur-[30px] transition-all duration-1000"
    style="
      background: radial-gradient(circle, var(--theme-color) 0%, transparent 70%);
      opacity: {supportAgent.aiPulse ? '0.2' : (isScrolled ? '0.02' : '0.1')};
      transform: scale({supportAgent.aiPulse ? '1.5' : '1'});
    "
  ></div>
  
  <!-- Dark Liquid Drop Structure -->
  <div class="relative w-full h-full rounded-[40%] flex items-center justify-center overflow-hidden apple-glass-dark-drop transition-all duration-500 {isScrolled ? 'hover:scale-110' : 'hover:scale-105'} active:scale-90 group shadow-2xl">
    <!-- Fluid morphing gradient background for Dark Mode -->
    <div 
      class="absolute inset-0 transition-colors duration-1000 saturate-200"
      style="background: linear-gradient(135deg, #000000 0%, #1e111a 50%, var(--theme-color) 150%);"
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
      color={contextUI.color}
      strokeWidth={contextUI.icon !== HelenIcon ? (isScrolled ? 2 : 1.5) : undefined} 
    />
  </div>

  {#if !supportAgent.isOpen && supportAgent.messages.length <= 1 && !isMobile && !isScrolled}
    <div 
      class="absolute right-[calc(100%+24px)] elite-status-pill tooltip-float flex items-center gap-3 transition-all animate-in fade-in slide-in-from-right-8"
      style="--status-color: var(--theme-color);"
    >
      <div class="elite-dot-container">
        <span class="elite-status-dot"></span>
      </div>
      <span class="elite-status-text">
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
    animation: helen-orb-morph 8s ease-in-out infinite alternate;
  }

  @keyframes helen-orb-morph {
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
