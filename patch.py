import re

with open("frontend/src/routes/(client)/(store)/user/address/+page.svelte", "r") as f:
    content = f.read()

# 1. Add import
content = content.replace(
    "import { CheckCircle2 } from 'lucide-svelte';",
    "import { CheckCircle2 } from 'lucide-svelte';\n  import divisions from '$lib/data/vn_divisions.json';"
)

# wait actually lucide-svelte has multiple imports
content = re.sub(
    r"import { [^}]+ } from 'lucide-svelte';",
    lambda m: m.group(0) + "\n  import divisions from '$lib/data/vn_divisions.json';",
    content
)

# 2. Interface District
content = content.replace("district: string;", "district?: string;")

# 3. Validation
content = content.replace(
    "if (!name || !phone || !address || !city || !district || !ward)",
    "if (!name || !phone || !address || !city || !ward)"
)

# 4. New Addr
content = content.replace(
    "        city,\n        district,\n        ward,",
    "        city,\n        ward,"
)

# 5. Form HTML
form_html_old = """        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="space-y-2">
            <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Tỉnh / Thành phố</label>
            <input
              type="text"
              bind:value={city}
              placeholder="Nhập tỉnh/thành"
              class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper transition-colors text-stone-800 placeholder:text-stone-300"
            />
          </div>
          <div class="space-y-2">
            <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Quận / Huyện</label>
            <input
              type="text"
              bind:value={district}
              placeholder="Nhập quận/huyện"
              class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper transition-colors text-stone-800 placeholder:text-stone-300"
            />
          </div>
          <div class="space-y-2">
            <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Phường / Xã</label>
            <input
              type="text"
              bind:value={ward}
              placeholder="Nhập phường/xã"
              class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper transition-colors text-stone-800 placeholder:text-stone-300"
            />
          </div>
        </div>"""

form_html_new = """        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="space-y-2">
            <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Tỉnh / Thành phố</label>
            <select
              bind:value={city}
              onchange={() => ward = ''}
              class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper transition-colors text-stone-800 cursor-pointer"
            >
              <option value="" disabled>Chọn tỉnh/thành</option>
              {#each divisions as div}
                <option value={div.name}>{div.name}</option>
              {/each}
            </select>
          </div>
          <div class="space-y-2">
            <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Phường / Xã</label>
            <select
              bind:value={ward}
              disabled={!city}
              class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper transition-colors text-stone-800 cursor-pointer disabled:opacity-50"
            >
              <option value="" disabled>Chọn phường/xã</option>
              {#each (divisions.find(d => d.name === city)?.wards || []) as w}
                <option value={w}>{w}</option>
              {/each}
            </select>
          </div>
        </div>"""

content = content.replace(form_html_old, form_html_new)

# 6. Display District
content_display_old = "<p>{addr.ward}, {addr.district}, {addr.city}</p>"
content_display_new = "<p>{addr.ward}, {addr.city}</p>"
content = content.replace(content_display_old, content_display_new)

with open("frontend/src/routes/(client)/(store)/user/address/+page.svelte", "w") as f:
    f.write(content)
