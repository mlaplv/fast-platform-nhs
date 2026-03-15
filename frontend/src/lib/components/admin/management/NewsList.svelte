<script lang="ts">
  import FileText from "lucide-svelte/icons/file-text";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Calendar from "lucide-svelte/icons/calendar";
  import Eye from "lucide-svelte/icons/eye";
  import Pencil from "lucide-svelte/icons/pencil";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import CheckSquare from "lucide-svelte/icons/check-square";
  import Square from "lucide-svelte/icons/square";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import type { Article } from "$lib/types";

  let { articles, selectedIds, onToggleSelect, onEdit, onDelete } = $props<{
    articles: Article[];
    selectedIds: Set<string>;
    onToggleSelect: (id: string) => void;
    onEdit: (a: Article) => void;
    onDelete: (id: string) => void;
  }>();

  $effect(() => {
    const action = nanobot.commandAction;
    if (action?.entity === "article" || action?.entity === "news") {
      if (action.verb === "edit" && action.args) {
        const target = articles.find(
          (a) =>
            a.id === action.args ||
            a.title.toLowerCase().includes(action.args.toLowerCase()),
        );
        if (target && nanobot.consumeCommand("edit", action.entity)) {
          onEdit(target);
        }
      }
      if (action.verb === "delete" && action.args) {
        const target = articles.find(
          (a) =>
            a.id === action.args ||
            a.title.toLowerCase().includes(action.args.toLowerCase()),
        );
        if (target && nanobot.consumeCommand("delete", action.entity)) {
          onDelete(target.id);
        }
      }
    }
  });
</script>

<div class="flex flex-col gap-3 sm:gap-0 sm:divide-y sm:divide-white/[0.03]">
  {#each articles as article (article.id)}
    <div
      class="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 p-4 sm:px-6 hover:bg-white/[0.02] transition-colors group bg-[#0a0a0a] sm:bg-transparent border border-white/5 sm:border-none rounded-xl sm:rounded-none relative"
    >
      <!-- Row 1 (Mobile only) / Left Column (Desktop): Checkbox + Icon + Title + AI Badge -->
      <div class="flex items-start gap-3 flex-1 min-w-0">
        <button
          onclick={() => onToggleSelect(article.id)}
          class="mt-[2px] sm:mt-0 text-gray-600 hover:text-[#FF33FF] transition-colors shrink-0"
        >
          {#if selectedIds.has(article.id)}<CheckSquare size={16} />{:else}<Square size={16} />{/if}
        </button>
        
        <div class="hidden sm:flex w-9 h-9 rounded-xl bg-[#FF33FF]/5 border border-[#FF33FF]/10 items-center justify-center shrink-0">
          <FileText size={15} class="text-[#FF33FF]/50" />
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-start sm:items-center gap-2 mb-1 sm:mb-1.5 flex-col sm:flex-row">
            <span class="text-[13px] sm:text-xs font-bold sm:font-medium text-white group-hover:text-[#FF33FF] transition-colors leading-tight line-clamp-2 sm:line-clamp-1 truncate sm:whitespace-nowrap sm:overflow-hidden sm:text-ellipsis">
              {article.title}
            </span>
            {#if article.author === "AI Editor"}
              <div class="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-[#FF33FF]/5 border border-[#FF33FF]/10 shrink-0 self-start sm:self-auto">
                <Sparkles size={8} class="text-[#FF33FF]" />
                <span class="text-[8px] sm:text-[7px] font-mono text-[#FF33FF] uppercase">AI</span>
              </div>
            {/if}
          </div>
          
          <div class="flex items-center flex-wrap gap-2 sm:gap-3 text-[10px] sm:text-[9px] font-mono text-gray-500 sm:text-gray-600 truncate">
            <span class="flex items-center gap-1 shrink-0 whitespace-nowrap"><Calendar size={10} class="sm:hidden" /><Calendar size={9} class="hidden sm:block" />{article.createdAt.split(' ')[0]}</span>
            <span class="hidden sm:inline-block w-1 h-1 rounded-full bg-gray-600"></span>
            <span class="shrink-0 max-w-[100px] truncate">{article.category}</span>
            <span class="hidden sm:inline-block w-1 h-1 rounded-full bg-gray-600"></span>
            <span class="shrink-0 max-w-[100px] truncate">{article.author}</span>
          </div>
        </div>
      </div>

      <!-- Row 2 / Right Columns: Status, Views, Actions -->
      <div class="flex items-center justify-between sm:justify-end gap-4 shrink-0 mt-2 sm:mt-0 pt-3 sm:pt-0 border-t border-white/5 sm:border-0 pl-[38px] sm:pl-0">
        
        <div class="flex items-center gap-3">
          {#if article.status === "published"}
            <span class="px-2 py-1 sm:py-0.5 rounded-md text-[9px] sm:text-[8px] font-mono font-bold text-[#39FF14] bg-[#39FF14]/5 border border-[#39FF14]/20 uppercase">Live</span>
            <div class="flex items-center gap-1 text-[10px] sm:text-[9px] font-mono text-gray-500">
              <Eye size={12} class="sm:hidden" /><Eye size={11} class="hidden sm:block" />{article.views?.toLocaleString()}
            </div>
          {:else}
            <span class="px-2 py-1 sm:py-0.5 rounded-md text-[9px] sm:text-[8px] font-mono font-bold text-[#FFB800] bg-[#FFB800]/5 border border-[#FFB800]/20 uppercase">Draft</span>
          {/if}
        </div>

        <div class="flex items-center gap-1 sm:opacity-0 group-hover:opacity-100 transition-opacity shrink-0 bg-[#0a0a0a] sm:bg-transparent -mr-2 sm:mr-0 px-2 sm:px-0">
          <button
            onclick={() => onEdit(article)}
            class="p-2 sm:p-1.5 text-gray-500 md:text-gray-600 hover:text-[#FFB800] transition-colors rounded-lg bg-white/5 sm:bg-transparent hover:bg-white/10 sm:hover:bg-white/5"
          >
            <Pencil size={14} class="sm:hidden" /><Pencil size={13} class="hidden sm:block" />
          </button>
          <button
            onclick={() => onDelete(article.id)}
            class="p-2 sm:p-1.5 text-red-500 md:text-gray-600 hover:text-red-400 transition-colors rounded-lg bg-white/5 sm:bg-transparent hover:bg-white/10 sm:hover:bg-white/5"
          >
            <Trash2 size={14} class="sm:hidden" /><Trash2 size={13} class="hidden sm:block" />
          </button>
        </div>

      </div>
    </div>
  {/each}
</div>
