<script lang="ts">
  import type { Product } from '$lib/types';
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Beaker from "@lucide/svelte/icons/beaker";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Info from "@lucide/svelte/icons/info";
  import InteractiveDashboard from '$lib/components/ui/InteractiveDashboard.svelte';
  import { getIngredientIcon } from '$lib/utils/product';

  interface Props {
    product: Product;
    productInfo: {
      barcode: string;
      brand: string;
      origin: string;
      weight: string;
      originalPrice: number;
      salePrice: number;
    };
    visibleAttributes: [string, string | number | object][];
  }

  let { product, productInfo, visibleAttributes }: Props = $props();

  function isJson(str: string): boolean {
    if (typeof str !== 'string' || !str) return false;
    try {
      const parsed: Record<string, unknown> = JSON.parse(str);
      return typeof parsed === 'object' && parsed !== null && ('hero_headline' in parsed || 'spec_bento' in parsed);
    } catch {
      return false;
    }
  }
</script>

<div class="max-w-[1200px] mx-auto flex flex-col gap-[20px] mb-0">
  <!-- CHI TIẾT SẢN PHẨM -->
  <div class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50 ">
     <div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-50">
        <div class="flex items-center gap-3">
           <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
           <h2 class="text-[20px] font-black text-gray-900 uppercase tracking-tight">Chi tiết sản phẩm</h2>
        </div>
        <div class="flex flex-col items-end">
           <span class="text-[9px] font-black text-gray-400 uppercase tracking-widest">Serial / SKU</span>
           <span class="text-[12px] font-black text-black tracking-widest">{product.sku || 'N/A'}</span>
        </div>
     </div>

     <div class="flex items-stretch bg-gray-50/50 border border-gray-100 divide-x divide-gray-100 rounded-none mb-10 overflow-hidden">
        {#if productInfo.brand}
          <div class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all group/spec cursor-default">
            <span class="text-[9px] text-gray-400 font-black uppercase tracking-[0.25em] mb-2 flex items-center gap-2">
              <div class="w-1 h-1 rounded-full bg-amber-400 animate-pulse"></div> Thương hiệu
            </span>
            <a href="/products?brand={encodeURIComponent(productInfo.brand)}" class="text-[14px] font-black text-[#ee4d2d] hover:underline flex items-center gap-1.5 uppercase tracking-tight">
              {productInfo.brand}
              <svg class="w-3.5 h-3.5 opacity-0 group-hover/spec:opacity-100 transition-all translate-x-[-5px] group-hover/spec:translate-x-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 5l7 7-7 7" /></svg>
            </a>
          </div>
        {/if}
        {#if productInfo.origin}
          <div class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all">
            <span class="text-[9px] text-gray-400 font-black uppercase tracking-[0.25em] mb-2 flex items-center gap-2">
              <div class="w-1 h-1 rounded-full bg-blue-400"></div> Xuất xứ
            </span>
            <span class="text-[14px] font-black text-gray-800 uppercase tracking-tighter">{productInfo.origin}</span>
          </div>
        {/if}
        {#if productInfo.weight}
          <div class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all">
            <span class="text-[9px] text-gray-400 font-black uppercase tracking-[0.25em] mb-2 flex items-center gap-2">
              <div class="w-1 h-1 rounded-full bg-emerald-400"></div> Quy cách
            </span>
            <span class="text-[14px] font-black text-gray-800">{productInfo.weight}</span>
          </div>
        {/if}
        <div class="flex-[1.5] px-8 py-5 flex flex-col justify-center hover:bg-white transition-all">
          <span class="text-[9px] text-gray-400 font-black uppercase tracking-[0.25em] mb-2 flex items-center gap-2">
             <div class="w-1 h-1 rounded-full bg-indigo-400"></div> Danh mục
          </span>
          <div class="flex items-center gap-2 text-[13px] font-bold uppercase tracking-tighter">
             <a href="/products" class="text-gray-400 hover:text-gray-900 transition-colors">osmo</a>
             <svg class="w-3 h-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 5l7 7-7 7" /></svg>
             <a href="/{product.categorySlug || 'products'}/" class="text-[#0384ff] hover:underline truncate">
                {product.category || 'CHĂM SÓC DA'}
             </a>
          </div>
        </div>
     </div>

     <div class="text-[14px] space-y-10">
        <div class="grid grid-cols-1 gap-6 w-full">
             {#if product.metadata?.featured_ingredients && product.metadata.featured_ingredients.length > 0}
             <div class="flex flex-col gap-3 py-2">
                <div class="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  <Sparkles size={12} class="text-amber-500" /> Thành phần nổi bật (Featured)
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {#each product.metadata.featured_ingredients as ing}
                    <div class="flex gap-3 bg-[#fdf2f2]/50 border border-[#ee4d2d]/5 p-3 rounded-xl hover:bg-white hover:shadow-xl hover:shadow-[#ee4d2d]/5 transition-all group/ing">
                      <div class="w-10 h-10 shrink-0 bg-white border border-[#ee4d2d]/10 rounded-full flex items-center justify-center text-[18px] group-hover/ing:scale-110 transition-transform shadow-sm">
                        {ing.icon || getIngredientIcon(ing.name)}
                      </div>
                      <div class="flex flex-col">
                        <span class="text-[13px] font-black text-gray-900 leading-none mb-1">{ing.name}</span>
                        <span class="text-[11px] text-gray-500 leading-relaxed font-medium">{ing.benefit}</span>
                      </div>
                    </div>
                  {/each}
                </div>
             </div>
             {/if}

             {#if product.metadata?.ingredients}
             <div class="flex flex-col gap-2 py-1">
                <div class="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  <Beaker size={12} class="text-teal-500" /> Bảng thành phần (Full INCI)
                </div>
                <div class="bg-gray-50/50 border border-gray-100 p-4 rounded-xl relative overflow-hidden group/inci">
                  <div class="absolute top-0 right-0 p-2 opacity-10 group-hover/inci:opacity-30 transition-opacity">
                    <FlaskConical size={40} />
                  </div>
                  <p class="text-[11px] text-gray-600 font-mono leading-relaxed tracking-tight relative z-10">
                    {product.metadata.ingredients}
                  </p>
                  <div class="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2">
                    <Info size={10} class="text-blue-500" />
                    <span class="text-[9px] text-gray-400 font-bold italic">Bảng thành phần công bố</span>
                  </div>
                </div>
             </div>
             {/if}

             {#if visibleAttributes.length > 0}
                <div class="grid grid-cols-2 gap-4 pt-4 mt-4 border-t border-gray-50">
                  {#each visibleAttributes as [key, value]}
                    <div class="flex items-center justify-between p-3 bg-gray-50/30 rounded-lg">
                      <span class="text-gray-400 font-medium capitalize">{key.replace(/_/g, " ")}</span>
                      <span class="text-gray-900 font-bold">{value}</span>
                    </div>
                  {/each}
                </div>
              {/if}
        </div>
     </div>
  </div>

   <!-- MÔ TẢ SẢN PHẨM -->
  <div class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50 ">
     <div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-50">
        <div class="flex items-center gap-3">
           <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
           <h2 class="text-[20px] font-black text-gray-900 uppercase tracking-tight">Mô tả sản phẩm</h2>
        </div>
     </div>
     <div class="px-0 prose-osmo">
        {#if isJson(product.description)}
           <div class="bg-slate-900 text-white p-4 rounded-none">
             <InteractiveDashboard data={product.description} compact={false} />
           </div>
        {:else}
           {@html product.description || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
        {/if}
     </div>
  </div>

  <!-- FAQ Section -->
  {#if product.metadata?.faqs && product.metadata.faqs.length > 0}
  <div class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50 ">
     <div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-50">
        <div class="flex items-center gap-3">
           <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
           <h2 class="text-[20px] font-black text-gray-900 uppercase tracking-tight">Câu hỏi thường gặp</h2>
        </div>
     </div>
     <div class="px-0 flex flex-col gap-4">
        {#each product.metadata.faqs as faq}
          <div class="border border-gray-100 p-4 rounded-md bg-gray-50/30">
            <h3 class="text-[15px] font-bold text-gray-900 mb-2">{faq.question}</h3>
            <p class="text-[14px] text-gray-600 leading-relaxed w-full">{faq.answer}</p>
          </div>
        {/each}
     </div>
  </div>
  {/if}
</div>
