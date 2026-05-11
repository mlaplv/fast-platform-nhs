<script lang="ts">
  import { fade, scale } from 'svelte/transition';
  import Download from "@lucide/svelte/icons/download";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import FileText from "@lucide/svelte/icons/file-text";

  let { 
    reportResult = null,
    reportLoading = false,
    generateReport,
    fmt
  } = $props();
</script>

<div class="flex flex-col h-full gap-8" in:fade>
   <!-- INVESTIGATION HEADER -->
   <div class="bg-white/[0.02] border border-white/5 rounded-sm p-8 flex justify-between items-center shadow-xl">
      <div class="flex items-center gap-6">
         <div class="p-4 bg-cyan-400/10 rounded-full">
            <FileText size={24} class="text-cyan-400" />
         </div>
         <div>
            <h2 class="text-xl font-black text-white uppercase tracking-tighter">CỔNG TRUY XUẤT PHÁP Y DỮ LIỆU</h2>
            <p class="text-[11px] text-slate-500 font-bold uppercase tracking-widest mt-1">Tổng hợp bằng chứng gian lận click để khiếu nại hoàn tiền Google Ads</p>
         </div>
      </div>
      <button 
         class="px-10 py-4 bg-white text-black text-[11px] font-black uppercase tracking-[0.2em] hover:bg-cyan-400 transition-all flex items-center gap-3 shadow-[0_0_20px_rgba(255,255,255,0.1)] active:scale-95" 
         onclick={generateReport} 
         disabled={reportLoading}
      >
         {#if reportLoading}<RefreshCw class="animate-spin" size={16} />{:else}<FileText size={16} />{/if}
         <span>{reportLoading ? 'ĐANG PHÂN TÍCH TÍN HIỆU...' : 'TRUY XUẤT BÁO CÁO BẰNG CHỨNG'}</span>
      </button>
   </div>

   {#if reportResult}
      <div class="flex-1 flex flex-col gap-8 overflow-hidden" in:scale>
         {#if reportResult.status === 'ready'}
            <!-- SUMMARY STATS -->
            <div class="grid grid-cols-2 gap-8">
               <div class="bg-black/60 border border-white/5 p-8 rounded-sm relative overflow-hidden">
                  <div class="absolute top-0 right-0 p-4 opacity-5"><ShieldCheck size={48} /></div>
                  <span class="text-[10px] uppercase text-slate-500 font-black tracking-widest block mb-2">Tổng số Click gian lận phát hiện</span>
                  <span class="text-4xl font-black font-mono text-white tracking-tighter">{reportResult.total_fraud_clicks} Lượt click</span>
               </div>
               <div class="bg-ruby/5 border border-ruby/20 p-8 rounded-sm relative overflow-hidden">
                  <div class="absolute top-0 right-0 p-4 opacity-10 text-ruby"><FileText size={48} /></div>
                  <span class="text-[10px] uppercase text-ruby font-black tracking-widest block mb-2">Giá trị yêu cầu hoàn tiền ước tính</span>
                  <span class="text-4xl font-black font-mono text-ruby tracking-tighter">{fmt(reportResult.estimated_wasted_vnd as number)}₫</span>
               </div>
            </div>
            
            <!-- EVIDENCE TERMINAL -->
            <div class="flex-1 bg-black border border-white/10 rounded-sm flex flex-col overflow-hidden shadow-2xl">
               <div class="bg-white/[0.05] px-6 py-4 text-[11px] font-mono flex justify-between items-center border-b border-white/10">
                  <div class="flex items-center gap-3">
                     <span class="text-emerald-500 font-black">● SẴN SÀNG</span>
                     <span class="text-slate-500">MÃ TÀI LIỆU: {reportResult.csv_path.split('/').pop()}</span>
                  </div>
                  <div class="text-slate-500 italic">Phân tích Pháp y v24.1</div>
               </div>
               <div class="flex-1 p-10 overflow-y-auto custom-scrollbar">
                  <pre class="text-[13px] text-slate-300 font-mono leading-relaxed whitespace-pre-wrap">{reportResult.support_message_preview}</pre>
               </div>
               <div class="p-8 border-t border-white/10 flex flex-col items-center gap-6 bg-white/[0.02]">
                  <div class="flex gap-4">
                     <a href={reportResult.csv_path} download class="px-12 py-4 bg-emerald-600 text-white text-[11px] font-black uppercase tracking-[0.2em] hover:bg-emerald-500 transition-all flex items-center gap-3 shadow-[0_10px_20px_rgba(16,185,129,0.2)]">
                        <Download size={16} /> TẢI XUỐNG FILE CSV BẰNG CHỨNG
                     </a>
                     <a href="https://support.google.com/google-ads/contact/invalid_clicks_billing" target="_blank" class="px-12 py-4 border border-white/20 text-white text-[11px] font-black uppercase tracking-[0.2em] hover:border-cyan-400 hover:text-cyan-400 transition-all flex items-center gap-3">
                        MỞ BIỂU MẪU KHIẾU NẠI GOOGLE
                     </a>
                  </div>
                  <p class="text-[10px] text-slate-600 font-mono uppercase italic tracking-widest">
                     * Đảm bảo tệp CSV bằng chứng được đính kèm khi gửi yêu cầu hoàn tiền cho Google Ads.
                  </p>
               </div>
            </div>
         {:else}
            <div class="flex-1 flex flex-col items-center justify-center opacity-20 gap-8">
               <ShieldCheck size={80} class="text-emerald-500" />
               <div class="text-center">
                  <h3 class="text-white font-black text-xl uppercase tracking-tighter">HỆ THỐNG AN TOÀN: 100%</h3>
                  <p class="text-xs text-slate-500 mt-2 font-bold uppercase tracking-widest">Không tìm thấy mô hình gian lận trong luồng dữ liệu hiện tại</p>
               </div>
            </div>
         {/if}
      </div>
   {/if}
</div>
