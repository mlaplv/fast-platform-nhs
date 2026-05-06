import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/ProductDetailDesktop.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

# Fix Exclusion Logic
old_logic = "((k === 'thương hiệu' || k === 'brand' || k === 'thương hiệu (brand)') && brand)"
new_logic = "((k === 'thương hiệu' || k === 'brand' || k === 'thương hiệu (brand)' || k === 'thương hiệu chính') && brand)"

if old_logic in content:
    content = content.replace(old_logic, new_logic)

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
