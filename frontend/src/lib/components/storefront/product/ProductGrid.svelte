<script lang="ts">
  import { trimProductName, formatCurrency } from '$lib/utils/format';
  import { fly } from 'svelte/transition';
  import type { Product } from '$lib/types';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { resolveOptimizedImageUrl } from '$lib/state/utils';

  interface Props {
    products: Product[];
  }

  let { products = [] }: Props = $props();

  const getDiscountPercent = (p: Product) => {
    if (!p.discountPrice || p.discountPrice >= p.price) return 0;
    return Math.round((1 - p.discountPrice / p.price) * 100);
  };
</script>

<!-- GRID ZONE (Elite Search-Style Marketplace) -->
<div class="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4 px-0.5">
  {#each products as product (product.id)}
    {@const discount = getDiscountPercent(product)}
    {@const soldStr = product.order_count_text || product.orderCountText || '0'}
    <a
      href={`/${product.slug}`}
      class="group/card relative bg-white rounded-2xl border border-gray-50 transition-all duration-300 cursor-pointer flex flex-col active:scale-[0.98] shadow-sm overflow-hidden no-underline"
      in:fly={{ y: 20, duration: 600, delay: 100 }}
    >
      <!-- IMAGE ZONE (Elite Marketplace Standard) -->
      <div class="aspect-square w-full relative overflow-hidden bg-gray-50">
        <!-- Mall / New Badge (Elite V2.2) -->
        {#if product.type === 'MALL'}
          <div class="absolute top-2 left-2" style:z-index={Z_INDEX_CLIENT.CONTENT}>
            <div class="bg-black text-white text-[8px] font-black px-1.5 py-0.5 flex flex-col items-center leading-none rounded-sm shadow-md">
              <span>Mall</span>
            </div>
          </div>
        {/if}

        <!-- Discount Tag (Search Style) -->
        {#if discount > 0}
          <div class="absolute top-2 right-2" style:z-index={Z_INDEX_CLIENT.CONTENT}>
            <div class="bg-[var(--color-brand-primary)] text-white text-[9px] font-black px-1.5 py-0.5 rounded-sm shadow-md">
              -{discount}%
            </div>
          </div>
        {/if}

        <img
          src={resolveOptimizedImageUrl(product.images?.[0] || '', 400)}
          alt={product.name}
          class="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
          loading="lazy"
          decoding="async"
        />

        <!-- Freeship Xtra Badge (Floating Bottom) -->
        {#if product.metadata?.is_freeship !== false}
          <div class="absolute bottom-2 left-2" style:z-index={Z_INDEX_CLIENT.CONTENT}>
            <div class="bg-[#00bfa5] text-white text-[8px] font-black px-1.5 py-0.5 tracking-tighter flex items-center gap-1 shadow-md rounded-[2px]">
               <span>Freeship</span>
            </div>
          </div>
        {/if}
      </div>

      <!-- CONTENT ZONE (Marketplace Standard) -->
      <div class="p-3 flex flex-col flex-1 bg-white">
        <h3 class="text-gray-800 text-[13px] font-bold leading-tight line-clamp-2 h-[34px] mb-2 transition-colors">
          {trimProductName(product.name)}
        </h3>

        <div class="mt-auto">
          <!-- Price Section -->
          <div class="flex items-baseline gap-1.5 flex-wrap">
             <span class="text-[#ee4d2d] font-black text-[16px] tabular-nums">
               {formatCurrency(Number(product.discountPrice) || Number(product.price))}
             </span>
             {#if product.discountPrice && product.price && product.discountPrice < product.price}
               <span class="text-[11px] text-gray-400 line-through font-medium tabular-nums">
                 {formatCurrency(product.price)}
               </span>
             {/if}
          </div>

          <!-- Real DB Rating -->
          {#if product.metadata?.reviews_trust_score}
            <div class="flex items-center gap-1 mt-1 mb-0.5">
              <span class="text-[#FF5722] text-[10px] font-black leading-none tracking-[-0.05em]">★★★★★</span>
              <span class="text-[10px] font-black text-[#FF5722] leading-none">{product.metadata.reviews_trust_score.toFixed(1)}</span>
              {#if product.metadata.review_count}
                <span class="text-[9px] text-gray-400 font-bold leading-none">&middot; {product.metadata.review_count} đánh giá</span>
              {/if}
            </div>
          {/if}

          <!-- Marketplace Meta Footer -->
          <div class="mt-auto pt-2 flex items-center justify-between">
             <div class="flex items-center text-gray-400">
                <span class="text-[10px] font-bold">
                  {soldStr.includes('Đã bán') ? soldStr : `Đã bán ${soldStr}`}
                </span>
             </div>

             <!-- Points Reward (Elite V2.2 Marketing) -->
             <div class="flex items-center gap-1 bg-amber-50/50 px-1.5 py-0.5 rounded-[4px] border border-amber-100/30">
               <span class="text-[9px] font-black text-amber-600 tracking-tighter">+{Math.floor((product.discountPrice || product.price) / 100000)} pts</span>
             </div>
             
             <!-- Location -->
             {#if product.metadata?.location}
                <span class="text-[10px] text-gray-400 font-medium truncate max-w-[50px]">{product.metadata.location}</span>
             {/if}
          </div>
        </div>
      </div>
    </a>
  {/each}
</div>

<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
