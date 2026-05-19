<script lang="ts">
  import { slide } from "svelte/transition";
  import FolderTree from "@lucide/svelte/icons/folder-tree";
  import Plus from "@lucide/svelte/icons/plus";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Skull from "@lucide/svelte/icons/skull";
  import Eye from "@lucide/svelte/icons/eye";
  import EyeOff from "@lucide/svelte/icons/eye-off";
  import CheckSquare from "@lucide/svelte/icons/check-square";
  import Square from "@lucide/svelte/icons/square";
  import Layers from "@lucide/svelte/icons/layers";
  import GripVertical from "@lucide/svelte/icons/grip-vertical";
  import Monitor from "@lucide/svelte/icons/monitor";
  import Smartphone from "@lucide/svelte/icons/smartphone";
  import { dndzone } from "svelte-dnd-action";

  import type { Category } from "$lib/types";

  let {
    categories,
    selectedIds,
    expandedIds,
    onToggleSelect,
    onToggleExpand,
    onAddSub,
    onEdit,
    onRequestDelete,
    onQuickToggle,
    onReorder,
  } = $props<{
    categories: Category[];
    selectedIds: Set<string>;
    expandedIds: Set<string>;
    onToggleSelect: (id: string) => void;
    onToggleExpand: (id: string) => void;
    onAddSub: (id: string) => void;
    onEdit: (cat: Category, parentId?: string | null) => void;
    onRequestDelete: (id: string, parentId: string | null, name: string, mode: "soft" | "hard") => void;
    onQuickToggle: (id: string, currentMobile: boolean, currentDesktop: boolean) => void;
    onReorder: (newOrder: Category[]) => void;
  }>();

  const flipDurationMs = 300;

  function handleDndConsider(e: any) {
    onReorder(e.detail.items);
  }

  function handleDndFinalize(e: any) {
    onReorder(e.detail.items);
  }
</script>

<div
  class="space-y-3 relative before:absolute before:inset-y-2 before:left-[22px] before:w-px before:bg-gradient-to-b before:from-white/10 before:via-white/5 before:to-transparent"
  use:dndzone={{ items: categories, flipDurationMs, dragDisabled: false }}
  onconsider={handleDndConsider}
  onfinalize={handleDndFinalize}
>
  {#snippet categoryNode(cat: Category, level: number, parentId: string | null)}
    <div class="group/cat relative">
      {#if level > 0}
        <div class="absolute left-[-11px] top-1/2 w-3 h-px bg-white/10"></div>
      {:else}
        <div class="absolute left-[-16px] top-1/2 w-4 h-px bg-white/10 hidden"></div>
      {/if}
      
      <div
        class={level === 0
          ? "flex items-center gap-4 px-5 py-4 bg-black/40 hover:bg-white/[0.04] border border-white/5 hover:border-[#00FFFF]/20 rounded-2xl cursor-pointer transition-all duration-300 relative overflow-hidden shadow-sm hover:shadow-[0_4px_20px_rgba(0,0,0,0.5)] z-10"
          : "flex flex-wrap sm:flex-nowrap items-center gap-3 sm:gap-4 px-3 py-3 sm:px-4 sm:py-3 bg-black/20 hover:bg-white/[0.03] border border-transparent hover:border-white/5 rounded-xl transition-all group/sub relative cursor-pointer"}
      >
        {#if level === 0}
          <div class="absolute inset-y-0 left-0 w-[3px] bg-gradient-to-b from-[#00FFFF]/60 to-[#00FFFF]/10 opacity-0 group-hover/cat:opacity-100 transition-opacity duration-300"></div>
          <button onclick={() => onToggleSelect(cat.id)} class="text-gray-600 hover:text-[#00FFFF] transition-colors shrink-0">
            {#if selectedIds.has(cat.id)}<CheckSquare size={16} class="text-[#00FFFF]" />{:else}<Square size={16} />{/if}
          </button>
          <div class="text-gray-700 cursor-grab active:cursor-grabbing hover:text-[#00FFFF]/50 transition-colors">
            <GripVertical size={16} />
          </div>
        {/if}

        {#if cat.children && cat.children.length > 0}
          <button onclick={() => onToggleExpand(cat.id)} class="text-gray-600 hover:text-[#00FFFF] transition-all shrink-0">
            <div class="transition-transform duration-300 {expandedIds.has(cat.id) ? 'rotate-90' : ''}">
              <ChevronRight size={14} />
            </div>
          </button>
        {:else}
          <div class={level === 0 ? "w-[14px]" : "w-0"}></div>
        {/if}

        <div class={level === 0
          ? "w-10 h-10 rounded-xl bg-gradient-to-br from-[#00FFFF]/10 to-transparent border border-[#00FFFF]/20 flex items-center justify-center text-[#00FFFF]/80 shrink-0 shadow-[0_0_15px_rgba(0,255,255,0.05)]"
          : "w-8 h-8 rounded-lg bg-[#00FFFF]/5 border border-[#00FFFF]/10 flex items-center justify-center shrink-0 text-[#00FFFF]/40 group-hover/sub:text-[#00FFFF]/80 group-hover/sub:bg-[#00FFFF]/10 transition-colors"}>
          <FolderTree size={level === 0 ? 18 : 14} />
        </div>

        <div class="flex-1 min-w-0 flex flex-col justify-center">
          <div class={level === 0 ? "text-[13px] font-bold text-gray-100 tracking-wide" : "text-[12px] font-medium text-gray-300 group-hover/sub:text-white transition-colors"}>
            {cat.name}
          </div>
          <div class={level === 0 ? "text-[10px] font-mono text-gray-500 mt-1 flex items-center flex-wrap gap-1 sm:gap-2" : "text-[9px] font-mono text-gray-600 mt-0.5 flex items-center gap-1"}>
            <span class={level === 0 ? "text-white/40" : "text-white/30 hidden sm:inline"}>ID:</span>
            <span class={level === 0 ? "truncate max-w-[100px] sm:max-w-none" : "truncate max-w-[80px] sm:max-w-none"}>{cat.slug}</span>
            {#if level === 0}
              <span class="w-1 h-1 rounded-full bg-white/20"></span>
              <span class="text-[#00FFFF]/60">{cat.productCount} items</span>
              <span class="w-1 h-1 rounded-full bg-white/20"></span>
              <div class="flex items-center gap-1">
                <Monitor size={10} class={cat.showOnDesktop !== false ? 'text-[#00FFFF]/80' : 'text-red-500/40'} />
                <Smartphone size={10} class={cat.showOnMobile !== false ? 'text-[#00FFFF]/80' : 'text-red-500/40'} />
              </div>
            {/if}
          </div>
        </div>

        {#if level > 0}
          <span class="hidden sm:inline-block text-[9px] font-mono text-[#00FFFF]/60 px-2 py-1 rounded bg-black/40 border border-white/5 shadow-inner">
            {cat.productCount} items
          </span>
        {/if}

        {#if level === 0 && cat.children && cat.children.length > 0}
          <div class="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-black/50 border border-white/10 shadow-inner">
            <Layers size={10} class="text-gray-500" />
            <span class="text-[9px] font-mono text-gray-400 font-bold">{cat.children.length} SUB</span>
          </div>
        {/if}

        <div class={level === 0
          ? "flex items-center gap-1 sm:opacity-0 group-hover/cat:opacity-100 transition-opacity duration-300 sm:translate-x-2 group-hover/cat:translate-x-0 w-full justify-end sm:w-auto mt-2 sm:mt-0 border-t border-white/5 pt-2 sm:border-0 sm:pt-0"
          : "flex items-center gap-1 sm:opacity-0 group-hover/sub:opacity-100 transition-opacity sm:translate-x-1 group-hover/sub:translate-x-0 w-full sm:w-auto justify-end mt-2 sm:mt-0"}>
          
          <button onclick={(e) => { e.stopPropagation(); onAddSub(cat.id); }} class="p-1.5 text-gray-500 hover:text-white transition-colors rounded-lg bg-black/40 border border-transparent hover:border-white/20" title="Thêm danh mục con">
            <Plus size={level === 0 ? 13 : 12} />
          </button>
          <button onclick={(e) => { e.stopPropagation(); onEdit(cat, parentId); }} class="p-1.5 text-gray-500 hover:text-[#FFB800] transition-colors rounded-lg bg-black/40 hover:bg-[#FFB800]/10 border border-transparent hover:border-[#FFB800]/20" title="Chỉnh sửa">
            <Pencil size={level === 0 ? 13 : 12} />
          </button>
          <button onclick={(e) => { e.stopPropagation(); onQuickToggle(cat.id, cat.showOnMobile ?? true, cat.showOnDesktop ?? true); }} class="p-1.5 transition-colors rounded-lg bg-black/40 border border-transparent hover:border-neon-cyan/20 {(cat.showOnMobile && cat.showOnDesktop) ? 'text-neon-cyan/70 hover:text-neon-cyan' : 'text-gray-600 hover:text-amber-400'}" title={(cat.showOnMobile && cat.showOnDesktop) ? 'Ẩn' : 'Bật hiển thị'}>
            {#if cat.showOnMobile && cat.showOnDesktop}<Eye size={level === 0 ? 13 : 12}/>{:else}<EyeOff size={level === 0 ? 13 : 12}/>{/if}
          </button>
          <button onclick={(e) => { e.stopPropagation(); onRequestDelete(cat.id, parentId, cat.name, "soft"); }} class="p-1.5 text-gray-500 hover:text-red-400 transition-colors rounded-lg bg-black/40 hover:bg-red-500/10 border border-transparent hover:border-red-500/20" title="Ẩn (soft)">
            <Trash2 size={level === 0 ? 13 : 12} />
          </button>
          <button onclick={(e) => { e.stopPropagation(); onRequestDelete(cat.id, parentId, cat.name, "hard"); }} class="p-1.5 text-gray-600 hover:text-rose-400 transition-colors rounded-lg bg-black/40 border border-transparent hover:border-rose-500/30" title="Xóa vĩnh viễn">
            <Skull size={level === 0 ? 13 : 12} />
          </button>
        </div>
      </div>

      {#if cat.children && cat.children.length > 0 && expandedIds.has(cat.id)}
        <div class="ml-6 sm:ml-12 mt-3 space-y-2 relative before:absolute before:inset-y-0 before:left-[-11px] before:w-px before:bg-white/10" transition:slide>
          {#each cat.children as child (child.id)}
            {@render categoryNode(child, level + 1, cat.id)}
          {/each}
        </div>
      {/if}
    </div>
  {/snippet}

  {#each categories as cat (cat.id)}
    {@render categoryNode(cat, 0, null)}
  {/each}
</div>
