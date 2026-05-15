<script lang="ts">
  /**
   * NeuralCleanMenu.svelte — Neural Clean Options Dropdown
   * Component split from Toolbar.svelte to maintain < 500 lines.
   * Elite V2.7: Strictly typed, no any, high-performance logic.
   */
  import { fade } from 'svelte/transition';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import type { CleanOptions } from '$lib/state/xohiActions';

  let {
    showCleanOptions = $bindable(),
    cleanPopupPos,
    cleanOptions = $bindable(),
    onClean
  }: {
    showCleanOptions: boolean;
    cleanPopupPos: { top: number; left: number };
    cleanOptions: CleanOptions;
    onClean: ((options: CleanOptions) => void) | null;
  } = $props();
</script>

{#if showCleanOptions}
  <div 
       use:portal
       class="fixed bg-[#0d0d0d] border border-white/10 rounded-xl p-4 shadow-[0_30px_60px_rgba(0,0,0,0.8)] flex flex-col gap-4 min-w-[220px]"
       style="top: {cleanPopupPos.top}px; left: {cleanPopupPos.left}px; transform: translateX(-100%); z-index: {Z_INDEX_ADMIN.TIPTAP_TOOLBAR_DROPDOWN}"
  >
    <div class="flex flex-col gap-1">
      <span class="text-[10px] font-black tracking-widest text-orange-500">Neural Clean</span>
      <span class="text-[8px] text-white/40">Select optimization parameters</span>
    </div>

    <div class="flex flex-col gap-3 py-2">
      <label class="flex items-center gap-3 cursor-pointer group">
        <input type="checkbox" bind:checked={cleanOptions.stripFont} class="w-3 h-3 rounded border-white/10 bg-white/5 text-orange-500 focus:ring-0" />
        <span class="text-[9px] font-bold text-white/60 group-hover:text-white transition-colors">Clear Font Families</span>
      </label>
      <label class="flex items-center gap-3 cursor-pointer group">
        <input type="checkbox" bind:checked={cleanOptions.stripAlign} class="w-3 h-3 rounded border-white/10 bg-white/5 text-orange-500 focus:ring-0" aria-label="Reset Text Alignment" />
        <span class="text-[9px] font-bold text-white/60 group-hover:text-white transition-colors">Reset Text Alignment</span>
      </label>
      <label class="flex items-center gap-3 cursor-pointer group">
        <input type="checkbox" bind:checked={cleanOptions.stripRedundantWrappers} class="w-3 h-3 rounded border-white/10 bg-white/5 text-orange-500 focus:ring-0" aria-label="Prune Redundant Tags" />
        <span class="text-[9px] font-bold text-white/60 group-hover:text-white transition-colors">Prune Redundant Tags</span>
      </label>
      <label class="flex items-center gap-3 cursor-pointer group">
        <input type="checkbox" bind:checked={cleanOptions.stripEmpty} class="w-3 h-3 rounded border-white/10 bg-white/5 text-orange-500 focus:ring-0" aria-label="Purge Empty Elements" />
        <span class="text-[9px] font-bold text-white/60 group-hover:text-white transition-colors">Purge Empty Elements</span>
      </label>
      <label class="flex items-center gap-3 cursor-pointer group">
        <input type="checkbox" bind:checked={cleanOptions.deduplicateContent} class="w-3 h-3 rounded border-white/10 bg-white/5 text-orange-500 focus:ring-0" aria-label="Neural Deduplication" />
        <span class="text-[9px] font-bold text-white/60 group-hover:text-white transition-colors">Neural Deduplication</span>
      </label>
      <label class="flex items-center gap-3 cursor-pointer group">
        <input type="checkbox" bind:checked={cleanOptions.stripLinks} class="w-3 h-3 rounded border-white/10 bg-white/5 text-orange-500 focus:ring-0" aria-label="Remove All Links" />
        <span class="text-[9px] font-bold text-white/60 group-hover:text-white transition-colors text-rose-400">Strip All Hyperlinks</span>
      </label>
    </div>

    <button 
      onclick={() => { onClean?.(cleanOptions); showCleanOptions = false; }}
      class="w-full py-2 bg-orange-500 text-black text-[9px] font-black tracking-widest rounded-lg hover:bg-orange-400 transition-all active:scale-95 shadow-lg shadow-orange-500/20"
    >
      Execute Neural Clean
    </button>
  </div>
  <div 
    use:portal 
    transition:fade={{ duration: 150 }} 
    class="fixed inset-0 cursor-default" 
    style="z-index: {Z_INDEX_ADMIN.TIPTAP_TOOLBAR_OVERLAY}" 
    onclick={() => showCleanOptions = false}
    onkeydown={(e) => e.key === 'Escape' && (showCleanOptions = false)}
    role="button"
    tabindex="-1"
    aria-label="Close Clean Options"
  ></div>
{/if}
