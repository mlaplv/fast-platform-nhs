import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingpageDesktop.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

import re
# Find the start of the section and replace up to the start of featured ingredients
pattern = re.compile(r'    <!-- CHI TIẾT SẢN PHẨM -->.*?<!-- Elite V2\.2: Featured Ingredients', re.DOTALL)

replacement = """    <!-- CHI TIẾT SẢN PHẨM -->
    <div class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50 mb-[20px]">
       <div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-50">
          <div class="flex items-center gap-3">
             <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
             <h2 class="text-[20px] font-black text-gray-900 uppercase tracking-tight">Chi tiết sản phẩm</h2>
          </div>
          <div class="flex items-center gap-4">
             <div class="flex flex-col items-end">
                <span class="text-[9px] font-black text-gray-400 uppercase tracking-widest">Serial / SKU</span>
                <span class="text-[12px] font-black text-black tracking-widest">{product.sku || 'N/A'}</span>
             </div>
          </div>
       </div>

       <!-- Viral 2026: Liquid Spec Bar (Desktop) -->
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

       <div class="px-0 text-[14px] space-y-10">
          <div class="grid grid-cols-1 gap-6 max-w-5xl">
               <!-- Elite V2.2: Featured Ingredients"""

content = pattern.sub(replacement, content)

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
