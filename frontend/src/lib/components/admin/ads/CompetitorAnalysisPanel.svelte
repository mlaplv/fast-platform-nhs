<script lang="ts">
  import { slide, fade } from 'svelte/transition';
  import type { CompetitorAnalysisResponse } from './adsState.svelte';
  import Brain from "@lucide/svelte/icons/brain";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Search from "@lucide/svelte/icons/search";
  import AlertTriangle from "@lucide/svelte/icons/alert-triangle";
  import Maximize from "@lucide/svelte/icons/maximize";
  import X from "@lucide/svelte/icons/x";

  let {
    competitorUrl = $bindable(),
    competitorAnalyzing = false,
    competitorAnalysis = null,
    analyzeCompetitor,
    importKeyword,
    addNegativeKeyword,
    fAd = $bindable(),
    adGroupKeywords = $bindable(),
    negativeKeywords = $bindable()
  } = $props<{
    competitorUrl?: string;
    competitorAnalyzing?: boolean;
    competitorAnalysis?: CompetitorAnalysisResponse | null;
    analyzeCompetitor: (url: string) => void;
    importKeyword: (kw: string) => void;
    addNegativeKeyword: (text: string) => void;
    fAd?: {
      final_url: string;
      display_path1: string;
      display_path2: string;
      headlines: string[];
      descriptions: string[];
      status: string;
    };
    adGroupKeywords?: string[];
    negativeKeywords?: string[];
  }>();

  const fmt = (n: number) => new Intl.NumberFormat('vi-VN').format(Math.round(n));

  // Tab state: 'keywords' | 'headlines' | 'negatives_gaps'
  let activeTab = $state<'keywords' | 'headlines' | 'negatives_gaps'>('keywords');

  // Fullview Modal State
  let showFullview = $state(false);

  let importedItems = $state<string[]>([]);

  let activeSlotType = $state<'headline' | 'description'>('headline');
  let activeSlotIndex = $state(0);
  let highlightedSlot = $state<{ type: 'headline' | 'description'; index: number } | null>(null);

  function triggerSlotHighlight(type: 'headline' | 'description', index: number) {
    highlightedSlot = { type, index };
    setTimeout(() => {
      if (highlightedSlot?.type === type && highlightedSlot?.index === index) {
        highlightedSlot = null;
      }
    }, 1200);
  }

  function scrollSlotIntoView(type: 'headline' | 'description', index: number) {
    setTimeout(() => {
      const el = document.getElementById(`${type}-slot-${index}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        const input = el.querySelector('input');
        if (input) {
          input.focus();
        }
      }
    }, 50);
  }

  function handleImportKeyword(text: string) {
    if (!fAd) {
      importKeyword(text);
      return;
    }
    if (activeSlotType === 'headline') {
      fAd.headlines[activeSlotIndex] = text.slice(0, 30);
      fAd.headlines = [...fAd.headlines];
      triggerSlotHighlight('headline', activeSlotIndex);
      // Auto-advance
      const nextEmpty = fAd.headlines.findIndex((h, idx) => !h.trim() && idx > activeSlotIndex);
      if (nextEmpty !== -1) {
        activeSlotIndex = nextEmpty;
      } else {
        const anyEmpty = fAd.headlines.findIndex(h => !h.trim());
        if (anyEmpty !== -1) activeSlotIndex = anyEmpty;
      }
      scrollSlotIntoView('headline', activeSlotIndex);
    } else {
      fAd.descriptions[activeSlotIndex] = text.slice(0, 90);
      fAd.descriptions = [...fAd.descriptions];
      triggerSlotHighlight('description', activeSlotIndex);
      // Auto-advance
      const nextEmpty = fAd.descriptions.findIndex((d, idx) => !d.trim() && idx > activeSlotIndex);
      if (nextEmpty !== -1) {
        activeSlotIndex = nextEmpty;
      } else {
        const anyEmpty = fAd.descriptions.findIndex(d => !d.trim());
        if (anyEmpty !== -1) activeSlotIndex = anyEmpty;
      }
      scrollSlotIntoView('description', activeSlotIndex);
    }
  }

  function trackImport(text: string, action: () => void) {
    action();
    if (!importedItems.includes(text)) {
      importedItems = [...importedItems, text];
    }
  }

  // Drag and Drop State & Handlers
  let dragOverSlot = $state<{ type: 'headline' | 'description'; index: number } | null>(null);
  let dragOverAdGroupKeywords = $state(false);

  function handleDragStart(event: DragEvent, text: string) {
    if (event.dataTransfer) {
      event.dataTransfer.setData('text/plain', text);
      event.dataTransfer.effectAllowed = 'copy';
    }
  }

  function handleDragOverSlot(event: DragEvent, type: 'headline' | 'description', index: number) {
    event.preventDefault();
    dragOverSlot = { type, index };
  }

  function handleDragLeave() {
    dragOverSlot = null;
  }

  function handleDropSlot(event: DragEvent, type: 'headline' | 'description', index: number) {
    event.preventDefault();
    dragOverSlot = null;
    const text = event.dataTransfer?.getData('text/plain');
    if (!text) return;

    if (type === 'headline') {
      fAd.headlines[index] = text.slice(0, 30);
      fAd.headlines = [...fAd.headlines];
      triggerSlotHighlight('headline', index);
    } else {
      fAd.descriptions[index] = text.slice(0, 90);
      fAd.descriptions = [...fAd.descriptions];
      triggerSlotHighlight('description', index);
    }

    if (!importedItems.includes(text)) {
      importedItems = [...importedItems, text];
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

    if (!adGroupKeywords.includes(text)) {
      adGroupKeywords = [...adGroupKeywords, text];
    }

    if (!importedItems.includes(text)) {
      importedItems = [...importedItems, text];
    }
  }
</script>

<div class="bg-purple-950/20 border border-purple-500/30 p-6 rounded-none relative overflow-hidden group/intel">
  <div class="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent pointer-events-none"></div>
  
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center gap-3">
      <div class="p-2 bg-purple-500/10 border border-purple-500/20 rounded-none text-purple-400">
        <Brain size={16} />
      </div>
      <h5 class="text-xs font-black text-white tracking-widest font-mono uppercase text-left">Trinh sát trang đích đối thủ</h5>
    </div>
    {#if competitorAnalysis}
      <button 
        type="button"
        class="px-2.5 py-1.5 bg-purple-500/10 border border-purple-500/20 text-purple-300 hover:bg-purple-600 hover:text-white transition-all rounded-none font-mono text-[9px] flex items-center gap-1.5 shrink-0"
        onclick={() => showFullview = true}
        title="Xem chế độ Fullview phóng to"
      >
        <Maximize size={10} />
        <span>PHÓNG TO</span>
      </button>
    {/if}
  </div>

  <!-- Input URL to analyze -->
  <div class="space-y-3 mb-4">
    <p class="text-[9px] text-purple-300/70 font-mono text-left">Nhập link để trích xuất chiến thuật, từ khóa và tiêu đề thực tế:</p>
    <div class="flex gap-2">
      <input 
        type="text" 
        bind:value={competitorUrl} 
        class="flex-1 bg-black/60 border border-purple-500/30 rounded-none p-3 text-xs text-white focus:border-purple-400 outline-none font-mono" 
        placeholder="Nhập URL đối thủ..." 
      />
      <button 
        class="px-4 py-3 bg-purple-600 text-white text-[10px] font-black tracking-widest hover:bg-purple-500 transition-all flex items-center gap-2 rounded-none"
        onclick={() => analyzeCompetitor(competitorUrl)}
        disabled={competitorAnalyzing}
      >
        {#if competitorAnalyzing}
          <RefreshCw size={12} class="animate-spin" />
        {:else}
          <Search size={12} />
        {/if}
        <span>PHÂN TÍCH</span>
      </button>
    </div>
  </div>

  {#if competitorAnalysis}
    <div class="space-y-4 pt-4 border-t border-purple-500/20" transition:slide>
      
      <!-- Summary -->
      <div class="space-y-2">
        <span class="text-[9px] text-purple-400 font-mono font-black block text-left">TỔM TẮT TRANG ĐÍCH</span>
        <p class="text-[10px] text-slate-300 bg-black/40 p-3 border border-white/5 leading-relaxed text-left">
          {competitorAnalysis.page_summary || 'Không có tóm tắt.'}
        </p>
      </div>

      <!-- Tabs Navigation -->
      <div class="flex border-b border-purple-500/30 bg-black/40 font-mono text-[9px] mt-2">
        <button 
          type="button"
          class="flex-1 py-2 text-center font-black transition-all border-b-2 {activeTab === 'keywords' ? 'border-purple-500 text-white bg-purple-500/10' : 'border-transparent text-slate-400 hover:text-white hover:bg-white/5'}"
          onclick={() => activeTab = 'keywords'}
        >
          TỪ KHÓA ({competitorAnalysis.keyword_suggestions?.length || 0})
        </button>
        <button 
          type="button"
          class="flex-1 py-2 text-center font-black transition-all border-b-2 {activeTab === 'headlines' ? 'border-purple-500 text-white bg-purple-500/10' : 'border-transparent text-slate-400 hover:text-white hover:bg-white/5'}"
          onclick={() => activeTab = 'headlines'}
        >
          TIÊU ĐỀ ({competitorAnalysis.competitor_headlines?.length || 0})
        </button>
        <button 
          type="button"
          class="flex-1 py-2 text-center font-black transition-all border-b-2 {activeTab === 'negatives_gaps' ? 'border-purple-500 text-white bg-purple-500/10' : 'border-transparent text-slate-400 hover:text-white hover:bg-white/5'}"
          onclick={() => activeTab = 'negatives_gaps'}
        >
          PHỦ ĐỊNH & KẼ HỞ
        </button>
      </div>

      <!-- Tab Content Area -->
      <div class="pt-2">
        {#if activeTab === 'keywords'}
          <!-- Keyword suggestions table -->
          <div class="space-y-2" transition:slide>
            <div class="overflow-hidden border border-white/5 bg-black/40 rounded-none">
              <table class="w-full text-left font-mono text-[9px]">
                <thead class="bg-[#120d1e] z-10">
                  <tr class="text-slate-500 font-black">
                    <th class="p-2">Từ khóa</th>
                    <th class="p-2">Intent</th>
                    <th class="p-2">Volume</th>
                    <th class="p-2">CPC</th>
                    <th class="p-2 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody class="text-slate-300">
                  {#each competitorAnalysis.keyword_suggestions || [] as kw}
                    <tr class="border-b border-white/5 hover:bg-purple-500/10 group/kw">
                      <td class="p-2 font-bold text-white text-left cursor-grab active:cursor-grabbing hover:text-purple-300" draggable="true" ondragstart={(e) => handleDragStart(e, kw.keyword)}>
                        <div class="flex items-center gap-1.5">
                          <span class="inline-block w-1.5 h-1.5 bg-purple-400"></span>
                          {kw.keyword}
                        </div>
                      </td>
                      <td class="p-2 text-left">
                        <span class="px-1.5 py-0.5 rounded-none text-[8px] {kw.intent === 'COMMERCIAL' ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'}">
                          {kw.intent === 'COMMERCIAL' ? 'MUA' : 'TÌM HIỂU'}
                        </span>
                      </td>
                      <td class="p-2 text-left">{kw.estimated_volume || 'N/A'}</td>
                      <td class="p-2 text-left">{kw.estimated_cpc_vnd ? fmt(kw.estimated_cpc_vnd) : 'N/A'}₫</td>
                      <td class="p-2 text-right">
                        <button 
                          class="px-2 py-1 border rounded-none font-bold transition-all {importedItems.includes(kw.keyword) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-purple-500/20 text-purple-300 border-purple-500/30 hover:bg-purple-500 hover:text-white animate-pulse'}"
                          onclick={() => trackImport(kw.keyword, () => {
                            if (!adGroupKeywords.includes(kw.keyword)) {
                              adGroupKeywords = [...adGroupKeywords, kw.keyword];
                            }
                          })}
                          disabled={importedItems.includes(kw.keyword)}
                          title={importedItems.includes(kw.keyword) ? "Đã thêm vào tiêu đề" : "Thêm vào tiêu đề quảng cáo"}
                        >
                          {importedItems.includes(kw.keyword) ? 'ĐÃ THÊM' : '+ THÊM'}
                        </button>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {:else if activeTab === 'headlines'}
          <!-- Competitor headlines -->
          <div class="space-y-2 text-left" transition:slide>
            <div class="space-y-2">
              {#each competitorAnalysis.competitor_headlines || [] as ch}
                <div class="bg-black/30 border border-white/5 p-3 flex justify-between items-center gap-3 group/ch hover:border-purple-500/30 cursor-grab active:cursor-grabbing" draggable="true" ondragstart={(e) => handleDragStart(e, ch.headline)}>
                  <div class="flex flex-col gap-1 min-w-0 text-left">
                    <span class="text-[10px] text-white font-black truncate">{ch.headline}</span>
                    <span class="text-[8px] text-purple-400 truncate">{ch.source_domain}</span>
                  </div>
                  <button 
                    class="px-2 py-1 border rounded-none text-[9px] font-mono font-bold shrink-0 transition-all {importedItems.includes(ch.headline) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-purple-500/20 text-purple-300 border-purple-500/30 hover:bg-purple-500 hover:text-white'}"
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
          <!-- Negative Keywords & Gaps -->
          <div class="space-y-4 text-left" transition:slide>
            <!-- Negative Keywords -->
            <div class="space-y-2">
              <span class="text-[9px] text-purple-400 font-mono font-black block text-left">GỢI Ý TỪ KHÓA PHỦ ĐỊNH (CLICK ĐỂ THÊM)</span>
              <div class="flex flex-wrap gap-2 text-left">
                {#each competitorAnalysis.negative_keyword_suggestions || [] as nk}
                  <button 
                    type="button"
                    class="px-2 py-1 border text-[9px] font-mono transition-all cursor-pointer rounded-none {importedItems.includes(nk) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-red-500/10 border-red-500/20 text-red-400 hover:bg-red-500 hover:text-white'}"
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

            <!-- Gaps warnings -->
            {#if competitorAnalysis.seo_gaps}
              <div class="border border-yellow-500/30 bg-yellow-500/5 p-4 rounded-none space-y-2 text-left">
                <div class="flex items-center gap-2 text-yellow-500">
                  <AlertTriangle size={14} />
                  <span class="text-[9px] font-black font-mono uppercase">Kẽ hở so với đối thủ</span>
                </div>
                <p class="text-[10px] text-yellow-200/80 leading-relaxed font-mono text-left">
                  {competitorAnalysis.seo_gaps}
                </p>
              </div>
            {/if}
          </div>
        {/if}
      </div>

    </div>
  {/if}
</div>

<!-- FULLVIEW MODAL OVERLAY -->
{#if showFullview && competitorAnalysis}
  <div class="fixed inset-0 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 lg:p-8 z-[9999]" transition:fade>
    <div class="bg-slate-950 border border-purple-500/30 p-6 lg:p-8 w-full max-w-7xl max-h-[95vh] overflow-y-auto relative rounded-none flex flex-col shadow-2xl">
      
      <!-- Modal Header -->
      <div class="flex justify-between items-start border-b border-purple-500/20 pb-4 mb-6">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-purple-500/10 border border-purple-500/20 rounded-none text-purple-400">
            <Brain size={18} />
          </div>
          <div>
            <h4 class="text-sm font-black text-white tracking-widest font-mono uppercase text-left">Trinh sát chi tiết đối thủ</h4>
            <p class="text-[10px] text-purple-400 font-mono mt-1 font-bold truncate max-w-2xl text-left">
              Đang phân tích URL: {competitorUrl || competitorAnalysis.page_title}
            </p>
          </div>
        </div>
        <button 
          type="button"
          class="p-2 bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-red-600 transition-all rounded-none"
          onclick={() => showFullview = false}
        >
          <X size={16} />
        </button>
      </div>

      <!-- Modal Body -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1 min-h-0 text-slate-300">
        
        {#if fAd}
          <!-- LEFT COLUMN: AD TEMPLATE BUILDER (4 Cols) -->
          <div class="lg:col-span-4 border-r border-purple-500/20 pr-6 flex flex-col space-y-4 max-h-[75vh] overflow-y-auto pr-2">
            <div class="flex items-center gap-2 text-cyan-400 font-mono font-black text-xs uppercase mb-2">
              <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
              <span>BIÊN TẬP QUẢNG CÁO (REAL-TIME)</span>
            </div>

            <!-- Final URL & Paths -->
            <div class="space-y-3 bg-black/40 p-4 border border-white/5">
              <div>
                <span class="block text-[9px] text-slate-500 font-black tracking-widest font-mono uppercase mb-1">Final URL (Trang đích)</span>
                <input 
                  type="text" 
                  bind:value={fAd.final_url} 
                  class="w-full bg-black/80 border border-white/10 p-2 text-xs font-mono text-white outline-none focus:border-cyan-400/50" 
                  placeholder="https://example.com..." 
                />
              </div>
              <div>
                <span class="block text-[9px] text-slate-500 font-black tracking-widest font-mono uppercase mb-1">Đường dẫn hiển thị</span>
                <div class="flex items-center bg-black/80 border border-white/10 px-2 py-1">
                  <span class="text-[10px] text-slate-600 font-mono select-none">/</span>
                  <input 
                    type="text" 
                    bind:value={fAd.display_path1} 
                    maxlength="15"
                    class="w-full bg-transparent border-none p-1 text-xs font-mono text-white outline-none focus:text-cyan-400" 
                    placeholder="path1" 
                  />
                  <span class="text-[10px] text-slate-600 font-mono select-none">/</span>
                  <input 
                    type="text" 
                    bind:value={fAd.display_path2} 
                    maxlength="15"
                    class="w-full bg-transparent border-none p-1 text-xs font-mono text-white outline-none focus:text-cyan-400" 
                    placeholder="path2" 
                  />
                </div>
              </div>
            </div>

            <!-- Headlines slots -->
            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <span class="text-[9px] text-slate-400 font-black tracking-widest font-mono uppercase">15 DÒNG TIÊU ĐỀ</span>
                <span class="text-[9px] font-mono font-black text-cyan-400">
                  Chỉ định điền: #{activeSlotIndex + 1}
                </span>
              </div>
              <div class="space-y-1.5 pr-1">
                {#each Array(15) as _, i}
                  <div 
                    id="headline-slot-{i}"
                    class="relative flex items-center bg-black/40 border transition-all duration-300 {activeSlotType === 'headline' && activeSlotIndex === i ? 'border-purple-500 ring-1 ring-purple-500/50' : 'border-white/5'} {highlightedSlot?.type === 'headline' && highlightedSlot?.index === i ? 'border-emerald-500 bg-emerald-950/20 ring-1 ring-emerald-500/50 animate-pulse scale-[1.02]' : ''} {dragOverSlot?.type === 'headline' && dragOverSlot?.index === i ? 'border-dashed border-cyan-400 bg-cyan-950/20' : ''}"
                    ondragover={(e) => handleDragOverSlot(e, 'headline', i)}
                    ondragleave={handleDragLeave}
                    ondrop={(e) => handleDropSlot(e, 'headline', i)}
                  >
                    <span class="pl-2 text-[9px] font-mono text-slate-600 font-black select-none w-5">#{i+1}</span>
                    <input 
                      type="text" 
                      bind:value={fAd.headlines[i]} 
                      maxlength="30"
                      onfocus={() => { activeSlotType = 'headline'; activeSlotIndex = i; }}
                      class="w-full bg-transparent border-none py-1.5 px-2 text-[11px] text-white outline-none font-mono" 
                      placeholder="Chọn vị trí này để điền..." 
                    />
                    <span class="pr-2 text-[8px] font-mono text-slate-600 select-none">{(fAd.headlines[i] || '').length}/30</span>
                  </div>
                {/each}
              </div>
            </div>

            <!-- Descriptions slots -->
            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <span class="text-[9px] text-slate-400 font-black tracking-widest font-mono uppercase">4 DÒNG MÔ TẢ</span>
              </div>
              <div class="space-y-1.5 pr-1">
                {#each Array(4) as _, i}
                  <div 
                    id="description-slot-{i}"
                    class="relative flex items-center bg-black/40 border transition-all duration-300 {activeSlotType === 'description' && activeSlotIndex === i ? 'border-purple-500 ring-1 ring-purple-500/50' : 'border-white/5'} {highlightedSlot?.type === 'description' && highlightedSlot?.index === i ? 'border-emerald-500 bg-emerald-950/20 ring-1 ring-emerald-500/50 animate-pulse scale-[1.02]' : ''} {dragOverSlot?.type === 'description' && dragOverSlot?.index === i ? 'border-dashed border-cyan-400 bg-cyan-950/20' : ''}"
                    ondragover={(e) => handleDragOverSlot(e, 'description', i)}
                    ondragleave={handleDragLeave}
                    ondrop={(e) => handleDropSlot(e, 'description', i)}
                  >
                    <span class="pl-2 text-[9px] font-mono text-slate-600 font-black select-none w-14">Mô tả #{i+1}</span>
                    <input 
                      type="text" 
                      bind:value={fAd.descriptions[i]} 
                      maxlength="90"
                      onfocus={() => { activeSlotType = 'description'; activeSlotIndex = i; }}
                      class="w-full bg-transparent border-none py-1.5 px-2 text-[11px] text-white outline-none font-mono" 
                      placeholder="Chọn vị trí này để điền..." 
                    />
                    <span class="pr-2 text-[8px] font-mono text-slate-600 select-none">{(fAd.descriptions[i] || '').length}/90</span>
                  </div>
                {/each}
              </div>
            </div>

          </div>
        {/if}

        <!-- RIGHT COLUMN: INTEL SCOUT (8 or 12 Cols) -->
        <div class="space-y-6 max-h-[78vh] overflow-y-auto pr-2 {fAd ? 'lg:col-span-8' : 'lg:col-span-12'}">
          <!-- Summary Callout -->
          <div class="bg-purple-950/20 border border-purple-500/20 p-5 backdrop-blur-sm rounded-none">
            <span class="text-[10px] text-purple-400 font-mono font-black block text-left mb-2 tracking-wider">🎯 TỔM TẮT TRANG ĐÍCH ĐỐI THỦ</span>
            <p class="text-xs text-slate-300 leading-relaxed text-left font-mono">
              {competitorAnalysis.page_summary || 'Không có tóm tắt.'}
            </p>
          </div>

          <!-- Section 1: Target Keywords (Full Width of Right Column) -->
          <div class="space-y-3 bg-black/40 p-5 border border-white/5 rounded-none">
            <span class="text-[11px] text-purple-400 font-mono font-black block text-left uppercase tracking-widest border-b border-purple-500/10 pb-2">🎯 DANH SÁCH TỪ KHÓA MỤC TIÊU ({competitorAnalysis.keyword_suggestions?.length || 0})</span>
            <div class="overflow-hidden border border-white/5 bg-black/60 rounded-none max-h-[280px] overflow-y-auto">
              <table class="w-full text-left font-mono text-[10px]">
                <thead class="bg-[#0f0b1a] sticky top-0 z-10">
                  <tr class="text-slate-500 font-black border-b border-white/5">
                    <th class="p-3">Từ khóa</th>
                    <th class="p-3">Intent</th>
                    <th class="p-3">Volume</th>
                    <th class="p-3">CPC</th>
                    <th class="p-3 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody class="text-slate-300">
                  {#each competitorAnalysis.keyword_suggestions || [] as kw}
                    <tr class="border-b border-white/5 hover:bg-purple-500/10 group/kw">
                      <td class="p-3 font-bold text-white text-left">{kw.keyword}</td>
                      <td class="p-3 text-left">
                        <span class="px-1.5 py-0.5 rounded-none text-[8px] {kw.intent === 'COMMERCIAL' ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'}">
                          {kw.intent === 'COMMERCIAL' ? 'MUA' : 'TÌM HIỂU'}
                        </span>
                      </td>
                      <td class="p-3 text-left">{kw.estimated_volume || 'N/A'}</td>
                      <td class="p-3 text-left">{kw.estimated_cpc_vnd ? fmt(kw.estimated_cpc_vnd) : 'N/A'}₫</td>
                      <td class="p-3 text-right">
                        <button 
                          class="px-2.5 py-1 border rounded-none text-[9px] font-bold transition-all {importedItems.includes(kw.keyword) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-purple-550 text-white hover:bg-purple-500'}"
                          onclick={() => trackImport(kw.keyword, () => {
                            if (!adGroupKeywords.includes(kw.keyword)) {
                              adGroupKeywords = [...adGroupKeywords, kw.keyword];
                            }
                          })}
                          disabled={importedItems.includes(kw.keyword)}
                        >
                          {importedItems.includes(kw.keyword) ? 'ĐÃ THÊM' : '+ THÊM'}
                        </button>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
            
            <!-- Real-time Current Ad Group Keywords (Drop zone) -->
            <div 
              class="pt-4 border-t border-white/5 text-left transition-all duration-200 {dragOverAdGroupKeywords ? 'bg-cyan-950/15 border-dashed border-cyan-400/50' : 'bg-transparent'}"
              ondragover={handleDragOverAdGroup}
              ondragleave={() => dragOverAdGroupKeywords = false}
              ondrop={handleDropAdGroup}
            >
              <span class="text-[9px] text-slate-500 font-mono font-black block uppercase mb-2">
                TỪ KHÓA HIỆN CÓ CỦA NHÓM ({adGroupKeywords?.length || 0})
                <span class="text-[8px] text-cyan-400/50 normal-case ml-2">(Kéo thả từ khóa vào đây để thêm)</span>
              </span>
              <div class="flex flex-wrap gap-1.5 max-h-[100px] overflow-y-auto min-h-[36px] border border-white/5 p-2 bg-black/20">
                {#each adGroupKeywords || [] as akw}
                  <span class="px-2 py-0.5 bg-cyan-950/20 border border-cyan-500/20 text-cyan-400 text-[9px] font-mono">
                    {akw}
                  </span>
                {:else}
                  <span class="text-[9px] text-slate-600 font-mono italic">Kéo thả từ khóa vào đây...</span>
                {/each}
              </div>
            </div>
          </div>

          <!-- Section 2: Competitor Headlines (Full Width of Right Column, 2-Column Grid Layout) -->
          <div class="space-y-3 bg-black/40 p-5 border border-white/5 rounded-none">
            <span class="text-[11px] text-purple-400 font-mono font-black block text-left uppercase tracking-widest border-b border-purple-500/10 pb-2">📢 TIÊU ĐỀ QUẢNG CÁO ĐỐI THỦ ({competitorAnalysis.competitor_headlines?.length || 0})</span>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[250px] overflow-y-auto pr-1 text-left">
              {#each competitorAnalysis.competitor_headlines || [] as ch}
                <div class="bg-black/30 border border-white/5 p-3 flex justify-between items-center gap-3 group/ch hover:border-purple-500/30 rounded-none transition-all cursor-grab active:cursor-grabbing" draggable="true" ondragstart={(e) => handleDragStart(e, ch.headline)}>
                  <div class="flex flex-col gap-1 min-w-0 text-left">
                    <span class="text-xs text-white font-black truncate">{ch.headline}</span>
                    <span class="text-[9px] text-purple-400 truncate">{ch.source_domain}</span>
                  </div>
                  <button 
                    class="px-2.5 py-1 border rounded-none text-[10px] font-mono font-bold shrink-0 transition-all {importedItems.includes(ch.headline) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-purple-600 text-white hover:bg-purple-500'}"
                    onclick={() => trackImport(ch.headline, () => handleImportKeyword(ch.headline))}
                    disabled={importedItems.includes(ch.headline)}
                  >
                    {importedItems.includes(ch.headline) ? 'ĐÃ DÙNG' : 'DÙNG'}
                  </button>
                </div>
              {/each}
            </div>
          </div>

          <!-- Section 3: Negatives & Gaps (2-Column Split Layout) -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-black/40 p-5 border border-white/5 rounded-none">
            <!-- Left: Negatives -->
            <div class="space-y-3 md:border-r md:border-white/5 md:pr-6">
              <span class="text-[10px] text-purple-400 font-mono font-black block text-left uppercase tracking-wider mb-2">🛑 GỢI Ý TỪ KHÓA PHỦ ĐỊNH (CLICK ĐỂ THÊM)</span>
              <div class="flex flex-wrap gap-2 text-left">
                {#each competitorAnalysis.negative_keyword_suggestions || [] as nk}
                  <button 
                    type="button"
                    class="px-2.5 py-1 border text-[10px] font-mono transition-all cursor-pointer rounded-none {importedItems.includes(nk) ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-red-500/10 border-red-500/20 text-red-400 hover:bg-red-500 hover:text-white'}"
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
              
              <!-- Real-time Current Campaign Negatives -->
              {#if negativeKeywords && negativeKeywords.length > 0}
                <div class="mt-4 pt-4 border-t border-white/10 text-left">
                  <span class="text-[9px] text-slate-500 font-mono font-black block uppercase mb-2">PHỦ ĐỊNH CHIẾN DỊCH ĐÃ CÓ ({negativeKeywords.length})</span>
                  <div class="flex flex-wrap gap-1.5 max-h-[100px] overflow-y-auto">
                    {#each negativeKeywords as nk}
                      <span class="px-2 py-0.5 bg-red-950/20 border border-red-500/20 text-red-400 text-[9px] font-mono">
                        {nk.text || nk}
                      </span>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>

            <!-- Right: Gaps -->
            <div class="space-y-3 md:pl-2">
              <span class="text-[10px] text-yellow-500 font-mono font-black block text-left uppercase tracking-wider mb-2">⚠️ KẼ HỞ CẠNH TRANH (SEO GAPS)</span>
              {#if competitorAnalysis.seo_gaps}
                <div class="border border-yellow-500/30 bg-yellow-500/5 p-4 rounded-none space-y-2 text-left">
                  <div class="flex items-center gap-2 text-yellow-500">
                    <AlertTriangle size={14} />
                    <span class="text-[10px] font-black font-mono uppercase">Phân tích khoảng trống</span>
                  </div>
                  <p class="text-xs text-yellow-200/80 leading-relaxed font-mono text-left">
                    {competitorAnalysis.seo_gaps}
                  </p>
                </div>
              {:else}
                <p class="text-xs text-slate-500 font-mono text-left">Không phát hiện kẽ hở cạnh tranh nào.</p>
              {/if}
            </div>
          </div>

        </div>
      </div>

    </div>
  </div>
{/if}
