<script lang="ts">
  import { fade, scale, slide } from 'svelte/transition';
  import Globe from "@lucide/svelte/icons/globe";
  import Target from "@lucide/svelte/icons/target";
  import Brain from "@lucide/svelte/icons/brain";
  import Activity from "@lucide/svelte/icons/activity";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Copy from "@lucide/svelte/icons/copy";
  import Terminal from "@lucide/svelte/icons/terminal";
  import Zap from "@lucide/svelte/icons/zap";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import BarChart3 from "@lucide/svelte/icons/bar-chart-3";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import X from "@lucide/svelte/icons/x";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Database from "@lucide/svelte/icons/database";
  import Radio from "@lucide/svelte/icons/radio";
  import { untrack } from 'svelte';

  let { 
    insights = [],
    campaigns = [],
    googleMetrics = [],
    selectedCampaign = $bindable(null),
    aiLoading = false,
    priorityColor,
    aiSuggest,
    aiResult = null,
    fmt = (n: number) => n.toLocaleString()
  } = $props();

  let dropdownOpen = $state(false);

  // Live Calculations
  const campaignMetrics = $derived(googleMetrics.filter(m => {
    if (!selectedCampaign) return false;
    const cid = selectedCampaign.resource_name.split('/').pop();
    return m.campaign_id === cid || m.campaign_name === selectedCampaign.name;
  }));

  const totalInvalid = $derived(campaignMetrics.reduce((s, m) => s + (Number(m.invalid_clicks) || 0), 0));
  const totalClicks = $derived(campaignMetrics.reduce((s, m) => s + (Number(m.clicks) || 0), 0));
  const invalidRate = $derived(totalClicks > 0 ? (totalInvalid / totalClicks * 100) : 0);
  
  // Real Chart Data + Ghost Path for "Live" feel
  const chartData = $derived(campaignMetrics.length > 0 
    ? campaignMetrics.slice(-12).map((m, i) => ({
        x: i * 32,
        y: 100 - (Math.min(100, (Number(m.invalid_clicks) / (Number(m.clicks) || 1)) * 400)),
        val: m.invalid_clicks
      }))
    : Array.from({length: 12}, (_, i) => ({ x: i * 32, y: 50 + Math.sin(i * 0.8) * 20 }))
  );

  function copyText(text: string) {
    navigator.clipboard.writeText(text);
  }

  // Terminal Log Simulator
  let logs = $state([
    { t: Date.now(), msg: '>> NEURAL_CORE_INITIALIZED', type: 'system' },
    { t: Date.now() - 1000, msg: '>> AWAITING_TACTICAL_ENCRYPTION...', type: 'system' }
  ]);

  let lastAiLoading = $state(false);
  let lastAiResult = $state(null);

  $effect(() => {
    // Only log on state transitions to avoid loops and duplicate entries
    if (aiLoading && !lastAiLoading) {
       const newLog = { t: Date.now(), msg: '>> SCANNING_CAMPAIGN_VECTORS...', type: 'process' };
       logs = [newLog, ...untrack(() => logs)];
       lastAiLoading = true;
    } else if (!aiLoading) {
       lastAiLoading = false;
    }

    if (aiResult && aiResult !== lastAiResult) {
       const newLog = { t: Date.now(), msg: '>> DECODING_COMPLETE: STRATEGY_READY', type: 'success' };
       logs = [newLog, ...untrack(() => logs)];
       lastAiResult = aiResult;
    }
  });
</script>

<div class="flex flex-col gap-6 h-full relative" in:fade>
   <!-- DECORATIVE BACKGROUND GRID -->
   <div class="absolute inset-0 pointer-events-none opacity-[0.03] bg-[linear-gradient(rgba(34,211,238,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(34,211,238,0.1)_1px,transparent_1px)] bg-[length:40px_40px]"></div>

   <!-- TOP HUD BAR -->
   <header class="flex items-center justify-between bg-[#0a0a0a]/80 border border-white/5 p-5 backdrop-blur-3xl relative z-50 shadow-2xl">
      <div class="flex items-center gap-8">
         <div class="flex items-center gap-4 border-r border-white/10 pr-8">
            <div class="relative">
               <div class="w-10 h-10 rounded-none bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                  <Brain size={22} class="text-cyan-400 animate-pulse" />
               </div>
               <div class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-cyan-500 rounded-none border border-black animate-ping"></div>
            </div>
            <div>
               <h2 class="text-[11px] font-black tracking-[0.4em] text-white font-mono leading-none mb-1.5">Xohi_Strategist_OS</h2>
               <div class="flex items-center gap-2">
                  <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                  <span class="text-[8px] text-emerald-500 font-mono font-black tracking-widest">Neural Link Active</span>
               </div>
            </div>
         </div>

         <div class="flex items-center gap-6 text-[9px] font-mono text-slate-500 tracking-widest">
            <div class="flex items-center gap-2">
               <Database size={12} />
               <span>Patterns: <b class="text-white">{insights.length}</b></span>
            </div>
            <div class="flex items-center gap-2">
               <Radio size={12} class="animate-pulse" />
               <span>Live_Sync: <b class="text-cyan-400">Stable</b></span>
            </div>
         </div>
      </div>

      <div class="flex items-center gap-4">
         {#if selectedCampaign}
            <div class="flex items-center gap-4 bg-rose-500/10 px-5 py-2.5 border border-rose-500/20 group/tag transition-all hover:bg-rose-500/20">
               <Target size={14} class="text-rose-500 group-hover/tag:scale-110 transition-transform" />
               <span class="text-[9px] font-black text-white tracking-widest font-mono">Target: {selectedCampaign.name}</span>
               <button class="ml-2 text-slate-500 hover:text-white" onclick={() => selectedCampaign = null}><X size={14} /></button>
            </div>
         {:else}
            <div class="relative">
               <button 
                  class="bg-cyan-500/5 border border-cyan-500/20 px-6 py-2.5 text-[9px] font-black text-cyan-400 font-mono tracking-[0.2em] flex items-center gap-4 hover:bg-cyan-500/10 transition-all"
                  onclick={() => dropdownOpen = !dropdownOpen}
               >
                  <span>Select_Mission_Target</span>
                  <ChevronDown size={14} class="transition-transform {dropdownOpen ? 'rotate-180' : ''}" />
               </button>
               {#if dropdownOpen}
                  <div class="absolute top-full right-0 mt-2 w-64 bg-[#0f0f0f] border border-cyan-500/30 shadow-[0_30px_60px_rgba(0,0,0,0.9)] z-[100] overflow-hidden" in:slide>
                     {#each campaigns as c}
                        <button class="w-full text-left p-4 text-[9px] font-black text-slate-400 font-mono hover:bg-cyan-500/10 hover:text-cyan-400 border-b border-white/5 " onclick={() => { selectedCampaign = c; dropdownOpen = false; }}>{c.name}</button>
                     {/each}
                  </div>
               {/if}
            </div>
         {/if}
      </div>
   </header>

   <!-- MAIN GRID -->
   <div class="flex flex-col flex-1 min-h-0 relative z-10 w-full">
      <!-- MISSION COMMAND (Main) -->
      <main class="flex-1 flex flex-col gap-6 w-full">
         
         {#if selectedCampaign}
            <div class="flex-1 flex flex-col gap-6 min-h-0 w-full">
               <!-- MISSION COMMAND: STRATEGIC MATRIX -->
               <div class="flex-1 flex flex-col gap-6 overflow-hidden w-full">
                  <!-- NEURAL AUDIT HUD -->
                  <div class="bg-white/[0.02] border border-white/5 p-8 relative overflow-hidden group shadow-2xl shrink-0">
                     <div class="absolute top-0 left-0 w-1.5 h-full bg-cyan-500 shadow-[0_0_20px_#06b6d4]"></div>
                     <div class="absolute -right-16 -bottom-16 w-64 h-64 bg-cyan-500/5 rounded-full blur-[100px] pointer-events-none"></div>

                     <div class="flex items-center justify-between mb-10 relative z-10">
                        <div>
                           <div class="flex items-center gap-3 mb-2">
                              <ShieldCheck size={20} class="text-cyan-400" />
                              <h3 class="text-[14px] font-black text-white tracking-[0.4em]">Elite_Compliance_Audit</h3>
                           </div>
                           <p class="text-[10px] text-slate-500 font-mono tracking-[0.2em] leading-relaxed">
                              Phân tích đa tầng: <span class="text-cyan-400/70">SEO</span> • <span class="text-amber-400/70">SGE_Compatibility</span> • <span class="text-rose-400/70">Ads_Quality_Score</span>
                           </p>
                        </div>
                        <button 
                           class="px-8 py-3.5 bg-cyan-600 text-white text-[11px] font-black tracking-[0.3em] hover:bg-cyan-500 transition-all shadow-[0_15px_40px_rgba(6,182,212,0.3)] disabled:opacity-30 flex items-center gap-4 relative overflow-hidden group/auditbtn"
                           disabled={aiLoading || !selectedCampaign}
                           onclick={() => aiSuggest('AUDIT_LANDING_PAGE', `Analyze Landing Page for Campaign: ${selectedCampaign.name}. URL: ${selectedCampaign.landing_page_url || (typeof window !== 'undefined' ? window.location.origin : '')}`)}
                        >
                           <div class="absolute inset-0 bg-white/20 -translate-x-full group-hover/auditbtn:translate-x-full transition-transform duration-500 skew-x-12"></div>
                           {#if aiLoading}
                              <RefreshCw size={16} class="animate-spin" />
                              RECON_IN_PROGRESS...
                           {:else}
                              <Radio size={16} />
                              START_NEURAL_AUDIT
                           {/if}
                        </button>
                     </div>

                     <div class="grid grid-cols-3 gap-8 relative z-10">
                        <!-- SEO SCORE -->
                        <div class="border border-white/10 p-6 bg-black/40 flex flex-col items-center justify-center gap-4 hover:border-emerald-500/50 transition-colors group/score">
                           <span class="text-[9px] text-slate-500 font-black tracking-widest ">SEO_INDEX</span>
                           <div class="relative scale-110">
                              <svg class="w-20 h-20 -rotate-90">
                                 <circle cx="40" cy="40" r="36" fill="none" stroke="currentColor" stroke-width="3" class="text-white/5" />
                                 <circle 
                                    cx="40" cy="40" r="36" fill="none" stroke="currentColor" stroke-width="3" 
                                    class="{aiLoading ? 'text-emerald-500/30 animate-pulse' : 'text-emerald-500'} transition-all duration-1000" 
                                    stroke-dasharray="226" 
                                    stroke-dashoffset={aiLoading ? 113 : (226 - (226 * (aiResult?.seo_score || 0) / 100))} 
                                 />
                              </svg>
                              <div class="absolute inset-0 flex items-center justify-center text-2xl font-black text-white">
                                 {#if aiLoading}
                                    <div class="w-4 h-4 border-2 border-emerald-500 border-t-transparent animate-spin"></div>
                                 {:else}
                                    {aiResult?.seo_score ?? '--'}
                                 {/if}
                              </div>
                           </div>
                           <span class="text-[8px] {(aiResult?.seo_score > 80) ? 'text-emerald-500' : 'text-slate-600'} font-mono tracking-widest">
                              {aiLoading ? 'Analyzing...' : (aiResult?.seo_score ? (aiResult.seo_score > 80 ? 'Optimal' : 'Needs_Optimization') : 'Awaiting_Scan')}
                           </span>
                        </div>
 
                        <!-- SGE SCORE -->
                        <div class="border border-white/10 p-6 bg-black/40 flex flex-col items-center justify-center gap-4 hover:border-amber-500/50 transition-colors group/score">
                           <span class="text-[9px] text-slate-500 font-black tracking-widest ">SGE_RELEVANCE</span>
                           <div class="relative scale-110">
                              <svg class="w-20 h-20 -rotate-90">
                                 <circle cx="40" cy="40" r="36" fill="none" stroke="currentColor" stroke-width="3" class="text-white/5" />
                                 <circle 
                                    cx="40" cy="40" r="36" fill="none" stroke="currentColor" stroke-width="3" 
                                    class="{aiLoading ? 'text-amber-500/30 animate-pulse' : 'text-amber-500'} transition-all duration-1000" 
                                    stroke-dasharray="226" 
                                    stroke-dashoffset={aiLoading ? 113 : (226 - (226 * (aiResult?.sge_score || 0) / 100))} 
                                 />
                              </svg>
                              <div class="absolute inset-0 flex items-center justify-center text-2xl font-black text-white">
                                 {#if aiLoading}
                                    <div class="w-4 h-4 border-2 border-amber-500 border-t-transparent animate-spin"></div>
                                 {:else}
                                    {aiResult?.sge_score ?? '--'}
                                 {/if}
                              </div>
                           </div>
                           <span class="text-[8px] {(aiResult?.sge_score > 70) ? 'text-amber-400' : 'text-slate-600'} font-mono tracking-widest">
                              {aiLoading ? 'Synching...' : (aiResult?.sge_score ? (aiResult.sge_score > 70 ? 'Generative_Ready' : 'Incompatible') : 'Awaiting_Scan')}
                           </span>
                        </div>
 
                        <!-- QUALITY SCORE -->
                        <div class="border border-white/10 p-6 bg-black/40 flex flex-col items-center justify-center gap-4 hover:border-rose-500/50 transition-colors group/score">
                           <span class="text-[9px] text-slate-500 font-black tracking-widest ">ADS_QUALITY</span>
                           <div class="relative scale-110">
                              <svg class="w-20 h-20 -rotate-90">
                                 <circle cx="40" cy="40" r="36" fill="none" stroke="currentColor" stroke-width="3" class="text-white/5" />
                                 <circle 
                                    cx="40" cy="40" r="36" fill="none" stroke="currentColor" stroke-width="3" 
                                    class="{aiLoading ? 'text-rose-500/30 animate-pulse' : 'text-rose-500'} transition-all duration-1000" 
                                    stroke-dasharray="226" 
                                    stroke-dashoffset={aiLoading ? 113 : (226 - (226 * (aiResult?.quality_score || 0) * 22.6))} 
                                 />
                              </svg>
                              <div class="absolute inset-0 flex items-center justify-center text-2xl font-black text-white">
                                 {#if aiLoading}
                                    <div class="w-4 h-4 border-2 border-rose-500 border-t-transparent animate-spin"></div>
                                 {:else}
                                    {aiResult?.quality_score ?? '--'}
                                 {/if}
                              </div>
                           </div>
                           <span class="text-[8px] {(aiResult?.quality_score > 7) ? 'text-rose-400' : 'text-slate-600'} font-mono tracking-widest">
                              {aiLoading ? 'Auditing...' : (aiResult?.quality_score ? (aiResult.quality_score > 7 ? 'Elite_Score' : 'At_Risk') : 'Awaiting_Scan')}
                           </span>
                        </div>
                     </div>
                  </div>

                  <!-- TERMINAL INTEGRATION -->
                  <div class="flex-1 bg-black border border-white/10 p-6 flex flex-col relative overflow-hidden min-h-0">
                     <div class="flex items-center justify-between mb-6 border-b border-white/5 pb-4">
                        <div class="flex items-center gap-3">
                           <Terminal size={14} class="text-rose-500" />
                           <span class="text-[9px] font-black text-rose-500 tracking-widest font-mono">Neural_Analysis_Stream</span>
                        </div>
                        <div class="flex gap-1">
                           <div class="w-1 h-1 bg-rose-500 animate-pulse"></div>
                           <div class="w-1 h-1 bg-rose-500/50"></div>
                        </div>
                     </div>
                     
                     <div class="flex-1 overflow-y-auto custom-scrollbar font-mono text-[11px] space-y-6">
                        {#if aiResult}
                           <div in:fade>
                              <div class="text-rose-400 font-black mb-4">>> MISSION_DECODE_SUCCESS</div>
                              <div class="text-slate-300 leading-relaxed pl-4 border-l border-rose-500/30 whitespace-pre-wrap">{aiResult.message}</div>
                           </div>
                        {:else}
                           <div class="opacity-20 flex flex-col gap-4">
                              <p class="animate-pulse">>> WAITING_FOR_COMMAND...</p>
                              <p class="opacity-50">>> SYSTEM_IDLE: AWAITING_NEURAL_AUDIT_INPUT</p>
                           </div>
                        {/if}
                     </div>
                  </div>
               </div>
            </div>
         {:else}
            <div class="flex-1 flex flex-col items-center justify-center p-20 text-center gap-10 border border-dashed border-white/5 bg-white/[0.01]">
               <div class="relative">
                  <div class="w-32 h-32 rounded-full border border-white/10 flex items-center justify-center animate-[pulse_4s_infinite]">
                     <Activity size={64} class="text-slate-700" />
                  </div>
                  <div class="absolute inset-0 bg-cyan-500/5 blur-[60px] rounded-full"></div>
               </div>
               <div class="max-w-md">
                  <h3 class="text-xl font-black text-white tracking-[0.5em] mb-6">Awaiting_Mission_Command</h3>
                  <p class="text-[11px] text-slate-500 font-mono leading-relaxed tracking-widest">
                     Vui lòng chọn chiến dịch mục tiêu tại bảng điều khiển phía trên để kích hoạt luồng dữ liệu trinh sát AI.
                  </p>
               </div>
            </div>
         {/if}
      </main>
   </div>
</div>

<style>
   .custom-scrollbar::-webkit-scrollbar { width: 3px; }
   .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
   .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); }
   .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(6,182,212,0.2); }

   @keyframes scan {
      from { transform: translateX(0); }
      to { transform: translateX(360px); }
   }
</style>
