<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import { fly } from 'svelte/transition';
  import type { Product } from '$lib/types';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  interface Props {
    products: Product[];
  }

  // SINGLE SOURCE OF TRUTH: parent (ProductListDesktop) đã sort/filter xong.
  // ProductGrid chỉ render, KHÔNG re-sort nội bộ.
  let { products = [] }: Props = $props();

  const getDiscountPercent = (p: Product) => {
    if (!p.discountPrice || p.discountPrice >= p.price) return 0;
    return Math.round((1 - p.discountPrice / p.price) * 100);
  };
</script>

<!-- GRID ZONE (High-Density Marketplace) -->
<div class="grid grid-cols-2 md:grid-cols-3 gap-2 md:gap-4 px-1">
  {#each products as product (product.id)}
    {@const discount = getDiscountPercent(product)}
    <a
      href={`/${slugify(product.name)}`}
      class="group/card relative bg-white border border-gray-100 transition-all duration-300 cursor-pointer flex flex-col active:scale-[0.98] shadow-sm overflow-hidden no-underline"
      in:fly={{ y: 20, duration: 600, delay: 100 }}
    >
      <!-- IMAGE ZONE (Elite Marketplace Standard) -->
      <div class="aspect-square w-full relative overflow-hidden bg-[#fafafa]">
        <!-- Mall / New Badge (Elite V2.2) -->
        {#if product.type === 'MALL'}
          <div class="absolute top-0 left-0" style:z-index={Z_INDEX_CLIENT.CONTENT}>
            <div class="bg-[#d0011b] text-white text-[9px] font-black px-1.5 py-0.5 uppercase flex flex-col items-center leading-none rounded-br-sm shadow-sm">
              <span>MALL</span>
            </div>
          </div>
        {/if}

        <!-- Flash Sale / Discount Tag (Shopee Style) -->
        {#if discount > 0}
          <div class="absolute top-0 right-0" style:z-index={Z_INDEX_CLIENT.CONTENT}>
            <div class="bg-[#ffd839] text-[#ee4d2d] text-[10px] font-black px-1.5 py-1 uppercase flex flex-col items-center leading-none relative">
              <span>-{discount}%</span>
              <!-- Bottom notch -->
              <div class="absolute -bottom-1 inset-x-0 h-1 bg-[#ffd839] [clip-path:polygon(0%_0%,50%_100%,100%_0%)]"></div>
            </div>
          </div>
        {/if}

        <img
          src={product.images?.[0] || ''}
          alt={product.name}
          class="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
          loading="lazy"
        />

        <!-- Freeship Xtra Badge Overlay -->
        {#if product.metadata?.is_freeship !== false}
          <div class="absolute bottom-0 left-0" style:z-index={Z_INDEX_CLIENT.CONTENT}>
            <div class="bg-[#00bfa5] text-white text-[8px] font-black px-1.5 py-0.5 uppercase tracking-tighter flex items-center gap-1 shadow-sm">
               <span>FREESHIP</span>
               <span class="bg-white text-[#00bfa5] px-0.5 rounded-[1px]">XTRA</span>
            </div>
          </div>
        {/if}
      </div>

      <!-- CONTENT ZONE (Marketplace Standard) -->
      <div class="p-2 flex flex-col flex-1 bg-white">
        <h3 class="text-gray-800 text-[12px] font-medium leading-[1.4] line-clamp-2 h-[34px] mb-2 transition-colors">
          {product.name}
        </h3>

        <div class="mt-auto">
          <!-- Price Section -->
          <div class="flex items-baseline gap-1">
             <span class="text-black font-bold text-[16px] tabular-nums group-hover/card:text-[#C18F7E] transition-colors">
               <span class="text-[12px] font-black text-[#C18F7E] mr-0.5">đ</span>{(product.discountPrice ?? product.price).toLocaleString('vi-VN')}
             </span>
          </div>

          <!-- Marketplace Meta Footer -->
          <div class="mt-2 flex flex-col gap-1">
             <!-- Sold Stats -->
             <div class="flex items-center justify-between">
                <div class="flex items-center gap-0.5 text-[#ffac33]">
                   {#each Array(5) as _}
                     <svg class="w-2 h-2 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                   {/each}
                </div>
                <span class="text-[10px] text-gray-400 font-medium">
                  {product.metadata?.reviews_count_text ? `${product.metadata.reviews_count_text} + Lượt mua` : ''}
                </span>
             </div>
             
             <!-- Location -->
             {#if product.metadata?.location}
               <div class="text-right">
                  <span class="text-[10px] text-gray-400 font-medium">{product.metadata.location}</span>
               </div>
             {/if}
          </div>
        </div>
      </div>
      
      <!-- Subtle Hover Effect (Standard Mobile) -->
      <div class="absolute inset-x-0 bottom-0 h-0.5 bg-[#C18F7E] scale-x-0 group-hover/card:scale-x-100 transition-transform duration-300 origin-left"></div>
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

  /* Kỹ thuật Sticky Elite V2.2 */
  :global(.grid-header-sticky) {
    top: calc(var(--header-height, 60px) + 1px);
  }

  /* Hiệu ứng hover cho Tab */
  button {
    -webkit-tap-highlight-color: transparent;
  }
</style>
