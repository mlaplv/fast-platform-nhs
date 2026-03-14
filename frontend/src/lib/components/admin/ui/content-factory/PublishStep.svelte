<script lang="ts">
  import {
    Edit2,
    RotateCcw,
    Sparkles
  } from "lucide-svelte";
  import RichTextEditor from "../RichTextEditor.svelte";

  let {
    assets = [],
    selectedAvatarUrl = $bindable(null),
    viewingStep = $bindable(6),
    isEditing = $bindable(false),
    keywords = $bindable({}),
    finalHtml = $bindable(),
    draft_content = $bindable(),
    campaign_id,
    apiClient,
    copyrightScore = null,
    seoScore = null,
    aiScore = null,
    analysis_cache = {}
  } = $props();

  let editingField = $state<string | null>(null);
  let showAvatarPicker = $state(false);

  $effect(() => {
    console.log("[PublishStep] Content Check:", {
      draft_content_len: (draft_content || "").length,
      finalHtml_len: (finalHtml || "").length,
      asset_count: assets.length
    });
  });

  // QUAN TRỌNG: finalHtml ưu tiên vì đã qua MediaCompressor (ảnh localized)
  // draft_content là bản raw từ AI, chỉ dùng khi finalHtml rỗng
  let displayContent = $derived.by(() => {
    let base = finalHtml || draft_content || "";
    if (!base) return "";

    // Thay thế placeholder [IMAGE_n]
    if (base.includes("[IMAGE_")) {
      assets.forEach((url, i) => {
        const local = fixUrl(url);
        base = base.split(`[IMAGE_${i + 1}]`).join(
          `<img src="${local}" alt="image ${i+1}" class="max-w-full h-auto my-4 shadow-lg" />`
        );
      });
    }

    // Thay thế link ảnh ngoài bằng assets local (theo thứ tự)
    if (base.includes("<img") && assets.length > 0) {
      let idx = 0;
      const locals = assets.map(fixUrl);
      base = base.replace(/<img([^>]+)src=["'](https?:\/\/[^"']+)["']([^>]*)>/gi, (full, pre, src, post) => {
        if (idx < locals.length) return `<img${pre}src="${locals[idx++]}"${post}>`;
        return full;
      });
    }

    return base;
  });

  function fixUrl(url: string | null) {
    if (!url) return "";
    let p = url;
    if (p.startsWith("static/")) p = "/" + p;
    if (p.startsWith("/static/uploads/")) p = p.replace("/static/uploads/", "/uploads/");
    return p;
  }

  $effect(() => {
    if (!selectedAvatarUrl && assets.length > 0) selectedAvatarUrl = assets[0];
  });

  async function saveField() {
    editingField = null;
    try {
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, {
        keywords,
        draft_content,
        final_html: draft_content
      });
    } catch (e) { console.error("Save failed", e); }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') saveField();
    if (e.key === 'Escape') editingField = null;
  }

  async function selectAvatar(url: string) {
    selectedAvatarUrl = url;
    showAvatarPicker = false;
    try {
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, {
        gold_metadata: { ...keywords, avatar: url }
      });
    } catch (e) { console.error("Avatar sync failed", e); }
  }
</script>

<!-- ROOT: chiếm toàn bộ không gian được cấp bởi ContentReviewCard (overflow-hidden) -->
<div class="w-full h-full flex flex-col gap-3 min-h-0">

  <!-- Scores header -->
  <div class="hidden md:flex items-center gap-3 shrink-0">
    <div class="w-8 h-px bg-gradient-to-r from-transparent to-green-500/50"></div>
    <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-green-400">Website Publisher 2026</h5>
    {#if copyrightScore !== null}
      <span class="text-[9px] font-black {copyrightScore >= 90 ? 'text-emerald-400' : 'text-yellow-400'}">· Copyright {copyrightScore}%</span>
    {/if}
    {#if seoScore !== null}
      <span class="text-[9px] font-black text-blue-400">· SEO ({seoScore}/100)</span>
    {/if}
    {#if aiScore !== null}
      <span class="text-[9px] font-black text-purple-400">· AI {aiScore}%</span>
    {/if}
  </div>

  <!-- Title & Avatar - chiều cao cố định -->
  <div class="shrink-0 flex items-center gap-4 p-3 border border-white/5 bg-black/20">
    <!-- Avatar -->
    <div class="relative group shrink-0">
      <div
        class="w-16 h-16 overflow-hidden border-2 border-white/10 hover:border-green-500/50 transition-all cursor-pointer"
        onclick={() => showAvatarPicker = !showAvatarPicker}
      >
        {#if selectedAvatarUrl}
          <img src={fixUrl(selectedAvatarUrl)} alt="avatar" class="w-full h-full object-cover" />
        {:else}
          <div class="w-full h-full bg-white/5 flex items-center justify-center">
            <Sparkles size={16} class="text-white/20" />
          </div>
        {/if}
        <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
          <Edit2 size={12} class="text-white" />
        </div>
      </div>

      {#if showAvatarPicker}
        <div class="absolute top-full left-0 mt-2 z-50 w-64 bg-neutral-900 border border-white/10 p-3 shadow-2xl">
          <p class="text-[9px] font-black text-white/40 uppercase tracking-widest mb-2">Chọn ảnh đại diện</p>
          <div class="grid grid-cols-4 gap-2 max-h-40 overflow-y-auto custom-scrollbar">
            {#each assets as url}
              <button
                class="aspect-square overflow-hidden border-2 {selectedAvatarUrl === url ? 'border-green-500' : 'border-transparent'}"
                onclick={() => selectAvatar(url)}
              >
                <img src={fixUrl(url)} alt="asset" class="w-full h-full object-cover" />
              </button>
            {/each}
          </div>
          <button onclick={() => showAvatarPicker = false} class="w-full mt-2 py-1 text-[10px] text-white/40 hover:text-white">Đóng</button>
        </div>
      {/if}
    </div>

    <!-- Title -->
    <div class="flex-1 min-w-0">
      <p class="text-[9px] font-black text-white/30 uppercase tracking-widest mb-1">Post Title (dblclick to edit)</p>
      {#if editingField === 'title'}
        <input
          type="text" autofocus
          bind:value={keywords.title}
          onblur={saveField}
          onkeydown={handleKeydown}
          class="w-full bg-white/5 border border-green-500/30 px-2 py-1 text-base font-bold text-white focus:ring-0"
        />
      {:else}
        <h2
          class="text-base font-bold text-white/90 cursor-text hover:text-white truncate"
          ondblclick={() => editingField = 'title'}
        >{keywords.title || 'Untitled Article'}</h2>
      {/if}
    </div>
  </div>

  <!-- Article Content - flex-1 chiếm toàn bộ không gian còn lại -->
  <div class="flex-1 min-h-0 flex flex-col border border-white/10 bg-black/30" ondblclick={() => { if (editingField !== 'content') editingField = 'content'; }}>
    <div class="shrink-0 flex items-center justify-between px-3 py-2 border-b border-white/5">
      <span class="text-[9px] font-black uppercase tracking-widest text-white/40">Nội dung bài viết <span class="text-[8px] lowercase opacity-60">(dblclick to edit)</span></span>
      {#if editingField === 'content'}
        <span class="text-[8px] text-purple-400 animate-pulse font-black uppercase">Đang chỉnh sửa</span>
      {/if}
    </div>

    <!-- Content area -->
    <div class="flex-1 min-h-0">
      {#if editingField === 'content'}
        <div class="h-full flex flex-col bg-black/40">
          <RichTextEditor
            content={displayContent}
            assets={assets}
            onChange={(val) => { draft_content = val; finalHtml = val; }}
            editable={true}
            placeholder="Chỉnh sửa nội dung..."
            onblur={saveField}
          />
          <div class="shrink-0 p-2 border-t border-white/5 flex justify-end">
            <button
              class="px-4 py-1.5 bg-purple-500 text-[10px] font-black text-white hover:bg-purple-600 uppercase"
              onclick={saveField}
            >LƯU NỘI DUNG</button>
          </div>
        </div>
      {:else if displayContent}
        <div class="h-full overflow-y-auto custom-scrollbar p-5 prose prose-invert max-w-none text-white text-sm leading-relaxed">
          {@html displayContent}
        </div>
      {:else}
        <!-- Lỗi: hiển thị chi tiết để debug -->
        <div class="h-full flex flex-col items-center justify-center gap-3 p-6 bg-red-950/20 border-t border-red-500/20">
          <span class="text-red-400 font-black text-sm uppercase">⚠ Lỗi tải nội dung bài viết</span>
          <div class="bg-black/40 border border-red-500/20 p-3 text-[10px] font-mono text-red-300/60 w-full max-w-sm space-y-1">
            <p>draft_content: {draft_content ? draft_content.length + ' chars' : 'RỖNG'}</p>
            <p>finalHtml: {finalHtml ? finalHtml.length + ' chars' : 'RỖNG'}</p>
            <p>assets: {assets.length} files</p>
            <p class="text-red-400/50 pt-1">→ displayContent rỗng — kiểm tra dữ liệu từ API</p>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <!-- Bottom Row: Category/Slug & Meta -->
  <div class="shrink-0 grid grid-cols-2 gap-3">
    <!-- Category & Slug -->
    <div class="p-3 bg-blue-500/5 border border-blue-500/10 space-y-3">
      <div ondblclick={() => editingField = 'category'}>
        <p class="text-[9px] font-black text-blue-400 uppercase tracking-widest mb-1">Category</p>
        {#if editingField === 'category'}
          <input type="text" autofocus bind:value={keywords.category}
            onblur={saveField} onkeydown={handleKeydown}
            class="bg-white/5 border border-blue-500/30 px-2 py-0.5 text-[12px] font-bold text-white w-full focus:ring-0"
          />
        {:else}
          <div class="flex items-center justify-between pb-1 border-b border-blue-500/20 cursor-text group">
            <span class="text-[12px] font-bold text-white">{keywords.category || 'Chưa phân loại'}</span>
            <Edit2 size={10} class="text-white/10 group-hover:text-blue-400" />
          </div>
        {/if}
      </div>

      <div ondblclick={() => { keywords.slug = keywords.slug || keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'') || 'article-url'; editingField = 'slug'; }}>
        <p class="text-[9px] font-black text-blue-400 uppercase tracking-widest mb-1">Slug (URL)</p>
        {#if editingField === 'slug'}
          <div class="flex items-center gap-1 bg-white/5 border border-blue-500/30 px-2 h-7">
            <span class="text-[10px] text-white/20">/</span>
            <input type="text" autofocus bind:value={keywords.slug}
              onblur={saveField} onkeydown={handleKeydown}
              class="bg-transparent border-none p-0 text-[11px] font-bold text-white focus:ring-0 w-full"
            />
          </div>
        {:else}
          <div class="flex items-center gap-1 cursor-text group h-7">
            <span class="text-[10px] text-white/20">/</span>
            <span class="text-[11px] font-bold text-white truncate">{keywords.slug || (keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'') || 'article-url')}</span>
            <Edit2 size={10} class="text-white/10 group-hover:text-blue-400 ml-auto" />
          </div>
        {/if}
      </div>
    </div>

    <!-- Meta Description -->
    <div class="p-3 bg-purple-500/5 border border-purple-500/10 flex flex-col" ondblclick={() => editingField = 'description'}>
      <div class="flex items-center justify-between mb-1 shrink-0">
        <p class="text-[9px] font-black text-purple-400 uppercase tracking-widest flex items-center gap-1"><Sparkles size={9} /> Meta Description</p>
        <span class="text-[9px] text-white/20 font-mono">{(keywords.description || '').length}/160</span>
      </div>
      {#if editingField === 'description'}
        <textarea autofocus bind:value={keywords.description}
          onblur={saveField} rows="3"
          class="flex-1 bg-black/40 border border-purple-500/40 p-2 text-[11px] text-white focus:ring-0 resize-none italic"
        ></textarea>
      {:else}
        <div class="flex-1 cursor-text hover:bg-black/10 p-1 transition-all">
          <p class="text-[11px] text-white/50 leading-relaxed italic line-clamp-4">
            {keywords.description || 'Chưa cập nhật mô tả SEO...'}
          </p>
        </div>
      {/if}
    </div>
  </div>

</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 0; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.1); }
</style>
