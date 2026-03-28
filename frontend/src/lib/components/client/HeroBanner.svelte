<script lang="ts">
  import { onMount } from 'svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { browser } from '$app/environment';
  import type { Product } from '$lib/types';
  import LiquidHeader from './LiquidHeader.svelte';
  import "./HeroBanner.css";
  
  interface HeroBannerProps {
    product: GenericProduct;
    scrollToQuiz?: () => void;
  }

  // Senior Architect Note: Use a more flexible type for initial props while maintaining strict safety
  type GenericProduct = Partial<Product> & {
    attributes?: {
      hero_headline?: string;
      absorption_value?: string;
      efficiency_value?: string;
      origin_value?: string;
      [key: string]: unknown;
    };
  };

  let { product, scrollToQuiz }: HeroBannerProps = $props();
  let themeMode = $state<'system' | 'light' | 'dark'>('system');
  let mouse = $state({ x: 0, y: 0 });

  const handleMouseMove = (e: MouseEvent) => {
    if (!browser) return;
    mouse.x = (e.clientX / window.innerWidth - 0.5) * 30;
    mouse.y = (e.clientY / window.innerHeight - 0.5) * 30;
  };

  const productName: string = $derived(product?.name ?? 'Elite Formulation');
  const mainImage: string = $derived(resolveMediaUrl(product?.images?.[0] ?? ''));
  const rawHeadline: string = $derived((product?.attributes?.hero_headline as string) ?? 'CHẤM DỨT <br/> MÙI CƠ THỂ.');
  
  let displayText = $state<string>("");
  let isTypingComplete = $state<boolean>(false);

  const typeWriter = async (signal: AbortSignal): Promise<void> => {
    if (!browser) return;
    const parts = rawHeadline.split(/(<br\s*\/?>)/i);
    let currentText = "";
    
    // Initial delay for cinematic effect
    await new Promise(r => setTimeout(r, 800));
    if (signal.aborted) return;

    for (const part of parts) {
      if (part.toLowerCase().startsWith("<br")) {
        currentText += part;
        displayText = currentText;
      } else {
        for (const char of part) {
          if (signal.aborted) return;
          currentText += char;
          displayText = currentText;
          // Slower, more deliberate typing speed
          const delay = char === '.' || char === ',' ? 500 : 150 + Math.random() * 100;
          await new Promise(r => setTimeout(r, delay));
        }
      }
    }
    isTypingComplete = true;
  };

  const updateDOM = (theme: 'light' | 'dark') => {
    if (!browser) return;
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
  };

  const applyTheme = (mode: 'system' | 'light' | 'dark') => {
    themeMode = mode;
    if (!browser) return;
    localStorage.setItem('hero-theme-mode', mode);
    if (mode === 'system') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      updateDOM(isDark ? 'dark' : 'light');
    } else {
      updateDOM(mode as 'light' | 'dark');
    }
  };

  onMount(() => {
    if (browser) {
      const controller = new AbortController();
      typeWriter(controller.signal);

      const savedTheme = localStorage.getItem('hero-theme-mode');
      const validTheme = (savedTheme === 'light' || savedTheme === 'dark' || savedTheme === 'system') ? savedTheme : 'system';
      applyTheme(validTheme);
      
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      const h = (e: MediaQueryListEvent): void => {
        if (themeMode === 'system') updateDOM(e.matches ? 'dark' : 'light');
      };
      
      mq.addEventListener('change', h);
      return () => {
        controller.abort();
        mq.removeEventListener('change', h);
      };
    }
  });

  const scrollToCare = () => {
    if (!browser) return;
    const element = document.getElementById('personalized-care');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };
</script>

<section
  id="hero"
  role="region"
  aria-label="Hero Spotlight Area"
  class="hero-center-layout content-hero snap-session relative w-full overflow-hidden flex flex-col items-center justify-start bg-[#020617] text-white"
  onmousemove={handleMouseMove}
  style="--mx: {mouse.x}px; --my: {mouse.y}px; --hero-accent: #3b82f6; --hero-glass-blur: 32px;"
>
  <LiquidHeader {themeMode} {applyTheme} scrollToQuiz={scrollToCare} />


  <!-- NUCLEAR VIDEO BACKGROUND (Standard Full Coverage: 100% Native) -->
  <div class="absolute inset-x-0 top-0 bottom-0 z-0 overflow-hidden pointer-events-none w-full h-full">
    <div class="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-[#020617] to-transparent w-full" style:z-index="var(--z-surface)"></div>
    <video autoplay muted loop playsinline class="elite-video-bg">
      <source src="/video/video-hn.mp4" type="video/mp4" />
    </video>
  </div>

  <div class="container relative flex flex-col items-center pt-[clamp(1.5rem,5vh,3.5rem)] px-6" style:z-index="var(--z-surface)">

    <h1 class="typing-headline text-center w-full max-w-4xl lg:max-w-7xl font-black mb-6 mt-0">
       {@html displayText}
       {#if !isTypingComplete}
          <span class="typing-cursor">|</span>
       {/if}
    </h1>

    {#if product?.shortDescription}
       <p class="hero-description outline-none">
          {@html product.shortDescription}
       </p>
    {/if}

    <div class="hero-product-display relative w-full max-w-6xl py-8 md:py-12 flex items-center justify-center">
       <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
       </div>
    <div class="relative flex flex-col lg:flex-row items-center justify-center gap-12 lg:gap-16 w-full px-4 lg:px-12" style:z-index="var(--z-surface)">
          
          <div class="relative float-anim parallax-layer">
             <!-- FLASH LIGHT BEAM (Cinematic Highlight - Locked to Product Left Edge) -->
             <div class="flashlight-beam hidden lg:block"></div>

             <div class="elite-product-card relative hud-frame">
                
                <div class="product-glass-container flex items-center justify-center overflow-hidden rounded-[3.5rem] aspect-square w-64 md:w-80 lg:w-96">
                   <img src="{mainImage}" alt="{productName}" class="w-full h-full object-cover image-rim-light" />
                </div>
                
                <!-- NEW: Mist Spray originating from the RIGHT EDGE of the product -->
                <div class="mist-container absolute top-1/2 -right-4 -translate-y-1/2 pointer-events-none hidden lg:block" style:z-index="var(--z-surface)">
                   {#each Array(20) as _, i}
                      <div class="mist-particle" style="--p-idx: {i};"></div>
                   {/each}
                </div>
                
                <!-- SCANNING LINE -->
                <div class="absolute inset-x-0 h-[1px] bg-blue-400/20 shadow-[0_0_15px_rgba(96,165,250,0.5)] scan-anim pointer-events-none"></div>
             </div>
          </div>

          <div id="products" class="metrics-arc-container relative">
             {#each [
                { label: 'Absorption', value: product?.attributes?.absorption_value || 'XUẤT THẤU 3s', color: 'blue' },
                { label: 'Efficiency', value: product?.attributes?.efficiency_value || '48H KHÔ THOÁNG', color: 'indigo' },
                { label: 'Origin', value: product?.attributes?.origin_value || 'THẢO DƯỢC 100%', color: 'emerald' }
             ] as metric, i}
                <div class="arc-item group flex flex-col" style="--idx: {i}">
                   <div class="flex items-center gap-4 mb-2">
                      <div class="metric-dot bg-{metric.color}-500 shadow-[0_0_15px_rgba(var(--{metric.color}-rgb),1)]"></div>
                      <span class="text-[10px] font-black text-{metric.color}-500 uppercase tracking-[0.25em] drop-shadow-sm">{metric.label}</span>
                   </div>
                   <span class="metric-value transform group-hover:scale-110 transition-transform">{metric.value}</span>
                </div>
             {/each}
          </div>
       </div>
    </div>

    <!-- PREMIUM CTA BUTTON -->
    <button class="hero-cta-button" onclick={scrollToCare}>
       <div class="cta-gradient-overlay"></div>
       <div class="cta-content">
          <div class="cta-status-dot"></div>
          <span class="cta-text">Personalized Care AI</span>
          <svg class="cta-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
       </div>
       <div class="cta-shimmer"></div>
    </button>

    <!-- MOUSE SCROLL INDICATOR -->
    <a href="#personalized-care" class="mouse-scroll-indicator" aria-label="Scroll to diagnostics section" onclick={(e) => { e.preventDefault(); scrollToCare(); }}>
       <div class="mouse-body">
          <div class="mouse-wheel"></div>
       </div>
    </a>
  </div>
</section>

