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
    fetchGoogleMetrics,
    getDateRange,
    fmt
  } = $props();

  const range = $derived(getDateRange());
</script>

<div class="flex flex-col h-full gap-8" in:fade>
   <!-- GOOGLE STATS BAR -->
   <div class="grid grid-cols-4 gap-6">
      <div class="bg-black/40 border border-white/10 p-6 rounded-sm flex flex-col gap-2 shadow-[inset_0_0_20px_rgba(0,243,255,0.02)]">
         <span class="text-[9px] text-slate-500 font-black uppercase tracking-[0.2em]">Tổng Click Quảng cáo</span>
         <span class="text-3xl font-black font-mono tracking-tighter text-white">{fmt(googleTotalClicks)}</span>
      </div>
      <div class="bg-ruby/5 border border-ruby/20 p-6 rounded-sm flex flex-col gap-2 shadow-[inset_0_0_20px_rgba(255,62,94,0.02)]">
         <span class="text-[9px] text-ruby font-black uppercase tracking-[0.2em]">Click Không Hợp Lệ</span>
         <span class="text-3xl font-black font-mono text-ruby tracking-tighter">{fmt(googleTotalInvalid)}</span>
      </div>
      <div class="bg-white/5 border border-white/10 p-6 rounded-sm flex flex-col gap-2">
         <span class="text-[9px] text-slate-500 font-black uppercase tracking-[0.2em]">Tỉ lệ Vi phạm TB</span>
         <span class="text-3xl font-black font-mono text-cyan-400 tracking-tighter">{googleAvgRate.toFixed(2)}%</span>
      </div>
      <div class="bg-white/5 border border-white/10 p-6 rounded-sm flex flex-col gap-2 shadow-[inset_0_0_20px_rgba(16,185,129,0.02)]">
         <span class="text-[9px] text-slate-500 font-black uppercase tracking-[0.2em]">Ngân sách thu hồi</span>
         <span class="text-3xl font-black font-mono text-emerald-400 tracking-tighter">{fmt(googleTotalCost)}₫</span>
      </div>
   </div>

   <!-- MAIN CONTENT AREA -->
   <div class="flex-1 bg-white/[0.02] border border-white/5 rounded-sm flex flex-col overflow-hidden">
      <div class="flex justify-between items-center p-6 border-b border-white/5 bg-white/[0.01]">
         <div class="flex items-center gap-4">
            <div class="p-3 bg-cyan-400/10 rounded-full animate-pulse">
               <Globe size={18} class="text-cyan-400" />
            </div>
            <div class="flex flex-col">
               <h3 class="text-xs font-black uppercase tracking-widest text-white">Đối soát Dữ liệu Google Ads</h3>
               <p class="text-[10px] text-slate-500 font-mono mt-1 uppercase tracking-tighter">
                  Phạm vi: {range.from} → {range.to} // Cửa sổ phân tích {selectedHours} Giờ
               </p>
            </div>
         </div>
         <button 
            class="flex items-center gap-2 px-8 py-3 bg-white text-black text-[10px] font-black uppercase tracking-widest hover:bg-cyan-400 transition-all shadow-xl active:scale-95"
            onclick={fetchGoogleMetrics}
            disabled={googleLoading}
         >
            <RefreshCw size={14} class={googleLoading ? 'animate-spin' : ''} />
            <span>{googleLoading ? 'Đang giải mã tín hiệu...' : 'Đồng bộ Dữ liệu Live'}</span>
         </button>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar">
         {#if googleError}
            <div class="h-full flex flex-col items-center justify-center text-ruby gap-4">
               <AlertTriangle size={48} />
               <span class="text-xs font-black uppercase tracking-widest">Lỗi Xác thực Nút Mạng API</span>
            </div>
         {:else if googleMetrics.length > 0}
            <table class="w-full border-collapse">
               <thead class="sticky top-0 bg-black/95 backdrop-blur-md z-10">
                  <tr class="text-[10px] text-slate-500 font-black uppercase tracking-widest text-left border-b border-white/10">
                     <th class="p-6">Chiến dịch / Mục tiêu</th>
                     <th class="p-6 text-right">Tổng Click</th>
                     <th class="p-6 text-right">Không hợp lệ</th>
                     <th class="p-6 text-right">Tỉ lệ phát hiện</th>
                     <th class="p-6 text-right">Giá trị bảo vệ</th>
                  </tr>
               </thead>
               <tbody class="font-mono text-[12px]">
                  {#each googleMetrics as m}
                     {@const rate = m.invalid_click_rate || (m.clicks > 0 ? (m.invalid_clicks / m.clicks) * 100 : 0)}
                     <tr class="border-b border-white/[0.03] hover:bg-white/[0.02] transition-all {rate > 10 ? 'bg-ruby/5' : ''} group">
                        <td class="p-6">
                           <div class="flex items-center gap-4">
                              <div class="w-8 h-8 flex items-center justify-center bg-white/5 border border-white/5 rounded-sm">
                                 <Megaphone size={14} class="text-cyan-400 opacity-40" />
                              </div>
                              <div class="flex flex-col">
                                 <span class="text-white font-black tracking-tighter uppercase group-hover:text-cyan-400 transition-colors">{m.campaign_name}</span>
                                 <span class="text-[9px] text-slate-600 font-bold uppercase tracking-widest">Mạng Tìm kiếm</span>
                              </div>
                           </div>
                        </td>
                        <td class="p-6 text-right text-slate-300">{fmt(m.clicks)}</td>
                        <td class="p-6 text-right text-ruby font-black">{fmt(m.invalid_clicks)}</td>
                        <td class="p-6 text-right font-black {rate > 10 ? 'text-ruby' : 'text-cyan-400'}">
                           <div class="flex items-center justify-end gap-2">
                              <span>{rate.toFixed(2)}%</span>
                              {#if rate > 10}
                                 <Activity size={10} class="animate-pulse" />
                              {/if}
                           </div>
                        </td>
                        <td class="p-6 text-right text-emerald-400 font-black">{fmt(m.cost_vnd)}₫</td>
                     </tr>
                  {/each}
               </tbody>
            </table>
         {:else}
            <div class="h-full flex flex-col items-center justify-center opacity-30 gap-6">
               <ShieldCheck size={80} class="text-emerald-500/30" />
               <span class="text-[10px] font-black uppercase tracking-[0.5em] text-center">Đang giám sát luồng dữ liệu...<br/>Chưa phát hiện click ảo</span>
            </div>
         {/if}
      </div>
   </div>
</div>
