<script lang="ts">
  import type { MediaAsset } from "$lib/state/types";
  import MediaModal from "$lib/components/media/MediaModal.svelte";

  let {
    show = $bindable(false),
    assets = [] as (MediaAsset | string)[],
    onSelect
  }: {
    show: boolean;
    assets: (MediaAsset | string)[];
    onSelect: (url: string) => void;
  } = $props();

  let imageUrl = $state('');
  let fileInput = $state<HTMLInputElement | null>(null);
  let showMediaLibrary = $state(false);

  function handleFileUpload(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        onSelect(result);
        show = false;
      };
      reader.readAsDataURL(file);
    }
  }

  function handleInsertUrl() {
    if (imageUrl.trim()) {
      onSelect(imageUrl.trim());
      imageUrl = '';
      show = false;
    }
  }

  function handleImageError(e: Event) {
    (e.target as HTMLImageElement).src = 'https://placehold.co/400x300?text=Image+Error';
  }
</script>

{#if show}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-[1000] flex items-center justify-center bg-[#09090b]/80 backdrop-blur-xl transition-all duration-500" onclick={() => show = false}>
    <div 
        class="bg-[#18181b] border border-white/5 p-8 shadow-[0_0_50px_-12px_rgba(59,130,246,0.3)] w-[95%] max-w-[900px] rounded-[2rem] relative overflow-hidden group" 
        onclick={(e) => e.stopPropagation()}
    >
      <!-- Background Ambient Glow -->
      <div class="absolute -top-24 -left-24 w-64 h-64 bg-blue-500/10 blur-[100px] rounded-full group-hover:bg-blue-500/15 transition-all duration-700"></div>
      <div class="absolute -bottom-24 -right-24 w-64 h-64 bg-purple-500/10 blur-[100px] rounded-full group-hover:bg-purple-500/15 transition-all duration-700"></div>

      <div class="relative flex items-center justify-between mb-8">
        <div class="flex flex-col">
            <h3 class="text-xl font-black text-white tracking-tighter uppercase italic">Media Intelligence</h3>
            <p class="text-[10px] text-zinc-500 font-mono tracking-[0.2em] uppercase">Visual Assets Command Center</p>
        </div>
        <button onclick={() => show = false} class="w-10 h-10 flex items-center justify-center rounded-full bg-white/5 border border-white/10 text-white/40 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all active:scale-95">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>

      <!-- Main Action Row: Slim & Efficient -->
      <div class="relative flex items-center gap-2 mb-8 bg-zinc-900/40 p-1.5 rounded-2xl border border-white/5">
        <!-- URL Input Component (Flexible) -->
        <div class="relative flex-1 group/input flex items-center pr-2">
            <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none text-zinc-500 group-focus-within/input:text-blue-500 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            </div>
            <input
                type="url"
                placeholder="Dán link ảnh..."
                bind:value={imageUrl}
                onkeydown={(e) => e.key === 'Enter' && handleInsertUrl()}
                class="w-full h-11 bg-transparent pl-10 pr-4 text-xs text-white placeholder:text-zinc-600 outline-none transition-all"
            />
            {#if imageUrl.trim()}
              <button 
                onclick={handleInsertUrl}
                class="px-3 h-7 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold rounded-lg transition-all animate-in fade-in slide-in-from-right-2"
              >
                Chèn
              </button>
            {/if}
        </div>

        <!-- Action Divider -->
        <div class="w-px h-6 bg-white/10 mx-1"></div>

        <!-- Upload Action -->
        <button 
            onclick={() => fileInput?.click()} 
            class="h-11 px-4 flex items-center gap-2 text-zinc-400 hover:text-white hover:bg-white/5 transition-all rounded-xl group/upload whitespace-nowrap"
            title="Tải ảnh mới"
        >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            <span class="text-[10px] font-bold uppercase tracking-wider">Tải lên</span>
        </button>
        <input type="file" bind:this={fileInput} accept="image/*" class="hidden" onchange={handleFileUpload} />

        <!-- Library Action -->
        <button
          onclick={() => showMediaLibrary = true}
          class="h-11 px-6 flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white transition-all rounded-xl group/library shadow-lg shadow-blue-500/10 whitespace-nowrap"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
          <span class="text-[10px] font-black uppercase tracking-widest italic">AI Vault</span>
        </button>
      </div>

      {#if assets && assets.length > 0}
         <div class="relative">
            <div class="flex items-center justify-between mb-4">
                <div class="text-[10px] uppercase font-black text-blue-500 tracking-[0.3em] flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                    Recent Intelligence Assets
                </div>
            </div>
            
            <div class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-4 max-h-[380px] overflow-y-auto pr-2 custom-scrollbar pb-4">
                {#each assets.filter(a => a) as asset}
                  {@const assetUrl = typeof asset === 'string' ? asset : (asset.file_path || asset.url || asset.link || '')}
                  {@const fullUrl = assetUrl && (assetUrl.startsWith('http') || assetUrl.startsWith('data:')) ? assetUrl : (assetUrl.startsWith('/') ? assetUrl : '/storage/' + assetUrl)}
                  <!-- svelte-ignore a11y_click_events_have_key_events -->
                  <!-- svelte-ignore a11y_no_static_element_interactions -->
                  <div 
                     class="group/asset relative aspect-square rounded-2xl overflow-hidden border border-white/5 hover:border-blue-500/50 cursor-pointer transition-all duration-300 bg-zinc-900 hover:scale-[1.02] hover:shadow-[0_0_30px_-10px_rgba(59,130,246,0.3)]"
                     onclick={() => { onSelect(fullUrl); show = false; }}
                  >
                      <img src={fullUrl} alt="asset" class="w-full h-full object-cover grayscale-[0.5] group-hover/asset:grayscale-0 transition-all duration-500" onerror={handleImageError} />
                      <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover/asset:opacity-100 transition-opacity flex items-end p-3">
                          <span class="text-[9px] text-white font-mono truncate uppercase tracking-tighter">{assetUrl.split('/').pop()}</span>
                      </div>
                      <div class="absolute top-2 right-2 w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center opacity-0 group-hover/asset:opacity-100 translate-y-2 group-hover/asset:translate-y-0 transition-all">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                      </div>
                  </div>
                {/each}
              </div>
          </div>
      {/if}

      <div class="mt-8 pt-6 border-t border-white/5 flex items-center justify-between">
        <div class="flex items-center gap-4 text-[10px] text-zinc-600 uppercase font-mono tracking-widest">
            <span class="flex items-center gap-1.5"><span class="w-1 h-1 rounded-full bg-green-500"></span> AI Optimization Active</span>
            <span class="flex items-center gap-1.5"><span class="w-1 h-1 rounded-full bg-blue-500"></span> Auto-WebP Ready</span>
        </div>
        <button onclick={() => show = false} class="px-8 py-3 bg-zinc-800/50 hover:bg-zinc-800 text-zinc-400 hover:text-white text-[11px] font-bold uppercase tracking-widest rounded-xl transition-all active:scale-95">
            Dismiss
        </button>
      </div>
    </div>
  </div>

  <MediaModal
    bind:show={showMediaLibrary}
    onSelect={(asset) => {
      onSelect(asset.file_path);
      showMediaLibrary = false;
      show = false;
    }}
    onClose={() => showMediaLibrary = false}
  />
{/if}

<style>
    .custom-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 10px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: rgba(59, 130, 246, 0.5);
    }
</style>
