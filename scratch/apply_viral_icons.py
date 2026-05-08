import os

def update_file(path):
    with open(path, 'rb') as f:
        content = f.read().decode('utf-8')
    
    # Add import
    if "import { getIngredientIcon } from '$lib/utils/product';" not in content:
        if "import {" in content:
            content = content.replace("import {", "import { getIngredientIcon } from '$lib/utils/product';\n  import {", 1)
        else:
            content = "<script>\n  import { getIngredientIcon } from '$lib/utils/product';\n" + content[content.find("<script>")+8:]
            
    # Replace icon logic
    content = content.replace("{ing.icon || '🧬'}", "{ing.icon || getIngredientIcon(ing.name)}")
    
    with open(path, 'wb') as f:
        f.write(content.encode('utf-8'))

update_file('/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingpageDesktop.svelte')
update_file('/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/ProductMobileSpecs.svelte')
