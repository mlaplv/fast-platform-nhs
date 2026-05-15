<script lang="ts">
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";

  import { onMount } from "svelte";

  let { 
    currentPage = $bindable(), 
    totalPages, 
    pageSize, 
    totalItems,
    onPageChange
  } = $props<{
    currentPage: number;
    totalPages: number;
    pageSize: number;
    totalItems: number;
    onPageChange?: () => void;
  }>();

  let pages = $derived.by(() => {
    const items: (number | string)[] = [];
    for (let i = 1; i <= totalPages; i++) {
      if (
        i === 1 ||
        i === totalPages ||
        (i >= currentPage - 1 && i <= currentPage + 1)
      ) {
        items.push(i);
      } else if (i === currentPage - 2 || i === currentPage + 2) {
        items.push("…");
      }
    }
    return items;
  });

  onMount(() => {
    if (currentPage === undefined) currentPage = 1;
  });
</script>

{#if totalPages > 1}
  <div
    class="sticky bottom-0 bg-[#050505] px-4 py-2 flex items-center justify-end gap-4 border-t border-white/5 admin-pagination-footer"
    style="z-index: var(--z-sticky-header);"
  >
    <span class="text-[9px] font-mono text-gray-600 tracking-widest">
      Viewing {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, totalItems)} of {totalItems}
    </span>

    <div class="flex items-center gap-0.5">
      <button
        onclick={() => { if (currentPage > 1) { currentPage -= 1; onPageChange?.(); } }}
        disabled={currentPage === 1}
        class="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-white disabled:opacity-20 transition-colors"
      >
        <ChevronLeft size={14} />
      </button>

      {#each pages as page}
        {#if typeof page === 'number'}
          <button
            onclick={() => { currentPage = page; onPageChange?.(); }}
            class="w-6 h-6 flex items-center justify-center text-[9px] font-mono font-bold transition-colors
              {currentPage === page ? 'text-neon-cyan' : 'text-gray-600 hover:text-white'}"
          >
            {page}
          </button>
        {:else}
          <span class="text-gray-700 text-[9px] px-0.5 font-mono">{page}</span>
        {/if}
      {/each}

      <button
        onclick={() => { if (currentPage < totalPages) { currentPage += 1; onPageChange?.(); } }}
        disabled={currentPage === totalPages}
        class="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-white disabled:opacity-20 transition-colors"
      >
        <ChevronRight size={14} />
      </button>
    </div>
  </div>
{/if}
