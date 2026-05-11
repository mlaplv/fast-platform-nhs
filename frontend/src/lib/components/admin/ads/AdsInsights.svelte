<script lang="ts">
  import { fade, scale } from 'svelte/transition';
  import Globe from "@lucide/svelte/icons/globe";
  import Target from "@lucide/svelte/icons/target";
  import Brain from "@lucide/svelte/icons/brain";
  import Activity from "@lucide/svelte/icons/activity";

  let { 
    insights = [],
    selectedCampaign = null,
    aiLoading = false,
    priorityColor,
    aiSuggest
  } = $props();
</script>

<div class="grid grid-cols-12 gap-8 h-full" in:fade>
   <!-- CỘT TRÁI (7): CHIẾN LƯỢC HỆ THỐNG -->
   <div class="col-span-7 bg-white/[0.02] border border-white/5 rounded-sm p-8 flex flex-col">
      <div class="flex items-center justify-between mb-8 pb-4 border-b border-white/5">
         <div class="flex items-center gap-3">
            <Globe size={18} class="text-cyan-400" />
            <h3 class="text-xs font-black uppercase tracking-[0.2em] text-white">MA TRẬN CHIẾN LƯỢC HỆ THỐNG</h3>
         </div>
         <div class="flex items-center gap-2">
            <div class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></div>
            <span class="text-[9px] font-black text-cyan-400 uppercase tracking-widest">ĐỘNG CƠ XOHI ĐANG CHẠY</span>
         </div>
      </div>
      
      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-6">
         {#each insights as ins}
            <div class="bg-black/40 border-l-4 p-6 rounded-sm transition-all hover:bg-white/[0.03] group" style="border-color: {priorityColor(ins.priority)}">
               <div class="flex justify-between items-start mb-4">
                  <span class="text-[9px] font-black px-3 py-1 bg-white/5 rounded-full uppercase tracking-widest" style="color: {priorityColor(ins.priority)}">
                     ƯU TIÊN {ins.priority === 'HIGH' ? 'CAO' : ins.priority === 'MEDIUM' ? 'TRUNG BÌNH' : 'THẤP'}
                  </span>
                  <div class="flex items-center gap-2 text-cyan-400 font-mono text-[10px] font-bold">
                     <Activity size={12} />
                     <span>TIẾT KIỆM ƯỚC TÍNH: {ins.estimated_saving_pct}%</span>
                  </div>
               </div>
               <h4 class="text-white text-base font-black mb-2 group-hover:text-cyan-400 transition-colors">{ins.title}</h4>
               <p class="text-[12px] text-slate-400 leading-relaxed mb-6">{ins.detail}</p>
               <div class="bg-white/[0.03] border border-white/5 p-4 rounded-sm italic text-[11px] text-cyan-50">
                  <span class="text-cyan-500 font-black not-italic text-[9px] uppercase block mb-1">HÀNH ĐỘNG KHUYẾN NGHỊ:</span>
                  "{ins.action}"
               </div>
            </div>
         {:else}
            <div class="h-full flex flex-col items-center justify-center opacity-20 gap-6">
               <Brain size={64} />
               <span class="text-[10px] uppercase tracking-[0.4em] font-black text-center">Chưa xác định được mô hình nơ-ron...<br/>Đang quét dữ liệu trực tiếp...</span>
            </div>
         {/each}
      </div>
   </div>

   <!-- CỘT PHẢI (5): TỐI ƯU CHIẾN DỊCH -->
   <div class="col-span-5 flex flex-col gap-8">
      <div class="bg-white/[0.03] border border-white/10 rounded-sm p-8 shadow-2xl relative overflow-hidden flex-1 flex flex-col">
         <div class="absolute top-0 right-0 w-32 h-32 bg-ruby/5 blur-3xl rounded-full"></div>
         
         <div class="flex items-center gap-3 mb-8 pb-4 border-b border-white/10">
            <Target size={18} class="text-ruby" />
            <h3 class="text-xs font-black uppercase tracking-widest text-ruby">TỐI ƯU CHIẾN THUẬT CHIẾN DỊCH</h3>
         </div>

         {#if selectedCampaign}
            <div class="flex-1 flex flex-col">
               <div class="bg-ruby/5 border border-ruby/20 p-6 rounded-sm mb-8">
                  <div class="text-[9px] text-ruby font-black uppercase tracking-widest mb-2">ĐỐI TƯỢNG ĐANG QUÉT:</div>
                  <div class="text-xl font-black text-white tracking-tighter mb-4">{selectedCampaign.name}</div>
                  <div class="grid grid-cols-2 gap-6 pt-4 border-t border-ruby/10">
                     <div>
                        <div class="text-slate-500 text-[9px] font-black uppercase">Điểm Bảo vệ</div>
                        <div class="text-white font-black text-lg font-mono">98.2%</div>
                     </div>
                     <div>
                        <div class="text-slate-500 text-[9px] font-black uppercase">Chỉ số Rủi ro</div>
                        <div class="text-ruby font-black text-lg font-mono">THẤP</div>
                     </div>
                  </div>
               </div>

               <button 
                  class="w-full py-6 bg-ruby text-white font-black tracking-[0.3em] text-[11px] hover:brightness-125 transition-all active:scale-95 shadow-xl flex items-center justify-center gap-3 mb-8"
                  onclick={() => aiSuggest('RSA', `Analyze tactical patterns for: ${selectedCampaign?.name}`)}
                  disabled={aiLoading}
               >
                  <Brain size={18} class={aiLoading ? 'animate-spin' : ''} />
                  <span>{aiLoading ? 'XOHI ĐANG PHÂN TÍCH...' : 'KHỞI TẠO QUÉT CHIẾN THUẬT'}</span>
               </button>

               <div class="flex-1 bg-black/60 border border-white/10 rounded-sm p-6 relative">
                  <div class="text-[9px] text-ruby font-black font-mono mb-4 flex items-center gap-2">
                     <span class="w-1.5 h-1.5 rounded-full bg-ruby animate-pulse"></span>
                     LUỒNG DỮ LIỆU ĐẦU RA XOHI
                  </div>
                  <div class="text-[11px] text-slate-400 font-mono leading-relaxed overflow-y-auto max-h-[180px]">
                     <span class="text-ruby mr-2">>></span> Đang chờ khởi tạo lệnh quét...<br/>
                     <span class="text-ruby mr-2">>></span> Trí tuệ nhân tạo Xohi sẽ phân tích hiệu suất từ khóa, tần suất click và mô hình địa lý để đề xuất các loại trừ tối ưu cho chiến dịch này.
                  </div>
               </div>
            </div>
         {:else}
            <div class="h-full flex flex-col items-center justify-center opacity-20 gap-8">
               <Activity size={64} class="text-slate-600" />
               <p class="text-[10px] uppercase tracking-[0.3em] text-center font-black leading-loose">
                  Vui lòng chọn chiến dịch mục tiêu<br/>tại Tab Điều phối<br/>để bắt đầu phân tích chiến thuật
               </p>
            </div>
         {/if}
      </div>
   </div>
</div>
