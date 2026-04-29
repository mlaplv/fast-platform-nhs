<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify, formatCurrency, trimProductName } from '$lib/utils/format';
  import { onMount } from 'svelte';
  import { fly, fade, scale } from 'svelte/transition';
  import { backOut } from 'svelte/easing';
  import type { ReviewStats } from '$lib/types';

  import type { Product as RealProduct } from '$lib/types';
  
  interface Product extends Partial<RealProduct> {
    id: string;
    name: string;
    price: number;
    image: string;
    sales?: number;
    originalPrice?: number;
  }

  interface Props {
    product: Product | null;
  }

  let { product = null }: Props = $props();

  let stats = $state<ReviewStats | null>(null);

  onMount(async () => {
    if (product?.id) {
      try {
        const res = await fetch(`/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`);
        if (res.ok) stats = await res.json();
      } catch (e) {
        console.error('Failed to load banner stats:', e);
      }
    }
  });

  // Giá gốc tính toán nếu không có (Elite V2.2)
  const displayProduct = $derived(() => {
    if (!product) return null;
    return {
      ...product,
      name: trimProductName(product.name),
      originalPrice: product.originalPrice || product.price * 1.55,
      sales: product.orderCount || product.sales || 0,
      metadata: product.metadata || {}
    };
  });

  // Các badge thông tin từ real DB (Elite V2.2)
  const specs = $derived(() => {
    const p = displayProduct();
    if (!p) return [];
    
    return [
      { 
        label: 'Đánh Giá AI', 
        value: stats ? `${stats.average_rating.toFixed(1)}/5` : (p.metadata?.reviews_trust_score || '4.9/5'), 
        color: 'text-orange-500' 
      },
      { 
        label: 'Đã Xác Thực', 
        value: p.metadata?.offer_trust_verified_by || 'Chuyên Gia Micsmo', 
        color: 'text-blue-500' 
      },
      { 
        label: 'Tình Trạng', 
        value: p.metadata?.brand_type || 'Loại A++', 
        color: 'text-emerald-500' 
      }
    ];
  });
</script>

{#if displayProduct()}
  <div class="category-banner relative h-[400px] md:h-[450px] overflow-hidden bg-white/50 backdrop-blur-3xl border-b border-black/[0.03]">
  
  <!-- Subtle Background Glow -->
  <div class="absolute -top-24 -left-20 w-[400px] h-[400px] bg-[#ee4d2d]/5 rounded-full blur-[100px] animate-pulse pointer-events-none"></div>
  <div class="absolute inset-0 bg-gradient-to-br from-[#C18F7E]/5 via-white to-white pointer-events-none"></div>

  {#if displayProduct()}
    {@const slide = displayProduct()!}
    <div 
        in:fade={{duration: 800}} 
        class="absolute inset-0 flex items-center justify-between px-8 md:px-[76px] z-10"
    >
      <!-- Content Left -->
      <div class="relative z-10 flex flex-col gap-4 max-w-[55%] ml-[-20px]">
        <div in:fly={{y: 20, duration: 1000, delay: 200}} class="flex items-center gap-3">
            <div class="flex items-center gap-0.5 bg-gradient-to-r from-[#ee4d2d] to-[#ff6a00] text-white px-2 py-1 italic font-black text-[10px] tracking-tighter uppercase shadow-[0_4px_10px_rgba(238,77,45,0.2)]">
                <span>F</span>
                <svg class="w-3 h-3 fill-white animate-pulse drop-shadow-[0_0_5px_rgba(255,255,255,0.8)]" viewBox="0 0 24 24">
                    <path d="M13 2L4 14h7l-1 8 9-12h-7z"/>
                </svg>
                <span>ash Sale</span>
            </div>
            <div class="h-px w-8 bg-black/10"></div>
            <span class="text-black/30 text-[7px] font-black uppercase tracking-[0.3em]">Hàng hiếm có sẵn</span>
        </div>
        
        <div in:fade={{duration: 800, delay: 300}} class="flex flex-col">
            <h2 class="text-2xl md:text-4xl font-black leading-tight tracking-tight line-clamp-2 bg-gradient-to-br from-black via-gray-700 to-[#C18F7E] bg-clip-text text-transparent italic">
                {slide.name}
            </h2>
        </div>

        <div in:fly={{y: 30, duration: 1000, delay: 500}} class="flex items-center gap-8">
            <div class="flex flex-col">
                <div class="flex items-center gap-3 mb-1">
                    <span class="text-sm font-bold text-gray-300 line-through tabular-nums decoration-gray-400/20">
                        {formatCurrency(Math.round(slide.originalPrice!))}
                    </span>
                    <span class="text-[9px] text-[#ee4d2d] font-black uppercase tracking-widest animate-pulse">−55%</span>
                </div>
                <span class="text-[#ee4d2d] text-3xl font-black tabular-nums tracking-tighter flex items-end gap-1">
                    {formatCurrency(slide.price)}
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
            
            {#each specs() as spec, idx}
                <div in:fly={{x: 30, duration: 1000, delay: 800 + (idx * 200)}} 
                     class="absolute z-20 px-3 py-1.5 bg-white/90 backdrop-blur-xl border border-white shadow-xl flex flex-col gap-0.5 animate-float-spec" 
                     style="top: {20 + (idx * 20)}%; right: {5 + (idx % 2 * 8)}%; animation-delay: {idx * 1.5}s">
                    <span class="text-[7px] font-black uppercase tracking-[0.1em] text-black/30">{spec.label}</span>
                    <span class="text-[9px] font-black {spec.color}">{spec.value}</span>
                </div>
            {/each}

            <div in:fly={{x: -30, duration: 1000, delay: 1200}} 
                 class="absolute z-20 bottom-[20%] left-[8%] px-3 py-2 bg-black text-white flex items-center gap-2 shadow-xl">
                <div class="h-1.5 w-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]"></div>
                <span class="text-[8px] font-black uppercase tracking-[0.2em]">
                    {slide.metadata?.brand || slide.metadata?.origin || 'Chính hãng'}
                </span>
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
{/if}
