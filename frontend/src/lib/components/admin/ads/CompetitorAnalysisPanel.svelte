<script lang="ts">
  import { slide, fade } from 'svelte/transition';
  import type { CompetitorAnalysisResponse } from './adsState.svelte';
  import Brain from "@lucide/svelte/icons/brain";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Search from "@lucide/svelte/icons/search";
  import Maximize from "@lucide/svelte/icons/maximize";
  import X from "@lucide/svelte/icons/x";

  import GoogleSearchAdMockup from './GoogleSearchAdMockup.svelte';
  import PolicyShieldSection from './PolicyShieldSection.svelte';
  import KeywordsScoutSection from './KeywordsScoutSection.svelte';
  import PMaxUpgradeSection from './PMaxUpgradeSection.svelte';
  import AdAssetsAndGapsSection from './AdAssetsAndGapsSection.svelte';

  let {
    competitorUrl = $bindable(),
    competitorAnalyzing = false,
    competitorAnalysis = null,
    analyzeCompetitor,
    importKeyword,
    addNegativeKeyword,
    addAdGroupKeywords,
    removeAdGroupKeyword,
    fAd = $bindable(),
    adGroupKeywords = $bindable(),
    negativeKeywords = $bindable(),
    selectedCampaign = null,
    selectedAdGroup = null
  } = $props<{
    competitorUrl?: string;
    competitorAnalyzing?: boolean;
    competitorAnalysis?: CompetitorAnalysisResponse | null;
    analyzeCompetitor: (url: string) => void;
    importKeyword: (kw: string) => void;
    addNegativeKeyword: (text: string) => void;
    addAdGroupKeywords: (keywords: string[], matchType?: string) => Promise<boolean>;
    removeAdGroupKeyword: (keyword: string) => Promise<void>;
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
    selectedCampaign?: any;
    selectedAdGroup?: any;
  }>();

  // Match Type and View Mode states
  let selectedMatchType = $state<'EXACT' | 'PHRASE' | 'BROAD'>('PHRASE');
  let viewMode = $state<'list' | 'cluster'>('list');
  let activeTab = $state<'keywords' | 'headlines' | 'negatives_gaps'>('keywords');
  let showFullview = $state(false);
  let importedItems = $state<string[]>([]);
  let hideLowQualityKeywords = $state(true);
  let deletingKeywords = $state<string[]>([]);

  // Policy Shield state bound to PolicyShieldSection
  let policyShieldResults = $state<any>(null);
  let policyShieldLoading = $state(false);

  // Slot states for ad editing
  let activeSlotType = $state<'headline' | 'description'>('headline');
  let activeSlotIndex = $state(0);
  let highlightedSlot = $state<{ type: 'headline' | 'description'; index: number } | null>(null);
  let dragOverSlot = $state<{ type: 'headline' | 'description'; index: number } | null>(null);

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
      
      <!-- AI Policy Shield Box -->
      <PolicyShieldSection 
        view="scan"
        {selectedAdGroup}
        {fAd}
        {competitorUrl}
        {adGroupKeywords}
        bind:policyShieldResults
        bind:policyShieldLoading
      />

      <!-- Summary -->
      <div class="space-y-2">
        <span class="text-[9px] text-purple-400 font-mono font-black block text-left">TỔM TẮT TRANG ĐÍCH</span>
        <p class="text-[10px] text-slate-300 bg-black/40 p-3 border border-white/5 leading-relaxed text-left font-mono">
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
          <KeywordsScoutSection 
            {competitorAnalysis}
            bind:adGroupKeywords
            bind:importedItems
            bind:selectedMatchType
            bind:viewMode
            bind:hideLowQualityKeywords
            bind:deletingKeywords
            {addAdGroupKeywords}
            {removeAdGroupKeyword}
            fullview={false}
          />
        {:else}
          <AdAssetsAndGapsSection 
            {competitorAnalysis}
            bind:importedItems
            bind:negativeKeywords
            {addNegativeKeyword}
            {handleImportKeyword}
            fullview={false}
            {activeTab}
          />
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
            <div class="flex items-center gap-2 text-cyan-400 font-mono font-black text-xs uppercase mb-1">
              <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
              <span>BIÊN TẬP QUẢNG CÁO (REAL-TIME)</span>
            </div>

            <!-- OPTIMIZATION SCORE WIDGET -->
            <div class="bg-black/60 border border-purple-500/20 p-3 font-mono relative overflow-hidden text-left">
              <div class="flex justify-between items-center mb-1">
                <span class="text-[9px] text-slate-400 font-black tracking-wider uppercase">ĐIỂM TỐI ƯU HÓA CHÍNH SÁCH</span>
                <span class="text-xs font-black text-purple-400">
                  {policyShieldResults?.score !== undefined ? Math.round(policyShieldResults.score) : 100}%
                </span>
              </div>
              <div class="w-full bg-white/10 h-1.5 overflow-hidden relative">
                <div 
                  class="h-full transition-all duration-500 bg-gradient-to-r 
                    { (policyShieldResults?.score || 100) > 80 ? 'from-emerald-500 to-teal-400' :
                      (policyShieldResults?.score || 100) > 50 ? 'from-amber-500 to-orange-400' : 'from-rose-600 to-red-400'}"
                  style="width: {policyShieldResults?.score !== undefined ? policyShieldResults.score : 100}%"
                ></div>
              </div>
              <p class="text-[8px] text-slate-500 mt-1 leading-relaxed">
                {#if policyShieldResults?.score !== undefined}
                  {policyShieldResults.score === 100 ? 'Hoàn hảo! Quảng cáo đạt điểm chính sách tối đa.' : 'Lưu ý sửa các cảnh báo để cải thiện điểm số.'}
                {:else}
                  Chưa có dữ liệu quét chính sách.
                {/if}
              </p>
            </div>

            <!-- REAL-TIME GOOGLE SEARCH AD PREVIEW -->
            <GoogleSearchAdMockup 
              final_url={fAd.final_url} 
              display_path1={fAd.display_path1} 
              display_path2={fAd.display_path2} 
              headlines={fAd.headlines} 
              descriptions={fAd.descriptions} 
            />

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

          <!-- AI MAX UPGRADE DASHBOARD / HUD -->
          <PMaxUpgradeSection {selectedCampaign} />

          <!-- HISTORICAL POLICY AUDIT LOGS -->
          <PolicyShieldSection 
            view="history"
            {selectedAdGroup}
          />

          <!-- Section 1: Target Keywords (Full Width of Right Column) -->
          <div class="space-y-3 bg-black/40 p-5 border border-white/5 rounded-none font-mono">
            <span class="text-[11px] text-purple-400 font-black block text-left uppercase tracking-widest border-b border-purple-500/10 pb-2">🎯 TỪ KHÓA ĐỀ XUẤT</span>
            <KeywordsScoutSection 
              {competitorAnalysis}
              bind:adGroupKeywords
              bind:importedItems
              bind:selectedMatchType
              bind:viewMode
              bind:hideLowQualityKeywords
              bind:deletingKeywords
              {addAdGroupKeywords}
              {removeAdGroupKeyword}
              fullview={true}
            />
          </div>

          <!-- Section 2 & 3: Competitor Headlines, Negatives & Gaps -->
          <AdAssetsAndGapsSection 
            {competitorAnalysis}
            bind:importedItems
            bind:negativeKeywords
            {addNegativeKeyword}
            {handleImportKeyword}
            fullview={true}
          />

        </div>
      </div>

    </div>
  </div>
{/if}
