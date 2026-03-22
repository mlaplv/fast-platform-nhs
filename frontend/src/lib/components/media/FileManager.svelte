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
        onSelect?: (assets: MediaAsset[]) => void;
        standalone?: boolean;
        mode?: 'manage' | 'pick';
        pickTabActive?: 'current' | 'ai' | 'library';
        onPickTabChange?: (tab: string) => void;
        onPickConfirm?: () => void;
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

    // ── Post Tracking Filter (V569) ──
    let showPostFilter = $state(false);
    let filterPostType = $state('');   // 'news' | 'product' | ''
    let filterPostId = $state('');
    let showUnlinkedOnly = $state(false);

    // ── Link-to-post modal ──
    let showLinkModal = $state(false);
    let linkPostId = $state('');
    let linkPostType = $state<'news' | 'product'>('news');

    // ── Hard Delete confirmation ──
    let pendingHardDeleteId = $state<string | null>(null);

    // ── Overflow Menu (V2026) ──
    let showMoreActions = $state(false);

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
                        a.filename?.toLowerCase().includes(action.args!.toLowerCase()) ||
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
            let pass = true;

            if (query) {
                const basicMatch = asset.filename?.toLowerCase().includes(query) ||
                                 (asset.alt_text && asset.alt_text.toLowerCase().includes(query));
                const aiTags = asset.media_metadata?.ai_tags || [];
                const tagMatch = aiTags.some((tag: string) => tag.toLowerCase().includes(query));
                const vibeMatch = asset.media_metadata?.ai_sentiment?.toLowerCase().includes(query);
                pass = !!(basicMatch || tagMatch || vibeMatch);
            }

            // Post filter
            if (showUnlinkedOnly && asset.linked_post_id) pass = false;
            if (!showUnlinkedOnly && filterPostType && asset.linked_post_type !== filterPostType) pass = false;
            if (!showUnlinkedOnly && filterPostId && asset.linked_post_id !== filterPostId) pass = false;

            return pass;
        })
    );

    const selectedAsset = $derived(
        mediaStore.assets.find(a => a.id === selectedAssetId) || null
    );

    // Trích xuất các Top Tags thực tế từ dữ liệu để làm gợi ý
    const suggestiveTags = $derived.by(() => {
        const tagMap = new Map<string, number>();
        mediaStore.assets.forEach(asset => {
            (asset.media_metadata?.ai_tags || []).forEach((tag: string) => {
                tagMap.set(tag, (tagMap.get(tag) || 0) + 1);
            });
        });
        return Array.from(tagMap.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8)
            .map(entry => entry[0]);
    });

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
            // Optimistic update
            aiVisionEnabled = newState;
            const res = await fetch('/api/v1/media/settings/ai-vision', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: newState })
            });
            if (!res.ok) {
                // Revert on failure
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

    onMount(() => {
        mediaStore.loadStats();
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
        }
    }

    async function handleBulkDelete() {
        if (mediaStore.isTrashMode) {
            const confirmed = await nanobot.showConfirm({
                title: "CẢNH BÁO",
                message: `Sếp có chắc chắn muốn xóa VĨNH VIỄN ${mediaStore.selectedIds.size} ảnh đã chọn? (Xóa file thật sự trên đĩa)`,
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

    function applyPostFilter() {
        mediaStore.setPostFilter(
            filterPostId || null,
            filterPostType || null
        );
    }

    function clearPostFilter() {
        filterPostId = '';
        filterPostType = '';
        showUnlinkedOnly = false;
        mediaStore.setPostFilter(null, null);
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
            target.value = ''; // Reset
            if (successCount > 0) nanobot.showToast(`Đã tải lên thành công ${successCount} ảnh`, "success");
            if (failCount > 0) nanobot.showToast(`Lỗi kỹ thuật: ${failCount} ảnh không thể tải lên`, "error");
        }
    }
</script>


<div class="file-manager flex flex-col h-full bg-white dark:bg-[#0c0e14] overflow-hidden" class:rounded-xl={!standalone} class:border={!standalone}>
    <!-- Top Bar — Liquid Glass -->
    <div class="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between bg-zinc-50 dark:bg-white/[0.03] backdrop-blur-xl">
        <div class="flex items-center gap-4 flex-1">
            {#if onPickTabChange}
              <!-- Pick-mode tabs -->
              <div class="flex bg-white/[0.05] p-0.5 rounded-lg border border-white/[0.06] shrink-0">
                <button 
                  onclick={() => onPickTabChange?.('current')}
                  class="px-3 py-1.5 rounded-md text-[11px] font-semibold transition-all {pickTabActive === 'current' ? 'bg-indigo-500/90 text-white shadow-lg shadow-indigo-500/20' : 'text-white/30 hover:text-white/60 hover:bg-white/[0.05]'}"
                >
                  Ảnh bài này
                </button>
                <button 
                  onclick={() => onPickTabChange?.('library')}
                  class="px-3 py-1.5 rounded-md text-[11px] font-semibold transition-all {pickTabActive === 'library' ? 'bg-indigo-500/90 text-white shadow-lg shadow-indigo-500/20' : 'text-white/30 hover:text-white/60 hover:bg-white/[0.05]'}"
                >
                  Thư viện
                </button>
                <button 
                  onclick={() => onPickTabChange?.('ai')}
                  class="px-3 py-1.5 rounded-md text-[11px] font-semibold transition-all {pickTabActive === 'ai' ? 'bg-indigo-500/90 text-white shadow-lg shadow-indigo-500/20' : 'text-white/30 hover:text-white/60 hover:bg-white/[0.05]'}"
                >
                  Phát sinh AI
                </button>
              </div>
            {:else if mode !== 'pick'}
            <h3 class="font-bold text-lg flex items-center gap-2 whitespace-nowrap shrink-0">
                <span class="p-1.5 bg-blue-600 text-white rounded-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                </span>
                THƯ VIỆN HÌNH ẢNH
            </h3>
            {/if}

            <!-- Search Bar (Liquid) -->
            <div class="relative flex-1 max-w-sm ml-4 min-w-[120px]">
                <input
                    type="text"
                    bind:value={searchQuery}
                    placeholder="Tìm kiếm ảnh..."
                    class="w-full pl-9 pr-4 py-2 bg-white dark:bg-zinc-800 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                />
                <svg class="absolute left-3 top-2.5 text-zinc-400" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </div>

            <!-- Local Upload Action -->
            <div class="relative ml-2">
                <input
                    type="file"
                    accept="image/*"
                    multiple
                    class="hidden"
                    bind:this={fileInput}
                    onchange={handleFileUpload}
                />
                <button
                    onclick={() => fileInput?.click()}
                    class="flex items-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
                    title="Tải ảnh từ máy"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    TẢI LÊN
                </button>
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
                        style="z-index: {Z_INDEX.HUD_FLOATING};"
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

            <!-- View Mode, Filters & Actions (Adaptive Overflow) -->
            <div class="flex items-center gap-2 ml-auto shrink-0 relative">
                <!-- Main Actions (Adaptive Unfolding) -->
                <div class="hidden lg:flex items-center gap-2">
                    <!-- Select All (lg+) -->
                    <button
                        onclick={() => mediaStore.selectedIds.size === mediaStore.assets.length ? mediaStore.clearSelection() : mediaStore.selectAll()}
                        class="text-[10px] font-bold uppercase px-2 py-1.5 rounded bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 transition-colors whitespace-nowrap"
                    >
                        {mediaStore.selectedIds.size === mediaStore.assets.length ? 'Bỏ chọn' : 'Chọn tất'}
                    </button>

                    <!-- Filter (lg+) -->
                    <button
                        onclick={() => showPostFilter = !showPostFilter}
                         class="flex items-center gap-2 px-3 py-1.5 {showPostFilter || mediaStore.linkedPostId ? 'bg-orange-500 text-white' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600'} rounded-lg text-[10px] font-bold transition-all"
                        title="Lọc bài viết"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 3H2l8 9v6l4 2v-8l8-9z"/></svg>
                        LỌC
                    </button>

                    <!-- Trash (lg+) -->
                    <button 
                        onclick={() => mediaStore.toggleTrashMode()} 
                        class="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase transition-all relative flex items-center gap-2 {mediaStore.isTrashMode ? 'bg-red-500 text-white' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500'}"
                        title="Thùng rác"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
                        {#if mediaStore.stats?.total_trash_count > 0}
                            <span class="px-1 py-0.5 bg-red-600 text-white text-[8px] rounded-full">
                                {mediaStore.stats.total_trash_count}
                            </span>
                        {/if}
                    </button>
                </div>

                <!-- Utility Actions (xl+) -->
                <div class="hidden xl:flex items-center gap-2">
                    <div class="flex items-center gap-1 bg-zinc-200 dark:bg-zinc-700/50 p-1 rounded-lg">
                        <button
                            onclick={() => viewMode = 'grid'}
                            class="p-1.5 rounded-md transition-all {viewMode === 'grid' ? 'bg-white dark:bg-zinc-600 shadow-sm' : 'text-zinc-500'}"
                            title="Grid View"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
                        </button>
                        <button
                            onclick={() => viewMode = 'list'}
                            class="p-1.5 rounded-md transition-all {viewMode === 'list' ? 'bg-white dark:bg-zinc-600 shadow-sm' : 'text-zinc-500'}"
                            title="List View"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                        </button>
                    </div>

                    <button
                        onclick={() => showStats = !showStats}
                        class="p-2 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg transition-colors text-zinc-500"
                        title="Thống kê"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>
                    </button>

                    <button
                        onclick={() => mediaStore.loadAssets(campaignId, true)}
                        class="p-2 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg transition-colors text-zinc-500 {mediaStore.isLoading ? 'animate-spin' : ''}"
                        title="Reload"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
                    </button>
                </div>

                <!-- AI Vision (2xl+) -->
                <div class="hidden 2xl:flex items-center">
                    <button
                        onclick={toggleAIVision}
                        class="flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all {aiVisionEnabled ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-600' : 'bg-transparent border-zinc-200 dark:border-zinc-700 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800'}"
                        title="Bật/tắt AI phân tích ảnh tự động"
                    >
                        <span class="text-[9px] font-bold uppercase tracking-widest">AI Vision</span>
                        <div class="relative w-6 h-3.5 rounded-full transition-colors {aiVisionEnabled ? 'bg-indigo-500' : 'bg-zinc-300 dark:bg-zinc-600'}">
                            <div class="absolute top-[2px] left-[2px] w-2.5 h-2.5 bg-white rounded-full transition-transform {aiVisionEnabled ? 'translate-x-2.5' : 'translate-x-0'}"></div>
                        </div>
                    </button>
                </div>

                <!-- Overflow Trigger (Visible on small screens, hidden when 2XL desktop unfolds everything) -->
                <button
                    onclick={() => showMoreActions = !showMoreActions}
                    class="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 dark:bg-zinc-800/50 border border-white/10 hover:bg-white/10 transition-all relative group 2xl:hidden"
                    title="Thêm hành động"
                    aria-label="Thêm hành động"
                >
                    <span class="text-xs font-bold text-zinc-400 group-hover:text-white transition-colors">»</span>
                    {#if mediaStore.stats?.total_trash_count > 0}
                        <div class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-[#0c0e14] animate-pulse"></div>
                    {/if}
                </button>

                <!-- Overflow Dropdown Content -->
                {#if showMoreActions}
                    <div 
                        class="absolute top-full right-0 mt-2 w-64 p-3 bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-800 flex flex-col gap-2"
                        style="z-index: {Z_INDEX.HUD_SERVICE};"
                        transition:slide={{ axis: 'y', duration: 300 }}
                    >
                        <div class="flex items-center justify-between px-2 mb-1">
                            <p class="text-[9px] font-black text-zinc-500 uppercase tracking-widest">Công cụ bổ sung</p>
                            <button onclick={() => showMoreActions = false} class="text-zinc-500 hover:text-white transition-colors" aria-label="Đóng menu">
                                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                            </button>
                        </div>

                        <!-- Selection Actions (Hidden on lg+ because it unfolds) -->
                        <button
                            onclick={() => { mediaStore.selectedIds.size === mediaStore.assets.length ? mediaStore.clearSelection() : mediaStore.selectAll(); showMoreActions = false; }}
                            class="flex lg:hidden items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all text-xs font-bold text-zinc-600 dark:text-zinc-400"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                            {mediaStore.selectedIds.size === mediaStore.assets.length ? 'BỎ CHỌN TẤT CẢ' : 'CHỌN TẤT CẢ'}
                        </button>
                        
                        <!-- Post Filter (Hidden on lg+ because it unfolds) -->
                        <button
                            onclick={() => { showPostFilter = !showPostFilter; showMoreActions = false; }}
                            class="flex lg:hidden items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all text-xs font-bold {showPostFilter || mediaStore.linkedPostId ? 'text-orange-500' : 'text-zinc-600 dark:text-zinc-400'}"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 3H2l8 9v6l4 2v-8l8-9z"/></svg>
                            LỌC BÀI VIẾT
                        </button>

                        <!-- Trash bin (Hidden on lg+ because it unfolds) -->
                        <button 
                            onclick={() => { mediaStore.toggleTrashMode(); showMoreActions = false; }} 
                            class="flex lg:hidden items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all text-xs font-bold {mediaStore.isTrashMode ? 'text-red-500' : 'text-zinc-600 dark:text-zinc-400'}"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                            THÙNG RÁC
                            {#if mediaStore.stats?.total_trash_count > 0}
                                <span class="ml-auto px-1.5 py-0.5 bg-red-500 text-white text-[9px] font-bold rounded-full">
                                    {mediaStore.stats.total_trash_count}
                                </span>
                            {/if}
                        </button>

                        <div class="h-px bg-zinc-200 dark:bg-zinc-800 my-1 lg:hidden"></div>

                        <!-- Mobile View Mode (Hidden on xl+ because it unfolds) -->
                        <div class="flex xl:hidden items-center gap-2 px-1 mb-1">
                            <button
                                onclick={() => viewMode = 'grid'}
                                class="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg {viewMode === 'grid' ? 'bg-indigo-500 text-white' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500'} transition-all text-[10px] font-bold"
                            >
                                GRID
                            </button>
                            <button
                                onclick={() => viewMode = 'list'}
                                class="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg {viewMode === 'list' ? 'bg-indigo-500 text-white' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500'} transition-all text-[10px] font-bold"
                            >
                                LIST
                            </button>
                        </div>

                        <!-- Stats & Reload (Hidden on xl+ because it unfolds) -->
                        <div class="flex xl:hidden items-center gap-2 px-1">
                            <button
                                onclick={() => { showStats = !showStats; showMoreActions = false; }}
                                class="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all text-[10px] font-bold text-zinc-500"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>
                                STATS
                            </button>
                            <button
                                onclick={() => { mediaStore.loadAssets(campaignId, true); showMoreActions = false; }}
                                class="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all text-[10px] font-bold text-zinc-500 {mediaStore.isLoading ? 'animate-spin' : ''}"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
                                RELOAD
                            </button>
                        </div>

                        <!-- AI Vision toggle (Hidden on 2xl+ because it unfolds) -->
                        <button
                            onclick={() => { toggleAIVision(); showMoreActions = false; }}
                            class="flex 2xl:hidden items-center justify-between px-3 py-2.5 rounded-xl bg-indigo-500/5 hover:bg-indigo-500/10 border border-indigo-500/10 transition-all mt-1"
                        >
                            <span class="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">AI Vision</span>
                            <div class="relative w-7 h-4 rounded-full transition-colors {aiVisionEnabled ? 'bg-indigo-500' : 'bg-zinc-600'}">
                                <div class="absolute top-[2px] left-[2px] w-3 h-3 bg-white rounded-full transition-transform {aiVisionEnabled ? 'translate-x-3' : 'translate-x-0'}"></div>
                            </div>
                        </button>
                    </div>
                {/if}

                {#if onPickConfirm || onPickClose}
                    <div class="flex items-center gap-2 pl-2 border-l border-white/10 shrink-0">
                        {#if onPickConfirm}
                        <button 
                            onclick={onPickConfirm}
                            class="px-4 py-1.5 bg-indigo-500/90 hover:bg-indigo-400/90 text-white rounded-lg text-[11px] font-bold transition-all shadow-lg shadow-indigo-500/15"
                        >
                            Xác nhận
                        </button>
                        {/if}
                        {#if onPickClose}
                        <button
                            onclick={onPickClose}
                            class="w-8 h-8 rounded-lg border border-white/[0.08] bg-white/[0.04] flex items-center justify-center hover:bg-red-500/20 hover:border-red-400/30 transition-all"
                            aria-label="Đóng"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white/30"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                        {/if}
                    </div>
                {/if}
            </div>
        </div>
    </div>

    <!-- Post Filter Panel -->
    {#if showPostFilter}
        <div class="p-4 bg-zinc-50 dark:bg-zinc-800/30 border-b flex flex-col gap-4" transition:slide>
            <div class="flex items-center justify-between">
                <span class="text-[10px] font-black uppercase tracking-widest text-zinc-500">BỘ LỌC TRUY XUẤT NGUỒN GỐC</span>
                <button onclick={() => showPostFilter = false} class="text-zinc-400 hover:text-zinc-600">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
            <div class="flex flex-wrap items-center gap-4">
                <div class="flex items-center gap-2">
                    <span class="text-xs text-zinc-500">Loại bài:</span>
                    <select bind:value={filterPostType} class="px-2 py-1.5 bg-white dark:bg-zinc-900 border rounded text-xs outline-none">
                        <option value="">Tất cả</option>
                        <option value="news">Bài viết (News)</option>
                        <option value="product">Sản phẩm (Product)</option>
                    </select>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-xs text-zinc-500">ID bài viết:</span>
                    <input type="text" bind:value={filterPostId} placeholder="Nhập ID..." class="px-2 py-1.5 bg-white dark:bg-zinc-900 border rounded text-xs outline-none w-48" />
                </div>
                <label class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" bind:checked={showUnlinkedOnly} class="w-3.5 h-3.5" />
                    <span class="text-xs text-zinc-500">Chỉ hiện ảnh chưa gán bài</span>
                </label>
                <div class="flex-1"></div>
                <div class="flex items-center gap-2">
                    <button onclick={clearPostFilter} class="px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-700">Xoá bộ lọc</button>
                    <button onclick={applyPostFilter} class="px-4 py-1.5 bg-orange-500 text-white rounded text-xs font-bold hover:bg-orange-600 transition-all">ÁP DỤNG</button>
                </div>
            </div>
        </div>
    {/if}

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
            <div class="flex flex-col gap-1 text-red-500">
                <span class="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Thùng rác</span>
                <span class="text-lg font-bold font-mono">{mediaStore.stats.total_trash_count}</span>
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
        <div class="px-4 py-2 border-b border-white/[0.06] bg-white dark:bg-white/[0.02] flex items-center gap-2 overflow-x-auto no-scrollbar whitespace-nowrap" in:fade>
            <span class="text-[9px] font-semibold text-zinc-400 dark:text-white/25 uppercase tracking-widest flex-shrink-0 mr-1">Gợi ý AI:</span>
            {#each suggestiveTags as tag}
                <button
                    onclick={() => searchQuery = tag}
                    class="px-3 py-1 rounded-full text-[10px] font-medium transition-all border backdrop-blur-sm
                    {searchQuery.toLowerCase() === tag.toLowerCase()
                        ? 'bg-indigo-500/90 border-indigo-400/50 text-white shadow-lg shadow-indigo-500/20'
                        : 'bg-white/[0.06] border-white/[0.08] text-white/50 hover:bg-white/[0.1] hover:border-indigo-400/30 hover:text-white/80'}"
                >
                    #{tag}
                </button>
            {/each}
            {#if searchQuery}
                <button
                    onclick={() => searchQuery = ''}
                    class="text-[9px] font-bold text-red-400/80 hover:text-red-400 uppercase ml-2 transition-colors"
                >
                    Xóa lọc
                </button>
            {/if}
        </div>
    {/if}

    <!-- Content -->
    <div class="flex-1 flex overflow-hidden">
        <div class="flex-1 overflow-y-auto p-4 custom-scrollbar bg-white dark:bg-[#0a0c12]">
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
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3" in:fade>
                    {#each filteredAssets as asset (asset.id)}
                        <!-- svelte-ignore a11y_click_events_have_key_events -->
                        <!-- svelte-ignore a11y_no_static_element_interactions -->
                        <div
                            class="group relative aspect-square bg-zinc-100 dark:bg-white/[0.04] rounded-2xl overflow-hidden border transition-all duration-300
                            {selectedAssetId === asset.id ? 'border-indigo-400/50 ring-1 ring-indigo-400/20 shadow-[0_0_25px_rgba(99,102,241,0.15)]' : 'border-white/[0.06] hover:border-white/[0.15] hover:shadow-lg hover:shadow-black/20'} cursor-pointer glass-card"
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
                                src={asset.id?.startsWith('tmp_') ? asset.file_path : (asset.id ? `/api/v1/media/${asset.id}/thumb?w=400&t=${asset._updatedAt || ''}` : '')}
                                alt={asset.alt_text || asset.filename}
                                class="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-105"
                                loading="lazy"
                            />

                            <!-- Privacy Lock Icon (V10.0) -->
                            {#if !asset.is_public}
                                <div class="absolute top-2 right-10 p-1 bg-black/60 backdrop-blur-md text-yellow-500 rounded-lg shadow-sm" title="Riêng tư">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                                </div>
                            {/if}

                            <!-- Dynamic Processing Overlay -->
                            {#if asset.media_metadata?.status === 'uploading'}
                                <div class="absolute inset-0 bg-zinc-900/40 backdrop-blur-[2px] flex items-center justify-center z-10 transition-all duration-300">
                                    <div class="flex flex-col items-center justify-center gap-2">
                                        <div class="w-6 h-6 border-2 border-white/80 border-t-white rounded-full animate-spin"></div>
                                        <span class="text-[8px] font-bold text-white uppercase tracking-widest drop-shadow-md">Uploading</span>
                                    </div>
                                </div>
                            {:else if asset.media_metadata?.status === 'processing' || (!asset.media_metadata?.ai_description && asset.media_metadata?.status !== 'ready')}
                                <div class="absolute inset-0 bg-blue-500/10 backdrop-blur-[1px] flex items-center justify-center z-10 transition-all duration-300">
                                    <div class="relative w-full h-full">
                                        <!-- Scanning line effect -->
                                        <div class="absolute top-0 left-0 w-full h-1 bg-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.5)] animate-scan-loop"></div>
                                        <div class="absolute inset-0 flex flex-col items-center justify-center gap-2">
                                            <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                            <span class="text-[8px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-tighter">AI Scanning</span>
                                        </div>
                                    </div>
                                </div>
                            {/if}

                            <!-- Overlay Quick Actions -->
                            <div class="absolute top-2 right-2 flex flex-col gap-1.5 opacity-0 group-hover:opacity-100 transition-all duration-200 translate-x-2 group-hover:translate-x-0">
                                <!-- Edit/View Details -->
                                <button
                                    onclick={(e) => { e.stopPropagation(); selectedAssetId = asset.id; }}
                                    class="p-1.5 bg-white/90 dark:bg-zinc-900/90 text-zinc-700 dark:text-zinc-200 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-lg backdrop-blur-md shadow-sm hover:scale-105 transition-all"
                                    title="Sửa chi tiết"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>
                                </button>
                                
                                <!-- Download -->
                                <a
                                    onclick={(e) => e.stopPropagation()}
                                    href={asset.file_path}
                                    download={asset.filename}
                                    target="_blank"
                                    class="p-1.5 bg-white/90 dark:bg-zinc-900/90 flex text-zinc-700 dark:text-zinc-200 hover:text-green-600 dark:hover:text-green-400 rounded-lg backdrop-blur-md shadow-sm hover:scale-105 transition-all"
                                    title="Tải xuống"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
                                </a>

                                <!-- Copy Link -->
                                <button
                                    onclick={(e) => { e.stopPropagation(); copyToClipboard(asset.file_path); }}
                                    class="p-1.5 bg-white/90 dark:bg-zinc-900/90 text-zinc-700 dark:text-zinc-200 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg backdrop-blur-md shadow-sm hover:scale-105 transition-all"
                                    title="Copy link"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                                </button>

                                {#if mediaStore.isTrashMode}
                                <!-- Restore -->
                                <button
                                    onclick={(e) => { e.stopPropagation(); handleRestore(asset.id); }}
                                    class="p-1.5 bg-white/90 dark:bg-zinc-900/90 flex justify-center text-zinc-700 dark:text-zinc-200 hover:text-green-500 dark:hover:text-green-400 rounded-lg backdrop-blur-md shadow-sm hover:scale-105 transition-all"
                                    title="Khôi phục"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                                </button>
                                {/if}

                                <!-- Delete -->
                                <button
                                    onclick={(e) => { e.stopPropagation(); handleDelete(asset.id); }}
                                    class="p-1.5 bg-white/90 dark:bg-zinc-900/90 text-zinc-700 dark:text-zinc-200 hover:text-red-500 dark:hover:text-red-400 rounded-lg backdrop-blur-md shadow-sm hover:scale-105 transition-all"
                                    title={mediaStore.isTrashMode ? 'Xóa vĩnh viễn' : 'Chuyển vào thùng rác'}
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                                </button>
                            </div>

                            <div class="absolute bottom-0 left-0 right-0 p-2.5 bg-gradient-to-t from-black/70 via-black/30 to-transparent text-white text-[10px] truncate font-medium opacity-0 group-hover:opacity-100 transition-all duration-300 backdrop-blur-sm">
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
                            <div class="col-span-2 flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <!-- Edit/View Details -->
                                <button
                                    onclick={(e) => { e.stopPropagation(); selectedAssetId = asset.id; }}
                                    class="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-indigo-500 transition-all"
                                    title="Sửa chi tiết"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>
                                </button>

                                <!-- Download -->
                                <a
                                    onclick={(e) => e.stopPropagation()}
                                    href={asset.file_path}
                                    download={asset.filename}
                                    target="_blank"
                                    class="p-2 flex hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-green-500 transition-all"
                                    title="Tải xuống"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
                                </a>

                                <!-- Copy Link -->
                                 <button
                                    onclick={(e) => { e.stopPropagation(); copyToClipboard(asset.file_path); }}
                                    class="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-blue-500 transition-all"
                                    title="Copy link"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                                </button>

                                {#if mediaStore.isTrashMode}
                                <!-- Restore -->
                                <button
                                    onclick={(e) => { e.stopPropagation(); handleRestore(asset.id); }}
                                    class="p-2 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg text-zinc-400 hover:text-green-500 transition-all"
                                    title="Khôi phục"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                                </button>
                                {/if}

                                <!-- Delete -->
                                <button
                                    onclick={(e) => { e.stopPropagation(); handleDelete(asset.id); }}
                                    class="p-2 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg text-zinc-400 hover:text-red-500 transition-all"
                                    title={mediaStore.isTrashMode ? 'Xóa vĩnh viễn' : 'Chuyển vào thùng rác'}
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                                </button>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>

        <!-- Right Detail Panel — Liquid Glass -->
        {#if selectedAsset}
            <div class="w-80 border-l border-white/[0.06] bg-zinc-50 dark:bg-white/[0.02] backdrop-blur-xl flex flex-col overflow-y-auto custom-scrollbar" transition:slide={{ axis: 'x', duration: 300 }}>
                <div class="px-4 py-3 border-b border-white/[0.06] bg-white dark:bg-white/[0.03] flex justify-between items-center">
                    <h4 class="font-semibold text-sm text-zinc-700 dark:text-white/70">Chi tiết</h4>
                    <button onclick={() => selectedAssetId = null} class="p-1.5 hover:bg-white/10 rounded-lg transition-colors" aria-label="Đóng">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white/30"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
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
                            <div class="space-y-1">
                                <span class="text-[9px] text-zinc-400 uppercase block">Nguồn gốc/Link bài</span>
                                {#if selectedAsset.linked_post_id}
                                    <div class="flex items-center gap-2 p-2 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                                        <div class="p-1 bg-orange-500 rounded text-white">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                                        </div>
                                        <div class="flex-1 min-w-0">
                                            <p class="text-[10px] font-bold text-orange-600 uppercase truncate">{selectedAsset.linked_post_type}</p>
                                            <p class="text-[9px] text-zinc-500 font-mono truncate">{selectedAsset.linked_post_id}</p>
                                        </div>
                                    </div>
                                {:else}
                                    <p class="text-[10px] italic text-zinc-500">Chưa được gán cho bài viết hay sản phẩm nào.</p>
                                {/if}
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
        <div class="fixed bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 px-6 py-3 bg-zinc-900 text-white rounded-full shadow-2xl border border-white/10 z-[100]" transition:fade>
            <div class="flex items-center gap-2 pr-4 border-r border-white/20">
                <span class="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px] font-bold">
                    {mediaStore.selectedIds.size}
                </span>
                <span class="text-[10px] font-bold uppercase tracking-wider">Đã chọn</span>
            </div>
            
            <div class="flex items-center gap-3 text-zinc-400">
                <button 
                    onclick={() => showLinkModal = true}
                    class="p-1.5 hover:bg-white/10 hover:text-white rounded-lg transition-colors group relative"
                    title="Gán cho bài viết/sản phẩm"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                    <span class="absolute -top-10 left-1/2 -translate-x-1/2 bg-zinc-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap transition-opacity shadow-xl border border-white/10">LƯU VẾT BÀI</span>
                </button>

                <button 
                    onclick={handleMagicWand} 
                    class="p-1.5 hover:bg-white/10 hover:text-white rounded-lg transition-colors group relative"
                    class:animate-pulse={isAutoFilling}
                    title="AI Alt-text"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21 11-8-8"/><path d="m21 3-9 9"/><path d="M12 12 3 21"/><path d="m11 21 8-8"/><circle cx="7.5" cy="7.5" r=".5"/><circle cx="10.5" cy="10.5" r=".5"/><circle cx="13.5" cy="13.5" r=".5"/></svg>
                    <span class="absolute -top-10 left-1/2 -translate-x-1/2 bg-zinc-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap transition-opacity shadow-xl border border-white/10">AI ALT-TEXT</span>
                </button>

                <button 
                    onclick={() => {
                        const ids = Array.from(mediaStore.selectedIds);
                        mediaStore.bulkDownload(ids);
                    }}
                    class="p-1.5 hover:bg-white/10 hover:text-white rounded-lg transition-colors group relative"
                    title="Tải ZIP"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    <span class="absolute -top-10 left-1/2 -translate-x-1/2 bg-zinc-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap transition-opacity shadow-xl border border-white/10">TẢI ZIP</span>
                </button>

                <button 
                    onclick={() => showBulkSeo = true}
                    class="p-1.5 hover:bg-white/10 hover:text-white rounded-lg transition-colors group relative"
                    title="Tối ưu SEO"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
                    <span class="absolute -top-10 left-1/2 -translate-x-1/2 bg-zinc-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap transition-opacity shadow-xl border border-white/10">TỐI ƯU SEO</span>
                </button>

                <div class="w-px h-4 bg-white/20 mx-1"></div>

                {#if mediaStore.isTrashMode}
                <button 
                    onclick={() => mediaStore.bulkRestore()} 
                    class="p-1.5 hover:bg-green-500 hover:text-white rounded-lg transition-colors group relative text-green-400"
                    title="Khôi phục"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                    <span class="absolute -top-10 left-1/2 -translate-x-1/2 bg-zinc-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap transition-opacity shadow-xl border border-white/10">KHÔI PHỤC</span>
                </button>
                {/if}

                <button 
                    onclick={handleBulkDelete} 
                    class="p-1.5 hover:bg-red-500 hover:text-white rounded-lg transition-colors group relative text-red-400"
                    title={mediaStore.isTrashMode ? "Xoá vĩnh viễn khỏi đĩa" : "Chuyển vào thùng rác"}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>
                    </svg>
                    <span class="absolute -top-10 left-1/2 -translate-x-1/2 bg-zinc-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap transition-opacity shadow-xl border border-white/10">
                        {mediaStore.isTrashMode ? 'PURGE FILE' : 'XÓA TẠM'}
                    </span>
                </button>
            </div>
            <button onclick={() => mediaStore.clearSelection()} class="text-[10px] font-black uppercase text-zinc-500 hover:text-white ml-2 transition-colors">Đóng</button>
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

    <!-- ── MODAL: LINK TO POST ── -->
    {#if showLinkModal}
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[200]" transition:fade>
            <div class="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 w-full max-w-sm overflow-hidden" transition:slide>
                <div class="p-4 border-b flex items-center justify-between bg-zinc-50 dark:bg-zinc-800/50">
                    <h3 class="font-bold text-[10px] uppercase tracking-wider">GẮN ẢNH VÀO BÀI VIẾT / SẢN PHẨM</h3>
                    <button onclick={() => showLinkModal = false} class="text-zinc-500 hover:text-zinc-700">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div class="p-5 space-y-4">
                    <p class="text-[10px] text-zinc-500 uppercase font-black tracking-widest">Đang gán {mediaStore.selectedIds.size} ảnh:</p>

                    <div class="space-y-4">
                        <div>
                            <label class="block text-[9px] font-bold text-zinc-400 uppercase mb-2">Phân loại nội dung</label>
                            <div class="grid grid-cols-2 gap-2">
                                <button
                                    onclick={() => linkPostType = 'news'}
                                    class="flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 transition-all {linkPostType === 'news' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600' : 'border-zinc-100 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'}"
                                >
                                    <span class="text-[10px] font-black uppercase">Article</span>
                                </button>
                                <button
                                    onclick={() => linkPostType = 'product'}
                                    class="flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 transition-all {linkPostType === 'product' ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20 text-orange-600' : 'border-zinc-100 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'}"
                                >
                                    <span class="text-[10px] font-black uppercase">Product</span>
                                </button>
                            </div>
                        </div>

                        <div>
                            <label class="block text-[9px] font-bold text-zinc-400 uppercase mb-2">ID Bài viết / SKU Sản phẩm</label>
                            <input
                                type="text"
                                bind:value={linkPostId}
                                placeholder="Nhập mã định danh..."
                                class="w-full px-4 py-3 bg-zinc-50 dark:bg-zinc-800 border rounded-xl outline-none focus:ring-2 focus:ring-blue-500 text-xs font-mono"
                            />
                        </div>
                    </div>
                </div>
                <div class="p-4 bg-zinc-50 dark:bg-zinc-800/50 border-t flex items-center justify-end gap-3">
                    <button onclick={() => showLinkModal = false} class="px-4 py-2 text-[10px] font-black text-zinc-500 hover:text-zinc-700 uppercase">Huỷ</button>
                    <button
                        onclick={handleLinkToPost}
                        disabled={!linkPostId.trim()}
                        class="px-6 py-2.5 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-xl text-[10px] font-black uppercase hover:scale-105 transition-all shadow-lg shadow-zinc-500/20 disabled:opacity-50"
                    >
                        XÁC NHẬN LƯU VẾT
                    </button>
                </div>
            </div>
        </div>
    {/if}

    <!-- ── MODAL: HARD DELETE CONFIRM ── -->
    {#if pendingHardDeleteId}
        <div class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-[210]" transition:fade>
            <div class="bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl border border-red-500/20 w-full max-w-sm overflow-hidden" transition:slide>
                <div class="p-8 text-center space-y-4">
                    <div class="w-20 h-20 bg-red-100 dark:bg-red-900/30 text-red-600 rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce">
                        <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                    </div>
                    <h3 class="text-xl font-black text-red-600 uppercase italic tracking-tighter">XOÁ TRIỆT ĐỂ KHỎI SERVER</h3>
                    <p class="text-[11px] text-zinc-500 leading-relaxed font-medium">
                        Dữ liệu này sẽ biến mất vĩnh viễn khỏi ổ cứng. <br/>
                        Hành động này <b>KHÔNG THỂ KHÔI PHỤC</b>. <br/>
                        Sếp chắc chắn chứ?
                    </p>
                </div>
                <div class="p-6 bg-zinc-50 dark:bg-zinc-800/50 border-t grid grid-cols-2 gap-4">
                    <button onclick={() => pendingHardDeleteId = null} class="py-4 bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-200 rounded-2xl text-[10px] font-black uppercase transition-all hover:bg-zinc-300">HUỶ (AN TOÀN)</button>
                    <button onclick={confirmHardDelete} class="py-4 bg-red-600 text-white rounded-2xl text-[10px] font-black uppercase transition-all hover:bg-red-700 hover:scale-105 shadow-xl shadow-red-500/30">XOÁ VĨNH VIỄN</button>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    /* ═══ Liquid Glass iOS 2026 ═══ */
    .file-manager :global(.custom-scrollbar::-webkit-scrollbar) {
        width: 4px;
        height: 4px;
    }
    .file-manager :global(.custom-scrollbar::-webkit-scrollbar-track) {
        background: transparent;
    }
    .file-manager :global(.custom-scrollbar::-webkit-scrollbar-thumb) {
        background: rgba(255,255,255,0.08);
        border-radius: 20px;
    }
    .file-manager :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) {
        background: rgba(255,255,255,0.15);
    }

    /* Glass Card — subtle inner light on edges */
    .file-manager :global(.glass-card) {
        box-shadow:
            inset 0 1px 0 0 rgba(255,255,255,0.04),
            0 2px 8px -2px rgba(0,0,0,0.3);
    }
    .file-manager :global(.glass-card:hover) {
        box-shadow:
            inset 0 1px 0 0 rgba(255,255,255,0.08),
            0 8px 25px -5px rgba(0,0,0,0.4),
            0 0 0 1px rgba(255,255,255,0.06);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px) scale(0.97); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    .file-manager :global(.grid-item) {
        animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    @keyframes scan-loop {
        0% { top: 0; opacity: 0.8; }
        50% { opacity: 0.4; }
        100% { top: 100%; opacity: 0; }
    }

    .file-manager :global(.animate-scan-loop) {
        animation: scan-loop 2.5s ease-in-out infinite;
    }
</style>
