<script lang="ts">
  import { slide } from 'svelte/transition';
  import Plus from "@lucide/svelte/icons/plus";
  import X from "@lucide/svelte/icons/x";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Megaphone from "@lucide/svelte/icons/megaphone";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Search from "@lucide/svelte/icons/search";
  import Filter from "@lucide/svelte/icons/filter";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";

  let {
    campaignView = $bindable(),
    selectedCampaign = $bindable(),
    selectedAd = $bindable(),
    isEditingAd = $bindable(),
    fAd = $bindable(),
    competitorUrl = $bindable(),
    campaignLoading,
    fetchCampaigns,
    toggleFullView,
    isFullView,
    searchQuery = $bindable(),
    statusFilter = $bindable(),
    filteredCampaigns = [],
    campaigns = []
  } = $props();
</script>

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
                  {campaignView === 'create_campaign' ? 'CREATE_DEPLOYMENT' : campaignView === 'ad_groups' ? 'AD_GROUPS_MATRIX' : campaignView === 'ads' ? 'AD_ASSETS' : 'AD_ASSET_CREATION'}
               </span>
            {/if}
         </div>
      </div>

      <div class="flex items-center gap-4">
         {#if campaignView === 'list'}
            <button class="px-8 py-3.5 bg-cyan-600 text-white text-[11px] font-black tracking-widest hover:bg-cyan-500 transition-all active:scale-95 flex items-center gap-3 rounded-none shadow-xl group/btn" onclick={() => campaignView = 'create_campaign'}>
               <Plus size={18} class="group-hover/btn:rotate-90 transition-transform" /> <span>Khởi tạo chiến dịch</span>
            </button>
         {:else if campaignView === 'ads'}
            <button class="px-8 py-3.5 bg-emerald-600 text-white text-[11px] font-black tracking-widest hover:bg-emerald-500 transition-all active:scale-95 flex items-center gap-3 rounded-none shadow-xl group/btn" onclick={() => {
               isEditingAd = false;
               selectedAd = null;
               fAd.final_url = selectedCampaign?.final_url || '';
               fAd.display_path1 = '';
               fAd.display_path2 = '';
               fAd.status = 'PAUSED';
               fAd.headlines = Array(15).fill('');
               fAd.descriptions = Array(4).fill('');
               competitorUrl = fAd.final_url;
               campaignView = 'create_ad';
            }}>
               <Plus size={18} class="group-hover/btn:rotate-90 transition-transform" /> <span>Tạo quảng cáo</span>
            </button>
            <button class="px-8 py-3.5 bg-white/5 border border-white/10 text-white text-[11px] font-black tracking-widest hover:bg-white/10 transition-all flex items-center gap-3 rounded-none" onclick={() => {
               campaignView = 'ad_groups';
            }}>
               <X size={18} /> <span>Quay lại</span>
            </button>
         {:else}
            <button class="px-8 py-3.5 bg-white/5 border border-white/10 text-white text-[11px] font-black tracking-widest hover:bg-white/10 transition-all flex items-center gap-3 rounded-none" onclick={() => {
               if (campaignView === 'create_campaign' || campaignView === 'ad_groups') campaignView = 'list';
               else if (campaignView === 'create_ad') campaignView = 'ads';
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
