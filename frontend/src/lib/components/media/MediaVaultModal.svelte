<script lang="ts">
  import AssetStep from "$lib/components/admin/ui/content-factory/AssetStep.svelte";
  import FileManager from "$lib/components/media/FileManager.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { mediaStore } from "$lib/state/media.svelte";
  import { fade } from "svelte/transition";
  import { resolveMediaUrl } from "$lib/state/utils";

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

  import { untrack } from "svelte";

  let internalAssets = $state<(MediaAsset | string)[]>([]);

  $effect(() => {
    if (isOpen) {
      untrack(() => {
        internalAssets = assets ? [...assets] : [];
      });
    }
  });

  function onConfirm() {
    // CNS V80: Polymorphic Return. If parent passed strings, return strings. If objects, return objects.
    const isStringMode = assets && (assets.length === 0 || typeof assets[0] === 'string');

    if (isStringMode) {
      assets = internalAssets.map(a => {
        if (typeof a === 'string') return a;
        return a.file_path || a.url || '';
      });
    } else {
      // Normalize objects before returning
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
      activeTab = 'current'; // switch to show the result
    }
  }

  function switchTab(tab: 'current' | 'library' | 'ai') {
    activeTab = tab;
    if (tab === 'library') {
      mediaStore.isTrashMode = false;
      mediaStore.loadAssets(undefined, true);
    }
  }

  // Portal action
  function portal(node: HTMLElement) {
    document.body.appendChild(node);
    return {
      destroy() {
        node.remove();
      }
    };
  }

  // === Current post image helpers ===
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

{#if isOpen}
  <div use:portal class="fixed inset-0 bg-[#0a0c12]/98 backdrop-blur-2xl flex flex-col" style="z-index: 99998;" transition:fade={{ duration: 200 }}>

    {#if activeTab === 'current'}
      <!-- Current Post Images tab -->
      <div class="w-full h-full flex flex-col bg-[#0c0e14]">
        <!-- Toolbar -->
        <div class="px-4 py-3 border-b border-white/[0.06] flex items-center gap-4 bg-white/[0.03] backdrop-blur-xl shrink-0">
          <div class="flex bg-white/[0.05] p-0.5 rounded-lg border border-white/[0.06] shrink-0">
            <button 
              onclick={() => switchTab('current')}
              class="px-3 py-1.5 rounded-md text-[11px] font-semibold transition-all bg-indigo-500/90 text-white shadow-lg shadow-indigo-500/20"
            >
              Ảnh bài này ({internalAssets.length})
            </button>
            <button 
              onclick={() => switchTab('library')}
              class="px-3 py-1.5 rounded-md text-[11px] font-semibold transition-all text-white/30 hover:text-white/60 hover:bg-white/[0.05]"
            >
              Thư viện
            </button>
            <button 
              onclick={() => switchTab('ai')}
              class="px-3 py-1.5 rounded-md text-[11px] font-semibold transition-all text-white/30 hover:text-white/60 hover:bg-white/[0.05]"
            >
              Phát sinh AI
            </button>
          </div>
          <div class="flex-1"></div>
          <span class="text-[10px] text-white/20 hidden sm:block">{internalAssets.length} ảnh trong bài</span>
          <button 
            onclick={onConfirm}
            class="px-4 py-1.5 bg-indigo-500/90 hover:bg-indigo-400/90 text-white rounded-lg text-[11px] font-bold transition-all shadow-lg shadow-indigo-500/15"
          >
            Xác nhận
          </button>
          <button
            onclick={onClose}
            class="w-8 h-8 rounded-lg border border-white/[0.08] bg-white/[0.04] flex items-center justify-center hover:bg-red-500/20 hover:border-red-400/30 transition-all"
            aria-label="Đóng"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white/30"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <!-- Current images grid -->
        <div class="flex-1 overflow-y-auto p-6 bg-[#0a0c12]">
          {#if internalAssets.length === 0}
            <div class="flex flex-col items-center justify-center h-full gap-4 text-white/20">
              <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
              <p class="text-sm">Chưa có ảnh nào trong bài viết này</p>
              <button 
                onclick={() => switchTab('library')}
                class="px-4 py-2 bg-indigo-500/90 text-white rounded-lg text-xs font-bold hover:bg-indigo-400/90 transition-all"
              >
                Chọn ảnh từ thư viện
              </button>
            </div>
          {:else}
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {#each internalAssets as asset, index (index)}
                <div 
                  class="group relative aspect-square bg-white/[0.04] rounded-2xl overflow-hidden border border-white/[0.06] transition-all duration-300 hover:border-white/[0.15] hover:shadow-lg hover:shadow-black/20"
                  style="animation: fadeIn 0.4s ease-out {index * 0.05}s both;"
                >
                  <!-- Index Badge -->
                  <div class="absolute top-2 left-2 z-10 w-7 h-7 rounded-lg bg-black/60 backdrop-blur-md border border-white/10 flex items-center justify-center">
                    <span class="text-[11px] font-bold text-white/80">{index + 1}</span>
                  </div>

                  <!-- Avatar badge -->
                  {#if selectedAvatarUrl === getImageUrl(asset)}
                    <div class="absolute top-2 left-11 z-10 px-2 py-0.5 rounded-md bg-amber-500/90 backdrop-blur-md text-[9px] font-bold text-white uppercase">
                      Avatar
                    </div>
                  {/if}

                  <img 
                    src={getImageUrl(asset)}
                    alt={getImageLabel(asset)}
                    class="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-105"
                    loading="lazy"
                  />

                  <!-- Actions overlay -->
                  <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 flex flex-col justify-end p-3">
                    <p class="text-[10px] text-white/70 truncate mb-2 font-medium">{getImageLabel(asset)}</p>
                    <div class="flex items-center gap-1.5">
                      <!-- Move up -->
                      <button 
                        onclick={() => moveUp(index)}
                        class="p-1.5 rounded-lg bg-white/10 backdrop-blur-md hover:bg-white/20 transition-all {index === 0 ? 'opacity-30 pointer-events-none' : ''}"
                        title="Di chuyển lên"
                        aria-label="Di chuyển ảnh lên trước"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="m15 18-6-6 6-6"/></svg>
                      </button>
                      <!-- Move down -->
                      <button 
                        onclick={() => moveDown(index)}
                        class="p-1.5 rounded-lg bg-white/10 backdrop-blur-md hover:bg-white/20 transition-all {index >= internalAssets.length - 1 ? 'opacity-30 pointer-events-none' : ''}"
                        title="Di chuyển xuống"
                        aria-label="Di chuyển ảnh xuống sau"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="m9 18 6-6-6-6"/></svg>
                      </button>
                      <!-- Set as avatar -->
                      <button 
                        onclick={() => selectAsAvatar(getImageUrl(asset))}
                        class="p-1.5 rounded-lg backdrop-blur-md transition-all {selectedAvatarUrl === getImageUrl(asset) ? 'bg-amber-500/80' : 'bg-white/10 hover:bg-amber-500/40'}"
                        title="Đặt làm ảnh đại diện"
                        aria-label="Đặt làm ảnh đại diện"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                      </button>
                      <div class="flex-1"></div>
                      <!-- Remove -->
                      <button 
                        onclick={() => removeFromPost(index)}
                        class="p-1.5 rounded-lg bg-red-500/20 backdrop-blur-md hover:bg-red-500/60 transition-all"
                        title="Xoá khỏi bài"
                        aria-label="Xoá ảnh khỏi bài viết"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
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
      <!-- AI tab -->
      <div class="w-full h-full flex flex-col bg-[#0c0e14]">
        <div class="px-4 py-3 border-b border-white/[0.06] flex items-center gap-4 bg-white/[0.03] backdrop-blur-xl shrink-0">
          <div class="flex bg-white/[0.05] p-0.5 rounded-lg border border-white/[0.06] shrink-0">
            <button 
              onclick={() => switchTab('current')}
              class="px-3 py-1.5 rounded-md text-[11px] font-semibold transition-all text-white/30 hover:text-white/60 hover:bg-white/[0.05]"
            >
              Ảnh bài này ({internalAssets.length})
            </button>
            <button 
              onclick={() => switchTab('library')}
              class="px-3 py-1.5 rounded-md text-[11px] font-semibold transition-all text-white/30 hover:text-white/60 hover:bg-white/[0.05]"
            >
              Thư viện
            </button>
            <button 
              onclick={() => switchTab('ai')}
              class="px-3 py-1.5 rounded-md text-[11px] font-semibold transition-all bg-indigo-500/90 text-white shadow-lg shadow-indigo-500/20"
            >
              Phát sinh AI
            </button>
          </div>
          <div class="flex-1"></div>
          <button 
            onclick={onConfirm}
            class="px-4 py-1.5 bg-indigo-500/90 hover:bg-indigo-400/90 text-white rounded-lg text-[11px] font-bold transition-all shadow-lg shadow-indigo-500/15"
          >
            Xác nhận
          </button>
          <button
            onclick={onClose}
            class="w-8 h-8 rounded-lg border border-white/[0.08] bg-white/[0.04] flex items-center justify-center hover:bg-red-500/20 hover:border-red-400/30 transition-all"
            aria-label="Đóng"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white/30"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto">
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
          />
        </div>
      </div>

    {:else}
      <!-- Library tab -->
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
{/if}

<style>
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
</style>
