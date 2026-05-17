<script lang="ts">
  import { onMount } from 'svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { browser } from '$app/environment';
  import "./HeroBanner.css";
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import { typewriter } from '$lib/actions/typewriter';
  import { fade } from 'svelte/transition';

  const shopStore = getShopStore();

  interface HeroBannerProps {
    scrollToQuiz?: () => void;
    triggerScan?: () => void;
  }

  let { scrollToQuiz, triggerScan }: HeroBannerProps = $props();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);
  const metadata = $derived(product?.metadata || {});

  const FALLBACK_METRICS = [
    { label: '[TỰ TIN]', value: 'DIỆN BIKINI KHÔNG CHÚT TỲ VẾT', desc: 'Xóa tan mặc cảm thâm sạm vùng cánh và bikini line. Trả lại sự tự tin tuyệt đối cho nàng trong mọi trang phục quyến rũ.', color: 'copper' },
    { label: '[TỐC ĐỘ]', value: 'BẬT TÔNG TRẮNG HỒNG SAU 14 NGÀY', desc: 'Công nghệ Nano-penetration độc quyền giúp tinh chất thẩm thấu sâu, ức chế melanin tối màu nhanh gấp 3 lần thông thường.', color: 'gold' },
    { label: '[CẢM GIÁC]', value: 'MỊN MÀNG & QUYẾN RŨ TỨC THÌ', desc: 'Chất serum lỏng nhẹ như sương, không bết dính. Nuôi dưỡng làn da vùng nhạy cảm trở nên mướt mịn, thơm nhẹ nhàng.', color: 'peach' }
  ];

  let targetMouse = { x: 0, y: 0 };
  let springMouse = $state({ x: 0, y: 0 });
  let currentImageIndex = $state(0);
  let _springRafId: number | null = null;


  function _tickSpring() {
    const dx = targetMouse.x - springMouse.x;
    const dy = targetMouse.y - springMouse.y;
    if (Math.abs(dx) < 0.05 && Math.abs(dy) < 0.05) {
      springMouse.x = targetMouse.x;
      springMouse.y = targetMouse.y;
      _springRafId = null;
      return;
    }
    springMouse.x += dx * 0.12;
    springMouse.y += dy * 0.12;
    _springRafId = requestAnimationFrame(_tickSpring);
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!browser) return;
    targetMouse.x = (e.clientX / window.innerWidth - 0.5) * 40;
    targetMouse.y = (e.clientY / window.innerHeight - 0.5) * 40;
    if (_springRafId === null) _tickSpring();
  };

  $effect(() => {
    if (!browser) return;
    const interval = setInterval(() => {
      if (images && images.length > 1) {
        const next = (currentImageIndex + 1) % images.length;
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

  onMount(() => () => {
    if (_springRafId !== null) {
      cancelAnimationFrame(_springRafId);
      _springRafId = null;
    }
  });

  const labels = $derived({
    product_name: product?.name || metadata.hero_product_name_fallback || '',
    video_url: (metadata.video_url as string) || (metadata.hero_video_url as string) || (metadata.hero_video as string) || '/uploads/video/HN_TikTok.mp4',
    cta_text: metadata.hero_cta_text || 'Khám phá bí quyết sau 14 ngày',
    aria_hero: metadata.hero_aria_label || 'Hero Spotlight Area',
    aria_scroll: metadata.hero_aria_scroll || 'Scroll to results section',
    metrics: FALLBACK_METRICS.map((fb, i) => {
      const custom = metadata.hero_metrics?.[i];
      if (!custom) return fb;
      return { label: custom.label || fb.label, value: custom.value || fb.value, desc: custom.desc || fb.desc, color: custom.color || fb.color };
    })
  });

  const productName = $derived(labels.product_name);
  const images = $derived(product?.images || []);
  const mainImage = $derived(images.length > 0 ? resolveMediaUrl(images[currentImageIndex]) : '');
  
  const stripTags = (h: string) => h ? h.replace(/<[^>]*>?/gm, '').trim() : '';
  const legacyParts = $derived(metadata.hero_headline?.split('<br/>') || []);
  const h1 = $derived(clean(metadata.hero_headline_1 || stripTags(legacyParts[0]) || "Miccosmo Beppin Body"));
  const h2 = $derived(clean(metadata.hero_headline_2 || stripTags(legacyParts[1]) || "Virgin White Serum"));
  
  const rawH1 = $derived(metadata.hero_headline_1 || stripTags(legacyParts[0]) || "Miccosmo Beppin Body");
  const rawH2 = $derived(metadata.hero_headline_2 || stripTags(legacyParts[1]) || "Virgin White Serum");

  const rawHeadline = $derived.by(() => {
    const isH1Off = rawH1.startsWith('[OFF]');
    const isH2Off = rawH2.startsWith('[OFF]');
    if (isH1Off && isH2Off) return '';
    if (isH1Off) return `<span class="text-luxury-copper">${h2}</span>`;
    if (isH2Off) return h1;
    return `<span class="text-[1.2em] block leading-[1.4] mb-[-0.35em]">${h1}</span><span class="text-luxury-copper">${h2}</span>`;
  });

  const fallbackDesc = `
    <div class="text-center mb-3 text-[15px] md:text-[17px] font-light leading-relaxed tracking-wide">
      Bật tông trắng sáng cùng <h1 class="inline font-semibold" style="font-size:inherit;margin:0;padding:0;color:inherit">Beppin Body Virgin White Serum</h1> trẻ hóa da cấp độ tế bào - Tinh chất dưỡng sáng hồng vùng nhạy cảm (Nách, Nhũ hoa, Bikini).
    </div>
    <p class="text-center text-[14px] md:text-[15px] font-light leading-relaxed opacity-80 mx-auto max-w-2xl">
      Giải pháp thẩm thấu sâu đa tầng, giúp tế bào kích hoạt độ bóng, trong, trắng sáng. An toàn - Hiệu quả cho mọi loại da kể cả da nhạy cảm. Không bết dính.
    </p>
  `;

  const processedDescription = $derived.by(() => {
    let desc = product?.shortDescription || fallbackDesc;
    const keyword = "Beppin Body Virgin White Serum";
    
    // Nếu đã có thẻ h1 bọc từ khóa rồi thì trả về luôn
    if (desc.includes('<h1') && desc.includes(keyword)) return desc;

    // Ưu tiên thay thế nếu từ khóa đang nằm trong thẻ span (pattern cũ)
    if (desc.includes('<span') && desc.includes(keyword)) {
      desc = desc.replace(
        /<span([^>]*)>(.*?Beppin Body Virgin White Serum.*?)<\/span>/gi,
        '<h1 style="display:inline;font-size:inherit;font-weight:inherit;margin:0;padding:0;color:inherit">$2</h1>'
      );
      if (desc.includes('<h1')) return desc;
    }

    // Nếu là text thô, bọc trực tiếp
    return desc.replace(
      new RegExp(keyword, 'gi'),
      `<h1 class="inline font-semibold" style="font-size:inherit;margin:0;padding:0;color:inherit">$&</h1>`
    );
  });

  const clean = (s: unknown) => {
    if (!s) return "";
    let val = String(s);
    if (val.startsWith('[OFF]')) return val.substring(5).trim();
    return val;
  };

  const videoUrl = $derived.by(() => {
    let url = labels.video_url?.trim() ?? '';
    if (!url) return '';
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

  $effect(() => {
    if (videoEl && videoMode === 'local' && videoUrl) {
      videoEl.load();
      
      const onMeta = () => {
        if (videoEl) {
          videoEl.currentTime = videoStartTime;
          videoEl.play().catch(() => {});
        }
      };
      
      videoEl.addEventListener('loadedmetadata', onMeta, { once: true });
      return () => videoEl?.removeEventListener('loadedmetadata', onMeta);
    }
  });
  // Elite V2.2: Reactive derived state so Svelte 5 $effect accurately tracks it
  const isEditing = $derived(liveEditStore.activePath !== null);

  // Pause video during live editing to save GPU/CPU and prevent jitter/crashes
  $effect(() => {
    if (!videoEl) return;
    if (isEditing) {
      videoEl.pause();
    } else {
      videoEl.play().catch(() => {});
    }
  });
  function handleTimeUpdate() {
    if (!videoEl) return;
    if (videoEndTime !== null && videoEl.currentTime >= videoEndTime) {
      videoEl.currentTime = videoStartTime;
      videoEl.play().catch(() => {});
    }
  }

  function handleVideoEnded() {
    if (!videoEl) return;
    videoEl.currentTime = videoStartTime;
    videoEl.play().catch(() => {});
  }

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
  let isTypingComplete = $state(false);

  $effect(() => {
    if (rawHeadline) isTypingComplete = false;
  });

  // Elite V2.2: The actual headline is derived from shopStore metadata
  // We use the centralized typewriter action to handle the animation
</script>

  <section
  id="hero"
  role="region"
  aria-label={labels.aria_hero}
  class="hero-center-layout content-hero snap-session relative w-full overflow-hidden flex flex-col items-center justify-start bg-[#010101] text-white"
  onmousemove={handleMouseMove}
  style:--mx="{springMouse.x}px"
  style:--my="{springMouse.y}px"
  style:--hero-accent="#0d9488"
  style:--hero-glass-blur="64px"
  style:--luxury-copper="#0d9488"
  style:--luxury-gold="#f59e0b"
  style:--luxury-peach="#ea580c"
  style:--color-luxury-copper="#0d9488"
  style:--color-luxury-gold="#f59e0b"
  style:--color-luxury-peach="#ea580c"
>
  <div class="absolute inset-0 overflow-hidden pointer-events-none" style="z-index: var(--z-base);">
    <div style:display={isEditing ? 'none' : 'block'} class="absolute inset-0">
      {#if videoMode === 'local'}
        <video
          bind:this={videoEl}
          ontimeupdate={handleTimeUpdate}
          onended={handleVideoEnded}
          autoplay muted preload="metadata" playsinline
          loop={videoEndTime === null}
          class="elite-video-bg fade-in"
          src={videoUrl}
        ></video>
      {:else if videoMode === 'youtube' || videoMode === 'tiktok'}
        <iframe
          class="elite-video-bg pointer-events-none fade-in"
          src={iframeEmbedUrl}
          title="Hero Video"
          allow="autoplay; fullscreen; picture-in-picture"
          allowfullscreen
          frameborder="0"
        ></iframe>
      {/if}
    </div>
    {#if isEditing}
      <div class="elite-video-bg bg-[#0d1117] fade-in"></div>
    {/if}

    <div class="video-dim-overlay {isEditing ? 'opacity-100 bg-black/90' : ''} transition-all duration-700"></div>
    <div class="video-vignette-top"></div>
    <div class="video-vignette-bottom"></div>
    <div class="video-vignette-radial"></div>

    <div class="absolute inset-0 pointer-events-auto" style="z-index: var(--z-wave);">
      <EditableWrapper path="metadata.video_url" type="video" label="SỬA VIDEO NỀN">
         <span></span>
      </EditableWrapper>
    </div>
  </div>

  <div class="container mx-auto px-6 max-w-7xl relative flex flex-col items-center pb-12 z-surface">
    <header class="text-center w-full mb-8 md:mb-12 relative" in:fade>
      <div class="elite-hero-headline typing-headline text-center font-bold">
        {#if !liveEditStore.isEditMode}
          <span 
            use:typewriter={{ 
                text: rawHeadline, 
                speed: 40,
                onComplete: () => isTypingComplete = true 
            }}
          >{@html rawHeadline}</span>
        {:else}
          {#if !rawH1.startsWith('[OFF]') || liveEditStore.isEditMode}
            <EditableWrapper path="metadata.hero_headline_1" type="text" label="SỬA TIÊU ĐỀ 1" class="inline" as="span">
              {@html h1}
            </EditableWrapper>
          {/if}
          
          {#if (!rawH1.startsWith('[OFF]') && !rawH2.startsWith('[OFF]')) || liveEditStore.isEditMode}
            <br/>
          {/if}
 
          {#if !rawH2.startsWith('[OFF]') || liveEditStore.isEditMode}
            <span class="text-luxury-copper">
              <EditableWrapper path="metadata.hero_headline_2" type="text" label="SỬA TIÊU ĐỀ 2" class="inline" as="span">
                {@html h2}
              </EditableWrapper>
            </span>
          {/if}
        {/if}
        <span class="typing-cursor {isTypingComplete ? 'is-complete' : ''} text-luxury-copper"></span>
      </div>

      {#if processedDescription}
         <EditableWrapper path="shortDescription" label="SỬA MÔ TẢ NGẮN">
              <div class="section-description hero-description text-slate-200 max-w-3xl mx-auto mt-4 md:mt-6">
                {@html processedDescription}
             </div>
         </EditableWrapper>
      {/if}
    </header>

    <div class="hero-product-display relative w-full mt-4 md:mt-6 lg:mt-8 pb-0 flex flex-col md:flex-row items-center justify-center gap-2 lg:gap-4 z-surface">
          <div class="relative w-full md:w-1/2 flex justify-center parallax-layer">
              <div class="group relative flex items-center justify-center w-full max-w-md float-anim cinematic-frame">
                <div class="absolute -inset-2 z-20 pointer-events-none opacity-60 transition-opacity group-hover:opacity-100">
                   <div class="absolute -top-4 -left-4 w-12 h-12 border-t-[1px] border-l-[1px] border-white/40 rounded-tl-[2px]">
                      <span class="absolute top-2 left-2 text-[8px] font-mono tracking-widest text-[#E8D5B0] flex items-center gap-1">
                         <span class="w-1.5 h-1.5 bg-[#E8D5B0] rounded-full animate-pulse"></span> REC
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

                <button onclick={() => triggerScan?.()} class="absolute top-2 right-2 z-[99] w-14 h-14 cursor-pointer hover:scale-105 transition-transform drop-shadow-md bg-transparent border-none p-0 focus:outline-none pointer-events-auto">
                    <img src="/01.Badge_52ad415e46.webp" alt="Huy hiệu chứng nhận sản phẩm chính hãng bởi Osmo" class="w-full h-full object-contain filter drop-shadow-[0_0_10px_rgba(255,255,255,0.3)]" />
                 </button>

                <EditableWrapper path="images.0" type="image" label="SỬA ẢNH CHIẾN DỊCH">
                    <div class="relative film-grain-container rounded-[2px] overflow-hidden">
                        <img
                          src="{mainImage}"
                          alt="{productName}"
                          loading="eager"
                          fetchpriority="high"
                          decoding="async"
                          class="relative z-10 w-full h-auto object-contain transition-transform duration-700 group-hover:scale-[1.03] cinematic-grading rounded-[2px]"
                        />
                        <div class="absolute inset-0 z-20 pointer-events-none film-grain-mask"></div>
                    </div>
                </EditableWrapper>

                <div class="absolute -bottom-16 left-0 right-0 flex justify-center gap-2" style="z-index: var(--z-content);">
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
                <div class="hud-metric-segment group relative pt-3 px-6 pb-3 -mx-6 transition-all duration-500 rounded-3xl border border-transparent hover:border-white/10 hover:bg-white/[0.02]" 
                     style:--idx={i}
                     onmousemove={(e) => {
                       const rect = e.currentTarget.getBoundingClientRect();
                       e.currentTarget.style.setProperty('--light-x', `${e.clientX - rect.left}px`);
                       e.currentTarget.style.setProperty('--light-y', `${e.clientY - rect.top}px`);
                     }}>
                    <!-- Premium Flashlight Effect (Brightened) -->
                    <div class="absolute inset-0 z-0 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500 overflow-hidden rounded-3xl"
                         style="background: radial-gradient(400px circle at var(--light-x, 50%) var(--light-y, 50%), rgba(13, 148, 136, 0.25), transparent 80%);">
                    </div>
                    
                    <div class="relative z-10">
                      <EditableWrapper path="metadata.hero_metrics.{i}.label" value={metric.label} label="SỬA NHÃN {i+1}">
                        <span class="text-[10px] font-black tracking-[.2em] whitespace-nowrap transition-colors duration-500"
                              class:text-luxury-copper={metric.color === 'copper'}
                              class:text-luxury-gold={metric.color === 'gold'}
                              class:text-luxury-peach={metric.color === 'peach'}
                              class:text-sakura-pink={!metric.color || metric.color === 'sakura'}>{metric.label}</span>
                      </EditableWrapper>
                      
                      <EditableWrapper path="metadata.hero_metrics.{i}.value" value={metric.value} label="SỬA GIÁ TRỊ {i+1}">
                        <h3 class="text-lg font-black tracking-normal text-white transition-colors duration-300 whitespace-nowrap"
                            class:group-hover:text-luxury-copper={metric.color === 'copper'}
                            class:group-hover:text-luxury-gold={metric.color === 'gold'}
                            class:group-hover:text-luxury-peach={metric.color === 'peach'}
                            class:group-hover:text-sakura-pink={!metric.color || metric.color === 'sakura'}>{metric.value}</h3>
                      </EditableWrapper>

                      <p class="mt-2 text-sm text-slate-400 font-medium leading-relaxed opacity-70 group-hover:opacity-100 transition-opacity metric-desc">
                        <EditableWrapper path="metadata.hero_metrics.{i}.desc" label="SỬA MÔ TẢ {i+1}" as="span">
                          {metric.desc}
                        </EditableWrapper>
                      </p>
                    </div>
                </div>
            {/each}
         </div>
      </div>
    </div>
  </div>


  <button class="hero-cta-button shadow-2xl transition-all duration-300 hover:scale-105 active:scale-95" 
          style="
            position: absolute;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 50;
            background: linear-gradient(135deg, #ea580c, #c2410c) !important;
            color: white !important;
            padding: 1rem 2.5rem !important;
            font-size: 14px !important;
            font-weight: 900 !important;
            border: none !important;
            border-radius: 9999px !important;
            box-shadow: 0 10px 30px rgba(234, 88, 12, 0.45) !important;
            letter-spacing: 0.1em;
            cursor: pointer;
          "
          onclick={scrollToQuiz}>
     <EditableWrapper path="metadata.hero_cta_text" value={ctaText} label="SỬA CHỮ NÚT BẤM" class="w-full flex justify-center">
        <div class="flex items-center gap-3 justify-center">
           <div class="elite-dot-container">
              <span class="w-2.5 h-2.5 rounded-full bg-white block animate-pulse"></span>
           </div>
           <span class="tracking-[0.2em] font-extrabold uppercase">{ctaText}</span>
           <svg class="w-5 h-5 text-white ml-1 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
           </svg>
        </div>
     </EditableWrapper>
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
