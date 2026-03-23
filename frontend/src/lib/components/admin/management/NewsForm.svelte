<script lang="ts">
  import { slide } from "svelte/transition";
  import { onMount } from "svelte";
  import { 
    X, 
    Globe, 
    FileText, 
    Image, 
    Settings, 
    Trash2, 
    Plus 
  } from "lucide-svelte";
  import MediaVaultModal from "../../media/MediaVaultModal.svelte";
  import { resolveMediaUrl, processContentImages } from "$lib/state/utils";
  import type { MediaAsset } from "$lib/types";

  let {
    editingId,
    formTitle = $bindable(),
    formCategory = $bindable(),
    formStatus = $bindable(),
    formExcerpt = $bindable(),
    formContent = $bindable(),
    formSlug = $bindable(),
    formSeoTitle = $bindable(),
    formSeoDescription = $bindable(),
    formFeaturedImage = $bindable(),
    dbCategories,
    onSave,
    onClose,
    generateSlug,
    isSaving,
    errors,
  } = $props<{
    editingId: string | null;
    formTitle: string;
    formCategory: string;
    formStatus: string;
    formExcerpt: string;
    formContent: string;
    formSlug: string;
    formSeoTitle: string;
    formSeoDescription: string;
    formFeaturedImage: string | null;
    dbCategories: string[];
    onSave: () => void;
    onClose: () => void;
    generateSlug: (title: string) => string;
    isSaving?: boolean;
    errors?: Record<string, string>;
  }>();

  let activeTab = $state("general");
  let newImageUrl = $state("");
  let showMediaModal = $state(false);
  let featuredAssets = $state<string[]>([]);
  let reserve_assets = $state<string[]>([]);
  let selectedAvatarUrl = $state<string | null>(null);
  let selectedAssetIndex = $state(0);

  // CNS V2.2: Reactive Media Resolution for Editor
  // CNS V2.2: Stabilized Image Resolution Logic
  // We avoid re-processing on every keystroke to prevent feedback loops
  let contentAssets = $state<(MediaAsset | string)[]>([]);
  let featuredContextAssets = $state<(MediaAsset | string)[]>([]);

  // V22: Stabilized Image Resolution Logic
  function resolvePlaceholders(html: string) {
    if (!html) return "";
    return processContentImages(html, contentAssets);
  }

  // Extract assets from content on initial load (only if contentAssets is empty)
  $effect(() => {
    if (formContent && contentAssets.length === 0) {
      const imgRegex = /<img[^>]+src=["']([^"']+)["']/g;
      const found: string[] = [];
      let match;
      while ((match = imgRegex.exec(formContent)) !== null) {
        if (match[1] && !found.includes(match[1])) found.push(match[1]);
      }
      if (found.length > 0) {
        contentAssets = found;
      }
    }
  });

  // Effect to resolve placeholders from AI/Legacy content
  $effect(() => {
    if (formContent && formContent.includes("[IMAGE_")) {
      formContent = resolvePlaceholders(formContent);
    }
  });

  // Synergize: Ensure featured image is in the context assets for the modal
  $effect(() => {
    if (formFeaturedImage && featuredContextAssets.length === 0) {
      featuredContextAssets = [formFeaturedImage];
    }
  });

  function setFeaturedImage(url: string) {
    if (!url) return;
    formFeaturedImage = url.trim();
    newImageUrl = "";
    showMediaModal = false;
  }

  function handleMediaSelect(asset: MediaAsset) {
    const url = asset.file_path || asset.url;
    if (url) {
      formFeaturedImage = url;
    }
    showMediaModal = false;
  }

  onMount(() => {
    if (formTitle === undefined) formTitle = "";
    if (formCategory === undefined) formCategory = dbCategories?.[0] || "";
    if (formStatus === undefined) formStatus = "DRAFT";
    if (formExcerpt === undefined) formExcerpt = "";
    if (formContent === undefined) formContent = "";
    if (formSlug === undefined) formSlug = "";
    if (formSeoTitle === undefined) formSeoTitle = "";
    if (formSeoDescription === undefined) formSeoDescription = "";
    if (formFeaturedImage === undefined) formFeaturedImage = null;
  });
</script>

<div
  class="bg-[#050505]/95 md:bg-black/90 md:backdrop-blur-2xl border border-white/10 rounded-[2rem] p-8 flex flex-col gap-8 shadow-[0_30px_100px_rgba(0,0,0,0.8)] my-6 relative overflow-hidden max-w-6xl mx-auto w-full"
  transition:slide={{ duration: 400, axis: "y" }}
>
  <!-- Ambient Effect -->
  <div class="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent opacity-30"></div>
  <div class="absolute -bottom-48 -right-48 w-96 h-96 bg-cyan-500/5 blur-[120px] rounded-full"></div>

  <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-white/5 pb-6">
    <div class="flex flex-col gap-2">
      <div class="text-[10px] font-black text-cyan-400 uppercase tracking-[0.4em] flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></div>
        {editingId ? "Đang đồng bộ tin tức" : "Soạn tin tức mới"}
      </div>
      <h2 class="text-2xl font-bold text-white tracking-tight">{formTitle || "Bản thảo chưa đặt tên"}</h2>
    </div>

    <div class="flex items-center gap-1 bg-white/5 p-1.5 rounded-2xl border border-white/10 overflow-x-auto no-scrollbar">
      {#each [
        { id: "general", label: "Thông tin", icon: Settings },
        { id: "content", label: "Nội dung", icon: FileText },
        { id: "media", label: "Hình ảnh", icon: Image },
        { id: "seo", label: "SEO", icon: Globe }
      ] as tab}
        <button 
          onclick={() => activeTab = tab.id}
          class="flex items-center gap-2 px-4 py-2 text-[10px] font-bold uppercase tracking-widest rounded-xl transition-all whitespace-nowrap {activeTab === tab.id ? 'bg-cyan-500 text-black shadow-[0_0_20px_rgba(6,182,212,0.3)]' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}"
        >
          <tab.icon size={12} />
          {tab.label}
        </button>
      {/each}
    </div>
  </div>

  <div class="min-h-[400px]">
    {#if activeTab === "general"}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8" transition:slide>
        <div class="flex flex-col gap-6">
          <div class="flex flex-col gap-2">
            <label for="news-title" class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Tiêu đề bài viết</label>
            <div class="relative bg-white/[0.03] border {errors?.title ? 'border-red-500/50' : 'border-white/5'} focus-within:border-cyan-500/40 rounded-2xl transition-all shadow-inner">
              <input 
                id="news-title"
                bind:value={formTitle} 
                oninput={() => { if (!editingId) formSlug = generateSlug(formTitle); }}
                placeholder="Nhập tiêu đề..." 
                class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none" 
              />
            </div>
            {#if errors?.title}
              <span class="text-[9px] font-bold text-red-500 ml-2 animate-pulse">{errors.title}</span>
            {/if}
          </div>
          
          <div class="flex flex-col gap-2">
            <label for="news-category" class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Chuyên mục</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-cyan-500/40 rounded-2xl transition-all shadow-inner">
              <select id="news-category" bind:value={formCategory} class="w-full bg-[#0a0a0a] py-4 px-6 text-sm text-gray-300 focus:outline-none rounded-2xl appearance-none">
                {#each dbCategories as c}
                  <option value={c}>{c}</option>
                {/each}
              </select>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-6">
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Trạng thái bài viết</label>
            <div class="flex items-center gap-2 bg-white/5 p-1 rounded-2xl border border-white/10">
              <button onclick={() => formStatus = 'PUBLISHED'} class="flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all {formStatus === 'PUBLISHED' ? 'bg-[#39FF14]/20 text-[#39FF14]' : 'text-gray-500 hover:text-white'}">Công khai</button>
              <button onclick={() => formStatus = 'DRAFT'} class="flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all {formStatus === 'DRAFT' ? 'bg-cyan-500/20 text-cyan-400' : 'text-gray-500 hover:text-white'}">Bản thảo</button>
              <button onclick={() => formStatus = 'ARCHIVED'} class="flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all {formStatus === 'ARCHIVED' ? 'bg-red-500/20 text-red-500' : 'text-gray-500 hover:text-white'}">Lưu trữ</button>
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <label for="news-excerpt" class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Mô tả ngắn (Excerpt)</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-cyan-500/40 rounded-2xl transition-all shadow-inner">
              <textarea id="news-excerpt" bind:value={formExcerpt} placeholder="Tóm tắt nội dung bài viết..." rows="3" class="w-full bg-transparent py-4 px-6 text-sm text-gray-400 focus:outline-none resize-none"></textarea>
            </div>
          </div>
        </div>
      </div>
    {:else if activeTab === "content"}
      <div class="flex flex-col gap-4 h-[600px]" transition:slide>
        <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1 flex items-center gap-2">
          <FileText size={12} /> Nội dung bài viết (Tiptap V2)
        </label>
        <div class="flex-1 rounded-3xl overflow-hidden border border-white/5 bg-black/40">
          <TiptapEditor
            content={formContent}
            bind:assets={contentAssets}
            bind:selectedAvatarUrl={selectedAvatarUrl}
            bind:selectedAssetIndex={selectedAssetIndex}
            onChange={(val) => { formContent = val; }}
            placeholder="Viết nội dung bài viết tại đây..."
          />
        </div>
      </div>
    {:else if activeTab === "media"}
      <div class="flex flex-col gap-6" transition:slide>
        <div class="flex flex-col gap-2">
          <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Ảnh đại diện bài viết</label>
          <div class="max-w-2xl">
            {#if formFeaturedImage && formFeaturedImage.includes('/')}
              <div class="relative group aspect-video rounded-[2rem] overflow-hidden border border-white/10 shadow-2xl bg-black">
                <img
                  src={resolveMediaUrl(formFeaturedImage)}
                  alt="Featured"
                  class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                
                <!-- Hover Overlay Actions -->
                <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center gap-4 backdrop-blur-sm">
                  <button 
                    onclick={() => showMediaModal = true}
                    class="px-6 py-3 bg-white text-black text-[10px] font-black uppercase tracking-widest rounded-xl hover:scale-105 transition-all shadow-2xl"
                  >
                    Thay đổi ảnh
                  </button>
                  <button 
                    onclick={() => formFeaturedImage = null}
                    class="p-3 bg-red-500/20 text-red-500 border border-red-500/20 rounded-xl hover:bg-red-500 hover:text-white transition-all"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>

                <!-- Source Badge -->
                <div class="absolute bottom-4 left-4 px-3 py-1.5 bg-black/50 backdrop-blur-xl border border-white/10 rounded-lg text-[8px] font-bold text-white/60 uppercase tracking-widest">
                  {formFeaturedImage.startsWith('http') ? 'External_Source' : 'Local_Asset'}
                </div>
              </div>
            {:else}
              <button 
                onclick={() => showMediaModal = true}
                class="w-full aspect-video rounded-[2rem] border-2 border-dashed border-white/5 hover:border-cyan-500/30 bg-white/[0.02] hover:bg-cyan-500/[0.02] transition-all flex flex-col items-center justify-center gap-4 group/drop"
              >
                <div class="w-16 h-16 rounded-3xl bg-white/5 flex items-center justify-center group-hover/drop:bg-cyan-500/10 transition-colors">
                  <Image size={32} class="text-cyan-500/50 group-hover/drop:text-cyan-400" />
                </div>
                <div class="flex flex-col items-center gap-1">
                  <span class="text-[11px] font-black text-white/40 group-hover/drop:text-white uppercase tracking-widest">Thêm ảnh đại diện</span>
                  <span class="text-[8px] font-medium text-gray-600 uppercase tracking-widest italic">Hệ thống thư viện & AI Intelligence</span>
                </div>
              </button>
            {/if}
          </div>
        </div>
      </div>
    {:else if activeTab === "seo"}
      <div class="max-w-3xl flex flex-col gap-8" transition:slide>
        <div class="flex flex-col gap-2">
          <label for="news-slug" class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Đường dẫn bài viết (Slug)</label>
          <div class="relative bg-white/[0.03] border {errors?.slug ? 'border-red-500/50' : 'border-white/5'} focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
            <div class="absolute left-6 top-1/2 -translate-y-1/2 text-gray-700 font-mono text-xs">/news/</div>
            <input id="news-slug" bind:value={formSlug} placeholder="slug-bai-viet..." class="w-full bg-transparent py-4 pl-20 pr-6 text-sm text-cyan-400 font-mono focus:outline-none" />
          </div>
          {#if errors?.slug}
            <span class="text-[9px] font-bold text-red-500 ml-2">{errors.slug}</span>
          {/if}
        </div>
        <div class="flex flex-col gap-2">
          <label for="news-seo-title" class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Tiêu đề SEO (Meta Title)</label>
          <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
            <input id="news-seo-title" bind:value={formSeoTitle} placeholder="Nhập tiêu đề SEO..." class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 focus:outline-none" />
            <div class="absolute right-6 top-1/2 -translate-y-1/2 text-[9px] font-mono text-gray-600">{(formSeoTitle || '').length}/60</div>
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label for="news-seo-description" class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Mô tả SEO (Meta Description)</label>
          <div class="relative bg-white/[0.03] border border-white/10 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
            <textarea id="news-seo-description" bind:value={formSeoDescription} placeholder="Nhập mô tả SEO cho bài viết..." rows="4" class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 focus:outline-none resize-none"></textarea>
            <div class="absolute right-6 bottom-4 text-[9px] font-mono text-gray-600">{(formSeoDescription || '').length}/160</div>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <div class="flex items-center justify-end gap-4 mt-8 pt-8 border-t border-white/5">
    <button onclick={onClose} class="px-8 py-4 text-gray-500 hover:text-white text-[10px] font-black uppercase tracking-[0.3em] transition-all">Hủy bỏ</button>
    <button
      onclick={onSave}
      disabled={isSaving}
      class="px-12 py-4 bg-cyan-500 text-black rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] hover:shadow-[0_0_50px_rgba(6,182,212,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-400 shadow-[0_10px_30px_rgba(6,182,212,0.2)] disabled:opacity-50 disabled:grayscale disabled:cursor-not-allowed flex items-center justify-center gap-2"
    >
      {#if isSaving}
        <div class="w-3 h-3 border-2 border-black/20 border-t-black rounded-full animate-spin"></div>
        SYNCING...
      {:else}
        {editingId ? "Cập nhật" : "Đăng tải"}
      {/if}
    </button>
  </div>
</div>

<MediaVaultModal 
  isOpen={showMediaModal} 
  onClose={() => showMediaModal = false}
  bind:assets={featuredContextAssets}
  bind:reserve_assets
  bind:selectedAvatarUrl
  bind:selectedAssetIndex
  onSelect={(url) => { formFeaturedImage = url; showMediaModal = false; }}
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
