import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingpageDesktop.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

import re

# Refined regex for section headers
headers_to_fix = [
    ('Mô tả sản phẩm', 'Mô tả sản phẩm'),
    ('Câu hỏi thường gặp', 'Câu hỏi thường gặp')
]

for old_title, new_title in headers_to_fix:
    pattern = re.compile(rf'<div class="bg-gray-50/50 px-0 py-4 border-b border-gray-100 mb-6">\s+<h2 class="text-\[18px\] font-black text-gray-800 uppercase tracking-tight">{old_title}</h2>\s+</div>', re.DOTALL)
    replacement = f"""<div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-50">
          <div class="flex items-center gap-3">
             <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
             <h2 class="text-[20px] font-black text-gray-900 uppercase tracking-tight">{new_title}</h2>
          </div>
       </div>"""
    content = pattern.sub(replacement, content)

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
