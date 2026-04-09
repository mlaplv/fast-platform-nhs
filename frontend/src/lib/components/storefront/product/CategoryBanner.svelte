<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import { onMount } from 'svelte';
  import { fly, fade, scale } from 'svelte/transition';
  import { backOut } from 'svelte/easing';

  interface Product {
    id: string;
    name: string;
    price: number;
    image: string;
    sales?: number;
    originalPrice?: number;
  }

  interface Props {
    products: Product[];
  }

  let { products = [] }: Props = $props();

  // Slide State
  let currentSlide = $state(0);
  let slideTimer: ReturnType<typeof setInterval>;
  
  // Lấy 4 sản phẩm đầu tiên làm featured
  const featuredSlides = $derived(() => {
    return products.slice(0, 4).map((p, i) => ({
      ...p,
      originalPrice: p.originalPrice || p.price * 1.55,
      sales: p.sales || 1200 + (i * 45)
    }));
  });

  const specs = [
    { label: 'Đánh Giá AI', value: '9.9/10', color: 'text-orange-500' },
    { label: 'Đã Xác Thực', value: 'Trợ Lý Cao Cấp', color: 'text-blue-500' },
    { label: 'Tình Trạng', value: 'Loại A+', color: 'text-emerald-500' }
  ];

  function nextSlide() {
    if (featuredSlides().length > 0) {
      currentSlide = (currentSlide + 1) % featuredSlides().length;
    }
  }

  onMount(() => {
    slideTimer = setInterval(nextSlide, 8000);
    return () => clearInterval(slideTimer);
  });
</script>

<div class="category-banner relative h-[400px] md:h-[450px] overflow-hidden bg-white/50 backdrop-blur-3xl border-b border-black/[0.03]">
  
  <!-- Subtle Background Glow -->
  <div class="absolute -top-24 -left-20 w-[400px] h-[400px] bg-[#ee4d2d]/5 rounded-full blur-[100px] animate-pulse pointer-events-none"></div>
  <div class="absolute inset-0 bg-gradient-to-br from-[#C18F7E]/5 via-white to-white pointer-events-none"></div>

  {#if featuredSlides().length > 0}
    {#each featuredSlides() as slide, i}
      {#if currentSlide === i}
        <div 
            in:fade={{duration: 800}} 
            out:fade={{duration: 600}}
            class="absolute inset-0 flex items-center justify-between px-8 md:px-24 transition-all z-10"
        >
          <!-- Content Left -->
          <div class="relative z-10 flex flex-col gap-4 max-w-[55%]">
            <div in:fly={{y: 20, duration: 1000, delay: 200}} class="flex items-center gap-3">
                <span class="bg-[#C18F7E]/10 text-[#C18F7E] text-[8px] font-black px-2 py-1 uppercase tracking-widest border border-[#C18F7E]/20">Micsmo Elite Choice</span>
                <div class="h-px w-8 bg-black/10"></div>
                <span class="text-black/30 text-[7px] font-black uppercase tracking-[0.3em]">Hàng hiếm có sẵn</span>
            </div>
            
            <div in:fade={{duration: 800, delay: 300}} class="flex flex-col">
                <h2 class="text-2xl md:text-4xl font-black leading-tight uppercase tracking-tight line-clamp-2 bg-gradient-to-br from-black via-gray-700 to-[#C18F7E] bg-clip-text text-transparent italic">
                    {slide.name}
                </h2>
            </div>

            <div in:fly={{y: 30, duration: 1000, delay: 500}} class="flex items-center gap-8">
                <div class="flex flex-col">
                    <div class="flex items-center gap-3 mb-1">
                        <span class="text-sm font-bold text-gray-300 line-through tabular-nums decoration-gray-400/20">
                            đ{Math.round(slide.originalPrice!).toLocaleString('vi-VN')}
                        </span>
                        <span class="text-[9px] text-[#ee4d2d] font-black uppercase tracking-widest animate-pulse">−55%</span>
                    </div>
                    <span class="text-black text-3xl font-black tabular-nums tracking-tighter flex items-end gap-1">
                        <span class="text-[#C18F7E] text-xl mb-1">đ</span>{slide.price.toLocaleString('vi-VN')}
                    </span>
                </div>
                <div class="w-px h-8 bg-black/5"></div>
                <div class="flex flex-col">
                    <span class="text-[8px] font-black uppercase tracking-[0.2em] text-black/20 mb-1">Đã tin dùng</span>
                    <span class="text-black text-lg font-black italic">+{slide.sales?.toLocaleString()}</span>
                </div>
            </div>
            
            <div in:fly={{y: 40, duration: 1000, delay: 700}} class="flex flex-col gap-3">
                <button 
                    onclick={() => goto(`/${slugify(slide.name)}`)}
                    class="group/btn relative w-fit px-12 py-4 bg-black text-white text-[10px] font-black uppercase tracking-[0.3em] overflow-hidden transition-all active:scale-95 shadow-xl"
                >
                    <span class="relative z-10">Sở Hữu Ngay</span>
                    <div class="absolute inset-0 bg-[#C18F7E] translate-y-full group-hover/btn:translate-y-0 transition-transform duration-500 ease-out"></div>
                </button>
            </div>
          </div>
          
          <!-- IMAGE RIGHT: Floating Badges -->
          <div class="absolute right-0 top-0 w-[45%] h-full flex items-center justify-center pointer-events-none">
            <div 
                in:scale={{duration: 1500, start: 0.9, easing: backOut, delay: 400}}
                class="relative h-[85%] w-[85%] flex items-center justify-center"
            >
                <div class="absolute inset-0 bg-[#ee4d2d]/5 blur-[80px] rounded-full animate-pulse"></div>
                
                {#each specs as spec, idx}
                    <div in:fly={{x: 30, duration: 1000, delay: 800 + (idx * 200)}} 
                         class="absolute z-20 px-3 py-1.5 bg-white/90 backdrop-blur-xl border border-white shadow-xl flex flex-col gap-0.5 animate-float-spec" 
                         style="top: {20 + (idx * 20)}%; right: {5 + (idx % 2 * 8)}%; animation-delay: {idx * 1.5}s">
                        <span class="text-[7px] font-black uppercase tracking-[0.1em] text-black/30">{spec.label}</span>
                        <span class="text-[9px] font-black {spec.color}">{spec.value}</span>
                    </div>
                {/each}

                <div in:fly={{x: -30, duration: 1000, delay: 1200}} 
                     class="absolute z-20 bottom-[20%] left-[8%] px-3 py-2 bg-black text-white flex items-center gap-2 shadow-xl">
                    <div class="h-1.5 w-1.5 rounded-full bg-green-500"></div>
                    <span class="text-[8px] font-black uppercase tracking-[0.2em]">Chính hãng</span>
                </div>

                <img 
                    src={slide.image} 
                    alt={slide.name} 
                    class="relative z-10 max-h-full object-contain filter drop-shadow-2xl animate-float-3d" 
                />
            </div>
          </div>
        </div>
      {/if}
    {/each}

    <!-- Indicators -->
    <div class="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-3 z-40">
        {#each featuredSlides() as _, i}
            <button 
                onclick={() => (currentSlide = i)}
                class="h-1 transition-all duration-700 {currentSlide === i ? 'w-8 bg-[#C18F7E]' : 'w-4 bg-black/10'}"
            ></button>
        {/each}
    </div>
  {/if}
</div>

<style>
  @keyframes float3d {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(-15px) rotate(2deg); }
  }
  .animate-float-3d { animation: float3d 6s infinite ease-in-out; }

  @keyframes floatSpec {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(5px, -10px); }
  }
  .animate-float-spec { animation: floatSpec 5s infinite ease-in-out; }
</style>
