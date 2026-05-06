import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/ProductDetailDesktop.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

# 1. Fix all section headers to use the Viral 2026 style
old_headers = [
    ('<h2 class="text-[18px] font-black text-gray-800 uppercase tracking-tight">Mô tả sản phẩm</h2>', 'Mô tả sản phẩm'),
    ('<h2 class="text-[18px] font-black text-gray-800 uppercase tracking-tight">Câu hỏi thường gặp</h2>', 'Câu hỏi thường gặp')
]

for old_h_snippet, title in old_headers:
    new_h = f"""<div class="flex items-center gap-3">
             <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
             <h2 class="text-[20px] font-black text-gray-900 uppercase tracking-tight">{title}</h2>
          </div>"""
    content = content.replace(f'<div class="bg-gray-50/50 px-0 py-4 border-b border-gray-100 mb-6">\n          {old_h_snippet}\n       </div>', 
                              f'<div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-50">\n          {new_h}\n       </div>')

# 2. Clean up the attributes loop to remove the top border if it's the only thing there
content = content.replace('<div class="grid grid-cols-2 gap-4 pt-4 border-t border-gray-50">', '<div class="grid grid-cols-2 gap-4 pt-4 mt-4 border-t border-gray-50">')

# 3. Ensure uniform spacing between major blocks
content = content.replace('<div class="bg-white p-5 shadow-sm">', '<div class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50 mb-[20px]">')

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
