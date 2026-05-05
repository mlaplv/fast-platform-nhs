<script lang="ts">
  import { onMount } from "svelte";
  import { fade, slide } from "svelte/transition";
  import Plus from "lucide-svelte/icons/plus";
  import Search from "lucide-svelte/icons/search";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Edit3 from "lucide-svelte/icons/edit-3";
  import Globe from "lucide-svelte/icons/globe";
  import Monitor from "lucide-svelte/icons/monitor";
  import Smartphone from "lucide-svelte/icons/smartphone";
  import Layout from "lucide-svelte/icons/layout";
  import Save from "lucide-svelte/icons/save";
  import X from "lucide-svelte/icons/x";
  import Upload from "lucide-svelte/icons/upload";
  import ExternalLink from "lucide-svelte/icons/external-link";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";

  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import type { BaseWidgetProps, MediaAsset, Banner, BannerForm } from "$lib/types";
  import BannerDrawer from "./BannerDrawer.svelte";

  let { data = {} } = $props<BaseWidgetProps>();

  // --- STATE ---
  let banners = $state<Banner[]>([]);
  let isLoading = $state(true);
  let showDrawer = $state(false);

  // Filters
  let searchQuery = $state("");
  let filterPosition = $state("all");
  let filterDevice = $state("all");

  // Selection
  let selectedIds = $state<Set<string>>(new Set());

  // Derived
  const filteredBanners = $derived(banners.filter(b => {
    if (searchQuery && !b.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (filterPosition !== "all" && b.position !== filterPosition) return false;
    if (filterDevice !== "all" && b.device_type !== filterDevice) return false;
    return true;
  }));
  const isAllSelected = $derived(filteredBanners.length > 0 && selectedIds.size === filteredBanners.length);

  // Form State
  let form = $state<BannerForm>({
    title: "",
    description: "",
    image_url: "",
    mobile_image_url: "",
    link_url: "",
    position: "home_main",
    order_index: 0,
    is_active: true,
    device_type: "all"
  });

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

  async function loadBanners() {
    isLoading = true;
    try {
      const res = await apiClient.get<{ data: Banner[]; total: number }>("/api/v1/banners");
      banners = res.data;
    } catch (err) {
      nanobot.showToast("Không thể tải danh sách banner.", "error");
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadBanners();
  });

  function openCreate() {
    form = {
      title: "",
      description: "",
      image_url: "",
      mobile_image_url: "",
      link_url: "",
      position: "home_main",
      order_index: banners.length,
      is_active: true,
      device_type: "all",
      id: undefined
    };
    showDrawer = true;
  }

  function openEdit(b: Banner) {
    form = {
      id: b.id,
      title: b.title,
      description: b.description || "",
      image_url: b.image_url,
      mobile_image_url: b.mobile_image_url || "",
      link_url: b.link_url || "",
      position: b.position,
      order_index: b.order_index,
      is_active: b.is_active,
      device_type: b.device_type
    };
    showDrawer = true;
  }

  async function save() {
    await loadBanners();
  }

  async function toggleActive(b: Banner) {
    try {
      await apiClient.put(`/api/v1/banners/${b.id}`, { is_active: !b.is_active });
      b.is_active = !b.is_active;
    } catch (err) {
      nanobot.showToast("Không thể cập nhật trạng thái.", "error");
    }
  }

  async function remove(id: string) {
    if (!confirm("Boss có chắc muốn xóa banner này không?")) return;
    try {
      await apiClient.delete(`/api/v1/banners/${id}`);
      nanobot.showToast("Đã xóa banner.", "success");
      selectedIds.delete(id);
      selectedIds = new Set(selectedIds);
      await loadBanners();
    } catch (err) {
      nanobot.showToast("Xóa banner thất bại.", "error");
    }
  }

  function toggleSelection(id: string) {
    if (selectedIds.has(id)) {
      selectedIds.delete(id);
    } else {
      selectedIds.add(id);
    }
    selectedIds = new Set(selectedIds);
  }

  function toggleAll() {
    if (isAllSelected) {
      selectedIds = new Set();
    } else {
      const newSet = new Set(selectedIds);
      filteredBanners.forEach(b => newSet.add(b.id));
      selectedIds = newSet;
    }
  }

  async function bulkDelete() {
    if (selectedIds.size === 0) return;
    if (!confirm(`Boss có chắc muốn xóa ${selectedIds.size} banner đã chọn?`)) return;
    
    try {
      // In a real app we'd have a bulk delete endpoint, but we loop here for now
      for (const id of selectedIds) {
        await apiClient.delete(`/api/v1/banners/${id}`);
      }
      nanobot.showToast(`Đã xóa ${selectedIds.size} banner.`, "success");
      selectedIds = new Set();
      await loadBanners();
    } catch (err) {
      nanobot.showToast("Xóa một số banner thất bại.", "error");
      await loadBanners();
    }
  }

  async function bulkToggleActive(targetStatus: boolean) {
    if (selectedIds.size === 0) return;
    
    try {
      for (const id of selectedIds) {
        await apiClient.put(`/api/v1/banners/${id}`, { is_active: targetStatus });
      }
      nanobot.showToast(`Đã cập nhật trạng thái ${selectedIds.size} banner.`, "success");
      selectedIds = new Set();
      await loadBanners();
    } catch (err) {
      nanobot.showToast("Cập nhật một số banner thất bại.", "error");
      await loadBanners();
    }
  }

  // Removed redundant media select (now in BannerDrawer)
</script>

<div class="w-full h-full flex flex-col bg-[#020202] text-zinc-100 font-sans selection:bg-cyan-500/30">
  <!-- Header -->
  <header class="h-16 px-8 border-b border-white/5 flex items-center justify-between bg-zinc-950/40 backdrop-blur-xl z-50 sticky top-0">
    <div class="flex items-center gap-4">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
        <Layout size={20} class="text-black" />
      </div>
      <div>
        <h1 class="text-lg font-black tracking-tighter uppercase italic text-transparent bg-clip-text bg-gradient-to-r from-white to-zinc-500">
          BANNER_VAULT
        </h1>
        <p class="text-[8px] font-mono text-cyan-500 uppercase tracking-[0.4em]">Visual Promotion Protocol</p>
      </div>
    </div>

    <div class="flex items-center gap-4">
      <button
        onclick={openCreate}
        class="h-10 px-6 bg-cyan-600 hover:bg-cyan-500 text-black font-black rounded-lg text-[10px] uppercase tracking-widest shadow-[0_0_20px_rgba(8,145,178,0.3)] transition-all flex items-center gap-2 group"
      >
        <Plus size={14} class="group-hover:rotate-90 transition-transform duration-300" />
        New Deployment
      </button>
    </div>
  </header>

  <main class="flex-1 overflow-y-auto custom-scrollbar p-8">
    <!-- Filter Bar -->
    <div class="mb-8 flex flex-col gap-4">
      <div class="flex items-center justify-between gap-4">
        <!-- Search -->
        <div class="relative flex-1 max-w-md">
          <Search size={16} class="absolute left-4 top-1/2 -translate-y-1/2 text-white/50" />
          <input 
            type="text" 
            bind:value={searchQuery}
            placeholder="Search deployments..." 
            class="w-full bg-white/[0.05] border border-white/20 rounded-xl pl-12 pr-4 py-3 text-sm font-bold text-white placeholder:text-white/40 focus:outline-none focus:border-cyan-500/50 transition-all"
          />
        </div>

        <!-- Filters -->
        <div class="flex items-center gap-4">
          <select bind:value={filterPosition} class="bg-white/[0.05] border border-white/20 rounded-xl px-4 py-3 text-[11px] font-bold text-white outline-none focus:border-cyan-500/50 transition-all custom-select w-48">
            <option value="all" class="bg-[#050505]">All Placements</option>
            {#each POSITIONS as p}
              <option value={p.id} class="bg-[#050505]">{p.label}</option>
            {/each}
          </select>
          <select bind:value={filterDevice} class="bg-white/[0.05] border border-white/20 rounded-xl px-4 py-3 text-[11px] font-bold text-white outline-none focus:border-cyan-500/50 transition-all custom-select w-40">
            <option value="all" class="bg-[#050505]">All Devices</option>
            <option value="desktop" class="bg-[#050505]">Desktop Only</option>
            <option value="mobile" class="bg-[#050505]">Mobile Only</option>
          </select>
        </div>
      </div>

      <!-- Bulk Actions Bar -->
      <div class="h-12 border border-white/20 rounded-xl bg-white/[0.05] flex items-center px-4 justify-between transition-all {selectedIds.size > 0 ? 'opacity-100 border-cyan-500/50 bg-cyan-950/30' : 'opacity-70'}">
        <div class="flex items-center gap-4">
          <button 
            onclick={toggleAll}
            class="w-5 h-5 rounded border {isAllSelected ? 'bg-cyan-500 border-cyan-500 text-black' : 'border-white/40 hover:border-cyan-500 text-transparent'} flex items-center justify-center transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </button>
          <span class="text-[11px] font-black uppercase tracking-widest {selectedIds.size > 0 ? 'text-cyan-400' : 'text-zinc-500'}">
            {selectedIds.size} Selected
          </span>
        </div>
        
        <div class="flex items-center gap-2 transition-all {selectedIds.size === 0 ? 'opacity-50 pointer-events-none' : 'opacity-100'}">
          <button 
            onclick={() => bulkToggleActive(true)}
            class="h-8 px-4 rounded-lg bg-white/10 hover:bg-white/20 text-[10px] font-black uppercase tracking-widest text-white transition-all flex items-center gap-2"
          >
            <div class="w-2 h-2 rounded-full bg-cyan-500"></div> Activate
          </button>
          <button 
            onclick={() => bulkToggleActive(false)}
            class="h-8 px-4 rounded-lg bg-white/10 hover:bg-white/20 text-[10px] font-black uppercase tracking-widest text-white transition-all flex items-center gap-2"
          >
            <div class="w-2 h-2 rounded-full bg-red-500"></div> Deactivate
          </button>
          <div class="w-px h-4 bg-white/20 mx-2"></div>
          <button 
            onclick={bulkDelete}
            class="h-8 px-4 rounded-lg bg-red-500/10 hover:bg-red-500 hover:text-white border border-red-500/50 hover:border-red-500 text-[10px] font-black uppercase tracking-widest text-red-500 transition-all flex items-center gap-2"
          >
            <Trash2 size={12} /> Delete
          </button>
        </div>
      </div>
    </div>

    {#if isLoading}
      <div class="h-full flex flex-col items-center justify-center gap-6">
        <div class="w-16 h-16 border-2 border-cyan-500/10 border-t-cyan-500 rounded-full animate-spin"></div>
        <p class="text-[10px] font-mono text-cyan-400 uppercase tracking-[0.5em] animate-pulse">Syncing Visual Assets...</p>
      </div>
    {:else if filteredBanners.length === 0}
      <div class="h-full flex flex-col items-center justify-center gap-8 opacity-40">
        <div class="w-24 h-24 rounded-full border border-dashed border-white/20 flex items-center justify-center">
          <Layout size={40} />
        </div>
        <div class="text-center space-y-2">
          <p class="text-xs font-mono uppercase tracking-[0.3em]">No Active Deployments Found</p>
          <button onclick={openCreate} class="text-cyan-400 text-[10px] font-black uppercase hover:underline">Initialize First Banner</button>
        </div>
      </div>
    {:else}
      <div class="grid grid-cols-1 gap-4">
        {#each filteredBanners as b, i}
          <div
            class="group bg-zinc-950/40 border {selectedIds.has(b.id) ? 'border-cyan-500/50 shadow-[0_0_20px_rgba(8,145,178,0.15)]' : 'border-white/5'} rounded-2xl p-4 flex items-center gap-6 hover:border-cyan-500/30 transition-all duration-300 animate-in slide-in-from-bottom-2"
            style="animation-delay: {i * 0.05}s"
          >
            <!-- Checkbox -->
            <button 
              onclick={() => toggleSelection(b.id)}
              class="w-5 h-5 shrink-0 rounded border {selectedIds.has(b.id) ? 'bg-cyan-500 border-cyan-500 text-black' : 'border-white/40 hover:border-cyan-500 text-transparent'} flex items-center justify-center transition-all"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </button>

            <!-- Preview -->
            <div class="w-48 aspect-video rounded-xl bg-black border border-white/10 overflow-hidden relative shadow-2xl flex">
              {#if b.image_url}
                <div class="flex-1 relative h-full">
                  <img src={b.image_url} alt={b.title} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-1000 opacity-80 group-hover:opacity-100" />
                  <div class="absolute top-1 left-1 px-1.5 py-0.5 bg-black/60 rounded text-[6px] font-black text-white/50 uppercase">Desktop</div>
                </div>
              {/if}
              {#if b.mobile_image_url}
                <div class="w-16 border-l border-white/10 relative h-full bg-zinc-900">
                  <img src={b.mobile_image_url} alt={b.title} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-1000 opacity-80 group-hover:opacity-100" />
                  <div class="absolute top-1 left-1 px-1 py-0.5 bg-black/60 rounded text-[6px] font-black text-white/50 uppercase">Mob</div>
                </div>
              {/if}
              <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none"></div>
              <div class="absolute bottom-2 left-2 px-2 py-0.5 bg-black/60 backdrop-blur-md rounded text-[7px] font-black text-cyan-400 uppercase tracking-widest border border-cyan-500/20">
                {b.position}
              </div>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-3 mb-1">
                <h3 class="text-sm font-black text-white group-hover:text-cyan-400 transition-colors uppercase tracking-tight truncate">
                  {b.title}
                </h3>
                <div class="flex items-center gap-1.5">
                  {#if b.device_type === 'all'}
                    <Globe size={10} class="text-zinc-500" />
                  {:else if b.device_type === 'desktop'}
                    <Monitor size={10} class="text-zinc-500" />
                  {:else}
                    <Smartphone size={10} class="text-zinc-500" />
                  {/if}
                </div>
              </div>
              <p class="text-[10px] text-zinc-500 line-clamp-1 h-4 italic">
                {b.link_url || 'No redirect link'}
              </p>

              <div class="mt-4 flex items-center gap-6">
                <div class="flex flex-col gap-0.5">
                  <span class="text-[8px] font-mono text-zinc-600 uppercase">Rank</span>
                  <span class="text-xs font-black text-zinc-300">#{b.order_index}</span>
                </div>
                <div class="h-6 w-px bg-white/5"></div>
                <div class="flex flex-col gap-1">
                   <span class="text-[8px] font-mono text-zinc-600 uppercase">Protocol Status</span>
                   <button
                    onclick={() => toggleActive(b)}
                    class="flex items-center gap-2 group/toggle"
                   >
                     <div class="w-8 h-4 rounded-full transition-colors duration-300 relative {b.is_active ? 'bg-cyan-500' : 'bg-red-500/20'}">
                        <div class="absolute top-1 left-1 w-2 h-2 rounded-full bg-white transition-transform duration-300 {b.is_active ? 'translate-x-4' : ''} shadow-[0_0_8px_rgba(0,255,255,0.4)]"></div>
                     </div>
                     <span class="text-[9px] font-black uppercase tracking-widest {b.is_active ? 'text-cyan-400' : 'text-red-500'}">
                        {b.is_active ? 'ACTIVE' : 'OFFLINE'}
                     </span>
                   </button>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-2 pr-2">
              <button
                onclick={() => openEdit(b)}
                class="w-10 h-10 rounded-xl bg-white/5 border border-white/5 flex items-center justify-center hover:bg-cyan-500 hover:text-black hover:border-cyan-500 transition-all text-zinc-500"
              >
                <Edit3 size={16} />
              </button>
              <button
                onclick={() => remove(b.id)}
                class="w-10 h-10 rounded-xl bg-white/5 border border-white/5 flex items-center justify-center hover:bg-red-500 hover:text-white hover:border-red-500 transition-all text-zinc-500"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </main>
  
  <BannerDrawer
    bind:isOpen={showDrawer}
    bind:banner={form}
    onClose={() => showDrawer = false}
    onSave={loadBanners}
  />
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='rgba(255,255,255,0.6)'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 1rem center;
    background-size: 1rem;
  }
</style>
