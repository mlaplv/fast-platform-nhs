<script lang="ts">
  import { slide } from 'svelte/transition';
  import AlertTriangle from "@lucide/svelte/icons/alert-triangle";
  import Info from "@lucide/svelte/icons/info";

  let {
    competitorAnalysis = null,
    importedItems = $bindable([]),
    negativeKeywords = $bindable([]),
    addNegativeKeyword,
    handleImportKeyword,
    fullview = false,
    activeTab = 'headlines'
  } = $props<{
    competitorAnalysis?: any;
    importedItems: string[];
    negativeKeywords: any[];
    addNegativeKeyword: (word: string) => void;
    handleImportKeyword: (headline: string) => void;
    fullview?: boolean;
    activeTab?: string;
  }>();

  function trackImport(text: string, action: () => void) {
    action();
    if (!importedItems.some(k => k.toLowerCase().trim() === text.toLowerCase().trim())) {
      importedItems = [...importedItems, text];
    }
  }

  function handleDragStart(event: DragEvent, text: string) {
    if (event.dataTransfer) {
      event.dataTransfer.setData('text/plain', text);
      event.dataTransfer.effectAllowed = 'copy';
    }
  }
</script>

{#if fullview}
  <div class="space-y-6 font-mono">
    <!-- Section 2: Competitor Headlines -->
    <div class="space-y-3 bg-black/40 p-5 border border-white/5 rounded-none">
      <span class="text-[11px] text-purple-400 font-black block text-left uppercase tracking-widest border-b border-purple-500/10 pb-2">📢 TIÊU ĐỀ QUẢNG CÁO ĐỐI THỦ ({competitorAnalysis?.competitor_headlines?.length || 0})</span>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[250px] overflow-y-auto pr-1 text-left">
        {#each competitorAnalysis?.competitor_headlines || [] as ch}
          <div class="bg-black/30 border border-white/5 p-3 flex justify-between items-center gap-3 group/ch hover:border-purple-500/30 rounded-none transition-all cursor-grab active:cursor-grabbing" draggable="true" ondragstart={(e) => handleDragStart(e, ch.headline)}>
            <div class="flex flex-col gap-1 min-w-0 text-left">
              <span class="text-xs text-white font-black truncate">{ch.headline}</span>
              <span class="text-[9px] text-purple-400 truncate">{ch.source_domain}</span>
            </div>
            <button 
              class="px-2.5 py-1 border rounded-none text-[10px] font-bold shrink-0 transition-all {importedItems.includes(ch.headline) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-purple-600 text-white hover:bg-purple-500'}"
              onclick={() => trackImport(ch.headline, () => handleImportKeyword(ch.headline))}
              disabled={importedItems.includes(ch.headline)}
            >
              {importedItems.includes(ch.headline) ? 'ĐÃ DÙNG' : 'DÙNG'}
            </button>
          </div>
        {/each}
      </div>
    </div>

    <!-- Section 3: Negatives & Gaps -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-black/40 p-5 border border-white/5 rounded-none">
      <!-- Left: Negatives -->
      <div class="space-y-3 md:border-r md:border-white/5 md:pr-6">
        <span class="text-[10px] text-purple-400 font-black block text-left uppercase tracking-wider mb-2">🛑 GỢI Ý TỪ KHÓA PHỦ ĐỊNH (CLICK ĐỂ THÊM)</span>
        <div class="flex flex-wrap gap-2 text-left">
          {#each competitorAnalysis?.negative_keyword_suggestions || [] as nk}
            <button 
              type="button"
              class="px-2.5 py-1 border text-[10px] transition-all cursor-pointer rounded-none {importedItems.includes(nk) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-red-500/10 border-red-500/20 text-red-400 hover:bg-red-500 hover:text-white'}"
              onclick={() => trackImport(nk, () => {
                addNegativeKeyword(nk);
                negativeKeywords = [...(negativeKeywords || []), { text: nk }];
              })}
              disabled={importedItems.includes(nk)}
              title={importedItems.includes(nk) ? "Đã thêm vào phủ định" : "Thêm vào danh sách phủ định"}
            >
              {importedItems.includes(nk) ? '✓ ' + nk : '+ ' + nk}
            </button>
          {/each}
        </div>
        
        {#if negativeKeywords && negativeKeywords.length > 0}
          <div class="mt-4 pt-4 border-t border-white/10 text-left">
            <span class="text-[9px] text-slate-500 font-black block uppercase mb-2">PHỦ ĐỊNH CHIẾN DỊCH ĐÃ CÓ ({negativeKeywords.length})</span>
            <div class="flex flex-wrap gap-1.5 max-h-[100px] overflow-y-auto">
              {#each negativeKeywords as nk}
                <span class="px-2 py-0.5 bg-red-950/20 border border-red-500/20 text-red-400 text-[9px]">
                  {nk.text || nk}
                </span>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <!-- Right: Gaps -->
      <div class="space-y-3 md:pl-2">
        <span class="text-[10px] text-yellow-500 font-black block text-left uppercase tracking-wider mb-2">⚠️ KẼ HỞ CẠNH TRANH (SEO GAPS)</span>
        {#if competitorAnalysis?.seo_gaps}
          <div class="border border-yellow-500/30 bg-yellow-500/5 p-4 rounded-none space-y-2 text-left">
            <div class="flex items-center gap-2 text-yellow-500 relative">
              <AlertTriangle size={14} />
              <span class="text-[10px] font-black uppercase">Phân tích khoảng trống</span>
              <div class="relative group cursor-pointer inline-flex items-center">
                <Info size={12} class="text-yellow-500/60 hover:text-yellow-400 transition-colors" />
                <span class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-64 bg-slate-950 border border-yellow-500/30 text-yellow-200 text-[9px] p-2 rounded shadow-2xl leading-normal z-50 whitespace-normal">
                  So sánh trực tiếp trang đích với đối thủ trên Google Search để tìm khoảng trống về: Social Proof, CTA, và độ dài/độ sâu nội dung tối ưu cho Google SGE.
                </span>
              </div>
            </div>
            <p class="text-xs text-yellow-200/80 leading-relaxed text-left">
              {competitorAnalysis.seo_gaps}
            </p>
          </div>
        {:else}
          <p class="text-xs text-slate-500 text-left">Không phát hiện kẽ hở cạnh tranh nào.</p>
        {/if}
      </div>
    </div>
  </div>
{:else}
  <!-- Mini View mode (tab panels) -->
  <div class="font-mono">
    {#if activeTab === 'headlines'}
      <div class="space-y-2 text-left" transition:slide>
        <div class="space-y-2">
          {#each competitorAnalysis?.competitor_headlines || [] as ch}
            <div class="bg-black/30 border border-white/5 p-3 flex justify-between items-center gap-3 group/ch hover:border-purple-500/30 cursor-grab active:cursor-grabbing" draggable="true" ondragstart={(e) => handleDragStart(e, ch.headline)}>
              <div class="flex flex-col gap-1 min-w-0 text-left">
                <span class="text-[10px] text-white font-black truncate">{ch.headline}</span>
                <span class="text-[8px] text-purple-400 truncate">{ch.source_domain}</span>
              </div>
              <button 
                class="px-2 py-1 border rounded-none text-[9px] font-bold shrink-0 transition-all {importedItems.includes(ch.headline) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-purple-500/20 text-purple-300 border-purple-500/30 hover:bg-purple-500 hover:text-white'}"
                onclick={() => trackImport(ch.headline, () => handleImportKeyword(ch.headline))}
                disabled={importedItems.includes(ch.headline)}
              >
                {importedItems.includes(ch.headline) ? 'ĐÃ DÙNG' : 'DÙNG'}
              </button>
            </div>
          {/each}
        </div>
      </div>
    {:else if activeTab === 'negatives_gaps'}
      <div class="space-y-4 text-left" transition:slide>
        <div class="space-y-2">
          <span class="text-[9px] text-purple-400 font-black block text-left">GỢI Ý TỪ KHÓA PHỦ ĐỊNH (CLICK ĐỂ THÊM)</span>
          <div class="flex flex-wrap gap-2 text-left">
            {#each competitorAnalysis?.negative_keyword_suggestions || [] as nk}
              <button 
                type="button"
                class="px-2 py-1 border text-[9px] transition-all cursor-pointer rounded-none {importedItems.includes(nk) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-red-500/10 border-red-500/20 text-red-400 hover:bg-red-500 hover:text-white'}"
                onclick={() => trackImport(nk, () => {
                  addNegativeKeyword(nk);
                  negativeKeywords = [...(negativeKeywords || []), { text: nk }];
                })}
                disabled={importedItems.includes(nk)}
                title={importedItems.includes(nk) ? "Đã thêm vào phủ định" : "Thêm vào danh sách phủ định"}
              >
                {importedItems.includes(nk) ? '✓ ' + nk : '+ ' + nk}
              </button>
            {/each}
          </div>
        </div>

        {#if competitorAnalysis?.seo_gaps}
          <div class="border border-yellow-500/30 bg-yellow-500/5 p-4 rounded-none space-y-2 text-left">
            <div class="flex items-center gap-2 text-yellow-500 relative">
              <AlertTriangle size={14} />
              <span class="text-[9px] font-black uppercase">Kẽ hở so với đối thủ</span>
              <div class="relative group cursor-pointer inline-flex items-center">
                <Info size={11} class="text-yellow-500/60 hover:text-yellow-400 transition-colors" />
                <span class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-48 bg-slate-950 border border-yellow-500/30 text-yellow-200 text-[8px] p-2 rounded shadow-2xl leading-normal z-50 whitespace-normal">
                  So sánh trực tiếp trang đích với đối thủ trên Google Search để tìm khoảng trống về: Social Proof, CTA, và độ dài/độ sâu nội dung tối ưu cho Google SGE.
                </span>
              </div>
            </div>
            <p class="text-[10px] text-yellow-200/80 leading-relaxed text-left">
              {competitorAnalysis.seo_gaps}
            </p>
          </div>
        {/if}
      </div>
    {/if}
  </div>
{/if}
