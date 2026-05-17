<script lang="ts">
  /**
   * HOME PRODUCT GRID - ELITE V2.2 OPTIMIZED
   * Compliance: Svelte 5 Runes, Static Typing 100%, No Sticky Tab (UX Fix)
   */
  import { goto } from '$app/navigation';
  import { slugify, trimProductName, formatCurrency } from '$lib/utils/format';
  import { onMount, onDestroy } from 'svelte';
  import { fly, fade, scale } from 'svelte/transition';
  import { cubicOut, backOut } from 'svelte/easing';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  /**
   * INTERFACES (Elite Static Typing)
   */
  interface Product {
    id: string;
    name: string;
    price: number;
    image: string;
    slug?: string;
    sales?: string | number;
    tags?: string[];
    isAiPick?: boolean;
    createdAt?: Date;
    originalPrice?: number;
    originalSlug?: string;
    discountPercent?: number;
    stock?: number;
    stockPercent?: number;
    // Tầng dữ liệu thô từ API
    discountPrice?: number;
    orderCount?: number;
    order_count?: number;
    orderCountText?: string;
    order_count_text?: string;
    metadata?: {
      image_url?: string;
      reviews_count_text?: string;
    };
    images?: string[];
    isAiFeatured?: boolean;
  }

  interface Props {
    products: Product[];
    productsAi?: Product[];
  }

  let { products = [], productsAi = [] }: Props = $props();

  /**
   * TAB LOGIC
   */
  type TabType = 'ai' | 'latest' | 'popular' | 'bestseller';
  let activeTab: TabType = $state('ai');

  const tabs = [
    { id: 'ai', label: 'Gợi ý AI', icon: '✨' },
    { id: 'latest', label: 'Mới nhất', icon: '🕒' },
    { id: 'popular', label: 'Phổ biến', icon: '🔥' },
    { id: 'bestseller', label: 'Bán chạy', icon: '🏆' }
  ] as const;

  /**
   * ELITE NORMALIZER - Chuyển đổi dữ liệu thô sang chuẩn Elite UI
   */
  const normalizeProduct = (p: Product, tabId: string): Product => {
    const hasDiscount: boolean = !!p.discountPrice && p.discountPrice < p.price;
    const sellingPrice: number = hasDiscount ? p.discountPrice! : p.price;
    const originalPrice: number = hasDiscount ? p.price : (p.price * 1.4);
    const realSalesCount: number = p.orderCount || p.order_count || 0;
    const displaySales: string = p.orderCountText || p.order_count_text || p.metadata?.reviews_count_text || (realSalesCount > 0 ? `${realSalesCount.toLocaleString()}+` : "0");
    
    const imgCandidates: (string | undefined)[] = [
        ...(Array.isArray(p.images) ? p.images : []),
        p.metadata?.image_url,
        '/placeholder_video.webp'
    ];
    const primaryImage: string = imgCandidates.find(img => img && typeof img === 'string' && img.length > 0) || '/placeholder_video.webp';
    
    const discountPercent: number = originalPrice > 0 ? Math.round(((originalPrice - sellingPrice) / originalPrice) * 100) : 0;
    const cleanName: string = trimProductName(p.name);

    return {
      ...p,
      id: `${tabId}-${p.id}`,
      name: cleanName,
      image: primaryImage,
      price: sellingPrice,
      originalPrice: originalPrice,
      discountPercent: discountPercent,
      sales: displaySales,
      stockPercent: (p.stock ?? 0) > 0 ? 100 : 0,
      isAiPick: tabId === 'ai',
      originalSlug: p.slug
    };
  };

  /**
   * REACTIVE CATALOG (Svelte 5 $derived)
   */
  const extendedCatalog: Product[] = $derived(
    tabs.flatMap((tab) => {
      const currentLimit = tab.id === activeTab ? visibleLimit : 10;
      const endSlice = currentLimit + 1;
      if (tab.id === 'ai' && productsAi.length > 0) {
        return productsAi.slice(1, endSlice).map((p) => normalizeProduct(p, 'ai'));
      } else if (products.length > 0) {
        return products.slice(1, endSlice).map((p) => normalizeProduct(p, tab.id));
      }
      return [];
    })
  );

  const currentProducts: Product[] = $derived(extendedCatalog.filter(p => p.id.startsWith(activeTab)));

  const featuredSlides: Product[] = $derived(
    (productsAi.length > 0 ? [productsAi[0]] : products.filter(p => p.isAiFeatured).slice(0, 1))
    .map((p) => normalizeProduct(p, 'featured'))
  );

  const specs = [
    { label: 'Đánh Giá AI', value: '4.9/5', color: 'text-orange-500' },
    { label: 'Đã Xác Thực', value: 'Trợ Lý Cao Cấp', color: 'text-blue-500' },
    { label: 'Tình Trạng', value: 'Loại A+', color: 'text-emerald-500' }
  ] as const;

  /**
   * COUNTDOWN & FOMO LOGIC
   */
  let timeLeft = $state({ h: '00', m: '00', s: '00' });
  const SALE_SESSIONS: number[] = [0, 9, 12, 15, 18, 21];

  function updateCountdown(): void {
    const now: Date = new Date();
    const currentHour: number = now.getHours();
    
    let nextSessionHour: number | undefined = SALE_SESSIONS.find(h => h > currentHour);
    let targetDate: Date = new Date(now);
    
    if (nextSessionHour === undefined) {
      nextSessionHour = 0;
      targetDate.setDate(targetDate.getDate() + 1);
    }
    
    targetDate.setHours(nextSessionHour, 0, 0, 0);
    
    const diff: number = Math.max(0, targetDate.getTime() - now.getTime());
    timeLeft = {
      h: Math.floor(diff / (1000 * 60 * 60)).toString().padStart(2, '0'),
      m: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)).toString().padStart(2, '0'),
      s: Math.floor((diff % (1000 * 60)) / 1000).toString().padStart(2, '0')
    };
  }

  let timerInterval: ReturnType<typeof setInterval> | undefined;

  onMount(() => {
    updateCountdown();
    timerInterval = setInterval(updateCountdown, 1000);
  });

  onDestroy(() => {
    if (timerInterval) clearInterval(timerInterval);
  });

  /**
   * LOAD MORE LOGIC - Desktop Scroll Listener (Elite V2.2)
   * Dùng window scroll thay vì IntersectionObserver vì layout desktop là
   * overflow-x-auto (scroll ngang), trigger element nằm ngay trong viewport.
   */
  let visibleLimit = $state(10);
  let autoLoaded = $state(false);
  let sectionEl = $state<HTMLElement | null>(null);

  const hasMoreProducts = $derived(
    activeTab === 'ai'
      ? productsAi.length > visibleLimit + 1
      : products.length > visibleLimit + 1
  );

  $effect(() => {
    const _ = activeTab;
    visibleLimit = 10;
    autoLoaded = false;
  });

  $effect(() => {
    if (autoLoaded || !hasMoreProducts || !sectionEl) return;

    function onScroll(): void {
      if (!sectionEl || autoLoaded) return;
      const rect = sectionEl.getBoundingClientRect();
      // Kích hoạt khi bottom của section cách đáy viewport <= 300px
      if (rect.bottom <= window.innerHeight + 300) {
        visibleLimit = 20;
        autoLoaded = true;
        window.removeEventListener('scroll', onScroll, { passive: true } as EventListenerOptions);
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });

    // Kiểm tra ngay lập tức phòng trường hợp section đã trong viewport khi mount
    onScroll();

    return () => {
      window.removeEventListener('scroll', onScroll, { passive: true } as EventListenerOptions);
    };
  });

  function handleLoadMore(): void {
    visibleLimit += 10;
  }
</script>

<section bind:this={sectionEl} class="home-product-grid-section relative mb-[5px] overflow-visible">

  <!-- Optimized Background -->
  <div class="absolute inset-0 bg-gradient-to-b from-[#ee4d2d]/5 to-transparent pointer-events-none"></div>

  <!-- Tab Header: Non-Sticky Fix (Elite UX) -->
  <nav class="relative mb-2 py-1 px-1 bg-[#f5f5f5]/80 backdrop-blur-[30px] border-b border-black/[0.03] flex items-center justify-between transition-all duration-700">
    <div class="flex flex-1 items-center justify-center md:justify-start md:gap-16 overflow-x-auto no-scrollbar scroll-smooth">
      {#each tabs as tab}
        <button
          onclick={() => (activeTab = tab.id)}
          class="relative px-8 py-5 flex flex-col items-center gap-1 group/tab transition-all duration-500"
        >
          <div class="flex items-center gap-3">
            <span class="text-lg transition-all transform duration-700 {activeTab === tab.id ? 'scale-125 opacity-100 rotate-12' : 'opacity-20 scale-100 group-hover/tab:opacity-100 group-hover/tab:-rotate-12'}">
              {tab.icon}
            </span>
            <span class="text-[12px] font-black tracking-[0.2em] transition-all duration-500
              {activeTab === tab.id ? 'text-black' : 'text-gray-400 group-hover/tab:text-gray-900'}">
              {tab.label}
            </span>
          </div>

          {#if activeTab === tab.id}
            <div 
                in:scale={{duration: 600, start: 0.8, easing: cubicOut}}
                class="absolute bottom-0 left-0 w-full h-[3px] bg-gradient-to-r from-transparent {activeTab === 'ai' ? 'via-[#A855F7] via-[#3B82F6] via-[#14B8A6]' : 'via-[#ee4d2d] via-[#ffd839] via-[#ee4d2d]'} to-transparent shadow-[0_4px_15px_rgba(168,85,247,0.3)]"
            ></div>
          {/if}
        </button>
      {/each}
    </div>

    <!-- Elite Brand Indicator -->
    <div class="hidden xl:flex items-center gap-3 px-6 py-2 bg-white/50 backdrop-blur-md border border-gray-100 mr-6 pointer-events-none">
      <span class="text-[10px] font-black tracking-[0.2em] text-[#C18F7E]">Bộ sưu tập Thượng lưu 2026</span>
    </div>
  </nav>

  <!-- FEATURED SLIDE -->
  <div class="mb-6 relative group/slide h-[450px] md:h-[500px] overflow-hidden shadow-[0_60px_100px_-20px_rgba(0,0,0,0.08)] bg-white/50 backdrop-blur-3xl ring-1 ring-black/[0.02]">
    
    <div class="absolute inset-0 bg-gradient-to-br from-[#C18F7E]/5 via-white to-white pointer-events-none"></div>

    {#each featuredSlides as slide}
      <div 
          in:fade={{duration: 800}} 
          class="absolute inset-0 flex items-center justify-between px-8 md:px-12 transition-all"
          style:z-index={Z_INDEX_CLIENT.CONTENT}
      >
        <!-- Content Left -->
        <div class="relative z-10 flex flex-col gap-6 max-w-[60%]">
          <div in:fly={{y: 20, duration: 1500, delay: 400}} class="flex items-center gap-4">
              <span class="bg-[#C18F7E]/10 text-[#C18F7E] text-[10px] font-black px-3 py-1.5 tracking-tight border border-[#C18F7E]/20">Lựa chọn Tinh hoa osmo</span>
              <span class="text-black/20 text-[9px] font-black tracking-[0.2em]">Số lượng giới hạn</span>
          </div>
          
          <div in:fade={{duration: 1200, delay: 400}} class="flex flex-col">
              <h2 class="text-3xl md:text-4xl lg:text-5xl font-extrabold leading-[1.3] tracking-tight line-clamp-3 bg-gradient-to-br from-[#1A1A1A] via-[#333333] to-[#C18F7E] bg-clip-text text-transparent">
                  {slide.name}
              </h2>
          </div>

          <div in:fly={{y: 40, duration: 1500, delay: 800}} class="flex items-center gap-10">
              <div class="flex flex-col">
                  <div class="flex items-center gap-4 mb-1">
                      <span class="text-[10px] font-black tracking-[0.1em] text-black/20">Đặc quyền osmo</span>
                      {#if slide.originalPrice}
                          <span class="text-sm font-bold text-gray-300 line-through tabular-nums decoration-gray-400/30">
                              {formatCurrency(Math.round(slide.originalPrice))}
                          </span>
                      {/if}
                  </div>
                  <span class="text-[#ee4d2d] text-4xl font-black tabular-nums tracking-tighter flex items-end gap-2">
                      {formatCurrency(slide.price || 0)}
                      <span class="text-[10px] text-[#C18F7E] font-bold tracking-tight mb-1.5 animate-pulse">−{slide.discountPercent}% Giới hạn</span>
                  </span>
              </div>
              <div class="flex flex-col">
                  <span class="text-[10px] font-black tracking-[0.2em] text-black/20 mb-1">Cộng đồng</span>
                  <span class="text-black text-xl font-black italic">+{slide.sales || 0} <span class="text-[10px] opacity-30 not-italic ml-1">Tin dùng</span></span>
              </div>
          </div>
          
          <div in:fly={{y: 50, duration: 1500, delay: 1000}} class="flex flex-col gap-4">
              <button 
                  onclick={() => goto(`/${slide.originalSlug || slide.slug || slugify(slide.name)}`)}
                  class="group/btn relative w-fit px-20 py-6 bg-black text-white text-[12px] font-black tracking-[0.2em] overflow-hidden transition-all active:scale-95 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.3)] hover:shadow-[0_40px_80px_-15px_rgba(193,143,126,0.4)]"
              >
                  <span class="relative z-10 transition-colors group-hover/btn:text-white">Sở Hữu Ngay</span>
                  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn:animate-shivering pointer-events-none"></div>
                  <div class="absolute inset-0 bg-[#C18F7E] translate-y-full group-hover/btn:translate-y-0 transition-transform duration-500 ease-out"></div>
              </button>
              
              <div class="flex items-center gap-2 animate-pulse">
                  <div class="h-1 w-1 rounded-full bg-[#C18F7E]"></div>
                  <span class="text-[9px] font-bold tracking-tight text-black/40">Chỉ còn 12 suất ưu đãi trong hôm nay</span>
              </div>
          </div>
        </div>
        
        <!-- IMAGE RIGHT -->
        <div class="absolute right-0 top-0 w-[50%] h-full flex items-center justify-center pointer-events-none">
          <div 
              in:scale={{duration: 2000, start: 0.9, easing: backOut, delay: 400}}
              class="relative h-[80%] w-[80%] flex items-center justify-center"
              style="perspective: 1000px"
          >
              <div class="absolute inset-0 bg-[#ee4d2d]/10 blur-[100px] rounded-full animate-pulse opacity-50"></div>
              
              {#each specs as spec, idx}
                  <div in:fly={{x: 50, duration: 1500, delay: 1200 + (idx * 300)}} 
                       class="absolute z-20 px-4 py-2 bg-white/90 backdrop-blur-xl border border-white shadow-2xl flex flex-col gap-0.5 animate-float-spec" 
                       style="top: {15 + (idx * 25)}%; right: {5 + (idx % 2 * 10)}%; animation-delay: {idx * 2}s">
                      <span class="text-[8px] font-black tracking-[0.2em] text-black/30">{spec.label}</span>
                      <span class="text-[11px] font-black {spec.color}">{spec.value}</span>
                  </div>
              {/each}

              <div in:fly={{x: -50, duration: 1500, delay: 1800}} 
                   class="absolute z-20 bottom-[15%] left-[5%] px-4 py-3 bg-black text-white flex items-center gap-3 shadow-2xl">
                  <div class="h-2 w-2 rounded-full bg-green-500"></div>
                  <span class="text-[9px] font-black tracking-[0.3em]">Xác nhận Chính hãng</span>
              </div>

              <img 
                  src={slide.image} 
                  alt={slide.name} 
                  class="relative z-10 max-h-full object-contain filter drop-shadow-[0_40px_100px_rgba(0,0,0,0.15)] animate-float-3d" 
              />
              <div class="absolute bottom-[-5%] w-[120%] h-[15%] bg-black/[0.05] blur-[40px] rounded-full scale-y-[0.3]"></div>
          </div>
        </div>
      </div>
    {/each}
  </div>

  <!-- PRODUCT LIST -->
  <div class="flex overflow-x-auto no-scrollbar scroll-smooth gap-2 px-1 md:px-0 pb-10">
    {#each currentProducts as product (product.id)}
      <button
        onclick={() => goto(`/${product.originalSlug || product.slug || slugify(product.name)}`)}
        class="group/card relative flex-shrink-0 w-[calc((100%-6px)/2)] md:w-[calc((100%-6px)/4)] lg:w-[calc((100%-6px)/4)] bg-white border border-black/5 transition-all duration-700 cursor-pointer text-left flex flex-col active:scale-[0.98] shadow-sm hover:shadow-2xl"
      >
        <div class="aspect-square w-full relative overflow-hidden bg-[#fafafa]">
          {#if product.isAiPick}
            <div class="absolute top-2 left-2 z-20 flex flex-col gap-0.5">
                <div class="bg-[#ee4d2d] text-white flex items-center shadow-[0_4px_12px_rgba(238,77,45,0.4)] overflow-hidden animate-shivering">
                    <div class="bg-black text-[8px] font-black px-1.5 py-1 flex items-center justify-center tracking-tighter italic border-r border-white/10">
                        SẮP CHÁY HÀNG
                    </div>
                    <div class="flex items-center gap-0.5 px-2 py-1 font-mono text-[10px] font-black bg-[#ee4d2d]">
                        <span class="w-4 text-center">{timeLeft.h}</span>
                        <span class="animate-pulse">:</span>
                        <span class="w-4 text-center">{timeLeft.m}</span>
                        <span class="animate-pulse">:</span>
                        <span class="w-4 text-center">{timeLeft.s}</span>
                    </div>
                </div>
                <div class="bg-white/95 backdrop-blur-md border border-[#ee4d2d]/20 text-[7px] font-black text-[#ee4d2d] px-1.5 py-0.5 w-fit tracking-[0.15em] shadow-sm">
                    Chỉ còn {Math.abs((product.id.length % 7) + 2)} suất cuối
                </div>
            </div>
            <div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#A855F7] via-[#3B82F6] to-[#14B8A6] z-10 opacity-70"></div>
          {/if}

          <div class="absolute inset-0 bg-gradient-to-tr from-transparent via-white/40 to-transparent -translate-x-full group-hover/card:translate-x-full transition-transform duration-1000 z-10 pointer-events-none"></div>

          <img
            src={product.image}
            alt={product.name}
            class="w-full h-full object-cover transition-all duration-1000 group-hover/card:scale-110 group-hover/card:rotate-2"
            loading="lazy"
          />
        </div>

        <div class="p-6 flex flex-col flex-1 bg-white relative">
          <h3 class="text-black text-[14px] font-black tracking-tight line-clamp-2 h-[42px] leading-[21px] mb-5 group-hover/card:text-[#C18F7E] transition-colors">{product.name}</h3>

          <div class="mt-auto pt-4 border-t border-black/[0.03] space-y-3">
            <div class="flex flex-col gap-1">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        {#if product.originalPrice}
                            <span class="text-[11px] font-bold text-gray-300 line-through tabular-nums decoration-gray-400/20">
                                {formatCurrency(Math.round(product.originalPrice))}
                            </span>
                        {/if}
                        <span class="text-[10px] font-black text-[#C18F7E] bg-[#C18F7E]/10 px-1.5 py-0.5">-{product.discountPercent}%</span>
                    </div>
                    <span class="text-[9px] font-black text-[#C18F7E] animate-pulse flex items-center gap-1">
                        <div class="w-1 h-1 rounded-full bg-[#C18F7E]"></div> ĐANG CHÁY HÀNG
                    </span>
                </div>
                <p class="text-[#ee4d2d] font-black text-2xl tracking-tighter tabular-nums flex items-end gap-1 group-hover/card:text-[#C18F7E] transition-colors">
                    {formatCurrency(product.price)}
                </p>
            </div>

            <div class="relative w-full h-4 bg-[#C18F7E]/5 overflow-hidden flex items-center justify-center border border-[#C18F7E]/10">
                <div class="absolute inset-0 bg-gradient-to-r from-[#C18F7E] via-[#E2B1A2] to-[#C18F7E] transition-all duration-1000" style="width: {product.stockPercent}%"></div>
                <span class="relative z-10 text-[9px] font-black text-[#C18F7E] mix-blend-multiply flex items-center gap-1">
                    <svg class="w-2 h-2" fill="currentColor" viewBox="0 0 20 20"><path d="M12 2a1 1 0 01.894.553L17.382 11H13v6a1 1 0 01-1.894.447l-5-10A1 1 0 017 6h4V2z"/></svg>
                    {product.sales.toString().includes('Đã bán') ? product.sales : `Đã bán ${product.sales}`}
                </span>
                <div class="absolute inset-0 bg-white/20 w-1/3 skew-x-[-20deg] animate-gliding-light pointer-events-none"></div>
            </div>
          </div>
        </div>
      </button>
    {/each}
  </div>


  <!-- BRAND FLOOR -->
  {#if autoLoaded && hasMoreProducts}
    <footer class="mt-[8px] mb-1 flex flex-col items-center">
      <button 
          onclick={handleLoadMore}
          class="group/foot relative py-1 px-6 overflow-hidden active:scale-95 transition-all"
      >
          <span class="relative z-10 text-[11px] font-black tracking-[0.4em] text-black/40 group-hover/foot:text-black group-hover/foot:tracking-[0.5em] transition-all duration-700 flex items-center gap-4">
              Xem thêm
              <svg class="w-4 h-4 opacity-20 group-hover/foot:opacity-100 group-hover/foot:translate-x-2 transition-all duration-700" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
          </span>
          <div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-[1px] bg-black/10 group-hover/foot:w-full transition-all duration-1000"></div>
      </button>
    </footer>
  {/if}
</section>

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

  @keyframes float3d {
    0%, 100% { transform: translateY(0) rotate(0deg) scale(1.02); }
    50% { transform: translateY(-30px) rotate(3deg) scale(1); }
  }
  .animate-float-3d { animation: float3d 8s infinite ease-in-out; }

  @keyframes floatSpec {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(10px, -15px); }
  }
  .animate-float-spec { animation: floatSpec 6s infinite ease-in-out; }

  @keyframes glidingLight {
    from { transform: translateX(-100%) skewX(-20deg); }
    to { transform: translateX(400%) skewX(-20deg); }
  }
  @keyframes shivering {
    0%, 100% { transform: scale(1); }
    10%, 20% { transform: scale(0.98) rotate(-1deg); }
    30%, 50%, 70%, 90% { transform: scale(1.02) rotate(1deg); }
    40%, 60%, 80% { transform: scale(1.02) rotate(-1deg); }
  }
  .animate-shivering { animation: shivering 0.8s infinite cubic-bezier(.36,.07,.19,.97); }
</style>
