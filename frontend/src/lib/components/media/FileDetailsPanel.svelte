<script lang="ts">
    import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';
    import { fade, slide, scale } from 'svelte/transition';
    import { X, Trash2, RotateCcw, Edit3, Link, Wand2, Maximize2, ShieldCheck, Tag, Hash, Activity, Clock, HardDrive, Image as ImageIcon, Eye } from 'lucide-svelte';
    import type { MediaAsset } from '$lib/state/types';
    import { mediaStore } from '$lib/state/media.svelte';
    import { resolveMediaUrl, resolveThumbnailUrl, formatBytes, formatDate } from '$lib/state/utils';
    import ImagePreviewModal from '../admin/ui/ImagePreviewModal.svelte';

    interface Props {
        asset: MediaAsset | null;
        selectedAssetId: string | null;
        onDelete: (id: string) => void;
        onRestore: (id: string) => void;
        onSelect?: (assets: MediaAsset[]) => void;
        onQuickEdit: (action: string, params: Record<string, unknown> | null) => void;
        onPlayVideo?: (url: string) => void;
        mode?: 'manage' | 'pick';
    }

    let {
        asset,
        selectedAssetId = $bindable(),
        onDelete,
        onRestore,
        onSelect,
        onQuickEdit,
        onPlayVideo,
        mode = 'manage'
    } = $props<Props>();

    let isEditingAlt = $state(false);
    let editedAlt = $state('');
    let previewImageUrl = $state<string | null>(null);

    $effect(() => {
        if (asset) {
            editedAlt = asset.alt_text || '';
            isEditingAlt = false;
        }
    });

    function saveAlt() {
        if (!asset) return;
        mediaStore.bulkUpdateMetadata([{
            id: asset.id,
            metadata: { alt_text: editedAlt }
        }]);
        isEditingAlt = false;
    }
</script>

{#if asset}
    <ImagePreviewModal imageUrl={previewImageUrl} onClose={() => previewImageUrl = null} />
    <div
        class="w-80 border-l border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#0c0e14] flex flex-col h-full overflow-hidden shadow-[-20px_0_50px_rgba(0,0,0,0.1)] relative" style="z-index: {Z_INDEX_ADMIN.SIDEBAR_SUB};"
        transition:slide={{ axis: 'x', duration: 400 }}
    >
        <!-- Liquid Glow Accent -->
        <div class="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-[80px] pointer-events-none"></div>

        <!-- Header -->
        <div class="p-5 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/50 dark:bg-white/[0.02] backdrop-blur-md sticky top-0" style="z-index: {Z_INDEX_ADMIN.SURFACE};">
            <div class="flex flex-col">
                <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-400 dark:text-zinc-500">Resource Analyst</h3>
                <span class="text-[8px] font-bold text-blue-500 tracking-widest">{asset.id.slice(0, 16)}</span>
            </div>
            <button
                onclick={() => selectedAssetId = null}
                class="w-8 h-8 flex items-center justify-center hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded-xl transition-all text-zinc-400 hover:text-zinc-900 dark:hover:text-white"
            >
                <X size={18} />
            </button>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-8 no-scrollbar">
            <!-- Large Preview Stage -->
            <div class="relative aspect-square rounded-[2rem] overflow-hidden bg-zinc-100 dark:bg-[#080a0f] border border-zinc-200 dark:border-zinc-800 shadow-inner group cursor-zoom-in">
                {#if asset.mime_type?.startsWith('video/')}
                    <video
                        src={asset.file_path}
                        class="w-full h-full object-contain p-2 transition-transform duration-1000 group-hover:scale-110"
                        controls
                        playsinline
                        onerror={(e) => {
                            const video = e.target as HTMLVideoElement;
                            console.error('[FileManager] Video error:', {
                                error: video.error,
                                src: video.src,
                                networkState: video.networkState,
                                readyState: video.readyState
                            });
                            const parent = video.parentElement;
                            if (parent) parent.innerHTML = '<div class="w-full h-full flex items-center justify-center text-[10px] text-red-500">Video format not supported.</div>';
                        }}
                    ></video>
                {:else}
                    <img
                        src={resolveThumbnailUrl(asset)}
                        alt={asset.alt_text}
                        class="w-full h-full object-contain p-2 transition-transform duration-1000 group-hover:scale-110"
                    />
                {/if}
                <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="absolute top-4 right-4 flex gap-2 translate-y-2 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all">
                    <button
                        onclick={() => {
                            if (asset.mime_type?.startsWith('video/')) {
                                onPlayVideo?.(asset.file_path);
                            } else {
                                previewImageUrl = resolveThumbnailUrl(asset);
                            }
                        }}
                        class="p-2.5 bg-white/10 backdrop-blur-xl border border-white/20 rounded-xl text-white hover:bg-white/20 transition-all shadow-2xl"
                    >
                        <Maximize2 size={18} />
                    </button>
                </div>
            </div>

            <!-- Core Metadata -->
            <div class="space-y-5 px-1">
                <div class="flex flex-col gap-1.5">
                    <div class="flex items-center gap-2 opacity-40">
                        <Hash size={12} />
                        <span class="text-[9px] font-black text-zinc-500 uppercase tracking-widest leading-none">Original Filename</span>
                    </div>
                    <span class="text-[12px] font-bold text-zinc-800 dark:text-zinc-200 break-all leading-tight">{asset.filename || 'unknown_payload'}</span>
                </div>

                <div class="grid grid-cols-2 gap-6 pt-2">
                    <div class="flex flex-col gap-1.5">
                        <div class="flex items-center gap-2 opacity-40">
                            <HardDrive size={12} />
                            <span class="text-[9px] font-black text-zinc-500 uppercase tracking-widest leading-none">Space Usage</span>
                        </div>
                        <span class="text-[11px] font-mono font-black text-zinc-600 dark:text-zinc-400">{formatBytes(asset.file_size)}</span>
                    </div>
                    <div class="flex flex-col gap-1.5">
                        <div class="flex items-center gap-2 opacity-40">
                            <Clock size={12} />
                            <span class="text-[9px] font-black text-zinc-500 uppercase tracking-widest leading-none">Ingested At</span>
                        </div>
                        <span class="text-[10px] font-bold text-zinc-600 dark:text-zinc-400 leading-none">{formatDate(asset.created_at)}</span>
                    </div>
                </div>
            </div>

            <!-- AI Neural Analysis Block -->
            <div class="p-5 rounded-[2rem] bg-gradient-to-br from-blue-600/[0.03] to-indigo-600/[0.03] border border-blue-500/10 dark:border-blue-500/5 space-y-5 relative overflow-hidden">
                <div class="absolute top-[-10%] left-[-10%] w-20 h-20 bg-blue-500/5 blur-2xl rounded-full"></div>
                
                <div class="flex items-center justify-between relative" style="z-index: {Z_INDEX_ADMIN.SURFACE};">
                    <div class="flex items-center gap-2.5">
                        <div class="p-1.5 bg-blue-500 text-white rounded-lg shadow-lg shadow-blue-500/20">
                            <Wand2 size={12} strokeWidth={3} />
                        </div>
                        <span class="text-[10px] font-black text-zinc-800 dark:text-zinc-200 uppercase tracking-[0.2em]">Neural Intelligence</span>
                    </div>
                    {#if asset.media_metadata?.ai_sentiment}
                        <span class="px-2 py-0.5 rounded-full bg-blue-500 text-white text-[8px] font-black uppercase tracking-tighter shadow-lg shadow-blue-500/20">
                            {asset.media_metadata.ai_sentiment}
                        </span>
                    {/if}
                </div>

                <!-- Alt text (SEO) -->
                <div class="space-y-3 relative" style="z-index: {Z_INDEX_ADMIN.SURFACE};">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2 opacity-60">
                            <Tag size={12} class="text-blue-500" />
                            <span class="text-[9px] font-black text-zinc-500 uppercase tracking-widest leading-none">Semantic Alt-Text</span>
                        </div>
                        <button onclick={() => isEditingAlt = !isEditingAlt} class="p-1.5 hover:bg-blue-500/10 text-blue-500 rounded-lg transition-all">
                            <Edit3 size={14} />
                        </button>
                    </div>

                    {#if isEditingAlt}
                        <div class="flex flex-col gap-3" in:slide>
                            <textarea
                                bind:value={editedAlt}
                                class="w-full p-4 text-[11px] bg-white dark:bg-[#0c0e14] border-2 border-blue-500/20 rounded-2xl outline-none focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/5 min-h-[100px] transition-all no-scrollbar"
                                placeholder="Mô tả nội dung ảnh để tối ưu SEO..."
                            ></textarea>
                            <div class="flex justify-end gap-2">
                                <button onclick={() => isEditingAlt = false} class="px-4 py-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Huỷ</button>
                                <button onclick={saveAlt} class="px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-xl shadow-blue-500/20 active:scale-95 transition-all">Lưu kết quả</button>
                            </div>
                        </div>
                    {:else}
                        <div class="p-4 bg-white/40 dark:bg-black/20 rounded-2xl border border-white/5 shadow-inner">
                            <p class="text-[11px] text-zinc-600 dark:text-zinc-400 leading-relaxed font-medium italic">
                                "{asset.alt_text || 'Chưa có phân tích ngữ nghĩa. Sếp hãy bật AI Vision để em quét ảnh cho nhé.'}"
                            </p>
                        </div>
                    {/if}
                </div>

                <!-- AI Semantic Tags -->
                {#if asset.media_metadata?.ai_tags && asset.media_metadata.ai_tags.length > 0}
                    <div class="space-y-3 relative" style="z-index: {Z_INDEX_ADMIN.SURFACE};">
                        <div class="flex items-center gap-2 opacity-60">
                            <Activity size={12} class="text-indigo-500" />
                            <span class="text-[9px] font-black text-zinc-500 uppercase tracking-widest leading-none">Detected Tags</span>
                        </div>
                        <div class="flex flex-wrap gap-2">
                            {#each asset.media_metadata.ai_tags as tag}
                                <span class="px-2.5 py-1 bg-white dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 rounded-lg text-[9px] font-bold border border-zinc-200/50 dark:border-zinc-700/50 shadow-sm">
                                    #{tag}
                                </span>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>

            <!-- Logic Actions Control -->
            <div class="space-y-4 pt-6 mt-4 border-t border-zinc-100 dark:border-zinc-800 relative" style="z-index: {Z_INDEX_ADMIN.SURFACE};">
                {#if mode === 'pick' || onSelect}
                    <button 
                        onclick={() => onSelect?.([asset])} 
                        class="w-full py-5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-[1.5rem] text-[12px] font-black uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3 border border-white/10"
                    >
                        <Link size={16} />
                        {mode === 'pick' ? 'CHỌN TÀI NGUYÊN NÀY' : 'GẮN VÀO AGENT'}
                    </button>
                {/if}

                <div class="grid grid-cols-2 gap-3">
                    {#if mediaStore.isTrashMode}
                        <button onclick={() => onRestore(asset.id)} class="flex flex-col items-center justify-center gap-2 py-4 bg-green-500/5 text-green-500 rounded-2xl text-[9px] font-black uppercase border border-green-500/10 hover:bg-green-500 hover:text-white transition-all group">
                            <RotateCcw size={16} class="group-hover:rotate-[-45deg] transition-transform" />
                            RESTORE_VAL
                        </button>
                        <button onclick={() => onDelete(asset.id)} class="flex flex-col items-center justify-center gap-2 py-4 bg-red-500/5 text-red-500 rounded-2xl text-[9px] font-black uppercase border border-red-500/10 hover:bg-red-500 hover:text-white transition-all group">
                            <Trash2 size={16} class="group-hover:animate-bounce" />
                            PURGE_DATA
                        </button>
                    {:else}
                        <button onclick={() => onQuickEdit('optimize-seo', null)} class="flex flex-col items-center justify-center gap-2 py-4 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 rounded-2xl text-[9px] font-black uppercase hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all border border-transparent">
                            <ShieldCheck size={16} class="text-blue-500" />
                            SEO_SYNC
                        </button>
                        <button onclick={() => onQuickEdit('watermark', null)} class="flex flex-col items-center justify-center gap-2 py-4 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 rounded-2xl text-[9px] font-black uppercase hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all border border-transparent">
                            <ShieldCheck size={16} class="text-indigo-500" />
                            WATERMARK
                        </button>
                        <button onclick={() => onDelete(asset.id)} class="flex flex-col items-center justify-center gap-2 py-4 bg-zinc-100 dark:bg-zinc-800 text-zinc-400 rounded-2xl text-[9px] font-black uppercase hover:bg-red-500 hover:text-white transition-all border border-transparent">
                            <Trash2 size={16} class="text-red-500/60 group-hover:text-white" />
                            BIN_MOVE
                        </button>
                    {/if}
                </div>
            </div>
        </div>

        <!-- System Architecture Footnote -->
        <div class="p-5 bg-zinc-50 dark:bg-black/40 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
            <div class="flex items-center gap-2">
                <span class="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                <span class="text-[8px] font-mono text-zinc-400 uppercase tracking-widest">System Online</span>
            </div>
            <span class="text-[8px] font-mono text-zinc-300 dark:text-zinc-700">CORE v9.42_STABLE</span>
        </div>
    </div>
{:else}
    <div 
        class="w-80 border-l border-zinc-100 dark:border-zinc-800 flex flex-col items-center justify-center bg-white dark:bg-[#0c0e14] h-full p-8 text-center"
        transition:fade
    >
        <div class="relative mb-8">
            <div class="absolute inset-0 bg-blue-500/10 blur-[40px] rounded-full scale-150 animate-pulse"></div>
            <div class="relative w-20 h-20 bg-zinc-100 dark:bg-zinc-800 rounded-[2rem] flex items-center justify-center border border-zinc-200 dark:border-zinc-700 shadow-inner">
                <ImageIcon size={32} class="text-zinc-300 dark:text-zinc-700" />
            </div>
        </div>
        <h4 class="text-[11px] font-black text-zinc-800 dark:text-zinc-200 uppercase tracking-[0.4em] mb-2">Select Asset</h4>
        <p class="text-[9px] text-zinc-400 font-medium leading-relaxed max-w-[150px] uppercase tracking-wider">
            Waiting for target selection to initialize neural analysis pipeline...
        </p>
    </div>
{/if}

<style>
    /* Premium scrollbar for the details panel */
    .custom-scrollbar::-webkit-scrollbar {
        width: 3px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.05);
        border-radius: 10px;
    }
    :global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.05);
    }
</style>
