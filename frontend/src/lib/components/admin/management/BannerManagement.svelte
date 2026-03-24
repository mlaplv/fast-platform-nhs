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

  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import type { BaseWidgetProps, MediaAsset } from "$lib/types";
  import FileManager from "../../media/FileManager.svelte";

  interface Banner {
    id: string;
    title: string;
    description: string | null;
    image_url: string;
    link_url: string | null;
    position: string;
    order_index: number;
    is_active: boolean;
    device_type: string;
    created_at: string;
  }

  let { data = {} } = $props<BaseWidgetProps>();

  // --- STATE ---
  let banners = $state<Banner[]>([]);
  let isLoading = $state(true);
  let isSaving = $state(false);
  let showModal = $state(false);
  let showMediaVault = $state(false);
  let editingId = $state<string | null>(null);

  // Form State
  let form = $state({
    title: "",
    description: "",
    image_url: "",
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
    editingId = null;
    form = {
      title: "",
      description: "",
      image_url: "",
      link_url: "",
      position: "home_main",
      order_index: banners.length,
      is_active: true,
      device_type: "all"
    };
    showModal = true;
  }

  function openEdit(b: Banner) {
    editingId = b.id;
    form = {
      title: b.title,
      description: b.description || "",
      image_url: b.image_url,
      link_url: b.link_url || "",
      position: b.position,
      order_index: b.order_index,
      is_active: b.is_active,
      device_type: b.device_type
    };
    showModal = true;
  }

  async function save() {
    if (!form.title || !form.image_url) {
      nanobot.showToast("Vui lòng nhập tiêu đề và chọn ảnh.", "warning");
      return;
    }

    isSaving = true;
    try {
      if (editingId) {
        await apiClient.put(`/api/v1/banners/${editingId}`, form);
        nanobot.showToast("Đã cập nhật banner.", "success");
      } else {
        await apiClient.post("/api/v1/banners", form);
        nanobot.showToast("Đã tạo banner mới.", "success");
      }
      showModal = false;
      await loadBanners();
    } catch (err) {
      nanobot.showToast("Lưu banner thất bại.", "error");
    } finally {
      isSaving = false;
    }
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
      await loadBanners();
    } catch (err) {
      nanobot.showToast("Xóa banner thất bại.", "error");
    }
  }

  function handleMediaSelect(assets: MediaAsset[]) {
    if (assets.length > 0) {
      // Rule: Assets from FileManager use file_path.
      // We prepend the API URL if it's not a full URL, but typically the UI handles this via proxy.
      // Based on other components, we just store the file_path.
      form.image_url = assets[0].file_path;
    }
    showMediaVault = false;
  }
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
    {#if isLoading}
      <div class="h-full flex flex-col items-center justify-center gap-6">
        <div class="w-16 h-16 border-2 border-cyan-500/10 border-t-cyan-500 rounded-full animate-spin"></div>
        <p class="text-[10px] font-mono text-cyan-400 uppercase tracking-[0.5em] animate-pulse">Syncing Visual Assets...</p>
      </div>
    {:else if banners.length === 0}
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
        {#each banners as b, i}
          <div
            class="group bg-zinc-950/40 border border-white/5 rounded-2xl p-4 flex items-center gap-6 hover:border-cyan-500/30 transition-all duration-500 animate-in slide-in-from-bottom-2"
            style="animation-delay: {i * 0.05}s"
          >
            <!-- Preview -->
            <div class="w-48 aspect-video rounded-xl bg-black border border-white/10 overflow-hidden relative shadow-2xl">
              <img src={b.image_url} alt={b.title} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-1000 opacity-80 group-hover:opacity-100" />
              <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
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

  <!-- Modal Layer -->
  {#if showModal}
    <div
      class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-md"
      transition:fade={{ duration: 200 }}
    >
      <div
        class="w-full max-w-2xl bg-[#0a0a0a] border border-white/10 rounded-3xl overflow-hidden shadow-2xl animate-in zoom-in-95 duration-300"
      >
        <header class="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-zinc-950/40">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
              <Plus size={16} class="text-cyan-400" />
            </div>
            <h2 class="text-sm font-black uppercase tracking-widest">
              {editingId ? 'Modify Strategy' : 'New Deployment'}
            </h2>
          </div>
          <button onclick={() => showModal = false} class="p-2 text-zinc-500 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </header>

        <div class="p-8 space-y-6">
          <div class="grid grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Banner Title</label>
              <input bind:value={form.title} type="text" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-cyan-500/50 outline-none" placeholder="e.g. Summer Sale 2026" />
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Target URL</label>
              <div class="relative">
                <input bind:value={form.link_url} type="text" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-cyan-500/50 outline-none pr-10" placeholder="https://..." />
                <div class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-600"><ExternalLink size={14} /></div>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Visual Asset</label>
            <div
              class="w-full aspect-[21/9] rounded-2xl border border-dashed border-white/10 bg-white/[0.02] flex flex-col items-center justify-center gap-4 relative overflow-hidden group/picker cursor-pointer"
              onclick={() => showMediaVault = true}
            >
              {#if form.image_url}
                <img src={form.image_url} alt="Preview" class="w-full h-full object-cover" />
                <div class="absolute inset-0 bg-black/60 opacity-0 group-hover/picker:opacity-100 flex items-center justify-center transition-all">
                   <div class="px-4 py-2 bg-white text-black text-[9px] font-black uppercase rounded-lg">Update Visual</div>
                </div>
              {:else}
                <div class="w-12 h-12 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400">
                  <Upload size={20} />
                </div>
                <div class="text-center">
                  <p class="text-[9px] font-black uppercase text-zinc-400">Sync with Media Library</p>
                  <p class="text-[7px] text-zinc-600 mt-1 uppercase font-mono">Recommend: 1920x800</p>
                </div>
              {/if}
            </div>
          </div>

          <div class="grid grid-cols-3 gap-6">
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest text-center block">Placement</label>
              <select bind:value={form.position} class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs outline-none">
                {#each POSITIONS as p}
                  <option value={p.id} class="bg-zinc-900">{p.label}</option>
                {/each}
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest text-center block">Device Target</label>
              <div class="flex p-1 bg-black/50 border border-white/5 rounded-xl">
                {#each DEVICES as d}
                  <button
                    onclick={() => form.device_type = d.id}
                    class="flex-1 py-2 flex items-center justify-center rounded-lg transition-all
                      {form.device_type === d.id ? 'bg-white/10 text-cyan-400' : 'text-zinc-600 hover:text-zinc-400'}"
                    title={d.label}
                  >
                    <d.icon size={14} />
                  </button>
                {/each}
              </div>
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest text-center block">Priority Index</label>
              <input bind:value={form.order_index} type="number" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs text-center outline-none" />
            </div>
          </div>
        </div>

        <footer class="px-8 py-6 border-t border-white/5 bg-zinc-950/20 flex items-center justify-between">
          <div class="flex items-center gap-4">
             <button
              onclick={() => form.is_active = !form.is_active}
              class="flex items-center gap-2 group/modtoggle"
             >
               <div class="w-10 h-5 rounded-full transition-colors duration-300 relative {form.is_active ? 'bg-cyan-500' : 'bg-red-500/20'}">
                  <div class="absolute top-1 left-1 w-3 h-3 rounded-full bg-white transition-transform duration-300 {form.is_active ? 'translate-x-5' : ''} shadow-[0_0_8px_rgba(0,255,255,0.4)]"></div>
               </div>
               <span class="text-[9px] font-black uppercase tracking-widest {form.is_active ? 'text-cyan-400' : 'text-red-500'}">
                  {form.is_active ? 'ACTIVE' : 'OFFLINE'}
               </span>
             </button>
          </div>

          <div class="flex items-center gap-4">
            <button onclick={() => showModal = false} class="text-[10px] font-black uppercase text-zinc-500 hover:text-white transition-colors">Discard</button>
            <button
              onclick={save}
              disabled={isSaving}
              class="px-8 py-3 bg-cyan-600 hover:bg-cyan-501 text-black font-black rounded-xl text-[10px] uppercase tracking-widest shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {#if isSaving}
                <RefreshCw size={14} class="animate-spin" />
              {:else}
                <Save size={14} />
              {/if}
              Deploy
            </button>
          </div>
        </footer>
      </div>
    </div>
  {/if}
</div>

{#if showMediaVault}
  <div class="fixed inset-0 z-[200] bg-black/90 backdrop-blur-xl flex flex-col" transition:fade>
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
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='rgba(255,255,255,0.2)'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 1rem center;
    background-size: 1rem;
  }
</style>
