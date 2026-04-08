<script lang="ts">
    import { fade, slide } from 'svelte/transition';
    import { mediaStore } from '$lib/state/media.svelte';
    import { useNanobot } from '$lib/state/nanobot.svelte';
    import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';
    import { portal } from '$lib/core/actions/portal';

    interface Props {
        show: boolean;
    }

    let { show = $bindable() } = $props<Props>();
    const nanobot = useNanobot();

    let linkPostId = $state('');
    let linkPostType = $state<'news' | 'product'>('news');

    async function handleLinkToPost() {
        if (!linkPostId.trim() || !linkPostType) return;
        await mediaStore.linkToPost(linkPostId.trim(), linkPostType);
        show = false;
        linkPostId = '';
        nanobot.showToast(`Đã gắn ${mediaStore.selectedIds.size} ảnh vào ${linkPostType} thành công`, "success");
    }
</script>

{#if show}
    <div use:portal class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center" style="z-index: {Z_INDEX_ADMIN.MODAL_SUB};" transition:fade>
        <div class="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 w-full max-w-sm overflow-hidden" transition:slide>
            <div class="p-4 border-b flex items-center justify-between bg-zinc-50 dark:bg-zinc-800/50">
                <h3 class="font-bold text-[10px] uppercase tracking-wider">GẮN ẢNH VÀO BÀI VIẾT / SẢN PHẨM</h3>
                <button aria-label="Đóng" onclick={() => show = false} class="text-zinc-500 hover:text-zinc-700">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
            <div class="p-5 space-y-4">
                <div class="grid grid-cols-2 gap-2">
                    <button onclick={() => linkPostType = 'news'} class="py-2.5 rounded-xl border-2 transition-all {linkPostType === 'news' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600' : 'border-zinc-100 dark:border-zinc-800 text-zinc-500'} font-black text-[10px] uppercase">Article</button>
                    <button onclick={() => linkPostType = 'product'} class="py-2.5 rounded-xl border-2 transition-all {linkPostType === 'product' ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20 text-orange-600' : 'border-zinc-100 dark:border-zinc-800 text-zinc-500'} font-black text-[10px] uppercase">Product</button>
                </div>
                <input type="text" bind:value={linkPostId} placeholder="ID bài viết / SKU..." class="w-full px-4 py-3 bg-zinc-50 dark:bg-zinc-800 border rounded-xl outline-none focus:ring-2 focus:ring-blue-500 text-xs font-mono" />
            </div>
            <div class="p-4 bg-zinc-50 dark:bg-zinc-800/50 border-t flex justify-end gap-3">
                <button onclick={() => show = false} class="px-4 py-2 text-[10px] font-black text-zinc-500 uppercase">Huỷ</button>
                <button onclick={handleLinkToPost} disabled={!linkPostId.trim()} class="px-6 py-2.5 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-xl text-[10px] font-black uppercase disabled:opacity-50">XÁC NHẬN</button>
            </div>
        </div>
    </div>
{/if}
