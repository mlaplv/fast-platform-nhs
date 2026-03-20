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
  } from "lucide-svelte";
  import { fade, scale } from "svelte/transition";
  import { vuiController } from "$lib/vui";

  import type { MediaAsset } from "$lib/state/types";

  let {
    isProcessing,
    isExpanded,
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
  import { extractIdFromUrl } from "$lib/state/utils";

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
      const formattedAssets = assets.map((item, i) => {
        const url =
          typeof item === "string" ? item : item.file_path || item.url || "";
        const recoveredId = extractIdFromUrl(url);

        if (typeof item === "string") {
          return {
            id: recoveredId || generateStableId(item, i),
            file_path: item, // R105 Standard alignment
            url: item, // UI legacy compatibility
            is_primary: i === selectedAssetIndex,
            order_index: i,
          } as MediaAsset;
        }
        // CNS V73.9: Safety gate for missing IDs or field names
        const obj = { ...item };
        // CNS V75: Priority to real DB ID from URL
        if (
          !obj.id ||
          obj.id.startsWith("img_") ||
          obj.id.startsWith("stable_")
        ) {
          if (recoveredId) obj.id = recoveredId;
        }
        if (!obj.id)
          obj.id = generateStableId(obj.file_path || obj.url || "", i);
        if (!obj.file_path && obj.url) obj.file_path = obj.url;
        return obj as MediaAsset;
      });
      xohiImageStore.initAssets(formattedAssets);
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
        selectedAvatarUrl =
          storeAssets[primaryIdx].file_path || storeAssets[primaryIdx].url;
      } else if (storeAssets.length === 0) {
        selectedAssetIndex = 0;
        selectedAvatarUrl = null;
      }
      untrack(() => syncAssetChanges());
    }
  });
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

  <!-- Unified Command Bar: iPhone 18 Aesthetic -->
  <div
    class="flex flex-col md:flex-row md:items-end justify-between gap-4 px-1 -mt-3"
  >
    <div class="flex items-center gap-5">
      <div
        class="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-500/10 border border-blue-400/20 flex items-center justify-center shadow-[0_8px_30px_rgba(59,130,246,0.15)] group/icon"
      >
        <LayoutGrid
          size={28}
          class="text-blue-400 group-hover:scale-110 transition-transform duration-500"
        />
        <div
          class="absolute -top-1 -right-1 w-3.5 h-3.5 bg-blue-500 rounded-full border-2 border-slate-950 shadow-[0_0_10px_#3b82f6]"
        ></div>
      </div>
      <div class="flex flex-col">
        <div class="flex items-center gap-3 mb-1 whitespace-nowrap">
          <span
            class="text-[10px] text-blue-400 font-black tracking-[0.4em] uppercase"
            >Asset Intelligence</span
          >
          <div
            class="px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 shadow-inner"
          >
            <span
              class="text-[8px] text-blue-300 font-black uppercase tracking-widest"
              >Active</span
            >
          </div>
        </div>
        <h3
          class="text-xl font-black text-white uppercase tracking-[0.2em] leading-tight"
        >
          Cấu trúc hình ảnh
        </h3>
        <div class="flex items-center gap-2 mt-1.5 opacity-40">
          <div class="w-8 h-[1px] bg-white/20"></div>
          <p
            class="text-[9px] text-white font-bold uppercase tracking-widest italic"
          >
            XOHI // NEURAL STUDIO
          </p>
        </div>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      {#if !isProcessing}
        <div class="flex items-center gap-3">
          <!-- URL Entry Island -->
          <div
            class="flex bg-white/[0.02] hover:bg-white/[0.04] p-1.5 rounded-2xl border border-white/10 transition-all h-11 group/input focus-within:border-blue-500/40 shadow-2xl"
          >
            <div
              class="flex items-center justify-center pl-3 text-white/30 group-focus-within/input:text-blue-400 transition-colors"
            >
              <LinkIcon size={16} />
            </div>
            <input
              type="url"
              placeholder="Dán link ảnh tại đây..."
              bind:value={customImageUrl}
              onkeydown={(e) => {
                if (
                  e.key === "Enter" &&
                  customImageUrl.trim() &&
                  customImageUrl.startsWith("http")
                ) {
                  e.preventDefault();
                  xohiImageStore.addImagesFromUrl(customImageUrl.trim());
                  customImageUrl = "";
                  vuiController.speak("Đã thêm ảnh.");
                }
              }}
              class="bg-transparent border-none outline-none text-[12px] text-white placeholder:text-white/20 px-4 w-36 transition-all focus:w-64 font-medium"
            />
          </div>

          <!-- Upload Island -->
          <label class="cursor-pointer group relative">
            <div
              class="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500"
            ></div>
            <div
              class="relative bg-blue-600 hover:bg-blue-500 border border-white/10 px-6 py-3 rounded-2xl text-xs font-black text-white uppercase tracking-[0.15em] transition-all flex items-center gap-2 shadow-xl active:scale-95"
            >
              <Upload size={16} class="text-white/80" />
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

      <!-- Found Count Badge -->
      <div
        class="px-6 py-3 rounded-2xl bg-white/[0.03] border border-white/10 shadow-2xl backdrop-blur-md"
      >
        <span
          class="text-[10px] text-white/40 font-black uppercase tracking-[0.2em]"
          >Assets Found // <span class="text-blue-400 ml-1"
            >{xohiImageStore.assets.length}</span
          ></span
        >
      </div>
    </div>
  </div>

  <div
    class="transition-all duration-700 min-h-[310px] relative bg-gradient-to-br from-blue-500/10 via-white/[0.01] to-transparent rounded-[2rem] border border-white/10 shadow-2xl mb-0"
  >
    <div class="p-2 md:p-3">
      <ImageGrid />
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
            >Kho dự phòng // RESERVES</span
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
                  xohiImageStore.addImagesFromUrl(url);
                  reserve_assets = reserve_assets.filter((_, idx) => idx !== i);
                }
              }}
              onclick={() => {
                // Add Logic: Move from reserve to primary collection
                vuiController.speak("Đã thêm vào bộ sưu tập.");
                xohiImageStore.addImagesFromUrl(url);
                reserve_assets = reserve_assets.filter((_, idx) => idx !== i);
              }}
              class="group/reserve relative aspect-square rounded-2xl overflow-hidden border border-white/10 bg-white/[0.02] hover:border-amber-500/50 hover:bg-white/[0.05] hover:scale-105 transition-all duration-500 cursor-pointer shadow-lg"
            >
              <img
                src={url}
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
                    reserve_assets = (reserve_assets as string[]).filter((_, idx) => idx !== i);
                    
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

{#if assets.length === 0 && !isProcessing}
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
