<script lang="ts">
  import ChevronLeft from "lucide-svelte/icons/chevron-left";
  import ChevronRight from "lucide-svelte/icons/chevron-right";

  let {
    currentPage = $bindable(),
    totalPages,
    pageSize,
    totalItems
  } = $props<{
    currentPage: number;
    totalPages: number;
    pageSize: number;
    totalItems: number;
  }>();

  // R82: Safe initialization for bindable prop
  onMount(() => {
    if (currentPage === undefined) currentPage = 1;
  });
</script>

{#if totalPages > 1}
  <div class="sticky bottom-0 z-20 px-6 py-3 flex items-center justify-end gap-4">
    <span class="text-[9px] font-mono text-gray-600 uppercase tracking-widest">
      Viewing {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, totalItems)} of {totalItems}
    </span>

    <div class="flex items-center gap-0.5">
      <button 
        onclick={() => currentPage > 1 && (currentPage -= 1)}
        disabled={currentPage === 1}
        class="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-white disabled:opacity-20 transition-colors"
      >
        <ChevronLeft size={14} />
      </button>
      
      {#each Array(totalPages) as _, i}
        {@const page = i + 1}
        {#if page === 1 || page === totalPages || (page >= currentPage - 1 && page <= currentPage + 1)}
          <button 
            onclick={() => currentPage = page}
            class="w-6 h-6 flex items-center justify-center text-[9px] font-mono font-bold transition-colors
              {currentPage === page ? 'text-neon-cyan' : 'text-gray-600 hover:text-white'}"
          >
            {page}
          </button>
        {:else if page === currentPage - 2 || page === currentPage + 2}
          <span class="text-gray-700 text-[9px] px-0.5 font-mono">…</span>
        {/if}
      {/each}
      
      <button 
        onclick={() => currentPage < totalPages && (currentPage += 1)}
        disabled={currentPage === totalPages}
        class="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-white disabled:opacity-20 transition-colors"
      >
        <ChevronRight size={14} />
      </button>
    </div>
  </div>
{/if}
