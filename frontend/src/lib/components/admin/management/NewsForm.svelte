<script lang="ts">
  import { slide } from "svelte/transition";
  import XIcon from "lucide-svelte/icons/x";
  import GlobeIcon from "lucide-svelte/icons/globe";
  import FileTextIcon from "lucide-svelte/icons/file-text";
  import ImageIcon from "lucide-svelte/icons/image";
  import SettingsIcon from "lucide-svelte/icons/settings";
  import Trash2Icon from "lucide-svelte/icons/trash-2";
  import TiptapEditor from "../ui/tiptap/TiptapEditor.svelte";
  import PlusIcon from "lucide-svelte/icons/plus";
  import MediaVaultModal from "../../media/MediaVaultModal.svelte";
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
  }>();

  let activeTab = $state("general");
  let newImageUrl = $state("");
  let showMediaModal = $state(false);
  let featuredAssets = $state<string[]>([]);
  let reserve_assets = $state<string[]>([]);
  let selectedAvatarUrl = $state<string | null>(null);
  let selectedAssetIndex = $state(0);

  $effect(() => {
    if (formFeaturedImage && featuredAssets.length === 0) {
      featuredAssets = [formFeaturedImage];
    }
  });

  $effect(() => {
    if (featuredAssets.length > 0) {
      formFeaturedImage = featuredAssets[0];
    } else {
      formFeaturedImage = null;
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
        {editingId ? "Article Neural Sync Active" : "Prepare New Intelligence"}
      </div>
      <h2 class="text-2xl font-bold text-white tracking-tight">{formTitle || "Untitled_Draft"}</h2>
    </div>

    <div class="flex items-center gap-1 bg-white/5 p-1.5 rounded-2xl border border-white/10 overflow-x-auto no-scrollbar">
      {#each [
        { id: "general", label: "General", icon: SettingsIcon },
        { id: "content", label: "Narrative", icon: FileTextIcon },
        { id: "media", label: "Media", icon: ImageIcon },
        { id: "seo", label: "SEO", icon: GlobeIcon }
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
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Title_Header</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-cyan-500/40 rounded-2xl transition-all shadow-inner">
              <input 
                bind:value={formTitle} 
                oninput={() => { if (!editingId) formSlug = generateSlug(formTitle); }}
                placeholder="Article title..." 
                class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none" 
              />
            </div>
          </div>
          
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Classification_Node</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-cyan-500/40 rounded-2xl transition-all shadow-inner">
              <select bind:value={formCategory} class="w-full bg-[#0a0a0a] py-4 px-6 text-sm text-gray-300 focus:outline-none rounded-2xl appearance-none">
                {#each dbCategories as c}
                  <option value={c}>{c}</option>
                {/each}
              </select>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-6">
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Status_Control</label>
            <div class="flex items-center gap-2 bg-white/5 p-1 rounded-2xl border border-white/10">
              <button onclick={() => formStatus = 'PUBLISHED'} class="flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all {formStatus === 'PUBLISHED' ? 'bg-[#39FF14]/20 text-[#39FF14]' : 'text-gray-500 hover:text-white'}">Live</button>
              <button onclick={() => formStatus = 'DRAFT'} class="flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all {formStatus === 'DRAFT' ? 'bg-cyan-500/20 text-cyan-400' : 'text-gray-500 hover:text-white'}">Draft</button>
              <button onclick={() => formStatus = 'ARCHIVED'} class="flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all {formStatus === 'ARCHIVED' ? 'bg-red-500/20 text-red-500' : 'text-gray-500 hover:text-white'}">Archive</button>
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Brief_Excerpt</label>
            <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-cyan-500/40 rounded-2xl transition-all shadow-inner">
              <textarea bind:value={formExcerpt} placeholder="Summarize this intelligence..." rows="3" class="w-full bg-transparent py-4 px-6 text-sm text-gray-400 focus:outline-none resize-none"></textarea>
            </div>
          </div>
        </div>
      </div>
    {:else if activeTab === "content"}
      <div class="flex flex-col gap-4 h-[600px]" transition:slide>
        <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1 flex items-center gap-2">
          <FileTextIcon size={12} /> Detailed_Content_Stream (Tiptap_V2)
        </label>
        <div class="flex-1 rounded-3xl overflow-hidden border border-white/5 bg-black/40">
          <TiptapEditor bind:content={formContent} placeholder="Inject your knowledge stream here..." />
        </div>
      </div>
    {:else if activeTab === "media"}
      <div class="flex flex-col gap-8" transition:slide>
         <button 
           onclick={(e) => { e.preventDefault(); showMediaModal = true; }}
           class="w-fit relative group/btn overflow-hidden rounded-[1.8rem] p-[1px] transition-all duration-500 hover:scale-[1.01] active:scale-95 shadow-2xl"
         >
           <div class="absolute inset-0 bg-gradient-to-r from-cyan-500 via-blue-400 to-cyan-500 animate-rotate-slow opacity-20 group-hover/btn:opacity-100 transition-opacity"></div>
           <div class="relative h-full w-full bg-[#0a0a0a] rounded-[calc(1.8rem-1px)] py-5 px-8 flex items-center justify-center gap-4 border border-white/5">
             <div class="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center group-hover/btn:bg-cyan-500/20 transition-colors">
               <PlusIcon size={20} class="text-cyan-400" />
             </div>
             <div class="flex flex-col items-start">
               <span class="text-[11px] font-black text-white uppercase tracking-[0.2em]">Open MEDIA INTELLIGENCE</span>
               <span class="text-[7px] font-mono text-cyan-400/40 uppercase tracking-widest mt-0.5">Manage Neural_Assets</span>
             </div>
           </div>
         </button>

        <div class="max-w-md">
          {#if formFeaturedImage && formFeaturedImage.includes('/')}
            <div class="aspect-video rounded-3xl bg-white/5 border border-white/10 relative group overflow-hidden">
              <img src={formFeaturedImage} alt="Featured" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
              <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <button onclick={() => formFeaturedImage = null} class="p-4 bg-red-500/20 text-red-500 rounded-full hover:bg-red-500 hover:text-white transition-all shadow-2xl">
                  <Trash2Icon size={20} />
                </button>
              </div>
            </div>
          {:else}
            <div class="aspect-video border-2 border-dashed border-white/5 rounded-3xl flex flex-col items-center justify-center opacity-30">
              <ImageIcon size={48} class="mb-4 text-cyan-500" />
              <div class="text-[10px] font-bold uppercase tracking-[0.3em]">No_Visual_Cover_Attached</div>
            </div>
          {/if}
        </div>
      </div>
    {:else if activeTab === "seo"}
      <div class="max-w-3xl flex flex-col gap-8" transition:slide>
        <div class="flex flex-col gap-2">
          <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Semantic_Route (Slug)</label>
          <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
            <div class="absolute left-6 top-1/2 -translate-y-1/2 text-gray-700 font-mono text-xs">/intel/</div>
            <input bind:value={formSlug} placeholder="slug-path..." class="w-full bg-transparent py-4 pl-20 pr-6 text-sm text-blue-400 font-mono focus:outline-none" />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Meta_Search_Title</label>
          <div class="relative bg-white/[0.03] border border-white/5 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
            <input bind:value={formSeoTitle} placeholder={formTitle} class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 focus:outline-none" />
            <div class="absolute right-6 top-1/2 -translate-y-1/2 text-[9px] font-mono text-gray-600">{(formSeoTitle || '').length}/60</div>
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Meta_Search_Description</label>
          <div class="relative bg-white/[0.03] border border-white/10 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
            <textarea bind:value={formSeoDescription} placeholder="Intelligence snippet for indexers..." rows="4" class="w-full bg-transparent py-4 px-6 text-sm text-gray-100 focus:outline-none resize-none"></textarea>
            <div class="absolute right-6 bottom-4 text-[9px] font-mono text-gray-600">{(formSeoDescription || '').length}/160</div>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <div class="flex items-center justify-end gap-4 mt-8 pt-8 border-t border-white/5">
    <button onclick={onClose} class="px-8 py-4 text-gray-500 hover:text-white text-[10px] font-black uppercase tracking-[0.3em] transition-all">Purge_Draft</button>
    <button
      onclick={onSave}
      class="px-12 py-4 bg-cyan-500 text-black rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] hover:shadow-[0_0_50px_rgba(6,182,212,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-400 shadow-[0_10px_30px_rgba(6,182,212,0.2)]"
    >
      {editingId ? "Update_Intelligence" : "Deploy_Intelligence"}
    </button>
  </div>
</div>

<MediaVaultModal 
  isOpen={showMediaModal} 
  onClose={() => showMediaModal = false}
  bind:assets={featuredAssets}
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
