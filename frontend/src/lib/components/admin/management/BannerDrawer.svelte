<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import Plus from "@lucide/svelte/icons/plus";
  import Save from "@lucide/svelte/icons/save";
  import Upload from "@lucide/svelte/icons/upload";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Globe from "@lucide/svelte/icons/globe";
  import Monitor from "@lucide/svelte/icons/monitor";
  import Smartphone from "@lucide/svelte/icons/smartphone";
  import Activity from "@lucide/svelte/icons/activity";
import X from "@lucide/svelte/icons/x";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import type { MediaAsset, BannerForm } from "$lib/types";
  import FileManager from "../../media/FileManager.svelte";

  let {
    isOpen = $bindable(),
    banner = $bindable(),
    onClose,
    onSave
  } = $props<{
    isOpen: boolean;
    banner: BannerForm;
    onClose: () => void;
    onSave: () => void;
  }>();

  let isSaving = $state(false);
  let showMediaVault: 'desktop' | 'mobile' | false = $state(false);

  const POSITIONS = [
    { id: "home_main", label: "Home Main Slider" },
    { id: "home_side", label: "Home Sidebar" },
    { id: "product_top", label: "Product Top" },
    { id: "popup", label: "Global Popup" }
  ];

  const DEVICES = [
    { id: "all", label: "All Devices", icon: Globe },
    { id: "desktop", label: "Desktop Only", icon: Monitor },
    { id: "mobile", label: "Mobile Only", icon: Smartphone }
  ];

  async function handleSave() {
    if (!banner.title || (!banner.image_url && !banner.mobile_image_url)) {
      nanobot.showToast("Vui lòng nhập tiêu đề và chọn ít nhất 1 ảnh.", "warning");
      return;
    }

    isSaving = true;
    try {
      if (banner.id) {
        await apiClient.put(`/api/v1/banners/${banner.id}`, banner);
        nanobot.showToast("Đã cập nhật banner thành công.", "success");
      } else {
        await apiClient.post("/api/v1/banners", banner);
        nanobot.showToast("Đã tạo banner mới thành công.", "success");
      }
      onSave();
      onClose();
    } catch (err) {
      console.error("Save failure", err);
      nanobot.showToast("Lưu banner thất bại.", "error");
    } finally {
      isSaving = false;
    }
  }

  function handleMediaSelect(assets: MediaAsset[]) {
    if (assets.length > 0) {
      if (showMediaVault === 'desktop') {
        banner.image_url = assets[0].file_path;
      } else if (showMediaVault === 'mobile') {
        banner.mobile_image_url = assets[0].file_path;
      }
    }
    showMediaVault = false;
  }
</script>

{#if isOpen}
  <div use:portal class="relative" style="z-index: {Z_INDEX_ADMIN.MODAL};">
    <!-- Backdrop -->
    <div
      class="fixed inset-0 bg-black/95 md:bg-black/90 md:backdrop-blur-sm"
      style="z-index: {Z_INDEX_ADMIN.OVERLAY};"
      transition:fade={{ duration: 300 }}
      onclick={onClose}
      aria-label="Close drawer"
      role="button"
      tabindex="0"
      onkeydown={(e) => e.key === 'Escape' && onClose()}
    ></div>

    <!-- Drawer Panel: ELITE DESIGN (Right Aligned) -->
    <div
      class="fixed top-0 right-0 h-full w-[500px] max-w-full bg-[#050505] border-l border-white/10 shadow-[-30px_0_50px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden"
      transition:fly={{ x: 500, duration: 300, opacity: 1 }}
      style="z-index: {Z_INDEX_ADMIN.MODAL + 10};"
    >
      <!-- Header -->
      <div class="h-16 flex items-center justify-between px-6 border-b border-white/10 relative bg-black/40">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <Activity size={14} class="text-cyan-500 animate-pulse" />
          </div>
          <div>
            <h2 class="text-sm font-bold text-white tracking-widest uppercase">
              {banner.id ? 'Modify Deployment' : 'New Deployment'}
            </h2>
            {#if banner.id}
              <div class="text-[9px] font-mono text-gray-500 uppercase">SYS_ID: {banner.id}</div>
            {/if}
          </div>
        </div>
        <button 
          onclick={onClose}
          class="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-white hover:bg-white/10 rounded-lg transition-colors border border-transparent hover:border-white/10"
        >
          <X size={16} />
        </button>

        <div class="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
      </div>

      <!-- Form Body -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
        <!-- Title & URL -->
        <div class="grid grid-cols-1 gap-6">
          <div class="space-y-3">
            <label class="block text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1" for="title">Banner Title</label>
            <input 
              id="title"
              bind:value={banner.title}
              type="text" 
              placeholder="e.g. Strategic Campaign 2026..."
              class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-4 text-sm font-bold text-white placeholder:text-white/5 focus:outline-none focus:border-cyan-500/30 transition-all shadow-inner"
            />
          </div>
          <div class="space-y-3">
            <label class="block text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1" for="url">Target URL</label>
            <div class="relative">
              <input 
                id="url"
                bind:value={banner.link_url}
                type="text" 
                placeholder="https://osmo/promo..."
                class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-4 text-sm font-bold text-white placeholder:text-white/5 focus:outline-none focus:border-cyan-500/30 transition-all shadow-inner pr-12"
              />
              <ExternalLink size={14} class="absolute right-5 top-1/2 -translate-y-1/2 text-white/10" />
            </div>
          </div>
        </div>

        <!-- Visual Asset -->
        <div class="space-y-4">
          <label class="block text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Visual Assets</label>
          <div class="grid grid-cols-2 gap-4">
            <!-- Desktop -->
            <button
              class="w-full aspect-[21/9] rounded-2xl border border-dashed border-white/10 bg-white/[0.02] flex flex-col items-center justify-center gap-4 relative overflow-hidden group/picker transition-all hover:border-cyan-500/30"
              onclick={() => showMediaVault = 'desktop'}
            >
              {#if banner.image_url}
                <img src={banner.image_url} alt="Desktop Preview" class="w-full h-full object-cover" />
                <div class="absolute inset-0 bg-black/60 opacity-0 group-hover/picker:opacity-100 flex items-center justify-center transition-all backdrop-blur-sm">
                   <div class="px-4 py-2 bg-white text-black text-[9px] font-black uppercase rounded-lg shadow-xl">Update Desktop</div>
                </div>
              {:else}
                <div class="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 group-hover/picker:scale-110 transition-transform">
                  <Monitor size={16} />
                </div>
                <div class="text-center">
                  <p class="text-[8px] font-black uppercase text-zinc-400">Desktop Image</p>
                  <p class="text-[6px] text-zinc-600 mt-1 uppercase font-mono tracking-widest">1920x800 PX</p>
                </div>
              {/if}
            </button>
            
            <!-- Mobile -->
            <button
              class="w-full aspect-[9/16] max-h-32 rounded-2xl border border-dashed border-white/10 bg-white/[0.02] flex flex-col items-center justify-center gap-4 relative overflow-hidden group/picker transition-all hover:border-cyan-500/30 mx-auto"
              onclick={() => showMediaVault = 'mobile'}
            >
              {#if banner.mobile_image_url}
                <img src={banner.mobile_image_url} alt="Mobile Preview" class="w-full h-full object-cover" />
                <div class="absolute inset-0 bg-black/60 opacity-0 group-hover/picker:opacity-100 flex items-center justify-center transition-all backdrop-blur-sm">
                   <div class="px-4 py-2 bg-white text-black text-[9px] font-black uppercase rounded-lg shadow-xl">Update Mobile</div>
                </div>
              {:else}
                <div class="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 group-hover/picker:scale-110 transition-transform">
                  <Smartphone size={16} />
                </div>
                <div class="text-center">
                  <p class="text-[8px] font-black uppercase text-zinc-400">Mobile Image</p>
                  <p class="text-[6px] text-zinc-600 mt-1 uppercase font-mono tracking-widest">1080x1920 PX</p>
                </div>
              {/if}
            </button>
          </div>
        </div>

        <!-- Configuration Grid -->
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-3">
            <label class="block text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Placement</label>
            <select bind:value={banner.position} class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-4 py-4 text-[11px] font-bold text-white outline-none focus:border-cyan-500/30 transition-all custom-select">
              {#each POSITIONS as p}
                <option value={p.id} class="bg-[#050505]">{p.label}</option>
              {/each}
            </select>
          </div>
          <div class="space-y-3">
            <label class="block text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Priority Index</label>
            <input 
              bind:value={banner.order_index} 
              type="number" 
              class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-4 text-[11px] font-bold text-white text-center outline-none focus:border-cyan-500/30 transition-all" 
            />
          </div>
        </div>

        <!-- Device Target -->
        <div class="space-y-4">
          <label class="block text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Device Target</label>
          <div class="flex p-1.5 bg-white/[0.02] border border-white/5 rounded-2xl">
            {#each DEVICES as d}
              {@const active = banner.device_type === d.id}
              <button
                onclick={() => banner.device_type = d.id}
                class="flex-1 py-3 flex items-center justify-center gap-2 rounded-xl transition-all
                  {active ? 'bg-cyan-500 text-black shadow-lg shadow-cyan-500/20' : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5'}"
              >
                <d.icon size={14} />
                <span class="text-[9px] font-black uppercase tracking-widest">{d.id}</span>
              </button>
            {/each}
          </div>
        </div>

        <!-- Protocol Status -->
        <div class="space-y-4">
          <div class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Protocol Status</div>
          <button
            onclick={() => banner.is_active = !banner.is_active}
            class="w-full p-5 rounded-2xl bg-white/[0.02] border border-white/5 flex items-center justify-between group/status transition-all hover:bg-white/[0.04]"
          >
            <div class="flex items-center gap-4">
              <div class="w-12 h-6 rounded-full transition-colors duration-500 relative {banner.is_active ? 'bg-cyan-500' : 'bg-red-500/20'}">
                <div class="absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform duration-500 {banner.is_active ? 'translate-x-6' : ''} shadow-lg"></div>
              </div>
              <span class="text-[10px] font-black uppercase tracking-[0.2em] {banner.is_active ? 'text-cyan-400' : 'text-red-500'}">
                {banner.is_active ? 'Operational' : 'Decommissioned'}
              </span>
            </div>
            <Activity size={16} class={banner.is_active ? 'text-cyan-500' : 'text-zinc-800'} />
          </button>
        </div>

        <!-- Submit Nexus -->
        <div class="pt-6">
          <button 
            onclick={handleSave}
            disabled={isSaving}
            class="w-full py-5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 text-black text-[11px] font-black uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_10px_30px_-5px_rgba(8,145,178,0.4)] disabled:opacity-50 flex items-center justify-center overflow-hidden relative group/save"
          >
            <div class="absolute inset-0 bg-white/30 -translate-x-full group-hover/save:translate-x-full transition-transform duration-1000"></div>
            
            {#if isSaving}
              <RefreshCw size={16} class="animate-spin mr-3" />
              Processing...
            {:else}
              Deploy Strategy
            {/if}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

{#if showMediaVault}
  <div 
    use:portal
    class="fixed inset-0 bg-black/90 backdrop-blur-xl flex flex-col" 
    style="z-index: {Z_INDEX_ADMIN.MEDIA_OVERLAY};"
    transition:fade
  >
    <div class="flex-1 overflow-hidden">
      <FileManager
        mode="pick"
        onPickConfirm={handleMediaSelect}
        onPickClose={() => showMediaVault = false}
      />
    </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0, 255, 255, 0.3); }

  .custom-select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='rgba(255,255,255,0.2)'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 1.25rem center;
    background-size: 1rem;
  }
</style>
