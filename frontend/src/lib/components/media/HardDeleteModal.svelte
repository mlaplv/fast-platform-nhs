<script lang="ts">
    import { fade, slide } from 'svelte/transition';
    import { mediaStore } from '$lib/state/media.svelte';
    import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';
    import { portal } from '$lib/core/actions/portal';

    interface Props {
        pendingId: string | null;
        onConfirm: () => void;
    }

    let { pendingId = $bindable(), onConfirm } = $props<Props>();
</script>

{#if pendingId}
    <div use:portal class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center" style="z-index: {Z_INDEX_ADMIN.MODAL_SUB_HIGH};" transition:fade>
        <div class="bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl border border-red-500/20 w-full max-w-sm overflow-hidden" transition:slide>
            <div class="p-8 text-center space-y-4">
                <div class="w-20 h-20 bg-red-100 dark:bg-red-900/30 text-red-600 rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                </div>
                <h3 class="text-xl font-black text-red-600 italic tracking-tighter">XOÁ TRIỆT ĐỂ</h3>
                <p class="text-[11px] text-zinc-500">Hành động này KHÔNG THỂ KHÔI PHỤC.</p>
            </div>
            <div class="p-6 bg-zinc-50 dark:bg-zinc-800/50 border-t grid grid-cols-2 gap-4">
                <button onclick={() => pendingId = null} class="py-4 bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-200 rounded-2xl text-[10px] font-black ">HUỶ</button>
                <button onclick={onConfirm} class="py-4 bg-red-600 text-white rounded-2xl text-[10px] font-black ">XOÁ VĨNH VIỄN</button>
            </div>
        </div>
    </div>
{/if}
