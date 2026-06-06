<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import Globe from "@lucide/svelte/icons/globe";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import AlertTriangle from "@lucide/svelte/icons/alert-triangle";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Megaphone from "@lucide/svelte/icons/megaphone";
  import Activity from "@lucide/svelte/icons/activity";

  let { 
    googleMetrics = [], 
    googleLoading = false, 
    googleError = null,
    googleTotalInvalid,
    googleTotalClicks,
    googleTotalCost,
    googleAvgRate,
    selectedHours,
    dateFrom,
    fetchGoogleMetrics,
    getDateRange,
    fmt
  } = $props();

  const range = $derived(getDateRange());
</script>

<div class="flex flex-col h-full gap-8" in:fade>
   <!-- GOOGLE STATS BAR -->
   <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="bg-white/[0.02] border border-white/10 p-6 rounded-none flex flex-col gap-3 shadow-xl relative overflow-hidden group">
         <div class="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:opacity-10 transition-all text-cyan-400">
            <Activity size={48} />
         </div>
         <span class="text-[9px] text-slate-500 font-mono font-black tracking-[0.2em] relative z-10">Tổng click quảng cáo</span>
         <span class="text-3xl font-black font-mono tracking-tighter text-white relative z-10">{fmt(googleTotalClicks)}</span>
      </div>
      <div class="bg-rose-500/[0.02] border border-rose-500/10 p-6 rounded-none flex flex-col gap-3 shadow-xl relative overflow-hidden group">
         <div class="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:opacity-10 transition-all text-rose-500">
            <AlertTriangle size={48} />
         </div>
         <span class="text-[9px] text-rose-500 font-mono font-black tracking-[0.2em] relative z-10">Click không hợp lệ</span>
         <span class="text-3xl font-black font-mono text-rose-500 tracking-tighter relative z-10">{fmt(googleTotalInvalid)}</span>
      </div>
      <div class="bg-white/[0.02] border border-white/10 p-6 rounded-none flex flex-col gap-3 shadow-xl relative overflow-hidden group">
         <div class="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:opacity-10 transition-all text-cyan-400">
            <ShieldCheck size={48} />
         </div>
         <span class="text-[9px] text-slate-500 font-mono font-black tracking-[0.2em] relative z-10">Tỉ lệ vi phạm trung bình</span>
         <span class="text-3xl font-black font-mono text-cyan-400 tracking-tighter relative z-10">{googleAvgRate.toFixed(2)}%</span>
      </div>
      <div class="bg-emerald-500/[0.02] border border-emerald-500/10 p-6 rounded-none flex flex-col gap-3 shadow-xl relative overflow-hidden group">
         <div class="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:opacity-10 transition-all text-emerald-500">
            <Activity size={48} />
         </div>
         <span class="text-[9px] text-slate-500 font-mono font-black tracking-[0.2em] relative z-10">Ngân sách thu hồi</span>
         <span class="text-3xl font-black font-mono text-emerald-400 tracking-tighter relative z-10">{fmt(googleTotalCost)}₫</span>
      </div>
   </div>

   <!-- MAIN CONTENT AREA -->
    <div class="flex-1 bg-white/[0.02] border border-white/5 rounded-none flex flex-col overflow-hidden shadow-2xl relative group">
       <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>
       {#if googleLoading}
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm z-20 flex flex-col items-center justify-center gap-4" in:fade>
             <RefreshCw size={32} class="animate-spin text-cyan-400" />
             <span class="text-[10px] font-black tracking-widest text-cyan-400 animate-pulse">ĐANG CẬP NHẬT DỮ LIỆU...</span>
          </div>
       {/if}

      <div class="flex justify-between items-center p-8 border-b border-white/10 bg-white/[0.01] relative z-10 backdrop-blur-md">
         <div class="flex items-center gap-5">
            <div class="p-3 bg-cyan-400/10 rounded-none border border-cyan-400/20 animate-pulse">
               <Globe size={20} class="text-cyan-400" />
            </div>
            <div class="flex flex-col">
               <h3 class="text-sm font-black tracking-widest text-white tracking-[0.1em]">Đối soát dữ liệu Google Ads</h3>
               <p class="text-[10px] text-slate-500 font-mono mt-1 tracking-tighter font-bold">
                  Phạm vi: <span class="text-cyan-400">{range.from}</span> → <span class="text-cyan-400">{range.to}</span> 
                  // <span class="text-slate-600">{dateFrom ? 'Khoảng ngày tùy chỉnh' : `Cửa sổ ${selectedHours}h`}</span>
               </p>
            </div>
         </div>
         <button 
            class="flex items-center gap-3 px-8 py-4 bg-white text-black text-[11px] font-black tracking-widest hover:bg-cyan-400 transition-all shadow-xl active:scale-95 rounded-none group/btn"
            onclick={fetchGoogleMetrics}
            disabled={googleLoading}
         >
            <RefreshCw size={16} class="{googleLoading ? 'animate-spin' : 'group-hover/btn:rotate-180 transition-transform duration-500'}" />
            <span>{googleLoading ? 'Đang giải mã tín hiệu...' : 'Đồng bộ dữ liệu trực tiếp'}</span>
         </button>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar relative z-10">
         {#if googleError}
            <div class="h-full flex flex-col items-center justify-center text-rose-500 gap-6 py-20 px-8 text-center max-w-2xl mx-auto">
               <AlertTriangle size={64} class="animate-bounce text-rose-500" />
               <span class="text-[10px] font-black tracking-[0.4em] font-mono uppercase text-rose-400">LỖI XÁC THỰC API GOOGLE ADS</span>
               <p class="text-xs font-mono bg-rose-950/20 border border-rose-500/20 p-4 text-rose-300 select-all whitespace-pre-wrap leading-relaxed">{googleError}</p>
            </div>
         {:else if googleMetrics.length > 0}
            <table class="w-full border-collapse">
               <thead class="sticky top-0 bg-black/90 backdrop-blur-xl z-10 border-b border-white/10">
                  <tr class="text-[9px] text-slate-500 font-mono font-black tracking-widest text-left ">
                     <th class="px-8 py-5">Chiến dịch / Mục tiêu</th>
                     <th class="px-8 py-5 text-right">Tổng Click</th>
                     <th class="px-8 py-5 text-right">Không hợp lệ</th>
                     <th class="px-8 py-5 text-right">Tỉ lệ phát hiện</th>
                     <th class="px-8 py-5 text-right">Giá trị bảo vệ</th>
                  </tr>
               </thead>
               <tbody class="font-mono text-[12px]">
                  {#each googleMetrics as m}
                     {@const rate = (m.invalid_click_rate * 100) || (m.clicks > 0 ? (m.invalid_clicks / m.clicks) * 100 : 0)}
                     <tr class="border-b border-white/[0.03] hover:bg-white/[0.02] transition-all {rate > 10 ? 'bg-rose-500/[0.03]' : ''} group/row">
                        <td class="px-8 py-5">
                           <div class="flex items-center gap-4">
                              <div class="w-10 h-10 flex items-center justify-center bg-white/5 border border-white/10 rounded-none group-hover/row:border-cyan-400/30 transition-all">
                                 <Megaphone size={16} class="text-cyan-400 opacity-40 group-hover/row:opacity-100 transition-opacity" />
                              </div>
                              <div class="flex flex-col">
                                 <span class="text-white font-black tracking-tighter group-hover/row:text-cyan-400 transition-colors text-sm">{m.campaign_name}</span>
                                 <span class="text-[9px] text-slate-600 font-bold tracking-widest">Google search network</span>
                              </div>
                           </div>
                        </td>
                        <td class="px-8 py-5 text-right text-slate-400 font-bold">{fmt(m.clicks)}</td>
                        <td class="px-8 py-5 text-right text-rose-500 font-black">{fmt(m.invalid_clicks)}</td>
                        <td class="px-8 py-5 text-right font-black {rate > 10 ? 'text-rose-500' : 'text-cyan-400'}">
                           <div class="flex items-center justify-end gap-2">
                              <span class="text-sm">{rate.toFixed(2)}%</span>
                              {#if rate > 10}
                                 <Activity size={12} class="animate-pulse" />
                              {/if}
                           </div>
                        </td>
                        <td class="px-8 py-5 text-right text-emerald-400 font-black text-sm">{fmt(m.cost_vnd)}₫</td>
                     </tr>
                  {/each}
               </tbody>
            </table>
         {:else}
            <div class="h-full flex flex-col items-center justify-center opacity-20 gap-10 py-24">
               <div class="relative">
                  <ShieldCheck size={100} class="text-emerald-500/30" />
                  <div class="absolute inset-0 bg-emerald-500/10 blur-[60px] rounded-full animate-pulse"></div>
               </div>
               <span class="text-[10px] font-mono font-black tracking-[0.6em] text-center leading-loose">
                  Đang giám sát luồng dữ liệu...<br/>
                  Chưa phát hiện click ảo
               </span>
            </div>
         {/if}
      </div>
   </div>
</div>
