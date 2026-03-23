<script lang="ts">
  import AssetStep from "$lib/components/admin/ui/content-factory/AssetStep.svelte";
  import FileManager from "$lib/components/media/FileManager.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { mediaStore } from "$lib/state/media.svelte";
  import { resolveMediaUrl } from "$lib/state/utils";
  import MissionControlShell from "$lib/components/admin/ui/MissionControlShell.svelte";
  import ImagePlus from "lucide-svelte/icons/image-plus";
  import { Z_INDEX } from "$lib/core/constants/zIndex";

  let {
    isOpen,
    onClose,
    campaignId,
    assets = $bindable(),
    reserve_assets = $bindable(),
    selectedAvatarUrl = $bindable(),
    selectedAssetIndex = $bindable(),
    onSelect
  }: {
    isOpen: boolean;
    onClose: () => void;
    campaignId?: string;
    assets?: (MediaAsset | string)[];
    reserve_assets?: (MediaAsset | string)[];
    selectedAvatarUrl?: string | null;
    selectedAssetIndex?: number;
    onSelect?: (url: string) => void;
  } = $props();

  import { untrack, onMount } from "svelte";

  let internalAssets = $state<(MediaAsset | string)[]>([]);

  onMount(() => {
    if (assets === undefined) assets = [];
    if (reserve_assets === undefined) reserve_assets = [];
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
  });

  $effect(() => {
    if (isOpen) {
      untrack(() => {
        internalAssets = assets ? [...assets] : [];
      });
    }
  });

  function onConfirm() {
    const isStringMode = assets && (assets.length === 0 || typeof assets[0] === 'string');

    if (isStringMode) {
      assets = internalAssets.map(a => {
        if (typeof a === 'string') return a;
        return a.file_path || a.url || '';
      });
    } else {
      assets = internalAssets.map(a => {
        if (typeof a === 'string') {
          return {
            id: `stable_${Math.random().toString(36).slice(2)}`,
            file_path: resolveMediaUrl(a),
            is_primary: false,
            order_index: 0
          } as MediaAsset;
        }
        return { ...a, file_path: resolveMediaUrl(a.file_path || a.url) };
      });
    }
    onClose();
  }

  let customImageUrl = $state("");
  let isProcessing = $state(false);

  function handleImageError(url: string) { console.error("Image error:", url); }
  function syncAssetChanges() {}
  function deleteAsset(url: string) {
    internalAssets = internalAssets.filter(a => (typeof a === 'string' ? a : a.file_path) !== url);
  }
  function handleRetry() {}
  function handleMouseMove(e: MouseEvent) {}

  let activeTab = $state<'current' | 'library' | 'ai'>('current');

  function handleLibrarySelect(asset: MediaAsset | MediaAsset[]) {
    const assetsArr = Array.isArray(asset) ? asset : [asset];
    
    if (onSelect) {
      const first = assetsArr[0];
      const url = first.file_path || first.url || '';
      if (url) {
        onSelect(url);
        onClose?.();
        return;
      }
    }

    let changed = false;
    assetsArr.forEach(a => {
      const url = a.file_path || a.url || '';
      if (url && !internalAssets.find(existing => (typeof existing === 'string' ? existing : existing.file_path) === url)) {
        internalAssets = [...internalAssets, url];
        changed = true;
      }
    });
    if (changed) {
      activeTab = 'current';
    }
  }

  function switchTab(tab: 'current' | 'library' | 'ai') {
    activeTab = tab;
    if (tab === 'library') {
      mediaStore.isTrashMode = false;
      mediaStore.loadAssets(undefined, true);
    }
  }

  function getImageUrl(asset: MediaAsset | string): string {
    const url = typeof asset === 'string' ? asset : (asset.file_path || asset.url || '');
    return resolveMediaUrl(url);
  }

  function getImageLabel(asset: MediaAsset | string): string {
    if (typeof asset === 'string') {
      const parts = asset.split('/');
      const last = parts[parts.length - 1] || 'image';
      return last.split('?')[0];
    }
    return asset.filename || asset.alt_text || 'image';
  }

  function removeFromPost(index: number) {
    internalAssets = internalAssets.filter((_, i) => i !== index);
  }

  function moveUp(index: number) {
    if (index === 0) return;
    const arr = [...internalAssets];
    [arr[index - 1], arr[index]] = [arr[index], arr[index - 1]];
    internalAssets = arr;
  }

  function moveDown(index: number) {
    if (index >= internalAssets.length - 1) return;
    const arr = [...internalAssets];
    [arr[index], arr[index + 1]] = [arr[index + 1], arr[index]];
    internalAssets = arr;
  }

  function selectAsAvatar(url: string) {
    selectedAvatarUrl = url;
  }
</script>

<MissionControlShell
  title="MEDIA_VAULT_INTERFACE"
  protocol="GHOST_v12"
  isOpen={isOpen}
  onClose={onClose}
  headerIcon={ImagePlus}
  fullScreen={true}
  zIndex={Z_INDEX.MEDIA_OVERLAY}
>
  <div class="w-full h-full flex flex-col">
    {#if activeTab === 'current'}
      <div class="w-full h-full flex flex-col">
        <div class="px-6 py-3 border-b border-white/[0.06] flex items-center justify-between bg-white/[0.02] shrink-0">
          <div class="flex bg-white/[0.05] p-0.5 rounded-lg border border-white/[0.06] shrink-0">
            <button 
              onclick={() => switchTab('current')}
              class="px-4 py-1.5 rounded-md text-[10px] font-black uppercase tracking-wider transition-all bg-cyan-500 text-black shadow-lg shadow-cyan-500/20"
            >
              Ảnh bài này ({internalAssets.length})
            </button>
            <button 
              onclick={() => switchTab('library')}
              class="px-4 py-1.5 rounded-md text-[10px] font-black uppercase tracking-wider transition-all text-white/30 hover:text-white/60 hover:bg-white/[0.05]"
            >
              Thư viện
            </button>
            <button 
              onclick={() => switchTab('ai')}
              class="px-4 py-1.5 rounded-md text-[10px] font-black uppercase tracking-wider transition-all text-white/30 hover:text-white/60 hover:bg-white/[0.05]"
            >
              Phát sinh AI
            </button>
          </div>
          
          <div class="flex items-center gap-4">
            <span class="text-[9px] font-mono text-white/20 uppercase tracking-[0.3em]">{internalAssets.length} items sync_locked</span>
            <button 
              onclick={onConfirm}
              class="px-8 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-black rounded-lg text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all cursor-pointer"
            >
              Xác nhận
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-8 scrollbar-mission bg-transparent">
          {#if internalAssets.length === 0}
            <div class="flex flex-col items-center justify-center h-full gap-6 text-white/10">
              <div class="w-20 h-20 rounded-full border border-dashed border-white/20 flex items-center justify-center">
                <ImagePlus size={32} class="opacity-20" />
              </div>
              <p class="text-[10px] font-mono uppercase tracking-[0.3em]">No local assets detected for this protocol</p>
              <button 
                onclick={() => switchTab('library')}
                class="px-6 py-2 border border-cyan-500/30 text-cyan-400 rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-cyan-500 hover:text-black transition-all"
              >
                OPEN_INTELLIGENCE_VAULT
              </button>
            </div>
          {:else}
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-6">
              {#each internalAssets as asset, index (index)}
                <div 
                  class="group relative aspect-square bg-[#0f111a] rounded-xl overflow-hidden border border-white/[0.06] transition-all duration-500 hover:border-cyan-500/40 hover:shadow-[0_0_30px_rgba(0,243,255,0.1)]"
                  style="animation: fadeIn 0.4s ease-out {index * 0.05}s both;"
                >
                  <div class="absolute top-2 left-2 z-20 w-6 h-6 rounded bg-black/80 backdrop-blur-md border border-white/10 flex items-center justify-center">
                    <span class="text-[10px] font-mono font-bold text-cyan-400">{index + 1}</span>
                  </div>

                  {#if selectedAvatarUrl === getImageUrl(asset)}
                    <div class="absolute top-2 right-2 z-20 px-2 py-0.5 rounded bg-cyan-500 text-black text-[9px] font-black uppercase tracking-tighter">
                      PRIMARY
                    </div>
                  {/if}

                  <img 
                    src={getImageUrl(asset)}
                    alt={getImageLabel(asset)}
                    class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110 opacity-80 group-hover:opacity-100"
                    loading="lazy"
                  />

                  <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end p-4">
                    <p class="text-[9px] font-mono text-cyan-400/80 truncate mb-3 uppercase tracking-wider">{getImageLabel(asset)}</p>
                    
                    {#if onSelect}
                      <button 
                        onclick={() => { onSelect?.(getImageUrl(asset)); onClose?.(); }}
                        class="mb-3 w-full py-2 bg-cyan-500 text-black rounded-lg text-[10px] font-black uppercase tracking-widest shadow-lg shadow-cyan-500/20 transition-all active:scale-95 cursor-pointer"
                      >
                        ATTACH_ASSET
                      </button>
                    {/if}

                    <div class="flex items-center gap-2">
                      <button 
                        onclick={() => moveUp(index)}
                        class="p-2 rounded bg-white/5 hover:bg-cyan-500/20 border border-white/5 hover:border-cyan-500/30 transition-all group/btn {index === 0 ? 'opacity-20 pointer-events-none' : 'cursor-pointer'}"
                        title="Move Up"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="text-white group-hover/btn:text-cyan-400"><path d="m15 18-6-6 6-6"/></svg>
                      </button>
                      <button 
                        onclick={() => moveDown(index)}
                        class="p-2 rounded bg-white/5 hover:bg-cyan-500/20 border border-white/5 hover:border-cyan-500/30 transition-all group/btn {index >= internalAssets.length - 1 ? 'opacity-20 pointer-events-none' : 'cursor-pointer'}"
                        title="Move Down"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="text-white group-hover/btn:text-cyan-400"><path d="m9 18 6-6-6-6"/></svg>
                      </button>
                      <button 
                        onclick={() => selectAsAvatar(getImageUrl(asset))}
                        class="p-2 rounded border transition-all {selectedAvatarUrl === getImageUrl(asset) ? 'bg-cyan-500 border-cyan-400 text-black' : 'bg-white/5 border-white/5 hover:border-cyan-500/30 text-white/40 hover:text-cyan-400 cursor-pointer'}"
                        title="Set Primary"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                      </button>
                      <div class="flex-1"></div>
                      <button 
                        onclick={() => removeFromPost(index)}
                        class="p-2 rounded bg-red-500/10 hover:bg-red-500 text-red-400 hover:text-black border border-red-500/20 transition-all cursor-pointer"
                        title="Discard"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                      </button>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>

    {:else if activeTab === 'ai'}
      <div class="w-full h-full flex flex-col bg-transparent">
        <div class="px-6 py-3 border-b border-white/[0.06] flex items-center justify-between bg-white/[0.02] shrink-0">
          <div class="flex bg-white/[0.05] p-0.5 rounded-lg border border-white/[0.06] shrink-0">
            <button 
              onclick={() => switchTab('current')}
              class="px-4 py-1.5 rounded-md text-[10px] font-black uppercase tracking-wider transition-all text-white/30 hover:text-white/60 hover:bg-white/[0.05]"
            >
              Ảnh bài này ({internalAssets.length})
            </button>
            <button 
              onclick={() => switchTab('library')}
              class="px-4 py-1.5 rounded-md text-[10px] font-black uppercase tracking-wider transition-all text-white/30 hover:text-white/60 hover:bg-white/[0.05]"
            >
              Thư viện
            </button>
            <button 
              onclick={() => switchTab('ai')}
              class="px-4 py-1.5 rounded-md text-[10px] font-black uppercase tracking-wider transition-all bg-cyan-500 text-black shadow-lg shadow-cyan-500/20"
            >
              Phát sinh AI
            </button>
          </div>
          <div class="flex items-center gap-4">
            <button 
              onclick={onConfirm}
              class="px-8 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-black rounded-lg text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all cursor-pointer"
            >
              Xác nhận
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto scrollbar-mission">
          <AssetStep
            {isProcessing}
            isExpanded={true}
            isStandalone={true}
            bind:assets={internalAssets}
            bind:reserve_assets
            bind:customImageUrl
            bind:selectedAvatarUrl
            bind:selectedAssetIndex={selectedAssetIndex}
            {handleImageError}
            {syncAssetChanges}
            {deleteAsset}
            {handleRetry}
            {handleMouseMove}
            {onSelect}
          />
        </div>
      </div>

    {:else}
      <FileManager 
        mode="pick" 
        standalone={true}
        campaignId={undefined}
        onSelect={handleLibrarySelect}
        pickTabActive={activeTab}
        onPickTabChange={switchTab}
        onPickConfirm={onConfirm}
        onPickClose={onClose}
      />
    {/if}
  </div>
</MissionControlShell>

<style>
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px) scale(0.95); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
</style>
