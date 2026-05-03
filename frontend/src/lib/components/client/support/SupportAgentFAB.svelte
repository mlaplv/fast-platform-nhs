<script lang="ts">
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';
  import { Sparkles, ShoppingCart, CreditCard, Home, PackageSearch } from 'lucide-svelte';
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


<!-- Elite V2.2: FAB Wrapper — fixed positioning hoisted to wrapper, pill is sibling of button -->
<div
  id="support-agent-fab-wrapper"
  class="agent-fab-wrapper hidden md:flex items-center gap-0"
  style="
    --theme-color: {contextUI.color};
    z-index: {Z_INDEX_CLIENT.FAB};
    bottom: {isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_BOTTOM : SUPPORT_AGENT_UI.DESKTOP_FAB_BOTTOM};
    right: {isMobile ? SUPPORT_AGENT_UI.MOBILE_FAB_RIGHT : SUPPORT_AGENT_UI.DESKTOP_FAB_RIGHT};
    transform: {isScrolled ? 'translateY(8px)' : 'translateY(0)'};
    transition: transform 0.7s cubic-bezier(0.16,1,0.3,1), opacity 0.7s cubic-bezier(0.16,1,0.3,1);
    opacity: {supportAgent.isOpen ? '0' : '1'};
    pointer-events: {supportAgent.isOpen ? 'none' : 'auto'};
  "
>
  <!-- FAB Button -->
  <button
    id="support-agent-fab"
    class="fab-btn relative flex items-center justify-center transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]
      {supportAgent.aiPulse ? 'neural-pulse-active' : ''}"
    style="
      width: {isScrolled ? (isMobile ? '40px' : '48px') : (isMobile ? '56px' : '64px')};
      height: {isScrolled ? (isMobile ? '40px' : '48px') : (isMobile ? '56px' : '64px')};
      flex-shrink: 0;
    "
    onclick={toggleAgent}
    aria-label={contextUI.label}
  >
    <!-- Stealth Glow: Viral Liquid Aura -->
    <div 
      class="absolute inset-[-15px] rounded-full blur-[30px] transition-all duration-1000 pointer-events-none"
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
  </button>
</div>

<style>
  /* Wrapper đảm nhận position:fixed thay cho button, tránh overflow-hidden clip pill */
  .agent-fab-wrapper {
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
