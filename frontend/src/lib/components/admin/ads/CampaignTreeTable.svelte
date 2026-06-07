<script lang="ts">
  import { slide, fade } from 'svelte/transition';
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Settings from "@lucide/svelte/icons/settings";
  import Brain from "@lucide/svelte/icons/brain";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Play from "@lucide/svelte/icons/play";
  import Pause from "@lucide/svelte/icons/pause";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Target from "@lucide/svelte/icons/target";
  import { apiClient } from '$lib/utils/apiClient';

  let {
    paginatedCampaigns = [],
    campaigns = [],
    expandedCampaigns = $bindable({}),
    expandedAdGroups = $bindable({}),
    campaignAdGroups = $bindable({}),
    adGroupAds = $bindable({}),
    loadingCampaigns = $bindable({}),
    loadingAdGroups = $bindable({}),
    expandedAds = $bindable({}),
    selectedCampaign = $bindable(),
    selectedAdGroup = $bindable(),
    fAd = $bindable(),
    isEditingAd = $bindable(),
    campaignView = $bindable(),
    adGroupKeywords = $bindable(),
    toggleCampaign,
    toggleAdGroup,
    toggleAd,
    fetchAdGroups,
    updateCampaignStatus,
    selectAdForEdit,
    fmt,
    activeTab = $bindable()
  } = $props();
</script>

<div class="overflow-hidden border border-white/10 rounded-none bg-black/20 shadow-inner">
   <table class="w-full border-collapse">
      <thead class="bg-white/5">
         <tr class="text-[9px] text-slate-500 font-mono font-black tracking-[0.2em] text-left border-b border-white/5">
            <th class="px-8 py-5">Chiến dịch / Target ID</th>
            <th class="px-8 py-5">Trạng thái</th>
            <th class="px-8 py-5 text-right">Ngân sách/Ngày</th>
            <th class="px-8 py-5 text-right">Hành động</th>
         </tr>
      </thead>
      <tbody class="font-mono text-[13px] text-slate-300">
         {#each paginatedCampaigns as c}
            <tr class="border-b border-white/[0.03] hover:bg-cyan-500/[0.03] transition-all group/row {selectedCampaign?.id === c.id ? 'bg-cyan-500/5' : ''}">
               <td class="px-8 py-6">
                  <div class="flex items-center gap-3">
                     <button class="w-6 h-6 flex items-center justify-center text-slate-500 hover:text-cyan-400 transition-colors" onclick={() => toggleCampaign(c)}>
                        {#if expandedCampaigns[c.resource_name]}
                           <ChevronDown size={16} class="text-cyan-400" />
                        {:else}
                           <ChevronRight size={16} />
                        {/if}
                     </button>
                     <div class="flex flex-col gap-1.5">
                        <span class="text-white font-black text-sm tracking-tighter cursor-pointer group-hover/row:text-cyan-400 transition-colors" onclick={() => toggleCampaign(c)}>{c.name}</span>
                        <span class="text-[9px] text-slate-600 font-black tracking-widest font-mono">ID: {c.resource_name.split('/').pop()}</span>
                     </div>
                  </div>
               </td>
               <td class="px-8 py-6">
                    <span class="px-4 py-1.5 rounded-none text-[9px] font-black tracking-[0.1em] font-mono {c.status === 'ENABLED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-500 border border-white/5'}">
                       {c.status === 'ENABLED' ? 'Đang chạy' : 'Đã tạm dừng'}
                    </span>
               </td>
               <td class="px-8 py-6 text-right text-white font-black text-sm font-mono">
                    {fmt(c.daily_budget_vnd)}₫
               </td>
               <td class="px-8 py-6">
                    <div class="flex justify-end gap-3">
                       <button class="w-10 h-10 flex items-center justify-center bg-white/5 border border-white/10 rounded-none text-slate-500 hover:text-cyan-400 hover:bg-cyan-400/10 transition-all shadow-md" onclick={() => fetchAdGroups(c)} title="Thiết lập">
                          <Settings size={18} />
                       </button>
                       <button class="w-10 h-10 flex items-center justify-center bg-white/5 border border-white/10 rounded-none text-slate-500 hover:text-amber-400 hover:bg-amber-400/10 transition-all shadow-md" onclick={() => { selectedCampaign = c; activeTab = 'insights'; }} title="Phân tích chiến thuật AI">
                          <Brain size={18} />
                       </button>
                       <button class="w-10 h-10 flex items-center justify-center bg-white/5 border border-white/10 rounded-none text-slate-500 hover:text-rose-500 hover:bg-rose-500/10 transition-all shadow-md" onclick={() => { selectedCampaign = c; activeTab = 'negative_keywords'; }} title="Kiểm soát rủi ro">
                          <ShieldAlert size={18} />
                       </button>
                       {#if c.status === 'PAUSED'}
                          <button class="w-10 h-10 flex items-center justify-center bg-emerald-500/10 border border-emerald-500/30 rounded-none text-emerald-500 hover:bg-emerald-600 hover:text-white transition-all shadow-lg" onclick={() => updateCampaignStatus(c.resource_name, 'ENABLED')}>
                             <Play size={18} />
                          </button>
                       {:else}
                          <button class="w-10 h-10 flex items-center justify-center bg-amber-500/10 border border-amber-500/30 rounded-none text-amber-500 hover:bg-amber-600 hover:text-white transition-all shadow-lg" onclick={() => updateCampaignStatus(c.resource_name, 'PAUSED')}>
                             <Pause size={18} />
                          </button>
                       {/if}
                    </div>
               </td>
            </tr>
            {#if expandedCampaigns[c.resource_name]}
               <tr>
                  <td colspan="4" class="p-0 border-b border-white/[0.03]">
                     {#if loadingCampaigns[c.resource_name]}
                        <div class="flex items-center gap-3 py-5 pl-16 text-cyan-400 font-mono text-[10px] tracking-widest animate-pulse">
                           <RefreshCw size={14} class="animate-spin text-cyan-400" />
                           <span>ĐANG TẢI AD_GROUPS_MATRIX...</span>
                        </div>
                     {:else if !campaignAdGroups[c.resource_name] || campaignAdGroups[c.resource_name].length === 0}
                        <div class="py-5 pl-16 text-slate-600 font-mono text-[10px] tracking-widest">
                           KHÔNG CÓ NHÓM QUẢNG CÁO NÀO
                        </div>
                     {:else}
                        <!-- Tree Branch (Ad Groups Level) -->
                        <div class="border-l border-white/10 ml-12 my-2 pl-6 flex flex-col gap-2 relative">
                           {#each campaignAdGroups[c.resource_name] as ag}
                              <!-- Ad Group Row (Clean tree node, no boxes or heavy border wrappers) -->
                              <div class="group/ag flex flex-col">
                                 <div class="flex justify-between items-center py-2.5 px-3 hover:bg-white/5 transition-all rounded-none">
                                    <div class="flex items-center gap-2.5 cursor-pointer select-none" onclick={() => toggleAdGroup(ag)}>
                                       {#if expandedAdGroups[ag.resource_name]}
                                          <ChevronDown size={14} class="text-cyan-400" />
                                       {:else}
                                          <ChevronRight size={14} class="text-slate-500" />
                                       {/if}
                                       <div class="flex flex-col">
                                          <span class="text-slate-200 font-bold text-[12px] group-hover/ag:text-cyan-400 transition-colors">{ag.name}</span>
                                          <span class="text-[8px] text-slate-600 font-mono">ID: {ag.resource_name.split('/').pop()}</span>
                                       </div>
                                    </div>
     
                                    <div class="flex items-center gap-4 text-[10px] font-mono">
                                       <span class="text-slate-500">
                                          CPC: 
                                          {#if c.bidding_strategy === 'MANUAL_CPC'}
                                             {fmt(ag.cpc_bid_vnd)}₫
                                          {:else}
                                             Tự động
                                          {/if}
                                       </span>
                                       <span class="px-2 py-0.5 rounded-none text-[8px] font-black tracking-widest {ag.status === 'ENABLED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-500 border border-white/5'}">
                                          {ag.status === 'ENABLED' ? 'ĐANG CHẠY' : 'TẠM DỪNG'}
                                       </span>
                                       <button 
                                          class="px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/35 text-[9px] text-emerald-400 hover:bg-emerald-500 hover:text-black transition-all font-black tracking-wider active:scale-95 rounded-none"
                                          onclick={(e) => { 
                                             e.stopPropagation(); 
                                             selectedCampaign = c;
                                             selectedAdGroup = ag; 
                                             
                                             // Reset form ad
                                             fAd = { headlines: Array(15).fill(''), descriptions: Array(4).fill(''), final_url: selectedCampaign?.final_url || '', display_path1: '', display_path2: '', status: 'PAUSED' };
                                             isEditingAd = false;
                                             
                                             // Lấy từ khóa nhóm quảng cáo để tính Ad Strength
                                             apiClient.get<string[]>(`/api/v1/ads/ad-groups/${ag.resource_name.split('/').pop()}/keywords`)
                                                .then((kws: string[] | null) => {
                                                   adGroupKeywords = kws ?? [];
                                                })
                                                .catch(() => {});
                                             
                                             campaignView = 'create_ad'; 
                                          }}
                                       >
                                          + THÊM QUẢNG CÁO
                                       </button>
                                    </div>
                                 </div>
     
                                 <!-- Ad Group Children (Ads Level) -->
                                 {#if expandedAdGroups[ag.resource_name]}
                                    {#if loadingAdGroups[ag.resource_name]}
                                       <div class="flex items-center gap-3 py-2 pl-8 text-emerald-400 font-mono text-[9px] tracking-widest animate-pulse border-l border-white/10 ml-4">
                                          <RefreshCw size={10} class="animate-spin text-emerald-400" />
                                          <span>ĐANG TẢI AD_ASSETS...</span>
                                       </div>
                                    {:else if !adGroupAds[ag.resource_name] || adGroupAds[ag.resource_name].length === 0}
                                       <div class="py-2 pl-8 text-slate-600 font-mono text-[9px] tracking-widest border-l border-white/10 ml-4">
                                          KHÔNG CÓ MẪU QUẢNG CÁO NÀO
                                       </div>
                                    {:else}
                                       <!-- Tree Branch (Ads Level) -->
                                       <div class="border-l border-white/10 ml-4 pl-4 flex flex-col gap-1 my-1">
                                          {#each adGroupAds[ag.resource_name] as ad}
                                             <div class="group/ad flex flex-col">
                                                <!-- Ad Row -->
                                                <div class="flex justify-between items-center py-1.5 px-3 hover:bg-white/5 transition-all rounded-none">
                                                   <div class="flex items-center gap-2 cursor-pointer group/adcell select-none" onclick={() => toggleAd(ad.resource_name)}>
                                                      {#if expandedAds[ad.resource_name]}
                                                         <ChevronDown size={12} class="text-emerald-400" />
                                                      {:else}
                                                         <ChevronRight size={12} class="text-slate-500" />
                                                      {/if}
                                                      <div class="flex flex-col">
                                                         <span class="text-slate-300 font-medium text-[11px] group-hover/adcell:text-emerald-400 transition-colors">
                                                            {ad.headlines && ad.headlines.filter(Boolean).length > 0 
                                                               ? ad.headlines.filter(Boolean).slice(0, 2).join(' | ') 
                                                               : ad.name || 'Responsive Search Ad'}
                                                         </span>
                                                         <span class="text-[8px] text-slate-600 font-mono">{ad.type || 'RSA'}</span>
                                                      </div>
                                                   </div>
      
                                                   <div class="flex items-center gap-4 text-[10px] font-mono">
                                                      <span class="px-1.5 py-0.5 rounded-none text-[8px] font-black tracking-widest {ad.status === 'ENABLED' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-500'}">
                                                         {ad.status === 'ENABLED' ? 'ĐANG CHẠY' : 'TẠM DỪNG'}
                                                      </span>
                                                      <button 
                                                         class="w-6.5 h-6.5 flex items-center justify-center bg-white/5 border border-white/10 rounded-none text-slate-500 hover:text-emerald-400 hover:bg-emerald-400/10 transition-all active:scale-95 shadow-sm" 
                                                         onclick={(e) => { 
                                                            e.stopPropagation(); 
                                                            selectAdForEdit(ad, ag, c); 
                                                         }} 
                                                         title="Thiết lập quảng cáo"
                                                      >
                                                         <Settings size={12} />
                                                      </button>
                                                   </div>
                                                </div>
      
                                                <!-- Ad Preview details box (indented like a child node) -->
                                                {#if expandedAds[ad.resource_name]}
                                                   <div class="pl-4 pr-3 pb-3 pt-1 border-l border-white/10 ml-2" transition:slide>
                                                      <div class="max-w-2xl bg-black/60 border border-white/5 p-4 rounded-none relative overflow-hidden shadow-2xl">
                                                         <div class="flex justify-between items-center mb-2.5 pb-1.5 border-b border-white/5 font-mono">
                                                            <span class="text-[8px] font-black tracking-widest text-emerald-400">GOOGLE SEARCH AD PREVIEW MOCKUP</span>
                                                            {#if ad.final_url}
                                                               <a href={ad.final_url} target="_blank" rel="noopener noreferrer" class="text-[8px] text-slate-500 hover:text-emerald-400 truncate max-w-xs">{ad.final_url}</a>
                                                            {/if}
                                                         </div>
                                                         
                                                         <!-- Search Ad Mockup -->
                                                         <div class="font-sans text-xs text-[#d1d5db] text-left">
                                                            <div class="flex items-center gap-1 text-[10px] text-slate-400 mb-1">
                                                               <span class="font-bold text-[8px] bg-white/5 px-1 py-0.5 rounded-none mr-1">Tài trợ</span>
                                                               <span class="truncate">
                                                                  {ad.final_url ? ad.final_url.replace(/^https?:\/\//, '').split('/')[0] : 'example.com'}
                                                                  {#if ad.display_path1}
                                                                     /{ad.display_path1}
                                                                  {/if}
                                                                  {#if ad.display_path2}
                                                                     /{ad.display_path2}
                                                                  {/if}
                                                               </span>
                                                            </div>
                                                            <h3 class="text-sm text-[#8ab4f8] hover:underline cursor-pointer leading-tight mb-1.5 font-medium">
                                                               {ad.headlines && ad.headlines.filter(Boolean).length > 0 
                                                                  ? ad.headlines.filter(Boolean).slice(0, 3).join(' | ') 
                                                                  : 'Tiêu đề quảng cáo hấp dẫn | Tối ưu chuyển đổi | Tiêu đề 3'}
                                                            </h3>
                                                            <p class="text-[11px] text-[#bdc1c6] leading-relaxed">
                                                               {ad.descriptions && ad.descriptions.filter(Boolean).length > 0 
                                                                  ? ad.descriptions.filter(Boolean).join(' ') 
                                                                  : 'Mô tả chi tiết về sản phẩm hoặc dịch vụ của bạn để tăng CTR và thu hút khách hàng tiềm năng.'}
                                                            </p>
                                                         </div>
                                                      </div>
                                                   </div>
                                                {/if}
                                             </div>
                                          {/each}
                                       </div>
                                    {/if}
                                 {/if}
                              </div>
                           {/each}
                        </div>
                     {/if}
                  </td>
               </tr>
            {/if}
         {:else}
             <tr>
                <td colspan="4" class="px-20 py-24 text-center">
                   <div class="flex flex-col items-center gap-4 max-w-md mx-auto" in:fade>
                      <div class="p-4 bg-cyan-400/5 border border-cyan-400/10 rounded-none mb-2">
                         <Target size={32} class="text-cyan-400/50 animate-pulse" />
                      </div>
                      <span class="text-[10px] font-black text-white tracking-[0.2em] font-mono uppercase">Tài khoản chưa có chiến dịch</span>
                      <p class="text-[10px] text-slate-500 font-medium leading-relaxed font-mono">
                         Google Ads API kết nối thành công! Tuy nhiên, tài khoản <strong>osmo</strong> hiện tại chưa có chiến dịch nào hoạt động. Sếp hãy nhấn nút <strong>"Khởi tạo chiến dịch"</strong> phía trên để bắt đầu triển khai!
                      </p>
                   </div>
                </td>
             </tr>
         {/each}
      </tbody>
   </table>
</div>
