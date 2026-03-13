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

  // Rules: UI state for double-click editing
  let editingField = $state<string | null>(null);
  let showAvatarPicker = $state(false);

  // CNS V72.1: Robust URL resolver to handle /static/ prefix transition
  function fixUrl(url: string | null) {
    if (!url) return "";
    if (url.startsWith("/static/uploads/")) {
      return url.replace("/static/uploads/", "/uploads/");
    }
    return url;
  }

  // Auto-init avatar if none selected
  $effect(() => {
    if (!selectedAvatarUrl && assets.length > 0) {
      selectedAvatarUrl = assets[0];
    }
  });

  async function saveField() {
    editingField = null;
    try {
      // CNS V72: Sync both keywords and draft_content if needed
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, { 
        keywords,
        draft_content: draft_content,
        final_html: draft_content
      });
    } catch (e) {
      console.error("Failed to sync campaign update", e);
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') saveField();
    if (e.key === 'Escape') editingField = null;
  }

  async function selectAvatar(url: string) {
    selectedAvatarUrl = url;
    showAvatarPicker = false;
    try {
      // CNS V72: Sync avatar change to backend immediately
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, { 
        avatar: url,
        gold_metadata: { ...keywords, avatar: url } 
      });
    } catch (e) { console.error("Avatar sync failed", e); }
  }
</script>

<div class="h-full flex flex-col overflow-hidden select-none">
  <div class="hidden md:flex items-center gap-3 mb-4 shrink-0">
    <div class="w-8 h-px bg-gradient-to-r from-transparent to-green-500/50"></div>
    <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-green-400">Website Publisher 2026</h5>
    
    {#if copyrightScore !== null}
      {@const rc = copyrightScore >= 90 ? 'text-emerald-400' : copyrightScore >= 70 ? 'text-yellow-400' : 'text-red-400'}
      <span class="text-[9px] font-black uppercase {rc}">· Copyright {copyrightScore}%</span>
    {/if}
    
    {#if seoScore !== null}
      {@const seoData = analysis_cache?.seo?.data}
      {@const grade = seoData?.grade || (seoScore >= 80 ? 'A' : seoScore >= 60 ? 'B' : 'C')}
      {@const gc = grade === 'A' ? 'text-emerald-400' : grade === 'B' ? 'text-blue-400' : grade === 'C' ? 'text-yellow-400' : 'text-red-400'}
      <span class="text-[9px] font-black uppercase {gc}">· SEO {grade} ({seoScore}/100)</span>
    {/if}
    
    {#if aiScore !== null}
      {@const ac = aiScore >= 85 ? 'text-purple-400' : aiScore >= 65 ? 'text-fuchsia-400' : 'text-red-400'}
      <span class="text-[9px] font-black uppercase {ac}">· AI {aiScore}%</span>
    {/if}
  </div>

  <div class="flex-1 overflow-hidden flex flex-col gap-4">
    
    <!-- TOP SECTION: Content & Avatar -->
    <div class="flex-1 flex flex-col gap-4 overflow-hidden border border-white/5 bg-black/20 p-4 mr-2">
       <!-- Title & Avatar Bar -->
       <div class="flex items-center gap-4 shrink-0">
          <div class="relative group">
            <div 
              class="w-20 h-20 overflow-hidden border-2 border-white/10 hover:border-green-500/50 transition-all cursor-pointer relative"
              onclick={() => showAvatarPicker = !showAvatarPicker}
              ondblclick={() => showAvatarPicker = !showAvatarPicker}
            >
              {#if selectedAvatarUrl}
                <img src={fixUrl(selectedAvatarUrl)} alt="avatar" class="w-full h-full object-cover" />
              {:else}
                <div class="w-full h-full bg-white/5 flex items-center justify-center">
                   <Sparkles size={20} class="text-white/20" />
                </div>
              {/if}
              <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center transition-opacity">
                <Edit2 size={14} class="text-white mb-1" />
                <span class="text-[8px] font-black text-white/80">THAY ĐỔI</span>
              </div>
            </div>

            {#if showAvatarPicker}
              <div class="absolute top-full left-0 mt-2 z-50 w-72 bg-neutral-900 border border-white/10 p-3 shadow-2xl backdrop-blur-xl">
                 <p class="text-[9px] font-black text-white/40 uppercase tracking-widest mb-3">Chọn ảnh đại diện</p>
                 <div class="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto custom-scrollbar">
                   {#each assets as url}
                     <button 
                        class="aspect-square overflow-hidden border-2 transition-all {selectedAvatarUrl === url ? 'border-green-500' : 'border-transparent hover:border-white/20'}"
                        onclick={() => selectAvatar(url)}
                     >
                        <img src={fixUrl(url)} alt="asset" class="w-full h-full object-cover" />
                     </button>
                   {/each}
                   <label class="aspect-square bg-white/5 border border-dashed border-white/10 flex items-center justify-center cursor-pointer hover:bg-white/10 transition-all">
                      <input type="file" class="hidden" accept="image/*" />
                      <span class="text-xl text-white/40">+</span>
                   </label>
                 </div>
                 <button 
                    onclick={() => showAvatarPicker = false}
                    class="w-full mt-3 py-2 text-[10px] font-bold text-white/60 hover:text-white transition-colors"
                 >Đóng</button>
              </div>
            {/if}
          </div>

          <div class="flex-1">
            <div class="flex items-center justify-between mb-1">
               <span class="text-[9px] font-black uppercase tracking-widest text-white/40">Post Title <span class="text-[8px] opacity-40 lowercase">(dblclick to edit)</span></span>
               {#if editingField === 'title'}
                  <span class="text-[8px] text-green-400 animate-pulse uppercase font-black">Editing</span>
               {/if}
            </div>
            
            {#if editingField === 'title'}
               <input 
                 type="text" 
                 autofocus
                 bind:value={keywords.title}
                 onblur={saveField}
                 onkeydown={handleKeydown}
                 class="w-full bg-white/5 border border-green-500/30 px-3 py-1 text-base font-bold text-white focus:ring-0 focus:border-green-500/50"
               />
            {:else}
               <h2 
                 class="text-lg font-bold text-white/90 cursor-text hover:text-white transition-colors"
                 ondblclick={() => editingField = 'title'}
               >
                 {keywords.title || 'Untitled Article'}
               </h2>
            {/if}
          </div>
       </div>

       <!-- Article Content -->
       <div 
         class="flex-1 border-t border-white/5 pt-4 overflow-hidden flex flex-col"
         ondblclick={() => editingField = 'content'}
       >
          <div class="flex items-center justify-between mb-2 shrink-0">
            <span class="text-[9px] font-black uppercase tracking-widest text-white/40">Article Content <span class="text-[8px] opacity-40 lowercase">(dblclick to edit)</span></span>
            {#if editingField === 'content'}
               <span class="text-[8px] text-purple-400 animate-pulse uppercase font-black">Editor Active</span>
            {/if}
          </div>
          
          <div class="flex-1 overflow-hidden bg-white/[0.02] border border-white/5 flex flex-col">
             {#if editingField === 'content'}
                <div class="flex-1 min-h-0 bg-black/40">
                  <RichTextEditor
                    content={draft_content || finalHtml || ""}
                    assets={assets}
                    onChange={(val) => {
                      draft_content = val;
                      finalHtml = val;
                    }}
                    editable={true}
                    placeholder="Chỉnh sửa nội dung cuối cùng..."
                    onblur={saveField}
                  />
                  <div class="p-2 border-t border-white/5 flex justify-end">
                    <button 
                      class="px-4 py-1.5 bg-purple-500 text-[10px] font-black text-white hover:bg-purple-600 transition-all uppercase"
                      onclick={saveField}
                    >LƯU NỘI DUNG</button>
                  </div>
                </div>
             {:else if draft_content || finalHtml}
                <div class="flex-1 overflow-y-auto custom-scrollbar p-4 prose prose-invert prose-sm max-w-none text-white/90 text-[13px] leading-relaxed selection:bg-green-500/30">
                  {@html draft_content || finalHtml}
                </div>
             {:else}
                <div class="flex flex-col items-center justify-center h-full gap-3 text-white/20">
                  <RotateCcw size={32} class="animate-spin opacity-20" />
                  <p class="text-sm">Hệ thống đang đóng gói nội dung...</p>
                </div>
             {/if}
          </div>
       </div>
    </div>

    <!-- BOTTOM ROW -->
    <div class="grid grid-cols-2 gap-4 shrink-0 pr-2">
      <!-- Category & Slug -->
      <div class="p-4 bg-blue-500/5 border border-blue-500/10 space-y-4">
         <div ondblclick={() => editingField = 'category'}>
           <p class="text-[9px] font-black text-blue-400 uppercase tracking-widest mb-1">Category</p>
           {#if editingField === 'category'}
             <input 
               type="text" 
               autofocus
               bind:value={keywords.category}
               onblur={saveField}
               onkeydown={handleKeydown}
               class="bg-white/5 border border-blue-500/30 rounded px-2 py-0.5 text-[12px] font-bold text-white focus:ring-0 w-full"
             />
           {:else}
             <div class="flex items-center justify-between pb-1 border-b border-blue-500/20 group cursor-text">
               <span class="text-[12px] font-bold text-white group-hover:text-blue-200 transition-colors">
                 {keywords.category || 'Chưa phân loại'}
               </span>
               <Edit2 size={10} class="text-white/10 group-hover:text-blue-400" />
             </div>
           {/if}
         </div>

         <div ondblclick={() => {
            if (!keywords.slug) {
              keywords.slug = keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'') || 'article-url';
            }
            editingField = 'slug'
         }}>
           <p class="text-[9px] font-black text-blue-400 uppercase tracking-widest mb-1">Slug (URL)</p>
           {#if editingField === 'slug'}
              <div class="flex items-center gap-1 bg-white/5 border border-blue-500/30 rounded px-2 h-8">
                <span class="text-[10px] text-white/20">/</span>
                <input 
                  type="text" 
                  autofocus
                  bind:value={keywords.slug}
                  onblur={saveField}
                  onkeydown={handleKeydown}
                  class="bg-transparent border-none p-0 text-[11px] font-bold text-white focus:ring-0 w-full"
                />
              </div>
           {:else}
             <div class="flex items-center gap-1 group pb-1 border-b border-blue-500/20 cursor-text h-8">
               <span class="text-[10px] text-white/20 font-mono">/</span>
               <span class="text-[11px] font-bold text-white group-hover:text-blue-200 truncate">
                 {keywords.slug || (keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'') || 'article-url')}
               </span>
               <Edit2 size={10} class="text-white/10 group-hover:text-blue-400 ml-auto" />
             </div>
           {/if}
         </div>
      </div>

      <!-- Meta Description -->
      <div class="p-4 bg-purple-500/5 border border-purple-500/10 flex flex-col" ondblclick={() => editingField = 'description'}>
         <div class="flex items-center justify-between mb-2">
            <p class="text-[9px] font-black text-purple-400 uppercase tracking-widest flex items-center gap-1"><Sparkles size={10} /> Meta Description</p>
            <span class="text-[9px] text-white/20 font-mono">{(keywords.description || '').length}/160</span>
         </div>
         
         {#if editingField === 'description'}
            <textarea 
               autofocus
               bind:value={keywords.description}
               onblur={saveField}
               rows="3"
               class="w-full bg-black/40 border border-purple-500/40 p-2 text-[11px] text-white leading-relaxed focus:ring-0 resize-none font-medium italic"
            ></textarea>
         {:else}
            <div class="flex-1 bg-black/10 hover:bg-black/20 p-2 transition-all cursor-text group border border-transparent hover:border-purple-500/20">
               <p class="text-[11px] text-white/50 leading-relaxed font-medium italic group-hover:text-white/80 line-clamp-3">
                 {keywords.description || 'Chưa cập nhật mô tả chuẩn SEO cho bài viết này...'}
               </p>
            </div>
         {/if}
      </div>
    </div>
    
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
    height: 4px;
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
</style>
