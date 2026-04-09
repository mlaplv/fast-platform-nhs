<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import { onMount } from 'svelte';
  import { fly, fade, scale } from 'svelte/transition';
  import { cubicOut, backOut } from 'svelte/easing';

  interface Product {
    id: string;
    name: string;
    price: number;
    image: string;
    sales?: number;
    tags?: string[];
    isAiPick?: boolean;
    createdAt?: Date;
    originalPrice?: number;
  }

  interface Props {
    products: Product[];
  }

  let { products = [] }: Props = $props();

  // Year Logic
  const currentYear = new Date().getFullYear();

  // Tab State
  type TabType = 'ai' | 'latest' | 'popular' | 'bestseller';
  let activeTab = $state<TabType>('ai');

  const tabs = [
    { id: 'ai', label: 'Gợi ý AI', icon: '✨' },
    { id: 'latest', label: 'Mới nhất', icon: '🕒' },
    { id: 'popular', label: 'Phổ biến', icon: '🔥' },
    { id: 'bestseller', label: 'Bán chạy', icon: '🏆' }
  ] as const;

  // Synthesis Extended Data
  const extendedCatalog = $derived(() => {
    if (products.length === 0) return [];
    const base = [...products];
    const extended: Product[] = [];
    tabs.forEach((tab) => {
      for (let i = 0; i < 6; i++) {
        const baseItem = base[i % base.length];
        extended.push({
          ...baseItem,
          id: `${tab.id}-${i}`,
          name: `${baseItem.name} ${tab.label} Cao Cấp`,
          price: baseItem.price + (i * 2000),
          originalPrice: (baseItem.price + (i * 2000)) * 1.55, // 55% higher for massive bargain feel
          sales: 1200 + (i * 45),
          stockPercent: 70 + (i * 5) % 30, // Random stock filler for FOMO
          isAiPick: tab.id === 'ai' || i === 0,
        });
      }
    });
    return extended;
  });

  // Filtered Products
  let currentProducts = $derived(() => {
    return extendedCatalog().filter(p => p.id.startsWith(activeTab));
  });

  // Slide State
  let currentSlide = $state(0);
  let slideTimer: ReturnType<typeof setInterval>;
  const featuredSlides = $derived(() => currentProducts().slice(0, 4));

  // Synthesize floating specs for Viral 2.3
  const specs = [
    { label: 'Đánh Giá AI', value: '9.9/10', color: 'text-orange-500' },
    { label: 'Đã Xác Thực', value: 'Trợ Lý Cao Cấp', color: 'text-blue-500' },
    { label: 'Tình Trạng', value: 'Loại A+', color: 'text-emerald-500' }
  ];

  function nextSlide() {
    currentSlide = (currentSlide + 1) % featuredSlides().length;
  }

  function prevSlide() {
    currentSlide = (currentSlide - 1 + featuredSlides().length) % featuredSlides().length;
  }

  onMount(() => {
    slideTimer = setInterval(nextSlide, 10000); // Slower auto-play
    return () => clearInterval(slideTimer);
  });

  $effect(() => {
    activeTab;
    currentSlide = 0;
  });
</script>

<!-- Viral 2.3 Cinematic Texture -->
<div class="fixed inset-0 pointer-events-none z-[9999] opacity-[0.03] mix-blend-overlay grain-texture"></div>

<section class="home-product-grid-section relative mb-[5px] overflow-visible">
  
  <!-- ENERGY MESH: Vibrant Background Glows (Viral 2.3) -->
  <div class="absolute -top-48 -left-20 w-[600px] h-[600px] bg-[#ee4d2d]/10 rounded-full blur-[120px] animate-pulse pointer-events-none"></div>
  <div class="absolute top-0 right-0 w-[500px] h-[500px] bg-orange-400/5 rounded-full blur-[150px] animate-energy-mesh pointer-events-none"></div>
  <div class="absolute -bottom-24 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-red-500/5 rounded-full blur-[100px] pointer-events-none"></div>

  <!-- Minimalist Tab Header (Sticky Glass) -->
  <div class="sticky top-0 z-40 mb-2 py-1 px-1 bg-[#f5f5f5]/80 backdrop-blur-[30px] border-b border-black/[0.03] flex items-center justify-between transition-all duration-700">
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
            <span class="text-[12px] font-black uppercase tracking-[0.4em] transition-all duration-500
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

    <!-- Engine Status 2.3 -->
    <div class="hidden xl:flex items-center gap-3 px-6 py-2 bg-white/50 backdrop-blur-md rounded-full border border-white ring-1 ring-black/[0.03] mr-6 group/engine pointer-events-auto">
      <div class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
      </div>
      <span class="text-[9px] font-black uppercase tracking-[0.5em] text-black">Xu hướng Viral {currentYear}</span>
    </div>
  </div>

  <!-- FEATURED SLIDE: Viral 2.3 Immersive Max-out -->
  <div class="mb-6 relative group/slide h-[450px] md:h-[500px] overflow-hidden rounded-none shadow-[0_60px_100px_-20px_rgba(0,0,0,0.08)] bg-white/50 backdrop-blur-3xl ring-1 ring-black/[0.02]">
    
    <!-- BACKGROUND DECAL: Large Vertical Typography (Viral 2.3) -->
    <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none select-none opacity-5">
      <span class="text-[150px] font-black uppercase tracking-tighter leading-none [writing-mode:vertical-lr] rotate-180">Micsmo</span>
    </div>
    <div class="absolute inset-y-0 right-4 flex items-center pointer-events-none select-none opacity-[0.03]">
      <span class="text-[200px] font-black uppercase tracking-tighter leading-none [writing-mode:vertical-lr]">{currentYear}</span>
    </div>

    <!-- Slides Stack -->
    {#each featuredSlides() as slide, i}
      {#if currentSlide === i}
        <div 
            in:fade={{duration: 2000}} 
            out:fade={{duration: 1500}}
            class="absolute inset-0 flex items-center justify-between px-8 md:px-12 transition-all"
        >
          <!-- Content Left -->
          <div class="relative z-10 flex flex-col gap-8 max-w-[55%]">
            <div in:fly={{y: 20, duration: 1500, delay: 400}} class="flex items-center gap-4">
                <span class="bg-[#ee4d2d] text-white text-[10px] font-black px-3 py-1.5 uppercase tracking-widest shadow-[0_10px_20px_rgba(238,77,45,0.2)]">Lựa Chọn Xu Hướng</span>
                <span class="text-black/30 text-[9px] font-black uppercase tracking-[0.4em]">Xếp Hạng #1 Xu Hướng</span>
            </div>
            
            <div in:fly={{y: 30, duration: 1500, delay: 600}} class="flex flex-col gap-2">
                <h2 class="text-4xl md:text-6xl font-black leading-[0.85] uppercase tracking-tighter line-clamp-2">
                    <span class="bg-gradient-to-r from-black via-black/80 to-[#ee4d2d] bg-clip-text text-transparent">{slide.name.split(' ').slice(0,-1).join(' ')}</span><br/>
                    <span class="text-[#ee4d2d] italic">{slide.name.split(' ').slice(-1)}</span>
                </h2>
            </div>

            <div in:fly={{y: 40, duration: 1500, delay: 800}} class="flex items-center gap-10">
                <div class="flex flex-col">
                    <div class="flex items-center gap-4 mb-2">
                        <span class="text-[10px] font-black uppercase tracking-[0.3em] text-black/20">Giá Micsmo</span>
                        {#if slide.originalPrice}
                            <div class="flex items-center gap-2">
                                <span class="text-base font-bold text-gray-300 line-through tabular-nums italic decoration-gray-400/30">
                                    đ{Math.round(slide.originalPrice).toLocaleString('vi-VN')}
                                </span>
                                <span class="bg-[#ee4d2d] text-white text-[10px] font-black px-2 py-0.5 rounded-sm animate-pulse">-55%</span>
                            </div>
                        {/if}
                    </div>
                    <span class="text-black text-4xl font-black tabular-nums tracking-tighter drop-shadow-sm flex items-end gap-2">
                        <span class="text-[#ee4d2d] text-2xl mb-1">đ</span>{slide.price.toLocaleString('vi-VN')}
                        <span class="text-[10px] text-green-500 font-bold uppercase tracking-widest mb-1.5 animate-bounce">⚡ Tiết kiệm cực lớn</span>
                    </span>
                </div>
                <div class="w-[1px] h-12 bg-black/5"></div>
                <div class="flex flex-col">
                    <span class="text-[10px] font-black uppercase tracking-[0.3em] text-black/20 mb-1">Đã bán</span>
                    <span class="text-black text-xl font-black italic">+{slide.sales.toLocaleString()} <span class="text-[10px] opacity-30 not-italic uppercase ml-1">Sản phẩm</span></span>
                </div>
            </div>
            
            <div in:fly={{y: 50, duration: 1500, delay: 1000}}>
                <button 
                    onclick={() => goto(`/${slugify(slide.name)}`)}
                    class="group/btn relative px-14 py-6 mt-6 bg-black text-white text-[11px] font-black uppercase tracking-[0.6em] overflow-hidden transition-all active:scale-95 shadow-[0_20px_40px_rgba(0,0,0,0.1)] hover:shadow-[0_30px_60px_rgba(238,77,45,0.3)]"
                >
                    <span class="relative z-10 transition-colors group-hover/btn:text-white">Sắm Ngay ✨</span>
                    <div class="absolute inset-0 bg-gradient-to-r from-[#ee4d2d] to-[#ff7337] -translate-x-full group-hover/btn:translate-x-0 transition-transform duration-1000 ease-in-out"></div>
                    <div class="absolute top-0 left-0 w-full h-[1px] bg-white/20 translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-1500"></div>
                </button>
            </div>
          </div>
          
          <!-- IMAGE RIGHT: Floating Tech Badges (Viral 2.3) -->
          <div class="absolute right-0 top-0 w-[50%] h-full flex items-center justify-center pointer-events-none">
            <div 
                in:scale={{duration: 2000, start: 0.9, easing: backOut, delay: 400}}
                class="relative h-[80%] w-[80%] flex items-center justify-center atmospheric-image-container"
            >
                <!-- Energy Pulse Glow -->
                <div class="absolute inset-0 bg-[#ee4d2d]/10 blur-[100px] rounded-full animate-pulse opacity-50"></div>
                
                <!-- Floating Glass Spec Cards -->
                {#each specs as spec, idx}
                    <div in:fly={{x: 50, duration: 1500, delay: 1200 + (idx * 300)}} 
                         class="absolute z-20 px-4 py-2 bg-white/90 backdrop-blur-xl border border-white shadow-2xl flex flex-col gap-0.5 animate-float-spec" 
                         style="top: {15 + (idx * 25)}%; right: {5 + (idx % 2 * 10)}%; animation-delay: {idx * 2}s">
                        <span class="text-[8px] font-black uppercase tracking-[0.2em] text-black/30">{spec.label}</span>
                        <span class="text-[11px] font-black {spec.color}">{spec.value}</span>
                    </div>
                {/each}

                <div in:fly={{x: -50, duration: 1500, delay: 1800}} 
                     class="absolute z-20 bottom-[15%] left-[5%] px-4 py-3 bg-black text-white flex items-center gap-3 shadow-2xl">
                    <div class="h-2 w-2 rounded-full bg-green-500"></div>
                    <span class="text-[9px] font-black uppercase tracking-[0.3em]">Xác nhận Chính hãng</span>
                </div>

                <img 
                    src={slide.image} 
                    alt={slide.name} 
                    class="relative z-10 max-h-full object-contain filter drop-shadow-[0_40px_100px_rgba(0,0,0,0.15)] animate-float-3d" 
                />
                
                <!-- Floor Projection -->
                <div class="absolute bottom-[-5%] w-[120%] h-[15%] bg-black/[0.05] blur-[40px] rounded-full scale-y-[0.3]"></div>
            </div>
          </div>
        </div>
      {/if}
    {/each}

    <!-- Hidden Edge Controls -->
    <div class="absolute inset-y-0 left-0 w-32 flex items-center justify-center group/nav opacity-0 hover:opacity-100 transition-opacity z-30 cursor-pointer" onclick={prevSlide}>
        <div class="w-[1px] h-24 bg-black/10 transition-all group-hover/nav:h-32 group-hover/nav:bg-black"></div>
        <span class="absolute left-12 text-xs font-black uppercase tracking-[0.5em] -rotate-90 origin-left opacity-0 group-hover/nav:opacity-100 transition-all">Trước</span>
    </div>
    <div class="absolute inset-y-0 right-0 w-32 flex items-center justify-center group/nav opacity-0 hover:opacity-100 transition-opacity z-30 cursor-pointer" onclick={nextSlide}>
        <div class="w-[1px] h-24 bg-black/10 transition-all group-hover/nav:h-32 group-hover/nav:bg-black"></div>
        <span class="absolute right-12 text-xs font-black uppercase tracking-[0.5em] rotate-90 origin-right opacity-0 group-hover/nav:opacity-100 transition-all">Tiếp</span>
    </div>

  </div>

  <!-- VIRAL SLIDER V2.7: Single Row Carousel -->
  <div class="flex overflow-x-auto no-scrollbar scroll-smooth gap-2 px-1 md:px-0 pb-10">
    {#each currentProducts() as product (product.id)}
      <button
        onclick={() => goto(`/${slugify(product.name)}`)}
        class="group/card relative flex-shrink-0 w-[calc((100%-6px)/2)] md:w-[calc((100%-6px)/4)] lg:w-[calc((100%-6px)/4)] bg-white border border-black/5 hover:border-black transition-all duration-700 cursor-pointer text-left flex flex-col active:scale-[0.98] shadow-sm hover:shadow-2xl"
      >
        <div class="aspect-square w-full relative overflow-hidden bg-[#fafafa]">
          {#if product.isAiPick}
            <div class="absolute top-3 left-3 z-20">
                <span class="bg-gradient-to-r from-[#ff4d4d] via-[#f9cb28] to-[#ff4d4d] text-black text-[9px] font-black px-3 py-1.5 uppercase tracking-widest shadow-[0_8px_16px_rgba(255,77,77,0.4)] flex items-center gap-2 border border-white/20">
                    <span class="animate-pulse">🔥</span> CỰC HỜI -35%
                </span>
            </div>
            <!-- Neural Spectral Glow (Viral 2.8) -->
            <div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#A855F7] via-[#3B82F6] to-[#14B8A6] z-10 opacity-70"></div>
          {/if}

          <!-- Glass Refraction Overlay (Viral 2.3) -->
          <div class="absolute inset-0 bg-gradient-to-tr from-transparent via-white/40 to-transparent -translate-x-full group-hover/card:translate-x-full transition-transform duration-1000 z-10 pointer-events-none"></div>

          <img
            src={product.image}
            alt={product.name}
            class="w-full h-full object-cover transition-all duration-1000 group-hover/card:scale-110 group-hover/card:rotate-2"
            loading="lazy"
          />
        </div>

        <div class="p-6 flex flex-col flex-1 bg-white relative">
          <h3 class="text-black text-[14px] font-black uppercase tracking-tight line-clamp-2 h-[42px] leading-[21px] mb-5 group-hover/card:text-[#ee4d2d] transition-colors">{product.name}</h3>

          <div class="mt-auto pt-4 border-t border-black/[0.03] space-y-3">
            <div class="flex flex-col gap-1">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        {#if product.originalPrice}
                            <span class="text-[11px] font-bold text-gray-300 line-through tabular-nums decoration-gray-400/20">
                                đ{Math.round(product.originalPrice).toLocaleString('vi-VN')}
                            </span>
                        {/if}
                        <span class="text-[10px] font-black text-[#ee4d2d] bg-[#ee4d2d]/10 px-1.5 py-0.5 rounded-sm">-35%</span>
                    </div>
                    <span class="text-[9px] font-black text-[#ee4d2d] animate-pulse flex items-center gap-1">
                        <div class="w-1 h-1 rounded-full bg-[#ee4d2d]"></div> ĐANG CHÁY HÀNG
                    </span>
                </div>
                <p class="text-[#ee4d2d] font-black text-2xl tracking-tighter tabular-nums flex items-end gap-1">
                    <span class="text-sm mb-1">đ</span>{product.price.toLocaleString('vi-VN')}
                </p>
            </div>

            <!-- STOCK PROGRESS: FOMO Max -->
            <div class="relative w-full h-4 bg-[#ee4d2d]/5 rounded-full overflow-hidden flex items-center justify-center border border-[#ee4d2d]/10">
                <div class="absolute inset-0 bg-gradient-to-r from-[#ee4d2d] to-[#ffaa00] transition-all duration-1000" style="width: {product.stockPercent}%"></div>
                <span class="relative z-10 text-[8px] font-black text-[#ee4d2d] mix-blend-multiply uppercase tracking-widest flex items-center gap-1">
                    <svg class="w-2 h-2" fill="currentColor" viewBox="0 0 20 20"><path d="M12 2a1 1 0 01.894.553L17.382 11H13v6a1 1 0 01-1.894.447l-5-10A1 1 0 017 6h4V2z"/></svg>
                    Đã bán {product.sales}
                </span>
                <!-- Progress Glitch Effect -->
                <div class="absolute inset-0 bg-white/20 w-1/3 skew-x-[-20deg] animate-gliding-light pointer-events-none"></div>
            </div>
          </div>
        </div>
      </button>
    {/each}
  </div>

  <!-- ULTIMATE BRAND FLOOR (Viral 2.6 Refined) -->
  <div class="mt-[8px] mb-1 flex flex-col items-center">
    <button 
        onclick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        class="group/foot relative py-1 px-6 overflow-hidden active:scale-95 transition-all"
    >
        <span class="relative z-10 text-[11px] font-black uppercase tracking-[0.4em] text-black/40 group-hover/foot:text-black group-hover/foot:tracking-[0.5em] transition-all duration-700 flex items-center gap-4">
            Xem thêm
            <svg class="w-4 h-4 opacity-20 group-hover/foot:opacity-100 group-hover/foot:translate-x-2 transition-all duration-700" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
        </span>
        <!-- Subtle Underline Ghost -->
        <div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-[1px] bg-black/10 group-hover/foot:w-full transition-all duration-1000"></div>
    </button>
  </div>
</section>

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

  /* 3D Floating Product */
  @keyframes float3d {
    0%, 100% { transform: translateY(0) rotate(0deg) scale(1.02); }
    50% { transform: translateY(-30px) rotate(3deg) scale(1); }
  }
  .animate-float-3d { animation: float3d 8s infinite ease-in-out; }

  /* Floating Spec Cards */
  @keyframes floatSpec {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(10px, -15px); }
  }
  .animate-float-spec { animation: floatSpec 6s infinite ease-in-out; }

  /* Energy Mesh Glow */
  @keyframes energyMesh {
    0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.5; }
    50% { transform: translate(-50px, 30px) scale(1.2); opacity: 0.8; }
  }
  .animate-energy-mesh { animation: energyMesh 25s infinite ease-in-out; }

  /* Gliding Light Effect */
  @keyframes glidingLight {
    from { transform: translateX(-100%) skewX(-20deg); }
    to { transform: translateX(400%) skewX(-20deg); }
  }
  .animate-gliding-light { animation: glidingLight 3s infinite linear; }

  .atmospheric-image-container {
    perspective: 1000px;
  }
</style>
