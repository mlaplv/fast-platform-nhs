<script lang="ts">
  import {
    Edit2,
    RotateCcw,
    Sparkles
  } from "lucide-svelte";

  let {
    selectedAvatarUrl,
    viewingStep = $bindable(6),
    isEditing = $bindable(false),
    keywords = $bindable({}),
    finalHtml,
    draft_content
  } = $props();
</script>

<div class="h-full flex flex-col overflow-hidden">
  <div class="hidden md:flex items-center gap-3 mb-4 shrink-0">
    <div class="w-8 h-px bg-gradient-to-r from-transparent to-green-500/50"></div>
    <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-green-400">Website Publisher 2026</h5>
  </div>

  <div class="flex-1 overflow-hidden flex flex-col gap-4">
    
    <!-- TOP SECTION: Content & Avatar -->
    <div class="flex-1 flex flex-col gap-4 overflow-hidden border border-white/5 bg-black/20 rounded-2xl p-4 mr-2">
       <!-- Title & Avatar Bar -->
       <div class="flex items-center gap-4 shrink-0">
          {#if selectedAvatarUrl}
            <div class="relative group">
              <img src={selectedAvatarUrl} alt="avatar" class="w-16 h-16 rounded-xl object-cover shrink-0 border-2 border-white/10" />
              <button 
                 onclick={() => { viewingStep = 2; isEditing = false; }}
                 class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-xl"
              >
                 <Edit2 size={12} class="text-white" />
              </button>
            </div>
          {/if}
          <div class="flex-1">
            <span class="text-[9px] font-black uppercase tracking-widest text-white/40 mb-1 block">Post Title</span>
            <input 
              type="text" 
              bind:value={keywords.title}
              class="w-full bg-transparent border-none p-0 text-base font-bold text-white focus:ring-0 placeholder:text-white/20"
              placeholder="Enter post title..."
            />
          </div>
       </div>

       <!-- Tiptap Editor / Content Preview -->
       <div class="flex-1 border-t border-white/5 pt-4 overflow-hidden flex flex-col">
          <span class="text-[9px] font-black uppercase tracking-widest text-white/40 mb-2 shrink-0">Article Content</span>
          <div class="flex-1 overflow-y-auto custom-scrollbar rounded-xl bg-white/[0.02] border border-white/5">
             {#if finalHtml}
                <div class="p-4 prose prose-invert prose-sm max-w-none text-white/90 text-[13px] leading-relaxed selection:bg-green-500/30">
                  {@html finalHtml}
                </div>
             {:else if draft_content}
                <div class="p-4 prose prose-invert prose-sm max-w-none text-white/70 text-[13px] leading-relaxed opacity-60">
                  {@html draft_content}
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

    <!-- BOTTOM ROW: Metadata Cards -->
    <div class="grid grid-cols-2 gap-4 shrink-0 pr-2">
      <!-- Category & Slug -->
      <div class="p-4 rounded-xl bg-blue-500/5 border border-blue-500/10 space-y-4">
         <div>
           <p class="text-[9px] font-black text-blue-400 uppercase tracking-widest mb-2">Category</p>
           <div class="flex items-center justify-between pb-1 border-b border-blue-500/20">
             <input 
               type="text" 
               bind:value={keywords.category}
               class="bg-transparent border-none p-0 text-[12px] font-bold text-white focus:ring-0 w-full"
               placeholder="Uncategorized"
             />
             <Edit2 size={10} class="text-white/20" />
           </div>
         </div>

         <div>
           <p class="text-[9px] font-black text-blue-400 uppercase tracking-widest mb-2">Target Slug (URL)</p>
           <div class="flex items-center gap-1 group pb-1 border-b border-blue-500/20">
             <span class="text-[10px] text-white/40 font-mono tracking-tighter">/blog/</span>
             <input 
               type="text" 
               bind:value={keywords.slug}
               placeholder={keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'')} 
               class="bg-transparent border-none p-0 text-[11px] font-bold text-white focus:ring-0 w-full"
             />
           </div>
         </div>
      </div>

      <!-- SEO 2026 Box -->
      <div class="p-4 rounded-xl bg-purple-500/5 border border-purple-500/10 flex flex-col gap-4">
         <div>
            <div class="flex items-center justify-between mb-2">
               <p class="text-[9px] font-black text-purple-400 uppercase tracking-widest flex items-center gap-1"><Sparkles size={10} /> Meta Description</p>
               <span class="text-[9px] text-white/20 font-mono">{(keywords.description || '').length}/160</span>
            </div>
            <textarea 
               bind:value={keywords.description}
               rows="2"
               class="w-full bg-black/20 border border-purple-500/20 rounded-lg p-2 text-[11px] text-white/70 leading-relaxed focus:ring-1 focus:ring-purple-500/50 resize-none font-medium italic"
               placeholder="Nhập Meta Description cho bài viết..."
            ></textarea>
         </div>

         <div>
           <p class="text-[9px] font-black text-purple-400 uppercase tracking-widest mb-2">Focus Keywords</p>
           <div class="flex flex-wrap gap-1.5">
              {#if keywords.primary_keyword}
                 <span class="px-2 py-1 rounded-full bg-purple-500/20 border border-purple-500/30 text-[9px] text-purple-200 font-bold max-w-full truncate">
                    {keywords.primary_keyword}
                 </span>
              {/if}
              {#each (keywords.secondary_keywords || []).slice(0, 3) as kw}
                 <span class="px-2 py-1 rounded-full bg-white/5 border border-white/5 text-[9px] text-white/40 max-w-full truncate">
                    {kw}
                 </span>
              {/each}
           </div>
         </div>
      </div>
    </div>
    
  </div>
</div>
