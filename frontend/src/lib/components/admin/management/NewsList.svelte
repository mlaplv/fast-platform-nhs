<script lang="ts">
  import FileTextIcon from "lucide-svelte/icons/file-text";
  import SparklesIcon from "lucide-svelte/icons/sparkles";
  import CalendarIcon from "lucide-svelte/icons/calendar";
  import EyeIcon from "lucide-svelte/icons/eye";
  import PencilIcon from "lucide-svelte/icons/pencil";
  import Trash2Icon from "lucide-svelte/icons/trash-2";
  import CheckSquareIcon from "lucide-svelte/icons/check-square";
  import SquareIcon from "lucide-svelte/icons/square";
  import GlobeIcon from "lucide-svelte/icons/globe";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import type { Article } from "$lib/types";
  import { fade, fly } from "svelte/transition";

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

<div class="flex flex-col gap-2 sm:gap-4 p-2 sm:p-6">
  <!-- Master Checkbox Row -->
  <div class="flex items-center gap-6 px-4 py-3 bg-white/[0.02] border border-white/5 rounded-2xl mb-2">
    <div class="flex items-center gap-4 shrink-0">
      <button
        onclick={() => (selectedIds.size === articles.length ? onToggleSelect('__all_off') : onToggleSelect('__all_on'))}
        class="p-2 rounded-xl transition-all {selectedIds.size === articles.length ? 'text-cyan-400 bg-cyan-500/10' : 'text-white/10 hover:text-white/30 bg-white/5'}"
      >
        {#if selectedIds.size === articles.length}
          <CheckSquareIcon size={20} class="text-cyan-400" />
        {:else if selectedIds.size > 0}
          <div class="w-5 h-5 flex items-center justify-center">
            <div class="w-3 h-0.5 bg-cyan-400 rounded-full"></div>
          </div>
        {:else}
          <SquareIcon size={20} />
        {/if}
      </button>
      <span class="text-[10px] font-black uppercase tracking-widest text-white/20">Select_All_Operational_Data</span>
    </div>
  </div>

  {#each articles as article, i (article.id)}
    <div
      class="news-row group relative flex items-center gap-2 sm:gap-6 p-2 sm:p-4 bg-[#080808]/40 backdrop-blur-md border border-white/5 rounded-xl sm:rounded-3xl transition-all duration-300 hover:bg-white/5 hover:border-cyan-500/30 hover:shadow-[0_0_30px_rgba(6,182,212,0.05)] active:scale-[0.995]"
      in:fly={{ x: -20, delay: i * 30, duration: 400 }}
    >
      <!-- Selection & Thumbnail Container -->
      <div class="relative flex items-center gap-1.5 sm:gap-4 shrink-0">
        <button
          onclick={() => onToggleSelect(article.id)}
          class="p-2 rounded-xl transition-all {selectedIds.has(article.id) ? 'text-cyan-400 bg-cyan-500/10' : 'text-white/10 hover:text-white/30 bg-white/5'}"
        >
          {#if selectedIds.has(article.id)}
            <CheckSquareIcon size={20} class="text-cyan-400" />
          {:else}
            <SquareIcon size={20} />
          {/if}
        </button>

        <div class="relative w-16 h-12 sm:w-32 sm:h-20 rounded-lg sm:rounded-2xl overflow-hidden bg-zinc-900 border border-white/5 shadow-inner">
          {#if article.featuredImage && article.featuredImage.includes('/')}
            <img 
              src={article.featuredImage} 
              alt={article.title}
              class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 opacity-80 group-hover:opacity-100"
            />
          {:else}
            <div class="w-full h-full flex items-center justify-center text-white/5">
              <FileTextIcon size={24} strokeWidth={1} />
            </div>
          {/if}
          
          <!-- Small Mini-Badge for AI on Thumbnail -->
          {#if article.author === "AI Editor" || article.authorName === "AI Editor"}
            <div class="absolute top-1 right-1 p-1 rounded-lg bg-purple-500/20 backdrop-blur-md border border-purple-500/30 text-purple-400">
              <SparklesIcon size={10} />
            </div>
          {/if}
        </div>
      </div>

      <!-- Content Core -->
      <div class="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-8">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-3 mb-1">
            <span class="text-[9px] font-black uppercase tracking-widest text-cyan-500/80 bg-cyan-500/5 px-2 py-0.5 rounded-lg border border-cyan-500/10">
              {article.category || 'Unclassified'}
            </span>
            <div class="flex items-center gap-1 text-[9px] font-mono text-gray-500">
              <CalendarIcon size={10} /> {article.createdAt?.slice(0, 10) || 'N/A'}
            </div>
          </div>
          <h3 class="text-sm sm:text-base font-bold text-white line-clamp-2 sm:truncate group-hover:text-cyan-400 transition-colors">
            {article.title}
          </h3>
          {#if article.slug}
            <div class="flex items-center gap-1.5 text-[10px] text-gray-600 font-mono mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <GlobeIcon size={10} /> /{article.slug}
            </div>
          {/if}
        </div>

        <!-- Meta Grid -->
        <div class="flex items-center gap-6 shrink-0 text-[11px] font-mono">
          <div class="flex flex-col items-center sm:items-start min-w-[60px]">
            <span class="text-[8px] text-gray-600 uppercase tracking-tighter mb-0.5">Status</span>
            {#if article.status === "published"}
              <div class="text-[#39FF14] text-[9px] flex items-center gap-1"><div class="w-1 h-1 rounded-full bg-[#39FF14] shadow-[0_0_5px_#39FF14]"></div>LIVE</div>
            {:else}
              <div class="text-cyan-400 text-[9px]">DRAFT</div>
            {/if}
          </div>

          <div class="flex flex-col items-center sm:items-start min-w-[60px] hidden sm:flex">
            <span class="text-[8px] text-gray-600 uppercase tracking-tighter mb-0.5">Reach</span>
            <div class="flex items-center gap-1.5 text-gray-400">
              <EyeIcon size={12} class="text-cyan-500/40" />
              {(article.views || 0).toLocaleString()}
            </div>
          </div>

          <!-- Vertical Divider -->
          <div class="h-8 w-px bg-white/5 hidden sm:block"></div>

          <!-- Actions Group -->
          <div class="flex items-center gap-1">
            <button
              onclick={() => onEdit(article)}
              class="p-2.5 rounded-xl bg-white/5 hover:bg-cyan-500/20 hover:text-cyan-400 border border-transparent hover:border-cyan-500/30 transition-all"
              title="Edit Stream"
            >
              <PencilIcon size={15} />
            </button>
            <button
              onclick={() => onDelete(article.id)}
              class="p-2.5 rounded-xl bg-white/5 hover:bg-red-500/20 hover:text-red-400 border border-transparent hover:border-red-500/30 transition-all"
              title="Purge Intel"
            >
              <Trash2Icon size={15} />
            </button>
          </div>
        </div>
      </div>

      <!-- Hover Indicator Light -->
      <div class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-cyan-500 rounded-r-full opacity-0 group-hover:opacity-100 transition-opacity blur-[2px]"></div>
    </div>
  {/each}
</div>

<style>
  @reference "tailwindcss";

  .news-row {
    transition: transform 0.3s cubic-bezier(0.23, 1, 0.32, 1), background-color 0.3s ease;
  }
</style>
