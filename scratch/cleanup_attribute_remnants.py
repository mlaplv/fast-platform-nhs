import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingpageDesktop.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

import re
# Regex to find the attributes block and replace it
pattern = re.compile(r'                 {#if product\.attributes && Object\.keys\(product\.attributes\)\.length > 0}.*?{/if}\s+{/if}\s+</div>\s+</div>\s+</div>', re.DOTALL)

# Wait, the closing tags might be tricky. Let's find the exact lines.
# I'll use a simpler search and replace for the if block.

old_block_pattern = re.compile(r'\{#if product\.attributes && Object\.keys\(product\.attributes\)\.length > 0\}.*?\{/if\}\s+\{/if\}', re.DOTALL)

new_block = """{#if visibleAttributes.length > 0}
                  <div class="grid grid-cols-2 gap-4 pt-4 mt-4 border-t border-gray-50">
                    {#each visibleAttributes as [key, value]}
                      <div class="flex items-center justify-between p-3 bg-gray-50/30 rounded-lg">
                        <span class="text-gray-400 font-medium capitalize">{key.replace(/_/g, " ")}</span>
                        <span class="text-gray-900 font-bold">{value}</span>
                      </div>
                    {/each}
                  </div>
                {/if}"""

# Actually, I should just find the start line and replace.
lines = content.split('\n')
start_line = -1
end_line = -1
for i, line in enumerate(lines):
    if '{#if product.attributes && Object.keys(product.attributes).length > 0}' in line:
        start_line = i
    if start_line != -1 and '{/each}' in line:
        # The next {/if} after {/each} is our end
        for j in range(i+1, len(lines)):
            if '{/if}' in lines[j]:
                end_line = j
                break
        if end_line != -1: break

if start_line != -1 and end_line != -1:
    new_lines = lines[:start_line] + [new_block] + lines[end_line+1:]
    content = '\n'.join(new_lines)

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
