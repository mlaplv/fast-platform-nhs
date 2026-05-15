<script lang="ts">
  import { fade, fly, slide } from 'svelte/transition';
  import Globe from "@lucide/svelte/icons/globe";
  import Target from "@lucide/svelte/icons/target";
  import Brain from "@lucide/svelte/icons/brain";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Zap from "@lucide/svelte/icons/zap";
  import Search from "@lucide/svelte/icons/search";
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";

  let { 
    negativeKeywords = [], 
    campaigns = [],
    selectedCampaign = $bindable(null), 
    isGlobalNegative = $bindable(true), 
    newNegativeKeyword = $bindable(''),
    aiSuggest,
    addNegativeKeyword,
    removeNegativeKeyword
  } = $props();

  let searchQuery = $state('');
  let currentPage = $state(1);
  const itemsPerPage = 15;

  const filteredGlobal = $derived(
    negativeKeywords
      .filter(k => !k.campaign_id)
      .filter(k => k.text.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const paginatedGlobal = $derived(
    filteredGlobal.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
  );

  const totalPages = $derived(Math.ceil(filteredGlobal.length / itemsPerPage));

  $effect(() => {
    if (searchQuery) currentPage = 1;
  });
</script>

<div class="grid grid-cols-12 gap-8 h-full" in:fade>
   <!-- CỘT TRÁI (7): KHO LƯU TRỮ TOÀN CẦU -->
   <div class="col-span-7 bg-white/[0.02] border border-white/5 rounded-none p-8 flex flex-col shadow-2xl overflow-hidden relative group">
      <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>
      <div class="flex items-center justify-between mb-8 pb-4 border-b border-white/10 relative z-10">
         <div class="flex items-center gap-3">
            <Globe size={18} class="text-cyan-400" />
            <h3 class="text-xs font-black tracking-[0.1em] text-slate-400 ">Kho từ khóa phủ định toàn cầu</h3>
         </div>
         <div class="flex items-center gap-4">
            <div class="relative w-48">
               <Search size={12} class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
               <input 
                  type="text" 
                  bind:value={searchQuery}
                  placeholder="Tìm từ khóa..."
                  class="w-full bg-white/5 border border-white/10 rounded-none py-1.5 pl-9 pr-3 text-[10px] text-white focus:border-cyan-400/50 outline-none transition-all font-mono"
               />
            </div>
            <span class="text-[10px] font-mono text-slate-500 font-bold ">{filteredGlobal.length} KEYWORDS</span>
         </div>
      </div>

      <div class="flex-1 overflow-hidden flex flex-col border border-white/5 rounded-none bg-black/40 relative z-10 shadow-inner">
         <div class="grid grid-cols-3 bg-white/5 p-4 text-[10px] font-black tracking-widest text-slate-500 border-b border-white/5">
            <span>Từ khóa</span>
            <span>Loại đối khớp</span>
            <span>Phạm vi</span>
         </div>
         <div class="flex-1 overflow-y-auto custom-scrollbar font-mono text-[11px]">
            {#each paginatedGlobal as nk}
               <div class="grid grid-cols-3 p-4 border-b border-white/[0.02] hover:bg-white/[0.02] transition-all group">
                  <span class="text-white font-bold tracking-tighter">{nk.text}</span>
                  <span class="text-cyan-500/60 ">{nk.match_type}</span>
                  <span class="text-slate-600 ">{nk.set_name || 'HỆ THỐNG'}</span>
               </div>
            {:else}
               <div class="h-full flex items-center justify-center text-[10px] text-slate-700 tracking-[0.3em] font-black opacity-20">Chưa có dữ liệu phủ định toàn cục</div>
            {/each}
         </div>

         <!-- PAGINATION -->
         {#if totalPages > 1}
            <div class="p-4 border-t border-white/10 bg-white/[0.02] flex justify-between items-center">
               <span class="text-[9px] font-mono text-slate-500 tracking-widest">Trang {currentPage}/{totalPages}</span>
               <div class="flex gap-2">
                  <button 
                     class="p-1.5 rounded-none bg-white/5 border border-white/10 text-slate-400 hover:text-white disabled:opacity-20 transition-all"
                     disabled={currentPage === 1}
                     onclick={() => currentPage--}
                   >
                     <ChevronLeft size={14} />
                  </button>
                  <button 
                     class="p-1.5 rounded-none bg-white/5 border border-white/10 text-slate-400 hover:text-white disabled:opacity-20 transition-all"
                     disabled={currentPage === totalPages}
                     onclick={() => currentPage++}
                  >
                     <ChevronRight size={14} />
                  </button>
               </div>
            </div>
         {/if}
      </div>
   </div>

   <!-- CỘT PHẢI (5): ĐIỀU KHIỂN TRIỂN KHAI -->
   <div class="col-span-5 h-full relative">
      <div class="sticky top-0 flex flex-col gap-8">
         <!-- CONTROL PANEL -->
         <div class="bg-white/[0.03] border border-white/10 rounded-none p-8 shadow-2xl relative overflow-hidden">
            <div class="absolute top-0 right-0 w-24 h-24 bg-cyan-400/5 blur-3xl rounded-none"></div>
            
            <div class="flex items-center justify-between mb-8 pb-4 border-b border-white/10">
               <div class="flex items-center gap-3">
                  <Target size={18} class={isGlobalNegative ? 'text-cyan-400' : 'text-ruby'} />
                  <h3 class="text-xs font-black tracking-widest {isGlobalNegative ? 'text-cyan-400' : 'text-ruby'}">
                     Mục tiêu: {isGlobalNegative ? 'Toàn bộ Tài khoản' : 'Chiến dịch Cụ thể'}
                  </h3>
               </div>
               <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" bind:checked={isGlobalNegative} class="sr-only peer" />
                  <div class="w-12 h-6 bg-white/5 border border-white/10 rounded-none peer peer-checked:bg-cyan-600/50 after:content-[''] after:absolute after:top-[4px] after:left-[4px] after:bg-slate-400 after:rounded-none after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-6 peer-checked:after:bg-cyan-400"></div>
               </label>
            </div>

            {#if !isGlobalNegative}
               <div class="mb-8" in:slide>
                  <label class="block text-[8px] text-slate-500 font-black mb-3 tracking-widest font-mono ">Lựa chọn mục tiêu thực thi</label>
                  <div class="relative">
                     <select 
                        bind:value={selectedCampaign} 
                        class="w-full bg-black/60 border border-white/10 rounded-none p-4 text-sm font-black text-white focus:border-ruby/50 outline-none appearance-none transition-all shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)] hover:border-white/20 cursor-pointer"
                     >
                        <option value={null} class="bg-[#0a0a0a] text-slate-500">-- CHỌN CHIẾN DỊCH / NHÓM --</option>
                        {#each campaigns as c}
                           <option value={c} class="bg-[#0a0a0a] text-white">{c.name} (Campaign)</option>
                           {#if c.ad_groups}
                              {#each c.ad_groups as ag}
                                 <option value={ag} class="bg-[#0a0a0a] text-ruby/80">&nbsp;&nbsp;↳ {ag.name} (Ad Group)</option>
                              {/each}
                           {/if}
                        {/each}
                     </select>
                     <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
                        <ChevronDown size={18} />
                     </div>
                  </div>
               </div>
            {/if}

            <div class="flex flex-col gap-4 mb-8">
               <div class="flex justify-between items-center">
                  <span class="text-[10px] text-slate-500 font-black ">Nhập danh sách từ khóa</span>
                  <button class="flex items-center gap-2 px-4 py-2 bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-[10px] font-black hover:bg-cyan-400 hover:text-black transition-all rounded-none" onclick={() => aiSuggest('NEGATIVE_KEYWORDS', 'Suggest high-risk keywords')}>
                     <Brain size={14} /> <span>Gợi ý từ Xohi AI</span>
                  </button>
               </div>
               <textarea 
                  bind:value={newNegativeKeyword}
                  class="w-full bg-black/60 border border-white/10 rounded-none p-5 text-sm font-mono text-cyan-50 h-40 focus:border-cyan-400/40 outline-none transition-all"
                  placeholder="Nhập mỗi từ khóa trên một dòng..."
               ></textarea>
            </div>

            <button 
               class="w-full py-5 {isGlobalNegative ? 'bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-500 hover:to-cyan-600' : 'bg-gradient-to-r from-ruby to-rose-700 hover:from-rose-500 hover:to-rose-600'} text-white font-black tracking-[0.3em] text-xs transition-all active:scale-[0.98] shadow-[0_10px_30px_rgba(0,0,0,0.3)] flex items-center justify-center gap-3 rounded-none border border-white/10"
               onclick={() => addNegativeKeyword(newNegativeKeyword)}
            >
               <Zap size={16} class="animate-pulse" />
               <span>THỰC THI TRIỂN KHAI</span>
            </button>
         </div>

         <!-- CAMPAIGN SPECIFIC -->
         {#if selectedCampaign}
            <div class="flex-1 bg-white/[0.02] border border-white/5 rounded-none p-6 flex flex-col overflow-hidden shadow-xl" in:fly={{y: 20}}>
               <div class="flex items-center gap-3 mb-4 text-ruby/80">
                  <div class="w-2 h-2 rounded-none bg-ruby animate-pulse shadow-[0_0_8px_#ff3e5e]"></div>
                  <span class="text-[10px] font-black tracking-widest truncate">Đang áp dụng: {selectedCampaign.name}</span>
               </div>
               <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-2">
                  {#each negativeKeywords.filter(k => k.campaign_id === selectedCampaign.resource_name || k.ad_group_id === selectedCampaign.resource_name) as nk}
                     <div class="flex justify-between items-center p-3 bg-white/[0.03] border border-white/5 group hover:border-ruby/30 transition-all rounded-none">
                        <span class="text-xs font-mono text-white/80 truncate">{nk.text}</span>
                        <button class="text-slate-600 hover:text-ruby transition-all rounded-none" onclick={() => removeNegativeKeyword(nk.resource_name)}>
                           <Trash2 size={14} />
                        </button>
                     </div>
                  {:else}
                     <div class="py-10 text-center text-[9px] text-slate-700 font-black tracking-widest opacity-30">Chưa có từ khóa phủ định riêng</div>
                  {/each}
               </div>
            </div>
         {/if}
      </div>
   </div>
</div>
