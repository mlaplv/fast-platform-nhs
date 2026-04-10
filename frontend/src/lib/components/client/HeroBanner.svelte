<script lang="ts">
  import { onMount } from 'svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { browser } from '$app/environment';
  import "./HeroBanner.css";
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';

  const shopStore = getShopStore();

  interface HeroBannerProps {
    scrollToQuiz?: () => void;
  }

  let { scrollToQuiz }: HeroBannerProps = $props();
  const product = $derived(shopStore.product);
  const metadata = $derived(product?.metadata || {});

  // Elite V2.2: Standard Branding Fallbacks (Non-logic descriptors)
  const FALLBACK_METRICS = [
    { label: '[Tốc độ]', value: 'THẨM THẤU TÀNG HÌNH - KHÔNG BẾT', desc: 'Chất kem dạng serum siêu mỏng nhẹ, tan và thấm ngay khi vừa chạm da. Mang lại cảm giác khô thoáng tắp lự, tuyệt đối không bết dính hay rít ngứa.', color: 'blue' },
    { label: '[Hiệu quả]', value: 'PHÁ VỠ HẮC SẮC TỐ - DƯỠNG SÁNG HỒNG', desc: 'Đánh bật thâm sạm, sần sùi tại các "vùng khuất" (nách, nhũ hoa, bikini line). Ức chế triệt để melanin tối màu, trả lại làn da sáng hồng.', color: 'indigo' },
    { label: '[Thành phần]', value: 'TINH CHẤT "CHUẨN NHẬT" LÀNH TÍNH', desc: 'Sức mạnh làm sáng từ chiết xuất Hoa Anh Đào (Sakura) kết hợp Vitamin C & E. Bảng thành phần không cồn, không paraben.', color: 'emerald' }
  ];

  let mouse = $state({ x: 0, y: 0 });
  let springMouse = $state({ x: 0, y: 0 });
  let currentImageIndex = $state(0);

  const handleMouseMove = (e: MouseEvent) => {
    if (!browser) return;
    const { clientX, clientY } = e;
    const { innerWidth, innerHeight } = window;

    mouse.x = (clientX / innerWidth - 0.5) * 40;
    mouse.y = (clientY / innerHeight - 0.5) * 40;
  };

  // Organic spring-like follow effect
  $effect(() => {
    let frame: number;
    const update = () => {
      springMouse.x += (mouse.x - springMouse.x) * 0.1;
      springMouse.y += (mouse.y - springMouse.y) * 0.1;
      frame = requestAnimationFrame(update);
    };
    frame = requestAnimationFrame(update);

    // Auto-slide 5s
    const interval = setInterval(() => {
        nextImage();
    }, 5000);

    return () => {
      cancelAnimationFrame(frame);
      clearInterval(interval);
    };
  });

  const nextImage = () => {
    if (images.length === 0) return;
    currentImageIndex = (currentImageIndex + 1) % images.length;
  };

  const prevImage = () => {
    if (images.length === 0) return;
    currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
  };

  const labels = $derived({
    product_name: product?.name || metadata.hero_product_name_fallback || 'Elite Formulation',
    headline: metadata.hero_headline || '<span>ĐÁNH BAY</span> <br/> <span class="headline-shift">THÂM SẠM</span>',
    video_url: metadata.video_url || metadata.hero_video_url || metadata.hero_video || '/uploads/video/HN_TikTok.mp4',
    cta_text: metadata.hero_cta_text || 'Chẩn đoán cá nhân hoá',
    aria_hero: metadata.hero_aria_label || 'Hero Spotlight Area',
    aria_scroll: metadata.hero_aria_scroll || 'Scroll to diagnostics section',
    metrics: metadata.hero_metrics || FALLBACK_METRICS
  });

  const productName = $derived(labels.product_name);
  const images = $derived(product?.images?.length ? product.images : []);
  const mainImage = $derived(images.length > 0 ? resolveMediaUrl(images[currentImageIndex]) : '');

  const rawHeadline = $derived(labels.headline);
  const rawVideoUrl = $derived.by((): string => {
    const url = labels.video_url?.trim() ?? '';
    // Auto-strip erroneous paths like /frontend/static/ or ./static/
    // SvelteKit serves static/ at root (no /static prefix).
    const sanitized = url.replace(/^(\.\/)?(\/)?(frontend\/)?static\//, '/');
    return resolveMediaUrl(sanitized);
  });
  const videoUrl = $derived(rawVideoUrl);

  const ctaText = $derived(labels.cta_text);
  const metrics = $derived(labels.metrics);

  type VideoMode = 'youtube' | 'tiktok' | 'local' | null;

  // Utility: extract YouTube video ID
  function getYoutubeId(url: string): string | null {
    const match = url.match(
      /(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/
    );
    return match ? match[1] : null;
  }

  // Utility: extract TikTok video ID
  function getTiktokId(url: string): string | null {
    const match = url.match(/tiktok\.com\/@[\w.-]+\/video\/(\d+)/);
    return match ? match[1] : null;
  }

  // Detect video mode: youtube | tiktok | local | null
  const videoMode = $derived.by((): VideoMode => {
    if (!videoUrl) return null;
    if (getYoutubeId(videoUrl)) return 'youtube';
    if (videoUrl.includes('tiktok.com')) return 'tiktok';
    if (/\.(mp4|webm|ogg|mov)(\?.*)?$/i.test(videoUrl)) return 'local';
    return 'local'; // Default to local for anything else if we want to try rendering it
  });

  // Iframe embed URL for YouTube / TikTok
  const iframeEmbedUrl = $derived.by((): string | null => {
    if (!videoUrl) return null;
    const ytId = getYoutubeId(videoUrl);
    if (ytId) {
      return `https://www.youtube.com/embed/${ytId}?autoplay=1&mute=1&loop=1&playlist=${ytId}&controls=0&playsinline=1&rel=0&modestbranding=1`;
    }

    if (videoUrl.includes('tiktok.com')) {
      const ttId = getTiktokId(videoUrl);
      if (ttId) return `https://www.tiktok.com/embed/v2/${ttId}`;
      return `https://www.tiktok.com/embed/${encodeURIComponent(videoUrl)}`;
    }
    return null;
  });

  let displayText = $state("");
  let isTypingComplete = $state(false);

  // Optimized Typewriter with Elite V2.2 Performance (Antigravity Style)
  const typeWriter = async (signal: AbortSignal) => {
    if (!browser) return;
    
    // Split by tags to keep HTML intact
    const parts = rawHeadline.split(/(<[^>]+>)/g);
    let currentText = "";
    
    // Initial cinematic pause
    await new Promise(r => setTimeout(r, 600));
    if (signal.aborted) return;

    for (const part of parts) {
      if (part.startsWith("<")) {
        currentText += part;
        displayText = currentText;
      } else {
        // Character by character with variable "human-like" delay
        for (const char of part) {
          if (signal.aborted) return;
          currentText += char;
          displayText = currentText;
          
          // Smooth timing: punctuation gets longer pause, normal chars are snappy
          const isPunctuation = ['.', ',', '!', '?'].includes(char);
          const delay = isPunctuation ? 500 : 45 + Math.random() * 55;
          await new Promise(r => setTimeout(r, delay));
        }
      }
    }
    isTypingComplete = true;
  };


  // Reactively trigger typewriter when headline data is ready
  $effect(() => {
    if (browser && rawHeadline) {
      const controller = new AbortController();
      
      // Reset state for new typewriter sequence
      displayText = "";
      isTypingComplete = false;
      
      typeWriter(controller.signal);

      return () => {
        controller.abort();
      };
    }
  });

</script>

<section
  id="hero"
  role="region"
  aria-label={labels.aria_hero}
  class="hero-center-layout content-hero snap-session relative w-full overflow-hidden flex flex-col items-center justify-start bg-[#020617] text-white"
  onmousemove={handleMouseMove}
  style:--mx="{springMouse.x}px" style:--my="{springMouse.y}px" style:--hero-accent="#3b82f6" style:--hero-glass-blur="64px"
>

  <!-- LIQUID METABALL BACKGROUND REMOVED FOR RAM OPTIMIZATION -->

  <!-- NUCLEAR VIDEO BACKGROUND (Standard Full Coverage: 100% Native) -->
  <div class="absolute inset-x-0 top-0 bottom-0 overflow-hidden pointer-events-none w-full h-full" style="z-index: var(--z-bg); opacity: 0.2;">
    <div class="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-[#020617] to-transparent w-full z-surface"></div>
    {#if videoMode === 'local'}
      <video autoplay muted loop playsinline class="elite-video-bg">
        <source src={videoUrl} type="video/mp4" />
      </video>
    {:else if videoMode === 'youtube' || videoMode === 'tiktok'}
      <iframe
        class="elite-video-bg pointer-events-none"
        src={iframeEmbedUrl}
        title="Hero Video"
        allow="autoplay; fullscreen; picture-in-picture"
        allowfullscreen
        frameborder="0"
      ></iframe>
    {/if}
  </div>

  <div class="container mx-auto px-6 max-w-6xl relative flex flex-col items-center pt-[var(--standard-pt)] z-surface">

    <h1 class="typing-headline text-center w-full max-w-4xl lg:max-w-7xl font-black mb-6 mt-0 text-5xl md:text-7xl lg:text-9xl tracking-tighter italic">
       {@html displayText}<span class="typing-cursor {isTypingComplete ? 'is-complete' : ''} text-red-500">_</span>
    </h1>

    {#if product?.shortDescription}
       <p class="hero-description text-center text-lg md:text-xl text-slate-300 max-w-2xl font-medium mb-12">
          {@html product.shortDescription}
       </p>
    {/if}

    <div class="hero-product-display relative w-full max-w-6xl pt-6 pb-0 flex flex-col md:flex-row items-center justify-center gap-8 z-surface">

          <div class="relative w-full md:w-1/2 flex justify-center parallax-layer">
             <!-- ELITE SPOTLIGHT HALO (Viral 2026) -->
             <div class="absolute inset-0 bg-radial-gradient from-sakura-glow/20 via-transparent to-transparent blur-[120px] scale-150 pointer-events-none opacity-60"></div>

             <div class="group relative flex items-center justify-center w-72 md:w-96 float-anim">
                <img
                  src="{mainImage}"
                  alt="{productName}"
                  class="relative z-10 w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110 drop-shadow-[0_20px_50px_rgba(0,0,0,0.5)] rounded-lg"
                />

                <!-- VIEW FINDER CORNERS (iOS 26 Liquid Aesthetic) -->
                <div class="absolute -inset-4 z-20 pointer-events-none">
                   <div class="absolute -top-1 -left-1 w-6 h-6 border-t-[3px] border-l-[3px] border-white/80 rounded-tl-lg"></div>
                   <div class="absolute -top-1 -right-1 w-6 h-6 border-t-[3px] border-r-[3px] border-white/80 rounded-tr-lg"></div>
                   <div class="absolute -bottom-1 -left-1 w-6 h-6 border-b-[3px] border-l-[3px] border-white/80 rounded-bl-lg"></div>
                   <div class="absolute -bottom-1 -right-1 w-6 h-6 border-b-[3px] border-r-[3px] border-white/80 rounded-br-lg"></div>
                </div>

                <!-- SCANNING LINE REMOVED -->

                <!-- SLIDER CONTROLS (INSIDE SLIDE) -->
                <div class="absolute bottom-4 left-0 right-0 flex justify-center gap-2 z-30">
                   {#each images as _, i}
                      <button
                        onclick={() => currentImageIndex = i}
                        class="w-2 h-2 rounded-full transition-all duration-300 {currentImageIndex === i ? 'bg-white w-6' : 'bg-white/30 hover:bg-white/60'}"
                        aria-label="Go to image {i + 1}"
                      ></button>
                   {/each}
                </div>
             </div>
          </div>

          <div class="w-full md:w-1/2 flex flex-col relative justify-center">
             <div class="metrics-arc-container">
                {#each metrics as metric, i}
                   <div class="hud-metric-segment group relative pt-5 px-0 pb-0 transition-all duration-500" style:--idx={i}>
                      <div class="flex items-center gap-3 mb-2">
                         <div class="w-1 h-1 rounded-full bg-sakura-pink shadow-[0_0_8px_#ffb7c5] animate-pulse"></div>
                         <span class="text-[10px] font-black text-sakura-pink/70 uppercase tracking-[.25em]">{metric.label}</span>
                      </div>
                      <h3 class="text-xl font-black italic tracking-tighter text-white group-hover:text-sakura-pink transition-colors duration-300">{metric.value}</h3>
                      <p class="mt-2 text-sm text-slate-400 font-medium leading-relaxed opacity-70 group-hover:opacity-100 transition-opacity metric-desc">{metric.desc}</p>
                      
                      <!-- Subtle Glow Interaction -->
                      <div class="absolute -inset-4 bg-radial-gradient from-sakura-pink/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
                   </div>
                {/each}
             </div>
          </div>
    </div>
  </div>

  <!-- PREMIUM CTA BUTTON (Fixed to section bottom!) -->
  <button class="hero-cta-button" onclick={scrollToQuiz}>
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
  <a href="#diagnostics" class="mouse-scroll-indicator" aria-label={labels.aria_scroll} onclick={(e) => { e.preventDefault(); scrollToQuiz?.(); }}>
     <div class="mouse-body">
        <div class="mouse-wheel"></div>
     </div>
  </a>
</section>

<style>
  .z-surface { z-index: var(--z-surface); }
  .z-hud-service { z-index: var(--z-hud-service); }
</style>
