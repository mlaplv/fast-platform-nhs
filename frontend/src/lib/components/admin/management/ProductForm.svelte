<script lang="ts">
  import { slide } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import Globe from "lucide-svelte/icons/globe";
  import FileText from "lucide-svelte/icons/file-text";
  import ImageIcon from "lucide-svelte/icons/image";
  import Tag from "lucide-svelte/icons/tag";
  import Settings from "lucide-svelte/icons/settings";
  import Plus from "lucide-svelte/icons/plus";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import TiptapEditor from "../ui/tiptap/TiptapEditor.svelte";
  import MediaVaultModal from "../../media/MediaVaultModal.svelte";
  import { resolveMediaUrl } from "$lib/state/utils";
  import type { MediaAsset } from "$lib/types";

  let {
    editingId,
    formName = $bindable(),
    formSku = $bindable(),
    formPrice = $bindable(),
    formStock = $bindable(),
    formCategory = $bindable(),
    formStatus = $bindable(),
    formDescription = $bindable(),
    formSlug = $bindable(),
    formSeoTitle = $bindable(),
    formSeoDescription = $bindable(),
    formImages = $bindable(),
    formAttributes = $bindable(),
    categories,
    onSave,
    onClose,
    generateSlug,
  } = $props<{
    editingId: string | null;
    formName: string;
    formSku: string;
    formPrice: number;
    formStock: number;
    formCategory: string;
    formStatus: "active" | "draft";
    formDescription: string;
    formSlug: string;
    formSeoTitle: string;
    formSeoDescription: string;
    formImages: string[];
    formAttributes: Record<string, string | number | boolean | null>;
    categories: { id: string; name: string }[];
    onSave: () => void;
    onClose: () => void;
    generateSlug: (name: string) => string;
  }>();

  let activeTab = $state("general");
  let newImageUrl = $state("");
  let newAttrKey = $state("");
  let newAttrValue = $state("");
  let showMediaModal = $state(false);
  let reserve_assets = $state<string[]>([]);
  let selectedAvatarUrl = $state<string | null>(null);
  let selectedAssetIndex = $state(0);

  function addImage() {
    if (newImageUrl.trim()) {
      formImages = [...formImages, newImageUrl.trim()];
      newImageUrl = "";
    }
  }

  function handleMediaSelect(asset: MediaAsset) {
    const url = asset.file_path || asset.url;
    if (url && !formImages.includes(url)) {
      formImages = [...formImages, url];
    }
    showMediaModal = false;
  }

  function removeImage(index: number) {
    formImages = formImages.filter((_, i) => i !== index);
  }

  function addAttribute() {
    if (newAttrKey.trim() && newAttrValue.trim()) {
      formAttributes = { ...formAttributes, [newAttrKey.trim()]: newAttrValue.trim() };
      newAttrKey = "";
      newAttrValue = "";
    }
  }

  function removeAttribute(key: string) {
    const updated = { ...formAttributes };
    delete updated[key];
    formAttributes = updated;
  }
</script>

<div
  class="bg-[#050505]/95 md:bg-black/90 md:backdrop-blur-2xl border border-white/10 rounded-[2rem] p-8 flex flex-col gap-8 shadow-[0_30px_100px_rgba(0,0,0,0.8)] my-6 relative overflow-hidden max-w-6xl mx-auto w-full"
  transition:slide={{ duration: 400, axis: "y" }}
>
  <!-- Ambient Effect -->
  <div class="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#FFB800]/40 to-transparent opacity-30"></div>
  <div class="absolute -bottom-48 -left-48 w-96 h-96 bg-[#FFB800]/5 blur-[120px] rounded-full"></div>

  <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-white/5 pb-6">
    <div class="flex flex-col gap-2">
      <div class="text-[10px] font-black text-[#FFB800] uppercase tracking-[0.4em] flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-[#FFB800] animate-pulse"></div>
        {editingId ? "Sửa đổi thuộc tính sản phẩm" : "Tạo mới sản phẩm"}
      </div>
      <h2 class="text-2xl font-bold text-white tracking-tight">{formName || "Sản phẩm chưa đặt tên"}</h2>
    </div>

    <div class="flex items-center gap-1 bg-white/5 p-1.5 rounded-2xl border border-white/10 overflow-x-auto custom-scrollbar no-scrollbar">
      {#each [
        { id: "general", label: "Thông tin", icon: Settings },
        { id: "content", label: "Mô tả", icon: FileText },
        { id: "media", label: "Hình ảnh", icon: ImageIcon },
        { id: "seo", label: "SEO", icon: Globe },
        { id: "attrs", label: "Thông số", icon: Tag }
      ] as tab}
        <button 
          onclick={() => activeTab = tab.id}
          class="flex items-center gap-2 px-4 py-2 text-[10px] font-bold uppercase tracking-widest rounded-xl transition-all whitespace-nowrap {activeTab === tab.id ? 'bg-[#FFB800] text-black shadow-[0_0_20px_rgba(255,184,0,0.3)]' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}"
        >
          <tab.icon size={12} />
          {tab.label}
        </button>
      {/each}
    </div>
  </div>

  <div class="min-h-[400px]">
    {#if activeTab === "general"}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" transition:slide>
        <div class="flex flex-col gap-6">
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Tên sản phẩm</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-[#FFB800]/40 rounded-2xl transition-all shadow-inner">
              <input 
                bind:value={formName} 
                oninput={() => { if (!editingId) formSlug = generateSlug(formName); }}
                placeholder="Nhập tên sản phẩm..." 
                class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none" 
              />
            </div>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Mã sản phẩm (SKU)</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-[#FFB800]/40 rounded-2xl transition-all shadow-inner">
              <input bind:value={formSku} placeholder="SKU-XXXX..." class="w-full bg-transparent py-4 px-6 text-sm text-[#FFB800] font-mono placeholder:text-gray-700 focus:outline-none uppercase" />
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-6">
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Giá bán (VND)</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-[#FFB800]/40 rounded-2xl transition-all shadow-inner">
              <input type="number" bind:value={formPrice} placeholder="0" class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 font-mono focus:outline-none" />
              <div class="absolute right-6 top-1/2 -translate-y-1/2 text-[10px] text-gray-600 font-bold">VND</div>
            </div>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Tồn kho</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-[#FFB800]/40 rounded-2xl transition-all shadow-inner">
              <input type="number" bind:value={formStock} placeholder="0" class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 font-mono focus:outline-none" />
              <div class="absolute right-6 top-1/2 -translate-y-1/2 text-[10px] text-gray-600 font-bold">SẢN PHẨM</div>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-6">
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Danh mục</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-[#FFB800]/40 rounded-2xl transition-all shadow-inner">
              <select bind:value={formCategory} class="w-full bg-[#0a0a0a] py-4 px-6 text-sm text-gray-300 focus:outline-none rounded-2xl appearance-none">
                <option value="">Chưa phân loại</option>
                {#each categories as cat}
                  <option value={cat.id}>{cat.name}</option>
                {/each}
              </select>
            </div>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Trạng thái hiện thị</label>
            <div class="flex items-center gap-2 bg-white/5 p-1 rounded-2xl border border-white/10">
              <button onclick={() => formStatus = 'active'} class="flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all {formStatus === 'active' ? 'bg-[#39FF14]/20 text-[#39FF14]' : 'text-gray-500 hover:text-white'}">Hoạt động</button>
              <button onclick={() => formStatus = 'draft'} class="flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all {formStatus === 'draft' ? 'bg-[#FFB800]/20 text-[#FFB800]' : 'text-gray-500 hover:text-white'}">Bản thảo</button>
            </div>
          </div>
        </div>
      </div>
    {:else if activeTab === "content"}
      <div class="flex flex-col gap-4 h-[500px]" transition:slide>
        <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1 flex items-center gap-2">
          <FileText size={12} /> Narrative_Rich_Description
        </label>
        <div class="flex-1 rounded-3xl overflow-hidden border border-white/5 bg-black/40">
          <TiptapEditor 
            content={formDescription} 
            onChange={(val) => { formDescription = val; }}
            placeholder="Craft a compelling story for this fashion item..." 
          />
        </div>
      </div>
    {:else if activeTab === "media"}
      <div class="flex flex-col gap-4" transition:slide>
        <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Bộ sưu tập hình ảnh sản phẩm</label>
        
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {#each formImages.filter(img => img && (img.includes('/') || img.startsWith('blob:'))) as img, i}
            <div class="aspect-square rounded-2xl bg-white/5 border border-white/10 relative group overflow-hidden">
              <img src={resolveMediaUrl(img)} alt="Product" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
              <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <button onclick={() => removeImage(i)} class="p-3 bg-red-500/20 text-red-500 rounded-full hover:bg-red-500 hover:text-white transition-all">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          {/each}
          
          <!-- Add Image Card -->
          <button 
            onclick={() => showMediaModal = true}
            class="aspect-square rounded-2xl border-2 border-dashed border-white/5 hover:border-amber-500/30 bg-white/[0.02] hover:bg-amber-500/[0.02] transition-all flex flex-col items-center justify-center gap-2 group/add"
          >
            <Plus size={24} class="text-amber-500/50 group-hover/add:text-amber-400 transition-colors" />
            <span class="text-[9px] font-black text-white/40 group-hover/add:text-white uppercase tracking-widest">Thêm hình</span>
          </button>
        </div>

        {#if formImages.length === 0}
          <div class="py-10 border border-white/5 rounded-3xl flex flex-col items-center justify-center opacity-30 mt-4">
            <ImageIcon size={32} class="mb-3 text-amber-500/50" />
            <div class="text-[9px] font-bold uppercase tracking-[0.2em]">Chưa có hình ảnh được chọn</div>
          </div>
        {/if}
      </div>
    {:else if activeTab === "seo"}
      <div class="max-w-3xl flex flex-col gap-8" transition:slide>
        <div class="flex flex-col gap-2">
          <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Đường dẫn sản phẩm (Slug)</label>
          <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
            <div class="absolute left-6 top-1/2 -translate-y-1/2 text-gray-700 font-mono text-xs">/products/</div>
            <input bind:value={formSlug} placeholder="slug-san-pham..." class="w-full bg-transparent py-4 pl-24 pr-6 text-sm text-blue-400 font-mono focus:outline-none" />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Tiêu đề SEO</label>
          <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
            <input bind:value={formSeoTitle} placeholder="Nhập tiêu đề SEO..." class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 focus:outline-none" />
            <div class="absolute right-6 top-1/2 -translate-y-1/2 text-[9px] font-mono text-gray-600">{formSeoTitle.length}/60</div>
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Mô tả SEO</label>
          <div class="relative bg-white/[0.03] border border-white/10 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
            <textarea bind:value={formSeoDescription} placeholder="Nhập mô tả SEO cho sản phẩm..." rows="4" class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 focus:outline-none resize-none"></textarea>
            <div class="absolute right-6 bottom-4 text-[9px] font-mono text-gray-600">{formSeoDescription.length}/160</div>
          </div>
        </div>
      </div>
    {:else if activeTab === "attrs"}
      <div class="flex flex-col gap-8" transition:slide>
        <div class="flex flex-col gap-4">
          <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1 text-purple-400">Add_Technical_Specification</label>
          <div class="flex gap-3">
            <input bind:value={newAttrKey} placeholder="Key (e.g. Size, Color)..." class="flex-1 bg-white/[0.03] border border-white/5 rounded-2xl py-4 px-6 text-sm text-purple-400 font-mono focus:border-purple-500/40 focus:outline-none" />
            <input bind:value={newAttrValue} placeholder="Value (e.g. Medium, Crimson)..." class="flex-1 bg-white/[0.03] border border-white/5 rounded-2xl py-4 px-6 text-sm text-gray-200 focus:border-purple-500/40 focus:outline-none" />
            <button onclick={addAttribute} class="px-8 py-4 bg-purple-500/10 hover:bg-purple-500 text-purple-500 hover:text-white rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">Inject_Spec</button>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each Object.entries(formAttributes) as [key, val]}
            <div class="flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-2xl group">
              <div class="flex flex-col">
                <span class="text-[9px] font-black text-purple-400 uppercase tracking-widest">{key}</span>
                <span class="text-sm text-white font-medium">{val}</span>
              </div>
              <button onclick={() => removeAttribute(key)} class="p-2 text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all">
                <Trash2 size={14} />
              </button>
            </div>
          {/each}
          {#if Object.keys(formAttributes).length === 0}
            <div class="col-span-full py-20 border-2 border-dashed border-white/5 rounded-3xl flex flex-col items-center justify-center opacity-30">
              <Tag size={48} class="mb-4" />
              <div class="text-[10px] font-bold uppercase tracking-[0.3em]">No_Specs_Found_In_System</div>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>

  <div class="flex items-center justify-end gap-4 mt-8 pt-8 border-t border-white/5">
    <button onclick={onClose} class="px-8 py-4 text-gray-500 hover:text-white text-[10px] font-black uppercase tracking-[0.3em] transition-all">Hủy bỏ</button>
    <button
      onclick={onSave}
      class="px-12 py-4 bg-[#FFB800] text-black rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] hover:shadow-[0_0_50px_rgba(255,184,0,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-400 shadow-[0_10px_30px_rgba(255,184,0,0.2)]"
    >
      {editingId ? "Cập nhật" : "Lưu sản phẩm"}
    </button>
  </div>
</div>

<MediaVaultModal 
  isOpen={showMediaModal} 
  onClose={() => showMediaModal = false}
  bind:assets={formImages}
  bind:reserve_assets
  bind:selectedAvatarUrl
  bind:selectedAssetIndex
/>

<style>
  :global(.tiptap-shell) {
    @apply border-none !bg-transparent;
  }
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  @keyframes rotate-slow {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  .animate-rotate-slow {
    animation: rotate-slow 8s linear infinite;
  }
</style>
