<script lang="ts">
  import { slide } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import Globe from "lucide-svelte/icons/globe";
  import FileText from "lucide-svelte/icons/file-text";
  import ImageIcon from "lucide-svelte/icons/image";
  import TiptapEditor from "../ui/tiptap/TiptapEditor.svelte";

  let {
    editingId,
    formParentId,
    formName = $bindable(),
    formSlug = $bindable(),
    formDescription = $bindable(),
    formSeoTitle = $bindable(),
    formSeoDescription = $bindable(),
    formImage = $bindable(),
    onSave,
    onClose,
    generateSlug,
  } = $props<{
    editingId: string | null;
    formParentId: string | null;
    formName: string;
    formSlug: string;
    formDescription: string;
    formSeoTitle: string;
    formSeoDescription: string;
    formImage: string;
    onSave: () => void;
    onClose: () => void;
    generateSlug: (name: string) => string;
  }>();

  let activeTab = $state("general");
</script>

<div
  class="bg-[#050505]/95 md:bg-black/80 md:backdrop-blur-xl border border-[#00FFFF]/30 rounded-3xl p-6 flex flex-col gap-6 shadow-[0_20px_50px_rgba(0,0,0,0.7)] my-4 relative overflow-hidden max-w-5xl mx-auto w-full"
  transition:slide={{ duration: 400, axis: "y" }}
>
  <!-- Ambient Background Effect -->
  <div class="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#00FFFF]/50 to-transparent opacity-30"></div>
  <div class="absolute -top-24 -right-24 w-48 h-48 bg-[#00FFFF]/5 blur-[100px] rounded-full"></div>

  <div class="flex items-center justify-between border-b border-white/5 pb-4">
    <div class="flex flex-col gap-1">
      <div class="text-[10px] font-bold text-[#00FFFF] uppercase tracking-[0.3em] flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-[#00FFFF] animate-pulse"></div>
        {editingId ? "Modify Taxonomy Node" : "Initialize Taxonomy Node"}
      </div>
      {#if formParentId}
        <div class="text-gray-500 font-mono text-[9px] uppercase tracking-wider">
          Inheriting from parent scope: <span class="text-[#00FFFF]/60">{formParentId}</span>
        </div>
      {/if}
    </div>

    <div class="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/10">
      <button 
        onclick={() => activeTab = "general"}
        class="px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded-lg transition-all {activeTab === 'general' ? 'bg-[#00FFFF]/20 text-[#00FFFF]' : 'text-gray-500 hover:text-gray-300'}"
      >General</button>
      <button 
        onclick={() => activeTab = "seo"}
        class="px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded-lg transition-all {activeTab === 'seo' ? 'bg-[#00FFFF]/20 text-[#00FFFF]' : 'text-gray-500 hover:text-gray-300'}"
      >SEO_Engine</button>
    </div>
  </div>

  <div class="flex flex-col gap-6">
    {#if activeTab === "general"}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6" transition:slide>
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Name_Identifier</label>
            <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-[#00FFFF]/40 rounded-2xl transition-all shadow-inner">
              <input
                bind:value={formName}
                oninput={() => { if (!editingId) formSlug = generateSlug(formName); }}
                placeholder="Enter category name..."
                class="w-full bg-transparent py-3.5 px-5 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none"
              />
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1">Slug_Reference</label>
            <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-[#00FFFF]/40 rounded-2xl transition-all shadow-inner">
              <div class="absolute left-4 top-1/2 -translate-y-1/2 text-[10px] text-[#00FFFF]/40 font-mono">/</div>
              <input
                bind:value={formSlug}
                placeholder="slug-path..."
                class="w-full bg-transparent py-3.5 pl-8 pr-5 text-sm text-[#00FFFF] font-mono placeholder:text-gray-700 focus:outline-none"
              />
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1 flex items-center gap-2">
              <ImageIcon size={10} /> Banner_Asset_URL
            </label>
            <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-[#00FFFF]/40 rounded-2xl transition-all shadow-inner">
              <input
                bind:value={formImage}
                placeholder="https://assets.xohi.io/banners/..."
                class="w-full bg-transparent py-3.5 px-5 text-xs text-gray-400 font-mono placeholder:text-gray-700 focus:outline-none"
              />
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-2 h-full">
          <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1 flex items-center gap-2">
            <FileText size={10} /> Rich_Description
          </label>
          <div class="flex-1 min-h-[180px] rounded-2xl overflow-hidden border border-white/5 focus-within:border-[#00FFFF]/20 transition-all">
            <TiptapEditor 
              bind:content={formDescription}
              placeholder="Describe this category for your customers and search engines..."
            />
          </div>
        </div>
      </div>
    {:else}
      <div class="grid grid-cols-1 gap-6" transition:slide>
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1 flex items-center gap-2 text-blue-400">
              <Globe size={10} /> Meta_Title_Override
            </label>
            <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
              <input
                bind:value={formSeoTitle}
                placeholder={formName || "Meta title..."}
                class="w-full bg-transparent py-3.5 px-5 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none"
              />
              <div class="absolute right-4 top-1/2 -translate-y-1/2 text-[9px] font-mono text-gray-600">{formSeoTitle.length}/60</div>
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <label class="text-[9px] font-bold text-gray-500 uppercase tracking-widest ml-1 flex items-center gap-2 text-purple-400">
              Meta_Description_Snippet
            </label>
            <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-purple-500/40 rounded-2xl transition-all shadow-inner">
              <textarea
                bind:value={formSeoDescription}
                placeholder="Brief summary for Google results..."
                rows="3"
                class="w-full bg-transparent py-3.5 px-5 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none resize-none"
              ></textarea>
              <div class="absolute right-4 bottom-3 text-[9px] font-mono text-gray-600">{formSeoDescription.length}/160</div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <div class="flex items-center justify-end gap-3 mt-4 pt-6 border-t border-white/5">
    <button
      onclick={onClose}
      class="px-6 py-3 text-gray-500 hover:text-white text-[10px] font-bold uppercase tracking-widest transition-all"
    >Abort_Changes</button>
    <button
      onclick={onSave}
      class="px-10 py-3 bg-[#00FFFF] text-black rounded-xl text-[10px] font-black uppercase tracking-[0.2em] hover:shadow-[0_0_30px_rgba(0,255,255,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-300"
    >
      {editingId ? "Sync_Node_State" : "Deploy_Taxonomy"}
    </button>
  </div>
</div>

<style>
  :global(.tiptap-shell) {
    @apply border-none !bg-transparent;
  }
</style>
