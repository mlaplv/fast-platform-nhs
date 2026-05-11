<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, scale, slide } from 'svelte/transition';
  import { createAdsState } from './ads/adsState.svelte';

  // Sub-components
  import AdsKpiGrid from './ads/AdsKpiGrid.svelte';
  import AdsOverview from './ads/AdsOverview.svelte';
  import AdsInsights from './ads/AdsInsights.svelte';
  import AdsInvestigation from './ads/AdsInvestigation.svelte';
  import AdsGoogleMetrics from './ads/AdsGoogleMetrics.svelte';
  import AdsCampaignManager from './ads/AdsCampaignManager.svelte';
  import AdsBlacklist from './ads/AdsBlacklist.svelte';
  import AdsNegativeKeywords from './ads/AdsNegativeKeywords.svelte';

  // Icons
  import X from "@lucide/svelte/icons/x";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Activity from "@lucide/svelte/icons/activity";

  const ads = createAdsState();
  let showTimeMenu = $state(false);

  onMount(() => {
    ads.fetchAll();
    ads.fetchCampaigns();
  });

  function close() { /* Logic close modal */ }
</script>

<div class="fixed inset-0 z-[9999] bg-black text-white font-sans overflow-hidden flex flex-col p-6 ads-premium-hud" in:fade>
  <!-- HIỆU ỨNG NỀN TINH GIẢN -->
  <div class="absolute inset-0 pointer-events-none opacity-10">
    <div class="absolute inset-0" style="background-image: radial-gradient(circle at 2px 2px, rgba(255,255,255,0.05) 1px, transparent 0); background-size: 30px 30px;"></div>
  </div>

  <div class="relative z-10 flex flex-col h-full w-full max-w-[1500px] mx-auto">
    <!-- HEADER TINH GỌN -->
    <header class="flex justify-between items-center border-b border-white/5 pb-4 mb-6">
      <div class="flex items-center gap-5">
        <div class="brand-box">
          <div class="text-[9px] text-cyan-400 font-black tracking-[0.4em] uppercase mb-1 opacity-70">XOHI AI // PROTECTION</div>
          <h1 class="text-2xl font-black tracking-tighter uppercase leading-none">TRUNG TÂM ĐIỀU HÀNH</h1>
        </div>
        <div class="h-8 w-[1px] bg-white/10"></div>
        <div class="flex items-center gap-3 bg-white/[0.03] px-3 py-1.5 rounded-full border border-white/5">
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span class="text-[9px] font-bold text-emerald-400/80 tracking-widest uppercase">MÁY CHỦ: TRỰC TUYẾN</span>
        </div>
      </div>

      <div class="flex items-center gap-3">
         <div class="relative">
            <button 
              class="px-4 py-2 bg-black border border-white/10 text-[10px] font-mono flex items-center gap-3 hover:border-cyan-400/50 transition-all min-w-[160px] justify-between"
              onclick={() => showTimeMenu = !showTimeMenu}
            >
               <span class="text-slate-500 uppercase tracking-tighter">Thời gian:</span>
               <span class="text-white font-black">{ads.selectedHours >= 168 ? '7 NGÀY' : ads.selectedHours + ' GIỜ'}</span>
               <ChevronDown size={12} class="text-cyan-400 {showTimeMenu ? 'rotate-180' : ''} transition-transform" />
            </button>
            
            {#if showTimeMenu}
               <div class="absolute top-full right-0 mt-1 w-full bg-black border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.8)] z-[100] overflow-hidden" in:slide={{duration: 200}}>
                  {#each [
                     { v: 2, l: '2 GIỜ QUA' },
                     { v: 6, l: '6 GIỜ QUA' },
                     { v: 12, l: '12 GIỜ QUA' },
                     { v: 24, l: '24 GIỜ QUA' },
                     { v: 168, l: '7 NGÀY QUA' }
                  ] as opt}
                     <button 
                       class="w-full text-left px-4 py-2.5 text-[9px] font-black uppercase tracking-widest hover:bg-cyan-400 hover:text-black transition-colors {ads.selectedHours === opt.v ? 'text-cyan-400 bg-white/5' : 'text-slate-500'}"
                       onclick={() => { 
                          ads.selectedHours = opt.v; 
                          ads.fetchAll(); 
                          if (ads.activeTab === 'google') ads.fetchGoogleMetrics();
                          if (ads.activeTab === 'negative_keywords') ads.fetchNegativeKeywords();
                          showTimeMenu = false;
                       }}
                     >
                        {opt.l}
                     </button>
                  {/each}
               </div>
            {/if}
         </div>
         <button class="w-10 h-10 flex items-center justify-center bg-white/5 hover:bg-ruby transition-all group" onclick={close}>
            <X size={20} class="group-hover:rotate-90 transition-transform" />
         </button>
      </div>
    </header>

    {#if ads.loading}
      <div class="flex-1 flex flex-col items-center justify-center gap-3 opacity-30">
        <Activity size={32} class="animate-spin text-cyan-400" />
        <span class="text-[9px] uppercase tracking-[0.6em] font-black">Khởi tạo luồng điều hành...</span>
      </div>
    {:else}
      <!-- KPI GRID TINH GỌN -->
      <div class="mb-6">
        <AdsKpiGrid summary={ads.summary} fmt={ads.fmt} />
      </div>

      <!-- NAVIGATION TINH GỌN -->
      <nav class="flex justify-center mb-6">
        <div class="inline-flex bg-white/[0.02] p-1 rounded-sm border border-white/5 backdrop-blur-md">
          {#each [
            { id: 'overview', label: 'TỔNG QUAN', fetch: () => ads.fetchAll() },
            { id: 'insights', label: 'CỐ VẤN AI' },
            { id: 'investigation', label: 'PHÁP Y' },
            { id: 'google', label: 'GOOGLE LIVE', fetch: () => ads.fetchGoogleMetrics() },
            { id: 'campaigns', label: 'ĐIỀU PHỐI', fetch: () => ads.fetchCampaigns() },
            { id: 'blacklist', label: 'DANH SÁCH ĐEN' },
            { id: 'negative_keywords', label: 'TỪ KHÓA PHỦ ĐỊNH', fetch: () => ads.fetchNegativeKeywords() }
          ] as tab}
            <button 
              class="px-6 py-2.5 text-[10px] font-black uppercase tracking-[0.15em] transition-all relative {ads.activeTab === tab.id ? 'text-white bg-white/5' : 'text-slate-500 hover:text-slate-300'}"
              onclick={() => { ads.activeTab = tab.id; if (tab.fetch) tab.fetch(); }}
            >
              {tab.label}
              {#if ads.activeTab === tab.id}
                <div class="absolute bottom-0 left-0 w-full h-[1.5px] bg-cyan-400 shadow-[0_0_8px_#00f3ff]" in:scale></div>
              {/if}
            </button>
          {/each}
        </div>
      </nav>

      <!-- VIEWPORT AREA -->
      <main class="flex-1 overflow-y-auto custom-scrollbar pr-1">
        <div class="h-full">
          {#if ads.activeTab === 'overview'}
            <AdsOverview summary={ads.summary} isBlacklisted={ads.isBlacklisted} blockIP={ads.blockIP} />
          {:else if ads.activeTab === 'insights'}
            <AdsInsights insights={ads.insights} selectedCampaign={ads.selectedCampaign} aiLoading={ads.aiLoading} priorityColor={ads.priorityColor} aiSuggest={ads.aiSuggest} />
          {:else if ads.activeTab === 'investigation'}
            <AdsInvestigation reportResult={ads.reportResult} reportLoading={ads.reportLoading} generateReport={ads.generateReport} fmt={ads.fmt} />
          {:else if ads.activeTab === 'google'}
            <AdsGoogleMetrics {...ads} />
          {:else if ads.activeTab === 'campaigns'}
            <AdsCampaignManager {...ads} />
          {:else if ads.activeTab === 'blacklist'}
            <AdsBlacklist {...ads} />
          {:else if ads.activeTab === 'negative_keywords'}
            <AdsNegativeKeywords 
              negativeKeywords={ads.negativeKeywords} 
              selectedCampaign={ads.selectedCampaign}
              bind:isGlobalNegative={ads.isGlobalNegative}
              bind:newNegativeKeyword={ads.newNegativeKeyword}
              aiSuggest={ads.aiSuggest}
              addNegativeKeyword={ads.addNegativeKeyword}
              removeNegativeKeyword={ads.removeNegativeKeyword}
            />
          {/if}
        </div>
      </main>
    {/if}
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 3px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 10px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0,243,255,0.2); }
  
  :global(.ads-premium-hud *) {
    letter-spacing: 0.02em;
  }
</style>
