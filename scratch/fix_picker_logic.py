import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductFormMetadata.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

import re

# Regex to find the broken loop and replace it
pattern = re.compile(r'{#each viralIcons as item}\s+<button\s+type="button"\s+title={item\.label}\s+onclick={\(e\) => {.*?item\.icon = item\.icon;.*?}}\s+class="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-white/10 transition-colors text-\[16px\]"\s+>\s+{item\.icon}\s+</button>\s+{/each}', re.DOTALL)

replacement = """{#each viralIcons as vIcon}
                      <button
                        type="button"
                        title={vIcon.label}
                        onclick={(e) => {
                          e.stopPropagation();
                          item.icon = vIcon.icon;
                          activeIconPicker = null;
                        }}
                        class="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-white/10 transition-colors text-[16px]"
                      >
                        {vIcon.icon}
                      </button>
                    {/each}"""

content = pattern.sub(replacement, content)

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
