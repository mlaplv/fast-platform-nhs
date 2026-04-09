<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { ShieldCheck } from 'lucide-svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';

  const shopStore = getShopStore();

  // Senior Architect Note: LiquidHeader uses Svelte 5 Runes for ultra-responsive local state
  let { themeMode, applyTheme, scrollToQuiz } = $props<{
    themeMode: 'system' | 'light' | 'dark';
    applyTheme: (mode: 'system' | 'light' | 'dark') => void;
    scrollToQuiz?: () => void;
  }>();

  const product = $derived(shopStore.product);

  const labels = $derived({
    home: product?.metadata?.nav_label_home || 'Trang chủ',
    diagnostics: product?.metadata?.nav_label_diagnostics || 'Chẩn đoán',
    science: product?.metadata?.nav_label_science || 'Cơ chế',
    reviews: product?.metadata?.nav_label_reviews || 'Đánh giá',
    offers: product?.metadata?.nav_label_offers || 'Ưu đãi'
  });

  const navLinks = $derived([
    { id: 'hero', label: labels.home, href: '#hero' },
    { id: 'diagnostics', label: labels.diagnostics, href: '#diagnostics' },
    { id: 'science', label: labels.science, href: '#science' },
    { id: 'reviews', label: labels.reviews, href: '#reviews' },
    { id: 'offers', label: labels.offers, href: '#offers' },
    { id: 'track', label: 'Tra cứu!', href: '/track' }
  ]);

  let scrolled = $state(false);
  let scrollY = $state(0);
  let activeSection = $state('hero');

  const handleScroll = () => {
    if (!browser) return;
    scrollY = window.scrollY;
    scrolled = scrollY > 50;
  };

  onMount(() => {
    if (browser) {
      window.addEventListener('scroll', handleScroll, { passive: true });
      handleScroll(); // Initial check

      // IntersectionObserver for Active Section
      const observerOptions = {
        root: null,
        rootMargin: '-30% 0px -30% 0px', // Wider 40% band for robust snapping!
        threshold: 0
      };

      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            // Update active section when any part enters the large center band
            activeSection = entry.target.id;
          }
        });
      }, observerOptions);

      const sectionIds = navLinks.map(link => link.id);
      sectionIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) observer.observe(el);
      });

      return () => {
        window.removeEventListener('scroll', handleScroll);
        observer.disconnect();
      };
    }
  });

  const headerClass = $derived(`liquid-header-wrapper ${scrolled ? 'is-collapsed' : 'is-expanded'}`);
</script>

<div class={headerClass}>
  <div class="liquid-island bg-black/60 backdrop-blur-2xl border border-white/10 rounded-full shadow-2xl">
    <div class="island-content">
      <!-- NAVIGATION SECTOR (Centered & Aligned) -->
      <nav class="island-nav">
        {#each navLinks as link}
          <a
            href={link.href}
            class="island-link text-[10px] font-black uppercase tracking-[0.2em] transition-all hover:text-red-500 {activeSection === link.id ? 'text-red-500 scale-105' : 'text-white/80'}"
            onclick={(e) => {
              if (link.href.startsWith('#')) {
                e.preventDefault();
                document.getElementById(link.id)?.scrollIntoView({ behavior: 'smooth' });
              }
            }}
          >
            {#if link.id === 'track'}
              <ShieldCheck class="w-3 h-3 mr-1.5 inline-block opacity-70" />
            {/if}
            {link.label}
          </a>
        {/each}
      </nav>
    </div>

    <!-- LIQUID DECORATION (Dynamic Highlight) -->
    <div class="liquid-reflection absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none"></div>
  </div>
</div>

<style>
  /* Component-specific layout; Aesthetic tokens remain in HeroBanner.css */
  .liquid-header-wrapper {
    position: fixed;
    top: 1.25rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: var(--z-sticky-header);
    width: auto; /* Shrink to fit content */
    display: flex;
    justify-content: center;
    pointer-events: none;
    transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .liquid-header-wrapper.is-collapsed {
    top: 0.75rem;
  }

  .island-content {
    display: flex;
    align-items: center;
    justify-content: center;
    width: fit-content;
    min-width: min-content;
    height: 100%;
    padding: 0 1.25rem; /* Reduced horizontal padding to minimum */
    position: relative;
    z-index: 2;
  }

  .island-nav {
    display: flex;
    align-items: center;
    gap: 2rem; /* Increased gap for better spacing when centered */
    pointer-events: auto;
  }
</style>
