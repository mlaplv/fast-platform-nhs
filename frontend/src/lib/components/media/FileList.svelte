<script lang="ts">
  import { mediaStore } from '$lib/state/media.svelte';
  import type { MediaAsset } from '$lib/state/types';
  import { formatDate } from '$lib/state/utils';
  import { fade, scale } from 'svelte/transition';
  import Check from "@lucide/svelte/icons/check";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import FileText from "@lucide/svelte/icons/file-text";
  import ImageIcon from "@lucide/svelte/icons/image";
  import FileCode from "@lucide/svelte/icons/file-code";
  import Film from "@lucide/svelte/icons/film";
  import Music from "@lucide/svelte/icons/music";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";
  import Calendar from "@lucide/svelte/icons/calendar";
  import Database from "@lucide/svelte/icons/database";
  import HardDrive from "@lucide/svelte/icons/hard-drive";
  import Tag from "@lucide/svelte/icons/tag";
  import Eye from "@lucide/svelte/icons/eye";
    import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';

    interface Props {
        assets: MediaAsset[];
        selectedAssetId: string | null;
        mode?: 'manage' | 'pick';
        onSelect?: (assets: MediaAsset[]) => void;
        onDelete: (id: string) => void;
        onRestore: (id: string) => void;
        onPreview: (url: string) => void;
    }

    let {
        assets,
        selectedAssetId = $bindable(),
        mode = 'manage',
        onSelect,
        onDelete,
        onRestore,
        onPreview
    } = $props<Props>();

    function handleSelect(asset: MediaAsset) {
        selectedAssetId = asset.id;
        if (mode === 'pick') {
            mediaStore.toggleSelection(asset.id);
        }
    }

    function getIcon(mimeType?: string) {
        if (mimeType?.startsWith('image/')) return ImageIcon;
        if (mimeType?.startsWith('video/')) return Film;
        if (mimeType?.startsWith('audio/')) return Music;
        if (mimeType?.includes('code') || mimeType?.includes('html') || mimeType?.includes('json')) return FileCode;
        return FileText;
    }
</script>

<div class="w-full overflow-x-auto no-scrollbar pb-10">
    <table class="w-full text-left border-separate border-spacing-y-2">
        <thead>
            <tr class="text-[9px] font-black text-zinc-400 dark:text-zinc-500 tracking-[0.3em] px-4">
                <th class="pb-4 pl-6 w-24">Select</th>
                <th class="pb-4">Filename / Metadata</th>
                <th class="pb-4 w-28">Size <Database size={10} class="inline ml-1 opacity-40" /></th>
                <th class="pb-4 w-32">Mime Type <Tag size={10} class="inline ml-1 opacity-40" /></th>
                <th class="pb-4 w-32">Created <Calendar size={10} class="inline ml-1 opacity-40" /></th>
                <th class="pb-4 pr-6 w-24 text-right">Actions</th>
            </tr>
        </thead>
        <tbody>
            {#each assets as asset (asset.id)}
                {@const Icon = getIcon(asset.mime_type)}
                <tr 
                    tabindex="0"
                    class="group bg-white dark:bg-[#0c0e14] hover:bg-zinc-50 dark:hover:bg-zinc-800/20 rounded-2xl transition-all duration-300 border-2 shadow-sm cursor-pointer relative {mediaStore.selectedIds.has(asset.id) ? 'border-blue-500 ring-4 ring-blue-500/10' : (selectedAssetId === asset.id ? 'border-blue-500' : 'border-transparent')}"
                    onclick={() => handleSelect(asset)}
                    onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && handleSelect(asset)}
                    transition:fade={{ duration: 150 }}
                >
                    <!-- Column: Select & Preview -->
                    <td class="py-4 pl-6 rounded-l-2xl">
                        <div class="flex items-center gap-3">
                            <button
                                onclick={(e) => {
                                    e.stopPropagation();
                                    mediaStore.toggleSelection(asset.id);
                                }}
                                class="w-5 h-5 rounded-md border flex items-center justify-center transition-all duration-200 flex-shrink-0
                                {mediaStore.selectedIds.has(asset.id)
                                    ? 'bg-blue-500 border-blue-500 text-white shadow-md shadow-blue-500/20'
                                    : 'border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-transparent hover:border-blue-500'}"
                            >
                                <Check size={12} strokeWidth={4} />
                            </button>

                            <div class="w-12 h-12 rounded-xl overflow-hidden bg-zinc-100 dark:bg-zinc-800 border-2 border-transparent group-hover:border-blue-500/20 transition-all shadow-inner relative flex-shrink-0">
                                {#if asset.mime_type?.startsWith('image/')}
                                    <img
                                        src={resolveThumbnailUrl(asset, 100)}
                                        alt=""
                                        class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                                        loading="lazy"
                                    />
                                {:else if asset.mime_type?.startsWith('video/')}
                                    <video
                                        src={asset.file_path}
                                        class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                                        muted
                                        playsinline
                                        onmouseenter={(e) => (e.target as HTMLVideoElement).play().catch(() => {})}
                                        onmouseleave={(e) => {
                                            const v = e.target as HTMLVideoElement;
                                            v.pause();
                                            v.currentTime = 0;
                                        }}
                                        onerror={(e) => {
                                            const video = e.target as HTMLVideoElement;
                                            console.error('[FileManager] List Video error:', {
                                                error: video.error,
                                                src: video.src,
                                                networkState: video.networkState,
                                                readyState: video.readyState
                                            });
                                        }}
                                    ></video>
                                {:else}
                                    <div class="w-full h-full flex items-center justify-center text-zinc-400 group-hover:text-blue-500 transition-colors">
                                        <Icon size={20} />
                                    </div>
                                {/if}
                            </div>
                        </div>
                    </td>

                    <!-- Column: Filename -->
                    <td class="py-4">
                        <div class="flex flex-col gap-0.5">
                            <span class="text-[11px] font-bold text-zinc-800 dark:text-zinc-200 group-hover:text-blue-500 transition-colors truncate max-w-[300px]">{asset.filename || 'unnamed_asset'}</span>
                            <div class="flex items-center gap-2">
                                <span class="text-[9px] font-mono text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded tracking-tighter">ID: {asset.id.slice(0, 12)}</span>
                                {#if asset.is_primary}
                                    <span class="text-[8px] font-black text-white bg-indigo-500 px-1.5 py-0.5 rounded tracking-tighter">Primary</span>
                                {/if}
                                {#if !asset.is_linked && !asset.id?.startsWith('tmp_') && !mediaStore.isTrashMode}
                                    <span class="text-[8px] font-black text-amber-600 bg-amber-100 dark:bg-amber-900/30 px-1.5 py-0.5 rounded tracking-tighter">Mồ côi</span>
                                {/if}
                            </div>
                        </div>
                    </td>

                    <!-- Column: Size -->
                    <td class="py-4 font-mono">
                        <span class="text-[10px] font-medium text-zinc-500 group-hover:text-zinc-700 dark:group-hover:text-zinc-300 transition-colors">
                            {formatBytes(asset.file_size)}
                        </span>
                    </td>

                    <!-- Column: Type -->
                    <td class="py-4">
                        <span class="text-[9px] font-black px-2.5 py-1 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-500 tracking-widest border border-transparent group-hover:border-blue-500/10 transition-all">
                            {asset.mime_type?.split('/')[1] || 'Unknown'}
                        </span>
                    </td>

                    <!-- Column: Date -->
                    <td class="py-4">
                        <span class="text-[10px] text-zinc-500 font-medium whitespace-nowrap">
                            {formatDate(asset.created_at)}
                        </span>
                    </td>

                    <!-- Column: Actions -->
                    <td class="py-4 pr-6 text-right rounded-r-2xl">
                        <div class="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            {#if !mediaStore.isTrashMode && (asset.mime_type?.startsWith('image/'))}
                                <button
                                    onclick={(e) => { e.stopPropagation(); onPreview(resolveThumbnailUrl(asset, 100)); }}
                                    class="w-8 h-8 flex items-center justify-center bg-zinc-100 dark:bg-zinc-800 text-zinc-500 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-xl transition-all shadow-sm active:scale-90"
                                    title="Xem ảnh"
                                >
                                    <Eye size={14} />
                                </button>
                            {/if}
                            {#if mediaStore.isTrashMode}
                                <button
                                    onclick={(e) => { e.stopPropagation(); onRestore(asset.id); }}
                                    class="w-8 h-8 flex items-center justify-center bg-green-500/10 text-green-500 hover:bg-green-500 hover:text-white rounded-xl transition-all shadow-sm active:scale-90"
                                    title="Khôi phục"
                                >
                                    <RotateCcw size={14} />
                                </button>
                                <button
                                    onclick={(e) => { e.stopPropagation(); onDelete(asset.id); }}
                                    class="w-8 h-8 flex items-center justify-center bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white rounded-xl transition-all shadow-sm active:scale-90"
                                    title="Xoá vĩnh viễn"
                                >
                                    <Trash2 size={14} />
                                </button>
                            {:else}
                                <div class="w-8 h-8 flex items-center justify-center text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl transition-all">
                                    <MoreHorizontal size={14} />
                                </div>
                            {/if}
                        </div>
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>
    
    {#if assets.length === 0}
        <div class="flex flex-col items-center justify-center py-20 bg-zinc-50/50 dark:bg-white/[0.01] rounded-[2rem] border-2 border-dashed border-zinc-100 dark:border-zinc-800">
            <span class="text-[10px] font-black text-zinc-300 dark:text-zinc-600 tracking-[0.4em]">Danh sách trống</span>
        </div>
    {/if}
</div>

<style>
    /* CSS for table-like behavior with spacing */
    tr {
        display: table-row !important;
    }
    
    td {
        border-top: 1px solid transparent;
        border-bottom: 1px solid transparent;
    }
    
    tr:hover td {
        border-top-color: rgba(59, 130, 246, 0.1);
        border-bottom-color: rgba(59, 130, 246, 0.1);
    }
</style>
