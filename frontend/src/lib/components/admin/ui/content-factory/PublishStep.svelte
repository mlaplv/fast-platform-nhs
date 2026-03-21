<script lang="ts">
  import { Pencil, Sparkles } from "lucide-svelte";
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import type { CampaignKeywords, MediaAsset, AnalysisCache } from "$lib/state/types";
  import type { CopyrightResult, SEOResult, AIInspectResult } from "$lib/types";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import { purifyAIContent } from "$lib/utils/purify";
  import { resolveMediaUrl, processContentImages } from "$lib/state/utils";

  interface Props {
    assets: (MediaAsset | string)[];
    selectedAvatarUrl: string | null;
    viewingStep: number;
    isEditing: boolean;
    keywords: CampaignKeywords;
    finalHtml: string;
    draft_content: string;
    campaign_id: string;
    apiClient: typeof import('$lib/utils/apiClient').apiClient;
    copyrightScore: number;
    seoScore: number;
    aiScore: number;
    analysis_cache: AnalysisCache;
  }

  let {
    assets = [],
    selectedAvatarUrl = $bindable(),
    viewingStep = $bindable(),
    isEditing = $bindable(),
    keywords = $bindable(),
    finalHtml = $bindable(),
    draft_content = $bindable(),
    campaign_id,
    apiClient,
    copyrightScore,
    seoScore,
    aiScore,
    analysis_cache = {}
  }: Props = $props();

  let editingField = $state<string | null>(null);
  let showAvatarPicker = $state(false);

  // Phase 15.3: Sync local assets to store if needed
  $effect(() => {
    if (assets.length > 0 && xohiImageStore.assets.length === 0) {
      xohiImageStore.initAssets(assets.map((a, i) =>
        typeof a === 'string' ? { id: `img_${i}`, url: a, is_primary: i === 0, order_index: i } : a
      ));
    }
  });

  // finalHtml: đã qua MediaCompressor (ảnh local) → ưu tiên trước
  // draft_content: bản raw từ AI → fallback
  let displayContent = $derived.by(() => {
    const base = finalHtml || draft_content || "";
    const currentAssets = xohiImageStore.assets.length > 0 ? xohiImageStore.assets : assets;
    return processContentImages(base, currentAssets);
  });

  $effect(() => {
    if (!selectedAvatarUrl && xohiImageStore.primaryAsset) {
      selectedAvatarUrl = xohiImageStore.primaryAsset.url;
    } else if (!selectedAvatarUrl && assets.length > 0) {
      const first = assets[0];
      selectedAvatarUrl = typeof first === 'string' ? first : first.url;
    }
  });

  async function saveField() {
    editingField = null;
    try {
      // Phase 15.3: Save processed displayContent to final_html to ensure images are resolved
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, {
        keywords,
        draft_content,
        final_html: displayContent
      });
    } catch (e) { console.error("Save failed", e); }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') saveField();
    if (e.key === 'Escape') editingField = null;
  }

  async function selectAvatar(asset: MediaAsset | string) {
    const assetId = typeof asset === 'string' ? null : asset.id;
    const url = typeof asset === 'string' ? asset : asset.url;

    selectedAvatarUrl = url;
    if (assetId) {
      xohiImageStore.swapPrimary(assetId);
    }

    showAvatarPicker = false;
    try {
      // Phase 15.3: Đồng bộ toàn bộ state ảnh mới khi đổi avatar
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, {
        assets: xohiImageStore.assets,
        avatar: url
      });
    } catch (e) {}
  }
</script>

<!--
  PATTERN: flex-1 min-h-0 overflow-hidden flex flex-col
  - Lấp đầy không gian ContentReviewCard cấp (overflow-hidden)
  - Không tràn ra ngoài
  - 3 phần: [shrink-0 header] [flex-1 scroll content] [shrink-0 footer]
-->
<div class="p-5 md:p-8 space-y-4 flex flex-col">
  <!-- Studio Label -->
  <div class="flex items-center gap-3 shrink-0">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">
      XOHI ·
      <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">NEURAL STUDIO</span>
    </h5>
  </div>

  <!-- ===== HEADER: Title + Avatar (cố định, không co giãn) ===== -->
  <div class="shrink-0 flex items-center gap-3 p-3 border-b border-white/5 bg-black/20">

    <!-- Scores mini -->
    {#if copyrightScore !== null || seoScore !== null}
      <div class="hidden md:flex items-center gap-2 text-[8px] font-black uppercase">
        {#if copyrightScore !== null}
          <span class="{copyrightScore >= 90 ? 'text-emerald-400' : 'text-yellow-400'}">COPYRIGHT {copyrightScore}%</span>
        {/if}
        {#if seoScore !== null}
          <span class="text-blue-400">SEO {seoScore}</span>
        {/if}
        {#if aiScore !== null}
          <span class="text-purple-400">AI {aiScore}%</span>
        {/if}
      </div>
      <div class="hidden md:block w-px h-4 bg-white/10"></div>
    {/if}

    <!-- Avatar -->
    <div class="relative shrink-0">
      <button
        class="w-12 h-12 overflow-hidden border border-white/10 hover:border-green-500/40 transition-all"
        onclick={() => showAvatarPicker = !showAvatarPicker}
      >
        {#if selectedAvatarUrl}
          <img src={resolveMediaUrl(selectedAvatarUrl)} alt="avatar" class="w-full h-full object-cover" />
        {:else}
          <div class="w-full h-full bg-white/5 flex items-center justify-center">
            <Sparkles size={14} class="text-white/20" />
          </div>
        {/if}
      </button>

      {#if showAvatarPicker}
        <div class="absolute top-full left-0 mt-1 z-50 w-56 bg-neutral-900 border border-white/10 p-2 shadow-2xl">
          <div class="grid grid-cols-4 gap-1 max-h-32 overflow-y-auto">
            {#each (xohiImageStore.assets.length > 0 ? xohiImageStore.assets : assets) as asset}
              {@const url = typeof asset === 'string' ? asset : asset.url}
              <button class="aspect-square overflow-hidden border {selectedAvatarUrl === url ? 'border-green-500' : 'border-transparent'}"
                onclick={() => selectAvatar(asset)}>
                <img src={resolveMediaUrl(url)} alt="" class="w-full h-full object-cover" />
              </button>
            {/each}
          </div>
          <button onclick={() => showAvatarPicker = false} class="w-full mt-1 text-[9px] text-white/30 hover:text-white py-1">Đóng</button>
        </div>
      {/if}
    </div>

    <!-- Title -->
    <div class="flex-1 min-w-0">
      {#if editingField === 'title'}
        <input type="text" autofocus bind:value={keywords.title}
          onblur={saveField} onkeydown={handleKeydown}
          class="w-full bg-white/5 border border-green-500/30 px-2 py-1 text-sm font-bold text-white focus:ring-0"
        />
      {:else}
        <h2 class="text-sm font-bold text-white/90 truncate cursor-text hover:text-white"
          ondblclick={() => editingField = 'title'}
        >{keywords.title || 'Untitled Article'}</h2>
        <p class="text-[8px] text-white/20 mt-0.5">dblclick để chỉnh tiêu đề • dblclick nội dung để chỉnh bài viết</p>
      {/if}
    </div>
  </div>

  <!-- ===== MIDDLE: Article Content (chiếm toàn bộ không gian còn lại) ===== -->
  <div class="flex flex-col border-b border-white/5"
    ondblclick={() => { if (editingField !== 'content') editingField = 'content'; }}
  >
    <!-- Sub-header -->
    <div class="shrink-0 flex items-center justify-between px-3 py-1.5 bg-white/[0.02] border-b border-white/5">
      <span class="text-[8px] font-black uppercase tracking-widest text-white/30">Nội dung bài viết</span>
      {#if editingField === 'content'}
        <button class="text-[8px] text-purple-400 font-black uppercase animate-pulse" onclick={saveField}>● Lưu</button>
      {/if}
    </div>

    <!-- Actual content: flex-1 overflow-y-auto -->
    {#if editingField === 'content'}
      <div class="flex-1 min-h-0 flex flex-col bg-black/40">
        <TiptapEditor
          content={displayContent}
          assets={assets}
          campaignId={campaign_id}
          onChange={(val) => {
            if (editingField === 'content') finalHtml = val; // Assuming isEditing refers to editingField === 'content'
          }}
          editable={editingField === 'content'} // Assuming isEditing refers to editingField === 'content'
          placeholder="Nội dung bài viết..."
          onblur={saveField}
        />
        <div class="shrink-0 p-2 border-t border-white/5 flex justify-end">
          <button onclick={saveField}
            class="px-3 py-1 bg-purple-500 text-[9px] font-black text-white hover:bg-purple-600 uppercase"
          >Lưu nội dung</button>
        </div>
      </div>
    {:else if displayContent}
      <div class="flex-1 min-h-0 flex flex-col overflow-hidden">
        <TiptapEditor
          content={displayContent}
          assets={assets}
          campaignId={campaign_id}
          editable={false}
          placeholder="Nội dung bài viết..."
        />
      </div>
    {:else}
      <div class="flex-1 flex flex-col items-center justify-center gap-2 p-4 bg-red-950/20">
        <span class="text-red-400 text-xs font-bold">⚠ Lỗi tải nội dung</span>
        <code class="text-[9px] text-red-300/50 text-center">
          draft: {(draft_content || '').length}c | html: {(finalHtml || '').length}c | assets: {assets.length}
        </code>
      </div>
    {/if}
  </div>

  <!-- ===== FOOTER: Category/Slug + Meta (cố định ở dưới) ===== -->
  <div class="shrink-0 grid grid-cols-2 divide-x divide-white/5">
    
    <!-- Category & Slug -->
    <div class="p-3 space-y-2">
      <div ondblclick={() => editingField = 'category'}>
        <p class="text-[8px] font-black text-blue-400 uppercase tracking-widest mb-1">Category</p>
        {#if editingField === 'category'}
          <input type="text" autofocus bind:value={keywords.category}
            onblur={saveField} onkeydown={handleKeydown}
            class="w-full bg-white/5 border border-blue-500/30 px-2 py-0.5 text-xs font-bold text-white focus:ring-0"
          />
        {:else}
          <div class="flex items-center justify-between cursor-text group">
            <span class="text-xs font-bold text-white">{keywords.category || 'Chưa phân loại'}</span>
            <Pencil size={9} class="text-white/10 group-hover:text-blue-400" />
          </div>
        {/if}
      </div>

      <div ondblclick={() => {
        keywords.slug = keywords.slug || keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'') || 'article-url';
        editingField = 'slug';
      }}>
        <p class="text-[8px] font-black text-blue-400 uppercase tracking-widest mb-1">Slug</p>
        {#if editingField === 'slug'}
          <div class="flex items-center gap-1 bg-white/5 border border-blue-500/30 px-2 h-6">
            <span class="text-[9px] text-white/20">/</span>
            <input type="text" autofocus bind:value={keywords.slug}
              onblur={saveField} onkeydown={handleKeydown}
              class="bg-transparent border-none p-0 text-[10px] font-bold text-white focus:ring-0 w-full"
            />
          </div>
        {:else}
          <div class="flex items-center gap-1 cursor-text group">
            <span class="text-[9px] text-white/20">/</span>
            <span class="text-[10px] font-bold text-white truncate">{keywords.slug || (keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'') || 'article-url')}</span>
            <Pencil size={9} class="text-white/10 group-hover:text-blue-400 ml-auto shrink-0" />
          </div>
        {/if}
      </div>
    </div>

    <!-- Meta Description -->
    <div class="p-3 flex flex-col" ondblclick={() => editingField = 'description'}>
      <div class="flex items-center justify-between mb-1 shrink-0">
        <p class="text-[8px] font-black text-purple-400 uppercase tracking-widest">Meta SEO</p>
        <span class="text-[8px] text-white/20">{(keywords.description || '').length}/160</span>
      </div>
      {#if editingField === 'description'}
        <textarea autofocus bind:value={keywords.description}
          onblur={saveField} rows="3"
          class="flex-1 bg-black/40 border border-purple-500/30 p-1.5 text-[10px] text-white focus:ring-0 resize-none italic leading-relaxed"
        ></textarea>
      {:else}
        <p class="text-[10px] text-white/40 leading-relaxed italic line-clamp-3 cursor-text hover:text-white/60">
          {keywords.description || 'Chưa cập nhật mô tả SEO...'}
        </p>
      {/if}
    </div>
  
  </div>

</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); border-radius: 0; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.12); }
</style>
