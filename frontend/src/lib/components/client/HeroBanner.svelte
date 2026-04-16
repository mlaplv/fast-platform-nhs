<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { browser } from '$app/environment';
  import "./HeroBanner.css";
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';

  const shopStore = getShopStore();

  interface HeroBannerProps {
    scrollToQuiz?: () => void;
  }

  let { scrollToQuiz }: HeroBannerProps = $props();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);
  const metadata = $derived(product?.metadata || {});

  const FALLBACK_METRICS = [
    { label: '[Tốc độ]', value: 'THẨM THẤU TÀNG HÌNH - KHÔNG BẾT', desc: 'Chất kem dạng serum siêu mỏng nhẹ, tan và thấm ngay khi vừa chạm da. Mang lại cảm giác khô thoáng tắp lự, tuyệt đối không bết dính hay rít ngứa.', color: 'blue' },
    { label: '[Hiệu quả]', value: 'PHÁ VỠ HẮC SẮC TỐ - DƯỠNG SÁNG HỒNG', desc: 'Đánh bật thâm sạm, sần sùi tại các "vùng khuất" (nách, nhũ hoa, bikini line). Ức chế triệt để melanin tối màu, trả lại làn da sáng hồng.', color: 'indigo' },
    { label: '[Thành phần]', value: 'TINH CHẤT "CHUẨN NHẬT" LÀNH TÍNH', desc: 'Sức mạnh làm sáng từ chiết xuất Hoa Anh Đào (Sakura) kết hợp Vitamin C & E. Bảng thành phần không cồn, không paraben.', color: 'emerald' }
  ];

  // ─── CTO FIX #1: Spring Mouse ─────────────────────────────────────────────
  // targetMouse: plain JS object — KHÔNG phải $state → mousemove write ZERO Svelte overhead
  let targetMouse = { x: 0, y: 0 };
  // springMouse: $state — Svelte re-render CHỈ khi spring thực sự update
  let springMouse = $state({ x: 0, y: 0 });
  let currentImageIndex = $state(0);
  // plain let — không phải $state → không trigger re-render khi gán
  let _springRafId: number | null = null;

  // Elite V2.2: Live FOMO Pulse Logic (Standardized)
  let liveViewers = $state(Math.floor(Math.random() * (45 - 12 + 1)) + 12);
  onMount(() => {
    const interval = setInterval(() => {
      const delta = Math.random() > 0.5 ? 1 : -1;
      liveViewers = Math.max(8, Math.min(64, liveViewers + delta));
    }, 5000);
    return () => clearInterval(interval);
  });

  /** CTO FIX #1: Self-terminating spring.
   *  Tự dừng khi delta < 0.05px — ZERO CPU khi user idle (tránh 60fps rAF vô hạn) */
  function _tickSpring() {
    const dx = targetMouse.x - springMouse.x;
    const dy = targetMouse.y - springMouse.y;
    if (Math.abs(dx) < 0.05 && Math.abs(dy) < 0.05) {
      springMouse.x = targetMouse.x; // snap final value
      springMouse.y = targetMouse.y;
      _springRafId = null;           // self-terminate
      return;
    }
    springMouse.x += dx * 0.12;
    springMouse.y += dy * 0.12;
    _springRafId = requestAnimationFrame(_tickSpring);
  }

  /** CTO FIX #2: mousemove → ZERO Svelte reactive writes.
   *  Ghi vào plain JS object, spring lazily starts nếu chưa running. */
  const handleMouseMove = (e: MouseEvent) => {
    if (!browser) return;
    targetMouse.x = (e.clientX / window.innerWidth - 0.5) * 40;
    targetMouse.y = (e.clientY / window.innerHeight - 0.5) * 40;
    if (_springRafId === null) _tickSpring(); // lazy-start
  };

  /** CTO FIX #3: Slideshow — $effect RIÊNG, TÁCH khỏi spring.
   *  CTO FIX #4: Preload ảnh kế chống flash khi swap (dùng Image() object). */
  $effect(() => {
    if (!browser) return;
    const interval = setInterval(() => {
      if (images && images.length > 1) {
        const next = (currentImageIndex + 1) % images.length;
        // Preload ảnh sau-next ngay bây giờ để browser cache trước
        const preloadIdx = (next + 1) % images.length;
        if (images[preloadIdx]) {
          const img = new Image();
          img.src = resolveMediaUrl(images[preloadIdx]);
        }
        currentImageIndex = next;
      }
    }, 5000);
    return () => clearInterval(interval);
  });

  // CTO FIX #7: Cleanup spring rAF khi component destroy (chống memory/CPU leak)
  onMount(() => () => {
    if (_springRafId !== null) {
      cancelAnimationFrame(_springRafId);
      _springRafId = null;
    }
  });

  const labels = $derived({
    product_name: product?.name || metadata.hero_product_name_fallback || '',
    headline: metadata.hero_headline || 'CHẤM DỨT<br/><span class="text-sakura-pink">SẠM NÁM</span>',
    video_url: (metadata.video_url as string) || (metadata.hero_video_url as string) || (metadata.hero_video as string) || '/uploads/video/HN_TikTok.mp4',
    cta_text: metadata.hero_cta_text || 'Chẩn đoán cá nhân hoá',
    aria_hero: metadata.hero_aria_label || 'Hero Spotlight Area',
    aria_scroll: metadata.hero_aria_scroll || 'Scroll to diagnostics section',
    metrics: FALLBACK_METRICS.map((fb, i) => {
      const custom = metadata.hero_metrics?.[i];
      if (!custom) return fb;
      return { label: custom.label || fb.label, value: custom.value || fb.value, desc: custom.desc || fb.desc, color: custom.color || fb.color };
    })
  });

  const productName = $derived(labels.product_name);
  const images = $derived(product?.images || []);
  const mainImage = $derived(images.length > 0 ? resolveMediaUrl(images[currentImageIndex]) : '');
  const rawHeadline = $derived(labels.headline);

  // Elite V2.2: Intelligent Path Sanitization (Fixing the "Missing Video" bug)
  const videoUrl = $derived.by(() => {
    let url = labels.video_url?.trim() ?? '';
    if (!url) return '';
    // If it starts with / (already absolute root-relative), keep it.
    if (url.startsWith('/')) return url;
    if (url.startsWith('http') || url.startsWith('//') || url.startsWith('blob:')) return url;
    return resolveMediaUrl(url);
  });

  type VideoMode = 'youtube' | 'tiktok' | 'local' | null;
  function getYoutubeId(url: string): string | null {
    const match = url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
    return match ? match[1] : null;
  }
  function getTiktokId(url: string): string | null {
    const match = url.match(/tiktok\.com\/@[\w.-]+\/video\/(\d+)/);
    return match ? match[1] : null;
  }

  const videoMode = $derived.by((): VideoMode => {
    if (!videoUrl) return null;
    if (getYoutubeId(videoUrl)) return 'youtube';
    if (videoUrl.includes('tiktok.com')) return 'tiktok';
    return 'local';
  });

  // Mirror ProductDetailDesktop: dùng typeof check để phân biệt 0 vs null
  const videoStartTime = $derived(
    typeof metadata.video_start_time === 'number' ? metadata.video_start_time :
    (metadata.video_start_time != null ? Number(metadata.video_start_time) : 0)
  );
  const videoEndTime = $derived.by((): number | null => {
    if (metadata.video_end_time == null) return null;
    const n = Number(metadata.video_end_time);
    return isNaN(n) ? null : n;
  });

  let videoEl: HTMLVideoElement | null = $state(null);

  /** timeupdate: seek về startTime khi chạm endTime (trim loop) */
  function handleTimeUpdate() {
    if (!videoEl) return;
    if (videoEndTime !== null && videoEl.currentTime >= videoEndTime) {
      videoEl.currentTime = videoStartTime;
      videoEl.play().catch(() => {});
    }
  }

  /** onended: safety net — bắt mọi trường hợp video kết thúc, luôn loop về startTime */
  function handleVideoEnded() {
    if (!videoEl) return;
    videoEl.currentTime = videoStartTime;
    videoEl.play().catch(() => {});
  }

  /** Khi videoUrl thay đổi → reset & autoplay từ startTime (Mirroring Working Detail Page) */
  $effect(() => {
    // R-FIX: Phải copy videoEl vào local const TRƯỚC để Svelte 5 track dependency đúng.
    // Nếu đọc videoEl trực tiếp trong `if`, Svelte sẽ không biết videoEl là dependency khi
    // nó còn null (condition false → body skip → dependency không được register → không re-run
    // khi bind:this bind xong).
    const el = videoEl;
    const currentUrl = videoUrl;
    const start = videoStartTime;
    const mode = videoMode;

    if (el && mode === 'local' && currentUrl) {
      el.load();
      const onMeta = () => {
        el.currentTime = start;
        el.play().catch(() => {});
      };
      el.addEventListener('loadedmetadata', onMeta, { once: true });
      return () => el.removeEventListener('loadedmetadata', onMeta);
    }
  });

  const iframeEmbedUrl = $derived.by((): string | null => {
    if (!videoUrl) return null;
    const ytId = getYoutubeId(videoUrl);
    if (ytId) {
      let url = `https://www.youtube.com/embed/${ytId}?autoplay=1&mute=1&loop=1&playlist=${ytId}&controls=0&playsinline=1&rel=0&modestbranding=1`;
      if (videoStartTime) url += `&start=${videoStartTime}`;
      if (videoEndTime) url += `&end=${videoEndTime}`;
      return url;
    }
    if (videoUrl.includes('tiktok.com')) {
      const ttId = getTiktokId(videoUrl);
      if (ttId) return `https://www.tiktok.com/embed/v2/${ttId}`;
      return `https://www.tiktok.com/embed/${encodeURIComponent(videoUrl)}`;
    }
    return null;
  });

  const ctaText = $derived(labels.cta_text);
  const metrics = $derived(labels.metrics);
  let displayText = $state("");
  let isTypingComplete = $state(false);

  const typeWriter = (signal: AbortSignal) => {
    if (!browser) return;
    const parts = rawHeadline.split(/(<[^>]+>)/g);
    
    const tokens: { text: string; delay: number }[] = [];
    for (const part of parts) {
      if (part.startsWith("<")) {
        tokens.push({ text: part, delay: 0 });
      } else {
        for (const char of part) {
          const isPunctuation = ['.', ',', '!', '?'].includes(char);
          const delay = isPunctuation ? 500 : 45 + Math.random() * 55;
          tokens.push({ text: char, delay });
        }
      }
    }

    let currentText = "";
    let tokenIdx = 0;
    let nextStepTime = performance.now() + 600;

    const tick = (now: number) => {
      if (signal.aborted) return;
      
      let changed = false;
      while (tokenIdx < tokens.length && now >= nextStepTime) {
        currentText += tokens[tokenIdx].text;
        nextStepTime += tokens[tokenIdx].delay;
        tokenIdx++;
        changed = true;
      }

      if (changed) {
        displayText = currentText;
      }

      if (tokenIdx < tokens.length) {
        requestAnimationFrame(tick);
      } else {
        isTypingComplete = true;
      }
    };

    requestAnimationFrame(tick);
  };

  $effect(() => {
    if (browser && rawHeadline) {
      const controller = new AbortController();
      displayText = "";
      isTypingComplete = false;
      typeWriter(controller.signal);
      return () => { controller.abort(); };
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
  <!-- VIDEO BACKGROUND: CINEMATIC 2026 ELITE -->
  <!-- Video đặt TRỰC TIẾP, không qua EditableWrapper để tránh height collapse -->
  <div class="absolute inset-0 overflow-hidden pointer-events-none" style="z-index: 0;">

    <!-- LOCAL VIDEO: mờ làm nền (Elite blur engine) -->
    {#if videoMode === 'local'}
      <video
        bind:this={videoEl}
        ontimeupdate={handleTimeUpdate}
        onended={handleVideoEnded}
        autoplay muted loop={videoEndTime === null && videoStartTime === 0} playsinline
        class="elite-video-bg"
        src={videoUrl}
      ></video>
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

    <!-- CTO FIX #5+#6: CSS class overlays thay inline style — browser cached, zero re-parse.
         video-dim-overlay thay CSS filter trực tiếp trên video (no GPU shader pass). -->
    <div class="video-dim-overlay"></div>
    <div class="video-vignette-top"></div>
    <div class="video-vignette-bottom"></div>
    <!-- Left + right + radial gộp 1 div = 1 paint pass thay 3 div -->
    <div class="video-vignette-radial"></div>

    <!-- Admin edit controls -->
    <div class="absolute inset-0 pointer-events-auto" style="z-index: 3;">
      <EditableWrapper path="metadata.video_url" type="video" label="SỬA VIDEO NỀN">
        <span></span>
      </EditableWrapper>
    </div>
  </div>

  <div class="container mx-auto px-6 max-w-7xl relative flex flex-col items-center pt-[var(--standard-pt)] pb-12 z-surface">
    <!-- SECTION HEADER: Normalized spacing & Full-width prominence -->
    <header class="text-center w-full mb-8 md:mb-12 relative" in:fade>
      <EditableWrapper path="metadata.hero_headline" type="html" label="SỬA TIÊU ĐỀ BANNER">
          <h1 class="hero-titanic-headline typing-headline text-center w-full max-w-4xl lg:max-w-7xl font-black mb-6 mt-0 tracking-tight mx-auto text-4xl md:text-7xl lg:text-8xl uppercase leading-[1]">
          {@html displayText}<span class="typing-cursor {isTypingComplete ? 'is-complete' : ''} text-red-500"></span>
          </h1>
      </EditableWrapper>

      {#if product?.shortDescription}
         <EditableWrapper path="shortDescription" label="SỬA MÔ TẢ NGẮN">
             <p class="section-description hero-description text-center text-slate-300 max-w-3xl font-medium mx-auto">
                {@html product.shortDescription}
             </p>
         </EditableWrapper>
      {/if}
    </header>

    <div class="hero-product-display relative w-full mt-6 md:mt-8 lg:mt-12 pb-0 flex flex-col md:flex-row items-center justify-center gap-2 lg:gap-4 z-surface">
          <div class="relative w-full md:w-1/2 flex justify-center parallax-layer">
              <div class="group relative flex items-center justify-center w-full max-w-md float-anim cinematic-frame">
                <div class="absolute -inset-2 z-20 pointer-events-none opacity-60 transition-opacity group-hover:opacity-100">
                   <div class="absolute -top-4 -left-4 w-12 h-12 border-t-[1px] border-l-[1px] border-white/40 rounded-tl-[2px]">
                      <span class="absolute top-2 left-2 text-[8px] font-mono tracking-widest text-red-500 flex items-center gap-1">
                         <span class="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse"></span> REC
                      </span>
                   </div>
                   <div class="absolute -top-4 -right-4 w-12 h-12 border-t-[1px] border-r-[1px] border-white/40 text-right rounded-tr-[2px]">
                      <span class="absolute top-2 right-2 text-[8px] font-mono tracking-widest text-white/50">4K 60FPS</span>
                   </div>
                   <div class="absolute -bottom-4 -left-4 w-12 h-12 border-b-[1px] border-l-[1px] border-white/40 rounded-bl-[2px]">
                      <span class="absolute bottom-2 left-2 text-[8px] font-mono tracking-widest text-white/50">TC 00:00:26:02</span>
                   </div>
                   <div class="absolute -bottom-4 -right-4 w-12 h-12 border-b-[1px] border-r-[1px] border-white/40 text-right rounded-br-[2px]">
                      <span class="absolute bottom-2 right-2 text-[8px] font-mono tracking-widest text-white/50">ISO 100</span>
                   </div>
                </div>

                <EditableWrapper path="images.0" type="image" label="SỬA ẢNH CHIẾN DỊCH">
                    <div class="relative film-grain-container rounded-[2px] overflow-hidden">
                        <img
                          src="{mainImage}"
                          alt="{productName}"
                          class="relative z-10 w-full h-auto object-contain transition-transform duration-700 group-hover:scale-[1.03] cinematic-grading rounded-[2px]"
                        />
                        <div class="absolute inset-0 z-20 pointer-events-none film-grain-mask"></div>
                    </div>
                </EditableWrapper>

                <div class="absolute -bottom-16 left-0 right-0 flex justify-center gap-2 z-30">
                   {#each images as _, i}
                      <button
                        onclick={() => currentImageIndex = i}
                        class="h-1 rounded-full transition-all duration-500 {currentImageIndex === i ? 'bg-white w-8 shadow-sm' : 'bg-white/10 w-1.5'}"
                        aria-label="Go to image {i + 1}"
                      ></button>
                   {/each}
                </div>
             </div>
          </div>

      <div class="w-full md:w-1/2 flex flex-col relative justify-center">
         <div class="metrics-arc-container">
            {#each metrics as metric, i}
                <div class="hud-metric-segment group relative pt-0 px-0 pb-0 transition-all duration-500" style:--idx={i}>
                    <EditableWrapper path="metadata.hero_metrics.{i}.label" value={metric.label} label="SỬA NHÃN {i+1}">
                      <span class="text-[10px] font-black uppercase tracking-[.2em] whitespace-nowrap transition-colors duration-500"
                            class:text-blue-400={metric.color === 'blue'}
                            class:text-indigo-400={metric.color === 'indigo'}
                            class:text-emerald-400={metric.color === 'emerald'}
                            class:text-sakura-pink={!metric.color || metric.color === 'sakura'}>{metric.label}</span>
                    </EditableWrapper>
                    
                    <EditableWrapper path="metadata.hero_metrics.{i}.value" value={metric.value} label="SỬA GIÁ TRỊ {i+1}">
                      <h3 class="text-lg font-black tracking-normal text-white transition-colors duration-300 whitespace-nowrap"
                          class:group-hover:text-blue-400={metric.color === 'blue'}
                          class:group-hover:text-indigo-400={metric.color === 'indigo'}
                          class:group-hover:text-emerald-400={metric.color === 'emerald'}
                          class:group-hover:text-sakura-pink={!metric.color || metric.color === 'sakura'}>{metric.value}</h3>
                    </EditableWrapper>

                   <EditableWrapper path="metadata.hero_metrics.{i}.desc" value={metric.desc} type="html" label="SỬA MÔ TẢ {i+1}">
                     <p class="mt-2 text-sm text-slate-400 font-medium leading-relaxed opacity-70 group-hover:opacity-100 transition-opacity metric-desc">{metric.desc}</p>
                   </EditableWrapper>
                   <div class="absolute -inset-4 bg-radial-gradient from-sakura-pink/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
                </div>
            {/each}
         </div>
      </div>
    </div>
  </div>

  <button class="hero-cta-button" onclick={scrollToQuiz}>
     <div class="cta-gradient-overlay"></div>
     <EditableWrapper path="metadata.hero_cta_text" value={ctaText} label="SỬA CHỮ NÚT BẤM" class="w-full flex justify-center">
        <div class="cta-content">
           <div class="cta-status-dot"></div>
           <span class="cta-text">{ctaText}</span>
           <svg class="cta-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
           </svg>
        </div>
     </EditableWrapper>
     <div class="cta-shimmer"></div>
  </button>

  <a href="#diagnostics" class="mouse-scroll-indicator" aria-label={labels.aria_scroll} onclick={(e) => { e.preventDefault(); scrollToQuiz?.(); }}>
     <div class="mouse-body">
        <div class="mouse-wheel"></div>
     </div>
  </a>
</section>

<style>
  .z-surface { z-index: var(--z-surface); }
</style>
