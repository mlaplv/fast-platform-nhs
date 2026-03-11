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

<div class="space-y-4 {isExpanded ? 'flex-1 overflow-hidden flex flex-col' : 'min-h-[400px]'}">
  <div class="flex items-center justify-between mb-1">
    <div class="flex items-center gap-3">
       <div class="relative w-4 h-4">
          <div class="absolute inset-0 bg-blue-500/40 blur-[4px] rounded-full animate-pulse"></div>
          <div class="absolute inset-1 bg-blue-400 rounded-full shadow-[0_0_8px_rgba(59,130,246,1)]"></div>
       </div>
       <div class="flex flex-col">
          <span class="text-[9px] text-blue-400/60 font-black tracking-[0.4em] leading-none mb-1 uppercase">Neural Asset Repository</span>
          <span class="text-[11px] text-white font-bold opacity-90 tracking-tight leading-none uppercase">SELECT_MODE://ACTIVE</span>
       </div>
    </div>
    <div class="flex items-center gap-2">
      {#if !isProcessing}
        <div class="flex bg-white/5 p-1 rounded-xl border border-white/10 ring-1 ring-black/20 focus-within:ring-blue-500/50 focus-within:border-blue-500/30 transition-all h-8 mr-2">
          <div class="flex items-center justify-center pl-2 text-white/40">
            <LinkIcon size={12} />
          </div>
          <input 
            type="url" 
            placeholder="Dán link ảnh và Enter..." 
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
                 syncAssetChanges();
              }
            }}
            class="bg-transparent border-none outline-none text-[10px] text-white placeholder:text-white/30 px-3 w-36 transition-all focus:w-48"
          />
          <button 
            class="p-1 rounded-lg bg-blue-500 text-white hover:bg-blue-400 disabled:opacity-50 disabled:hover:bg-blue-500 transition-colors"
            disabled={!customImageUrl.trim() || !customImageUrl.startsWith('http')}
            onclick={() => {
              if (customImageUrl.trim() && customImageUrl.startsWith('http')) {
                 assets = [...assets, customImageUrl.trim()];
                 if (!selectedAvatarUrl) {
                   selectedAvatarUrl = customImageUrl.trim();
                   selectedAssetIndex = assets.length - 1;
                 }
                 customImageUrl = "";
                 syncAssetChanges();
              }
            }}
            title="Thêm ảnh"
          >
            <Plus size={12} />
          </button>
        </div>
      {/if}

      <div class="flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/10 backdrop-blur-xl h-8">
         <span class="text-[11px] text-white/50 font-mono">ASSETS: <span class="text-blue-400">{assets.length}</span></span>
      </div>
    </div>
  </div>

  <div class="relative group/matrix {isExpanded ? 'flex-1 overflow-hidden flex flex-col' : ''}">
    <div class="absolute inset-0 pointer-events-none z-10 opacity-[0.02] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%]"></div>
    
    <div class="{isExpanded ? 'flex-1' : 'max-h-[500px]'} overflow-y-auto pr-2 custom-scrollbar space-y-4 min-h-0">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {#each (assets || []) as url, i}
          <div 
            role="button"
            tabindex="0"
            onclick={() => {
              selectedAssetIndex = i;
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
            class="group/item relative aspect-[4/3] rounded-2xl overflow-hidden border transition-all duration-500 cursor-pointer
              {selectedAssetIndex === i ? 'border-blue-500 ring-2 ring-blue-500/30 shadow-[0_0_20px_rgba(59,130,246,0.4)]' : 'border-white/5 bg-white/[0.02] hover:border-white/20 hover:scale-[1.02]'}
              {i % 5 === 0 ? 'lg:col-span-2 lg:row-span-2 aspect-square' : ''}"
            in:scale={{ duration: 500, delay: i * 40, start: 0.95 }}
          >
            <img 
              src={url} 
              alt="Asset {i}" 
              class="w-full h-full object-cover transition-all duration-1000 group-hover/item:scale-110 {selectedAssetIndex === i ? 'brightness-110' : 'brightness-75 group-hover/item:brightness-100'}"
              onerror={() => handleImageError(url)}
            />

            <div class="absolute top-2 right-2 flex flex-col gap-1.5 opacity-0 group-hover/item:opacity-100 transition-opacity z-20">
              <button 
                class="p-1.5 rounded-full bg-black/50 hover:bg-red-500/80 text-white/70 hover:text-white backdrop-blur-sm transition-all"
                onclick={(e) => deleteAsset(i, e)}
                title="Xóa ảnh"
              >
                <Trash2 size={12} />
              </button>
              <button 
                class="p-1.5 rounded-full {selectedAvatarUrl === url ? 'bg-amber-500 text-white' : 'bg-black/50 text-white/70 hover:bg-amber-500/50 hover:text-white'} backdrop-blur-sm transition-all shadow-md"
                onclick={(e) => {
                   e.stopPropagation();
                   selectedAvatarUrl = url;
                   selectedAssetIndex = i;
                   syncAssetChanges();
                }}
                title="Chọn làm Ảnh Đại Diện"
              >
                <Star size={12} class={selectedAvatarUrl === url ? 'fill-current' : ''} />
              </button>
            </div>
            
            <div class="absolute inset-0 transition-opacity duration-500 {selectedAssetIndex === i ? 'opacity-100' : 'opacity-0 group-hover/item:opacity-100'} bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none">
              <div class="absolute bottom-3 left-3 flex items-center gap-2">
                 <div class="p-1.5 rounded-full {selectedAssetIndex === i ? 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]' : 'bg-black/40 backdrop-blur-md'} border border-white/20 transition-all duration-500">
                    <Check size={12} class="text-white" />
                 </div>
                 <span class="text-[9px] font-black text-white uppercase tracking-widest">{selectedAssetIndex === i ? 'Selected' : 'Click to select'}</span>
              </div>
            </div>

            {#if selectedAssetIndex === i}
              <div class="absolute inset-0 border-2 border-blue-400/50 rounded-2xl animate-pulse pointer-events-none"></div>
            {/if}
            
            <div class="absolute inset-0 opacity-0 group-hover/item:opacity-100 transition-opacity duration-300 pointer-events-none bg-[radial-gradient(circle_at_var(--mouse-x,50%)_var(--mouse-y,50%),rgba(59,130,246,0.15)_0%,transparent_50%)]"></div>
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
