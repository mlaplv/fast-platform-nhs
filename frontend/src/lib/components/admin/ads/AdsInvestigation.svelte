<script lang="ts">
  import { fade, scale } from 'svelte/transition';
  import Download from "@lucide/svelte/icons/download";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import FileText from "@lucide/svelte/icons/file-text";
  import Search from "@lucide/svelte/icons/search";

  let { 
    reportResult = null,
    reportLoading = false,
    generateReport,
    fmt
  } = $props();
</script>

<div class="flex flex-col h-full gap-8" in:fade>
   <!-- INVESTIGATION HEADER -->
   <div class="bg-white/[0.02] border border-white/5 rounded-none p-8 flex justify-between items-center shadow-2xl relative group overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>

      <div class="flex items-center gap-6 relative z-10">
         <div class="p-4 bg-cyan-400/10 rounded-none border border-cyan-400/20 group-hover:scale-110 transition-transform">
            <Search size={24} class="text-cyan-400" />
         </div>
         <div>
            <h2 class="text-xl font-black text-white tracking-tighter tracking-[0.05em] mb-1">Cổng truy xuất pháp y dữ liệu</h2>
            <p class="text-[10px] text-slate-500 font-mono font-bold tracking-widest">Thiết lập bằng chứng gian lận để khiếu nại Google Ads</p>
         </div>
      </div>
      <button 
         class="px-10 py-4 bg-white text-black text-[11px] font-black tracking-[0.2em] hover:bg-cyan-400 transition-all flex items-center gap-4 shadow-xl active:scale-95 rounded-none relative z-10 group/btn" 
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
      <div class="flex-1 flex flex-col gap-8 overflow-hidden" in:fade={{duration: 600}}>
         {#if reportResult.status === 'ready'}
            <!-- SUMMARY STATS -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
               <div class="bg-black/60 border border-white/10 p-8 rounded-none relative overflow-hidden group shadow-xl">
                  <div class="absolute top-0 right-0 p-6 opacity-[0.03] group-hover:opacity-10 transition-all text-cyan-400 group-hover:scale-110">
                    <ShieldCheck size={64} />
                  </div>
                  <span class="text-[9px] text-slate-500 font-mono font-black tracking-widest block mb-3">Tổng số click gian lận phát hiện</span>
                  <div class="flex items-baseline gap-3">
                    <span class="text-4xl font-black font-mono text-white tracking-tighter">{reportResult.total_fraud_clicks}</span>
                    <span class="text-[10px] text-slate-500 font-black tracking-widest">Deployments</span>
                  </div>
               </div>
               <div class="bg-rose-500/[0.03] border border-rose-500/20 p-8 rounded-none relative overflow-hidden group shadow-xl">
                  <div class="absolute top-0 right-0 p-6 opacity-[0.03] group-hover:opacity-10 transition-all text-rose-500 group-hover:scale-110">
                    <FileText size={64} />
                  </div>
                  <span class="text-[9px] text-rose-500 font-mono font-black tracking-widest block mb-3">Giá trị yêu cầu hoàn tiền ước tính</span>
                  <div class="flex items-baseline gap-3">
                    <span class="text-4xl font-black font-mono text-rose-500 tracking-tighter">{fmt(reportResult.estimated_wasted_vnd as number)}₫</span>
                    <span class="text-[10px] text-rose-500/50 font-black tracking-widest">Reclaimable</span>
                  </div>
               </div>
            </div>
            
            <!-- EVIDENCE TERMINAL -->
            <div class="flex-1 bg-black border border-white/10 rounded-none flex flex-col overflow-hidden shadow-2xl relative">
               <div class="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none"></div>
               
               <div class="bg-white/[0.05] px-8 py-5 text-[10px] font-mono flex justify-between items-center border-b border-white/10 relative z-10 backdrop-blur-md">
                  <div class="flex items-center gap-4">
                     <div class="flex items-center gap-2">
                        <span class="w-2 h-2 rounded-none bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]"></span>
                        <span class="text-emerald-400 font-black tracking-widest">Dữ liệu đã sẵn sàng</span>
                     </div>
                     <div class="w-px h-4 bg-white/10 mx-2"></div>
                     <span class="text-slate-500 tracking-tighter">ID truy vết: {reportResult.csv_path.split('/').pop()?.slice(0, 16)}...</span>
                  </div>
                  <div class="text-slate-500 font-black tracking-[0.2em] opacity-40">Forensic analysis v24.1</div>
               </div>
               
               <div class="flex-1 p-10 overflow-y-auto custom-scrollbar relative z-10">
                  <pre class="text-[13px] text-slate-300 font-mono leading-relaxed whitespace-pre-wrap selection:bg-cyan-500/30">{reportResult.support_message_preview}</pre>
               </div>
               
               <div class="p-8 border-t border-white/10 flex flex-col items-center gap-6 bg-white/[0.02] relative z-10 backdrop-blur-md">
                  <div class="flex flex-col md:flex-row gap-5 w-full justify-center">
                     <a href={reportResult.csv_path} download class="px-12 py-5 bg-emerald-600 text-white text-[11px] font-black tracking-[0.2em] hover:bg-emerald-500 transition-all flex items-center justify-center gap-3 shadow-xl rounded-none group/dl">
                        <Download size={18} class="group-hover/dl:translate-y-1 transition-transform" /> 
                        Tải xuống tệp CSV bằng chứng
                     </a>
                     <a href="https://support.google.com/google-ads/contact/invalid_clicks_billing" target="_blank" class="px-12 py-5 border border-white/20 text-white text-[11px] font-black tracking-[0.2em] hover:border-cyan-400 hover:text-cyan-400 transition-all flex items-center justify-center gap-3 rounded-none group/ext">
                        Mở biểu mẫu khiếu nại Google
                     </a>
                  </div>
                  <p class="text-[9px] text-slate-600 font-mono italic tracking-widest font-bold">
                     <span class="text-rose-500 not-italic">Notice:</span> Đảm bảo tệp CSV bằng chứng được đính kèm khi gửi yêu cầu hoàn tiền cho Google Ads.
                  </p>
               </div>
            </div>
         {:else}
            <div class="flex-1 flex flex-col items-center justify-center opacity-30 gap-10 py-20">
               <div class="relative">
                  <ShieldCheck size={100} class="text-emerald-500" />
                  <div class="absolute inset-0 bg-emerald-500/20 blur-[60px] rounded-full animate-pulse"></div>
               </div>
               <div class="text-center">
                  <h3 class="text-white font-black text-2xl tracking-tighter mb-2">Hệ thống an toàn tuyệt đối</h3>
                  <p class="text-[10px] text-slate-500 font-mono font-black tracking-[0.4em]">Không tìm thấy mô hình gian lận trong luồng dữ liệu hiện tại</p>
               </div>
            </div>
         {/if}
      </div>
   {/if}
</div>
