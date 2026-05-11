<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import Globe from "@lucide/svelte/icons/globe";
  import Target from "@lucide/svelte/icons/target";
  import Brain from "@lucide/svelte/icons/brain";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Zap from "@lucide/svelte/icons/zap";

  let { 
    negativeKeywords = [], 
    selectedCampaign = null, 
    isGlobalNegative = $bindable(true), 
    newNegativeKeyword = $bindable(''),
    aiSuggest,
    addNegativeKeyword,
    removeNegativeKeyword
  } = $props();
</script>

<div class="grid grid-cols-12 gap-8 h-full" in:fade>
   <!-- CỘT TRÁI (7): KHO LƯU TRỮ TOÀN CẦU -->
   <div class="col-span-7 bg-white/[0.02] border border-white/5 rounded-sm p-8 flex flex-col">
      <div class="flex items-center gap-3 mb-8 pb-4 border-b border-white/5">
         <Globe size={18} class="text-cyan-400" />
         <h3 class="text-xs font-black uppercase tracking-[0.2em] text-slate-400">KHO TỪ KHÓA PHỦ ĐỊNH TOÀN CẦU</h3>
      </div>

      <div class="flex-1 overflow-hidden flex flex-col border border-white/5 rounded-sm bg-black/40">
         <div class="grid grid-cols-3 bg-white/5 p-4 text-[10px] font-black uppercase tracking-widest text-slate-500">
            <span>Từ khóa</span>
            <span>Loại Đối khớp</span>
            <span>Phạm vi</span>
         </div>
         <div class="flex-1 overflow-y-auto custom-scrollbar font-mono text-[11px]">
            {#each negativeKeywords.filter(k => !k.campaign_id) as nk}
               <div class="grid grid-cols-3 p-4 border-b border-white/[0.02] hover:bg-white/[0.02] transition-all group">
                  <span class="text-white font-bold tracking-tighter">{nk.text}</span>
                  <span class="text-cyan-500/60 uppercase">{nk.match_type}</span>
                  <span class="text-slate-600 uppercase">{nk.set_name || 'HỆ THỐNG'}</span>
               </div>
            {:else}
               <div class="h-full flex items-center justify-center text-[10px] uppercase text-slate-700 tracking-[0.3em] font-black opacity-20">Chưa có dữ liệu phủ định toàn cục</div>
            {/each}
         </div>
      </div>
   </div>

   <!-- CỘT PHẢI (5): ĐIỀU KHIỂN TRIỂN KHAI -->
   <div class="col-span-5 flex flex-col gap-8">
      <!-- CONTROL PANEL -->
      <div class="bg-white/[0.03] border border-white/10 rounded-sm p-8 shadow-2xl relative overflow-hidden">
         <div class="absolute top-0 right-0 w-24 h-24 bg-cyan-400/5 blur-3xl rounded-full"></div>
         
         <div class="flex items-center justify-between mb-8 pb-4 border-b border-white/10">
            <div class="flex items-center gap-3">
               <Target size={18} class={isGlobalNegative ? 'text-cyan-400' : 'text-ruby'} />
               <h3 class="text-xs font-black uppercase tracking-widest {isGlobalNegative ? 'text-cyan-400' : 'text-ruby'}">
                  Mục tiêu: {isGlobalNegative ? 'Toàn bộ Tài khoản' : 'Chiến dịch Cụ thể'}
               </h3>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
               <input type="checkbox" bind:checked={isGlobalNegative} class="sr-only peer" />
               <div class="w-12 h-6 bg-white/5 border border-white/10 rounded-full peer peer-checked:bg-cyan-600/50 after:content-[''] after:absolute after:top-[4px] after:left-[4px] after:bg-slate-400 after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-6 peer-checked:after:bg-cyan-400"></div>
            </label>
         </div>

         <div class="flex flex-col gap-4 mb-8">
            <div class="flex justify-between items-center">
               <span class="text-[10px] text-slate-500 font-black uppercase">Nhập danh sách từ khóa</span>
               <button class="flex items-center gap-2 px-4 py-2 bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-[10px] font-black uppercase hover:bg-cyan-400 hover:text-black transition-all" onclick={() => aiSuggest('NEGATIVE_KEYWORDS', 'Suggest high-risk keywords')}>
                  <Brain size={14} /> <span>Gợi ý từ Xohi AI</span>
               </button>
            </div>
            <textarea 
               bind:value={newNegativeKeyword}
               class="w-full bg-black/60 border border-white/10 rounded-sm p-5 text-sm font-mono text-cyan-50 h-40 focus:border-cyan-400/40 outline-none transition-all"
               placeholder="Nhập mỗi từ khóa trên một dòng..."
            ></textarea>
         </div>

         <button 
            class="w-full py-5 {isGlobalNegative ? 'bg-cyan-600' : 'bg-ruby'} text-white font-black tracking-[0.3em] text-xs hover:brightness-125 transition-all active:scale-95 shadow-xl flex items-center justify-center gap-3"
            onclick={() => addNegativeKeyword(newNegativeKeyword)}
         >
            <Zap size={16} />
            <span>THỰC THI TRIỂN KHAI</span>
         </button>
      </div>

      <!-- CAMPAIGN SPECIFIC -->
      {#if selectedCampaign}
         <div class="flex-1 bg-white/[0.02] border border-white/5 rounded-sm p-6 flex flex-col overflow-hidden">
            <div class="flex items-center gap-3 mb-4 text-ruby/80">
               <div class="w-2 h-2 rounded-full bg-ruby animate-pulse shadow-[0_0_8px_#ff3e5e]"></div>
               <span class="text-[10px] font-black uppercase tracking-widest">Đang áp dụng: {selectedCampaign.name}</span>
            </div>
            <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-2">
               {#each negativeKeywords.filter(k => k.campaign_id) as nk}
                  <div class="flex justify-between items-center p-3 bg-white/[0.03] border border-white/5 group hover:border-ruby/30 transition-all">
                     <span class="text-xs font-mono text-white/80">{nk.text}</span>
                     <button class="text-slate-600 hover:text-ruby transition-all" onclick={() => removeNegativeKeyword(nk.resource_name)}>
                        <Trash2 size={14} />
                     </button>
                  </div>
               {/each}
            </div>
         </div>
      {/if}
   </div>
</div>
