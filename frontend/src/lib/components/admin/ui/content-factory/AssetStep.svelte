<script lang="ts">
  import {
    Image as ImageIcon,
    Link as LinkIcon,
    Plus,
    Trash2,
    Star,
    Check,
    RotateCcw,
  } from "lucide-svelte";
  import { fade, scale } from "svelte/transition";
  import { vuiController } from "$lib/vui";

  import type { MediaAsset } from "$lib/state/types";

  let {
    isProcessing,
    isExpanded,
    assets = $bindable([] as (MediaAsset | string)[]),
    reserve_assets = $bindable([] as string[]),
    customImageUrl = $bindable(""),
    selectedAvatarUrl = $bindable(null),
    selectedAssetIndex = $bindable(0),
    handleImageError,
    syncAssetChanges,
    deleteAsset,
    handleRetry,
    handleMouseMove,
  }: {
    isProcessing: boolean;
    isExpanded: boolean;
    assets: (MediaAsset | string)[];
    reserve_assets: string[];
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
          const preset = (parts[1] || "square") as any;

          const targetAsset = xohiImageStore.assets[index];
          if (targetAsset) {
            vuiController.speak(`Dạ, em đang cắt ảnh số ${index + 1} theo khung ${preset} cho Sếp đây ạ.`);
            xohiImageStore.smartCrop(targetAsset.id, preset);
          } else {
            vuiController.speak("Dạ Sếp ơi, em không tìm thấy ảnh đó để cắt ạ.");
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

  // Phase 15.3: Đồng bộ hóa dữ liệu từ Campaign vào Store khi Step được load
  $effect(() => {
    if (assets.length > 0 && xohiImageStore.assets.length === 0) {
      const formattedAssets = assets.map((item, i) => {
        if (typeof item === 'string') {
          return {
            id: `img_${i}_${Date.now()}`,
            url: item,
            is_primary: i === selectedAssetIndex,
            order_index: i
          };
        }
        return item;
      });
      xohiImageStore.initAssets(formattedAssets);
    }
  });

  // Phase 15.3: Đồng bộ ngược lại khi Store thay đổi (Optimistic Sync)
  $effect(() => {
    const storeAssets = xohiImageStore.assets;
    // Phase 15.3: Luôn đồng bộ kể cả khi mảng rỗng để đảm bảo DB cập nhật đúng
    if (JSON.stringify(storeAssets) !== JSON.stringify(assets)) {
      assets = storeAssets;
      const primaryIdx = storeAssets.findIndex(a => a.is_primary);
      if (primaryIdx !== -1) {
        selectedAssetIndex = primaryIdx;
        selectedAvatarUrl = storeAssets[primaryIdx].file_path;
      } else if (storeAssets.length === 0) {
        selectedAssetIndex = 0;
        selectedAvatarUrl = null;
      }
      syncAssetChanges();
    }
  });
</script>

<div class="space-y-3 flex flex-col min-h-0">
  <!-- Modern Minimalist Header -->
  <div class="flex items-center justify-between">
    <div class="hidden md:flex items-center gap-4">
      <div class="relative w-2 h-2">
        <div
          class="absolute inset-0 bg-blue-500 rounded-full animate-ping opacity-20"
        ></div>
        <div
          class="absolute inset-0 bg-blue-400 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.8)]"
        ></div>
      </div>
      <div class="flex flex-col">
        <span
          class="text-[8px] text-blue-400/50 font-black tracking-[0.3em] uppercase mb-0.5"
          >Asset Intelligence</span
        >
        <span
          class="text-[12px] text-white/90 font-bold tracking-tight uppercase"
          >SELECT_MODE://ULTRA_DND</span
        >
      </div>
    </div>

    <div class="flex items-center gap-3">
      {#if !isProcessing}
        <div
          class="flex bg-white/[0.03] hover:bg-white/[0.05] p-1 rounded-xl border border-white/5 transition-all h-9 group/input"
        >
          <div
            class="flex items-center justify-center pl-3 text-white/20 group-focus-within/input:text-blue-400 transition-colors"
          >
            <LinkIcon size={14} />
          </div>
          <input
            type="url"
            placeholder="Dán link ảnh vào đây..."
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
            class="bg-transparent border-none outline-none text-[11px] text-white placeholder:text-white/20 px-3 w-40 transition-all focus:w-64"
          />
        </div>
      {/if}

      <div
        class="hidden md:block px-4 py-1.5 rounded-xl bg-white/[0.03] border border-white/5"
      >
        <span
          class="text-[10px] text-white/40 font-bold uppercase tracking-widest"
          >Found <span class="text-blue-400 ml-1 font-black"
            >{xohiImageStore.assets.length}</span
          ></span
        >
      </div>
    </div>
  </div>

  <div class="transition-all duration-500 min-h-0 relative bg-black/20 rounded-3xl border border-white/5 overflow-hidden">
    <ImageGrid />
  </div>

  <!-- Reserve Assets Section (Phase 120) -->
  {#if reserve_assets && reserve_assets.length > 0}
    <div
      class="mt-12 pt-8 border-t border-white/5"
      in:fade={{ duration: 800 }}
    >
      <div class="flex items-center gap-2 mb-1">
        <div
          class="w-1.5 h-1.5 rounded-full bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.6)]"
        ></div>
        <span
          class="text-[11px] text-amber-500/80 font-black tracking-[0.2em] uppercase"
          >Kho dự phòng</span
        >
      </div>

      <div
        class="flex gap-4 overflow-x-auto overflow-y-hidden pb-4 pt-1 px-1 -mx-1 custom-scrollbar-horizontal snap-x snap-mandatory"
      >
        {#each reserve_assets as url, i}
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
              class="group/reserve relative aspect-square rounded-[1.5rem] overflow-hidden border border-white/5 bg-white/[0.01] hover:border-amber-500/30 hover:scale-105 transition-all duration-500 cursor-pointer"
            >
              <img
                src={url}
                alt="Reserve {i}"
                class="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-700"
              />
              <div
                class="absolute inset-0 bg-amber-500/10 opacity-0 group-hover/reserve:opacity-100 flex items-center justify-center transition-opacity"
              >
                <Plus size={20} class="text-white drop-shadow-lg" />
              </div>

              <!-- Delete button for reserve assets -->
              <button
                onclick={(e) => {
                  e.stopPropagation();
                  reserve_assets = reserve_assets.filter((_, idx) => idx !== i);
                  syncAssetChanges();
                  vuiController.speak("Đã xóa khỏi kho dự phòng.");
                }}
                class="absolute top-2 right-2 p-1.5 rounded-full bg-black/40 text-white/40 hover:bg-red-500 hover:text-white opacity-0 group-hover/reserve:opacity-100 transition-all"
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
