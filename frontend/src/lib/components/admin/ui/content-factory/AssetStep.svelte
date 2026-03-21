<script lang="ts">
  import { onMount, untrack } from "svelte";
  import {
    Image as ImageIcon,
    Link as LinkIcon,
    Plus,
    Trash2,
    Star,
    Check,
    RotateCcw,
    LayoutGrid,
    Upload,
    Library,
    X,
    Flame
  } from "lucide-svelte";
  import { fade, scale } from "svelte/transition";
  import { vuiController } from "$lib/vui";
  import FileManager from "$lib/components/media/FileManager.svelte";

  import type { MediaAsset } from "$lib/state/types";

  let {
    isProcessing,
    isExpanded,
    isStandalone = false,
    assets = $bindable(),
    reserve_assets = $bindable(),
    customImageUrl = $bindable(),
    selectedAvatarUrl = $bindable(),
    selectedAssetIndex = $bindable(),
    handleImageError,
    syncAssetChanges,
    deleteAsset,
    handleRetry,
    handleMouseMove,
  }: {
    isProcessing: boolean;
    isExpanded: boolean;
    isStandalone?: boolean;
    assets: (MediaAsset | string)[];
    reserve_assets: (MediaAsset | string)[];
    customImageUrl: string;
    selectedAvatarUrl: string | null;
    selectedAssetIndex: number;
    handleImageError: (url: string) => void;
    syncAssetChanges: (newIndex?: number) => void;
    deleteAsset?: (url: string) => void;
    handleRetry: () => void;
    handleMouseMove: (e: MouseEvent) => void;
  } = $props();

  import ImageGrid from "$lib/components/xohi/ImageGrid.svelte";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { extractIdFromUrl, resolveMediaUrl } from "$lib/state/utils";

  // V22: Voice Mutation Injection - Asset Management
  $effect(() => {
    const action = nanobot.commandAction;
    if (!action || action.consumed) return;

    if (action.entity === "media" || action.entity === "image") {
      // 1. Giao thức Thêm ảnh (Create)
      if (action.verb === "create" && action.args) {
        if (nanobot.consumeCommand(action.verb, action.entity)) {
          xohiImageStore.addImagesFromUrl(action.args);
          vuiController.speak("Dạ, em đã thêm ảnh theo yêu cầu của Sếp rồi ạ.");
        }
      }

      // 2. Giao thức Cắt ảnh AI (Edit/Smart Crop)
      // Args format: "index preset" e.g. "1 square"
      if (action.verb === "edit" && action.args) {
        if (nanobot.consumeCommand(action.verb, action.entity)) {
          const parts = action.args.split(" ");
          const index = parseInt(parts[0]) - 1; // User says 1, we use 0
          const preset = (parts[1] || "square") as
            | "square"
            | "landscape"
            | "portrait";

          const targetAsset = xohiImageStore.assets[index];
          if (targetAsset) {
            vuiController.speak(
              `Dạ, em đang cắt ảnh số ${index + 1} theo khung ${preset} cho Sếp đây ạ.`,
            );
            xohiImageStore.smartCrop(targetAsset.id, preset);
          } else {
            vuiController.speak(
              "Dạ Sếp ơi, em không tìm thấy ảnh đó để cắt ạ.",
            );
          }
        }
      }

      // 3. Giao thức Xóa ảnh (Delete)
      if (action.verb === "delete" && action.args) {
        if (nanobot.consumeCommand(action.verb, action.entity)) {
          const index = parseInt(action.args) - 1;
          const targetAsset = xohiImageStore.assets[index];
          if (targetAsset) {
            xohiImageStore.removeAsset(targetAsset.id);
            vuiController.speak(`Dạ, em đã xóa ảnh số ${index + 1} rồi ạ.`);
          }
        }
      }
    }
  });

  // CNS V74: Stable ID Generator to prevent dnd-action from crashing
  function generateStableId(url: string, index: number) {
    if (!url) return `temp_${index}`;
    // Simple hash of URL to keep it stable across re-renders
    let hash = 0;
    for (let i = 0; i < url.length; i++) {
      const char = url.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return `stable_${Math.abs(hash).toString(36)}_${index}`;
  }

  onMount(() => {
    // Rule R03: Bindable Safety
    if (assets === undefined) assets = [];
    if (reserve_assets === undefined) reserve_assets = [];
    if (customImageUrl === undefined) customImageUrl = "";
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
  });

  // Phase 15.3: Đồng bộ hóa dữ liệu từ Campaign vào Store khi Step được load
  $effect(() => {
    if (
      assets.length > 0 &&
      untrack(() => xohiImageStore.assets.length) === 0
    ) {
      // CNS V80: Using Store's built-in initAssets which handles normalization
      xohiImageStore.initAssets(assets);
    }
  });

  // Phase 15.3: Đồng bộ ngược lại khi Store thay đổi (Optimistic Sync)
  $effect(() => {
    const storeAssets = xohiImageStore.assets;
    // CNS V74: Shallow comparison with untrack to prevent infinite loops
    const currentAssets = untrack(() => assets);

    if (JSON.stringify(storeAssets) !== JSON.stringify(currentAssets)) {
      assets = storeAssets;
      const primaryIdx = storeAssets.findIndex((a) => a.is_primary);
      if (primaryIdx !== -1) {
        selectedAssetIndex = primaryIdx;
        selectedAvatarUrl = resolveMediaUrl(
          storeAssets[primaryIdx].file_path || storeAssets[primaryIdx].url || ''
        );
      } else if (storeAssets.length === 0) {
        selectedAssetIndex = 0;
        selectedAvatarUrl = null;
      }
      untrack(() => syncAssetChanges());
    }
  });
  // Phase 15.4: Media Library Integration
  let showLibrary = $state(false);
  let pendingPurgeAsset = $state<MediaAsset | null>(null);

  async function confirmPurge(asset: MediaAsset) {
    if (!asset.id) return;
    try {
      await xohiImageStore.removeAsset(asset.id, true);
      vuiController.speak("Đã xoá dứt điểm ảnh khỏi hệ thống.");
      pendingPurgeAsset = null;
    } catch (err) {
      console.error("[AssetStep] Purge failed", err);
      vuiController.speak("Dạ, có lỗi khi xoá dứt điểm ảnh ạ.");
    }
  }

  async function handleLibrarySelect(selectedAssets: MediaAsset[]) {
    let addCount = 0;
    for (const asset of selectedAssets) {
      if (!xohiImageStore.assets.find(a => a.id === asset.id)) {
        try {
          await xohiImageStore.addImagesFromUrl(asset.file_path || asset.url);
          addCount++;
        } catch (err) {
          console.error("[AssetStep] Library sync failed", err);
        }
      }
    }
    showLibrary = false;
    if (addCount > 0) {
      vuiController.speak(`Dạ, em đã lấy ${addCount} ảnh từ thư viện cho Sếp rồi ạ.`);
    } else {
      vuiController.speak("Dạ, các ảnh này đã có sẵn trong dự án rồi ạ.");
    }
  }
</script>


<div
  class="flex-1 flex flex-col space-y-6 pt-2 pb-8 p-4 md:p-6 max-w-[1400px] mx-auto w-full"
>
  <!-- Studio Label -->
  <div class="flex items-center gap-3 shrink-0 w-full px-1">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">
      XOHI ·
      <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">NEURAL STUDIO</span>
    </h5>
  </div>

  <!-- Tùy chọn hình ảnh: Clean & Professional -->
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 px-1">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center shadow-inner">
        <LayoutGrid size={24} class="text-blue-400/80" />
      </div>
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
          <!-- URL Entry Island -->
          <div
            class="flex bg-white/[0.04] p-1.5 rounded-2xl border border-white/5 transition-all h-12 group/input focus-within:border-blue-500/40 shadow-inner"
          >
            <div
              class="flex items-center justify-center pl-3 text-white/20 group-focus-within/input:text-blue-400 transition-colors"
            >
              <LinkIcon size={16} />
            </div>
            <input
              type="url"
              placeholder="Dán link ảnh (URL) tại đây..."
              bind:value={customImageUrl}
              onkeydown={(e) => {
                if (
                  e.key === "Enter" &&
                  customImageUrl.trim() &&
                  customImageUrl.startsWith("http")
                ) {
                  e.preventDefault();
                  async function runAdd() {
                    try {
                      await xohiImageStore.addImagesFromUrl(customImageUrl.trim());
                      customImageUrl = "";
                      vuiController.speak("Đã thêm ảnh.");
                    } catch (err: any) {
                      console.error("[AssetStep] Failed to add image", err);
                      vuiController.speak(`Dạ Sếp ơi, em không lấy được ảnh này rồi ạ. ${err.message || ''}`);
                    }
                  }
                  runAdd();
                }
              }}
              class="bg-transparent border-none outline-none text-[12px] text-white placeholder:text-white/20 px-4 w-36 transition-all focus:w-64 font-medium"
            />
          </div>

          <!-- Upload Island -->
          <label class="cursor-pointer group relative">
            <div
              class="relative bg-blue-600 hover:bg-blue-500 border border-white/5 px-6 py-3.5 rounded-2xl text-[10px] font-black text-white uppercase tracking-widest transition-all flex items-center gap-2 shadow-xl active:scale-95"
            >
              <Upload size={14} class="text-white/80" />
              Tải ảnh lên
            </div>
            <input
              type="file"
              multiple
              accept="image/*"
              class="hidden"
              onchange={(e) =>
                e.target.files && xohiImageStore.addImages(e.target.files)}
            />
          </label>
        </div>
      {/if}

      <!-- Library Link Island -->
      {#if !isStandalone}
        <button 
          onclick={() => showLibrary = true}
          class="bg-indigo-600 hover:bg-indigo-500 border border-white/5 px-6 py-3.5 rounded-2xl text-[10px] font-black text-white uppercase tracking-widest transition-all flex items-center gap-2 shadow-xl active:scale-95 group"
        >
          <Library size={14} class="text-white/80 group-hover:rotate-12 transition-transform" />
          Mở thư viện
        </button>
      {/if}

      <!-- Found Count Badge -->
      <div
        class="px-5 py-3.5 rounded-2xl bg-white/[0.04] border border-white/5 shadow-inner"
      >
        <span
          class="text-[9px] text-white/40 font-black uppercase tracking-[0.2em]"
          >Đã chọn // <span class="text-blue-400 ml-1"
            >{xohiImageStore.assets.length}</span
          ></span
        >
      </div>
    </div>
  </div>

  <div
    class="transition-all duration-700 min-h-[310px] relative {xohiImageStore.assets.length > 0 ? 'bg-gradient-to-br from-blue-500/10 via-white/[0.01] to-transparent rounded-[2rem] border border-white/10 shadow-2xl' : ''} mb-0"
  >
    <div class="p-2 md:p-3">
      <ImageGrid onPurge={(asset) => pendingPurgeAsset = asset} />
    </div>
  </div>

  <!-- Integrated Reserve Tray (Mini Island) -->
  {#if reserve_assets && reserve_assets.length > 0}
    <div class="mt-6 pt-3 border-t border-white/5" in:fade={{ duration: 600 }}>
      <div class="flex items-center justify-between mb-3 px-1">
        <div class="flex items-center gap-3">
          <div
            class="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.6)]"
          ></div>
          <span
            class="text-[10px] text-amber-500/80 font-black tracking-[0.4em] uppercase"
            >HÌNH ẢNH DỰ PHÒNG</span
          >
        </div>
        <div
          class="text-[9px] text-white/10 font-bold uppercase tracking-widest"
        >
          {reserve_assets.length} items available
        </div>
      </div>

      <div
        class="flex gap-4 overflow-x-auto overflow-y-hidden pb-4 pt-1 px-1 -mx-1 custom-scrollbar-horizontal snap-x snap-mandatory"
      >
        {#each reserve_assets as url, i (url)}
          <div
            class="flex-shrink-0 w-[80px] md:w-[100px] lg:w-[120px] snap-start"
          >
            <div
              role="button"
              tabindex="0"
              onkeydown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  vuiController.speak("Đã thêm vào bộ sưu tập.");
                  xohiImageStore.addImagesFromUrl(url as string);
                  reserve_assets = reserve_assets.filter((_, idx) => idx !== i);
                }
              }}
              onclick={() => {
                // Add Logic: Move from reserve to primary collection
                vuiController.speak("Đã thêm vào bộ sưu tập.");
                xohiImageStore.addImagesFromUrl(url as string);
                reserve_assets = reserve_assets.filter((_, idx) => idx !== i);
              }}
              class="group/reserve relative aspect-square rounded-2xl overflow-hidden border border-white/10 bg-white/[0.02] hover:border-amber-500/50 hover:bg-white/[0.05] hover:scale-105 transition-all duration-500 cursor-pointer shadow-lg"
            >
              <img
                src={resolveMediaUrl(typeof url === 'string' ? url : (url.file_path || url.url || ''))}
                alt="Reserve {i}"
                class="w-full h-full object-cover opacity-60 hover:opacity-100 grayscale hover:grayscale-0 transition-all duration-700 blur-[0.5px] hover:blur-0"
              />
              <div
                class="absolute inset-0 bg-amber-500/10 opacity-0 group-hover/reserve:opacity-100 flex items-center justify-center transition-opacity"
              >
                <Plus size={20} class="text-white drop-shadow-lg" />
              </div>

              <!-- Delete button for reserve assets -->
              <button
                class="absolute top-2 right-2 p-1.5 rounded-full bg-black/60 text-white/60 hover:bg-red-500 hover:text-white opacity-0 group-hover/reserve:opacity-100 transition-all z-20 cursor-pointer"
                onclick={async (e) => {
                  e.stopPropagation();
                  try {
                    reserve_assets = reserve_assets.filter((_, idx) => idx !== i);
                    
                    const { tick } = await import("svelte");
                    await tick(); 
                    
                    syncAssetChanges();
                    vuiController.speak("Đã xóa khỏi kho dự phòng.");
                  } catch (err) {
                    console.error("[AssetStep] Delete failed", err);
                  }
                }}
              >
                <Trash2 size={12} />
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<!-- CNS V78: Media Library Modal (Full Manager Picker) -->
{#if showLibrary}
  <div 
    class="fixed inset-0 z-[60] flex items-center justify-center p-4 md:p-8 bg-slate-950/80 backdrop-blur-2xl"
    transition:fade
  >
    <div 
      class="relative w-full h-full max-w-7xl bg-[#0a0c10] rounded-[2.5rem] border border-white/10 shadow-[0_40px_100px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden"
      transition:scale={{ duration: 500, start: 0.95 }}
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-8 py-6 border-b border-white/5 bg-white/[0.02]">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
            <Library class="text-indigo-400" size={24} />
          </div>
          <div>
            <h2 class="text-xl font-black text-white uppercase tracking-widest leading-none">THƯ VIỆN HỆ THỐNG</h2>
            <p class="text-[9px] text-white/30 font-bold uppercase tracking-[0.3em] mt-1.5 flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></span>
              Kho ảnh hệ thống // Chế độ chọn ảnh
            </p>
          </div>
        </div>
        <button 
          onclick={() => showLibrary = false}
          class="p-4 bg-white/5 hover:bg-red-500/20 text-white/20 hover:text-red-400 rounded-2xl transition-all border border-white/5 hover:border-red-500/30 group"
          title="Đóng thư viện"
        >
          <X size={20} class="group-hover:rotate-90 transition-transform" />
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-hidden relative">
        <FileManager 
          mode="pick" 
          onSelect={handleLibrarySelect} 
        />
      </div>

      <!-- Footer HUD -->
      <div class="px-8 py-4 bg-black/40 border-t border-white/5 flex items-center justify-between">
        <div class="flex items-center gap-4 text-[7px] font-mono text-white/10 uppercase tracking-[0.3em]">
          <span>XOHI PROTOCOL V.03-ALPHA</span>
          <span class="w-1 h-1 rounded-full bg-white/10"></span>
          <span>EST_CONN: STABLE</span>
        </div>
        <button 
          onclick={() => showLibrary = false}
          class="px-8 py-3 bg-white/5 hover:bg-white/10 text-white/40 hover:text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border border-white/10 active:scale-95"
        >
          Đóng thư viện
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- CNS V78.2: Hard Delete (Purge) Confirmation Modal -->
{#if pendingPurgeAsset}
  <div 
    class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-red-950/40 backdrop-blur-md"
    transition:fade
  >
    <div 
      class="w-full max-w-sm bg-slate-900 border border-red-500/30 rounded-[2rem] p-8 shadow-[0_20px_60px_rgba(239,68,68,0.2)]"
      transition:scale
    >
      <div class="flex flex-col items-center text-center gap-6">
        <div class="w-20 h-20 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500 animate-pulse">
          <Flame size={32} />
        </div>
        
        <div>
          <h3 class="text-lg font-black text-white uppercase tracking-widest leading-none">XÁCH NHẬN XOÁ VĨNH VIỄN?</h3>
          <p class="text-[10px] text-red-400 font-bold uppercase tracking-widest mt-2">Ảnh này sẽ bị xóa khỏi hệ thống, không thể hoàn tác!</p>
        </div>

        <div class="w-24 h-24 rounded-2xl border border-white/5 overflow-hidden shadow-inner">
          <img src={resolveMediaUrl(pendingPurgeAsset.file_path || pendingPurgeAsset.url)} alt="Purge Preview" class="w-full h-full object-cover" />
        </div>

        <p class="text-[10px] text-white/40 font-medium leading-relaxed">
          Hành động này không thể hoàn tác. Ảnh sẽ bị xóa vĩnh viễn khỏi máy chủ của Sếp.
        </p>

        <div class="grid grid-cols-2 gap-3 w-full">
          <button 
            onclick={() => pendingPurgeAsset = null}
            class="py-3 px-4 bg-white/5 hover:bg-white/10 text-white/60 font-black text-[10px] uppercase tracking-widest rounded-xl transition-all border border-white/5"
          >
            Hủy bỏ
          </button>
          <button 
            onclick={() => { if (pendingPurgeAsset) confirmPurge(pendingPurgeAsset); }}
            class="py-3 px-4 bg-red-600 hover:bg-red-500 text-white font-black text-[10px] uppercase tracking-widest rounded-xl transition-all shadow-[0_10px_30px_rgba(220,38,38,0.4)] active:scale-95"
          >
            XÁC NHẬN XOÁ
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

{#if assets.length === 0 && !isProcessing && !isStandalone}
  <div
    class="flex flex-col items-center justify-center py-12 text-center gap-4"
    in:fade={{ duration: 300 }}
  >
    <div
      class="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center"
    >
      <ImageIcon size={28} class="text-white/20" />
    </div>
    <div>
      <p class="text-sm font-bold text-white/60">Không tìm thấy ảnh phù hợp</p>
      <p class="text-xs text-white/30 mt-1">
        Quota Google Search có thể đã hết, hoặc từ khóa quá ít phổ biến.
      </p>
    </div>
    <button
      onclick={handleRetry}
      class="flex items-center gap-2 px-5 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold transition-all"
    >
      <RotateCcw size={14} />
      Tìm lại ảnh
    </button>
  </div>
{/if}

<style>
  .neural-grid-glow {
    background: radial-gradient(1000px circle at var(--x) var(--y), rgba(59, 130, 246, 0.08), transparent 40%);
  }

  /* Subtle Custom Scrollbar - Vertical */
  .custom-scrollbar::-webkit-scrollbar {
    width: 3px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.1);
    border-radius: 10px;
  }
  .custom-scrollbar:hover::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.3);
  }

  /* Subtle Custom Scrollbar - Horizontal */
  .custom-scrollbar-horizontal::-webkit-scrollbar {
    height: 3px;
  }
  .custom-scrollbar-horizontal::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar-horizontal::-webkit-scrollbar-thumb {
    background: rgba(245, 158, 11, 0.1);
    border-radius: 10px;
  }
  .custom-scrollbar-horizontal:hover::-webkit-scrollbar-thumb {
    background: rgba(245, 158, 11, 0.3);
  }
</style>
