import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/ProductDetailDesktop.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

# 1. Remove the brand section at the top
brand_section = """               {#if productInfo.brand}
               <div class="flex items-center">
                  <span class="w-[180px] shrink-0 text-gray-400 font-medium">Thương hiệu</span>
                  <a href="/products?brand={encodeURIComponent(productInfo.brand)}" class="text-[#ee4d2d] font-black hover:underline flex items-center gap-1.5">{productInfo.brand}<svg class="w-3 h-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 5l7 7-7 7" /></svg></a>
               </div>
               {/if}"""

# Handle CRLF
if brand_section in content:
    content = content.replace(brand_section, "")
else:
    brand_section_crlf = brand_section.replace('\n', '\r\n')
    if brand_section_crlf in content:
        content = content.replace(brand_section_crlf, "")

# 2. Fix Category Links to use /slug/
old_cat = 'href="/products?category_id={product.categoryId || \'\'}"'
new_cat = 'href="/{product.categorySlug || \'products\'}/"'
content = content.replace(old_cat, new_cat)

# 3. Add link to brand in attributes loop
old_attr_val = '<span class="text-gray-900 font-medium">{value}</span>'
new_attr_val = """<span class="text-gray-900 font-medium">
                      {#if k === 'thương hiệu' || k === 'brand'}
                        <a href="/products?brand={encodeURIComponent(String(value))}" class="text-[#ee4d2d] font-bold hover:underline">{value}</a>
                      {:else}
                        {value}
                      {/if}
                    </span>"""
content = content.replace(old_attr_val, new_attr_val)

# 4. Remove brand from exclusion list so it shows up in loop
old_exclusion = "((k === 'thương hiệu' || k === 'brand' || k === 'thương hiệu (brand)' || k === 'thương hiệu chính') && brand) || "
content = content.replace(old_exclusion, "")

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
