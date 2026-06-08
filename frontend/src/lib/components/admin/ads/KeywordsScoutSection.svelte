<script lang="ts">
  import { slide } from 'svelte/transition';
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";

  let {
    competitorAnalysis = null,
    adGroupKeywords = $bindable([]),
    importedItems = $bindable([]),
    selectedMatchType = $bindable('PHRASE'),
    viewMode = $bindable('list'),
    hideLowQualityKeywords = $bindable(true),
    deletingKeywords = $bindable([]),
    addAdGroupKeywords,
    removeAdGroupKeyword,
    fullview = false
  } = $props<{
    competitorAnalysis?: any;
    adGroupKeywords: string[];
    importedItems: string[];
    selectedMatchType: 'EXACT' | 'PHRASE' | 'BROAD';
    viewMode: 'list' | 'cluster';
    hideLowQualityKeywords: boolean;
    deletingKeywords: string[];
    addAdGroupKeywords: (keywords: string[], matchType?: string) => Promise<boolean>;
    removeAdGroupKeyword: (keyword: string) => Promise<void>;
    fullview?: boolean;
  }>();

  const fmt = (n: number) => new Intl.NumberFormat('vi-VN').format(Math.round(n));

  let batchImporting = $state(false);
  let dragOverAdGroupKeywords = $state(false);

  function getKeywordInfo(kwText: string) {
    if (!kwText || !competitorAnalysis?.keyword_suggestions) return null;
    const kwLower = kwText.toLowerCase().trim();
    return competitorAnalysis.keyword_suggestions.find(
      (s: any) => s.keyword.toLowerCase().trim() === kwLower
    ) || null;
  }

  function parseVolume(volStr: string | number | undefined | null): number {
    if (!volStr) return 0;
    const str = String(volStr).toUpperCase().trim();
    if (str.includes('<')) {
      const num = parseFloat(str.replace(/[^0-9.]/g, ''));
      return isNaN(num) ? 0 : num - 1;
    }
    if (str.includes('K')) {
      const num = parseFloat(str.replace(/[^0-9.]/g, ''));
      return isNaN(num) ? 0 : num * 1000;
    }
    if (str.includes('M')) {
      const num = parseFloat(str.replace(/[^0-9.]/g, ''));
      return isNaN(num) ? 0 : num * 1000000;
    }
    const num = parseFloat(str.replace(/[^0-9.]/g, ''));
    return isNaN(num) ? 0 : num;
  }

  const filteredKeywords = $derived(
    (competitorAnalysis?.keyword_suggestions || [])
      .filter((kw: any) => {
        if (!hideLowQualityKeywords) return true;
        return kw.estimated_volume !== '< 100' && kw.intent === 'COMMERCIAL' && kw.relevance === 'HIGH';
      })
      .sort((a: any, b: any) => parseVolume(b.estimated_volume) - parseVolume(a.estimated_volume))
  );

  const intentClusters = $derived({
    commercial: filteredKeywords.filter((k: any) => k.intent === 'COMMERCIAL'),
    informational: filteredKeywords.filter((k: any) => k.intent !== 'COMMERCIAL')
  });

  function isKeywordAdded(kwText: string): boolean {
    if (!kwText) return false;
    const kwLower = kwText.toLowerCase().trim();
    const inAdGroup = (adGroupKeywords || []).some(k => k.toLowerCase().trim() === kwLower);
    const inImported = importedItems.some(k => k.toLowerCase().trim() === kwLower);
    return inAdGroup || inImported;
  }

  function trackImport(text: string, action: () => void) {
    action();
    if (!importedItems.some(k => k.toLowerCase().trim() === text.toLowerCase().trim())) {
      importedItems = [...importedItems, text];
    }
  }

  async function handleBatchImport(keywords: string[]) {
    if (batchImporting || !keywords || keywords.length === 0) return;
    batchImporting = true;
    try {
      const success = await addAdGroupKeywords(keywords, selectedMatchType);
      if (success) {
        const newImports = [...importedItems];
        keywords.forEach(kw => {
          if (!newImports.some(item => item.toLowerCase().trim() === kw.toLowerCase().trim())) {
            newImports.push(kw);
          }
        });
        importedItems = newImports;
      }
    } finally {
      batchImporting = false;
    }
  }

  async function handleRemoveKeyword(keyword: string) {
    if (deletingKeywords.includes(keyword)) return;
    deletingKeywords = [...deletingKeywords, keyword];
    try {
      await removeAdGroupKeyword(keyword);
    } finally {
      deletingKeywords = deletingKeywords.filter(k => k !== keyword);
    }
  }

  function handleDragStart(event: DragEvent, text: string) {
    if (event.dataTransfer) {
      event.dataTransfer.setData('text/plain', text);
      event.dataTransfer.effectAllowed = 'copy';
    }
  }

  function handleDragOverAdGroup(event: DragEvent) {
    event.preventDefault();
    dragOverAdGroupKeywords = true;
  }

  function handleDropAdGroup(event: DragEvent) {
    event.preventDefault();
    dragOverAdGroupKeywords = false;
    const text = event.dataTransfer?.getData('text/plain');
    if (!text) return;

    trackImport(text, () => {
      addAdGroupKeywords([text]);
    });
  }
</script>

<div class="space-y-2 font-mono" transition:slide>
  <!-- SGE controls bar -->
  <div class="flex flex-col gap-3 border border-purple-500/20 bg-black/60 p-3 mb-2 text-[9px]">
    <div class="flex flex-wrap justify-between items-center gap-3">
      <div class="flex items-center gap-4">
        <!-- Match Type Select -->
        <div class="flex items-center gap-1.5">
          <span class="text-slate-400 font-bold">Đối sánh:</span>
          <select 
            bind:value={selectedMatchType} 
            class="bg-black border border-purple-500/30 text-white px-2 py-0.5 outline-none text-[8px] font-black focus:border-purple-400 rounded-none cursor-pointer"
          >
            <option value="EXACT">EXACT (Chính xác)</option>
            <option value="PHRASE">PHRASE (Cụm từ)</option>
            <option value="BROAD">BROAD (Mở rộng)</option>
          </select>
        </div>

        <!-- View Mode Toggle -->
        <div class="flex items-center gap-1.5 border border-purple-500/20 bg-black/60 p-0.5">
          <button 
            type="button" 
            class="px-2 py-0.5 text-[8px] font-black {viewMode === 'list' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'}"
            onclick={() => viewMode = 'list'}
          >
            DANH SÁCH
          </button>
          <button 
            type="button" 
            class="px-2 py-0.5 text-[8px] font-black {viewMode === 'cluster' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'}"
            onclick={() => viewMode = 'cluster'}
          >
            NHÓM Ý ĐỊNH
          </button>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <label class="inline-flex items-center gap-1.5 cursor-pointer select-none">
          <input 
            type="checkbox" 
            bind:checked={hideLowQualityKeywords} 
            class="rounded-none border-purple-500/30 bg-black/60 text-purple-500 focus:ring-0 w-3 h-3" 
          />
          <span class="text-[8px] text-slate-400">Chỉ từ khóa chất lượng cao (Volume >= 100, Intent MUA)</span>
        </label>
        
        {#if viewMode === 'list'}
          <button 
            type="button"
            class="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white text-[9px] font-black rounded-none active:scale-95 transition-all disabled:opacity-50"
            disabled={batchImporting || filteredKeywords.length === 0}
            onclick={() => {
              const toAdd = filteredKeywords.map(kw => kw.keyword);
              handleBatchImport(toAdd);
            }}
          >
            {#if batchImporting}
              ĐANG THÊM...
            {:else}
              + THÊM TẤT CẢ ({filteredKeywords.length})
            {/if}
          </button>
        {/if}
      </div>
    </div>
  </div>

  {#if viewMode === 'list'}
    <!-- List View (Standard Table) -->
    <div class="overflow-hidden border border-white/5 rounded-none {fullview ? 'bg-black/60 max-h-[350px] overflow-y-auto' : 'bg-black/40'}">
      <table class="w-full text-left {fullview ? 'text-[10px]' : 'text-[9px]'}">
        <thead class="bg-[#0f0b1a] sticky top-0 z-10">
          <tr class="text-slate-500 font-black border-b border-white/5">
            <th class="p-2.5">Từ khóa</th>
            <th class="p-2.5">Intent</th>
            <th class="p-2.5">Volume</th>
            <th class="p-2.5">CPC</th>
            <th class="p-2.5">Trạng thái</th>
            <th class="p-2.5 text-right">Thao tác</th>
          </tr>
        </thead>
        <tbody class="text-slate-300">
          {#each filteredKeywords as kw}
            <tr class="border-b border-white/5 hover:bg-purple-500/10 group/kw">
              <td class="p-2.5 text-left">
                <div 
                  class="flex items-center gap-1.5 cursor-grab active:cursor-grabbing hover:text-purple-300 font-bold text-white" 
                  draggable="true" 
                  ondragstart={(e) => handleDragStart(e, kw.keyword)}
                >
                  <span class="inline-block w-1.5 h-1.5 bg-purple-400"></span>
                  {kw.keyword}
                </div>
              </td>
              <td class="p-2.5 text-left">
                <span class="px-1.5 py-0.5 rounded-none text-[8px] {kw.intent === 'COMMERCIAL' ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'}">
                  {kw.intent === 'COMMERCIAL' ? 'MUA' : 'TÌM HIỂU'}
                </span>
              </td>
              <td class="p-2.5 text-left">{kw.estimated_volume || 'N/A'}</td>
              <td class="p-2.5 text-left">{kw.estimated_cpc_vnd ? fmt(kw.estimated_cpc_vnd) : 'N/A'}₫</td>
              <td class="p-2.5 text-left">
                {#if kw.estimated_volume === '< 100'}
                  <span class="px-1 py-0.5 bg-red-500/10 text-red-400 text-[8px] font-black border border-red-500/20">VOLUME THẤP</span>
                {:else if kw.intent !== 'COMMERCIAL'}
                  <span class="px-1 py-0.5 bg-amber-500/10 text-amber-400 text-[8px] font-black border border-amber-500/20">Ý ĐỊNH THẤP</span>
                {:else}
                  <span class="px-1 py-0.5 bg-emerald-500/10 text-emerald-400 text-[8px] font-black border border-emerald-500/20">ĐỦ ĐIỀU KIỆN</span>
                {/if}
              </td>
              <td class="p-2.5 text-right">
                <button 
                  class="px-2 py-1 border rounded-none font-bold transition-all {isKeywordAdded(kw.keyword) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-purple-550 text-white hover:bg-purple-500'}"
                  onclick={() => trackImport(kw.keyword, () => {
                    addAdGroupKeywords([kw.keyword], selectedMatchType);
                  })}
                  disabled={isKeywordAdded(kw.keyword)}
                >
                  {isKeywordAdded(kw.keyword) ? 'ĐÃ THÊM' : '+ THÊM'}
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <!-- Cluster View (Collapsible Intent Clusters) -->
    <div class="space-y-4 {fullview ? 'max-h-[350px] overflow-y-auto' : ''}">
      <!-- 1. Commercial Cluster -->
      <div class="border border-red-500/20 bg-red-950/5 p-3">
        <div class="flex justify-between items-center mb-2 border-b border-red-500/10 pb-2">
          <div class="flex items-center gap-2">
            <span class="text-xs">🛍️</span>
            <span class="font-black text-red-400 uppercase tracking-wider text-[9px]">NHÓM Ý ĐỊNH MUA SẮM (COMMERCIAL) - {intentClusters.commercial.length} TỪ KHÓA</span>
          </div>
          {#if intentClusters.commercial.length > 0}
            <button 
              type="button"
              class="px-2.5 py-1 bg-red-650 hover:bg-red-650/80 text-white text-[8px] font-black rounded-none active:scale-95 transition-all disabled:opacity-50"
              disabled={batchImporting}
              onclick={() => {
                const toAdd = intentClusters.commercial.map(kw => kw.keyword);
                handleBatchImport(toAdd);
              }}
            >
              {#if batchImporting}
                ĐANG THÊM...
              {:else}
                + THÊM CẢ NHÓM MUA SẮM
              {/if}
            </button>
          {/if}
        </div>

        {#if intentClusters.commercial.length === 0}
          <div class="text-slate-500 italic py-2 text-center text-[10px]">Không có từ khóa ý định mua sắm nào.</div>
        {:else}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-left">
            {#each intentClusters.commercial as kw}
              <div class="flex justify-between items-center bg-black/40 border border-white/5 p-2 hover:border-red-500/30 group/kw">
                <div 
                  class="flex items-center gap-1.5 cursor-grab active:cursor-grabbing hover:text-red-300 font-bold text-white truncate text-[10px]" 
                  draggable="true" 
                  ondragstart={(e) => handleDragStart(e, kw.keyword)}
                >
                  <span class="inline-block w-1.5 h-1.5 bg-red-400 shrink-0"></span>
                  <span class="truncate">{kw.keyword}</span>
                  <span class="text-[8px] text-slate-500 shrink-0">({kw.estimated_volume || '0'})</span>
                </div>
                <button 
                  class="px-2 py-0.5 border rounded-none font-bold text-[8px] shrink-0 transition-all {isKeywordAdded(kw.keyword) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-purple-550 text-white hover:bg-purple-500'}"
                  onclick={() => trackImport(kw.keyword, () => {
                    addAdGroupKeywords([kw.keyword], selectedMatchType);
                  })}
                  disabled={isKeywordAdded(kw.keyword)}
                >
                  {isKeywordAdded(kw.keyword) ? 'ĐÃ THÊM' : '+ THÊM'}
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- 2. Informational Cluster -->
      <div class="border border-blue-500/20 bg-blue-950/5 p-3">
        <div class="flex justify-between items-center mb-2 border-b border-blue-500/10 pb-2">
          <div class="flex items-center gap-2">
            <span class="text-xs">ℹ️</span>
            <span class="font-black text-blue-400 uppercase tracking-wider text-[9px]">NHÓM Ý ĐỊNH TÌM HIỂU (INFORMATIONAL) - {intentClusters.informational.length} TỪ KHÓA</span>
          </div>
          {#if intentClusters.informational.length > 0}
            <button 
              type="button"
              class="px-2.5 py-1 bg-blue-650 hover:bg-blue-650/80 text-white text-[8px] font-black rounded-none active:scale-95 transition-all disabled:opacity-50"
              disabled={batchImporting}
              onclick={() => {
                const toAdd = intentClusters.informational.map(kw => kw.keyword);
                handleBatchImport(toAdd);
              }}
            >
              {#if batchImporting}
                ĐANG THÊM...
              {:else}
                + THÊM CẢ NHÓM TÌM HIỂU
              {/if}
            </button>
          {/if}
        </div>

        {#if intentClusters.informational.length === 0}
          <div class="text-slate-500 italic py-2 text-center text-[10px]">Không có từ khóa tìm hiểu/tìm kiếm thông tin nào.</div>
        {:else}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-left">
            {#each intentClusters.informational as kw}
              <div class="flex justify-between items-center bg-black/40 border border-white/5 p-2 hover:border-blue-500/30 group/kw">
                <div 
                  class="flex items-center gap-1.5 cursor-grab active:cursor-grabbing hover:text-blue-300 font-bold text-white truncate text-[10px]" 
                  draggable="true" 
                  ondragstart={(e) => handleDragStart(e, kw.keyword)}
                >
                  <span class="inline-block w-1.5 h-1.5 bg-blue-400 shrink-0"></span>
                  <span class="truncate">{kw.keyword}</span>
                  <span class="text-[8px] text-slate-500 shrink-0">({kw.estimated_volume || '0'})</span>
                </div>
                <button 
                  class="px-2 py-0.5 border rounded-none font-bold text-[8px] shrink-0 transition-all {isKeywordAdded(kw.keyword) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-purple-550 text-white hover:bg-purple-500'}"
                  onclick={() => trackImport(kw.keyword, () => {
                    addAdGroupKeywords([kw.keyword], selectedMatchType);
                  })}
                  disabled={isKeywordAdded(kw.keyword)}
                >
                  {isKeywordAdded(kw.keyword) ? 'ĐÃ THÊM' : '+ THÊM'}
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {/if}
  
  <!-- Real-time Current Ad Group Keywords (Drop zone) -->
  <div class="pt-4 border-t border-white/5 text-left mt-4">
    <span class="text-[9px] text-slate-500 font-black block uppercase mb-2">
      TỪ KHÓA HIỆN CÓ CỦA NHÓM ({adGroupKeywords?.length || 0})
      <span class="text-[8px] text-cyan-400/50 normal-case ml-2">(Kéo thả từ khóa vào đây để thêm)</span>
    </span>
    <div 
      class="flex flex-wrap gap-1.5 max-h-[100px] overflow-y-auto min-h-[48px] border p-2 bg-black/20 transition-all duration-200 {dragOverAdGroupKeywords ? 'border-dashed border-cyan-400 bg-cyan-950/20' : 'border-white/5'}"
      ondragover={handleDragOverAdGroup}
      ondragleave={() => dragOverAdGroupKeywords = false}
      ondrop={handleDropAdGroup}
    >
       {#each adGroupKeywords || [] as akw}
          {@const info = getKeywordInfo(akw)}
          <span class="inline-flex items-center gap-1.5 px-2 py-0.5 bg-cyan-950/20 border border-cyan-500/20 text-cyan-400 text-[9px] {dragOverAdGroupKeywords ? 'pointer-events-none' : ''} {deletingKeywords.includes(akw) ? 'opacity-40 select-none' : ''}">
            <span class="font-bold">{akw}</span>
            {#if info}
              <span class="text-[8px] px-1 bg-cyan-500/10 border border-cyan-500/20 text-cyan-300/80">
                Vol: {info.estimated_volume}
              </span>
            {/if}
            {#if deletingKeywords.includes(akw)}
              <span class="animate-spin text-[8px] ml-1">⏳</span>
            {:else}
              <button 
                type="button" 
                class="text-cyan-400/60 hover:text-cyan-300 font-bold ml-1 cursor-pointer focus:outline-none"
                onclick={() => handleRemoveKeyword(akw)}
                disabled={deletingKeywords.includes(akw)}
              >
                ×
              </button>
            {/if}
          </span>
      {:else}
        <span class="text-[9px] text-slate-600 italic">Kéo thả từ khóa vào đây...</span>
      {/each}
    </div>
  </div>
</div>
