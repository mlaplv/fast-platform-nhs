<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import Tag from "@lucide/svelte/icons/tag";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { spring } from 'svelte/motion';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';

  const shopStore = getShopStore();

  let { themeMode, applyTheme, scrollToQuiz, activeId = null } = $props<{
    themeMode: 'system' | 'light' | 'dark';
    applyTheme: (mode: 'system' | 'light' | 'dark') => void;
    scrollToQuiz?: () => void;
    activeId?: string | null;
  }>();

  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);

  const navLabels = $derived({
    hero: product?.metadata?.nav_label_home || 'Trang chủ',
    diagnostics: product?.metadata?.nav_label_diagnostics || 'Chẩn đoán',
    science: product?.metadata?.nav_label_science || 'Cơ chế',

    reviews: product?.metadata?.nav_label_reviews || 'Đánh giá',
    offers: product?.metadata?.nav_label_offers || 'Ưu đãi'
  });

  const navLinks = $derived([
    { id: 'hero', label: navLabels['hero'], href: '#hero', icon: Sparkles },
    { id: 'diagnostics', label: navLabels['diagnostics'], href: '#diagnostics' },
    { id: 'science', label: navLabels['science'], href: '#science' },

    { id: 'reviews', label: navLabels['reviews'], href: '#reviews' },
    { id: 'offers', label: navLabels['offers'], href: '#offers', icon: Tag }
  ]);

  let scrolled = $state(false);
  let hoverId = $state<string | null>(null);
  
  // Elite V2.2: Advanced Sliding Logic
  let navElements = $state<Record<string, HTMLElement>>({});
  const highlighterPos = spring({ left: 0, width: 0 }, { stiffness: 0.08, damping: 0.4 });

  const updateHighlighter = (id: string | null) => {
    if (!id || !navElements[id]) return;
    const el = navElements[id];
    highlighterPos.set({
      left: el.offsetLeft,
      width: el.offsetWidth
    });
  };

  $effect(() => {
    const target = hoverId || activeId;
    if (browser && target) {
      updateHighlighter(target);
    }
  });

  onMount(() => {
    if (browser) {
      const handleScroll = () => { scrolled = window.scrollY > 50; };
      window.addEventListener('scroll', handleScroll, { passive: true });
      handleScroll();
      // Initial pos
      setTimeout(() => updateHighlighter(activeId), 100);
      return () => window.removeEventListener('scroll', handleScroll);
    }
  });

  const headerClass = $derived(`liquid-header-wrapper ${scrolled ? 'is-collapsed' : 'is-expanded'}`);
</script>

<div class={headerClass}>
  <nav class="fluid-island-container">
    <div class="liquid-island bg-[#0A0A0A]/70 backdrop-blur-[30px] border border-white/10 rounded-full shadow-[0_20px_50px_rgba(0,0,0,0.6)] relative overflow-hidden">
      
      <!-- Premium Glass Refraction Glare (Viral Animation) -->
      <div class="liquid-glare absolute inset-0 pointer-events-none opacity-20 bg-gradient-to-r from-transparent via-white to-transparent -translate-x-full animate-shine"></div>

      <!-- Sliding Highlighter (The "Liquid" Core) -->
      {#if $highlighterPos.width > 0}
        <div 
          class="sliding-highlighter absolute top-1.5 bottom-1.5 rounded-full bg-white/10 border border-white/10 shadow-[0_0_30px_rgba(255,255,255,0.1)] z-0"
          style:left="{$highlighterPos.left}px"
          style:width="{$highlighterPos.width}px"
        >
          <!-- Internal Glow Edge (Liquid Light) -->
          <div class="absolute inset-x-4 top-0 h-[1px] bg-gradient-to-r from-transparent via-white/40 to-transparent"></div>
          <!-- Bottom Indicator Bar (Sleek replacement for the dot) -->
          <div class="absolute inset-x-1/2 -translate-x-1/2 bottom-[2px] w-6 h-[1.5px] bg-white rounded-full shadow-[0_0_12px_white]"></div>
        </div>
      {/if}

      <div class="island-content relative z-10 px-2 py-1.5 flex items-center gap-0.5">
        {#each navLinks as link}
          <a
            href={link.href}
            bind:this={navElements[link.id]}
            class="island-link relative flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-300 {activeId === link.id ? 'is-active text-white' : 'text-white/40 hover:text-white/80'}"
            onmouseenter={() => hoverId = link.id}
            onmouseleave={() => hoverId = null}
            onclick={(e) => {
              if (link.href.startsWith('#')) {
                e.preventDefault();
                document.getElementById(link.id)?.scrollIntoView({ behavior: 'smooth' });
              }
            }}
          >
            {#if link.icon}
               <link.icon class="w-3.5 h-3.5 transition-transform duration-500 {activeId === link.id ? 'scale-110' : 'opacity-60'}" />
            {/if}
            
             <span class="text-[10px] md:text-[11px] font-bold uppercase tracking-[0.2em] whitespace-nowrap">
                <EditableWrapper path={`metadata.nav_label_${link.id === 'hero' ? 'home' : link.id}`} type="text" label="SỬA ĐIỀU HƯỚNG" as="span">
                  {link.label}
                </EditableWrapper>
             </span>
            
            {#if activeId === link.id}
               <!-- Elite V2.2: Removed the ugly dot, using highlighter glow instead -->
            {/if}
          </a>
        {/each}
      </div>
    </div>
  </nav>
</div>

<style>
  .liquid-header-wrapper {
    position: fixed;
    top: 2rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: var(--z-header);
    transition: all 0.8s cubic-bezier(0.23, 1, 0.32, 1);
    pointer-events: none;
  }

  .liquid-header-wrapper.is-collapsed {
    top: 1.25rem;
    transform: translateX(-50%) scale(0.9);
  }

  .fluid-island-container {
    position: relative;
    pointer-events: auto;
  }

  .liquid-island {
    transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .island-link {
    text-shadow: 0 0 20px rgba(0,0,0,0.5);
  }

  /* PREMIUM SHINE ANIMATION */
  @keyframes shine {
    0% { transform: translateX(-150%) skewX(-30deg); }
    30% { transform: translateX(150%) skewX(-30deg); }
    100% { transform: translateX(150%) skewX(-30deg); }
  }

  .animate-shine {
    animation: shine 8s infinite ease-in-out;
  }

  .liquid-island:hover {
     border-color: rgba(255, 255, 255, 0.15);
     box-shadow: 0 30px 100px rgba(0,0,0,0.7);
     transform: translateY(-1px);
  }

  @media (max-width: 1024px) {
    .liquid-header-wrapper {
       width: 95%;
       max-width: fit-content;
    }
  }

  /* Tablet Refinement (768px - 1024px): Keep labels but compact */
  @media (min-width: 768px) and (max-width: 1024px) {
    .island-content {
       gap: 0.15rem;
       padding: 0.35rem;
    }
    .island-link {
       padding-left: 0.65rem;
       padding-right: 0.65rem;
    }
    .island-link span {
       font-size: 9px !important;
       letter-spacing: 0.1em !important;
    }
  }

  /* Mobile Only: Hide labels to save space */
  @media (max-width: 767px) {
    .island-content {
       gap: 0.1rem;
       padding: 0.4rem;
    }
    .island-link {
       padding-left: 0.75rem;
       padding-right: 0.75rem;
    }
    .island-link span {
       display: none;
    }
    .island-link.is-active span {
       display: inline-block;
       font-size: 9px;
    }
  }

  @media (max-width: 480px) {
     .liquid-header-wrapper.is-collapsed {
        transform: translateX(-50%) scale(0.85);
     }
  }
</style>
