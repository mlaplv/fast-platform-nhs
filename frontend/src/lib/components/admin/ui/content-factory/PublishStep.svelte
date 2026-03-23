<script lang="ts">
  import { Pencil, Sparkles } from "lucide-svelte";
  import { onMount } from "svelte";
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import type { CampaignKeywords, MediaAsset, AnalysisCache } from "$lib/state/types";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import { resolveMediaUrl } from "$lib/state/utils";
  import { createPublishController } from "$lib/state/xohiPublish.svelte";
  import { apiClient as defaultClient } from "$lib/utils/apiClient";

  let {
    assets = $bindable(), selectedAvatarUrl = $bindable(), selectedAssetIndex = $bindable(),
    keywords = $bindable(), finalHtml = $bindable(), draft_content = $bindable(), campaign_id,
    apiClient = defaultClient, copyrightScore, seoScore, aiScore
  }: {
    assets: (MediaAsset | string)[]; selectedAvatarUrl: string | null;
    selectedAssetIndex?: number;
    keywords: CampaignKeywords; finalHtml: string; draft_content: string;
    campaign_id: string; apiClient: typeof defaultClient; copyrightScore: number | null;
    seoScore: number | null; aiScore: number | null; analysis_cache?: AnalysisCache;
  } = $props();

  const ctrl = createPublishController({
    getCampaignId: () => campaign_id,
    getKeywords: () => keywords,
    getDraftContent: () => draft_content,
    getFinalHtml: () => finalHtml,
    getAssets: () => assets,
    setSelectedAvatarUrl: (v) => { selectedAvatarUrl = v; },
    setFinalHtml: (v) => { finalHtml = v; },
    getApiClient: () => apiClient
  });

  onMount(() => {
    if (assets === undefined) assets = [];
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
    if (keywords === undefined) keywords = {} as CampaignKeywords;
    if (finalHtml === undefined) finalHtml = "";
    if (draft_content === undefined) draft_content = "";
  });

  $effect(() => {
    ctrl.init();
    if (!selectedAvatarUrl && xohiImageStore.primaryAsset) {
      selectedAvatarUrl = xohiImageStore.primaryAsset.file_path;
    }
  });
</script>

<div class="p-5 md:p-8 space-y-4 flex flex-col">
  <div class="flex items-center gap-3 shrink-0">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">XOHI · <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">NEURAL STUDIO</span></h5>
  </div>

  <div class="shrink-0 flex items-center gap-3 p-3 border-b border-white/5 bg-black/20">
    {#if copyrightScore !== null || seoScore !== null}
      <div class="hidden md:flex items-center gap-2 text-[8px] font-black uppercase">
        {#if copyrightScore !== null}<span class="{copyrightScore >= 90 ? 'text-emerald-400' : 'text-yellow-400'}">COPYRIGHT {copyrightScore}%</span>{/if}
        {#if seoScore !== null}<span class="text-blue-400">SEO {seoScore}</span>{/if}
        {#if aiScore !== null}<span class="text-purple-400">AI {aiScore}%</span>{/if}
      </div>
      <div class="hidden md:block w-px h-4 bg-white/10"></div>
    {/if}

    <div class="relative shrink-0">
      <button 
        class="w-12 h-12 overflow-hidden border border-white/10 hover:border-green-500/40 transition-all" 
        onclick={() => ctrl.showAvatarPicker = !ctrl.showAvatarPicker}
        aria-label="Chọn avatar"
      >
        {#if selectedAvatarUrl}<img src={resolveMediaUrl(selectedAvatarUrl)} alt="avatar" class="w-full h-full object-cover" />
        {:else}<div class="w-full h-full bg-white/5 flex items-center justify-center"><Sparkles size={14} class="text-white/20" /></div>{/if}
      </button>
      {#if ctrl.showAvatarPicker}
        <div class="absolute top-full left-0 mt-1 z-50 w-56 bg-neutral-900 border border-white/10 p-2 shadow-2xl">
          <div class="grid grid-cols-4 gap-1 max-h-32 overflow-y-auto">
            {#each (xohiImageStore.assets.length > 0 ? xohiImageStore.assets : assets) as asset}
              {@const url = typeof asset === 'string' ? asset : asset.url}
              <button 
                class="aspect-square overflow-hidden border {selectedAvatarUrl === url ? 'border-green-500' : 'border-transparent'}" 
                onclick={() => ctrl.selectAvatar(asset)}
                aria-label="Chọn ảnh"
              >
                <img src={resolveMediaUrl(url)} alt="" class="w-full h-full object-cover" />
              </button>
            {/each}
          </div>
          <button onclick={() => ctrl.showAvatarPicker = false} class="w-full mt-1 text-[9px] text-white/30 hover:text-white py-1">Đóng</button>
        </div>
      {/if}
    </div>

    <div class="flex-1 min-w-0">
      {#if ctrl.editingField === 'title'}
        <input type="text" bind:value={keywords.title} onblur={ctrl.saveField} onkeydown={ctrl.handleKeydown} class="w-full bg-white/5 border border-green-500/30 px-2 py-1 text-sm font-bold text-white focus:ring-0" />
      {:else}
        <button 
          class="w-full text-left text-sm font-bold text-white/90 truncate cursor-text hover:text-white block" 
          onclick={() => ctrl.editingField = 'title'}
          ondblclick={() => ctrl.editingField = 'title'}
        >
          {keywords.title || 'Untitled Article'}
        </button>
        <p class="text-[8px] text-white/20 mt-0.5">dblclick để chỉnh tiêu đề • dblclick nội dung để chỉnh bài viết</p>
      {/if}
    </div>
  </div>

  <div 
    class="flex flex-col border-b border-white/5" 
    role="presentation"
  >
    <div class="shrink-0 flex items-center justify-between px-3 py-1.5 bg-white/[0.02] border-b border-white/5">
      <span class="text-[8px] font-black uppercase tracking-widest text-white/30">Nội dung bài viết</span>
      {#if ctrl.editingField === 'content'}<button class="text-[8px] text-purple-400 font-black uppercase animate-pulse" onclick={ctrl.saveField}>● Lưu</button>{/if}
    </div>
    {#if ctrl.editingField === 'content'}
      <div class="flex-1 min-h-0 flex flex-col bg-black/40">
        <TiptapEditor content={ctrl.displayContent} bind:assets bind:selectedAvatarUrl bind:selectedAssetIndex campaignId={campaign_id} onChange={(val) => { if (ctrl.editingField === 'content') finalHtml = val; }} editable={true} placeholder="Nội dung bài viết..." onblur={ctrl.saveField} />
        <div class="shrink-0 p-2 border-t border-white/5 flex justify-end"><button onclick={ctrl.saveField} class="px-3 py-1 bg-purple-500 text-[9px] font-black text-white hover:bg-purple-600 uppercase">Lưu nội dung</button></div>
      </div>
    {:else if ctrl.displayContent}
      <button 
        class="flex-1 min-h-0 flex flex-col overflow-hidden text-left w-full" 
        onclick={() => { if (ctrl.editingField !== 'content') ctrl.editingField = 'content'; }}
      >
        <TiptapEditor content={ctrl.displayContent} bind:assets bind:selectedAvatarUrl bind:selectedAssetIndex campaignId={campaign_id} editable={false} placeholder="Nội dung bài viết..." />
      </button>
    {:else}
      <div class="flex-1 flex flex-col items-center justify-center gap-2 p-4 bg-red-950/20"><span class="text-red-400 text-xs font-bold">⚠ Lỗi tải nội dung</span><code class="text-[9px] text-red-300/50 text-center">draft: {(draft_content || '').length}c | html: {(finalHtml || '').length}c | assets: {assets.length}</code></div>
    {/if}
  </div>

  <div class="shrink-0 grid grid-cols-2 divide-x divide-white/5">
    <div class="p-3 space-y-2">
      <button 
        class="w-full text-left block"
        onclick={() => ctrl.editingField = 'category'}
      >
        <p class="text-[8px] font-black text-blue-400 uppercase tracking-widest mb-1">Category</p>
        {#if ctrl.editingField === 'category'}<input type="text" bind:value={keywords.category} onblur={ctrl.saveField} onkeydown={ctrl.handleKeydown} class="w-full bg-white/5 border border-blue-500/30 px-2 py-0.5 text-xs font-bold text-white focus:ring-0" />
        {:else}<div class="flex items-center justify-between cursor-text group"><span class="text-xs font-bold text-white">{keywords.category || 'Chưa phân loại'}</span><Pencil size={9} class="text-white/10 group-hover:text-blue-400" /></div>{/if}
      </button>
      <button 
        class="w-full text-left block"
        onclick={() => { keywords.slug = keywords.slug || keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'') || 'article-url'; ctrl.editingField = 'slug'; }}
      >
        <p class="text-[8px] font-black text-blue-400 uppercase tracking-widest mb-1">Slug</p>
        {#if ctrl.editingField === 'slug'}<div class="flex items-center gap-1 bg-white/5 border border-blue-500/30 px-2 h-6"><span class="text-[9px] text-white/20">/</span><input type="text" bind:value={keywords.slug} onblur={ctrl.saveField} onkeydown={ctrl.handleKeydown} class="bg-transparent border-none p-0 text-[10px] font-bold text-white focus:ring-0 w-full" /></div>
        {:else}<div class="flex items-center gap-1 cursor-text group"><span class="text-[9px] text-white/20">/</span><span class="text-[10px] font-bold text-white truncate">{keywords.slug || (keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'') || 'article-url')}</span><Pencil size={9} class="text-white/10 group-hover:text-blue-400 ml-auto shrink-0" /></div>{/if}
      </button>
    </div>
    <button 
      class="p-3 flex flex-col text-left" 
      onclick={() => ctrl.editingField = 'description'}
    >
      <div class="flex items-center justify-between mb-1 shrink-0"><p class="text-[8px] font-black text-purple-400 uppercase tracking-widest">Meta SEO</p><span class="text-[8px] text-white/20">{(keywords.description || '').length}/160</span></div>
      {#if ctrl.editingField === 'description'}<textarea bind:value={keywords.description} onblur={ctrl.saveField} rows="3" class="flex-1 bg-black/40 border border-purple-500/30 p-1.5 text-[10px] text-white focus:ring-0 resize-none italic leading-relaxed"></textarea>
      {:else}<p class="text-[10px] text-white/40 leading-relaxed italic line-clamp-3 cursor-text hover:text-white/60">{keywords.description || 'Chưa cập nhật mô tả SEO...'}</p>{/if}
    </button>
  </div>
</div>

<style>
</style>
