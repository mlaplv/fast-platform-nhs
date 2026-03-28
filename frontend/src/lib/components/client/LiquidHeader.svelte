<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  // Senior Architect Note: LiquidHeader uses Svelte 5 Runes for ultra-responsive local state
  let { themeMode, applyTheme, scrollToQuiz } = $props<{
    themeMode: 'system' | 'light' | 'dark';
    applyTheme: (mode: 'system' | 'light' | 'dark') => void;
    scrollToQuiz?: () => void;
  }>();

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
        rootMargin: '-20% 0px -70% 0px', // Adjust to trigger when section is mostly in view
        threshold: 0
      };

      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            activeSection = entry.target.id;
          }
        });
      }, observerOptions);

      const sectionIds = ['hero', 'diagnostics', 'science', 'reviews', 'offers'];
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
  <div class="liquid-island">
    <div class="island-content">
      <!-- NAVIGATION SECTOR (Centered & Aligned) -->
      <nav class="island-nav">
        {#each [
          { id: 'hero', label: 'Trang chủ', href: '#hero' },
          { id: 'diagnostics', label: 'Chẩn đoán', href: '#diagnostics' },
          { id: 'science', label: 'Cơ chế', href: '#science' },
          { id: 'reviews', label: 'Đánh giá', href: '#reviews' },
          { id: 'offers', label: 'Ưu đãi', href: '#offers' }
        ] as link}
          <a
            href={link.href}
            class="island-link {activeSection === link.id ? 'is-active' : ''}"
            onclick={(e) => {
              e.preventDefault();
              document.getElementById(link.id)?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            {link.label}
          </a>
        {/each}
      </nav>
    </div>
    
    <!-- LIQUID DECORATION (Dynamic Highlight) -->
    <div class="liquid-reflection"></div>
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
