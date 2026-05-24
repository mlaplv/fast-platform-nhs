<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, scale, slide } from 'svelte/transition';
  import { createAdsState } from './ads/adsState.svelte';
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';

  const nanobot = useNanobot();
  import AdsKpiGrid from './ads/AdsKpiGrid.svelte';
  import AdsOverview from './ads/AdsOverview.svelte';
  import AdsInsights from './ads/AdsInsights.svelte';
  import AdsInvestigation from './ads/AdsInvestigation.svelte';
  import AdsGoogleMetrics from './ads/AdsGoogleMetrics.svelte';
  import AdsCampaignManager from './ads/AdsCampaignManager.svelte';
  import AdsBlacklist from './ads/AdsBlacklist.svelte';
  import AdsNegativeKeywords from './ads/AdsNegativeKeywords.svelte';
  import AdsDatePicker from './ads/AdsDatePicker.svelte';
  import AdsPowHud from "./ads/AdsPowHud.svelte";
  import GoogleMerchantWidget from "./widgets/GoogleMerchantWidget.svelte";

  // Icons
  import X from "@lucide/svelte/icons/x";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Activity from "@lucide/svelte/icons/activity";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Zap from "@lucide/svelte/icons/zap";
  import Brain from "@lucide/svelte/icons/brain";
  import AlertTriangle from "@lucide/svelte/icons/alert-triangle";

  const ads = createAdsState();
  let showTimeMenu = $state(false);
  let showIntelDropdown = $state(false);

  onMount(() => {
    ads.fetchAll();
    ads.fetchCampaigns();
    ads.initSSE();
    ads.initEdge();
  });

  onDestroy(() => {
     ads.dispose();
  });

  function close() {
    nanobot.closeUniversalModal();
  }

  function fmtDateShort(dStr: string | null) {
     if (!dStr) return '';
     const parts = dStr.split('-');
     if (parts.length !== 3) return dStr;
     return `${parts[2]}/${parts[1]}`;
  }
</script>

<div class="relative w-full h-full text-white font-sans overflow-hidden flex flex-col ads-premium-hud bg-[#050505]">
  <!-- HUD BACKGROUND EFFECTS (Elite V2.6 Standard) -->
  <div class="fixed inset-0 pointer-events-none overflow-hidden z-0">
    <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-cyan-500/10 blur-[150px] rounded-none animate-pulse"></div>
    <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-rose-500/10 blur-[150px] rounded-none animate-pulse" style="animation-delay: 2s"></div>
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_center,rgba(0,243,255,0.03)_0%,transparent_70%)]"></div>
    
    <!-- SCANLINE EFFECT -->
    <div class="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%),linear-gradient(90deg,rgba(255,0,0,0.03),rgba(0,255,0,0.01),rgba(0,0,255,0.03))] z-[60] pointer-events-none bg-[length:100%_4px,3px_100%] opacity-20"></div>
  </div>

  <div class="scanlines"></div>
  <div class="relative z-10 flex flex-col h-full w-full p-5">
    <!-- HEADER (Elite V3.0 Simple Pro) -->
    <header class="flex justify-between items-center border-b border-white/5 pb-5 mb-8 shrink-0 relative" style="z-index: {Z_INDEX_ADMIN.STICKY_HEADER}">
      <div class="flex items-center gap-8">
        <!-- Brand Core -->
        <div class="flex items-center gap-4">
          <div class="relative group">
            <div class="absolute inset-0 bg-cyan-400 blur-xl opacity-10 group-hover:opacity-30 transition-all duration-1000"></div>
            <ShieldCheck size={32} class="text-cyan-400 relative z-10 filter drop-shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
          </div>
          <div>
            <div class="flex items-center gap-2 mb-0.5">
              <span class="text-[9px] text-cyan-400/60 font-black tracking-[0.3em]">Xohi AI Protection</span>
              <span class="text-[7px] px-1.5 py-0.5 bg-cyan-400/10 text-cyan-400/80 border border-cyan-400/20 font-mono">V3.0_λ</span>
            </div>
            <h1 class="text-2xl font-black tracking-tighter text-white leading-none">Gian lận Quảng cáo</h1>
          </div>
        </div>

        <div class="h-8 w-[1px] bg-white/5"></div>

        <!-- Security Pulse Status -->
        <div class="flex items-center gap-4">
          {#if (ads.summary?.totals?.fraud_rate_pct || 0) > 30}
            <div class="flex items-center gap-3 bg-rose-500/5 px-4 py-1.5 border border-rose-500/20 group cursor-default">
              <div class="w-2 h-2 rounded-full bg-rose-500 animate-ping"></div>
              <span class="text-[10px] font-black text-rose-500 tracking-widest">Threat Level: High ({ads.summary.totals.fraud_rate_pct}%)</span>
            </div>
          {:else}
            <div class="flex items-center gap-3 bg-emerald-500/5 px-4 py-1.5 border border-emerald-500/20">
              <div class="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_#10b981]"></div>
              <span class="text-[10px] font-black text-emerald-400 tracking-widest">Shield Active</span>
            </div>
          {/if}

          {#if ads.edgeStatus === 'ready'}
            <div class="flex items-center gap-2 text-yellow-500/40 font-mono text-[9px] tracking-tighter">
              <Zap size={12} class="animate-pulse" />
              <span>Edge_Core_Online</span>
            </div>
          {/if}
        </div>
      </div>

      <div class="flex items-center gap-4">
        <!-- Tactical Intelligence -->
        {#if ads.summary?.insights?.length > 0}
          <div class="relative">
            <button 
              class="flex items-center gap-3 bg-amber-500/5 px-4 py-2 border border-amber-500/10 hover:bg-amber-500/10 transition-all group"
              onclick={() => showIntelDropdown = !showIntelDropdown}
            >
              <Brain size={16} class="text-amber-500 group-hover:scale-110 transition-transform" />
              <div class="flex flex-col items-start leading-tight">
                <span class="text-[10px] font-black text-white tracking-tighter">{ads.summary.insights.length} Mission Intel</span>
                <span class="text-[7px] text-amber-500/60 font-bold">Tactical Priority</span>
              </div>
              <ChevronDown size={14} class="text-white/20 group-hover:text-white transition-colors {showIntelDropdown ? 'rotate-180' : ''}" />
            </button>

            {#if showIntelDropdown}
              <div 
                class="absolute top-full right-0 mt-2 w-80 bg-[#080808]/95 backdrop-blur-2xl border border-white/10 shadow-2xl z-[200] p-4 flex flex-col gap-2"
                in:slide
              >
                <div class="flex items-center justify-between mb-2 border-b border-white/5 pb-2">
                   <span class="text-[9px] font-black text-amber-500 tracking-widest">Live Intelligence Feed</span>
                   <button class="text-white/20 hover:text-white" onclick={() => showIntelDropdown = false}><X size={14} /></button>
                </div>
                <div class="max-h-64 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-2">
                  {#each ads.summary.insights as ins}
                    <div class="bg-white/[0.02] border border-white/5 p-3 hover:border-amber-500/30 transition-all cursor-pointer" 
                         onclick={() => { ads.activeTab = 'insights'; showIntelDropdown = false; }}>
                        <h4 class="text-[10px] font-black text-white mb-1 ">{ins.title}</h4>
                        <p class="text-[9px] text-amber-500/70 italic">"{ins.action}"</p>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {/if}

        <div class="h-8 w-[1px] bg-white/5 mx-2"></div>

        <!-- Global Controls -->
        <div class="flex items-center gap-3">
          <div class="relative">
            <button 
              class="px-4 py-2 bg-white/5 border border-white/10 text-[10px] font-mono flex items-center gap-4 hover:border-cyan-400/50 transition-all min-w-[160px] justify-between group"
              onclick={() => showTimeMenu = !showTimeMenu}
            >
               <span class="text-slate-500 tracking-tighter group-hover:text-cyan-400/70 transition-colors">Thời gian:</span>
               <span class="text-white font-black">
                   {#if ads.selectedHours === 'all_time'}
                      Toàn thời gian
                   {:else if ads.dateFrom && ads.dateTo}
                      {fmtDateShort(ads.dateFrom)} → {fmtDateShort(ads.dateTo)}
                   {:else}
                      {ads.selectedHours >= 168 ? '7 ngày' : ads.selectedHours + ' giờ'}
                   {/if}
                </span>
                <ChevronDown size={14} class="text-cyan-400 {showTimeMenu ? 'rotate-180' : ''} transition-transform" />
            </button>
            
            {#if showTimeMenu}
               <div class="absolute top-full right-0 mt-2 w-[480px] bg-[#0a0a0a]/98 border border-white/10 shadow-[0_30px_100px_rgba(0,0,0,0.9)] flex h-[380px] backdrop-blur-3xl z-[200]"
                    in:slide={{duration: 250}}>
                  
                  <!-- LEFT: PRESETS -->
                  <div class="w-1/2 border-r border-white/10 p-2 flex flex-col custom-scrollbar overflow-y-auto">
                     <span class="text-[8px] text-slate-500 font-black tracking-[0.2em] p-3 mb-1">Mốc thời gian</span>
                     {#each [
                        { id: 'today', l: 'Hôm nay' },
                        { id: 'yesterday', l: 'Hôm qua' },
                        { id: 'last_7', l: '7 ngày qua' },
                        { id: 'last_14', l: '14 ngày qua' },
                        { id: 'last_30', l: '30 ngày qua' },
                        { id: 'this_month', l: 'Tháng này' },
                        { id: 'last_month', l: 'Tháng trước' },
                        { id: 'all_time', l: 'Toàn thời gian' }
                     ] as opt}
                        <button 
                          class="w-full text-left px-4 py-2.5 text-[10px] font-bold transition-all rounded-none flex items-center justify-between group/opt {ads.selectedHours === opt.id ? 'bg-cyan-500 text-black shadow-[0_0_20px_rgba(6,182,212,0.3)]' : 'text-slate-400 hover:bg-white/5 hover:text-white'}"
                          onclick={(e) => { 
                             e.stopPropagation();
                             const now = new Date();
                             const fmt = (d: Date) => d.toISOString().split('T')[0];
                             
                             if (opt.id === 'today') {
                                ads.dateFrom = fmt(now);
                                ads.dateTo = fmt(now);
                             } else if (opt.id === 'yesterday') {
                                const d = new Date(); d.setDate(d.getDate() - 1);
                                ads.dateFrom = fmt(d);
                                ads.dateTo = fmt(d);
                             } else if (opt.id === 'last_7') {
                                const d = new Date(); d.setDate(d.getDate() - 7);
                                ads.dateFrom = fmt(d);
                                ads.dateTo = fmt(now);
                             } else if (opt.id === 'last_30') {
                                const d = new Date(); d.setDate(d.getDate() - 30);
                                ads.dateFrom = fmt(d);
                                ads.dateTo = fmt(now);
                             } else if (opt.id === 'this_month') {
                                const d = new Date(now.getFullYear(), now.getMonth(), 1);
                                ads.dateFrom = fmt(d);
                                ads.dateTo = fmt(now);
                             } else if (opt.id === 'last_month') {
                                const d1 = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                                const d2 = new Date(now.getFullYear(), now.getMonth(), 0);
                                ads.dateFrom = fmt(d1);
                                ads.dateTo = fmt(d2);
                                ads.selectedHours = 720;
                             } else if (opt.id === 'all_time') {
                                 const startD = new Date(); startD.setFullYear(startD.getFullYear() - 10);
                                 ads.dateFrom = fmt(startD);
                                 ads.dateTo = fmt(now);
                                 ads.selectedHours = 87600; 
                             } else {
                                ads.selectedHours = 168;
                                ads.dateFrom = null;
                                ads.dateTo = null;
                             }
                             
                             ads.fetchAll(); 
                             showTimeMenu = false;
                          }}
                        >
                           <span>{opt.l}</span>
                           {#if ads.selectedHours === opt.id}
                              <div class="w-1.5 h-1.5 rounded-none bg-black animate-pulse"></div>
                           {/if}
                        </button>
                     {/each}
                  </div>
                  
                  <!-- RIGHT: CUSTOM RANGE -->
                  <div class="w-1/2 p-6 flex flex-col bg-white/[0.01]" onclick={(e) => e.stopPropagation()}>
                     <span class="text-[8px] text-slate-500 font-black tracking-[0.2em] mb-6">Khoảng ngày tùy chỉnh</span>
                     <div class="flex flex-col gap-4">
                        <AdsDatePicker bind:value={ads.dateFrom} label="Ngày bắt đầu" align="right" />
                        <AdsDatePicker bind:value={ads.dateTo} label="Ngày kết thúc" align="right" />
                        <button 
                           class="mt-4 w-full py-3 bg-cyan-600 text-white text-[10px] font-black tracking-widest hover:bg-cyan-500 transition-all"
                           onclick={() => { ads.fetchAll(); showTimeMenu = false; }}
                        >
                           Áp dụng
                        </button>
                     </div>
                  </div>
               </div>
            {/if}
          </div>
          
          <button 
            onclick={close}
            class="w-10 h-10 flex items-center justify-center bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all group"
          >
            <X size={20} class="text-white/40 group-hover:text-white group-hover:rotate-90 transition-all duration-500" />
          </button>
        </div>
      </div>
    </header>
    {#if ads.loading && !ads.summary}
      <div class="flex-1 flex flex-col items-center justify-center gap-4 opacity-50">
        <div class="relative">
          <Activity size={48} class="animate-spin text-cyan-400" />
          <div class="absolute inset-0 blur-lg bg-cyan-400/20 animate-pulse rounded-none"></div>
        </div>
        <span class="text-[10px] tracking-[0.4em] font-black animate-pulse text-cyan-400 ">Đang truy xuất dữ liệu bảo vệ...</span>
      </div>
    {:else}
      <div class="relative flex-1 flex flex-col min-h-0 {ads.loading ? 'pointer-events-none' : ''}">
        {#if ads.loading}
           <div class="absolute inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-[1px] rounded-none" in:fade>
              <div class="px-6 py-3 bg-[#0a0a0a] border border-white/10 rounded-none flex items-center gap-4 shadow-2xl">
                 <RefreshCw size={14} class="animate-spin text-cyan-400" />
                 <span class="text-[9px] font-black text-white tracking-widest ">Đang cập nhật...</span>
              </div>
           </div>
        {/if}
      <!-- KPI GRID -->
      <div class="mb-8" in:fade={{delay: 100}}>
        <AdsKpiGrid summary={ads.summary} fmt={ads.fmt} />
      </div>

      <!-- NAVIGATION (Elite V2.6 Standard) -->
      <nav class="flex justify-center mb-10" in:fade={{delay: 200}}>
        <div class="inline-flex bg-white/[0.03] p-2 rounded-none border border-white/10 backdrop-blur-2xl shadow-[0_10px_40px_rgba(0,0,0,0.4)] relative overflow-hidden group/nav">
          <div class="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-transparent to-rose-500/5 opacity-50"></div>
          {#each [
            { id: 'overview', label: 'Tổng quan', fetch: () => ads.fetchAll() },
            { id: 'insights', label: 'Cố vấn AI' },
            { id: 'investigation', label: 'Pháp y' },
            { id: 'google', label: 'Google Live', fetch: () => ads.fetchGoogleMetrics() },
            { id: 'campaigns', label: 'Điều phối', fetch: () => ads.fetchCampaigns() },
            { id: 'merchant', label: 'Google Merchant' },
            { id: 'blacklist', label: 'Danh sách đen' },
            { id: 'negative_keywords', label: 'Từ khóa phủ định', fetch: () => ads.fetchNegativeKeywords() }
          ] as tab}
            <button 
              class="px-7 py-3.5 text-[10px] font-black tracking-[0.15em] transition-all relative rounded-none {ads.activeTab === tab.id ? 'text-white bg-white/10 shadow-[0_0_20px_rgba(255,255,255,0.05)] border border-white/5' : 'text-slate-500 hover:text-slate-200 hover:bg-white/5'}"
              onclick={() => { ads.activeTab = tab.id; if (tab.fetch) tab.fetch(); }}
            >
              {tab.label}
              {#if ads.activeTab === tab.id}
                <div class="absolute bottom-1.5 left-1/2 -translate-x-1/2 w-6 h-[2px] bg-cyan-400 shadow-[0_0_15px_#00f3ff] rounded-none" in:scale></div>
              {/if}
            </button>
          {/each}
        </div>
      </nav>

      <!-- VIEWPORT AREA -->
      <main class="flex-1 overflow-y-auto custom-scrollbar pr-2" in:fade={{delay: 300}}>
        <div class="min-h-0">
          {#if ads.activeTab === 'overview'}
            <AdsOverview summary={ads.summary} isBlacklisted={ads.isBlacklisted} blockIP={ads.blockIP} periodLabel={ads.periodLabel} />
          {:else if ads.activeTab === 'insights'}
            <AdsInsights 
              insights={ads.insights} 
              campaigns={ads.campaigns}
              googleMetrics={ads.googleMetrics}
              bind:selectedCampaign={ads.selectedCampaign} 
              aiLoading={ads.aiLoading} 
              priorityColor={ads.priorityColor} 
              aiSuggest={ads.aiSuggest} 
              aiResult={ads.aiResult} 
            />
          {:else if ads.activeTab === 'investigation'}
            <AdsInvestigation 
               reportResult={ads.reportResult} 
               reportLoading={ads.reportLoading} 
               generateReport={ads.generateReport} 
               pastReports={ads.pastReports}
               fetchPastReports={ads.fetchPastReports}
               viewPastReport={ads.viewPastReport}
               fmt={ads.fmt} 
            />
          {:else if ads.activeTab === 'google'}
            <AdsGoogleMetrics {...ads} />
          {:else if ads.activeTab === 'campaigns'}
            <AdsCampaignManager {...ads} />
          {:else if ads.activeTab === 'merchant'}
            <div class="max-w-5xl mx-auto py-2">
              <GoogleMerchantWidget />
            </div>
          {:else if ads.activeTab === 'blacklist'}
            <AdsBlacklist {...ads} />
          {:else if ads.activeTab === 'negative_keywords'}
            <AdsNegativeKeywords 
              negativeKeywords={ads.negativeKeywords} 
              campaigns={ads.campaigns}
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
    {#if ads.activeTab === 'overview'}
    <!-- [Elite V3.0] System Status & Changelog Footer -->
    <footer class="mt-12 pt-8 border-t border-white/5 flex flex-col gap-6 opacity-40 hover:opacity-100 transition-opacity duration-700">
      <div class="flex justify-between items-start">
        <div class="flex flex-col gap-2">
          <div class="flex items-center gap-3">
             <span class="text-[9px] font-black text-cyan-400 tracking-[0.3em]">System_Infrastructure_V3.0_λ</span>
             <div class="h-px w-12 bg-cyan-400/20"></div>
          </div>
          <p class="text-[10px] text-slate-400 max-w-2xl leading-relaxed">
            Hệ thống bảo vệ đa tầng tích hợp Edge Intelligence (Fast Path) và Agentic C.O.R.E (Slow Path). 
            Tự động phản ứng với Botnet 2026 thông qua thử thách mật mã PoW và phân tích đặc vụ AI.
          </p>
        </div>
        <div class="text-right">
          <span class="text-[9px] font-mono text-slate-600 ">Last_Deployment: 2026-05-12_18:40</span>
        </div>
      </div>

      <div class="grid grid-cols-4 gap-8">
        <div class="flex flex-col gap-1.5">
          <span class="text-[8px] font-black text-white tracking-widest border-l-2 border-cyan-500 pl-2">Sprint 1: Edge Core</span>
          <ul class="text-[9px] text-slate-500 flex flex-col gap-1 list-none pl-2">
            <li>• ONNX Runtime Wasm Behavior Scoring</li>
            <li>• Cryptographic PoW (SHA-256) Integration</li>
            <li>• Zero-latency client-side heuristics</li>
          </ul>
        </div>
        <div class="flex flex-col gap-1.5">
          <span class="text-[8px] font-black text-white tracking-widest border-l-2 border-amber-500 pl-2">Sprint 2: Agentic C.O.R.E</span>
          <ul class="text-[9px] text-slate-500 flex flex-col gap-1 list-none pl-2">
            <li>• PydanticAI Forensic Investigation Agent</li>
            <li>• Redis Streams Event-driven Architecture</li>
            <li>• RAG Integration (Obsidian & GraphDB)</li>
          </ul>
        </div>
        <div class="flex flex-col gap-1.5">
          <span class="text-[8px] font-black text-white tracking-widest border-l-2 border-emerald-500 pl-2">Sprint 3: Elite HUD</span>
          <ul class="text-[9px] text-slate-500 flex flex-col gap-1 list-none pl-2">
            <li>• AdsPowHud Real-time Mitigation Display</li>
            <li>• Simple Pro Header Optimization</li>
            <li>• Multi-layered Forensic Archive UI</li>
          </ul>
        </div>
        <div class="flex flex-col gap-1.5">
          <span class="text-[8px] font-black text-white tracking-widest border-l-2 border-rose-500 pl-2">Hygiene & Safety</span>
          <ul class="text-[9px] text-slate-500 flex flex-col gap-1 list-none pl-2">
            <li>• LiteLLM Cost & Model Management</li>
            <li>• SSR Stealth Asset Injection (CORS Fix)</li>
            <li>• Real-time SSE Sync (Zero-noise Logging)</li>
          </ul>
        </div>
      </div>
      </footer>
    {/if}
    </div>
    {/if}
  </div>
</div>

<!-- [Elite V3.0] PoW Shield HUD -->
<AdsPowHud adsState={ads} />

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 3px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 0; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0,243,255,0.2); }
  
  :global(.ads-premium-hud *) {
    letter-spacing: 0.02em;
  }

  .scanlines {
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: linear-gradient(
      rgba(18, 16, 16, 0) 50%,
      rgba(0, 0, 0, 0.1) 50%
    ), linear-gradient(
      90deg,
      rgba(255, 0, 0, 0.01),
      rgba(0, 255, 0, 0.005),
      rgba(0, 0, 255, 0.01)
    );
    background-size: 100% 4px, 3px 100%;
    pointer-events: none;
    z-index: 100;
    opacity: 0.3;
  }
</style>
