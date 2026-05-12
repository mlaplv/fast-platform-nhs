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
  
  // Chart Logic (SVG Line)
  const chartData = $derived(campaignMetrics.slice(-10).map((m, i) => ({
    x: i * 40,
    y: 100 - (Math.min(100, (Number(m.invalid_clicks) / (Number(m.clicks) || 1)) * 500)),
    val: m.invalid_clicks
  })));

  function copyText(text: string) {
    navigator.clipboard.writeText(text);
  }
</script>

<div class="flex flex-col gap-6 h-full" in:fade>
   <!-- TOP BAR: STATUS & GLOBAL CONTROLS -->
   <div class="flex items-center justify-between bg-white/[0.03] border border-white/5 p-4 backdrop-blur-xl">
      <div class="flex items-center gap-6">
         <div class="flex items-center gap-3 border-r border-white/10 pr-6">
            <div class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_#22d3ee]"></div>
            <span class="text-[10px] font-black text-white tracking-[0.2em] font-mono uppercase">Neural Engine Online</span>
         </div>
         <div class="flex items-center gap-4">
            <span class="text-[9px] text-slate-500 font-mono uppercase tracking-widest">Active Insights:</span>
            <span class="text-[10px] font-black text-cyan-400 font-mono">{insights.length} Patterns Detected</span>
         </div>
      </div>
      
      {#if selectedCampaign}
         <div class="flex items-center gap-4 bg-rose-500/10 px-4 py-2 border border-rose-500/20">
            <Target size={14} class="text-rose-500" />
            <span class="text-[9px] font-black text-white uppercase tracking-widest font-mono">Target: {selectedCampaign.name}</span>
            <button 
               class="ml-2 p-1 hover:text-rose-400 transition-colors" 
               onclick={() => selectedCampaign = null}
            >
               <X size={12} />
            </button>
         </div>
      {:else}
         <div class="flex items-center gap-3 relative">
            <span class="text-[9px] text-slate-500 font-mono uppercase tracking-widest">Target_Selection:</span>
            
            <!-- CUSTOM HUD DROPDOWN -->
            <div class="relative min-w-[200px]">
               <button 
                  class="w-full bg-black/60 border border-white/10 px-4 py-2 text-[9px] font-black text-cyan-400 font-mono flex items-center justify-between hover:border-cyan-500/50 transition-all uppercase tracking-widest group"
                  onclick={() => dropdownOpen = !dropdownOpen}
               >
                  <span>{selectedCampaign?.name || 'Awaiting_Target...'}</span>
                  <ChevronDown size={14} class="transition-transform {dropdownOpen ? 'rotate-180' : ''}" />
               </button>

               {#if dropdownOpen}
                  <div 
                     class="absolute top-full left-0 w-full mt-1 bg-[#0f0f0f] border border-cyan-500/30 shadow-[0_20px_50px_rgba(0,0,0,0.8)] z-[2000] max-h-[300px] overflow-y-auto custom-scrollbar"
                     in:slide={{duration: 200}}
                  >
                     {#each campaigns as c}
                        <button 
                           class="w-full text-left px-5 py-3 text-[9px] font-black text-slate-400 font-mono hover:bg-cyan-500/10 hover:text-cyan-400 transition-all border-b border-white/5 last:border-none uppercase tracking-widest"
                           onclick={() => {
                              selectedCampaign = c;
                              dropdownOpen = false;
                           }}
                        >
                           {c.name}
                        </button>
                     {/each}
                     {#if campaigns.length === 0}
                        <div class="p-4 text-[8px] text-slate-600 font-mono text-center uppercase tracking-widest">No_Active_Campaigns</div>
                     {/if}
                  </div>
               {/if}
            </div>
         </div>
      {/if}
   </div>

   <!-- MAIN GRID -->
   <div class="grid grid-cols-12 gap-6 flex-1 min-h-0">
      
      <!-- LEFT: STRATEGIC MATRIX (Compact Sidebar) -->
      <div class="col-span-12 lg:col-span-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2 border-r border-white/5">
         
         <div class="bg-black/40 p-4 flex flex-col gap-4 relative overflow-hidden group">
            <div class="flex items-center gap-3 mb-2">
               <Globe size={14} class="text-cyan-400" />
               <h3 class="text-[9px] font-black tracking-[0.2em] text-white uppercase font-mono">System Insights</h3>
            </div>

            <div class="flex flex-col gap-3">
               {#each insights as ins}
                  <div class="bg-white/[0.02] border border-white/5 p-4 hover:bg-white/[0.05] transition-all relative group/card">
                     <div class="flex items-center gap-3 mb-2">
                        <span class="w-1 h-3" style="background-color: {priorityColor(ins.priority)}"></span>
                        <span class="text-[7px] font-black font-mono tracking-widest uppercase opacity-70" style="color: {priorityColor(ins.priority)}">
                           {ins.priority}
                        </span>
                     </div>
                     <h4 class="text-[11px] font-bold text-white mb-1 tracking-tight uppercase group-hover/card:text-cyan-400 transition-colors line-clamp-1">{ins.title}</h4>
                     <p class="text-[9px] text-slate-500 line-clamp-2 leading-relaxed">{ins.detail}</p>
                     
                     <div class="mt-3 text-[9px] font-bold text-cyan-400/80 bg-cyan-400/5 p-2 border border-cyan-400/10 italic">
                        "{ins.action}"
                     </div>
                  </div>
               {:else}
                  <div class="py-10 flex flex-col items-center justify-center opacity-20 gap-3">
                     <Brain size={32} />
                     <span class="text-[8px] font-mono tracking-[0.3em] uppercase">Scanning Matrix...</span>
                  </div>
               {/each}
            </div>
         </div>
      </div>

      <!-- RIGHT: TACTICAL CONTROL CENTER (Main Workspace) -->
      <div class="col-span-12 lg:col-span-8 flex flex-col gap-6">
         
         {#if selectedCampaign}
            <!-- CAMPAIGN HUD -->
            <div class="bg-[#0a0a0a] border border-rose-500/20 p-6 relative overflow-hidden group/hud">
               <div class="absolute top-0 right-0 w-32 h-32 bg-rose-500/5 blur-[50px] pointer-events-none"></div>
               
               <div class="flex items-center justify-between mb-6">
                  <div class="flex items-center gap-3">
                     <BarChart3 size={16} class="text-rose-500" />
                     <h3 class="text-[10px] font-black tracking-[0.3em] text-rose-500 uppercase font-mono">Tactical HUD</h3>
                  </div>
                  <div class="text-[10px] font-black text-white font-mono opacity-40">#{selectedCampaign.resource_name.split('/').pop()}</div>
               </div>

               <div class="text-2xl font-black text-white tracking-tighter uppercase mb-8 line-clamp-1 border-l-4 border-rose-600 pl-4">
                  {selectedCampaign.name}
               </div>

               <div class="grid grid-cols-3 gap-6 mb-8">
                  <div class="bg-white/5 p-4 border border-white/5">
                     <div class="text-[8px] text-slate-500 font-black uppercase mb-1">Safety</div>
                     <div class="text-lg font-black text-cyan-400 font-mono tracking-tighter">98.2%</div>
                  </div>
                  <div class="bg-white/5 p-4 border border-white/5">
                     <div class="text-[8px] text-slate-500 font-black uppercase mb-1">Risk</div>
                     <div class="text-lg font-black text-rose-500 font-mono tracking-tighter uppercase">Low</div>
                  </div>
                  <div class="bg-white/5 p-4 border border-white/5">
                     <div class="text-[8px] text-slate-500 font-black uppercase mb-1">Budget</div>
                     <div class="text-[11px] font-black text-white font-mono tracking-tighter">{fmt(selectedCampaign.daily_budget_vnd)}₫</div>
                  </div>
               </div>

               <button 
                  class="w-full py-5 bg-rose-600 hover:bg-rose-500 text-white font-black text-[11px] tracking-[0.3em] uppercase transition-all active:scale-95 flex items-center justify-center gap-4 shadow-[0_15px_40px_rgba(244,63,94,0.3)] relative overflow-hidden"
                  onclick={() => aiSuggest('RSA', `Strategic analysis for: ${selectedCampaign.name}`)}
                  disabled={aiLoading}
               >
                  {#if aiLoading}
                     <RefreshCw size={18} class="animate-spin" />
                     <span>DECODING_DATA...</span>
                  {:else}
                     <Brain size={18} />
                     <span>Khởi chạy Xohi Strategist</span>
                  {/if}
                  <div class="absolute bottom-0 left-0 h-1 bg-white/20 {aiLoading ? 'w-full animate-pulse' : 'w-0'} transition-all"></div>
               </button>
            </div>

            <!-- TERMINAL OUTPUT -->
            <div class="flex-1 bg-black border border-white/10 p-6 flex flex-col font-mono relative min-h-[300px]">
               <div class="flex items-center justify-between mb-4 border-b border-white/10 pb-4">
                  <div class="flex items-center gap-3">
                     <Terminal size={14} class="text-rose-500" />
                     <span class="text-[9px] font-black text-rose-500 uppercase tracking-widest">Xohi_Strategist_Output</span>
                  </div>
                  <div class="flex gap-1">
                     <div class="w-1.5 h-1.5 bg-rose-500/20"></div>
                     <div class="w-1.5 h-1.5 bg-rose-500/40"></div>
                     <div class="w-1.5 h-1.5 bg-rose-500 animate-pulse"></div>
                  </div>
               </div>

               <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 text-[11px] leading-relaxed text-slate-400">
                  {#if aiResult}
                     <div in:fade>
                        <p class="text-rose-400 font-black mb-4">>> ANALYSIS_COMPLETE</p>
                        <p class="text-white mb-8 border-l-2 border-rose-500 pl-4">{aiResult.message}</p>
                        
                        {#if aiResult.headlines}
                           <div class="mb-8">
                              <div class="text-[9px] text-slate-600 font-black uppercase mb-3 border-b border-white/5 pb-1">Gợi ý Headlines (RSA):</div>
                              <div class="grid gap-2">
                                 {#each aiResult.headlines as h}
                                    <div class="flex items-center justify-between group/line bg-white/5 p-2 border border-transparent hover:border-cyan-500/30 transition-colors">
                                       <span class="text-white truncate">{h}</span>
                                       <button class="opacity-0 group-hover/line:opacity-100 p-1 hover:text-cyan-400 transition-opacity" onclick={() => copyText(h)}>
                                          <Copy size={12} />
                                       </button>
                                    </div>
                                 {/each}
                              </div>
                           </div>
                        {/if}

                        {#if aiResult.descriptions}
                           <div>
                              <div class="text-[9px] text-slate-600 font-black uppercase mb-3 border-b border-white/5 pb-1">Gợi ý Descriptions:</div>
                              <div class="grid gap-2">
                                 {#each aiResult.descriptions as d}
                                    <div class="flex items-center justify-between group/line bg-white/5 p-2 border border-transparent hover:border-rose-500/30 transition-colors italic">
                                       <span class="text-slate-400 line-clamp-1">{d}</span>
                                       <button class="opacity-0 group-hover/line:opacity-100 p-1 hover:text-rose-400 transition-opacity" onclick={() => copyText(d)}>
                                          <Copy size={12} />
                                       </button>
                                    </div>
                                 {/each}
                              </div>
                           </div>
                        {/if}
                     </div>
                  {:else}
                     <div class="opacity-40">
                        <p class="mb-2">>> SYSTEM_READY</p>
                        <p class="mb-2">>> AWAITING_AI_STRATEGIST_EXECUTION...</p>
                        <p>Xohi AI sẽ phân tích hành vi người dùng, đối soát trinh sát đối thủ và luật Google Ads 2026 để đưa ra gợi ý tối ưu nhất cho chiến dịch này.</p>
                     </div>
                  {/if}
               </div>
            </div>
         {:else}
            <!-- EMPTY STATE -->
            <div class="flex-1 border border-dashed border-white/10 flex flex-col items-center justify-center p-12 text-center gap-8 opacity-40 hover:opacity-100 transition-opacity group/empty">
               <div class="relative">
                  <Activity size={64} class="text-slate-600 group-hover/empty:text-rose-500 transition-colors" />
                  <div class="absolute inset-0 bg-rose-500/10 blur-[40px] rounded-full animate-pulse opacity-0 group-hover/empty:opacity-100"></div>
               </div>
               <div class="max-w-[240px]">
                  <h4 class="text-[11px] font-black text-white uppercase tracking-[0.4em] mb-4">Hệ thống chờ mục tiêu</h4>
                  <p class="text-[9px] text-slate-500 font-mono leading-relaxed">
                     Chọn một chiến dịch mục tiêu tại thanh trạng thái phía trên hoặc tab Điều phối để kích hoạt trí tuệ chiến thuật.
                  </p>
               </div>
            </div>
         {/if}
      </div>
   </div>
</div>

<style>
   .custom-scrollbar::-webkit-scrollbar { width: 3px; }
   .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
   .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); }
   .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(6,182,212,0.2); }
</style>
