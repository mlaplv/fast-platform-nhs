<script lang="ts">
  import { onMount } from "svelte";
  import Image from "@lucide/svelte/icons/image";
  import ImageIcon from "@lucide/svelte/icons/image";
  import LinkIcon from "@lucide/svelte/icons/link";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import LayoutGrid from "@lucide/svelte/icons/layout-grid";
  import Upload from "@lucide/svelte/icons/upload";
  import Library from "@lucide/svelte/icons/library";
  import { fade } from "svelte/transition";
  import { vuiController } from "$lib/vui";
  import ImageGrid from "$lib/components/xohi/ImageGrid.svelte";
  import AssetModals from "./AssetModals.svelte";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import { resolveMediaUrl } from "$lib/state/utils";
  import { createAssetController } from "$lib/state/xohiAsset.svelte";
  import type { MediaAsset } from "$lib/state/types";

  let {
    campaign_id, isProcessing, isStandalone = false, isExpanded = false, assets = $bindable(), reserve_assets = $bindable(),
    customImageUrl = $bindable(), selectedAvatarUrl = $bindable(), selectedAssetIndex = $bindable(),
    syncAssetChanges, handleRetry, onSelect
  }: {
    campaign_id: string; isProcessing: boolean; isStandalone?: boolean; isExpanded?: boolean; assets: (MediaAsset | string)[];
    reserve_assets: (MediaAsset | string)[]; customImageUrl: string;
    selectedAvatarUrl: string | null; selectedAssetIndex: number;
    syncAssetChanges: (step: number, newIndex?: number) => void; handleRetry: () => void;
    onSelect?: (url: string) => void;
  } = $props();

  const ctrl = createAssetController({
    get id() { return campaign_id; },
    getAssets: () => assets, setAssets: (v) => { assets = v; },
    getReserveAssets: () => reserve_assets, setReserveAssets: (v) => { reserve_assets = v; },
    getIsProcessing: () => isProcessing,
    setSelectedAvatarUrl: (v) => { selectedAvatarUrl = v; },
    setSelectedAssetIndex: (v) => { selectedAssetIndex = v; },
    syncAssetChanges: () => syncAssetChanges
  });

  onMount(() => {
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
  });

  async function handleAddFromUrl() {
    if (!customImageUrl.trim() || !customImageUrl.startsWith("http")) return;
    try {
      await xohiImageStore.addImagesFromUrl(customImageUrl.trim());
      customImageUrl = "";
      vuiController.speak("Đã thêm ảnh.");
    } catch (err: unknown) {
      vuiController.speak(`Dạ Sếp ơi, em không lấy được ảnh này rồi ạ. ${err instanceof Error ? err.message : String(err)}`);
    }
  }
</script>

<div class="flex-1 flex flex-col space-y-6 pt-2 pb-8 p-4 md:p-6 max-w-[1400px] mx-auto w-full">
  <div class="flex items-center gap-3 shrink-0 w-full px-1">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">NEURAL XOHI · <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">STUDIO</span></h5>
  </div>

  <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 px-1">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center shadow-inner"><LayoutGrid size={24} class="text-blue-400/80" /></div>
      {#if !isStandalone}
        <div class="flex flex-col">
          <h3 class="text-lg font-bold text-white tracking-tight uppercase">TÙY CHỌN HÌNH ẢNH</h3>
          <p class="text-[9px] text-white/30 font-bold uppercase tracking-[0.3em]">AI Generator & Web Upload</p>
        </div>
      {/if}
    </div>

    <div class="flex flex-wrap items-center gap-3">
      {#if !isProcessing}
        <div class="flex items-center gap-3">
          <div class="flex bg-white/[0.04] p-1.5 rounded-2xl border border-white/5 transition-all h-12 group/input focus-within:border-blue-500/40 shadow-inner">
            <div class="flex items-center justify-center pl-3 text-white/20 group-focus-within/input:text-blue-400 transition-colors"><LinkIcon size={16} /></div>
            <input type="url" placeholder="Dán link ảnh (URL) tại đây..." bind:value={customImageUrl} onkeydown={(e) => e.key === "Enter" && handleAddFromUrl()} class="bg-transparent border-none outline-none text-[12px] text-white placeholder:text-white/20 px-4 w-36 transition-all focus:w-64 font-medium" />
          </div>
          <label class="cursor-pointer group relative">
            <div class="relative bg-blue-600 hover:bg-blue-500 border border-white/5 px-6 py-3.5 rounded-2xl text-[10px] font-black text-white uppercase tracking-widest transition-all flex items-center gap-2 shadow-xl active:scale-95"><Upload size={14} class="text-white/80" /> Tải ảnh lên</div>
            <input type="file" multiple accept="image/*" class="hidden" onchange={(e) => e.target.files && xohiImageStore.addImages(e.target.files)} />
          </label>
        </div>
      {/if}
      {#if !isStandalone}
        <button onclick={() => ctrl.showLibrary = true} class="bg-indigo-600 hover:bg-indigo-500 border border-white/5 px-6 py-3.5 rounded-2xl text-[10px] font-black text-white uppercase tracking-widest transition-all flex items-center gap-2 shadow-xl active:scale-95 group"><Library size={14} class="text-white/80 group-hover:rotate-12 transition-transform" /> Mở thư viện</button>
      {/if}
      <div class="px-5 py-3.5 rounded-2xl bg-white/[0.04] border border-white/5 shadow-inner"><span class="text-[9px] text-white/40 font-black uppercase tracking-[0.2em]">Đã chọn // <span class="text-blue-400 ml-1">{xohiImageStore.assets.length}</span></span></div>
    </div>
  </div>

  <div class="transition-all duration-700 min-h-[310px] relative {xohiImageStore.assets.length > 0 ? 'bg-gradient-to-br from-blue-500/10 via-white/[0.01] to-transparent rounded-[2rem] border border-white/10 shadow-2xl' : ''} mb-0">
    <div class="p-2 md:p-3">
        <ImageGrid 
          bind:items={assets} 
          {campaign_id} 
          {isProcessing} 
          {isExpanded}
          onRemove={(asset) => ctrl.confirmPurge(asset)} 
          {handleRetry} 
          {onSelect} 
        />
    </div>
  </div>

  {#if reserve_assets && reserve_assets.length > 0}
    <div class="mt-6 pt-3 border-t border-white/5" in:fade={{ duration: 600 }}>
      <div class="flex items-center justify-between mb-3 px-1">
        <div class="flex items-center gap-3">
          <div class="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.6)]"></div>
          <span class="text-[10px] text-amber-500/80 font-black tracking-[0.4em] uppercase">HÌNH ẢNH DỰ PHÒNG</span>
        </div>
        <div class="text-[9px] text-white/10 font-bold uppercase tracking-widest">{reserve_assets.length} items available</div>
      </div>
      <div class="flex gap-4 overflow-x-auto overflow-y-hidden pb-4 pt-1 px-1 -mx-1 custom-scrollbar-horizontal snap-x snap-mandatory">
        {#each reserve_assets as item, i (typeof item === 'string' ? item : (item.id || i))}
          {@const url = typeof item === 'string' ? item : (item.file_path || item.url || '')}
          <div class="flex-shrink-0 w-[80px] md:w-[100px] lg:w-[120px] snap-start">
            <div role="button" tabindex="0" onkeydown={(e) => (e.key === "Enter" || e.key === " ") && ctrl.addFromReserve(url, i)} onclick={() => ctrl.addFromReserve(url, i)} class="group/reserve relative aspect-square rounded-2xl overflow-hidden border border-white/10 bg-white/[0.02] hover:border-amber-500/50 hover:bg-white/[0.05] hover:scale-105 transition-all duration-500 cursor-pointer shadow-lg">
              <img src={resolveMediaUrl(url)} alt="Reserve {i}" class="w-full h-full object-cover opacity-60 hover:opacity-100 grayscale hover:grayscale-0 transition-all duration-700 blur-[0.5px] hover:blur-0" />
              <div class="absolute inset-0 bg-amber-500/10 opacity-0 group-hover/reserve:opacity-100 flex items-center justify-center transition-opacity"><Plus size={20} class="text-white drop-shadow-lg" /></div>
              <button class="absolute top-2 right-2 p-1.5 rounded-full bg-black/60 text-white/60 hover:bg-red-500 hover:text-white opacity-0 group-hover/reserve:opacity-100 transition-all z-20 cursor-pointer" onclick={(e) => { e.stopPropagation(); ctrl.removeFromReserve(i); }}><Trash2 size={12} /></button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<AssetModals bind:showLibrary={ctrl.showLibrary} bind:pendingPurgeAsset={ctrl.pendingPurgeAsset} onLibrarySelect={ctrl.handleLibrarySelect} onCloseLibrary={() => ctrl.showLibrary = false} onClosePurge={() => ctrl.pendingPurgeAsset = null} onConfirmPurge={ctrl.confirmPurge} />

<style>
  .custom-scrollbar-horizontal::-webkit-scrollbar { height: 3px; }
  .custom-scrollbar-horizontal::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar-horizontal::-webkit-scrollbar-thumb { background: rgba(245, 158, 11, 0.1); border-radius: 10px; }
  .custom-scrollbar-horizontal:hover::-webkit-scrollbar-thumb { background: rgba(245, 158, 11, 0.3); }
</style>
