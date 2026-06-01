<script lang="ts">
  import { mediaStore } from '$lib/state/media.svelte';
  import type { MediaAsset } from '$lib/state/types';
  import { resolveThumbnailUrl } from '$lib/state/utils';
  import { fade, scale } from 'svelte/transition';
  import Eye from "@lucide/svelte/icons/eye";
  import Check from "@lucide/svelte/icons/check";
  import Star from "@lucide/svelte/icons/star";
  import Info from "@lucide/svelte/icons/info";
    import TrashActions from './TrashActions.svelte';
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
</script>

<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 p-1">
    {#each assets as asset (asset.id)}
        <div 
            role="button"
            tabindex="0"
            class="group relative aspect-square rounded-2xl overflow-hidden border-2 transition-all duration-500 cursor-pointer shadow-lg hover:shadow-blue-500/20 {mediaStore.selectedIds.has(asset.id) ? 'border-blue-500 ring-4 ring-blue-500/10' : (selectedAssetId === asset.id ? 'border-blue-500' : 'border-transparent')}"
            onclick={() => handleSelect(asset)}
            onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && handleSelect(asset)}
        >
            <!-- Asset Preview Core (Elite V2.2) -->
            {#if asset.mime_type?.startsWith('video/')}
                    <video
                        src={asset.file_path}
                        class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
                        muted
                        playsinline
                        preload="none"
                        poster={asset.id?.startsWith('tmp_') ? '' : `/api/v1/media/${asset.id}/thumb?w=400`}
                        onmouseenter={(e) => (e.target as HTMLVideoElement).play().catch(() => {})}
                        onmouseleave={(e) => {
                            const v = e.target as HTMLVideoElement;
                            v.pause();
                            v.currentTime = 0;
                        }}
                        onerror={(e) => {
                            const video = e.target as HTMLVideoElement;
                            console.error('[FileManager] Grid Video error:', {
                                error: video.error,
                                src: video.src,
                                networkState: video.networkState,
                                readyState: video.readyState
                            });
                        }}
                    >
                    </video>
            {:else}
                <img
                    src={resolveThumbnailUrl(asset, 400)}
                    alt={asset.alt_text || asset.filename || 'Media asset'}
                    class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
                    loading="lazy"
                />
            {/if}

            <!-- Glassmorphism Gradient Overlay -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-40 group-hover:opacity-100 transition-opacity duration-500">
                <!-- Preview Action (Top-Right) -->
                {#if !asset.mime_type?.startsWith('video/') && !mediaStore.isTrashMode}
                    <button
                        onclick={(e) => { e.stopPropagation(); onPreview(resolveThumbnailUrl(asset, 400)); }}
                        class="absolute top-3 right-3 p-1.5 bg-black/40 backdrop-blur-md border border-white/10 rounded-lg text-white hover:bg-white hover:text-black transition-all"
                        title="Xem ảnh"
                    >
                        <Eye size={14} />
                    </button>
                {/if}
            </div>

            <!-- Selection Checkbox Badge (Top-Left) -->
            <button
                onclick={(e) => {
                    e.stopPropagation();
                    mediaStore.toggleSelection(asset.id);
                }}
                class="absolute top-3 left-3 w-7 h-7 rounded-full flex items-center justify-center border transition-all duration-300
                {mediaStore.selectedIds.has(asset.id)
                    ? 'bg-blue-500 text-white border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]'
                    : 'bg-black/30 border-white/20 text-white/70 hover:bg-black/60 hover:text-white opacity-0 group-hover:opacity-100'}"
                style="z-index: {Z_INDEX_ADMIN.GRID_HOVER};"
            >
                <Check size={16} strokeWidth={3} />
            </button>

            <!-- Primary Marker (Top-Right) -->
            {#if asset.is_primary}
                <div class="absolute top-3 right-3 px-2 py-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg flex items-center gap-1 shadow-xl" style="z-index: {Z_INDEX_ADMIN.GRID_HOVER};">
                    <Star size={10} class="fill-amber-400 text-amber-400" />
                    <span class="text-[8px] font-black text-white tracking-tighter">Primary</span>
                </div>
            {:else if !asset.is_linked && !asset.id?.startsWith('tmp_') && !mediaStore.isTrashMode}
                <!-- Orphaned Marker (Elite V2.2) -->
                <div class="absolute top-3 right-3 px-2 py-1 bg-amber-500/10 backdrop-blur-md border border-amber-500/20 rounded-lg flex items-center gap-1 shadow-xl" style="z-index: {Z_INDEX_ADMIN.GRID_HOVER};" transition:fade>
                    <Info size={10} class="text-amber-500" />
                    <span class="text-[8px] font-black text-amber-500 tracking-tighter">Mồ côi</span>
                </div>
            {/if}

            <!-- Bottom Info Strip -->
            <div class="absolute bottom-0 inset-x-0 p-3 flex flex-col gap-0.5 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-500">
                <span class="text-[10px] font-bold text-white truncate drop-shadow-md">{asset.filename || 'unnamedfile'}</span>
                <div class="flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-500 delay-75">
                    <span class="text-[8px] font-black text-blue-300 tracking-widest leading-none">
                        {asset.mime_type?.split('/')[1] || 'FILE'}
                    </span>
                    <span class="text-[8px] font-mono text-white/40">
                        {asset.file_size ? Math.round(asset.file_size / 1024) : 0} KB
                    </span>
                </div>
            </div>

            <!-- Trash Mode Visual Gating -->
            {#if mediaStore.isTrashMode}
                <TrashActions {asset} {onRestore} {onDelete} />
            {/if}

            <!-- Progress/Loading pulse for temp assets -->
            {#if asset.id?.startsWith('tmp_')}
                <div class="absolute inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center" style="z-index: {Z_INDEX_ADMIN.OVERLAY};">
                    <div class="flex flex-col items-center gap-2">
                        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                        <span class="text-[8px] font-black text-white tracking-[0.2em] animate-pulse">Uploading...</span>
                    </div>
                </div>
            {/if}
        </div>
    {/each}

    <!-- Empty Padding -->
    {#if assets.length < 6}
        {#each Array(6 - assets.length) as _}
            <div class="aspect-square rounded-2xl border-2 border-dashed border-zinc-100 dark:border-zinc-800/50 opacity-20"></div>
        {/each}
    {/if}
</div>

<style>
    /* Premium micro-shadows and smoother rendering */
    div[role="button"]:hover {
        transform: translateY(-4px);
    }
</style>
