<script lang="ts">
  import { onMount } from 'svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { browser } from '$app/environment';
  import LiquidHeader from './LiquidHeader.svelte';
  import "./HeroBanner.css";
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';

  const shopStore = getShopStore();

  interface HeroBannerProps {
    scrollToQuiz?: () => void;
  }

  let { scrollToQuiz }: HeroBannerProps = $props();
  const product = $derived(shopStore.product);
  const metadata = $derived(product?.metadata || {});
  let themeMode = $state<'system' | 'light' | 'dark'>('system');
  let mouse = $state({ x: 0, y: 0 });

  let currentImageIndex = $state(0);
  
  const handleMouseMove = (e: MouseEvent) => {
    if (!browser) return;
    mouse.x = (e.clientX / window.innerWidth - 0.5) * 30;
    mouse.y = (e.clientY / window.innerHeight - 0.5) * 30;
  };

  const nextImage = () => {
    if (images.length === 0) return;
    currentImageIndex = (currentImageIndex + 1) % images.length;
  };

  const prevImage = () => {
    if (images.length === 0) return;
    currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
  };

  const labels = $derived({
    product_name: product?.name || (metadata.hero_product_name_fallback as string) || 'Elite Formulation',
    headline: metadata.hero_headline || '<span>CHẤM DỨT</span> <br/> <span class="headline-shift">MÙI CƠ THỂ.</span>',
    video_url: metadata.hero_video_url || '/video/video-hn.mp4',
    cta_text: metadata.hero_cta_text || 'Personalized Care AI',
    aria_hero: (metadata.hero_aria_label as string) || 'Hero Spotlight Area',
    aria_scroll: (metadata.hero_aria_scroll as string) || 'Scroll to diagnostics section',
    metrics: metadata.hero_metrics || [
      { label: '[Tốc độ]', value: 'THẨM THẤU TÀNG HÌNH 3S', desc: 'Hạt Nano siêu phân tử. Chạm là khô tắp lự, tuyệt đối không bết dính.', color: 'blue' },
      { label: '[Hiệu quả]', value: 'PHONG TỎA MÙI 48H', desc: 'Khóa chặt tuyến bã nhờn và vi khuẩn sinh mùi. Áo sơ mi không một vệt ố vàng.', color: 'indigo' },
      { label: '[Thành phần]', value: 'TINH CHẤT DƯỢC LIỆU SẠCH', desc: 'Chiết xuất sinh học thân thiện with da nhạy cảm. Không cồn, không gây thâm sạm.', color: 'emerald' }
    ]
  });

  const productName = $derived(labels.product_name);
  const images = $derived(product?.images?.length ? product.images : []);
  const mainImage = $derived(images.length > 0 ? resolveMediaUrl(images[currentImageIndex]) : '');

  const rawHeadline = $derived(labels.headline);
  const videoUrl = $derived(labels.video_url);
  const ctaText = $derived(labels.cta_text);
  const metrics = $derived(labels.metrics);

  let displayText = $state("");
  let isTypingComplete = $state(false);

  // Optimized Typewriter with cleanup signal
  const typeWriter = async (signal: AbortSignal) => {
    if (!browser) return;
    const parts = rawHeadline.split(/(<[^>]+>)/g);
    let currentText = "";
    
    await new Promise(r => setTimeout(r, 800));
    if (signal.aborted) return;

    for (const part of parts) {
      if (part.startsWith("<")) {
        currentText += part;
        displayText = currentText;
      } else {
        for (const char of part) {
          if (signal.aborted) return;
          currentText += char;
          displayText = currentText;
          const delay = char === '.' || char === ',' ? 500 : 120 + Math.random() * 80;
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
    const element = document.getElementById('diagnostics');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };
</script>

<section
  id="hero"
  role="region"
  aria-label={labels.aria_hero}
  class="hero-center-layout content-hero snap-session relative w-full overflow-hidden flex flex-col items-center justify-start bg-[#020617] text-white"
  onmousemove={handleMouseMove}
  style="--mx: {mouse.x}px; --my: {mouse.y}px; --hero-accent: #3b82f6; --hero-glass-blur: 32px;"
>
  <LiquidHeader {product} {themeMode} {applyTheme} scrollToQuiz={scrollToCare} />


  <!-- NUCLEAR VIDEO BACKGROUND (Standard Full Coverage: 100% Native) -->
  <div class="absolute inset-x-0 top-0 bottom-0 z-0 overflow-hidden pointer-events-none w-full h-full">
    <div class="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-[#020617] to-transparent w-full" style:z-index="var(--z-surface)"></div>
    <video autoplay muted loop playsinline class="elite-video-bg">
      <source src={videoUrl} type="video/mp4" />
    </video>
  </div>

  <div class="container mx-auto px-6 max-w-6xl relative flex flex-col items-center pt-[var(--standard-pt)]" style:z-index="var(--z-surface)">

    <h1 class="typing-headline text-center w-full max-w-4xl lg:max-w-7xl font-black mb-6 mt-0">
       {@html displayText}<span class="typing-cursor {isTypingComplete ? 'is-complete' : ''}">|</span>
    </h1>

    {#if product?.shortDescription}
       <p class="hero-description outline-none">
          {@html product.shortDescription}
       </p>
    {/if}

    <div class="hero-product-display relative w-full max-w-6xl py-4 md:py-6 flex items-center justify-center bg-transparent">
    <div class="relative flex flex-col lg:grid lg:grid-cols-2 items-center justify-center gap-8 lg:gap-12 w-full px-4 lg:px-12" style:z-index="var(--z-surface)">
          
          <div class="relative float-anim parallax-layer flex lg:justify-end w-full">
             <div class="elite-product-card relative hud-frame">
                <!-- FLASH LIGHT BEAM (Cinematic Highlight) -->
                <div class="flashlight-beam hidden lg:block">
                   <!-- Cinematic Dots! -->
                   <div class="beam-dots absolute inset-0">
                      {#each Array(12) as _, i}
                         <div class="beam-dot" style="--d-idx: {i}"></div>
                      {/each}
                   </div>
                </div>
                
                <div class="product-glass-container group relative flex items-center justify-center overflow-hidden rounded-[3.5rem] aspect-square w-64 md:w-80 lg:w-96 bg-[#020617]">
                   <div 
                     class="flex h-full w-full transition-transform duration-700 ease-[cubic-bezier(0.23,1,0.32,1)]"
                     style="transform: translateX(-{currentImageIndex * 100}%);"
                   >
                     {#each images as img, i}
                        <div class="min-w-full h-full relative bg-[#020617]">
                           <img 
                             src="{resolveMediaUrl(img)}" 
                             alt="{productName} view {i + 1}" 
                             class="absolute inset-0 w-full h-full object-cover image-rim-light" 
                           />
                        </div>
                     {/each}
                   </div>

                   <!-- Slider Controls! -->
                   {#if images.length > 1}
                      <div class="absolute inset-x-0 bottom-8 flex justify-center gap-2" style:z-index="var(--z-hud-service)">
                         {#each images as _, i}
                            <button 
                               class="w-2 h-2 rounded-full transition-all duration-500 {i === currentImageIndex ? 'bg-blue-400 w-6' : 'bg-white/20 hover:bg-white/40'}"
                               onclick={(e) => { e.stopPropagation(); currentImageIndex = i; }}
                               aria-label="Go to slide {i + 1}"
                            ></button>
                         {/each}
                      </div>
                      
                      <button 
                         class="absolute left-4 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/20 backdrop-blur-md flex items-center justify-center text-white/40 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                         onclick={(e) => { e.stopPropagation(); prevImage(); }}
                         aria-label="Previous slide"
                      >
                         <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
                      </button>
                      <button 
                         class="absolute right-4 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/20 backdrop-blur-md flex items-center justify-center text-white/40 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                         onclick={(e) => { e.stopPropagation(); nextImage(); }}
                         aria-label="Next slide"
                      >
                         <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
                      </button>
                   {/if}
                </div>
                
                
                <!-- SCANNING LINE -->
                <div class="absolute inset-x-0 h-[1px] bg-blue-400/20 shadow-[0_0_15px_rgba(96,165,250,0.5)] scan-anim pointer-events-none"></div>
             </div>
          </div>

          <div id="products" class="metrics-arc-container relative flex lg:justify-start w-full">
             {#each metrics as metric, i}
                <div class="arc-item group flex flex-col max-w-[450px] md:max-w-none mb-6 lg:mb-8" style="--idx: {i}">
                   <div class="flex items-center gap-4 mb-2">
                      <div class="metric-dot bg-{metric.color}-500 shadow-[0_0_15px_rgba(var(--{metric.color}-rgb),1)]"></div>
                      <span class="text-[10px] font-black text-{metric.color}-500 uppercase tracking-[0.2em] drop-shadow-sm">{metric.label}</span>
                   </div>
                   <span class="metric-value transform group-hover:scale-105 transition-transform">{metric.value}</span>
                   <span class="metric-desc mt-2 text-[11px] text-slate-400 font-medium leading-relaxed max-w-[320px] opacity-80 group-hover:opacity-100 transition-opacity">
                      {metric.desc}
                   </span>
                </div>
             {/each}
          </div>
       </div>
    </div>
  </div>

  <!-- PREMIUM CTA BUTTON (Fixed to section bottom!) -->
  <button class="hero-cta-button" onclick={scrollToCare}>
     <div class="cta-gradient-overlay"></div>
     <div class="cta-content">
        <div class="cta-status-dot"></div>
        <span class="cta-text">{ctaText}</span>
        <svg class="cta-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
           <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
        </svg>
     </div>
     <div class="cta-shimmer"></div>
  </button>

  <!-- MOUSE SCROLL INDICATOR (Fixed to section bottom!) -->
  <a href="#diagnostics" class="mouse-scroll-indicator" aria-label={labels.aria_scroll} onclick={(e) => { e.preventDefault(); scrollToCare(); }}>
     <div class="mouse-body">
        <div class="mouse-wheel"></div>
     </div>
  </a>
</section>
