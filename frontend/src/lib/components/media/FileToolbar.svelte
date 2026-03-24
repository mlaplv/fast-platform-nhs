<script lang="ts">
  import type { MediaAsset } from '$lib/state/types';

  interface Props {
    searchQuery: string;
    viewMode: 'grid' | 'list';
    showPostFilter: boolean;
    filterPostType: string;
    filterPostId: string;
    showUnlinkedOnly: boolean;
    showStats: boolean;
    aiVisionEnabled: boolean;
    isUploading: boolean;
    isAutoFilling: boolean;
    onUploadClick: () => void;
    onRemoteUrlClick: () => void;
    onToggleStats: () => void;
    onToggleAIVision: () => void;
    onBulkSeoClick: () => void;
    onRefresh: () => void;
    onViewModeToggle: () => void;
    onPostFilterToggle: () => void;
    mode?: 'manage' | 'pick';
    pickTabActive?: 'current' | 'ai' | 'library';
    onPickTabChange?: (tab: string) => void;
    onPickConfirm?: () => void;
    onPickClose?: () => void;
    campaignId?: string;
  }

  let {
    searchQuery = $bindable(),
    viewMode = $bindable(),
    showPostFilter = $bindable(),
    filterPostType = $bindable(),
    filterPostId = $bindable(),
    showUnlinkedOnly = $bindable(),
    showStats = $bindable(),
    aiVisionEnabled,
    isUploading,
    isAutoFilling,
    onUploadClick,
    onRemoteUrlClick,
    onToggleStats,
    onToggleAIVision,
    onBulkSeoClick,
    onRefresh,
    onViewModeToggle,
    onPostFilterToggle,
    mode = 'manage',
    pickTabActive,
    onPickTabChange,
    onPickConfirm,
    onPickClose,
    campaignId
  } = $props<Props>();

</script>

<header class="p-4 border-b border-zinc-200 dark:border-zinc-700/50 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md sticky top-0 z-30 flex flex-wrap items-center justify-between gap-4">
    <div class="flex items-center gap-4 flex-1 min-w-[300px]">
        <div class="relative flex-1 max-w-md group">
            <div class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 group-focus-within:text-blue-500 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </div>
            <input
                type="text"
                bind:value={searchQuery}
                placeholder="Tìm kiếm ảnh, tags, phong cách AI..."
                class="w-full pl-10 pr-4 py-2 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm transition-all"
            />
        </div>

        <div class="flex items-center gap-1 bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl border border-zinc-200 dark:border-zinc-700">
            <button
                onclick={onUploadClick}
                disabled={isUploading}
                class="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-xs font-bold transition-all shadow-lg shadow-blue-500/20"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                {isUploading ? 'ĐANG TẢI...' : 'TẢI LÊN'}
            </button>
            <button
                onclick={onRemoteUrlClick}
                class="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-500 rounded-lg transition-all"
                title="Nhập URL ảnh"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            </button>
        </div>
    </div>

    <div class="flex items-center gap-2">
        <div class="flex items-center bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl border border-zinc-200 dark:border-zinc-700">
            <button
                onclick={onViewModeToggle}
                class="p-1.5 rounded-lg transition-all {viewMode === 'grid' ? 'bg-white dark:bg-zinc-700 shadow-sm text-blue-500' : 'text-zinc-500 hover:text-zinc-700'}"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
            </button>
            <button
                onclick={onViewModeToggle}
                class="p-1.5 rounded-lg transition-all {viewMode === 'list' ? 'bg-white dark:bg-zinc-700 shadow-sm text-blue-500' : 'text-zinc-500 hover:text-zinc-700'}"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
            </button>
        </div>

        <div class="flex items-center gap-1 bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl border border-zinc-200 dark:border-zinc-700">
            <button
                onclick={onToggleStats}
                class="p-1.5 rounded-lg transition-all {showStats ? 'bg-white dark:bg-zinc-700 shadow-sm text-blue-500' : 'text-zinc-500 hover:text-zinc-700'}"
                title="Thống kê"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            </button>
            <button
                onclick={onPostFilterToggle}
                class="p-1.5 rounded-lg transition-all {showPostFilter ? 'bg-white dark:bg-zinc-700 shadow-sm text-blue-500' : 'text-zinc-500 hover:text-zinc-700'}"
                title="Lọc theo bài viết"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
            </button>
            <button
                onclick={onBulkSeoClick}
                class="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-500 rounded-lg transition-all relative"
                title="Sửa Bulk SEO"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 12h10"/><path d="M12 7v10"/></svg>
            </button>
            <button
                onclick={onRefresh}
                class="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-500 rounded-lg transition-all"
                title="Làm mới"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
            </button>
        </div>

        <button
            onclick={onToggleAIVision}
            class="group flex items-center gap-2 px-3 py-1.5 rounded-xl border transition-all
            {aiVisionEnabled
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white border-transparent shadow-lg shadow-blue-500/20'
                : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400 border-zinc-200 dark:border-zinc-700 hover:text-zinc-600'}"
        >
            <div class={aiVisionEnabled ? 'animate-pulse' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
            </div>
            <span class="text-[10px] font-black uppercase tracking-widest">{aiVisionEnabled ? 'AI VISION: ON' : 'AI VISION: OFF'}</span>
        </button>

        {#if onPickConfirm}
            <button
                onclick={onPickConfirm}
                class="ml-2 flex items-center gap-2 px-6 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all shadow-lg shadow-blue-500/20"
                title="Xác nhận"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                Xác nhận
            </button>
        {/if}

        {#if onPickClose}
            <button
               onclick={onPickClose}
               class="ml-1 w-9 h-9 flex items-center justify-center bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white rounded-xl transition-all"
               title="Đóng thư viện"
            >
               <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
        {/if}
    </div>
</header>

{#if showPostFilter}
<div class="px-4 py-3 bg-zinc-50 dark:bg-zinc-800/30 border-b border-zinc-200 dark:border-zinc-700/50 flex flex-wrap items-center gap-4 animate-in slide-in-from-top-1 duration-200">
    <div class="flex items-center gap-2">
        <label for="post-type" class="text-[10px] font-bold text-zinc-400 uppercase">Loại:</label>
        <select
            id="post-type"
            bind:value={filterPostType}
            class="bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg px-2 py-1 text-xs outline-none focus:ring-1 focus:ring-blue-500"
        >
            <option value="">Tất cả</option>
            <option value="news">Bài viết</option>
            <option value="product">Sản phẩm</option>
        </select>
    </div>
    <div class="flex items-center gap-2">
        <label for="post-id" class="text-[10px] font-bold text-zinc-400 uppercase">ID/SKU:</label>
        <input
            id="post-id"
            type="text"
            bind:value={filterPostId}
            placeholder="Nhập mã định danh..."
            class="bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg px-3 py-1 text-xs outline-none focus:ring-1 focus:ring-blue-500 w-40"
        />
    </div>
    <label class="flex items-center gap-2 cursor-pointer group">
        <div class="relative w-8 h-4 bg-zinc-200 dark:bg-zinc-700 rounded-full transition-colors group-hover:bg-zinc-300 dark:group-hover:bg-zinc-600">
            <input type="checkbox" bind:checked={showUnlinkedOnly} class="sr-only peer" />
            <div class="absolute left-1 top-1 w-2 h-2 bg-white rounded-full transition-transform peer-checked:translate-x-4 peer-checked:bg-blue-500"></div>
        </div>
        <span class="text-[10px] font-bold text-zinc-500 uppercase">Chỉ ảnh chưa gắn link</span>
    </label>
</div>
{/if}
