<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import { fly } from 'svelte/transition';

  interface Product {
    id: string;
    name: string;
    price: number;
    image: string;
    sales?: number;
    originalPrice?: number;
    rating?: number;
    ratingCount?: number;
  }

  interface Props {
    products: Product[];
  }

  let { products = [] }: Props = $props();
</script>

<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
  {#each products as product (product.id)}
    <a
      href={`/${slugify(product.name)}`}
      class="group/card relative bg-white border border-gray-100 hover:border-[#ee4d2d] transition-all duration-300 cursor-pointer flex flex-col active:scale-[0.98] shadow-sm hover:shadow-xl overflow-hidden no-underline"
      in:fly={{ y: 20, duration: 600, delay: 100 }}
    >
      <!-- IMAGE ZONE -->
      <div class="aspect-square w-full relative overflow-hidden bg-[#fafafa]">
        <!-- Flash Sale / Discount Tag -->
        <div class="absolute top-0 right-0 z-20">
          <div class="bg-[#ffd839] text-[#ee4d2d] text-[10px] font-black px-1.5 py-1 uppercase flex flex-col items-center leading-none relative">
            <span>-35%</span>
            <span class="text-[8px] mt-0.5 opacity-80">GIẢM</span>
            <!-- Bottom notch for Shopee style tag -->
            <div class="absolute -bottom-1 inset-x-0 h-1 bg-[#ffd839] [clip-path:polygon(0%_0%,50%_100%,100%_0%)]"></div>
          </div>
        </div>

        {#if product.sales && product.sales > 1000}
           <div class="absolute top-2 left-2 z-20">
              <span class="bg-[#ee4d2d] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-sm uppercase tracking-tighter">Bán chạy</span>
           </div>
        {/if}

        <img
          src={product.image}
          alt={product.name}
          class="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
          loading="lazy"
        />
      </div>

      <!-- CONTENT ZONE -->
      <div class="p-3 flex flex-col flex-1 bg-white">
        <h3 class="text-gray-800 text-[12px] font-medium leading-normal line-clamp-2 h-[34px] mb-2 group-hover/card:text-[#ee4d2d] transition-colors">
          {product.name}
        </h3>

        <div class="mt-auto space-y-2">
          <!-- Price Section -->
          <div class="flex flex-col">
            <div class="flex items-center gap-1.5 h-4">
              <span class="text-[11px] text-gray-400 line-through tabular-nums decoration-gray-300">
                ₫{Math.round(product.originalPrice || product.price * 1.55).toLocaleString('vi-VN')}
              </span>
            </div>
            <p class="text-[#ee4d2d] font-bold text-lg tabular-nums flex items-baseline gap-0.5">
              <span class="text-sm font-medium">₫</span>{product.price.toLocaleString('vi-VN')}
            </p>
          </div>

          <!-- Bottom Footer Info -->
          <div class="pt-2 border-t border-gray-50 flex items-center justify-between">
            <div class="flex items-center gap-1 text-[#ffac33]">
               <svg class="w-2.5 h-2.5 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
               <span class="text-[9px] font-bold text-gray-400">{product.rating || 5}</span>
            </div>
            <span class="text-[10px] text-gray-400 font-medium">Đã bán {product.sales || 0}</span>
          </div>
        </div>
      </div>
      
      <!-- Hover Interaction Background -->
      <div class="absolute inset-0 border-2 border-[#ee4d2d] opacity-0 group-hover/card:opacity-100 transition-opacity pointer-events-none z-30"></div>
    </a>
  {/each}
</div>
