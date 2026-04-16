<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { ShieldCheck, Tag, Sparkles } from 'lucide-svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { fade, fly, scale } from 'svelte/transition';
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
    'result-timeline': product?.metadata?.nav_label_transformation || 'Lột xác',
    reviews: product?.metadata?.nav_label_reviews || 'Đánh giá',
    offers: product?.metadata?.nav_label_offers || 'Ưu đãi'
  });

  const navLinks = $derived([
    { id: 'hero', label: navLabels['hero'], href: '#hero', icon: Sparkles },
    { id: 'diagnostics', label: navLabels['diagnostics'], href: '#diagnostics' },
    { id: 'science', label: navLabels['science'], href: '#science' },
    { id: 'result-timeline', label: navLabels['result-timeline'], href: '#result-timeline' },
    { id: 'reviews', label: navLabels['reviews'], href: '#reviews' },
    { id: 'offers', label: navLabels['offers'], href: '#offers', icon: Tag }
  ]);

  let scrolled = $state(false);
  let scrollY = $state(0);
  let hoverId = $state<string | null>(null);

  const handleScroll = () => {
    if (!browser) return;
    scrollY = window.scrollY;
    scrolled = scrollY > 50;
  };

  onMount(() => {
    if (browser) {
      window.addEventListener('scroll', handleScroll, { passive: true });
      handleScroll();
      return () => window.removeEventListener('scroll', handleScroll);
    }
  });

  const headerClass = $derived(`liquid-header-wrapper ${scrolled ? 'is-collapsed' : 'is-expanded'}`);
</script>

<div class={headerClass}>
  <div class="fluid-island-container">
    <!-- Viral 2026: Bokeh Background for the Island -->
    <div class="bokeh-layer absolute inset-0 overflow-hidden rounded-full pointer-events-none">
       <div class="bokeh-dot" style:left="{(navLinks.findIndex(l => l.id === (hoverId || activeId)) * 100) / navLinks.length}%"></div>
    </div>

    <div class="liquid-island bg-black/40 backdrop-blur-[40px] border border-white/5 rounded-full shadow-[0_30px_100px_rgba(0,0,0,0.8)] relative">
      <div class="island-content px-6 py-3 flex items-center justify-center gap-10 md:gap-14">
        {#each navLinks as link}
          <a
            href={link.href}
            class="island-link relative group flex items-center gap-2 transition-all duration-500 {activeId === link.id ? 'is-active' : 'text-white/40 hover:text-white'}"
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
               <link.icon class="w-3 h-3 opacity-60 group-hover:opacity-100 group-hover:scale-110 transition-all duration-500" />
            {/if}
            <span class="text-[9px] md:text-[10px] font-black uppercase tracking-[0.3em] font-outfit">
               <EditableWrapper path={`metadata.nav_label_${link.id === 'hero' ? 'home' : (link.id === 'result-timeline' ? 'transformation' : link.id)}`} type="text" label="SỬA ĐIỀU HƯỚNG" as="span">
                 {link.label}
               </EditableWrapper>
            </span>
            
            {#if activeId === link.id}
               <div class="active-indicator absolute -bottom-2 left-1/2 -translate-x-1/2 w-1 h-1 bg-luxury-gold rounded-full shadow-[0_0_10px_var(--luxury-gold)]" in:scale={{ duration: 600 }}></div>
            {/if}
          </a>
        {/each}
      </div>

      <!-- Refraction Lens Effect -->
      <div class="lens-glare absolute inset-0 rounded-full bg-gradient-to-tr from-white/5 via-transparent to-white/5 pointer-events-none opacity-50"></div>
    </div>
  </div>
</div>

<style>
  .liquid-header-wrapper {
    position: fixed;
    top: 2rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: var(--z-sticky-header);
    transition: all 0.8s cubic-bezier(0.23, 1, 0.32, 1);
    pointer-events: none;
  }

  .liquid-header-wrapper.is-collapsed {
    top: 1rem;
    transform: translateX(-50%) scale(0.95);
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

  .island-link.is-active {
    color: var(--luxury-gold);
    filter: drop-shadow(0 0 10px rgba(232, 213, 176, 0.3));
  }

  /* BOKEH EFFECT */
  .bokeh-layer {
     z-index: 0;
  }

  .bokeh-dot {
     position: absolute;
     top: 50%;
     transform: translateY(-50%);
     width: 100px;
     height: 40px;
     background: var(--luxury-copper);
     filter: blur(25px);
     opacity: 0.15;
     transition: all 0.8s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .liquid-island:hover {
     transform: translateY(-2px);
     border-color: rgba(193, 143, 126, 0.2);
     box-shadow: 0 40px 120px rgba(0,0,0,0.9);
  }

  @media (max-width: 768px) {
    .liquid-header-wrapper {
       width: 90%;
    }
    .island-content {
       gap: 1.25rem;
       padding: 0.75rem 1rem;
    }
    .island-link span {
       display: none; /* Icon only on small mobile to avoid cramped text */
    }
    .island-link.is-active span {
       display: inline-block; /* Show only active label */
       font-size: 8px;
    }
  }
</style>
