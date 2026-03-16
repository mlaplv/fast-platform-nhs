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
  <div class="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={() => show = false}>
    <div class="bg-[#1a2233] border border-white/10 p-6 shadow-2xl w-[90%] max-w-[800px]" onclick={(e) => e.stopPropagation()}>
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-bold text-white">Chèn hình ảnh</h3>
        <button onclick={() => show = false} class="text-white/40 hover:text-white"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button>
      </div>

      {#if assets && assets.length > 0}
         <div class="text-[10px] uppercase font-bold text-blue-400 mb-2 tracking-wider">Chọn từ Kho Ảnh </div>
         <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-4 max-h-[400px] overflow-y-auto pr-1 custom-scrollbar">
            {#each assets.filter(a => a) as asset}
              {@const assetUrl = typeof asset === 'string' ? asset : (asset.file_path || asset.url || asset.link || '')}
              {@const fullUrl = assetUrl && (assetUrl.startsWith('http') || assetUrl.startsWith('data:')) ? assetUrl : (assetUrl.startsWith('/') ? assetUrl : '/storage/' + assetUrl)}
              <!-- svelte-ignore a11y_click_events_have_key_events -->
              <!-- svelte-ignore a11y_no_static_element_interactions -->
              <div 
                 class="aspect-video overflow-hidden border border-white/10 hover:border-blue-500 cursor-pointer transition-colors bg-white/5"
                 onclick={() => { onSelect(fullUrl); show = false; }}
                 title="Chèn ảnh này"
              >
                  <img src={fullUrl} alt="asset" class="w-full h-full object-cover" onerror={handleImageError} />
              </div>
            {/each}
          </div>
          <div class="flex items-center gap-2 mb-3">
            <div class="h-px bg-white/10 flex-1"></div>
            <span class="text-xs text-white/40 font-mono text-center">HOẶC CHÈN QUA URL / TẢI LÊN</span>
            <div class="h-px bg-white/10 flex-1"></div>
          </div>
      {/if}

      <div class="flex flex-col gap-3 mb-4">
        <button
          onclick={() => showMediaLibrary = true}
          class="w-full flex items-center justify-center gap-2 py-4 bg-blue-600 text-white hover:bg-blue-700 transition-all text-xs font-bold rounded-xl shadow-lg shadow-blue-500/20"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
          MỞ THƯ VIỆN ẢNH AI (FILE MANAGER)
        </button>

        <button onclick={() => fileInput?.click()} class="w-full flex items-center justify-center gap-2 py-3 bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 transition-all text-xs font-bold rounded-xl">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          Tải ảnh lên từ thiết bị
        </button>
        <input type="file" bind:this={fileInput} accept="image/*" class="hidden" onchange={handleFileUpload} />
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

      <input
        type="url"
        placeholder="Dán URL hình ảnh vào đây..."
        bind:value={imageUrl}
        onkeydown={(e) => e.key === 'Enter' && handleInsertUrl()}
        class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/30 outline-none focus:border-blue-500/50 mb-3"
      />
      <div class="flex gap-2 justify-end">
        <button onclick={() => show = false} class="px-4 py-2 text-xs text-white/60 hover:text-white transition-colors">Hủy</button>
        <button onclick={handleInsertUrl} class="px-4 py-2 bg-blue-500 hover:bg-blue-400 text-white text-xs font-bold transition-colors">Chèn URL</button>
      </div>
    </div>
  </div>
{/if}
