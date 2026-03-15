<script lang="ts">
  import { slide } from "svelte/transition";
  import FolderTree from "lucide-svelte/icons/folder-tree";
  import Plus from "lucide-svelte/icons/plus";
  import ChevronRight from "lucide-svelte/icons/chevron-right";
  import Pencil from "lucide-svelte/icons/pencil";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import CheckSquare from "lucide-svelte/icons/check-square";
  import Square from "lucide-svelte/icons/square";
  import Layers from "lucide-svelte/icons/layers";

  import type { Category } from "$lib/types";

  let {
    categories,
    selectedIds,
    expandedIds,
    onToggleSelect,
    onToggleExpand,
    onAddSub,
    onEdit,
    onDelete,
  } = $props<{
    categories: Category[];
    selectedIds: Set<string>;
    expandedIds: Set<string>;
    onToggleSelect: (id: string) => void;
    onToggleExpand: (id: string) => void;
    onAddSub: (id: string) => void;
    onEdit: (cat: Category, parentId?: string | null) => void;
    onDelete: (id: string, parentId?: string | null) => void;
  }>();
</script>

<div
  class="space-y-3 relative before:absolute before:inset-y-2 before:left-[22px] before:w-px before:bg-gradient-to-b before:from-white/10 before:via-white/5 before:to-transparent"
>
  {#each categories as cat (cat.id)}
    <div class="group/cat relative">
      <div
        class="absolute left-[-16px] top-1/2 w-4 h-px bg-white/10 hidden"
      ></div>
      <div
        class="flex items-center gap-4 px-5 py-4 bg-black/40 hover:bg-white/[0.04] border border-white/5 hover:border-[#00FFFF]/20 rounded-2xl cursor-pointer transition-all duration-300 relative overflow-hidden shadow-sm hover:shadow-[0_4px_20px_rgba(0,0,0,0.5)] z-10"
      >
        <div
          class="absolute inset-y-0 left-0 w-[3px] bg-gradient-to-b from-[#00FFFF]/60 to-[#00FFFF]/10 opacity-0 group-hover/cat:opacity-100 transition-opacity duration-300"
        ></div>
        <button
          onclick={() => onToggleSelect(cat.id)}
          class="text-gray-600 hover:text-[#00FFFF] transition-colors shrink-0"
        >
          {#if selectedIds.has(cat.id)}<CheckSquare
              size={16}
              class="text-[#00FFFF]"
            />{:else}<Square size={16} />{/if}
        </button>
        {#if cat.children && cat.children.length > 0}
          <button
            onclick={() => onToggleExpand(cat.id)}
            class="text-gray-600 hover:text-[#00FFFF] transition-all shrink-0"
          >
            <div
              class="transition-transform duration-300 {expandedIds.has(cat.id)
                ? 'rotate-90'
                : ''}"
            >
              <ChevronRight size={14} />
            </div>
          </button>
        {:else}
          <div class="w-[14px]"></div>
        {/if}
        <div
          class="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00FFFF]/10 to-transparent border border-[#00FFFF]/20 flex items-center justify-center text-[#00FFFF]/80 shrink-0 shadow-[0_0_15px_rgba(0,255,255,0.05)]"
        >
          <FolderTree size={18} />
        </div>
        <div class="flex-1 min-w-0 flex flex-col justify-center">
          <div class="text-[13px] font-bold text-gray-100 tracking-wide">
            {cat.name}
          </div>
          <div
            class="text-[10px] font-mono text-gray-500 mt-1 flex items-center flex-wrap gap-1 sm:gap-2"
          >
            <span class="text-white/40">ID:</span>
            <span class="truncate max-w-[100px] sm:max-w-none">{cat.slug}</span>
            <span class="w-1 h-1 rounded-full bg-white/20"></span>
            <span class="text-[#00FFFF]/60">{cat.productCount} items</span>
          </div>
        </div>
        {#if cat.children && cat.children.length > 0}
          <div
            class="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-black/50 border border-white/10 shadow-inner"
          >
            <Layers size={10} class="text-gray-500" />
            <span class="text-[9px] font-mono text-gray-400 font-bold"
              >{cat.children.length} SUB</span
            >
          </div>
        {/if}
        <div
          class="flex items-center gap-1.5 sm:opacity-0 group-hover/cat:opacity-100 transition-opacity duration-300 sm:translate-x-2 group-hover/cat:translate-x-0 w-full justify-end sm:w-auto mt-2 sm:mt-0 border-t border-white/5 pt-2 sm:border-0 sm:pt-0"
        >
          <button
            onclick={(e) => {
              e.stopPropagation();
              onAddSub(cat.id);
            }}
            class="p-2 sm:p-2 text-gray-400 sm:text-gray-500 hover:text-white transition-colors rounded-xl bg-white/5 sm:bg-black/40 border border-transparent hover:border-white/20"
            title="Thêm danh mục con"
          >
            <Plus size={14} class="sm:hidden" /><Plus size={14} class="hidden sm:block" />
          </button>
          <button
            onclick={(e) => {
              e.stopPropagation();
              onEdit(cat);
            }}
            class="p-2 sm:p-2 text-gray-400 sm:text-gray-500 hover:text-[#FFB800] transition-colors rounded-xl bg-white/5 sm:bg-black/40 border border-transparent hover:border-[#FFB800]/20"
            title="Chỉnh sửa"
          >
            <Pencil size={14} class="sm:hidden" /><Pencil size={14} class="hidden sm:block" />
          </button>
          <button
            onclick={(e) => {
              e.stopPropagation();
              onDelete(cat.id);
            }}
            class="p-2 sm:p-2 text-red-400 sm:text-gray-500 hover:text-red-400 transition-colors rounded-xl bg-red-500/10 sm:bg-black/40 border border-transparent hover:border-red-500/20"
            title="Xóa"
          >
            <Trash2 size={14} class="sm:hidden" /><Trash2 size={14} class="hidden sm:block" />
          </button>
        </div>
      </div>
      {#if cat.children && cat.children.length > 0 && expandedIds.has(cat.id)}
        <div
          class="ml-6 sm:ml-12 mt-3 space-y-2 relative before:absolute before:inset-y-0 before:left-[-11px] before:w-px before:bg-white/10"
          transition:slide
        >
          {#each cat.children as child (child.id)}
            <div
              class="flex flex-wrap sm:flex-nowrap items-center gap-3 sm:gap-4 px-3 py-3 sm:px-4 sm:py-3 bg-black/20 hover:bg-white/[0.03] border border-transparent hover:border-white/5 rounded-xl transition-all group/sub relative cursor-pointer"
            >
              <div
                class="absolute left-[-11px] top-1/2 w-3 h-px bg-white/10"
              ></div>
              <div
                class="w-8 h-8 rounded-lg bg-[#00FFFF]/5 border border-[#00FFFF]/10 flex items-center justify-center shrink-0 text-[#00FFFF]/40 group-hover/sub:text-[#00FFFF]/80 group-hover/sub:bg-[#00FFFF]/10 transition-colors"
              >
                <FolderTree size={14} />
              </div>
              <div class="flex-1 min-w-0">
                <div
                  class="text-[12px] font-medium text-gray-300 group-hover/sub:text-white transition-colors"
                >
                  {child.name}
                </div>
                <div class="text-[9px] font-mono text-gray-600 mt-0.5 flex items-center gap-1">
                  <span class="text-white/30 hidden sm:inline">ID:</span>
                  <span class="truncate max-w-[80px] sm:max-w-none">{child.slug}</span>
                </div>
              </div>
              <span
                class="hidden sm:inline-block text-[9px] font-mono text-[#00FFFF]/60 px-2 py-1 rounded bg-black/40 border border-white/5 shadow-inner"
                >{child.productCount} items</span
              >
              <div
                class="flex items-center gap-1.5 sm:opacity-0 group-hover/sub:opacity-100 transition-opacity sm:translate-x-1 group-hover/sub:translate-x-0 w-full sm:w-auto justify-end mt-2 sm:mt-0"
              >
                <button
                  onclick={(e) => {
                    e.stopPropagation();
                    onEdit(child, cat.id);
                  }}
                  class="p-2 sm:p-1.5 text-gray-400 sm:text-gray-500 hover:text-[#FFB800] transition-colors rounded-lg hover:bg-[#FFB800]/10 bg-white/5 sm:bg-black/40 border border-transparent hover:border-[#FFB800]/20"
                >
                  <Pencil size={12} class="sm:hidden" /><Pencil size={12} class="hidden sm:block" />
                </button>
                <button
                  onclick={(e) => {
                    e.stopPropagation();
                    onDelete(child.id, cat.id);
                  }}
                  class="p-2 sm:p-1.5 text-red-400 sm:text-gray-500 hover:text-red-400 transition-colors rounded-lg hover:bg-red-500/10 bg-red-500/10 sm:bg-black/40 border border-transparent hover:border-red-500/20"
                >
                  <Trash2 size={12} class="sm:hidden" /><Trash2 size={12} class="hidden sm:block" />
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/each}
</div>
