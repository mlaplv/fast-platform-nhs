<script lang="ts">
  import { fade, slide, scale } from 'svelte/transition';
  import Plus from "@lucide/svelte/icons/plus";
  import X from "@lucide/svelte/icons/x";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Megaphone from "@lucide/svelte/icons/megaphone";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Play from "@lucide/svelte/icons/play";
  import Pause from "@lucide/svelte/icons/pause";
  import Brain from "@lucide/svelte/icons/brain";
  import Settings from "@lucide/svelte/icons/settings";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Activity from "@lucide/svelte/icons/activity";

  let { 
    campaigns = [],
    campaignLoading = false,
    campaignView = $bindable('list'),
    selectedCampaign = $bindable(null),
    adGroups = [],
    adGroupLoading = false,
    selectedAdGroup = $bindable(null),
    ads = [],
    adsLoading = false,
    fCampaign = $bindable(),
    campaignSubmitting = false,
    aiLoading = false,
    fetchCampaigns,
    fetchAdGroups,
    fetchAds,
    updateCampaignStatus,
    submitCampaign,
    aiSuggest,
    fmt,
    activeTab = $bindable()
  } = $props();
</script>

<div class="grid grid-cols-12 gap-8 h-full" in:fade>
   <!-- MODULE CHÍNH -->
   <div class="col-span-12 bg-white/[0.02] border border-white/5 rounded-sm flex flex-col overflow-hidden shadow-2xl">
      <!-- CONTROL HEADER -->
      <header class="bg-white/[0.05] p-6 border-b border-white/10 flex justify-between items-center">
         <div class="flex items-center gap-4">
            <Megaphone size={18} class="text-cyan-400" />
            <div class="flex items-center gap-3">
               <h3 class="text-xs font-black uppercase tracking-widest text-white">ĐIỀU PHỐI CHIẾN DỊCH</h3>
               {#if campaignView !== 'list'}
                  <ChevronRight size={14} class="text-slate-600" />
                  <span class="text-[10px] font-black text-cyan-400 uppercase tracking-widest bg-cyan-400/10 px-3 py-1 rounded-full">
                     {campaignView === 'create_campaign' ? 'TẠO CHIẾN DỊCH' : campaignView === 'ad_groups' ? 'NHÓM QUẢNG CÁO' : 'MẪU QUẢNG CÁO'}
                  </span>
               {/if}
            </div>
         </div>

         <div class="flex items-center gap-4">
            {#if campaignView === 'list'}
               <button class="px-6 py-2 bg-cyan-600 text-white text-[10px] font-black uppercase tracking-widest hover:brightness-125 transition-all active:scale-95 flex items-center gap-2" onclick={() => campaignView = 'create_campaign'}>
                  <Plus size={14} /> <span>Tạo Chiến dịch Mới</span>
               </button>
            {:else}
               <button class="px-6 py-2 bg-white/5 border border-white/10 text-white text-[10px] font-black uppercase tracking-widest hover:bg-white/10 transition-all flex items-center gap-2" onclick={() => {
                  if (campaignView === 'create_campaign' || campaignView === 'ad_groups') campaignView = 'list';
                  else if (campaignView === 'ads') campaignView = 'ad_groups';
               }}>
                  <X size={14} /> <span>Quay lại</span>
               </button>
            {/if}
            <button class="w-10 h-10 flex items-center justify-center bg-black/40 border border-white/5 rounded-sm hover:border-cyan-400/50 transition-all" onclick={fetchCampaigns} disabled={campaignLoading}>
               <RefreshCw size={14} class={campaignLoading ? 'animate-spin text-cyan-400' : 'text-slate-500'} />
            </button>
         </div>
      </header>

      <!-- VIEWPORT -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-8">
         {#if campaignView === 'list'}
            <div class="overflow-hidden border border-white/5 rounded-sm">
               <table class="w-full border-collapse">
                  <thead>
                     <tr class="bg-white/[0.03] text-[10px] text-slate-500 font-black uppercase tracking-[0.2em] text-left">
                        <th class="p-6">Tên Chiến dịch / ID</th>
                        <th class="p-6">Trạng thái</th>
                        <th class="p-6 text-right">Ngân sách Ngày</th>
                        <th class="p-6 text-right">Thao tác</th>
                     </tr>
                  </thead>
                  <tbody class="font-mono text-xs text-slate-300">
                     {#each campaigns as c}
                        <tr class="border-b border-white/[0.02] hover:bg-white/[0.02] transition-all group {selectedCampaign?.id === c.id ? 'bg-cyan-500/5' : ''}">
                           <td class="p-6">
                              <div class="flex flex-col gap-1">
                                 <span class="text-white font-black text-sm tracking-tighter cursor-pointer group-hover:text-cyan-400 transition-colors" onclick={() => fetchAdGroups(c)}>{c.name}</span>
                                 <span class="text-[9px] text-slate-600 uppercase font-bold">MÃ: {c.resource_name.split('/').pop()}</span>
                              </div>
                           </td>
                           <td class="p-6">
                              <span class="px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest {c.status === 'ENABLED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-500 border border-white/5'}">
                                 {c.status === 'ENABLED' ? 'Đang chạy' : 'Đã dừng'}
                              </span>
                           </td>
                           <td class="p-6 text-right text-white font-bold text-sm">
                              {fmt(c.daily_budget_vnd)}₫
                           </td>
                           <td class="p-6">
                              <div class="flex justify-end gap-4">
                                 <button class="w-8 h-8 flex items-center justify-center bg-white/5 rounded-sm text-slate-500 hover:text-cyan-400 transition-all" onclick={() => fetchAdGroups(c)} title="Thiết lập">
                                    <Settings size={14} />
                                 </button>
                                 <button class="w-8 h-8 flex items-center justify-center bg-white/5 rounded-sm text-slate-500 hover:text-ruby transition-all" onclick={() => { selectedCampaign = c; activeTab = 'negative_keywords'; }} title="Kiểm soát Rủi ro">
                                    <ShieldAlert size={14} />
                                 </button>
                                 {#if c.status === 'PAUSED'}
                                    <button class="w-8 h-8 flex items-center justify-center bg-emerald-500/10 border border-emerald-500/30 rounded-sm text-emerald-500 hover:bg-emerald-500 hover:text-white transition-all" onclick={() => updateCampaignStatus(c.resource_name, 'ENABLED')}>
                                       <Play size={14} />
                                    </button>
                                 {:else}
                                    <button class="w-8 h-8 flex items-center justify-center bg-amber-500/10 border border-amber-500/30 rounded-sm text-amber-500 hover:bg-amber-500 hover:text-white transition-all" onclick={() => updateCampaignStatus(c.resource_name, 'PAUSED')}>
                                       <Pause size={14} />
                                    </button>
                                 {/if}
                              </div>
                           </td>
                        </tr>
                     {:else}
                        <tr><td colspan="4" class="p-20 text-center opacity-20 uppercase font-black tracking-[0.5em] text-[10px]">Đang quét hạ tầng Google Ads...</td></tr>
                     {/each}
                  </tbody>
               </table>
            </div>
         {:else if campaignView === 'create_campaign'}
            <div class="max-w-4xl mx-auto py-10" in:slide>
               <div class="bg-white/[0.03] border border-white/10 rounded-sm p-10 shadow-2xl relative overflow-hidden">
                  <div class="absolute top-0 right-0 w-40 h-40 bg-cyan-400/5 blur-3xl rounded-full"></div>
                  
                  <div class="flex justify-between items-center mb-10 pb-6 border-b border-white/10">
                     <div class="flex items-center gap-4">
                        <Activity size={20} class="text-cyan-400" />
                        <h4 class="text-lg font-black text-white uppercase tracking-tighter">Triển khai Chiến dịch Chiến lược</h4>
                     </div>
                     <button class="px-6 py-2 bg-cyan-400/10 border border-cyan-400/30 text-cyan-400 text-[10px] font-black uppercase hover:bg-cyan-400 hover:text-black transition-all flex items-center gap-3" onclick={() => aiSuggest('CAMPAIGN', 'Optimize deployment parameters')} disabled={aiLoading}>
                        <Brain size={14} class={aiLoading ? 'animate-spin' : ''} /> <span>Gợi ý từ Xohi AI</span>
                     </button>
                  </div>

                  <div class="grid grid-cols-2 gap-10">
                     <div class="space-y-6">
                        <div class="field">
                           <label class="block text-[10px] text-slate-500 font-black uppercase mb-3">Tên Chiến dịch Deployment</label>
                           <input type="text" bind:value={fCampaign.name} class="w-full bg-black/60 border border-white/10 p-4 text-sm font-bold text-white focus:border-cyan-400 transition-all outline-none" />
                        </div>
                        <div class="field">
                           <label class="block text-[10px] text-slate-500 font-black uppercase mb-3">Ngân sách Ngày (VNĐ)</label>
                           <input type="number" bind:value={fCampaign.daily_budget_vnd} class="w-full bg-black/60 border border-white/10 p-4 text-sm font-bold text-cyan-400 focus:border-cyan-400 transition-all outline-none font-mono" />
                        </div>
                     </div>
                     <div class="space-y-6">
                        <div class="field">
                           <label class="block text-[10px] text-slate-500 font-black uppercase mb-3">Chiến lược Đấu thầu</label>
                           <select bind:value={fCampaign.bidding_strategy} class="w-full bg-black/60 border border-white/10 p-4 text-sm font-bold text-white focus:border-cyan-400 transition-all outline-none appearance-none">
                              <option value="MAXIMIZE_CLICKS">TỐI ĐA HÓA LƯỢT CLICK</option>
                              <option value="MAXIMIZE_CONVERSIONS">TỐI ĐA HÓA CHUYỂN ĐỔI</option>
                              <option value="TARGET_CPA">CPA MỤC TIÊU</option>
                           </select>
                        </div>
                        <div class="field">
                           <label class="block text-[10px] text-slate-500 font-black uppercase mb-3">Chỉ số ROAS Mục tiêu</label>
                           <input type="number" step="0.1" bind:value={fCampaign.target_roas} class="w-full bg-black/60 border border-white/10 p-4 text-sm font-bold text-white focus:border-cyan-400 transition-all outline-none font-mono" />
                        </div>
                     </div>
                  </div>

                  <div class="mt-12 pt-8 border-t border-white/5 flex justify-end">
                     <button class="px-12 py-5 bg-cyan-600 text-white text-[12px] font-black uppercase tracking-[0.3em] hover:brightness-125 transition-all shadow-xl active:scale-95" onclick={submitCampaign} disabled={campaignSubmitting}>
                        {campaignSubmitting ? 'ĐANG TRIỂN KHAI...' : 'KHỞI TẠO CHIẾN DỊCH'}
                     </button>
                  </div>
               </div>
            </div>
         {:else if campaignView === 'ad_groups'}
            <div class="space-y-8" in:fade>
               <div class="bg-cyan-900/5 border border-cyan-400/20 p-6 rounded-sm flex justify-between items-center">
                  <div class="flex items-center gap-4 text-cyan-400 font-black uppercase text-sm tracking-tighter">
                     <Activity size={18} />
                     <span>Đang Kiểm tra: {selectedCampaign?.name}</span>
                  </div>
                  <div class="text-[10px] text-slate-500 font-mono italic uppercase">Cấp độ Hạ tầng: 02 (Nhóm Quảng cáo)</div>
               </div>
               
               {#if adGroupLoading}
                  <div class="py-20 flex justify-center"><RefreshCw size={32} class="animate-spin text-cyan-400 opacity-20" /></div>
               {:else}
                  <div class="grid grid-cols-3 gap-6">
                     {#each adGroups as ag}
                        <div class="bg-white/[0.03] border border-white/5 p-6 rounded-sm hover:border-cyan-400/30 transition-all group relative overflow-hidden" onclick={() => fetchAds(ag)}>
                           <div class="absolute top-0 right-0 w-16 h-16 bg-cyan-400/5 blur-2xl rounded-full"></div>
                           <h5 class="text-white font-black text-base tracking-tighter mb-4 group-hover:text-cyan-400 transition-colors cursor-pointer">{ag.name}</h5>
                           <div class="flex justify-between items-baseline pt-4 border-t border-white/5">
                              <span class="text-[10px] text-slate-500 font-black uppercase tracking-widest">GIÁ THẦU CPC</span>
                              <span class="text-white font-mono font-bold">{fmt(ag.cpc_bid_vnd)}₫</span>
                           </div>
                        </div>
                     {/each}
                     <button class="bg-white/2 border border-dashed border-white/10 p-6 rounded-sm hover:bg-white/5 transition-all flex flex-col items-center justify-center gap-3 group">
                        <Plus size={24} class="text-slate-600 group-hover:text-cyan-400 transition-colors" />
                        <span class="text-[10px] text-slate-500 font-black uppercase tracking-widest">Tạo Nhóm Quảng cáo Mới</span>
                     </button>
                  </div>
               {/if}
            </div>
         {/if}
      </div>
   </div>
</div>
