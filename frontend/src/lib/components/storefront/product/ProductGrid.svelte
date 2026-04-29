<script lang="ts">
  import { goto } from '$app/navigation';
  import { trimProductName, formatCurrency } from '$lib/utils/format';
  import { fly } from 'svelte/transition';
  import type { Product } from '$lib/types';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

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
            <div class="bg-black text-white text-[8px] font-black px-1.5 py-0.5 uppercase flex flex-col items-center leading-none rounded-sm shadow-md">
              <span>MALL</span>
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
          src={product.images?.[0] || ''}
          alt={product.name}
          class="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
          loading="lazy"
        />

        <!-- Freeship Xtra Badge (Floating Bottom) -->
        {#if product.metadata?.is_freeship !== false}
          <div class="absolute bottom-2 left-2" style:z-index={Z_INDEX_CLIENT.CONTENT}>
            <div class="bg-[#00bfa5] text-white text-[8px] font-black px-1.5 py-0.5 uppercase tracking-tighter flex items-center gap-1 shadow-md rounded-[2px]">
               <span>FREESHIP</span>
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
          <div class="flex items-baseline gap-1">
             <span class="text-[#ee4d2d] font-black text-[16px] tabular-nums">
               {formatCurrency(product.discountPrice ?? product.price)}
             </span>
          </div>

          <!-- Marketplace Meta Footer -->
          <div class="mt-2 flex items-center justify-between">
             <div class="flex items-center gap-0.5 text-[#ffac33]">
                <svg class="w-2.5 h-2.5 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                <span class="text-[10px] text-gray-400 font-bold ml-0.5">
                  Đã bán {product.order_count_text || product.orderCountText || '0'}
                </span>
             </div>

             <!-- Points Reward (Elite V2.2 Marketing) -->
             <div class="flex items-center gap-1 bg-amber-50/50 px-1.5 py-0.5 rounded-[4px] border border-amber-100/30">
               <span class="text-[9px] font-black text-amber-600 uppercase tracking-tighter">+{Math.floor((product.discountPrice || product.price) / 100000)} PTS</span>
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
