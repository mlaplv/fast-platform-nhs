<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { mediaStore } from '$lib/state/media.svelte';
    import { nanobot } from '$lib/state/nanobot.svelte';
    import { vuiController } from '$lib/vui';
    import { fade, slide, scale } from 'svelte/transition';
    import { Z_INDEX } from '$lib/core/constants/zIndex';
    import type { MediaAsset } from '$lib/state/types';
    import FileToolbar from './FileToolbar.svelte';
    import FileGrid from './FileGrid.svelte';
    import FileList from './FileList.svelte';
    import FileDetailsPanel from './FileDetailsPanel.svelte';

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
    let linkPostId = $state('');
    let linkPostType = $state<'news' | 'product'>('news');

    // -- Hard Delete confirmation --
    let pendingHardDeleteId = $state<string | null>(null);

    // -- Bulk SEO Modal --
    let showBulkSeo = $state(false);
    let isAutoFilling = $state(false);

    // AI Semantic Search Debounce
    $effect(() => {
        const query = searchQuery.trim();
        const timeout = setTimeout(() => {
            mediaStore.loadAssets(campaignId, true, query || undefined);
        }, 500);
        return () => clearTimeout(timeout);
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
            if (showUnlinkedOnly && asset.linked_post_id) pass = false;
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
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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

    async function handleBulkSeoSave() {
        const selectedAssets = mediaStore.assets.filter(a => mediaStore.selectedIds.has(a.id));
        const updates = selectedAssets.map(a => ({
            id: a.id,
            metadata: { alt_text: a.alt_text }
        }));
        await mediaStore.bulkUpdateMetadata(updates);
        vuiController.speak(`Đã tối ưu SEO cho ${updates.length} tài nguyên.`);
        showBulkSeo = false;
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

    async function handleLinkToPost() {
        if (!linkPostId.trim() || !linkPostType) return;
        await mediaStore.linkToPost(linkPostId.trim(), linkPostType);
        showLinkModal = false;
        linkPostId = '';
        nanobot.showToast(`Đã gắn ${mediaStore.selectedIds.size} ảnh vào ${linkPostType} thành công`, "success");
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
</script>

<div class="file-manager flex flex-col h-full bg-white dark:bg-[#0c0e14] overflow-hidden" class:rounded-xl={!standalone} class:border={!standalone}>
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
                />
            {:else}
                <FileList
                    assets={filteredAssets}
                    bind:selectedAssetId
                    {mode}
                    {onSelect}
                    onDelete={handleDelete}
                    onRestore={handleRestore}
                />
            {/if}
        </div>

        <FileDetailsPanel
            asset={selectedAsset}
            bind:selectedAssetId
            onDelete={handleDelete}
            onRestore={handleRestore}
            {onSelect}
            onQuickEdit={handleQuickEdit}
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
        <div class="fixed bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 px-6 py-3 bg-zinc-900 text-white rounded-full shadow-2xl border border-white/10 z-[100]" transition:fade>
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

    <!-- [Bulk SEO Modal] -->
    {#if showBulkSeo}
        <div class="fixed inset-0 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md" style="z-index: {Z_INDEX.POPOVER};" transition:fade>
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
                    <button onclick={() => showBulkSeo = false} class="p-2 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-full transition-colors"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
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
                    <button onclick={() => showBulkSeo = false} class="px-6 py-2 border border-zinc-200 dark:border-zinc-700 text-zinc-500 rounded-xl text-xs font-bold hover:bg-zinc-100 dark:hover:bg-zinc-800">HỦY</button>
                    <button onclick={handleBulkSeoSave} class="px-6 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:scale-105 shadow-lg shadow-blue-500/20">LƯU TẤT CẢ ({mediaStore.selectedIds.size})</button>
                </div>
            </div>
        </div>
    {/if}

    <!-- [Link to Post Modal] -->
    {#if showLinkModal}
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[200]" transition:fade>
            <div class="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 w-full max-w-sm overflow-hidden" transition:slide>
                <div class="p-4 border-b flex items-center justify-between bg-zinc-50 dark:bg-zinc-800/50">
                    <h3 class="font-bold text-[10px] uppercase tracking-wider">GẮN ẢNH VÀO BÀI VIẾT / SẢN PHẨM</h3>
                    <button onclick={() => showLinkModal = false} class="text-zinc-500 hover:text-zinc-700"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
                </div>
                <div class="p-5 space-y-4">
                    <div class="grid grid-cols-2 gap-2">
                        <button onclick={() => linkPostType = 'news'} class="py-2.5 rounded-xl border-2 transition-all {linkPostType === 'news' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600' : 'border-zinc-100 dark:border-zinc-800 text-zinc-500'} font-black text-[10px] uppercase">Article</button>
                        <button onclick={() => linkPostType = 'product'} class="py-2.5 rounded-xl border-2 transition-all {linkPostType === 'product' ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20 text-orange-600' : 'border-zinc-100 dark:border-zinc-800 text-zinc-500'} font-black text-[10px] uppercase">Product</button>
                    </div>
                    <input type="text" bind:value={linkPostId} placeholder="ID bài viết / SKU..." class="w-full px-4 py-3 bg-zinc-50 dark:bg-zinc-800 border rounded-xl outline-none focus:ring-2 focus:ring-blue-500 text-xs font-mono" />
                </div>
                <div class="p-4 bg-zinc-50 dark:bg-zinc-800/50 border-t flex justify-end gap-3">
                    <button onclick={() => showLinkModal = false} class="px-4 py-2 text-[10px] font-black text-zinc-500 uppercase">Huỷ</button>
                    <button onclick={handleLinkToPost} disabled={!linkPostId.trim()} class="px-6 py-2.5 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-xl text-[10px] font-black uppercase disabled:opacity-50">XÁC NHẬN</button>
                </div>
            </div>
        </div>
    {/if}

    <!-- [Hard Delete Modal] -->
    {#if pendingHardDeleteId}
        <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-[210]" transition:fade>
            <div class="bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl border border-red-500/20 w-full max-w-sm overflow-hidden" transition:slide>
                <div class="p-8 text-center space-y-4">
                    <div class="w-20 h-20 bg-red-100 dark:bg-red-900/30 text-red-600 rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce"><svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg></div>
                    <h3 class="text-xl font-black text-red-600 uppercase italic tracking-tighter">XOÁ TRIỆT ĐỂ</h3>
                    <p class="text-[11px] text-zinc-500">Hành động này KHÔNG THỂ KHÔI PHỤC.</p>
                </div>
                <div class="p-6 bg-zinc-50 dark:bg-zinc-800/50 border-t grid grid-cols-2 gap-4">
                    <button onclick={() => pendingHardDeleteId = null} class="py-4 bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-200 rounded-2xl text-[10px] font-black uppercase">HUỶ</button>
                    <button onclick={confirmHardDelete} class="py-4 bg-red-600 text-white rounded-2xl text-[10px] font-black uppercase">XOÁ VĨNH VIỄN</button>
                </div>
            </div>
        </div>
    {/if}

    <input type="file" accept="image/*" multiple class="hidden" bind:this={fileInput} onchange={handleFileUpload} />
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
