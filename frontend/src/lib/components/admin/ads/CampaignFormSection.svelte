<script lang="ts">
  import { fade } from 'svelte/transition';
  import Target from "@lucide/svelte/icons/target";
  import Brain from "@lucide/svelte/icons/brain";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";

  let {
    fCampaign = $bindable(),
    aiSuggest,
    aiLoading,
    submitCampaign,
    campaignSubmitting
  } = $props();
</script>

<div class="max-w-4xl mx-auto py-10" in:fade>
   <div class="bg-white/[0.03] border border-white/10 rounded-none p-12 shadow-2xl relative overflow-hidden group/form">
      <div class="absolute top-0 right-0 w-80 h-80 bg-cyan-500/5 blur-[100px] rounded-none transition-opacity group-hover/form:opacity-100"></div>
      
      <div class="flex justify-between items-center mb-12 pb-8 border-b border-white/10 relative z-10">
         <div class="flex items-center gap-5">
            <div class="p-3 bg-cyan-400/10 rounded-none border border-cyan-400/20">
               <Target size={24} class="text-cyan-400" />
            </div>
            <h4 class="text-xl font-black text-white tracking-tighter tracking-[0.05em] font-mono">Triển khai chiến dịch chiến lược</h4>
         </div>
         <button class="px-8 py-3 bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-[10px] font-black tracking-widest hover:bg-cyan-400 hover:text-black transition-all flex items-center gap-3 rounded-none group/ai shadow-lg" onclick={() => aiSuggest('CAMPAIGN', 'Optimize deployment parameters')} disabled={aiLoading}>
            <Brain size={16} class="{aiLoading ? 'animate-spin' : 'group-hover/ai:scale-110 transition-transform'}" /> 
            <span>Gợi ý từ Xohi AI</span>
         </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-12 relative z-10">
         <div class="space-y-8">
            <div class="field">
               <label class="block text-[9px] text-slate-500 font-black mb-4 tracking-widest font-mono">Tên chiến dịch</label>
               <input type="text" bind:value={fCampaign.name} class="w-full bg-black/40 border border-white/10 rounded-none p-5 text-sm font-black text-white focus:border-cyan-400/50 transition-all outline-none shadow-inner focus:bg-black/60" placeholder="Nhập tên chiến dịch..." />
            </div>
            <div class="field">
               <label class="block text-[9px] text-slate-500 font-black mb-4 tracking-widest font-mono">Ngân sách ngày (VNĐ)</label>
               <input type="number" bind:value={fCampaign.daily_budget_vnd} class="w-full bg-black/40 border border-white/10 rounded-none p-5 text-sm font-black text-cyan-400 focus:border-cyan-400/50 transition-all outline-none font-mono shadow-inner focus:bg-black/60" />
            </div>
         </div>
         <div class="space-y-8">
            <div class="field">
               <label class="block text-[9px] text-slate-500 font-black tracking-widest mb-4 font-mono">Chiến lược đấu thầu</label>
               <div class="relative">
                  <select bind:value={fCampaign.bidding_strategy} class="w-full bg-black/40 border border-white/10 rounded-none p-5 text-sm font-black text-white focus:border-cyan-400/50 transition-all outline-none appearance-none shadow-inner focus:bg-black/60">
                     <option value="MAXIMIZE_CLICKS">Tối đa hóa lượt click</option>
                     <option value="MAXIMIZE_CONVERSIONS">Tối đa hóa chuyển đổi</option>
                     <option value="TARGET_CPA">CPA mục tiêu</option>
                  </select>
                  <div class="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
                     <ChevronRight size={18} class="rotate-90" />
                  </div>
               </div>
            </div>
            <div class="field">
               <label class="block text-[9px] text-slate-500 font-black tracking-widest mb-4 font-mono">Chỉ số ROAS mục tiêu</label>
               <input type="number" step="0.1" bind:value={fCampaign.target_roas} class="w-full bg-black/40 border border-white/10 rounded-none p-5 text-sm font-black text-white focus:border-cyan-400/50 transition-all outline-none font-mono shadow-inner focus:bg-black/60" placeholder="e.g. 2.5" />
            </div>
         </div>
      </div>

      <div class="mt-16 pt-10 border-t border-white/10 flex justify-end relative z-10">
         <button class="px-16 py-5 bg-cyan-600 text-white text-[12px] font-black tracking-[0.2em] hover:bg-cyan-500 transition-all shadow-2xl active:scale-95 rounded-none" onclick={submitCampaign} disabled={campaignSubmitting}>
            {campaignSubmitting ? 'Đang triển khai...' : 'Khởi tạo chiến dịch'}
         </button>
      </div>
   </div>
</div>
