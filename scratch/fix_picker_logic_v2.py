import os

file_path = '/home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductFormMetadata.svelte'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

# Let's just find the viralIcons loop by its distinctive comment or context
start_marker = '{#if activeIconPicker === i}'
end_marker = '{/if}'

# I'll replace the entire popover content
popover_replacement = """{#if activeIconPicker === i}
                  <!-- svelte-ignore a11y_click_events_have_key_events -->
                  <!-- svelte-ignore a11y_no_static_element_interactions -->
                  <div 
                    class="fixed inset-0 z-[60]" 
                    onclick={(e) => { e.stopPropagation(); activeIconPicker = null; }}
                  ></div>
                  <div class="absolute z-[70] top-full left-0 mt-2 p-2 bg-[#1a1a1a] border border-white/10 rounded-xl grid grid-cols-5 gap-1 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)] min-w-[180px]">
                    {#each viralIcons as vIcon}
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
                    {/each}
                  </div>
                {/if}"""

import re
# Find the block between if/if
# We need to be careful with nested if/each
# But here it's quite specific.

# Find the specific broken block
pattern = re.compile(r'{#if activeIconPicker === i}.*?{#each viralIcons as item}.*?{/each}\s+</div>\s+{/if}', re.DOTALL)

if pattern.search(content):
    content = pattern.sub(popover_replacement, content)
else:
    # Try a broader search if the above fails
    print("Pattern not found, trying line-by-line")
    lines = content.split('\n')
    new_lines = []
    skip = False
    for i, line in enumerate(lines):
        if '{#if activeIconPicker === i}' in line:
            new_lines.append(popover_replacement)
            skip = True
        elif skip and '{/if}' in line and '</div>' in lines[i-1]:
            # This is likely the end of our block
            skip = False
            continue
        if not skip:
            new_lines.append(line)
    content = '\n'.join(new_lines)

with open(file_path, 'wb') as f:
    f.write(content.encode('utf-8'))
