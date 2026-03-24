<script lang="ts">
    import { mediaStore } from '$lib/state/media.svelte';
    import type { MediaAsset } from '$lib/state/types';
    import { fade, scale } from 'svelte/transition';
    import { Check, Trash2, RotateCcw, FileText, Image as ImageIcon, FileCode, Film, Music, MoreHorizontal, Calendar, Database, HardDrive, Tag } from 'lucide-svelte';

    interface Props {
        assets: MediaAsset[];
        selectedAssetId: string | null;
        mode?: 'manage' | 'pick';
        onSelect?: (assets: MediaAsset[]) => void;
        onDelete: (id: string) => void;
        onRestore: (id: string) => void;
    }

    let { 
        assets, 
        selectedAssetId = $bindable(), 
        mode = 'manage', 
        onSelect, 
        onDelete, 
        onRestore 
    } = $props<Props>();

    function handleSelect(asset: MediaAsset) {
        selectedAssetId = asset.id;
        if (mode === 'pick') {
            mediaStore.toggleSelection(asset.id);
        }
    }

    function formatBytes(bytes: number = 0) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function formatDate(dateStr?: string) {
        if (!dateStr) return 'N/A';
        return new Date(dateStr).toLocaleDateString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    function getIcon(mimeType?: string) {
        if (mimeType?.startsWith('image/')) return ImageIcon;
        if (mimeType?.startsWith('video/')) return Film;
        if (mimeType?.startsWith('audio/')) return Music;
        if (mimeType?.includes('code') || mimeType?.includes('html') || mimeType?.includes('json')) return FileCode;
        return FileText;
    }

    function getImageUrl(asset: MediaAsset) {
        if (asset.id?.startsWith('tmp_')) return asset.file_path;
        const base = `/api/v1/media/${asset.id}/thumb?w=100`;
        return asset._updatedAt ? `${base}&t=${asset._updatedAt}` : base;
    }
</script>

<div class="w-full overflow-x-auto no-scrollbar pb-10">
    <table class="w-full text-left border-separate border-spacing-y-2">
        <thead>
            <tr class="text-[9px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-[0.3em] px-4">
                <th class="pb-4 pl-6 w-16">Preview</th>
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
                    <!-- Column: Preview -->
                    <td class="py-4 pl-6 rounded-l-2xl">
                        <div class="w-12 h-12 rounded-xl overflow-hidden bg-zinc-100 dark:bg-zinc-800 border-2 border-transparent group-hover:border-blue-500/20 transition-all shadow-inner relative">
                            {#if asset.mime_type?.startsWith('image/')}
                                <img 
                                    src={getImageUrl(asset)} 
                                    alt="" 
                                    class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" 
                                    loading="lazy"
                                />
                                {#if mediaStore.selectedIds.has(asset.id)}
                                    <div class="absolute inset-0 bg-blue-500/40 flex items-center justify-center" transition:fade>
                                        <Check size={16} class="text-white" strokeWidth={3} />
                                    </div>
                                {/if}
                            {:else}
                                <div class="w-full h-full flex items-center justify-center text-zinc-400 group-hover:text-blue-500 transition-colors">
                                    <Icon size={20} />
                                </div>
                            {/if}
                        </div>
                    </td>

                    <!-- Column: Filename -->
                    <td class="py-4">
                        <div class="flex flex-col gap-0.5">
                            <span class="text-[11px] font-bold text-zinc-800 dark:text-zinc-200 group-hover:text-blue-500 transition-colors truncate max-w-[300px]">{asset.filename || 'unnamed_asset'}</span>
                            <div class="flex items-center gap-2">
                                <span class="text-[9px] font-mono text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded tracking-tighter">ID: {asset.id.slice(0, 12)}</span>
                                {#if asset.is_primary}
                                    <span class="text-[8px] font-black text-white bg-indigo-500 px-1.5 py-0.5 rounded uppercase tracking-tighter">Primary</span>
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
                        <span class="text-[9px] font-black px-2.5 py-1 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-500 uppercase tracking-widest border border-transparent group-hover:border-blue-500/10 transition-all">
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
            <span class="text-[10px] font-black text-zinc-300 dark:text-zinc-600 uppercase tracking-[0.4em]">Danh sách trống</span>
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
