<script lang="ts">
    import { fade, scale } from 'svelte/transition';
    import { mediaStore } from '$lib/state/media.svelte';
    import { vuiController } from '$lib/vui';
    import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';
    import { portal } from '$lib/core/actions/portal';

    interface Props {
        show: boolean;
        isAutoFilling: boolean;
    }

    let { show = $bindable(), isAutoFilling = $bindable() } = $props<Props>();

    async function handleMagicWand() {
        if (isAutoFilling) return;
        isAutoFilling = true;
        try {
            const ids = Array.from(mediaStore.selectedIds);
            await mediaStore.aiAutoFillAltText(ids);
            vuiController.speak("Đã tự động điền Alt-text cho các ảnh được chọn.");
        } finally {
            isAutoFilling = false;
        }
    }

    async function handleBulkSeoSave() {
        const selectedAssets = mediaStore.assets.filter(a => mediaStore.selectedIds.has(a.id));
        const updates = selectedAssets.map(a => ({
            id: a.id,
            metadata: { alt_text: a.alt_text }
        }));
        await mediaStore.bulkUpdateMetadata(updates);
        vuiController.speak(`Đã tối ưu SEO cho ${updates.length} tài nguyên.`);
        show = false;
    }
</script>

{#if show}
    <div use:portal class="fixed inset-0 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md" style="z-index: {Z_INDEX_ADMIN.MODAL};" transition:fade>
        <div class="bg-white dark:bg-zinc-900 w-full max-w-4xl max-h-[80vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-white/10" transition:scale>
            <div class="p-6 border-b flex justify-between items-center bg-zinc-50 dark:bg-zinc-800/50">
                <div class="flex items-center gap-4">
                    <div>
                        <h3 class="text-lg font-bold">Bulk SEO Editor</h3>
                        <p class="text-xs text-zinc-500">Đang tối ưu {mediaStore.selectedIds.size} ảnh được chọn</p>
                    </div>
                    <button onclick={handleMagicWand} disabled={isAutoFilling} class="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-xs font-bold transition-all shadow-lg shadow-blue-500/20 animate-pulse">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m2 22 1-1h3l9-9"/><path d="M3 21v-3l9-9"/><path d="m15 6 3.4-3.4a2.1 2.1 0 1 1 3 3L18 9l-3-3Z"/><path d="m9.5 15.5 3 3"/></svg>
                        {isAutoFilling ? 'ĐANG PHÂN TÍCH...' : 'MAGIC WAND (AI)'}
                    </button>
                </div>
                <button aria-label="Đóng" onclick={() => show = false} class="p-2 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-full transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
            <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
                <div class="space-y-6">
                    {#each mediaStore.assets.filter(a => mediaStore.selectedIds.has(a.id)) as asset}
                        <div class="flex gap-4 p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl border border-zinc-100 dark:border-zinc-700/50 group">
                            <div class="w-32 h-32 rounded-lg overflow-hidden bg-zinc-200 dark:bg-zinc-800 flex-shrink-0 relative">
                                <img src={asset.id?.startsWith('tmp_') ? asset.file_path : `/api/v1/media/${asset.id}/thumb?w=400`} alt="" class="w-full h-full object-cover" />
                            </div>
                            <div class="flex-1 flex flex-col gap-3">
                                <div class="flex justify-between items-start">
                                    <span class="text-xs font-bold truncate max-w-[200px]">{asset.filename}</span>
                                </div>
                                <textarea bind:value={asset.alt_text} class="w-full p-2 text-xs bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none h-16 transition-all" placeholder="Alt-text (SEO)..."></textarea>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
            <div class="p-6 border-t bg-zinc-50 dark:bg-zinc-800/50 flex justify-end gap-3">
                <button onclick={() => show = false} class="px-6 py-2 border border-zinc-200 dark:border-zinc-700 text-zinc-500 rounded-xl text-xs font-bold hover:bg-zinc-100 dark:hover:bg-zinc-800">HỦY</button>
                <button onclick={handleBulkSeoSave} class="px-6 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:scale-105 shadow-lg shadow-blue-500/20">LƯU TẤT CẢ ({mediaStore.selectedIds.size})</button>
            </div>
        </div>
    </div>
{/if}

<style>
    .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 20px; }
    :global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); }
</style>
