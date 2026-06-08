<script lang="ts">
  import { fade } from 'svelte/transition';
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { onDestroy } from 'svelte';

  import GoogleSearchAdMockup from './GoogleSearchAdMockup.svelte';
  import AdStrengthWidget from './AdStrengthWidget.svelte';
  import CompetitorAnalysisPanel from './CompetitorAnalysisPanel.svelte';
  import AdFormSection from './AdFormSection.svelte';
  import CampaignTreeTable from './CampaignTreeTable.svelte';
  import CampaignFormSection from './CampaignFormSection.svelte';
  import AdGroupsListSection from './AdGroupsListSection.svelte';
  import AdsListSection from './AdsListSection.svelte';
  import CampaignHeader from './CampaignHeader.svelte';

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
    activeTab = $bindable(),
    
    // Ads creation/edit properties
    isEditingAd = $bindable(),
    selectedAd = $bindable(),
    fAd = $bindable(),
    competitorUrl = $bindable(),
    aiResult,
    analyzeCompetitor,
    importKeyword,
    addNegativeKeyword,
    addAdGroupKeywords,
    removeAdGroupKeyword,
    negativeKeywords = $bindable([]),
    competitorAnalysis,
    competitorAnalyzing,
    selectAdForEdit,
    submitAd,
    aiSuggestRSA,
    adSubmitting = false,
    aiGenerating = false,
    adGroupKeywords = $bindable([]),

    // Tree View Cache States
    expandedCampaigns = {},
    expandedAdGroups = {},
    campaignAdGroups = {},
    adGroupAds = {},
    loadingCampaigns = {},
    loadingAdGroups = {},
    toggleCampaign,
    toggleAdGroup
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
  let expandedAds = $state<Record<string, boolean>>({});
  function toggleAd(resName: string) {
    expandedAds[resName] = !expandedAds[resName];
  }

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

       <CampaignHeader
          bind:campaignView={campaignView}
          bind:selectedCampaign={selectedCampaign}
          bind:selectedAd={selectedAd}
          bind:isEditingAd={isEditingAd}
          bind:fAd={fAd}
          bind:competitorUrl={competitorUrl}
          campaignLoading={campaignLoading}
          fetchCampaigns={fetchCampaigns}
          toggleFullView={toggleFullView}
          isFullView={isFullView}
          bind:searchQuery={searchQuery}
          bind:statusFilter={statusFilter}
          filteredCampaigns={filteredCampaigns}
          campaigns={campaigns}
       />

       <!-- VIEWPORT -->
       <div class="flex-1 overflow-y-auto custom-scrollbar p-6 relative z-10">
         {#if campaignView === 'list'}
            <CampaignTreeTable
               paginatedCampaigns={paginatedCampaigns}
               campaigns={campaigns}
               bind:expandedCampaigns={expandedCampaigns}
               bind:expandedAdGroups={expandedAdGroups}
               bind:campaignAdGroups={campaignAdGroups}
               bind:adGroupAds={adGroupAds}
               bind:loadingCampaigns={loadingCampaigns}
               bind:loadingAdGroups={loadingAdGroups}
               bind:expandedAds={expandedAds}
               bind:selectedCampaign={selectedCampaign}
               bind:selectedAdGroup={selectedAdGroup}
               bind:fAd={fAd}
               bind:isEditingAd={isEditingAd}
               bind:campaignView={campaignView}
               bind:adGroupKeywords={adGroupKeywords}
               toggleCampaign={toggleCampaign}
               toggleAdGroup={toggleAdGroup}
               toggleAd={toggleAd}
               fetchAdGroups={fetchAdGroups}
               updateCampaignStatus={updateCampaignStatus}
               selectAdForEdit={selectAdForEdit}
               fmt={fmt}
               bind:activeTab={activeTab}
            />

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
            <CampaignFormSection
               bind:fCampaign={fCampaign}
               aiSuggest={aiSuggest}
               aiLoading={aiLoading}
               submitCampaign={submitCampaign}
               campaignSubmitting={campaignSubmitting}
            />
         {:else if campaignView === 'ad_groups'}
            <AdGroupsListSection
               selectedCampaign={selectedCampaign}
               adGroupLoading={adGroupLoading}
               adGroups={adGroups}
               fetchAds={fetchAds}
               fmt={fmt}
            />
         {:else if campaignView === 'ads'}
            <AdsListSection
               selectedAdGroup={selectedAdGroup}
               adsLoading={adsLoading}
               ads={ads}
               selectAdForEdit={selectAdForEdit}
               selectedCampaign={selectedCampaign}
            />
         {:else if campaignView === 'create_ad'}
            <div class="grid grid-cols-12 gap-8 p-4 lg:p-6" in:fade>
               <!-- LEFT PANEL: RSA FORM (7/8 Cols) -->
               <div class="col-span-12 lg:col-span-7 xl:col-span-8 space-y-6 lg:space-y-8">
                  <AdFormSection
                     bind:fAd={fAd}
                     aiGenerating={aiGenerating}
                     aiSuggestRSA={aiSuggestRSA}
                     adSubmitting={adSubmitting}
                     submitAd={submitAd}
                     onBack={() => campaignView = 'ads'}
                     isEditingAd={isEditingAd}
                  />
               </div>

               <!-- RIGHT PANEL: PREVIEW, STRENGTH & COMPETITOR (5/4 Cols) -->
               <div class="col-span-12 lg:col-span-5 xl:col-span-4 space-y-6 lg:space-y-8">
                  <!-- GOOGLE SEARCH AD MOCKUP -->
                  <GoogleSearchAdMockup
                     final_url={fAd.final_url}
                     display_path1={fAd.display_path1}
                     display_path2={fAd.display_path2}
                     headlines={fAd.headlines}
                     descriptions={fAd.descriptions}
                  />

                  <!-- AD STRENGTH WIDGET -->
                  <AdStrengthWidget
                     headlines={fAd.headlines}
                     descriptions={fAd.descriptions}
                     bind:adGroupKeywords={adGroupKeywords}
                  />

                  <!-- PURPLE COMPETITOR RESEARCH PANEL -->
                  <CompetitorAnalysisPanel
                     bind:fAd={fAd}
                     bind:competitorUrl={competitorUrl}
                     competitorAnalyzing={competitorAnalyzing}
                     competitorAnalysis={competitorAnalysis}
                     analyzeCompetitor={analyzeCompetitor}
                     importKeyword={importKeyword}
                     addNegativeKeyword={addNegativeKeyword}
                     addAdGroupKeywords={addAdGroupKeywords}
                     removeAdGroupKeyword={removeAdGroupKeyword}
                     bind:adGroupKeywords={adGroupKeywords}
                     bind:negativeKeywords={negativeKeywords}
                     selectedCampaign={selectedCampaign}
                     selectedAdGroup={selectedAdGroup}
                  />
               </div>
             </div>
          {/if}
      </div>
   </div>
</div>
