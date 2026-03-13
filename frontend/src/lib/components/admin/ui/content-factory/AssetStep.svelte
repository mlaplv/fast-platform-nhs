<script lang="ts">
  import {
    Image as ImageIcon,
    Link as LinkIcon,
    Plus,
    Trash2,
    Star,
    Check,
    RotateCcw
  } from "lucide-svelte";
  import { fade, scale } from "svelte/transition";
  import { vuiController } from "$lib/vui";

  let { 
    isProcessing,
    isExpanded,
    assets = $bindable([]),
    customImageUrl = $bindable(""),
    selectedAvatarUrl = $bindable(null),
    selectedAssetIndex = $bindable(0),
    handleImageError,
    syncAssetChanges,
    deleteAsset,
    handleRetry,
    handleMouseMove
  } = $props();
</script>

<div class="space-y-6 flex-1 flex flex-col min-h-0">
  <!-- Modern Minimalist Header -->
  <div class="flex items-center justify-between">
    <div class="hidden md:flex items-center gap-4">
       <div class="relative w-2 h-2">
          <div class="absolute inset-0 bg-blue-500 rounded-full animate-ping opacity-20"></div>
          <div class="absolute inset-0 bg-blue-400 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.8)]"></div>
       </div>
       <div class="flex flex-col">
          <span class="text-[8px] text-blue-400/50 font-black tracking-[0.3em] uppercase mb-0.5">Asset Intelligence</span>
          <span class="text-[12px] text-white/90 font-bold tracking-tight uppercase">SELECT_MODE://ACTIVE</span>
       </div>
    </div>
    <div class="flex items-center gap-3">
      {#if !isProcessing}
        <div class="flex bg-white/[0.03] hover:bg-white/[0.05] p-1 rounded-xl border border-white/5 transition-all h-9 group/input">
          <div class="flex items-center justify-center pl-3 text-white/20 group-focus-within/input:text-blue-400 transition-colors">
            <LinkIcon size={14} />
          </div>
          <input 
            type="url" 
            placeholder="Paste image link..." 
            bind:value={customImageUrl}
            onkeydown={(e) => {
              if (e.key === 'Enter' && customImageUrl.trim() && customImageUrl.startsWith('http')) {
                 e.preventDefault();
                 assets = [...assets, customImageUrl.trim()];
                 if (!selectedAvatarUrl) {
                   selectedAvatarUrl = customImageUrl.trim();
                   selectedAssetIndex = assets.length - 1;
                 }
                 customImageUrl = "";
                 vuiController.speak("Added.");
                 syncAssetChanges();
              }
            }}
            class="bg-transparent border-none outline-none text-[11px] text-white placeholder:text-white/20 px-3 w-40 transition-all focus:w-64"
          />
          <button 
            class="px-2 rounded-lg bg-blue-500/80 text-white hover:bg-blue-500 transition-all"
            disabled={!customImageUrl.trim() || !customImageUrl.startsWith('http')}
            onclick={() => {
              if (customImageUrl.trim() && customImageUrl.startsWith('http')) {
                 assets = [...assets, customImageUrl.trim()];
                 if (!selectedAvatarUrl) {
                   selectedAvatarUrl = customImageUrl.trim();
                   selectedAssetIndex = assets.length - 1;
                 }
                 customImageUrl = "";
                 vuiController.speak("Added.");
                 syncAssetChanges();
              }
            }}
          >
            <Plus size={14} />
          </button>
        </div>
      {/if}

      <div class="hidden md:block px-4 py-1.5 rounded-xl bg-white/[0.03] border border-white/5">
         <span class="text-[10px] text-white/40 font-bold uppercase tracking-widest">Found <span class="text-blue-400 ml-1 font-black">{assets.length}</span></span>
      </div>
    </div>
  </div>

  <div class="relative flex-1 min-h-0">
    <div class="h-full overflow-y-auto pr-1 custom-scrollbar min-h-0">
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {#each (assets || []) as url, i}
          <div 
            role="button"
            tabindex="0"
            onclick={() => {
              selectedAssetIndex = i;
              vuiController.speak(`Photo ${i + 1}`);
              syncAssetChanges(i);
            }}
            onkeydown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                selectedAssetIndex = i;
                syncAssetChanges(i);
              }
            }}
            onmousemove={handleMouseMove}
            class="group/item relative aspect-square rounded-[2rem] overflow-hidden border transition-all duration-700 cursor-pointer
              {selectedAssetIndex === i ? 'border-blue-500/50 ring-4 ring-blue-500/10 shadow-[0_20px_50px_rgba(59,130,246,0.2)] scale-95' : 'border-white/5 bg-white/[0.01] hover:border-white/20 hover:scale-[1.02] hover:rounded-[1.5rem]'}"
            in:scale={{ duration: 600, delay: i * 30, start: 0.9 }}
          >
            <img 
              src={url} 
              alt="Asset {i}" 
              class="w-full h-full object-cover transition-all duration-700 group-hover/item:scale-110 {selectedAssetIndex === i ? 'brightness-110' : 'brightness-90 group-hover/item:brightness-100'}"
              onerror={() => handleImageError(url)}
            />

            <!-- Advanced Controls Overlay -->
            <div class="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/60 opacity-0 group-hover/item:opacity-100 transition-all duration-500">
              <div class="absolute top-4 right-4 flex flex-col gap-2 translate-y-2 group-hover/item:translate-y-0 transition-transform duration-500">
                <button 
                  class="w-8 h-8 rounded-full bg-white/10 hover:bg-red-500/80 text-white/50 hover:text-white backdrop-blur-md border border-white/10 transition-all flex items-center justify-center shadow-xl"
                  onclick={(e) => deleteAsset(i, e)}
                >
                  <Trash2 size={13} />
                </button>
                <button 
                  class="w-8 h-8 rounded-full {selectedAvatarUrl === url ? 'bg-amber-500 text-white' : 'bg-white/10 text-white/50 hover:bg-amber-500/80 hover:text-white'} backdrop-blur-md border border-white/10 transition-all flex items-center justify-center shadow-xl"
                  onclick={(e) => {
                     e.stopPropagation();
                     selectedAvatarUrl = url;
                     selectedAssetIndex = i;
                     vuiController.speak("Hero image set.");
                     syncAssetChanges();
                  }}
                >
                  <Star size={13} class={selectedAvatarUrl === url ? 'fill-current' : ''} />
                </button>
              </div>
              
              <div class="absolute bottom-4 left-4 right-4 flex items-center justify-between">
                <div class="flex items-center gap-2">
                   <div class="w-6 h-6 rounded-lg {selectedAssetIndex === i ? 'bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.6)]' : 'bg-white/10 backdrop-blur-md'} border border-white/10 flex items-center justify-center transition-all duration-500">
                      <Check size={12} class="text-white" />
                   </div>
                   <span class="text-[10px] font-bold text-white/80 uppercase tracking-widest">{selectedAssetIndex === i ? 'Selected' : 'Use this'}</span>
                </div>
                <span class="text-[9px] font-medium text-white/30 font-mono">#{i + 1}</span>
              </div>
            </div>

            <!-- Focus Animation -->
            {#if selectedAssetIndex === i}
              <div class="absolute inset-0 bg-blue-500/5 pointer-events-none"></div>
            {/if}
            
            <!-- Dynamic Gloss Effect -->
            <div class="absolute inset-0 opacity-0 group-hover/item:opacity-100 transition-opacity duration-500 pointer-events-none bg-[radial-gradient(circle_at_var(--mouse-x,50%)_var(--mouse-y,50%),rgba(255,255,255,0.08)_0%,transparent_60%)]"></div>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>

{#if assets.length === 0 && !isProcessing}
  <div class="flex flex-col items-center justify-center py-12 text-center gap-4" in:fade={{ duration: 300 }}>
    <div class="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
      <ImageIcon size={28} class="text-white/20" />
    </div>
    <div>
      <p class="text-sm font-bold text-white/60">Không tìm thấy ảnh phù hợp</p>
      <p class="text-xs text-white/30 mt-1">Quota Google Search có thể đã hết, hoặc từ khóa quá ít phổ biến.</p>
    </div>
    <button
      onclick={handleRetry}
      class="flex items-center gap-2 px-5 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold transition-all"
    >
      <RotateCcw size={14} />
      Tìm lại ảnh
    </button>
  </div>
{/if}
