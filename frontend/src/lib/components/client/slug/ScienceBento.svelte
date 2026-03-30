<script lang="ts">
  import { resolveMediaUrl } from '$lib/state/utils';
  import type { Product } from '$lib/types';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import "./ScienceBento.css";
  
  const shopStore = getShopStore();
  
  const product = $derived(shopStore.product);
  let isViewerOpen = $state(false);

  const metadata = $derived(product?.metadata || {});
  const mechanismImage = $derived(resolveMediaUrl(metadata.science_mechanism_image || ''));
  const claim1 = $derived(metadata.science_claims?.[0] || { label: 'HỆ THỐNG // LÕI NANO-BẠC', content: 'Phá vỡ cấu trúc vi khuẩn gây mùi ngay lập tức bằng mạng lưới ion bạc tự kích hoạt.', image: '' });
  const claim2 = $derived(metadata.science_claims?.[1] || { label: 'KIỂM ĐỊNH // CHỨNG THỰC', content: '"Chúng tôi không thể thay đổi gen hay cơ địa đặc trưng của bạn. <br/> Nhưng chúng tôi cam kết: Khóa mùi tuyệt đối, giữ bạn khô thoáng và tự tin suốt 48H."' });
  const stats = $derived(metadata.science_stats || { value: '48', unit: 'H', label: 'PHÒNG NGỰ CHỦ ĐỘNG', description: '3s khô thoáng – Chạm đúng chân ái.<br/> Khóa mùi tuyệt đối, tự tin suốt ngày dài.' });
  const guarantee = $derived(metadata.science_guarantee || { icon: '💎', label: 'BẢO CHỨNG', description: 'Hoàn 100% trong 3 ngày. <br/> <span class="text-cyan-400 font-bold tracking-widest">KHÔNG CẦN TRẢ VỎ</span>.' });

  const labels = $derived({
    headline: metadata.science_headline || 'Cơ chế khoa học',
    subheadline: metadata.science_subheadline || `Công nghệ Nano Bạc Tự Thân độc bản từ ${SHOP_CONFIG.pharmacy.name}.`,
    mechanism: (metadata.science_mechanism_label as string) || 'QUY TRÌNH // PHÒNG NGỰ PHÂN TỬ',
    scan: (metadata.science_scan_label as string) || 'QUÉT_CHUYÊN_SÂU',
    viewer: (metadata.science_viewer_label as string) || 'PHÂN TÍCH // CHẾ ĐỘ: QUÉT TĨNH chuyên sâu // CHẤT LƯỢNG CAO'
  });

  const openViewer = (e: MouseEvent) => {
    e.stopPropagation();
    isViewerOpen = true;
  };
</script>

  <section id="science" class="science-viewport snap-session relative">

    <div class="science-container container mx-auto px-6 max-w-6xl pt-[var(--standard-pt)]">
      <div class="mb-8 text-center">
        <h2 class="section-title text-center text-5xl font-black uppercase md:text-7xl">
          {labels.headline}
        </h2>
        <p class="mt-4 text-sm tracking-[0.5em] text-white/30 uppercase">
          {labels.subheadline}
        </p>
      </div>

      <div class="science-layout">

        <!-- LEFT: THE INNOVATION CORE -->
        <div class="column-left">

          <!-- 1. NANO CORE (Chamfered Glass) -->
          <div class="bento-tile glass-chamfer group">
            <div class="tile-content relative h-full" style:z-index="var(--z-surface)">
              <div class="hud-mono-label">{claim1.label || 'HỆ THỐNG // LÕI NANO-BẠC'}</div>
              <div class="text-shield">
                <div class="shield-blob blob-1"></div>
                <div class="shield-blob blob-2"></div>
                <p class="text-xs leading-relaxed tracking-widest uppercase text-highlight-science">
                  {claim1.content}
                </p>
              </div>
            </div>
            <div class="capsule-visual"
                 style="background-image: url('{resolveMediaUrl(claim1.image)}');">
            </div>
            <div class="laser-line"></div>
          </div>

          <!-- 2. MECHANISM (Horizon Sharp Glass) -->
          <div role="button" tabindex="0" aria-label="Open mechanism viewer" class="bento-tile glass-horizon group cursor-pointer relative" onclick={openViewer} onkeydown={(e) => e.key === 'Enter' && openViewer(e as unknown as MouseEvent)}>
            <div class="horizon-scroll-container absolute inset-0 overflow-hidden">
              <div class="horizon-slide-wrapper">
                <img src={mechanismImage} alt="Mechanism" class="w-full h-auto" />
                <img src={mechanismImage} alt="Mechanism" class="w-full h-auto" />
              </div>
            </div>

            <!-- MINIMALIST SCAN BUTTON -->
            <div class="absolute inset-x-0 bottom-12 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-700 translate-y-4 group-hover:translate-y-0" style:z-index="var(--z-layout-header)">
               <div class="hud-view-dot flex flex-col items-center gap-2">
                  <div class="w-12 h-12 rounded-full border border-white/20 backdrop-blur-xl flex items-center justify-center group/btn active:scale-95 transition-transform">
                     <svg class="w-5 h-5 text-emerald-400 group-hover/btn:scale-125 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                     </svg>
                  </div>
                  <div class="text-[8px] font-black tracking-[0.6em] text-emerald-400/50 uppercase">{labels.scan}</div>
               </div>
            </div>

            <div class="tile-content absolute bottom-12 left-12" style:z-index="var(--z-surface)">
              <div class="hud-mono-label mb-0 opacity-50">{labels.mechanism}</div>
            </div>
          </div>
        </div>

        <!-- RIGHT: THE TRUST SYSTEM -->
        <div class="column-right">

          <!-- 3. ADMISSION (Organic Blob) -->
          <div class="bento-tile glass-organic">
            <div class="tile-content">
              <div class="hud-mono-label opacity-20">{claim2.label || 'KIỂM ĐỊNH // CHỨNG THỰC'}</div>
              <blockquote class="quote-master">
                {@html claim2.content}
              </blockquote>
            </div>
          </div>

          <!-- 4. STATS (Pill Island) -->
          <div class="bento-tile glass-island">
            <div class="stats-content text-center">
              <div class="flex items-baseline justify-center">
                <span class="stats-value-giant">{stats.value}</span>
                <span class="stats-unit-cyan">{stats.unit}</span>
              </div>
              <div class="hud-mono-label mt-4 mb-0">{stats.label}</div>
              <p class="mt-6 text-[10px] leading-relaxed tracking-widest text-white/30 uppercase">
                {@html stats.description}
              </p>
            </div>
          </div>

          <!-- 5. GUARANTEE (Gem Cut Diamond) -->
          <div class="bento-tile glass-gem">
            <div class="guarantee-content">
              <div class="flex items-center gap-4 mb-4">
                <span class="text-3xl grayscale brightness-200">{guarantee.icon}</span>
                <span class="hud-mono-label mb-0 text-white opacity-80 text-lg">{guarantee.label}</span>
              </div>
              <p class="text-sm leading-relaxed text-slate-400">
                {@html guarantee.description}
              </p>
            </div>
          </div>

        </div>

      </div>
    </div>

    <!-- FULL SCREEN IMAGE VIEWER (Ultra Premium) -->
    {#if isViewerOpen}
      <div
        role="presentation"
        class="fixed inset-0 flex items-center justify-center p-8 bg-[#020617]/90 backdrop-blur-3xl animate-in fade-in duration-700"
        style:z-index="var(--z-sticky-header)"
        onclick={() => isViewerOpen = false}
      >
        <button
          class="absolute top-12 right-12 text-white/40 hover:text-white transition-colors"
          style:z-index="var(--z-hud-service)"
          onclick={() => isViewerOpen = false}
          aria-label="Close image viewer"
        >
          <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div class="relative w-full max-w-5xl h-[85vh] rounded-[2rem] overflow-hidden border border-white/10 shadow-[0_50px_100px_rgba(0,0,0,0.8)] bg-[#020617] flex items-center justify-center">
           <div class="w-full h-full overflow-y-auto custom-scrollbar">
              <img src={mechanismImage} alt={metadata.science_mechanism_image_alt || 'Mechanism Analysis'} class="w-full h-auto block" />
           </div>
           <!-- OVERLAYS FOR VIEWER -->
           <div class="absolute inset-0 pointer-events-none ring-1 ring-inset ring-white/10 rounded-[2rem]"></div>
           <div class="absolute bottom-12 left-12 hud-mono-label opacity-100 text-emerald-400">{labels.viewer}</div>
        </div>
      </div>
    {/if}
    <!-- Dynamic Line Wave Divider - Technical Science! -->
  <div class="wave-container">
    <svg viewBox="0 0 1440 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
      <defs>
        <linearGradient id="wave-gradient-science" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#3b82f6" stop-opacity="0" />
          <stop offset="50%" stop-color="#22d3ee" stop-opacity="1" />
          <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
        </linearGradient>
      </defs>
      <!-- Complex, interference-like patterns -->
      <path class="wave-line opacity-40" d="M0,160 Q360,60 720,160 T1440,160" />
      <path class="wave-line opacity-20" d="M0,160 Q360,260 720,160 T1440,160" />
      <path class="wave-line" d="M0,160 C180,100 360,220 540,160 C720,100 900,220 1080,160 C1260,100 1440,220 1440,160" />
      <path class="wave-line secondary" d="M0,160 C180,220 360,100 540,160 C720,220 900,100 1080,160 C1260,220 1440,100 1440,160" />
    </svg>
  </div>
</section>
