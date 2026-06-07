<script lang="ts">
  import { fade } from 'svelte/transition';
  import Target from "@lucide/svelte/icons/target";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Activity from "@lucide/svelte/icons/activity";
  import Settings from "@lucide/svelte/icons/settings";

  let {
    selectedAdGroup,
    adsLoading,
    ads = [],
    selectAdForEdit,
    selectedCampaign
  } = $props();
</script>

<div class="space-y-8" in:fade>
   <div class="bg-emerald-500/5 border border-emerald-500/20 p-8 rounded-none flex justify-between items-center shadow-lg relative overflow-hidden">
      <div class="flex items-center gap-5 text-emerald-400 font-black text-sm tracking-tighter relative z-10 font-mono">
         <div class="p-2 bg-emerald-500/10 rounded-none">
            <Target size={20} />
         </div>
         <span>QUẢNG CÁO TRONG NHÓM: {selectedAdGroup?.name}</span>
      </div>
      <div class="text-[9px] text-slate-500 font-mono font-black tracking-[0.2em] relative z-10">INFRA_LEVEL: 03 // AD_ASSETS</div>
   </div>

   {#if adsLoading}
      <div class="py-32 flex flex-col items-center gap-6">
         <RefreshCw size={48} class="animate-spin text-emerald-400 opacity-30" />
         <span class="text-[9px] font-mono font-black text-slate-500 tracking-[0.4em]">DEPLOYING_ASSETS...</span>
      </div>
   {:else}
      <div class="overflow-hidden border border-white/10 rounded-none bg-black/20 shadow-inner">
         <table class="w-full border-collapse">
            <thead class="bg-white/5">
               <tr class="text-[9px] text-slate-500 font-mono font-black tracking-[0.2em] text-left border-b border-white/5">
                  <th class="px-8 py-5">Quảng cáo / Loại</th>
                  <th class="px-8 py-5">Trạng thái</th>
                  <th class="px-8 py-5">Hiệu suất (Lượt click)</th>
                  <th class="px-8 py-5 text-right">Thao tác</th>
               </tr>
            </thead>
            <tbody class="font-mono text-[13px] text-slate-300">
               {#each ads as ad}
                  <tr class="border-b border-white/[0.03] hover:bg-emerald-500/[0.03] transition-all group/row">
                     <td class="px-8 py-6">
                        <div class="flex flex-col gap-1">
                           <span class="text-white font-black text-sm tracking-tighter">{ad.name || 'Responsive Search Ad'}</span>
                           <span class="text-[9px] text-slate-600 font-black tracking-widest ">{ad.type || 'RSA'}</span>
                        </div>
                     </td>
                     <td class="px-8 py-6">
                        <span class="px-3 py-1 rounded-none text-[9px] font-black tracking-widest {ad.status === 'ENABLED' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-500'}">
                           {ad.status === 'ENABLED' ? 'ĐANG CHẠY' : 'TẠM DỪNG'}
                        </span>
                     </td>
                     <td class="px-8 py-6">
                        <div class="flex items-center gap-2">
                           <Activity size={14} class="text-slate-600" />
                           <span class="text-white font-black">{ad.clicks || 0}</span>
                        </div>
                     </td>
                     <td class="px-8 py-6 text-right">
                        <button 
                           class="w-10 h-10 inline-flex items-center justify-center bg-white/5 border border-white/10 rounded-none text-slate-500 hover:text-emerald-400 transition-all"
                           onclick={() => selectAdForEdit(ad, selectedAdGroup, selectedCampaign)}
                        >
                           <Settings size={16} />
                        </button>
                     </td>
                   </tr>
               {:else}
                  <tr>
                     <td colspan="4" class="px-8 py-12 text-center text-[10px] text-slate-600 font-black tracking-[0.2em]">Không tìm thấy mẫu quảng cáo nào</td>
                  </tr>
               {/each}
            </tbody>
         </table>
      </div>
   {/if}
</div>
