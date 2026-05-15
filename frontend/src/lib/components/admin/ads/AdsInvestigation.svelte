<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import Download from "@lucide/svelte/icons/download";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import FileText from "@lucide/svelte/icons/file-text";
  import Search from "@lucide/svelte/icons/search";
  import Clock from "@lucide/svelte/icons/clock";
  import Zap from "@lucide/svelte/icons/zap";
  import Info from "@lucide/svelte/icons/info";
  import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';
  import type { InvestigationReportResult } from './adsState.svelte';

  let { 
    reportResult = null as InvestigationReportResult | null,
    reportLoading = false,
    generateReport,
    pastReports = [],
    fetchPastReports,
    viewPastReport,
    fmt
  } = $props();

  onMount(() => {
     fetchPastReports();
  });
</script>

<div class="flex flex-col h-full gap-8 font-sans" in:fade style="font-family: 'Be Vietnam Pro', sans-serif;">
   <!-- INVESTIGATION HEADER -->
   <div class="bg-white/[0.02] border border-white/5 rounded-none p-8 flex justify-between items-center shadow-2xl relative group overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-10 transition-opacity duration-1000 pointer-events-none"></div>

      <div class="flex items-center gap-6 relative z-10">
         <div class="p-4 bg-cyan-400/10 rounded-none border border-cyan-400/20 group-hover:scale-110 transition-transform shadow-[0_0_20px_rgba(6,182,212,0.1)]">
            <Search size={24} class="text-cyan-400" />
         </div>
         <div>
            <h2 class="text-xl font-black text-white tracking-tighter mb-1">Cổng truy xuất pháp y dữ liệu</h2>
            <p class="text-[10px] text-slate-500 font-mono font-bold tracking-widest opacity-60">Thiết lập bằng chứng gian lận để khiếu nại Google Ads</p>
         </div>
      </div>
      <button 
         class="px-10 py-4 bg-white text-black text-[11px] font-black tracking-[0.2em] hover:bg-cyan-400 transition-all flex items-center gap-4 shadow-[0_0_30px_rgba(255,255,255,0.1)] hover:shadow-[0_0_40px_rgba(34,211,238,0.4)] active:scale-95 rounded-none relative z-10 group/btn" 
         onclick={generateReport} 
         disabled={reportLoading}
      >
         {#if reportLoading}
            <RefreshCw class="animate-spin" size={18} />
         {:else}
            <FileText size={18} class="group-hover/btn:rotate-12 transition-transform" />
         {/if}
         <span>{reportLoading ? 'Đang phân tích tín hiệu...' : 'Truy xuất báo cáo pháp y'}</span>
      </button>
   </div>

   {#if reportResult}
      <div class="flex-1 flex flex-col gap-8" in:fade={{duration: 600}}>
         <!-- AUTOMATION & COMPLIANCE HUD -->
         <div class="flex flex-col md:flex-row gap-5">
            <div class="flex-1 bg-white/[0.03] border border-white/10 p-5 flex items-center justify-between group">
               <div class="flex items-center gap-4">
                  <div class="w-10 h-10 bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                     <ShieldCheck size={20} class="text-emerald-400" />
                  </div>
                  <div>
                     <div class="text-[10px] font-black text-white tracking-tighter">Tuân thủ Chính sách Google</div>
                     <div class="text-[8px] text-emerald-500 font-mono font-bold tracking-widest">Verified_v24.1_Compliant</div>
                  </div>
               </div>
               <div class="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-[8px] font-black text-emerald-400 tracking-widest">Đạt tiêu chuẩn</div>
            </div>

            <div class="flex-1 bg-white/[0.03] border border-white/10 p-5 flex items-center justify-between group">
               <div class="flex items-center gap-4">
                  <div class="w-10 h-10 bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                     <RefreshCw size={20} class="text-cyan-400" />
                  </div>
                  <div>
                     <div class="text-[10px] font-black text-white tracking-tighter">Tự động hóa báo cáo</div>
                     <div class="text-[8px] text-slate-500 font-mono font-bold tracking-widest">Auto_Generation_Active</div>
                  </div>
               </div>
               <div class="flex items-center gap-2">
                  <span class="text-[8px] text-emerald-500 font-bold tracking-tighter mr-2">LIVE_SYNC</span>
                  <div class="w-8 h-4 bg-emerald-500/20 border border-emerald-500/40 relative">
                     <div class="absolute right-0 top-0 bottom-0 w-4 bg-emerald-500 shadow-[0_0_10px_#10b981]"></div>
                  </div>
               </div>
            </div>
         </div>

         {#if reportResult.status === 'ready'}
            <!-- ELITE FORENSIC HUD (Elite v2.6 Refactored) -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6" in:fade>
               <!-- STAT: EVIDENCE -->
               <div class="bg-white/[0.02] border border-white/5 p-6 rounded-none flex items-center gap-5 group hover:bg-white/[0.04] transition-all">
                  <div class="w-12 h-12 bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                     <ShieldCheck size={24} class="text-cyan-400" />
                  </div>
                  <div>
                     <div class="text-[9px] text-slate-500 font-black tracking-widest mb-1">Click gian lận phát hiện</div>
                     <div class="text-2xl font-black font-mono text-white tracking-tighter">{reportResult.total_fraud_clicks} <span class="text-[10px] text-slate-500 ">Signals</span></div>
                  </div>
               </div>

               <!-- STAT: REFUND -->
               <div class="bg-white/[0.02] border border-white/5 p-6 rounded-none flex items-center gap-5 group hover:bg-rose-500/[0.04] transition-all">
                  <div class="w-12 h-12 bg-rose-500/10 border border-rose-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                     <FileText size={24} class="text-rose-500" />
                  </div>
                  <div>
                     <div class="text-[9px] text-rose-500/70 font-black tracking-widest mb-1">Ngân sách đòi lại (Dự kiến)</div>
                     <div class="text-2xl font-black font-mono text-rose-500 tracking-tighter">{fmt(reportResult.estimated_wasted_vnd as number)}₫</div>
                  </div>
               </div>

               <!-- ACTION HUD (Centrally Aligned CTA) -->
               <div class="bg-white/[0.03] border border-cyan-500/20 p-6 rounded-none flex flex-col justify-center gap-4 relative">
                  <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent pointer-events-none"></div>
                  
                  <div class="flex items-center justify-between relative z-10">
                     <span class="text-[9px] text-cyan-400 font-black tracking-[0.2em]">Cổng tác chiến</span>
                     <div class="group/tip relative cursor-help">
                        <Info size={14} class="text-slate-500 hover:text-white transition-colors" />
                        <!-- TOOLTIP (Elite Guidance) -->
                        <div class="absolute bottom-full right-0 mb-3 w-72 p-5 bg-[#0a0a0a] border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.8)] opacity-0 translate-y-2 pointer-events-none group-hover/tip:opacity-100 group-hover/tip:translate-y-0 transition-all" style="z-index: {Z_INDEX_ADMIN.POPOVER}">
                           <div class="text-[10px] font-black text-cyan-400 mb-3 border-b border-white/5 pb-2 tracking-widest">Mật lệnh cứu trợ 2026</div>
                           <p class="text-[9px] text-slate-400 font-mono leading-relaxed mb-3">
                              1. Gõ: <b class="text-white">"Invalid clicks investigation"</b> vào ô tìm kiếm hỗ trợ.<br/>
                              2. Chọn "Khác" -> <b class="text-white">"Email"</b> để hiện Form khiếu nại sạch.<br/>
                              3. Dán mẫu nội dung Preview & đính kèm tệp CSV vừa tải.
                           </p>
                           <div class="text-[8px] text-slate-600 italic">Lưu ý: Link trực tiếp đang lỗi, Sếp dùng Guided Help này là 100% OK.</div>
                           <div class="absolute top-full right-4 w-3 h-3 bg-[#0a0a0a] border-r border-b border-white/10 rotate-45 -mt-1.5"></div>
                        </div>
                     </div>
                  </div>

                  <div class="grid grid-cols-2 gap-3 relative z-10">
                     <a href={reportResult.csv_path} download class="py-4 bg-white/5 border border-white/10 text-white text-[10px] font-black tracking-widest hover:bg-white/10 hover:border-white/20 transition-all flex items-center justify-center gap-2">
                        <Download size={16} /> Tải bằng chứng
                     </a>
                     <a href="https://support.google.com/google-ads/gethelp" target="_blank" class="py-4 bg-cyan-600 text-white text-[10px] font-black tracking-widest hover:bg-cyan-500 transition-all flex items-center justify-center gap-2 shadow-[0_5px_15px_rgba(6,182,212,0.3)]">
                        <Zap size={16} /> Mở Portal
                     </a>
                  </div>
               </div>
            </div>
            
            <!-- EVIDENCE TERMINAL -->
            <div class="flex-1 bg-black/40 border border-white/10 rounded-none flex flex-col flex-col shadow-2xl relative min-h-[400px]">
               <div class="bg-white/[0.05] px-8 py-5 text-[10px] font-mono flex justify-between items-center border-b border-white/10 relative z-10 backdrop-blur-md">
                  <div class="flex items-center gap-4">
                     <div class="flex items-center gap-2">
                        <span class="w-2 h-2 rounded-none bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]"></span>
                        <span class="text-emerald-400 font-black tracking-widest ">Mẫu nội dung (Preview)</span>
                     </div>
                     <div class="w-px h-4 bg-white/10 mx-2"></div>
                     <span class="text-slate-600 tracking-tighter font-bold text-[8px]">Template v24.1 compliant</span>
                  </div>
                  <div class="text-slate-500 font-black tracking-[0.2em] opacity-40 text-[8px]">Forensic analysis v2.6</div>
               </div>
               
               <div class="flex-1 overflow-y-auto custom-scrollbar p-8 bg-black/20" style="font-family: 'JetBrains Mono', monospace;">
                  {#if reportLoading}
                     <div class="h-full flex flex-col items-center justify-center gap-4 opacity-50">
                        <RefreshCw size={40} class="animate-spin text-cyan-500" />
                        <span class="text-[10px] font-black tracking-[0.4em] text-cyan-400">ANALYZING_PACKETS...</span>
                     </div>
                  {:else if reportResult?.agentic_logs}
                     <div class="flex flex-col gap-3">
                        {#each reportResult.agentic_logs as log}
                           <div class="flex gap-4 group/log border-l-2 border-white/5 pl-4 py-1 hover:border-cyan-500/50 transition-colors">
                              <span class="text-[9px] text-slate-500 shrink-0 mt-1 font-bold">{log.time}</span>
                              <div class="flex flex-col gap-1">
                                 <div class="flex items-center gap-2">
                                    <span class="text-[9px] font-black tracking-widest {log.type === 'AGENT' ? 'text-cyan-400' : 'text-yellow-400'}">
                                       [{log.type}]
                                    </span>
                                    <span class="text-[11px] text-white/90 font-medium">{log.message}</span>
                                 </div>
                                 {#if log.detail}
                                    <div class="text-[9px] text-slate-500 leading-relaxed italic opacity-80 group-hover/log:opacity-100 transition-opacity">
                                       // {log.detail}
                                    </div>
                                 {/if}
                              </div>
                           </div>
                        {/each}
                        <div class="mt-6 pt-6 border-t border-white/10">
                           <span class="text-[10px] font-black text-emerald-400 tracking-[0.2em] mb-4 block">Bằng chứng pháp y Google Ads:</span>
                           <pre class="text-[11px] text-emerald-400/70 leading-relaxed whitespace-pre-wrap selection:bg-emerald-500/30 font-medium">
                              {reportResult.support_message_preview}
                           </pre>
                        </div>
                     </div>
                  {:else if reportResult?.support_message_preview}
                     <pre class="text-[11px] text-emerald-400/90 leading-relaxed whitespace-pre-wrap selection:bg-emerald-500/30 font-medium">
                        {reportResult.support_message_preview}
                     </pre>
                  {/if}
               </div>
               
               <div class="p-4 border-t border-white/5 bg-black/40 text-center relative z-10">
                  <p class="text-[9px] text-slate-600 font-mono italic tracking-widest font-bold">
                     <span class="text-rose-500 not-italic">Notice:</span> Mọi bằng chứng đã được mã hóa và chuẩn hóa theo tiêu chuẩn Google Ads Policy.
                  </p>
               </div>
            </div>
         {:else}
            <!-- EMPTY STATE -->
            <div class="flex-1 flex flex-col items-center justify-center p-20 bg-white/[0.02] border border-white/5 rounded-none relative overflow-hidden group">
               <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-cyan-500/[0.03] via-transparent to-transparent"></div>
               <div class="relative z-10 flex flex-col items-center text-center gap-6">
                  <div class="p-8 bg-white/[0.02] border border-white/5 rounded-none group-hover:scale-110 transition-transform duration-1000">
                     <ShieldCheck size={64} class="text-slate-700 group-hover:text-cyan-400 transition-colors" />
                  </div>
                  <div class="flex flex-col gap-2">
                     <h3 class="text-white text-[11px] font-black tracking-[0.3em]">Hệ thống đã sẵn sàng trinh sát</h3>
                     <p class="text-[10px] text-slate-500 font-mono font-black tracking-[0.4em] max-w-md mx-auto leading-relaxed">
                        Hệ thống đang trinh sát luồng dữ liệu 7 ngày qua. Nhấn nút "Truy xuất" phía trên để cưỡng bức quét sâu toàn bộ GCLID nghi vấn.
                     </p>
                  </div>
               </div>
            </div>
         {/if}
      </div>
   {/if}

   <!-- REPORT HISTORY (Elite Archive) -->
   {#if pastReports.length > 0}
      <div class="bg-white/[0.02] border border-white/5 rounded-none p-8 flex flex-col gap-6 shadow-2xl relative group overflow-hidden mt-8">
         <div class="flex items-center gap-3 border-b border-white/5 pb-5">
            <div class="p-2 bg-slate-500/10 border border-slate-500/20">
               <Clock size={18} class="text-slate-400" />
            </div>
            <h3 class="text-[10px] font-black tracking-[0.2em] text-slate-400 font-mono ">Lịch sử pháp y (Forensic Archive)</h3>
         </div>

         <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {#each pastReports as report}
               <button 
                  class="bg-black/40 border border-white/5 p-4 flex justify-between items-center group/report hover:border-cyan-500/30 transition-all text-left w-full"
                  onclick={() => viewPastReport(report.name)}
               >
                  <div class="flex flex-col gap-1">
                     <span class="text-[10px] font-black text-white font-mono tracking-tighter">{report.date}</span>
                     <span class="text-[8px] text-slate-500 tracking-widest">{report.name}</span>
                  </div>
                  <div class="p-2 text-slate-500 group-hover/report:text-cyan-400 transition-colors">
                     <Clock size={16} />
                  </div>
               </button>
            {/each}
         </div>
      </div>
   {/if}
</div>
