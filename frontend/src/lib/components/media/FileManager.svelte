<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { mediaStore } from '$lib/state/media.svelte';
    import { useNanobot } from '$lib/state/nanobot.svelte';
  const nanobot = useNanobot();
    import { vuiController } from '$lib/vui';
    import { fade, slide, scale } from 'svelte/transition';
    import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';
    import type { MediaAsset } from '$lib/state/types';
    import FileToolbar from './FileToolbar.svelte';
    import FileGrid from './FileGrid.svelte';
    import FileList from './FileList.svelte';
    import FileDetailsPanel from './FileDetailsPanel.svelte';
    import ImagePreviewModal from '../admin/ui/ImagePreviewModal.svelte';
    import BulkSEOModal from './BulkSEOModal.svelte';
    import LinkToPostModal from './LinkToPostModal.svelte';
    import HardDeleteModal from './HardDeleteModal.svelte';

    interface Props {
        campaignId?: string;
        onSelect?: (assets: MediaAsset[]) => void;
        standalone?: boolean;
        mode?: 'manage' | 'pick';
        pickTabActive?: 'current' | 'ai' | 'library';
        onPickTabChange?: (tab: string) => void;
        onPickConfirm?: (assets: MediaAsset[]) => void;
        onPickClose?: () => void;
    }

    let { campaignId, onSelect, standalone = false, mode = 'manage', pickTabActive, onPickTabChange, onPickConfirm, onPickClose } = $props<Props>();

    let viewMode = $state<'grid' | 'list'>('grid');
    let searchQuery = $state('');
    let selectedAssetId = $state<string | null>(null);
    let remoteUrl = $state('');
    let showRemoteInput = $state(false);
    let showStats = $state(false);
    let aiVisionEnabled = $state(false);
    let fileInput: HTMLInputElement;

    // -- Post Tracking Filter --
    let showPostFilter = $state(false);
    let filterPostType = $state('');   
    let filterPostId = $state('');
    let showUnlinkedOnly = $state(false);

    // -- Link-to-post modal --
    let showLinkModal = $state(false);

    // -- Hard Delete confirmation --
    let pendingHardDeleteId = $state<string | null>(null);

    // -- Bulk SEO Modal --
    let showBulkSeo = $state(false);
    let isAutoFilling = $state(false);
    let activeVideoUrl = $state<string | null>(null); // State mới cho video overlay
    let previewImageUrl = $state<string | null>(null);

    // AI Semantic Search Debounce
    $effect(() => {
        const query = searchQuery.trim();
        const timeout = setTimeout(() => {
            mediaStore.loadAssets(campaignId, true, query || undefined);
        }, 500);
        return () => clearTimeout(timeout);
    });

    // Neural Sync: Handle Unlinked Only Filter
    $effect(() => {
        if (showUnlinkedOnly) {
            mediaStore.setUnlinkedFilter(false); // Lọc các ảnh CÓ is_linked = false (Mồ côi)
        } else if (mediaStore.isLinkedFilter !== null) {
            mediaStore.setUnlinkedFilter(null); // Tắt lọc mồ côi
        }
    });

    // Voice Mutation Injection
    $effect(() => {
        const action = nanobot.commandAction;
        if (action?.entity === "media" || action?.entity === "image") {
            if (action.verb === "search" && action.args) {
                if (nanobot.consumeCommand("search", "media")) {
                    searchQuery = action.args;
                }
            } else if (action.verb === "select" && action.args) {
                if (nanobot.consumeCommand("select", "media")) {
                    const found = mediaStore.assets.find(a =>
                        a.filename?.toLowerCase().includes(action.args!.toLowerCase()) ||
                        (a.alt_text && a.alt_text.toLowerCase().includes(action.args!.toLowerCase()))
                    );
                    if (found) selectedAssetId = found.id;
                }
            }
        }
    });

    const filteredAssets = $derived(
        mediaStore.assets.filter(asset => {
            const query = searchQuery.toLowerCase().trim();
            let pass = true;
            if (query) {
                const basicMatch = asset.filename?.toLowerCase().includes(query) ||
                                (asset.alt_text && asset.alt_text.toLowerCase().includes(query));
                const aiTags = asset.media_metadata?.ai_tags || [];
                const tagMatch = aiTags.some((tag: string) => tag.toLowerCase().includes(query));
                const vibeMatch = asset.media_metadata?.ai_sentiment?.toLowerCase().includes(query);
                pass = !!(basicMatch || tagMatch || vibeMatch);
            }
            // Elite V2.2: Lọc "Mồ côi" dựa trên flag is_linked tập trung
            if (showUnlinkedOnly && asset.is_linked) pass = false;
            
            // Legacy filters (fallback if needed)
            if (!showUnlinkedOnly && filterPostType && asset.linked_post_type !== filterPostType) pass = false;
            if (!showUnlinkedOnly && filterPostId && asset.linked_post_id !== filterPostId) pass = false;
            return pass;
        })
    );

    const selectedAsset = $derived(
        mediaStore.assets.find(a => a.id === selectedAssetId) || null
    );

    onMount(() => {
        if (mode === 'pick') mediaStore.isTrashMode = false;
        mediaStore.loadAssets(campaignId, true);
        mediaStore.loadStats();
        fetchAIVisionStatus();
    });

    async function fetchAIVisionStatus() {
        try {
            const res = await fetch('/api/v1/media/settings/ai-vision');
            if (res.ok) {
                const data = await res.json();
                aiVisionEnabled = data.enabled;
            }
        } catch (e) {
            console.error("Failed to fetch AI Vision status:", e);
        }
    }

    async function toggleAIVision() {
        try {
            const newState = !aiVisionEnabled;
            aiVisionEnabled = newState;
            const res = await fetch('/api/v1/media/settings/ai-vision', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: newState })
            });
            if (!res.ok) {
                aiVisionEnabled = !newState;
                nanobot.showToast("Không thể thay đổi trạng thái AI Vision", "error");
            } else {
                nanobot.showToast(`Đã ${newState ? 'bật' : 'tắt'} AI Vision`, "success");
            }
        } catch (e) {
            console.error("Failed to toggle AI Vision:", e);
            nanobot.showToast("Không thể thay đổi trạng thái AI Vision", "error");
        }
    }

    onDestroy(() => {
        mediaStore.cleanup();
    });

    function formatSize(bytes: number) {
        return formatBytes(bytes);
    }

    async function handleDelete(id: string) {
        if (mediaStore.isTrashMode) {
            pendingHardDeleteId = id;
        } else {
            const confirmed = await nanobot.showConfirm({
                title: "QUẢN LÝ TÀI NGUYÊN",
                message: "Chuyển ảnh này vào Thùng rác?",
                confirmLabel: "CHUYỂN VÀO THÙNG RÁC"
            });
            if (confirmed) {
                await mediaStore.deleteAsset(id);
                if (selectedAssetId === id) selectedAssetId = null;
            }
        }
    }

    async function confirmHardDelete() {
        if (!pendingHardDeleteId) return;
        await mediaStore.deleteAsset(pendingHardDeleteId, true);
        if (selectedAssetId === pendingHardDeleteId) selectedAssetId = null;
        pendingHardDeleteId = null;
    }

    async function handleRestore(id: string) {
        await mediaStore.restoreAsset(id);
        if (selectedAssetId === id) selectedAssetId = null;
    }

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

    async function handleBulkDelete() {
        if (mediaStore.isTrashMode) {
            const confirmed = await nanobot.showConfirm({
                title: "CẢNH BÁO",
                message: `Sếp có chắc chắn muốn xóa VĨNH VIỄN ${mediaStore.selectedIds.size} ảnh đã chọn?`,
                confirmLabel: "XÓA VĨNH VIỄN"
            });
            if (confirmed) {
                await mediaStore.bulkDelete(true);
            }
        } else {
            const confirmed = await nanobot.showConfirm({
                title: "QUẢN LÝ TÀI NGUYÊN",
                message: `Sếp có chắc chắn muốn chuyển ${mediaStore.selectedIds.size} ảnh vào Thùng rác?`,
                confirmLabel: "CHUYỂN VÀO THÙNG RÁC"
            });
            if (confirmed) {
                await mediaStore.bulkDelete(false);
            }
        }
    }

    async function handleQuickEdit(action: string, params: Record<string, unknown> | null = null) {
        if (!selectedAssetId) return;
        await mediaStore.quickEdit(selectedAssetId, action, params);
    }

    async function handleFileUpload(e: Event) {
        const target = e.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            const { successCount, failCount } = await mediaStore.uploadAssets(target.files);
            target.value = '';
            if (successCount > 0) nanobot.showToast(`Đã tải lên thành công ${successCount} ảnh`, "success");
            if (failCount > 0) nanobot.showToast(`Lỗi kỹ thuật: ${failCount} ảnh không thể tải lên`, "error");
        }
    }

    // Hàm gọi từ FileDetailsPanel
    function playVideo(url: string) {
        activeVideoUrl = url;
    }

    function previewImage(url: string) {
        previewImageUrl = url;
    }
</script>

<div class="file-manager flex flex-col h-full bg-white dark:bg-[#0c0e14] overflow-hidden" class:rounded-xl={!standalone} class:border={!standalone}>
    <ImagePreviewModal imageUrl={previewImageUrl} onClose={() => previewImageUrl = null} />
    <FileToolbar
        {mode}
        {pickTabActive}
        {onPickTabChange}
        bind:searchQuery
        bind:viewMode
        bind:showPostFilter
        bind:filterPostType
        bind:filterPostId
        bind:showUnlinkedOnly
        bind:showStats
        bind:aiVisionEnabled
        {campaignId}
        isUploading={mediaStore.isLoading}
        isAutoFilling={isAutoFilling}
        onUploadClick={() => fileInput?.click()}
        onRemoteUrlClick={() => showRemoteInput = !showRemoteInput}
        onToggleStats={() => showStats = !showStats}
        onToggleAIVision={toggleAIVision}
        onBulkSeoClick={() => showBulkSeo = true}
        onRefresh={() => mediaStore.loadAssets(campaignId, true)}
        onViewModeToggle={() => viewMode = viewMode === 'grid' ? 'list' : 'grid'}
        onPostFilterToggle={() => showPostFilter = !showPostFilter}
        onPickConfirm={onPickConfirm ? () => onPickConfirm(mediaStore.assets.filter(a => mediaStore.selectedIds.has(a.id))) : undefined}
        onPickClose={onPickClose}
    />

    <div class="flex-1 flex overflow-hidden">
        <div class="flex-1 flex flex-col overflow-y-auto p-4 custom-scrollbar">
            {#if mediaStore.isLoading && mediaStore.assets.length === 0}
                <div class="flex items-center justify-center h-64">
                    <div class="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
            {:else if filteredAssets.length === 0}
                <div class="flex flex-col items-center justify-center h-full gap-4 text-zinc-400">
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                    <p>{searchQuery ? 'Không tìm thấy ảnh phù hợp' : 'Chưa có ảnh nào trong thư viện'}</p>
                </div>
            {:else if viewMode === 'grid'}
                <FileGrid
                    assets={filteredAssets}
                    bind:selectedAssetId
                    {mode}
                    {onSelect}
                    onDelete={handleDelete}
                    onRestore={handleRestore}
                    onPreview={previewImage}
                />
            {:else}
                <FileList
                    assets={filteredAssets}
                    bind:selectedAssetId
                    {mode}
                    {onSelect}
                    onDelete={handleDelete}
                    onRestore={handleRestore}
                    onPreview={previewImage}
                />
            {/if}
        </div>

        <FileDetailsPanel
            asset={selectedAsset}
            bind:selectedAssetId
            onDelete={handleDelete}
            onRestore={handleRestore}
            {onSelect}
            {mode}
            onQuickEdit={handleQuickEdit}
            onPlayVideo={playVideo}
            onPreview={previewImage}
        />
    </div>

    <!-- Footer Stats -->
    <div class="p-3 border-t bg-zinc-50 dark:bg-zinc-800/50 flex justify-between items-center text-[10px] text-zinc-500 font-medium overflow-x-auto no-scrollbar whitespace-nowrap">
        <div class="flex gap-4">
            <span>TỔNG CỘNG: {mediaStore.total} TÀI NGUYÊN</span>
            <span>ĐANG HIỂN THỊ: {filteredAssets.length}</span>
            {#if mediaStore.stats}
                <div class="flex gap-2">
                    {#each mediaStore.stats.breakdown.slice(0, 3) as item}
                        <div class="flex items-baseline gap-1" title="{item.count} files">
                            <span class="text-[10px] font-bold text-zinc-600 dark:text-zinc-400">{item.type}:</span>
                            <span class="text-[10px] font-mono text-zinc-500">{Math.round((item.size / mediaStore.stats.total_size) * 100)}%</span>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
        <div class="flex items-center gap-1">
            <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            HỆ THỐNG ĐÃ SẴN SÀNG
        </div>
    </div>

    <!-- Bulk Action Toolbar -->
    {#if mediaStore.selectedIds.size > 0}
        <div class="fixed bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 px-6 py-3 bg-zinc-900 text-white rounded-full shadow-2xl border border-white/10" style="z-index: {Z_INDEX_ADMIN.HUD_SERVICE};" transition:fade>
            <div class="flex items-center gap-2 pr-4 border-r border-white/20">
                <span class="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px] font-bold">
                    {mediaStore.selectedIds.size}
                </span>
                <span class="text-[10px] font-bold uppercase tracking-wider">Đã chọn</span>
            </div>

            <div class="flex items-center gap-3 text-zinc-400">
                <button onclick={() => showLinkModal = true} class="p-1.5 hover:bg-white/10 hover:text-white rounded-lg transition-colors group relative" title="Gán cho bài viết/sản phẩm">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                </button>
                <button onclick={handleMagicWand} class="p-1.5 hover:bg-white/10 hover:text-white rounded-lg transition-colors group relative" class:animate-pulse={isAutoFilling} title="AI Alt-text">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21 11-8-8"/><path d="m21 3-9 9"/><path d="M12 12 3 21"/><path d="m11 21 8-8"/><circle cx="7.5" cy="7.5" r=".5"/><circle cx="10.5" cy="10.5" r=".5"/><circle cx="13.5" cy="13.5" r=".5"/></svg>
                </button>
                <button onclick={() => mediaStore.bulkDownload(Array.from(mediaStore.selectedIds))} class="p-1.5 hover:bg-white/10 hover:text-white rounded-lg transition-colors group relative" title="Tải ZIP">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                </button>
                <button onclick={() => showBulkSeo = true} class="p-1.5 hover:bg-white/10 hover:text-white rounded-lg transition-colors group relative" title="Tối ưu SEO">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
                </button>
                <div class="w-px h-4 bg-white/20 mx-1"></div>
                {#if mediaStore.isTrashMode}
                    <button onclick={() => mediaStore.bulkRestore()} class="p-1.5 hover:bg-green-500 hover:text-white rounded-lg transition-colors text-green-400" title="Khôi phục">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                    </button>
                {/if}
                <button onclick={handleBulkDelete} class="p-1.5 hover:bg-red-500 hover:text-white rounded-lg transition-colors text-red-400" title={mediaStore.isTrashMode ? "Xoá vĩnh viễn" : "Chuyển vào thùng rác"}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                </button>
            </div>
            <button onclick={() => mediaStore.clearSelection()} class="text-[10px] font-black uppercase text-zinc-500 hover:text-white ml-2 transition-colors">Đóng</button>
        </div>
    {/if}

    <BulkSEOModal bind:show={showBulkSeo} bind:isAutoFilling />
    <LinkToPostModal bind:show={showLinkModal} />
    <HardDeleteModal bind:pendingId={pendingHardDeleteId} onConfirm={confirmHardDelete} />

    <!-- Video Full View Overlay -->
    {#if activeVideoUrl}
        <div class="fixed inset-0 bg-black flex flex-col" style="z-index: {Z_INDEX_ADMIN.MODAL_SUB_HIGHER};" transition:fade>
            <button
                onclick={() => activeVideoUrl = null}
                class="absolute top-4 left-4 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-xs font-bold backdrop-blur-md transition-all"
                style="z-index: {Z_INDEX_ADMIN.TOOLBAR_SUB};"
            >
                ← Quay lại Thư viện
            </button>
            <div class="flex-1 flex items-center justify-center p-4">
                <video src={activeVideoUrl} controls autoplay class="max-w-full max-h-full" />
            </div>
        </div>
    {/if}

    <input type="file" accept="image/*,video/*" multiple class="hidden" bind:this={fileInput} onchange={handleFileUpload} />
</div>

<style>
    .file-manager :global(.custom-scrollbar::-webkit-scrollbar) { width: 4px; height: 4px; }
    .file-manager :global(.custom-scrollbar::-webkit-scrollbar-track) { background: transparent; }
    .file-manager :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(255,255,255,0.08); border-radius: 20px; }
    .file-manager :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) { background: rgba(255,255,255,0.15); }

    @keyframes scan-loop {
        0% { top: 0; opacity: 0.8; }
        50% { opacity: 0.4; }
        100% { top: 100%; opacity: 0; }
    }

    .file-manager :global(.animate-scan-loop) {
        animation: scan-loop 2.5s ease-in-out infinite;
    }
</style>
