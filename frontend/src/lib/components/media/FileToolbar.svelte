<script lang="ts">
  import type { MediaAsset } from '$lib/state/types';
    import Search from "@lucide/svelte/icons/search";
  import Upload from "@lucide/svelte/icons/upload";
  import Link from "@lucide/svelte/icons/link";
  import LayoutGrid from "@lucide/svelte/icons/layout-grid";
  import List from "@lucide/svelte/icons/list";
  import BarChart3 from "@lucide/svelte/icons/bar-chart-3";
  import Filter from "@lucide/svelte/icons/filter";
  import FileEdit from "@lucide/svelte/icons/file-edit";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Brain from "@lucide/svelte/icons/brain";
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';

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
    isTrashMode: boolean;
    onToggleTrash: () => void;
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
    isTrashMode,
    onToggleTrash,
    campaignId
  } = $props<Props>();

</script>

<header class="p-4 border-b border-zinc-200 dark:border-zinc-700/50 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md sticky top-0 flex flex-wrap items-center justify-between gap-4" style="z-index: {Z_INDEX_ADMIN.LAYOUT_HEADER};">
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
                <Upload size={14} />
                {isUploading ? 'ĐANG TẢI...' : 'TẢI LÊN'}
            </button>
            <button
                onclick={onRemoteUrlClick}
                class="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-500 rounded-lg transition-all"
                title="Nhập URL ảnh"
            >
                <Link size={18} />
            </button>
        </div>
    </div>

    <div class="flex items-center gap-2">
        <div class="flex items-center bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl border border-zinc-200 dark:border-zinc-700">
            <button
                onclick={onViewModeToggle}
                class="p-1.5 rounded-lg transition-all {viewMode === 'grid' ? 'bg-white dark:bg-zinc-700 shadow-sm text-blue-500' : 'text-zinc-500 hover:text-zinc-700'}"
            >
                <LayoutGrid size={18} />
            </button>
            <button
                onclick={onViewModeToggle}
                class="p-1.5 rounded-lg transition-all {viewMode === 'list' ? 'bg-white dark:bg-zinc-700 shadow-sm text-blue-500' : 'text-zinc-500 hover:text-zinc-700'}"
            >
                <List size={18} />
            </button>
        </div>

        <div class="flex items-center gap-1 bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl border border-zinc-200 dark:border-zinc-700">
            <button
                onclick={onToggleStats}
                class="p-1.5 rounded-lg transition-all {showStats ? 'bg-white dark:bg-zinc-700 shadow-sm text-blue-500' : 'text-zinc-500 hover:text-zinc-700'}"
                title="Thống kê"
            >
                <BarChart3 size={18} />
            </button>
            <button
                onclick={onPostFilterToggle}
                class="p-1.5 rounded-lg transition-all {showPostFilter ? 'bg-white dark:bg-zinc-700 shadow-sm text-blue-500' : 'text-zinc-500 hover:text-zinc-700'}"
                title="Lọc theo bài viết"
            >
                <Filter size={18} />
            </button>
            <button
                onclick={onBulkSeoClick}
                class="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-500 rounded-lg transition-all relative"
                title="Sửa Bulk SEO"
            >
                <FileEdit size={18} />
            </button>
            <button
                onclick={onRefresh}
                class="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-500 rounded-lg transition-all"
                title="Làm mới"
            >
                <RefreshCw size={18} />
            </button>
            <button
                onclick={onToggleTrash}
                class="p-1.5 rounded-lg transition-all {isTrashMode ? 'bg-red-500/10 text-red-500' : 'text-zinc-500 hover:text-zinc-700'}"
                title="Thùng rác"
            >
                <Trash2 size={18} />
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
                <Brain size={16} />
            </div>
            <span class="text-[10px] font-black uppercase tracking-widest">{aiVisionEnabled ? 'AI VISION: ON' : 'AI VISION: OFF'}</span>
        </button>

        {#if onPickConfirm}
            <button
                onclick={onPickConfirm}
                class="ml-2 flex items-center gap-2 px-6 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all shadow-lg shadow-blue-500/20"
                title="Xác nhận"
            >
                <Check size={16} />
                Xác nhận
            </button>
        {/if}

        {#if onPickClose}
            <button
               onclick={onPickClose}
               class="ml-1 w-9 h-9 flex items-center justify-center bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white rounded-xl transition-all"
               title="Đóng thư viện"
            >
               <X size={18} />
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
