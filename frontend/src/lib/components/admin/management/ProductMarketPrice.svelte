<script lang="ts">
  import { fade } from "svelte/transition";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Zap from "@lucide/svelte/icons/zap";
  import Globe from "@lucide/svelte/icons/globe";
  import type { MarketPriceIntel } from "$lib/types";
  import { formatCurrency } from "$lib/utils/format";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import AdminModal from "../ui/AdminModal.svelte";

  const nanobot = useNanobot();

  let { product_id, market_data = $bindable(), last_sync } = $props<{
    product_id?: string;
    market_data?: MarketPriceIntel;
    last_sync?: string;
  }>();

  let isSyncing = $state(false);
  let showReport = $state(false);

  async function handleSync() {
    if (!product_id) return;
    isSyncing = true;
    try {
      const res = await apiClient.post<MarketPriceIntel>(`/api/v1/products/${product_id}/sync-market`);
      market_data = res;
      nanobot.showToast("Đã cập nhật tình báo giá mới nhất", "success");
    } catch (e) {
      nanobot.showToast("Đồng bộ giá thất bại", "error");
    } finally {
      isSyncing = false;
    }
  }

  function getPlatformColor(platform: string) {
    const p = platform.toLowerCase();
    if (p.includes('shopee')) return '#EE4D2D';
    if (p.includes('lazada')) return '#0F146D';
    if (p.includes('tiki')) return '#189EFF';
    return '#666';
  }
</script>

<div class="flex flex-col gap-5 p-6 rounded-2xl bg-black/40 border border-white/5 overflow-hidden relative group">
  <!-- Decorative background -->
  <div class="absolute -top-24 -right-24 w-48 h-48 bg-emerald-500/5 blur-[80px] rounded-full group-hover:bg-emerald-500/10 transition-colors"></div>

  <div class="flex items-center justify-between relative z-10">
    <div class="flex flex-col gap-1">
      <div class="flex items-center gap-2 text-[10px] font-black text-emerald-400 uppercase tracking-[0.3em]">
        <TrendingUp size={12} class="animate-pulse" />
        Deep Intel V2.2
      </div>
      {#if last_sync}
        <span class="text-[8px] font-mono text-white/20 uppercase">Last Sync: {new Date(last_sync).toLocaleString('vi-VN')}</span>
      {/if}
    </div>

    <button
      type="button"
      onclick={handleSync}
      disabled={isSyncing || !product_id}
      class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 hover:text-emerald-300 transition-all text-[9px] font-black uppercase tracking-wider disabled:opacity-30"
    >
      <RefreshCw size={10} class={isSyncing ? "animate-spin" : ""} />
      {isSyncing ? "Scanning..." : "Recon"}
    </button>
  </div>

  {#if market_data}
    <div transition:fade class="flex flex-col gap-4 relative z-10">
      <!-- Fast Metrics -->
      <div class="grid grid-cols-3 gap-2">
        <div class="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col gap-1">
          <span class="text-[8px] text-white/30 uppercase font-mono tracking-wider">Avg Price</span>
          <span class="text-[11px] font-black text-white/80">{market_data.avg_market_price ? formatCurrency(market_data.avg_market_price) : 'N/A'}</span>
        </div>
        <div class="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col gap-1">
          <span class="text-[8px] text-white/30 uppercase font-mono tracking-wider">Competitors</span>
          <span class="text-[11px] font-black text-white/80">{market_data.competitor_count || 0}</span>
        </div>
        <div class="p-3 rounded-xl bg-emerald-500/[0.03] border border-emerald-500/10 flex flex-col gap-1">
          <span class="text-[8px] text-emerald-400/50 uppercase font-mono tracking-wider">Ads Count</span>
          <span class="text-[11px] font-black text-emerald-400">{market_data.ads?.length || 0}</span>
        </div>
      </div>

      <!-- Quick Analysis -->
      <div class="p-4 rounded-xl bg-white/[0.01] border border-dashed border-white/10">
        <p class="text-[10px] text-white/50 leading-relaxed line-clamp-2">
          {market_data.analysis_overview || market_data.analysis || 'Chưa có phân tích dữ liệu...'}
        </p>
      </div>

      <button 
        onclick={() => showReport = true}
        class="w-full py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all text-[9px] font-black uppercase tracking-[0.2em] text-white/60"
      >
        Xem báo cáo chi tiết
      </button>
    </div>
  {:else}
    <div class="flex flex-col items-center justify-center py-8 gap-3 border border-dashed border-white/10 rounded-2xl bg-white/[0.01]">
      <div class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
        <TrendingUp size={18} class="text-white/10" />
      </div>
      <span class="text-[9px] text-white/20 uppercase font-black tracking-[0.2em] text-center">
        Dữ liệu trinh sát trống.<br/>Khởi động Recon để thu thập.
      </span>
    </div>
  {/if}
</div>

<!-- Intel Report Modal -->
<AdminModal
  isOpen={showReport}
  onClose={() => showReport = false}
  title="Báo cáo trinh sát thị trường"
  subtitle="Deep Intel V2.2 | XOHI Neural Engine"
  variant="emerald"
  headerIcon={TrendingUp}
  maxWidth="max-w-6xl"
>
  {#if market_data}
    <div class="flex flex-col lg:flex-row gap-8 min-h-[600px]">
      <!-- Left Panel: Strategic Analysis & Metrics -->
      <div class="w-full lg:w-[400px] flex flex-col gap-6 shrink-0">
        <!-- Main Intelligence Box -->
        <div class="p-6 rounded-3xl bg-emerald-500/[0.03] border border-emerald-500/10 relative overflow-hidden group">
          <div class="absolute -top-12 -right-12 w-32 h-32 bg-emerald-500/5 blur-3xl rounded-full group-hover:bg-emerald-500/10 transition-all"></div>
          
          <div class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Sparkles size={18} class="text-emerald-400" />
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-emerald-400 uppercase tracking-[0.2em]">Phân tích từ XOHI</span>
              <span class="text-[8px] font-mono text-white/20 uppercase tracking-widest">Neural Insight Engine</span>
            </div>
          </div>

          <div class="flex flex-col gap-6">
            <div class="flex flex-col gap-2">
               <h4 class="text-[9px] font-black text-white/40 uppercase tracking-widest flex items-center gap-2">
                 <div class="w-1 h-1 rounded-full bg-emerald-500"></div>
                 Tổng quan
               </h4>
               <p class="text-[12px] text-white/70 leading-relaxed italic border-l-2 border-emerald-500/20 pl-4 py-1">
                 "{market_data.analysis_overview || 'AI đang tổng hợp dữ liệu...'}"
               </p>
            </div>

            <div class="flex flex-col gap-2">
               <h4 class="text-[9px] font-black text-amber-400/60 uppercase tracking-widest flex items-center gap-2">
                 <div class="w-1 h-1 rounded-full bg-amber-500"></div>
                 Phản biện sắc bén
               </h4>
               <p class="text-[12px] text-white/70 leading-relaxed italic border-l-2 border-amber-500/20 pl-4 py-1">
                 "{market_data.critical_analysis || 'Đang bóc tách đối thủ...'}"
               </p>
            </div>

            <div class="flex flex-col gap-2">
               <h4 class="text-[9px] font-black text-cyan-400/60 uppercase tracking-widest flex items-center gap-2">
                 <div class="w-1 h-1 rounded-full bg-cyan-500"></div>
                 Chiến lược tối ưu
               </h4>
               <p class="text-[12px] text-white/70 leading-relaxed italic border-l-2 border-cyan-500/20 pl-4 py-1">
                 "{market_data.optimization_strategy || 'Đang tính toán Sweet Spot...'}"
               </p>
            </div>
            
            <div class="flex flex-col gap-2">
               <h4 class="text-[9px] font-black text-indigo-400/60 uppercase tracking-widest flex items-center gap-2">
                 <div class="w-1 h-1 rounded-full bg-indigo-500"></div>
                 Góc nhìn Viral
               </h4>
               <p class="text-[12px] text-white/70 leading-relaxed italic border-l-2 border-indigo-500/20 pl-4 py-1">
                 "{market_data.viral_hook || 'Đang tìm kiếm Market Gap...'}"
               </p>
            </div>
          </div>
        </div>

        <!-- Quick Stats Cards -->
        <div class="grid grid-cols-2 gap-4">
          <div class="p-5 rounded-2xl bg-white/[0.02] border border-white/5 flex flex-col gap-1 group hover:border-emerald-500/20 transition-all">
            <span class="text-[9px] font-black text-white/20 uppercase tracking-widest">Ads Count</span>
            <span class="text-2xl font-black text-emerald-400 group-hover:scale-110 transition-transform origin-left">{market_data.ads?.length || 0}</span>
          </div>
          <div class="p-5 rounded-2xl bg-white/[0.02] border border-white/5 flex flex-col gap-1 group hover:border-emerald-500/20 transition-all">
            <span class="text-[9px] font-black text-white/20 uppercase tracking-widest">Organic Results</span>
            <span class="text-2xl font-black text-white/80 group-hover:scale-110 transition-transform origin-left">{market_data.organic_results?.length || 0}</span>
          </div>
        </div>

        <!-- Price Range Visualizer -->
        <div class="p-5 rounded-2xl bg-white/[0.01] border border-dashed border-white/10 flex flex-col gap-4">
           <div class="flex items-center justify-between">
              <span class="text-[9px] font-black text-white/30 uppercase tracking-widest">Price Spectrum</span>
              <span class="text-[10px] font-mono text-emerald-400/60">AVG: {market_data.avg_market_price ? formatCurrency(market_data.avg_market_price) : 'N/A'}</span>
           </div>
           <div class="h-1.5 w-full bg-white/5 rounded-full relative overflow-hidden">
              <div class="absolute inset-y-0 left-0 bg-emerald-500/40 w-1/3"></div>
              <div class="absolute inset-y-0 left-1/3 bg-emerald-400 w-1/4"></div>
           </div>
           <div class="flex justify-between text-[8px] font-mono text-white/20 uppercase">
              <span>Min: {market_data.min_market_price ? formatCurrency(market_data.min_market_price) : 'N/A'}</span>
              <span>{market_data.competitor_count} Competitors</span>
           </div>
        </div>
      </div>

      <!-- Right Panel: Live Feed (Ads & Organic) -->
      <div class="flex-1 flex flex-col gap-8">
        <!-- Ads Section -->
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between px-2">
            <div class="flex items-center gap-3">
               <div class="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                 <Zap size={14} class="text-amber-400 animate-pulse" />
               </div>
               <div class="flex flex-col">
                 <span class="text-[10px] font-black text-amber-400 uppercase tracking-[0.2em]">Quảng cáo (Sponsored/Ads)</span>
                 <span class="text-[8px] font-mono text-white/20 uppercase tracking-wider">High conversion landing pages</span>
               </div>
            </div>
            <div class="text-[8px] font-mono text-amber-500/40 px-2 py-0.5 rounded border border-amber-500/20 uppercase">Live Trace</div>
          </div>
          
          <div class="grid grid-cols-1 gap-2 max-h-[250px] overflow-y-auto custom-scrollbar pr-2">
            {#if market_data.ads && market_data.ads.length > 0}
              {#each market_data.ads as ad}
                <a
                  href={ad.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center gap-4 p-4 rounded-2xl bg-amber-500/[0.02] border border-amber-500/10 hover:border-amber-500/30 hover:bg-amber-500/[0.05] transition-all group"
                >
                  <div class="flex flex-col flex-1 min-w-0 gap-1">
                    <div class="flex items-center gap-2">
                      <span class="text-[8px] font-black px-1.5 py-0.5 rounded bg-white/5 text-white/60 uppercase tracking-tighter" style="color: {getPlatformColor(ad.platform)}">
                        {ad.platform}
                      </span>
                      <div class="text-[11px] font-bold text-white/80 line-clamp-1 group-hover:text-white transition-colors">{ad.title}</div>
                    </div>
                  </div>
                  <div class="text-[11px] font-mono font-black text-amber-400 whitespace-nowrap">{ad.price ? formatCurrency(ad.price) : 'Liên hệ'}</div>
                  <div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-amber-500/20 transition-colors">
                    <ExternalLink size={12} class="text-white/20 group-hover:text-amber-400 transition-colors" />
                  </div>
                </a>
              {/each}
            {:else}
               <div class="py-12 flex flex-col items-center justify-center border border-dashed border-white/5 rounded-2xl bg-white/[0.01] gap-2">
                  <Zap size={24} class="text-white/5" />
                  <span class="text-[9px] text-white/20 uppercase font-mono tracking-widest italic">No Sponsored Content Detected</span>
               </div>
            {/if}
          </div>
        </div>

        <!-- Organic Section -->
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between px-2">
            <div class="flex items-center gap-3">
               <div class="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                 <Globe size={14} class="text-emerald-400" />
               </div>
               <div class="flex flex-col">
                 <span class="text-[10px] font-black text-emerald-400 uppercase tracking-[0.2em]">Top 10 Kết quả tự nhiên</span>
                 <span class="text-[8px] font-mono text-white/20 uppercase tracking-wider">Natural search intelligence</span>
               </div>
            </div>
            <div class="text-[8px] font-mono text-emerald-500/40 px-2 py-0.5 rounded border border-emerald-500/20 uppercase">Deep Recon</div>
          </div>

          <div class="flex flex-col gap-2 max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
            {#if market_data.organic_results && market_data.organic_results.length > 0}
              {#each market_data.organic_results as res, i}
                <a
                  href={res.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center gap-4 p-3 rounded-xl bg-white/[0.01] border border-white/[0.03] hover:bg-white/[0.03] hover:border-emerald-500/20 transition-all group"
                >
                  <div class="w-6 h-6 rounded bg-white/5 flex items-center justify-center text-[9px] font-mono text-white/20 group-hover:text-emerald-400 transition-colors">
                    {i + 1}
                  </div>
                  <div class="flex flex-col flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                       <div class="text-[11px] font-bold text-white/60 group-hover:text-white/90 transition-colors line-clamp-1">{res.title}</div>
                       <div class="flex items-center gap-1 px-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-[7px] font-black text-emerald-400 uppercase tracking-tighter shrink-0">
                          <ShieldCheck size={8} />
                          Verified
                       </div>
                    </div>
                    <div class="flex items-center gap-2 mt-0.5">
                       <div class="w-1 h-1 rounded-full bg-emerald-500/40"></div>
                       <span class="text-[8px] font-mono text-white/25 uppercase tracking-wider">{res.platform}</span>
                    </div>
                  </div>
                  <div class="text-[11px] font-mono font-bold text-emerald-400 group-hover:scale-105 transition-transform origin-right">{res.price ? formatCurrency(res.price) : 'N/A'}</div>
                  <ExternalLink size={12} class="text-white/10 group-hover:text-emerald-400 transition-colors" />
                </a>
              {/each}
            {:else}
              <div class="py-20 flex flex-col items-center justify-center border border-dashed border-white/5 rounded-2xl bg-white/[0.01] gap-2">
                  <Globe size={32} class="text-white/5 animate-spin-slow" />
                  <span class="text-[9px] text-white/20 uppercase font-mono tracking-widest italic">Scanning Internet for Organic Results...</span>
               </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  {/if}

  {#snippet footer()}
    <div class="flex items-center justify-between w-full">
       <div class="flex items-center gap-4">
          <div class="flex -space-x-2">
             {#each Array(3) as _}
                <div class="w-6 h-6 rounded-full border-2 border-black bg-white/10 flex items-center justify-center">
                   <ShieldCheck size={10} class="text-emerald-500" />
                </div>
             {/each}
          </div>
          <span class="text-[8px] font-mono text-white/30 uppercase tracking-widest">Verified by XOHI Neural Engine</span>
       </div>
       <button 
         onclick={() => showReport = false}
         class="px-10 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] text-white/60 hover:text-white transition-all active:scale-95 flex items-center gap-3 group"
       >
         Đóng báo cáo
         <X size={14} class="text-white/20 group-hover:text-red-400 transition-colors" />
       </button>
    </div>
  {/snippet}
</AdminModal>

<style>
  @reference "tailwindcss";
</style>
