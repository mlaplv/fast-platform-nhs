<script lang="ts">
  import { fade } from 'svelte/transition';
  import Activity from "@lucide/svelte/icons/activity";
  import Search from "@lucide/svelte/icons/search";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Plus from "@lucide/svelte/icons/plus";

  let {
    selectedCampaign,
    adGroupLoading,
    adGroups = [],
    fetchAds,
    fmt
  } = $props();
</script>

<div class="space-y-8" in:fade>
   <div class="bg-cyan-500/5 border border-cyan-400/20 p-8 rounded-none flex flex-col md:flex-row justify-between items-center gap-6 shadow-lg relative overflow-hidden group">
      <div class="absolute inset-0 bg-gradient-to-r from-cyan-400/5 to-transparent pointer-events-none"></div>
      <div class="flex items-center gap-5 text-cyan-400 font-black text-sm tracking-tighter relative z-10 font-mono">
         <div class="p-2 bg-cyan-400/10 rounded-none">
            <Activity size={20} />
         </div>
         <span>ĐANG KIỂM TRA_MATRIX: {selectedCampaign?.name}</span>
      </div>
      <div class="flex items-center gap-4 relative z-10">
         <div class="relative w-64">
            <Search size={12} class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input 
               type="text" 
               placeholder="Lọc nhóm quảng cáo..."
               class="w-full bg-black/40 border border-white/10 rounded-none py-2 pl-9 pr-3 text-[10px] text-white focus:border-cyan-400/50 outline-none transition-all font-mono"
            />
         </div>
         <div class="text-[9px] text-slate-500 font-mono font-black tracking-[0.2em]">INFRA_LEVEL: 02 // AD_GROUPS</div>
      </div>
   </div>
   
   {#if adGroupLoading}
      <div class="py-32 flex flex-col items-center gap-6">
         <RefreshCw size={48} class="animate-spin text-cyan-400 opacity-30" />
         <span class="text-[9px] font-mono font-black text-slate-500 tracking-[0.4em]">SYNCHRONIZING_GROUPS...</span>
      </div>
   {:else}
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
         {#each adGroups as ag}
            <div class="bg-white/[0.03] border border-white/10 p-8 rounded-none hover:border-cyan-400/40 transition-all group/ag relative overflow-hidden shadow-xl flex flex-col cursor-pointer" onclick={() => fetchAds(ag)}>
               <div class="absolute top-0 right-0 w-32 h-32 bg-cyan-400/5 blur-[50px] rounded-none transition-opacity opacity-50 group-hover/ag:opacity-100"></div>
               <h5 class="text-white font-black text-lg tracking-tighter mb-6 group-hover/ag:text-cyan-400 transition-colors relative z-10 ">{ag.name}</h5>
               <div class="mt-auto flex justify-between items-center pt-6 border-t border-white/5 relative z-10">
                  <span class="text-[9px] text-slate-500 font-mono font-black tracking-widest">CPC_BID_VND</span>
                  <span class="text-white font-mono font-black text-sm">{fmt(ag.cpc_bid_vnd)}₫</span>
               </div>
            </div>
         {/each}
         <button class="bg-white/[0.01] border border-dashed border-white/20 p-8 rounded-none hover:bg-white/[0.05] hover:border-cyan-400/30 transition-all flex flex-col items-center justify-center gap-5 group/add min-h-[180px]">
            <div class="w-12 h-12 rounded-none border border-white/10 flex items-center justify-center group-hover/add:border-cyan-400/50 transition-all">
               <Plus size={24} class="text-slate-600 group-hover/add:text-cyan-400 group-hover/add:rotate-90 transition-all" />
            </div>
            <span class="text-[9px] text-slate-500 font-mono font-black tracking-[0.2em]">ADD_NEW_AD_GROUP</span>
         </button>
      </div>
   {/if}
</div>
