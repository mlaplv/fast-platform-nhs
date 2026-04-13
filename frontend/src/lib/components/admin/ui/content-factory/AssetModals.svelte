<script lang="ts">
  import { onMount } from "svelte";
  import { Library, X, Flame } from "lucide-svelte";
  import { fade, scale } from "svelte/transition";
  import FileManager from "$lib/components/media/FileManager.svelte";
  import { resolveMediaUrl } from "$lib/state/utils";
  import type { MediaAsset } from "$lib/state/types";

  interface Props {
    showLibrary: boolean;
    pendingPurgeAsset: MediaAsset | null;
    onLibrarySelect: (selectedAssets: MediaAsset[]) => void;
    onCloseLibrary: () => void;
    onClosePurge: () => void;
    onConfirmPurge: (asset: MediaAsset) => void;
  }

  let { showLibrary = $bindable(), pendingPurgeAsset = $bindable(), onLibrarySelect, onCloseLibrary, onClosePurge, onConfirmPurge }: Props = $props();

  onMount(() => {
    if (showLibrary === undefined) showLibrary = false;
    if (pendingPurgeAsset === undefined) pendingPurgeAsset = null;
  });
</script>

<!-- CNS V78: Media Library Modal (Full Manager Picker) -->
{#if showLibrary}
  <div
    class="fixed inset-0 z-[var(--z-admin-asset-modal-backdrop)] flex items-center justify-center p-4 md:p-8 bg-slate-950/80 backdrop-blur-2xl"
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
          onclick={onCloseLibrary}
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
          onSelect={onLibrarySelect}
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
          onclick={onCloseLibrary}
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
            onclick={onClosePurge}
            class="py-3 px-4 bg-white/5 hover:bg-white/10 text-white/60 font-black text-[10px] uppercase tracking-widest rounded-xl transition-all border border-white/5"
          >
            Hủy bỏ
          </button>
          <button
            onclick={() => { if (pendingPurgeAsset) onConfirmPurge(pendingPurgeAsset); }}
            class="py-3 px-4 bg-red-600 hover:bg-red-500 text-white font-black text-[10px] uppercase tracking-widest rounded-xl transition-all shadow-[0_10px_30px_rgba(220,38,38,0.4)] active:scale-95"
          >
            XÁC NHẬN XOÁ
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
