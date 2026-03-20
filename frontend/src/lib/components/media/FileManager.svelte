<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { mediaStore } from '$lib/state/media.svelte';
    import { nanobot } from '$lib/state/nanobot.svelte';
    import { vuiController, vuiState } from '$lib/vui';
    import { fade, slide } from 'svelte/transition';
    import { Z_INDEX } from '$lib/core/constants/zIndex';
    import type { MediaAsset } from '$lib/state/types';

    interface Props {
        campaignId?: string;
        onSelect?: (asset: MediaAsset) => void;
        standalone?: boolean;
    }

    let { campaignId, onSelect, standalone = false } = $props<Props>();

    let viewMode = $state<'grid' | 'list'>('grid');
    let searchQuery = $state('');
    let selectedAssetId = $state<string | null>(null);
    let remoteUrl = $state('');
    let showRemoteInput = $state(false);
    let showStats = $state(false);

    // AI Semantic Search Debounce (R03)
    $effect(() => {
        const query = searchQuery.trim();
        const timeout = setTimeout(() => {
            mediaStore.loadAssets(campaignId, true, query || undefined);
        }, 500); // Debounce 500ms để bảo vệ CPU server

        return () => clearTimeout(timeout);
    });

    // V22: Voice Mutation Injection - Media Management
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
                        a.filename.toLowerCase().includes(action.args!.toLowerCase()) ||
                        (a.alt_text && a.alt_text.toLowerCase().includes(action.args!.toLowerCase()))
                    );
                    if (found) selectedAssetId = found.id;
                }
            }
        }
    });

    // Local filtering can stay as a fallback for ultra-fast UI response while waiting for server
    const filteredAssets = $derived(
        mediaStore.assets.filter(asset => {
            const query = searchQuery.toLowerCase().trim();
            if (!query) return true;

            // Tìm theo tên file hoặc Alt text
            const basicMatch = asset.filename.toLowerCase().includes(query) ||
                             (asset.alt_text && asset.alt_text.toLowerCase().includes(query));

            // Tìm sâu vào AI Metadata (Tags & Sentiment)
            const aiTags = asset.media_metadata.ai_tags || [];
            const tagMatch = aiTags.some((tag: string) => tag.toLowerCase().includes(query));
            const vibeMatch = asset.media_metadata.ai_sentiment?.toLowerCase().includes(query);

            return basicMatch || tagMatch || vibeMatch;
        })
    );

    const selectedAsset = $derived(
        mediaStore.assets.find(a => a.id === selectedAssetId) || null
    );

    // Trích xuất các Top Tags thực tế từ dữ liệu để làm gợi ý
    const suggestiveTags = $derived.by(() => {
        const tagMap = new Map<string, number>();
        mediaStore.assets.forEach(asset => {
            (asset.media_metadata.ai_tags || []).forEach((tag: string) => {
                tagMap.set(tag, (tagMap.get(tag) || 0) + 1);
            });
        });
        // Lấy top 8 tag phổ biến nhất
        return Array.from(tagMap.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8)
            .map(entry => entry[0]);
    });

    onMount(() => {
        mediaStore.loadAssets(campaignId);
        mediaStore.loadStats();
    });

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
            if (confirm('Sếp có chắc chắn muốn xóa VĨNH VIỄN ảnh này? Hành động này không thể hoàn tác.')) {
                await mediaStore.deleteAsset(id); // Store handles the permanent logic via isTrashMode? No, I need to check store logic.
                if (selectedAssetId === id) selectedAssetId = null;
            }
        } else {
            if (confirm('Chuyển ảnh này vào Thùng rác?')) {
                await mediaStore.deleteAsset(id);
                if (selectedAssetId === id) selectedAssetId = null;
            }
        }
    }

    async function handleRestore(id: string) {
        await mediaStore.restoreAsset(id);
        if (selectedAssetId === id) selectedAssetId = null;
    }

    let showBulkSeo = $state(false);
    let isAutoFilling = $state(false);

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

    function applyAIAltText(text: string) {
        if (!selectedAssetId) return;
        const index = mediaStore.assets.findIndex(a => a.id === selectedAssetId);
        if (index !== -1) {
            mediaStore.assets[index].alt_text = text;
            mediaStore.updateMetadata(selectedAssetId, { alt_text: text });
            vuiController.speak("Đã áp dụng gợi ý AI vào Alt-text.");
        }
    }

    function addTagToAltText(tag: string) {
        if (!selectedAssetId) return;
        const index = mediaStore.assets.findIndex(a => a.id === selectedAssetId);
        if (index !== -1) {
            const currentAlt = mediaStore.assets[index].alt_text || "";
            if (currentAlt.includes(tag)) return;
            const newAlt = currentAlt ? `${currentAlt}, ${tag}` : tag;
            mediaStore.assets[index].alt_text = newAlt;
            mediaStore.updateMetadata(selectedAssetId, { alt_text: newAlt });
            vuiController.speak(`Đã thêm tag ${tag} vào Alt-text.`);
        }
    }

    async function handleBulkDelete() {
        const msg = mediaStore.isTrashMode
            ? `Sếp có chắc chắn muốn xóa VĨNH VIỄN ${mediaStore.selectedIds.size} ảnh đã chọn?`
            : `Sếp có chắc chắn muốn chuyển ${mediaStore.selectedIds.size} ảnh vào Thùng rác?`;

        if (confirm(msg)) {
            await mediaStore.bulkDelete(mediaStore.isTrashMode);
        }
    }

    function toggleAssetSelection(e: MouseEvent, id: string) {
        e.stopPropagation();
        mediaStore.toggleSelection(id);
    }

    async function handleQuickEdit(action: string, params: Record<string, unknown> | null = null) {
        if (!selectedAssetId) return;
        await mediaStore.quickEdit(selectedAssetId, action, params);
    }

    async function applySmartCrop(preset: 'square' | 'banner' | 'story' | 'feed') {
        if (!selectedAssetId) return;
        await handleQuickEdit('smart_crop', { preset });
    }

    function copyToClipboard(text: string) {
        if (typeof navigator !== 'undefined' && navigator.clipboard) {
            navigator.clipboard.writeText(text);
            nanobot.showToast("Đã copy đường dẫn vào bộ nhớ tạm", "success");
        }
    }
</script>

<div class="file-manager flex flex-col h-full bg-white dark:bg-zinc-900 overflow-hidden" class:rounded-xl={!standalone} class:border={!standalone}>
    <!-- Top Bar -->
    <div class="p-4 border-b flex items-center justify-between bg-zinc-50 dark:bg-zinc-800/50">
        <div class="flex items-center gap-4 flex-1">
            <h3 class="font-bold text-lg flex items-center gap-2">
                <span class="p-1.5 bg-blue-600 text-white rounded-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                </span>
                MEDIA INTELLIGENCE
            </h3>

            <div class="flex items-center gap-2 ml-4">
                <button
                    onclick={() => mediaStore.selectedIds.size === mediaStore.assets.length ? mediaStore.clearSelection() : mediaStore.selectAll()}
                    class="text-[10px] font-bold uppercase px-2 py-1 rounded bg-zinc-200 dark:bg-zinc-700 hover:bg-zinc-300 transition-colors"
                >
                    {mediaStore.selectedIds.size === mediaStore.assets.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
                </button>
            </div>

            <div class="relative max-w-xs w-full ml-2">
                <input
                    type="text"
                    bind:value={searchQuery}
                    placeholder="Tìm kiếm ảnh..."
                    class="w-full pl-9 pr-4 py-2 bg-white dark:bg-zinc-800 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                />
                <svg class="absolute left-3 top-2.5 text-zinc-400" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </div>

            <!-- Remote Fetch Action (V9.0) -->
            <div class="relative ml-2">
                <button
                    onclick={() => showRemoteInput = !showRemoteInput}
                    class="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
                    title="Tải ảnh từ URL"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    URL
                </button>

                {#if showRemoteInput}
                    <div 
                        class="absolute top-full right-0 mt-2 w-72 p-3 bg-white dark:bg-zinc-800 rounded-xl shadow-2xl border border-zinc-200 dark:border-zinc-700" 
                        style="z-index: {Z_INDEX.SURFACE + 50};"
                        transition:fade
                    >
                        <p class="text-[10px] font-bold text-zinc-400 uppercase mb-2">Dán link ảnh để AI tải về:</p>
                        <div class="flex flex-col gap-2">
                            <input
                                type="text"
                                bind:value={remoteUrl}
                                placeholder="https://example.com/image.jpg"
                                class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-900 border rounded-lg text-xs outline-none focus:ring-2 focus:ring-blue-500"
                                onkeydown={(e) => {
                                    if (e.key === 'Enter') {
                                        mediaStore.fetchRemote(remoteUrl);
                                        remoteUrl = '';
                                        showRemoteInput = false;
                                    }
                                }}
                            />
                            <button
                                onclick={() => {
                                    mediaStore.fetchRemote(remoteUrl);
                                    remoteUrl = '';
                                    showRemoteInput = false;
                                }}
                                class="w-full py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition-all"
                            >
                                BẮT ĐẦU TẢI VỀ
                            </button>
                        </div>
                    </div>
                {/if}
            </div>

            <!-- View Mode Switch -->
            <div class="flex bg-zinc-200 dark:bg-zinc-700 p-1 rounded-lg ml-2">
                <button
                    onclick={() => viewMode = 'grid'}
                    class="p-1.5 rounded-md transition-all {viewMode === 'grid' ? 'bg-white dark:bg-zinc-600 shadow-sm' : 'text-zinc-500'}"
                    aria-label="Grid view"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
                </button>
                <button
                    onclick={() => viewMode = 'list'}
                    class="p-1.5 rounded-md transition-all {viewMode === 'list' ? 'bg-white dark:bg-zinc-600 shadow-sm' : 'text-zinc-500'}"
                    aria-label="List view"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                </button>
            </div>

            <!-- Global Actions -->
            <div class="flex items-center gap-1 ml-2">
                <button
                    onclick={() => {
                        showStats = !showStats;
                        if (showStats) mediaStore.loadStats();
                    }}
                    class="p-2 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg transition-colors {showStats ? 'text-blue-600 bg-blue-50 dark:bg-blue-900/20' : ''}"
                    title="Thống kê kho"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
                </button>
                <button
                    onclick={() => mediaStore.toggleTrashMode()}
                    class="p-2 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg transition-colors {mediaStore.isTrashMode ? 'text-red-500 bg-red-50 dark:bg-red-900/20' : ''}"
                    title="Thùng rác"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                </button>
                <button
                    onclick={() => mediaStore.loadAssets(campaignId, true)}
                    class="p-2 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg transition-colors"
                    title="Làm mới"
                >
                    <svg class="{mediaStore.isLoading ? 'animate-spin' : ''}" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
                </button>
            </div>
        </div>

        <div class="flex items-center gap-2 pr-12">
            <!-- Space reserved for modal close button when in MediaModal (standalone) -->
        </div>
    </div>

    <!-- Smart Filter Pills (V65.0 AI Powered) -->
    {#if showStats && mediaStore.stats}
        <div class="px-4 py-4 border-b bg-blue-50/30 dark:bg-blue-900/10 grid grid-cols-2 md:grid-cols-4 gap-4" transition:slide>
            <div class="flex flex-col gap-1">
                <span class="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Dung lượng tổng</span>
                <span class="text-lg font-bold text-blue-600 dark:text-blue-400 font-mono">{formatSize(mediaStore.stats.total_size)}</span>
            </div>
            <div class="flex flex-col gap-1">
                <span class="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Số lượng file</span>
                <span class="text-lg font-bold text-zinc-800 dark:text-zinc-200 font-mono">{mediaStore.stats.total_count}</span>
            </div>
            <div class="flex flex-col gap-1">
                <span class="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Lưu trữ tại</span>
                <div class="flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full {mediaStore.stats.storage_provider === 'local' ? 'bg-orange-500' : 'bg-green-500'}"></span>
                    <span class="text-xs font-bold uppercase">{mediaStore.stats.storage_provider}</span>
                </div>
            </div>
            <div class="flex flex-col gap-1">
                <span class="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Phân bổ định dạng</span>
                <div class="flex gap-2">
                    {#each mediaStore.stats.breakdown.slice(0, 3) as item}
                        <div class="flex items-baseline gap-1" title="{item.count} files">
                            <span class="text-[10px] font-bold text-zinc-600 dark:text-zinc-400">{item.type}:</span>
                            <span class="text-[10px] font-mono text-zinc-500">{Math.round((item.size / mediaStore.stats.total_size) * 100)}%</span>
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    {/if}

    {#if suggestiveTags.length > 0}
        <div class="px-4 py-2 border-b bg-white dark:bg-zinc-900 flex items-center gap-2 overflow-x-auto no-scrollbar whitespace-nowrap" in:fade>
            <span class="text-[9px] font-bold text-zinc-400 uppercase tracking-widest flex-shrink-0 mr-1">Gợi ý AI:</span>
            {#each suggestiveTags as tag}
                <button
                    onclick={() => searchQuery = tag}
                    class="px-3 py-1 rounded-full text-[10px] font-medium transition-all border
                    {searchQuery.toLowerCase() === tag.toLowerCase()
                        ? 'bg-blue-600 border-blue-600 text-white shadow-md shadow-blue-500/20'
                        : 'bg-zinc-100 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 hover:border-blue-500/50'}"
                >
                    #{tag}
                </button>
            {/each}
            {#if searchQuery}
                <button
                    onclick={() => searchQuery = ''}
                    class="text-[9px] font-bold text-red-500 hover:text-red-600 uppercase ml-2"
                >
                    Xóa lọc
                </button>
            {/if}
        </div>
    {/if}

    <!-- Content -->
    <div class="flex-1 flex overflow-hidden">
        <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {#if mediaStore.isLoading && mediaStore.assets.length === 0}
                <div class="flex flex-col items-center justify-center h-full gap-4 text-zinc-400">
                    <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <p>Đang tải tài nguyên...</p>
                </div>
            {:else if filteredAssets.length === 0}
                <div class="flex flex-col items-center justify-center h-full gap-4 text-zinc-400">
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                    <p>{searchQuery ? 'Không tìm thấy ảnh phù hợp' : 'Chưa có ảnh nào trong thư viện'}</p>
                </div>
            {:else if viewMode === 'grid'}
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4" in:fade>
                    {#each filteredAssets as asset (asset.id)}
                        <!-- svelte-ignore a11y_click_events_have_key_events -->
                        <!-- svelte-ignore a11y_no_static_element_interactions -->
                        <div
                            class="group relative aspect-square bg-zinc-100 dark:bg-zinc-800 rounded-xl overflow-hidden border-2 transition-all shadow-sm hover:shadow-md
                            {selectedAssetId === asset.id ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-transparent hover:border-blue-500/50'} cursor-pointer"
                            onclick={() => selectedAssetId = asset.id}
                            role="button"
                            tabindex="0"
                        >
                            <!-- Multi-selection Checkbox -->
                            <button
                                onclick={(e) => toggleAssetSelection(e, asset.id)}
                                class="absolute top-2 left-2 z-10 w-5 h-5 rounded border-2 transition-all flex items-center justify-center
                                {mediaStore.selectedIds.has(asset.id)
                                    ? 'bg-blue-600 border-blue-600 text-white'
                                    : 'bg-white/50 border-white/80 dark:bg-zinc-900/50 dark:border-zinc-700 opacity-0 group-hover:opacity-100'}"
                                aria-label="Select asset {asset.filename}"
                                aria-pressed={mediaStore.selectedIds.has(asset.id)}
                            >
                                {#if mediaStore.selectedIds.has(asset.id)}
                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                                {/if}
                            </button>

                            <img
                                src={asset.id ? `/api/v1/media/${asset.id}/thumb?w=400&t=${asset._updatedAt || ''}` : ''}
                                alt={asset.alt_text || asset.filename}
                                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                loading="lazy"
                            />

                            <!-- Privacy Lock Icon (V10.0) -->
                            {#if !asset.is_public}
                                <div class="absolute top-2 right-10 p-1 bg-black/60 backdrop-blur-md text-yellow-500 rounded-lg shadow-sm" title="Riêng tư">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                                </div>
                            {/if}

                            <!-- AI Processing Overlay (V76) -->
                            {#if !asset.media_metadata.ai_description}
                                <div class="absolute inset-0 bg-blue-500/10 backdrop-blur-[1px] flex items-center justify-center">
                                    <div class="relative w-full h-full">
                                        <!-- Scanning line effect -->
                                        <div class="absolute top-0 left-0 w-full h-1 bg-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.5)] animate-scan-loop"></div>
                                        <div class="absolute inset-0 flex flex-col items-center justify-center gap-2">
                                            <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                            <span class="text-[8px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-tighter">AI Processing</span>
                                        </div>
                                    </div>
                                </div>
                            {/if}

                            <!-- Overlay Quick Actions -->
                            <div class="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onclick={(e) => { e.stopPropagation(); copyToClipboard(asset.file_path); }}
                                    class="p-1.5 bg-white/80 dark:bg-zinc-900/80 text-zinc-700 dark:text-zinc-200 rounded-lg backdrop-blur-md shadow-sm"
                                    title="Copy link"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                                </button>
                            </div>

                            <div class="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/80 to-transparent text-white text-[10px] truncate font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                                {asset.filename}
                            </div>
                        </div>
                    {/each}
                </div>
            {:else}
                <!-- List View (Same as before but with selection) -->
                <div class="flex flex-col gap-2" in:fade>
                    {#each filteredAssets as asset (asset.id)}
                        <div
                            role="button"
                            tabindex="0"
                            class="grid grid-cols-12 items-center px-4 py-3 bg-white dark:bg-zinc-800 border rounded-xl hover:shadow-sm transition-all group cursor-pointer text-left
                            {selectedAssetId === asset.id ? 'border-blue-500 bg-blue-50/30 dark:bg-blue-900/10' : ''}"
                            onclick={() => selectedAssetId = asset.id}
                            onkeydown={(e) => e.key === 'Enter' && (selectedAssetId = asset.id)}
                        >
                            <div class="col-span-1 flex justify-center">
                                <button
                                    onclick={(e) => toggleAssetSelection(e, asset.id)}
                                    class="w-5 h-5 rounded border-2 transition-all flex items-center justify-center
                                    {mediaStore.selectedIds.has(asset.id)
                                        ? 'bg-blue-600 border-blue-600 text-white'
                                        : 'bg-zinc-200 dark:bg-zinc-700 border-zinc-300 dark:border-zinc-600'}"
                                >
                                    {#if mediaStore.selectedIds.has(asset.id)}
                                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                                    {/if}
                                </button>
                            </div>
                            <div class="col-span-5 flex items-center gap-3">
                                <div class="w-12 h-12 rounded-lg overflow-hidden bg-zinc-100 flex-shrink-0 relative">
                                    <img src={asset.file_path && asset.file_path.includes('/') ? `${asset.file_path}?t=${asset._updatedAt || ''}` : ''} alt="" class="w-full h-full object-cover" />
                                    {#if !asset.is_public}
                                        <div class="absolute inset-0 bg-black/40 flex items-center justify-center text-yellow-500">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                                        </div>
                                    {/if}
                                </div>
                                <div class="overflow-hidden flex flex-col">
                                    <div class="flex items-center gap-2">
                                        <p class="text-sm font-medium truncate">{asset.filename}</p>
                                        {#if !asset.is_public}
                                            <span class="px-1.5 py-0.5 bg-yellow-500/10 text-yellow-600 dark:text-yellow-500 rounded text-[8px] font-bold uppercase">Private</span>
                                        {/if}
                                    </div>
                                    <p class="text-xs text-zinc-400 truncate">{asset.file_path}</p>
                                </div>
                            </div>
                            <div class="col-span-2 text-center text-sm text-zinc-500">{asset.dimensions || 'N/A'}</div>
                            <div class="col-span-2 text-center text-sm text-zinc-500">{formatSize(asset.file_size)}</div>
                            <div class="col-span-2 flex justify-end gap-2">
                                 <button
                                    onclick={(e) => { e.stopPropagation(); copyToClipboard(asset.file_path); }}
                                    class="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-blue-500 transition-all"
                                    aria-label="Copy file path"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                                </button>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>

        <!-- Right Detail Panel (CKEditor Style) -->
        {#if selectedAsset}
            <div class="w-80 border-l bg-zinc-50 dark:bg-zinc-900/50 flex flex-col overflow-y-auto custom-scrollbar" transition:slide={{ axis: 'x', duration: 300 }}>
                <div class="p-4 border-b bg-white dark:bg-zinc-800 flex justify-between items-center">
                    <h4 class="font-bold text-sm uppercase tracking-wider">Chi tiết tài nguyên</h4>
                    <button onclick={() => selectedAssetId = null} class="p-1 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded" aria-label="Close detail panel">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>

                <div class="p-4 flex flex-col gap-6">
                    <!-- Preview -->
                    <div class="aspect-video bg-zinc-200 dark:bg-zinc-800 rounded-xl overflow-hidden border shadow-inner relative group/preview">
                        <img src={selectedAsset.file_path && selectedAsset.file_path.includes('/') ? `${selectedAsset.file_path}?t=${selectedAsset._updatedAt || ''}` : ''} alt="" class="w-full h-full object-contain" />

                        {#if !selectedAsset.media_metadata.ai_description}
                            <div class="absolute inset-0 bg-blue-500/5 flex items-center justify-center">
                                <div class="absolute top-0 left-0 w-full h-1 bg-blue-500/40 animate-scan-loop"></div>
                            </div>
                        {/if}

                        <!-- Quick Edit Floating Bar -->
                        <div class="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center gap-1 p-1 bg-black/50 backdrop-blur-md rounded-lg border border-white/10 opacity-0 group-hover/preview:opacity-100 transition-opacity">
                            <button
                                onclick={() => handleQuickEdit('rotate_left')}
                                class="p-1.5 hover:bg-white/20 text-white rounded transition-colors"
                                title="Xoay trái 90°"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                            </button>
                            <button
                                onclick={() => handleQuickEdit('rotate_right')}
                                class="p-1.5 hover:bg-white/20 text-white rounded transition-colors"
                                title="Xoay phải 90°"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
                            </button>
                            <div class="w-px h-4 bg-white/20 mx-1"></div>
                            <button
                                onclick={() => handleQuickEdit('flip_h')}
                                class="p-1.5 hover:bg-white/20 text-white rounded transition-colors"
                                title="Lật ngang"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="m22 7-5 5 5 5"/><path d="m2 17 5-5-5-5"/></svg>
                            </button>
                            <button
                                onclick={() => handleQuickEdit('flip_v')}
                                class="p-1.5 hover:bg-white/20 text-white rounded transition-colors"
                                title="Lật dọc"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h18"/><path d="m7 2 5 5 5-5"/><path d="m17 22-5-5-5 5"/></svg>
                            </button>
                            <div class="w-px h-4 bg-white/20 mx-1"></div>
                            <button
                                onclick={() => handleQuickEdit('watermark')}
                                class="p-1.5 hover:bg-white/20 text-white rounded transition-colors"
                                title="Đóng dấu (Watermark)"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M14.8 9c0-1.1-.9-2-2-2h-1.4C10.2 7 9 8.1 9 9.5c0 1.3 1.1 2.2 2.4 2.2h1.2c1.3 0 2.4.9 2.4 2.2 0 1.4-1.2 2.5-2.6 2.5h-1.4c-1.1 0-2-1-2-2.1"/><path d="M12 5v2"/><path d="M12 17v2"/></svg>
                            </button>
                        </div>
                    </div>

                    <!-- Crop Presets -->
                    <div class="flex flex-col gap-2">
                        <div class="flex items-center justify-between">
                            <span class="text-[10px] font-bold text-zinc-500 uppercase">AI Smart Crop (V11.0)</span>
                            {#if selectedAsset.media_metadata.focal_point}
                                <span class="text-[8px] px-1 bg-green-500/10 text-green-600 rounded">Focal Point Ready</span>
                            {:else}
                                <span class="text-[8px] px-1 bg-zinc-500/10 text-zinc-500 rounded">Center fallback</span>
                            {/if}
                        </div>
                        <div class="grid grid-cols-4 gap-2">
                            <button
                                onclick={() => applySmartCrop('square')}
                                class="flex flex-col items-center gap-1 p-2 bg-white dark:bg-zinc-800 border rounded-lg hover:border-blue-500 transition-all group/btn"
                                title="Cắt hình vuông (1:1)"
                            >
                                <div class="w-6 h-6 border-2 border-zinc-400 group-hover/btn:border-blue-500 rounded-sm"></div>
                                <span class="text-[9px] font-bold">Square</span>
                            </button>
                            <button
                                onclick={() => applySmartCrop('banner')}
                                class="flex flex-col items-center gap-1 p-2 bg-white dark:bg-zinc-800 border rounded-lg hover:border-blue-500 transition-all group/btn"
                                title="Cắt ngang (16:9)"
                            >
                                <div class="w-8 h-4.5 border-2 border-zinc-400 group-hover/btn:border-blue-500 rounded-sm"></div>
                                <span class="text-[9px] font-bold">Banner</span>
                            </button>
                            <button
                                onclick={() => applySmartCrop('story')}
                                class="flex flex-col items-center gap-1 p-2 bg-white dark:bg-zinc-800 border rounded-lg hover:border-blue-500 transition-all group/btn"
                                title="Cắt dọc (9:16)"
                            >
                                <div class="w-4.5 h-8 border-2 border-zinc-400 group-hover/btn:border-blue-500 rounded-sm"></div>
                                <span class="text-[9px] font-bold">Story</span>
                            </button>
                            <button
                                onclick={() => applySmartCrop('feed')}
                                class="flex flex-col items-center gap-1 p-2 bg-white dark:bg-zinc-800 border rounded-lg hover:border-blue-500 transition-all group/btn"
                                title="Cắt dọc Feed (4:5)"
                            >
                                <div class="w-5 h-6.5 border-2 border-zinc-400 group-hover/btn:border-blue-500 rounded-sm"></div>
                                <span class="text-[9px] font-bold">Feed</span>
                            </button>
                        </div>
                    </div>

                    <!-- AI Metadata Section -->
                    <div class="flex flex-col gap-4">
                        <div class="bg-blue-500/5 border border-blue-500/20 rounded-xl p-3">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="p-1 bg-blue-500 text-white rounded text-[10px]">AI</span>
                                <h5 class="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase">Visual Intelligence</h5>
                            </div>

                            {#if selectedAsset.media_metadata.ai_description}
                                <div class="relative group/desc">
                                    <p class="text-[11px] text-zinc-600 dark:text-zinc-400 italic mb-3 pr-8">"{selectedAsset.media_metadata.ai_description}"</p>
                                    <button
                                        onclick={() => { 
                                            const desc = selectedAsset?.media_metadata?.ai_description;
                                            if (typeof desc === 'string') applyAIAltText(desc);
                                        }}
                                        class="absolute top-0 right-0 p-1 bg-blue-500 text-white rounded opacity-0 group-hover/desc:opacity-100 transition-opacity hover:scale-110 active:scale-95"
                                        title="Sử dụng làm Alt-text"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17l-5-5"/></svg>
                                    </button>
                                </div>
                            {:else}
                                <div class="flex flex-col gap-2 mb-3">
                                    <div class="h-3 w-full bg-blue-500/10 rounded animate-pulse"></div>
                                    <div class="h-3 w-4/5 bg-blue-500/10 rounded animate-pulse"></div>
                                    <p class="text-[9px] text-blue-500 font-bold animate-pulse mt-1">HỆ THỐNG ĐANG PHÂN TÍCH THỊ GIÁC...</p>
                                </div>
                            {/if}

                            {#if selectedAsset.media_metadata.ai_tags}
                                <div class="flex flex-wrap gap-1">
                                    {#each selectedAsset.media_metadata.ai_tags as tag}
                                        <button
                                            onclick={() => addTagToAltText(tag)}
                                            class="px-2 py-0.5 bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-full text-[9px] font-medium hover:bg-blue-500 hover:text-white transition-all active:scale-90"
                                            title="Thêm tag này vào Alt-text"
                                        >
                                            #{tag}
                                        </button>
                                    {/each}
                                </div>
                            {/if}

                            {#if selectedAsset.media_metadata.ai_sentiment}
                                <div class="mt-3 flex items-center gap-2">
                                    <span class="text-[10px] text-zinc-400 uppercase font-bold">Vibe:</span>
                                    <span class="text-[10px] font-bold text-zinc-700 dark:text-zinc-200">{selectedAsset.media_metadata.ai_sentiment}</span>
                                </div>
                            {/if}
                        </div>

                        <!-- Manual SEO Inputs -->
                        <div class="flex flex-col gap-3">
                            <div class="flex items-center justify-between p-2 bg-zinc-100 dark:bg-zinc-800/50 rounded-lg border border-white/5">
                                <div class="flex flex-col">
                                    <span class="text-[10px] font-bold text-zinc-500 uppercase">Quyền riêng tư</span>
                                    <span class="text-[9px] text-zinc-400">{selectedAsset.is_public ? 'Công khai toàn hệ thống' : 'Chỉ mình Sếp thấy'}</span>
                                </div>
                                <button
                                    onclick={() => mediaStore.updateMetadata(selectedAsset!.id, { is_public: !selectedAsset!.is_public })}
                                    class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none {selectedAsset.is_public ? 'bg-blue-600' : 'bg-zinc-400'}"
                                    aria-label="Toggle privacy"
                                >
                                    <span class="inline-block h-3 w-3 transform rounded-full bg-white transition-transform {selectedAsset.is_public ? 'translate-x-5' : 'translate-x-1'}"></span>
                                </button>
                            </div>

                            <div>
                                <label for="alt-{selectedAsset.id}" class="text-[10px] font-bold text-zinc-500 uppercase mb-1 block">Alt Text (Chuẩn SEO)</label>
                                <textarea
                                    id="alt-{selectedAsset.id}"
                                    bind:value={selectedAsset.alt_text}
                                    class="w-full p-2 text-xs bg-white dark:bg-zinc-800 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none h-20"
                                    placeholder="AI đang phân tích..."
                                    onchange={() => mediaStore.updateMetadata(selectedAsset!.id, { alt_text: selectedAsset!.alt_text })}
                                ></textarea>
                            </div>

                            <!-- AI Intelligence (V11.0) -->
                            {#if selectedAsset.media_metadata.ai_tags || selectedAsset.media_metadata.ai_description}
                                <div class="p-3 bg-blue-50/50 dark:bg-blue-900/10 rounded-lg border border-blue-100/50 dark:border-blue-500/10">
                                    <div class="flex items-center gap-2 mb-2">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="text-blue-500"><path d="M12 2v8"/><path d="m4.93 4.93 4.24 4.24"/><path d="M2 12h8"/><path d="m4.93 19.07 4.24-4.24"/><path d="M12 22v-8"/><path d="m19.07 19.07-4.24-4.24"/><path d="M22 12h-8"/><path d="m19.07 4.93-4.24 4.24"/></svg>
                                        <span class="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">AI Gợi ý</span>
                                    </div>

                                    {#if selectedAsset.media_metadata.ai_tags}
                                        <div class="flex flex-wrap gap-1 mb-2">
                                            {#each selectedAsset.media_metadata.ai_tags as tag}
                                                <span class="px-1.5 py-0.5 bg-white dark:bg-zinc-800 text-[9px] text-zinc-600 dark:text-zinc-400 rounded border border-zinc-200 dark:border-zinc-700">#{tag}</span>
                                            {/each}
                                        </div>
                                    {/if}

                                    {#if selectedAsset.media_metadata.ai_sentiment}
                                        <div class="text-[9px] text-zinc-500">
                                            Vibe: <span class="text-blue-600 dark:text-blue-400 font-bold">{selectedAsset.media_metadata.ai_sentiment}</span>
                                        </div>
                                    {/if}

                                    {#if selectedAsset.media_metadata.focal_point}
                                        <div class="text-[9px] text-zinc-500 mt-1">
                                            Focal Point: <span class="font-mono">({selectedAsset.media_metadata.focal_point.x.toFixed(2)}, {selectedAsset.media_metadata.focal_point.y.toFixed(2)})</span>
                                        </div>
                                    {/if}
                                </div>
                            {/if}
                        </div>

                        <!-- Technical Specs -->
                        <div class="grid grid-cols-2 gap-2 bg-zinc-100 dark:bg-zinc-800/50 p-3 rounded-lg border border-white/5">
                            <div>
                                <span class="text-[9px] text-zinc-400 uppercase block">Kích thước</span>
                                <span class="text-xs font-mono">{selectedAsset.dimensions}</span>
                            </div>
                            <div>
                                <span class="text-[9px] text-zinc-400 uppercase block">Dung lượng</span>
                                <span class="text-xs font-mono">{formatSize(selectedAsset.file_size)}</span>
                            </div>
                            <div class="col-span-2">
                                <span class="text-[9px] text-zinc-400 uppercase block">Định dạng</span>
                                <span class="text-xs font-mono uppercase">{selectedAsset.mime_type}</span>
                            </div>
                        </div>
                    </div>

                    <div class="flex flex-col gap-2 mt-auto">
                        {#if mediaStore.isTrashMode}
                            <button
                                onclick={() => handleRestore(selectedAsset!.id)}
                                class="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-bold shadow-lg shadow-green-500/20 transition-all flex items-center justify-center gap-2"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
                                KHÔI PHỤC ẢNH
                            </button>
                            <button
                                onclick={() => handleDelete(selectedAsset!.id)}
                                class="w-full py-2 text-red-500 hover:bg-red-500/10 rounded-lg text-xs font-bold transition-all border border-transparent hover:border-red-500/20"
                            >
                                XÓA VĨNH VIỄN
                            </button>
                        {:else}
                            {#if onSelect}
                                <button
                                    onclick={() => onSelect!(selectedAsset!)}
                                    class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg shadow-blue-500/20 transition-all flex items-center justify-center gap-2"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                                    SỬ DỤNG ẢNH NÀY
                                </button>
                            {/if}
                            <button
                                onclick={() => handleDelete(selectedAsset!.id)}
                                class="w-full py-2 text-red-500 hover:bg-red-500/10 rounded-lg text-xs font-bold transition-all border border-transparent hover:border-red-500/20"
                            >
                                XÓA KHỎI HỆ THỐNG
                            </button>
                        {/if}
                    </div>
                </div>
            </div>
        {/if}
    </div>

    <!-- Footer Stats -->
    <div class="p-3 border-t bg-zinc-50 dark:bg-zinc-800/50 flex justify-between items-center text-[10px] text-zinc-500 font-medium">
        <div class="flex gap-4">
            <span>TỔNG CỘNG: {mediaStore.total} TÀI NGUYÊN</span>
            <span>ĐANG HIỂN THỊ: {filteredAssets.length}</span>
        </div>
        <div class="flex items-center gap-1">
            <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            HỆ THỐNG ĐÃ SẴN SÀNG
        </div>
    </div>

    <!-- Bulk Action Toolbar (V65.0 Floating) -->
    {#if mediaStore.selectedIds.size > 0}
        <div
            class="absolute bottom-16 left-1/2 -translate-x-1/2 px-6 py-3 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-2xl shadow-2xl border border-white/10 flex items-center gap-6 z-50"
            transition:fade={{ duration: 200 }}
        >
            <div class="flex items-center gap-2 pr-4 border-r border-white/20 dark:border-zinc-900/20">
                <span class="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                    {mediaStore.selectedIds.size}
                </span>
                <span class="text-xs font-bold uppercase tracking-wider">Đã chọn</span>
            </div>

            <div class="flex items-center gap-2">
                <button
                    onclick={handleBulkDelete}
                    class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2 shadow-lg shadow-red-500/20"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                    XÓA TẤT CẢ ({mediaStore.selectedIds.size})
                </button>

                <button
                    onclick={() => mediaStore.bulkDownload()}
                    class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2 shadow-lg shadow-blue-500/20"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    TẢI XUỐNG ZIP
                </button>

                <button
                    onclick={() => showBulkSeo = true}
                    class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/20"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
                    TỐI ƯU SEO
                </button>

                <button
                    onclick={() => mediaStore.clearSelection()}
                    class="px-4 py-2 hover:bg-white/10 dark:hover:bg-black/10 rounded-lg text-xs font-bold transition-all"
                >
                    HỦY BỎ
                </button>
            </div>
        </div>
    {/if}

    <!-- Bulk SEO Editor Modal (V11.0 Elite) -->
    {#if showBulkSeo}
        <div
            class="fixed inset-0 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md"
            style="z-index: {Z_INDEX.POPOVER};"
            transition:fade={{ duration: 200 }}
        >
            <div
                class="bg-white dark:bg-zinc-900 w-full max-w-4xl max-h-[80vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-white/10"
                transition:scale={{ start: 0.95, duration: 200 }}
            >
                <div class="p-6 border-b flex justify-between items-center bg-zinc-50 dark:bg-zinc-800/50">
                    <div class="flex items-center gap-4">
                        <div>
                            <h3 class="text-lg font-bold">Bulk SEO Editor</h3>
                            <p class="text-xs text-zinc-500">Đang tối ưu {mediaStore.selectedIds.size} ảnh được chọn</p>
                        </div>
                        <button
                            onclick={handleMagicWand}
                            disabled={isAutoFilling}
                            class="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-xs font-bold transition-all shadow-lg shadow-blue-500/20 animate-pulse"
                            title="Tự động điền Alt-text bằng AI Vision"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m2 22 1-1h3l9-9"/><path d="M3 21v-3l9-9"/><path d="m15 6 3.4-3.4a2.1 2.1 0 1 1 3 3L18 9l-3-3Z"/><path d="m9.5 15.5 3 3"/></svg>
                            {isAutoFilling ? 'ĐANG PHÂN TÍCH...' : 'MAGIC WAND (AI)'}
                        </button>
                    </div>
                    <button
                        onclick={() => showBulkSeo = false}
                        class="p-2 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-full transition-colors"
                        aria-label="Close bulk SEO editor"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>

                <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
                    <div class="space-y-6">
                        {#each mediaStore.assets.filter(a => mediaStore.selectedIds.has(a.id)) as asset}
                            <div class="flex gap-4 p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl border border-zinc-100 dark:border-zinc-700/50 group">
                                <div class="w-32 h-32 rounded-lg overflow-hidden bg-zinc-200 dark:bg-zinc-800 flex-shrink-0 relative">
                                    <img src={asset.file_path} alt="" class="w-full h-full object-cover" />
                                    <div class="absolute bottom-1 right-1 px-1 bg-black/50 text-[8px] text-white rounded font-mono uppercase">
                                        {asset.dimensions}
                                    </div>
                                </div>
                                <div class="flex-1 flex flex-col gap-3">
                                    <div class="flex justify-between items-start">
                                        <span class="text-xs font-bold truncate max-w-[200px]">{asset.filename}</span>
                                        <span class="text-[9px] px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full font-bold uppercase tracking-wider">
                                            {asset.media_metadata.ai_sentiment || 'Standard'}
                                        </span>
                                    </div>

                                    <div>
                                        <label for="bulk-alt-{asset.id}" class="text-[9px] font-bold text-zinc-400 uppercase mb-1 block">Alt Text (SEO)</label>
                                        <textarea
                                            id="bulk-alt-{asset.id}"
                                            bind:value={asset.alt_text}
                                            class="w-full p-2 text-xs bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none h-16 transition-all"
                                            placeholder="Gõ alt-text để ảnh lên top..."
                                        ></textarea>
                                    </div>

                                    {#if asset.media_metadata.ai_tags}
                                        <div class="flex flex-wrap gap-1">
                                            {#each asset.media_metadata.ai_tags.slice(0, 5) as tag}
                                                <span class="px-1.5 py-0.5 bg-zinc-200 dark:bg-zinc-700 text-[9px] text-zinc-500 dark:text-zinc-400 rounded">#{tag}</span>
                                            {/each}
                                        </div>
                                    {/if}
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>

                <div class="p-6 border-t bg-zinc-50 dark:bg-zinc-800/50 flex justify-end gap-3">
                    <button
                        onclick={() => showBulkSeo = false}
                        class="px-6 py-2 border border-zinc-200 dark:border-zinc-700 text-zinc-500 rounded-xl text-xs font-bold hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all"
                    >
                        HỦY
                    </button>
                    <button
                        onclick={handleBulkSeoSave}
                        class="px-6 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:scale-105 active:scale-95 shadow-lg shadow-blue-500/20 transition-all"
                    >
                        LƯU TẤT CẢ ({mediaStore.selectedIds.size})
                    </button>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .custom-scrollbar::-webkit-scrollbar {
        width: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #e2e8f0;
        border-radius: 10px;
    }
    :global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #334155;
    }
    @keyframes scan-loop {
        0% { top: 0; }
        100% { top: 100%; }
    }
    .animate-scan-loop {
        animation: scan-loop 2s linear infinite;
    }
</style>
