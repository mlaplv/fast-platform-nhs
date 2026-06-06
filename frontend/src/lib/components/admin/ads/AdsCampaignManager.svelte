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
  import Target from "@lucide/svelte/icons/target";
  import Search from "@lucide/svelte/icons/search";
  import Filter from "@lucide/svelte/icons/filter";
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { onDestroy } from 'svelte';

  let { 
    campaigns = [],
    campaignLoading = false,
    campaignView = $bindable(),
    selectedCampaign = $bindable(),
    adGroups = [],
    adGroupLoading = false,
    selectedAdGroup = $bindable(),
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

  // Khởi tạo an toàn để tránh lỗi props_invalid_value
  if (campaignView === undefined) campaignView = 'list';
  if (selectedCampaign === undefined) selectedCampaign = null;
  if (selectedAdGroup === undefined) selectedAdGroup = null;

  // Search & Filter State
  let searchQuery = $state('');
  let statusFilter = $state('ALL'); // ALL, ENABLED, PAUSED
  let currentPage = $state(1);
  let itemsPerPage = 10;

  // Derived filtered campaigns
  const filteredCampaigns = $derived(
    campaigns.filter(c => {
      const matchesSearch = c.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                           c.resource_name.includes(searchQuery);
      const matchesStatus = statusFilter === 'ALL' || c.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
  );

  const paginatedCampaigns = $derived(
    filteredCampaigns.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
  );

  const totalPages = $derived(Math.ceil(filteredCampaigns.length / itemsPerPage));

  // Reset page when filter changes
  $effect(() => {
    if (searchQuery || statusFilter) {
      currentPage = 1;
    }
  });

  let isFullView = $state(false);

  function toggleFullView(): void {
    isFullView = !isFullView;
    if (typeof window !== 'undefined') {
      document.body.style.overflow = isFullView ? 'hidden' : '';
    }
  }

  onDestroy(() => {
    if (typeof window !== 'undefined') {
      document.body.style.overflow = '';
    }
  });
</script>

<div 
   use:portal={isFullView}
   class={isFullView 
     ? "fixed inset-0 w-screen h-screen bg-[#050505] p-8 flex flex-col overflow-hidden text-white" 
     : "grid grid-cols-12 gap-8 h-full"}
   style={isFullView ? `z-index: ${Z_INDEX_ADMIN.TIPTAP_FULLSCREEN};` : ""}
   in:fade
>
   <!-- MODULE CHÍNH -->
   <div class={isFullView
      ? "flex-1 bg-[#050505]/40 border border-white/5 rounded-none flex flex-col overflow-hidden shadow-2xl relative group"
      : "col-span-12 bg-white/[0.02] border border-white/5 rounded-none flex flex-col overflow-hidden shadow-2xl relative group"}>
      <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>
      {#if campaignLoading}
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm z-20 flex flex-col items-center justify-center gap-4" in:fade>
             <RefreshCw size={32} class="animate-spin text-cyan-400" />
             <span class="text-[10px] font-black tracking-widest text-cyan-400 animate-pulse">ĐANG TRUY XUẤT HẠ TẦNG...</span>
          </div>
       {/if}

      <!-- CONTROL HEADER -->
      <header class="bg-white/[0.05] p-6 border-b border-white/10 flex flex-col gap-6 relative z-10 backdrop-blur-md">
         <div class="flex justify-between items-center">
            <div class="flex items-center gap-5">
               <div class="p-3 bg-cyan-400/10 rounded-none border border-cyan-400/20">
                  <Megaphone size={20} class="text-cyan-400" />
               </div>
               <div class="flex items-center gap-4">
                  <h3 class="text-sm font-black tracking-widest text-white tracking-[0.1em] font-mono">Điều phối chiến dịch quảng cáo</h3>
                  {#if campaignView !== 'list'}
                     <ChevronRight size={16} class="text-slate-600" />
                     <span class="text-[9px] font-black text-cyan-400 tracking-widest bg-cyan-400/10 px-4 py-1.5 rounded-none border border-cyan-400/20 font-mono">
                        {campaignView === 'create_campaign' ? 'CREATE_DEPLOYMENT' : campaignView === 'ad_groups' ? 'AD_GROUPS_MATRIX' : 'AD_ASSETS'}
                     </span>
                  {/if}
               </div>
            </div>

            <div class="flex items-center gap-4">
               {#if campaignView === 'list'}
                  <button class="px-8 py-3.5 bg-cyan-600 text-white text-[11px] font-black tracking-widest hover:bg-cyan-500 transition-all active:scale-95 flex items-center gap-3 rounded-none shadow-xl group/btn" onclick={() => campaignView = 'create_campaign'}>
                     <Plus size={18} class="group-hover/btn:rotate-90 transition-transform" /> <span>Khởi tạo chiến dịch</span>
                  </button>
               {:else}
                  <button class="px-8 py-3.5 bg-white/5 border border-white/10 text-white text-[11px] font-black tracking-widest hover:bg-white/10 transition-all flex items-center gap-3 rounded-none" onclick={() => {
                     if (campaignView === 'create_campaign' || campaignView === 'ad_groups') campaignView = 'list';
                     else if (campaignView === 'ads') campaignView = 'ad_groups';
                  }}>
                     <X size={18} /> <span>Quay lại</span>
                  </button>
               {/if}
               <button class="w-12 h-12 flex items-center justify-center bg-black/40 border border-white/10 rounded-none hover:border-cyan-400/50 transition-all shadow-lg group/refresh" onclick={fetchCampaigns} disabled={campaignLoading} title="Tải lại dữ liệu">
                  <RefreshCw size={18} class="{campaignLoading ? 'animate-spin text-cyan-400' : 'text-slate-500 group-hover/refresh:text-cyan-400 transition-colors'}" />
               </button>
               <button class="w-12 h-12 flex items-center justify-center bg-black/40 border border-white/10 rounded-none hover:border-cyan-400/50 transition-all shadow-lg group/fullscreen" onclick={toggleFullView} title={isFullView ? "Thu nhỏ" : "Phóng to toàn màn hình"}>
                  {#if isFullView}
                     <Minimize2 size={18} class="text-slate-500 group-hover/fullscreen:text-cyan-400 transition-colors" />
                  {:else}
                     <Maximize2 size={18} class="text-slate-500 group-hover/fullscreen:text-cyan-400 transition-colors" />
                  {/if}
               </button>
            </div>
         </div>

         {#if campaignView === 'list'}
            <div class="flex flex-wrap gap-4 items-center bg-black/20 p-3 rounded-none border border-white/5" in:slide>
               <div class="flex-1 relative min-w-[240px]">
                  <Search size={14} class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input 
                     type="text" 
                     bind:value={searchQuery}
                     placeholder="Tìm kiếm theo tên hoặc ID chiến dịch..."
                     class="w-full bg-white/[0.03] border border-white/10 rounded-none py-2.5 pl-11 pr-4 text-[11px] text-white focus:border-cyan-400/50 outline-none transition-all font-mono"
                  />
               </div>
               
               <div class="flex items-center gap-2 bg-white/[0.03] p-1 rounded-none border border-white/10">
                  <div class="px-3 text-[9px] font-black text-slate-500 tracking-widest flex items-center gap-2">
                     <Filter size={12} /> Trạng thái:
                  </div>
                  {#each [
                     { id: 'ALL', label: 'Tất cả' },
                     { id: 'ENABLED', label: 'Đang chạy' },
                     { id: 'PAUSED', label: 'Tạm dừng' }
                  ] as opt}
                     <button 
                        class="px-4 py-1.5 rounded-none text-[9px] font-black transition-all {statusFilter === opt.id ? 'bg-cyan-500 text-black shadow-lg' : 'text-slate-500 hover:text-white'}"
                        onclick={() => statusFilter = opt.id}
                     >
                        {opt.label}
                     </button>
                  {/each}
               </div>

               <div class="text-[9px] font-mono text-slate-600 font-bold ml-auto">
                  HIỂN THỊ: {filteredCampaigns.length} / {campaigns.length} CHIẾN DỊCH
               </div>
            </div>
         {/if}
      </header>

      <!-- VIEWPORT -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-6 relative z-10">
         {#if campaignView === 'list'}
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
                               <div class="flex flex-col gap-1.5">
                                  <span class="text-white font-black text-sm tracking-tighter cursor-pointer group-hover/row:text-cyan-400 transition-colors" onclick={() => fetchAdGroups(c)}>{c.name}</span>
                                  <span class="text-[9px] text-slate-600 font-black tracking-widest">ID truy vết: {c.resource_name.split('/').pop()}</span>
                               </div>
                           </td>
                           <td class="px-8 py-6">
                               <span class="px-4 py-1.5 rounded-none text-[9px] font-black tracking-[0.1em] font-mono {c.status === 'ENABLED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-500 border border-white/5'}">
                                  {c.status === 'ENABLED' ? 'Đang chạy' : 'Đã tạm dừng'}
                               </span>
                           </td>
                           <td class="px-8 py-6 text-right text-white font-black text-sm">
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

            <!-- PAGINATION -->
            {#if totalPages > 1}
               <div class="mt-6 flex justify-between items-center bg-white/[0.03] p-4 rounded-none border border-white/5">
                  <div class="text-[10px] text-slate-500 font-mono font-black tracking-widest">
                     Trang {currentPage} / {totalPages}
                  </div>
                  <div class="flex items-center gap-2">
                     <button 
                        class="w-10 h-10 flex items-center justify-center rounded-none bg-white/5 border border-white/10 text-white disabled:opacity-30 hover:bg-cyan-500/10 transition-all"
                        disabled={currentPage === 1}
                        onclick={() => currentPage--}
                     >
                        <ChevronLeft size={16} />
                     </button>
                     {#each Array.from({length: Math.min(5, totalPages)}, (_, i) => {
                        if (totalPages <= 5) return i + 1;
                        if (currentPage <= 3) return i + 1;
                        if (currentPage >= totalPages - 2) return totalPages - 4 + i;
                        return currentPage - 2 + i;
                     }) as p}
                        <button 
                           class="w-10 h-10 flex items-center justify-center rounded-none border {currentPage === p ? 'bg-cyan-500 border-cyan-400 text-black shadow-lg font-black' : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'} transition-all text-[11px] font-mono"
                           onclick={() => currentPage = p}
                        >
                           {p}
                        </button>
                     {/each}
                     <button 
                        class="w-10 h-10 flex items-center justify-center rounded-none bg-white/5 border border-white/10 text-white disabled:opacity-30 hover:bg-cyan-500/10 transition-all"
                        disabled={currentPage === totalPages}
                        onclick={() => currentPage++}
                     >
                        <ChevronRight size={16} />
                     </button>
                  </div>
               </div>
            {/if}
         {:else if campaignView === 'create_campaign'}
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
         {:else if campaignView === 'ad_groups'}
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
                           oninput={(e) => {
                              // Local filter for ad groups if needed
                           }}
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
         {:else if campaignView === 'ads'}
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
                                    <button class="w-10 h-10 inline-flex items-center justify-center bg-white/5 border border-white/10 rounded-none text-slate-500 hover:text-emerald-400 transition-all">
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
         {/if}
      </div>
   </div>
</div>
