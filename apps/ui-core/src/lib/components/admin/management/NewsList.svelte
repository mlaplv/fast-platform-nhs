<script lang="ts">
  import FileText from "lucide-svelte/icons/file-text";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Calendar from "lucide-svelte/icons/calendar";
  import Eye from "lucide-svelte/icons/eye";
  import Pencil from "lucide-svelte/icons/pencil";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import CheckSquare from "lucide-svelte/icons/check-square";
  import Square from "lucide-svelte/icons/square";

  let { articles, selectedIds, onToggleSelect, onEdit, onDelete } = $props<{
    articles: any[];
    selectedIds: Set<string>;
    onToggleSelect: (id: string) => void;
    onEdit: (a: any) => void;
    onDelete: (id: string) => void;
  }>();
</script>

<div class="divide-y divide-white/[0.03]">
  {#each articles as article (article.id)}
    <div
      class="flex items-center gap-4 px-6 py-4 hover:bg-white/[0.02] transition-colors group"
    >
      <button
        onclick={() => onToggleSelect(article.id)}
        class="text-gray-600 hover:text-[#FF33FF] transition-colors shrink-0"
      >
        {#if selectedIds.has(article.id)}<CheckSquare size={15} />{:else}<Square
            size={15}
          />{/if}
      </button>
      <div
        class="w-9 h-9 rounded-xl bg-[#FF33FF]/5 border border-[#FF33FF]/10 flex items-center justify-center shrink-0"
      >
        <FileText size={15} class="text-[#FF33FF]/50" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span
            class="text-xs font-medium text-white group-hover:text-[#FF33FF] transition-colors truncate"
            >{article.title}</span
          >
          {#if article.author === "AI Editor"}
            <div
              class="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-[#FF33FF]/5 border border-[#FF33FF]/10 shrink-0"
            >
              <Sparkles size={8} class="text-[#FF33FF]" />
              <span class="text-[7px] font-mono text-[#FF33FF] uppercase"
                >AI</span
              >
            </div>
          {/if}
        </div>
        <div class="flex items-center gap-3 text-[9px] font-mono text-gray-600">
          <span class="flex items-center gap-1"
            ><Calendar size={9} />{article.createdAt}</span
          >
          <span>{article.category}</span>
          <span>{article.author}</span>
        </div>
      </div>
      <div class="flex items-center gap-4 shrink-0">
        {#if article.status === "published"}
          <div
            class="flex items-center gap-1 text-[9px] font-mono text-gray-500"
          >
            <Eye size={11} />{article.views?.toLocaleString()}
          </div>
          <span
            class="px-2 py-0.5 rounded-md text-[8px] font-mono text-[#39FF14] bg-[#39FF14]/5 border border-[#39FF14]/20 uppercase"
            >Live</span
          >
        {:else}
          <span
            class="px-2 py-0.5 rounded-md text-[8px] font-mono text-[#FFB800] bg-[#FFB800]/5 border border-[#FFB800]/20 uppercase"
            >Draft</span
          >
        {/if}
      </div>
      <div
        class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
      >
        <button
          onclick={() => onEdit(article)}
          class="p-1.5 text-gray-600 hover:text-[#FFB800] transition-colors rounded-lg hover:bg-white/5"
        >
          <Pencil size={13} />
        </button>
        <button
          onclick={() => onDelete(article.id)}
          class="p-1.5 text-gray-600 hover:text-red-400 transition-colors rounded-lg hover:bg-white/5"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  {/each}
</div>
