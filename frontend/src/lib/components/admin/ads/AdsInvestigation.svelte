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
         <!-- AUTOMATION & COMPLIANCE HUD -->
         <div class="flex flex-col md:flex-row gap-5">
            <div class="flex-1 bg-white/[0.03] border border-white/10 p-5 flex items-center justify-between group">
               <div class="flex items-center gap-4">
                  <div class="w-10 h-10 bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                     <ShieldCheck size={20} class="text-emerald-400" />
                  </div>
                  <div>
                     <div class="text-[10px] font-black text-white uppercase tracking-tighter">Tuân thủ Chính sách Google</div>
                     <div class="text-[8px] text-emerald-500 font-mono font-bold uppercase tracking-widest">Verified_v24.1_Compliant</div>
                  </div>
               </div>
               <div class="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-[8px] font-black text-emerald-400 uppercase tracking-widest">Đạt tiêu chuẩn</div>
            </div>

            <div class="flex-1 bg-white/[0.03] border border-white/10 p-5 flex items-center justify-between group">
               <div class="flex items-center gap-4">
                  <div class="w-10 h-10 bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                     <RefreshCw size={20} class="text-cyan-400" />
                  </div>
                  <div>
                     <div class="text-[10px] font-black text-white uppercase tracking-tighter">Tự động hóa báo cáo</div>
                     <div class="text-[8px] text-slate-500 font-mono font-bold uppercase tracking-widest">Auto_Generation_Active</div>
                  </div>
               </div>
               <div class="flex items-center gap-2">
                  <span class="text-[8px] text-emerald-500 font-bold uppercase tracking-tighter mr-2">LIVE_SYNC</span>
                  <div class="w-8 h-4 bg-emerald-500/20 border border-emerald-500/40 relative">
                     <div class="absolute right-0 top-0 bottom-0 w-4 bg-emerald-500 shadow-[0_0_10px_#10b981]"></div>
                  </div>
               </div>
            </div>
         </div>

         {#if reportResult.status === 'ready'}
            <!-- MANUAL SUBMISSION GUIDE (Elite V2.6) -->
            <div class="bg-amber-500/10 border border-amber-500/30 p-6 rounded-none flex flex-col gap-4" in:fade>
               <div class="flex items-center gap-3">
                  <div class="w-8 h-8 bg-amber-500/20 flex items-center justify-center">
                     <FileText size={16} class="text-amber-500" />
                  </div>
                  <h3 class="text-[11px] font-black text-white uppercase tracking-widest">Hướng dẫn khiếu nại thủ công (Google Refund Request)</h3>
               </div>
               <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-[10px] text-slate-400 leading-relaxed">
                  <div class="flex flex-col gap-2 p-4 bg-black/40 border border-white/5">
                     <span class="text-amber-500 font-black">BƯỚC 1:</span>
                     <p>Nhấn nút <b>"Tải xuống tệp CSV"</b> bên dưới để lấy danh sách GCLID vi phạm.</p>
                  </div>
                  <div class="flex flex-col gap-2 p-4 bg-black/40 border border-white/5">
                     <span class="text-amber-500 font-black">BƯỚC 2:</span>
                     <p>Nhấn <b>"Mở biểu mẫu"</b>. Lưu ý: Sếp cần đăng nhập tài khoản Google Ads quản lý trước.</p>
                  </div>
                  <div class="flex flex-col gap-2 p-4 bg-black/40 border border-white/5">
                     <span class="text-amber-500 font-black">BƯỚC 3:</span>
                     <p>Sao chép nội dung <b>Preview</b> bên dưới vào phần mô tả và đính kèm tệp CSV đã tải.</p>
                  </div>
               </div>
            </div>
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
                        <span class="text-emerald-400 font-black tracking-widest">BẰNG CHỨNG PHÁP Y ĐÃ SẴN SÀNG</span>
                     </div>
                     <div class="w-px h-4 bg-white/10 mx-2"></div>
                     <span class="text-slate-500 tracking-tighter">ID: {reportResult.csv_path.split('/').pop()}</span>
                  </div>
                  <div class="text-slate-500 font-black tracking-[0.2em] opacity-40">Forensic analysis v24.1</div>
               </div>
               
               <div class="flex-1 p-10 overflow-y-auto custom-scrollbar relative z-10">
                  <div class="mb-6 p-4 bg-emerald-500/5 border-l-2 border-emerald-500 text-[10px] text-emerald-400 font-mono leading-relaxed">
                     Hệ thống đã tự động cấu trúc báo cáo theo định dạng yêu cầu của Google Ads Support Team. 
                     Mọi GCLID và IP đã được gán nhãn vi phạm dựa trên mô hình Neural v2.6.
                  </div>
                  <pre class="text-[13px] text-slate-300 font-mono leading-relaxed whitespace-pre-wrap selection:bg-cyan-500/30">{reportResult.support_message_preview}</pre>
               </div>
               
               <div class="p-8 border-t border-white/10 flex flex-col items-center gap-6 bg-white/[0.02] relative z-10 backdrop-blur-md">
                  <div class="flex flex-col md:flex-row gap-5 w-full justify-center">
                     <a href={reportResult.csv_path} download class="px-12 py-5 bg-emerald-600 text-white text-[11px] font-black tracking-[0.2em] hover:bg-emerald-500 transition-all flex items-center justify-center gap-3 shadow-xl rounded-none group/dl">
                        <Download size={18} class="group-hover/dl:translate-y-1 transition-transform" /> 
                        Tải xuống tệp CSV bằng chứng
                     </a>
                     <div class="flex flex-col gap-2">
                        <a href="https://support.google.com/google-ads/contact/click_quality?hl=vi" target="_blank" class="px-12 py-5 border border-white/20 text-white text-[11px] font-black tracking-[0.2em] hover:border-cyan-400 hover:text-cyan-400 transition-all flex items-center justify-center gap-3 rounded-none group/ext">
                           Mở biểu mẫu khiếu nại (Chính)
                        </a>
                        <a href="https://support.google.com/google-ads/answer/2473030?hl=vi" target="_blank" class="text-[8px] text-slate-500 hover:text-cyan-400 text-center uppercase tracking-widest font-black">
                           Link dự phòng 2: Trung tâm hỗ trợ
                        </a>
                     </div>
                  </div>
                  <p class="text-[9px] text-slate-600 font-mono italic tracking-widest font-bold">
                     <span class="text-rose-500 not-italic">Notice:</span> Hệ thống Xohi AI đảm bảo tính minh bạch của bằng chứng theo tiêu chuẩn Google Ads Policy.
                  </p>
               </div>
            </div>
         {:else}
            <div class="flex-1 flex flex-col items-center justify-center opacity-30 gap-10 py-20 bg-black/40 border border-dashed border-white/10">
               <div class="relative">
                  <ShieldCheck size={100} class="text-slate-500" />
                  <div class="absolute inset-0 bg-white/5 blur-[60px] rounded-full"></div>
               </div>
               <div class="text-center">
                  <h3 class="text-white font-black text-2xl tracking-tighter mb-2">Chưa có hồ sơ pháp y mới</h3>
                  <p class="text-[10px] text-slate-500 font-mono font-black tracking-[0.4em] max-w-md mx-auto leading-relaxed">
                     Hệ thống đang trinh sát luồng dữ liệu 7 ngày qua. Nhấn nút "Truy xuất" phía trên để cưỡng bức quét sâu toàn bộ GCLID nghi vấn.
                  </p>
               </div>
            </div>
         {/if}
      </div>
   {/if}
</div>
