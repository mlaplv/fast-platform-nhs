import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/ProductDetailDesktop.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

# Fix Category Links
old_cat_section = """                  <div class="flex items-center gap-2 text-[#0384ff] font-black uppercase text-[12px] tracking-tighter">
                     <a href="/" class="hover:underline">osmo</a> 
                     <svg class="w-2.5 h-2.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" /></svg>
                     <a href="/" class="hover:underline">{product.category || 'CHĂM SÓC DA'}</a>
                  </div>"""

new_cat_section = """                  <div class="flex items-center gap-2 text-[#0384ff] font-black uppercase text-[12px] tracking-tighter">
                     <a href="/products" class="hover:underline text-gray-400">osmo</a> 
                     <svg class="w-2.5 h-2.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" /></svg>
                     <a href="/products?category_id={product.categoryId || ''}" class="hover:underline">{product.category || 'CHĂM SÓC DA'}</a>
                  </div>"""

# Handle potential CRLF
if old_cat_section in content:
    content = content.replace(old_cat_section, new_cat_section)
else:
    old_cat_section_crlf = old_cat_section.replace('\n', '\r\n')
    if old_cat_section_crlf in content:
        content = content.replace(old_cat_section_crlf, new_cat_section.replace('\n', '\r\n'))
    else:
        # Fallback to single line replacement if block fails
        content = content.replace('<a href="/" class="hover:underline">osmo</a>', '<a href="/products" class="hover:underline text-gray-400">osmo</a>')
        content = content.replace('<a href="/" class="hover:underline">{product.category || \'CHĂM SÓC DA\'}</a>', '<a href="/products?category_id={product.categoryId || \'\'}" class="hover:underline">{product.category || \'CHĂM SÓC DA\'}</a>')

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
