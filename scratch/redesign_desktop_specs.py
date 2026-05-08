import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingpageDesktop.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

# The block to replace
old_block_start = '           <div class="grid grid-cols-1 gap-4 max-w-4xl">'
old_block_end = '         </div>\n      </div>\n   </div>'

# We need a more robust way to find the end of the section
import re
pattern = re.compile(r'           <div class="grid grid-cols-1 gap-4 max-w-4xl">.*?{#if product\.attributes}.*?{/if}\s+</div>\s+</div>', re.DOTALL)

new_layout = """        <div class="grid grid-cols-4 gap-3 mb-6">
          {#if productInfo.brand}
            <div class="flex flex-col p-4 bg-gray-50/50 rounded-xl border border-gray-100 hover:border-[#ee4d2d]/20 transition-all group/spec">
              <span class="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-2 flex items-center gap-1.5">
                <Sparkles size={10} class="text-amber-500" /> Thương hiệu
              </span>
              <a href="/products?brand={encodeURIComponent(productInfo.brand)}" class="text-[13px] font-black text-[#ee4d2d] hover:underline truncate">
                {productInfo.brand}
              </a>
            </div>
          {/if}
          {#if productInfo.origin}
            <div class="flex flex-col p-4 bg-gray-50/50 rounded-xl border border-gray-100">
              <span class="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-2 flex items-center gap-1.5">
                <Info size={10} class="text-blue-500" /> Xuất xứ
              </span>
              <span class="text-[13px] font-black text-gray-900">{productInfo.origin}</span>
            </div>
          {/if}
          {#if productInfo.weight}
            <div class="flex flex-col p-4 bg-gray-50/50 rounded-xl border border-gray-100">
              <span class="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-2 flex items-center gap-1.5">
                <Beaker size={10} class="text-emerald-500" /> Quy cách
              </span>
              <span class="text-[13px] font-black text-gray-900">{productInfo.weight}</span>
            </div>
          {/if}
          <div class="flex flex-col p-4 bg-gray-50/50 rounded-xl border border-gray-100">
            <span class="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-2 flex items-center gap-1.5">
               <FlaskConical size={10} class="text-indigo-500" /> Danh mục
            </span>
            <div class="flex items-center gap-1 text-[13px] font-black">
               <a href="/products" class="text-gray-400 hover:text-gray-600 transition-colors">osmo</a>
               <span class="text-gray-300">/</span>
               <a href="/{product.categorySlug || 'products'}/" class="text-[#0384ff] hover:underline truncate">
                  {product.category || 'CHĂM SÓC DA'}
               </a>
            </div>
          </div>
        </div>

        <div class="px-0 text-[14px] space-y-6">
           <div class="grid grid-cols-1 gap-4 max-w-4xl">
                <!-- Elite V2.2: Featured Ingredients (Viral 2026 UI) -->
                {#if product.metadata?.featured_ingredients && product.metadata.featured_ingredients.length > 0}
                <div class="flex flex-col gap-3 py-2">
                   <div class="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                     <Sparkles size={12} class="text-amber-500" /> Thành phần nổi bật (Featured)
                   </div>
                   <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                     {#each product.metadata.featured_ingredients as ing}
                       <div class="flex gap-3 bg-[#fdf2f2]/50 border border-[#ee4d2d]/5 p-3 rounded-xl hover:bg-white hover:shadow-xl hover:shadow-[#ee4d2d]/5 transition-all group/ing">
                         <div class="w-10 h-10 shrink-0 bg-white border border-[#ee4d2d]/10 rounded-full flex items-center justify-center text-[18px] group-hover/ing:scale-110 transition-transform shadow-sm">
                           {ing.icon || '🧬'}
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

                <!-- Elite V2.2: Full Ingredients (SGE Shield & Technical Transparency) -->
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

                <!-- Other Technical Specs -->
                {#if product.attributes && Object.keys(product.attributes).length > 0}
                  <div class="grid grid-cols-2 gap-4 pt-4 border-t border-gray-50">
                    {#each Object.entries(product.attributes) as [key, value]}
                      {@const k = key.toLowerCase().replace(/_/g, ' ').trim()}
                      {@const brand = productInfo.brand}
                      {@const origin = productInfo.origin}
                      {@const weight = productInfo.weight}
                      {#if !( ((k === 'xuất xứ' || k === 'origin') && origin) || ((k === 'trọng lượng' || k === 'quy cách' || k === 'weight') && weight) || ((k === 'mã vạch' || k === 'barcode') && productInfo.barcode && productInfo.barcode !== 'N/A') || (k === 'thương hiệu' || k === 'brand') )}
                        <div class="flex items-center justify-between p-3 bg-gray-50/30 rounded-lg">
                          <span class="text-gray-400 font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                          <span class="text-gray-900 font-bold">{value}</span>
                        </div>
                      {/if}
                    {/each}
                  </div>
                {/if}
           </div>
        </div>"""

# Replace the block
content = pattern.sub(new_layout, content)

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
