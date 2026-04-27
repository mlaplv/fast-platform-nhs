<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import ExternalLink from "lucide-svelte/icons/external-link";
  import TrendingUp from "lucide-svelte/icons/trending-up";
  import ShieldCheck from "lucide-svelte/icons/shield-check";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import type { MarketPriceIntel } from "$lib/types";
  import { formatCurrency } from "$lib/utils/format";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";

  const nanobot = useNanobot();

  let { product_id, market_data = $bindable(), last_sync } = $props<{
    product_id?: string;
    market_data?: MarketPriceIntel;
    last_sync?: string;
  }>();

  let isSyncing = $state(false);

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

<div class="flex flex-col gap-6 p-5 rounded-2xl bg-white/[0.02] border border-white/5 overflow-hidden">
  <div class="flex items-center justify-between">
    <div class="flex flex-col gap-1">
      <div class="flex items-center gap-2 text-[10px] font-black text-white/40 uppercase tracking-[0.3em]">
        <TrendingUp size={12} class="text-emerald-400/70" />
        Tình báo giá thị trường
      </div>
      {#if last_sync}
        <span class="text-[8px] font-mono text-white/20 uppercase">Lần cuối trinh sát: {new Date(last_sync).toLocaleString('vi-VN')}</span>
      {/if}
    </div>

    <button
      type="button"
      onclick={handleSync}
      disabled={isSyncing || !product_id}
      class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 hover:text-emerald-300 transition-all text-[9px] font-black uppercase tracking-wider disabled:opacity-30"
    >
      <RefreshCw size={10} class={isSyncing ? "animate-spin" : ""} />
      {isSyncing ? "ĐANG TRUY QUÉT..." : "TRINH SÁT NGAY"}
    </button>
  </div>

  {#if market_data}
    <div transition:fade class="flex flex-col gap-6">
      <!-- Analysis AI -->
      <div class="p-4 rounded-xl bg-emerald-500/[0.03] border border-emerald-500/10 relative overflow-hidden group">
        <div class="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
          <Sparkles size={40} class="text-emerald-400" />
        </div>
        <div class="flex items-center gap-2 mb-2">
          <ShieldCheck size={12} class="text-emerald-400" />
          <span class="text-[9px] font-black text-emerald-400 uppercase tracking-widest">Phân tích từ XOHI</span>
        </div>
        <p class="text-[11px] text-white/70 leading-relaxed italic">
          "{market_data.analysis}"
        </p>
      </div>

      <!-- Ads Section -->
      {#if market_data.ads && market_data.ads.length > 0}
        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-2 text-[8px] font-black text-amber-400/60 uppercase tracking-[0.2em]">
            🔥 Kết quả quảng cáo (Sponsored)
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            {#each market_data.ads as ad}
              <a
                href={ad.link}
                target="_blank"
                class="flex flex-col gap-2 p-3 rounded-xl bg-amber-500/[0.03] border border-amber-500/10 hover:border-amber-500/30 transition-all group"
              >
                <div class="flex items-center justify-between">
                  <span class="px-1.5 py-0.5 rounded bg-white/5 text-[8px] font-bold text-white/40 uppercase" style="color: {getPlatformColor(ad.platform)}">
                    {ad.platform}
                  </span>
                  <ExternalLink size={10} class="text-white/20 group-hover:text-amber-400 transition-colors" />
                </div>
                <div class="text-[10px] font-bold text-white/80 line-clamp-1">{ad.title}</div>
                <div class="text-[11px] font-mono text-amber-400">{ad.price ? formatCurrency(ad.price) : 'Liên hệ'}</div>
              </a>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Organic Section -->
      {#if market_data.organic_results && market_data.organic_results.length > 0}
        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-2 text-[8px] font-black text-white/20 uppercase tracking-[0.2em]">
            🌐 Top 10 tìm kiếm tự nhiên
          </div>
          <div class="flex flex-col gap-1.5">
            {#each market_data.organic_results as res, i}
              <a
                href={res.link}
                target="_blank"
                class="flex items-center gap-4 p-2.5 rounded-lg bg-white/[0.01] border border-white/[0.03] hover:bg-white/[0.03] hover:border-white/10 transition-all group"
              >
                <span class="text-[9px] font-mono text-white/10 w-4">{i + 1}</span>
                <div class="flex flex-col flex-1 min-w-0">
                  <div class="text-[10px] font-bold text-white/60 group-hover:text-white/90 transition-colors line-clamp-1">{res.title}</div>
                  <div class="text-[8px] font-mono text-white/25 uppercase">{res.platform}</div>
                </div>
                <div class="text-[10px] font-mono text-emerald-400/80">{res.price ? formatCurrency(res.price) : 'N/A'}</div>
                <ExternalLink size={10} class="text-white/10 group-hover:text-emerald-400 transition-colors" />
              </a>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="flex flex-col items-center justify-center py-10 gap-3 border border-dashed border-white/10 rounded-xl">
      <div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center">
        <TrendingUp size={16} class="text-white/20" />
      </div>
      <span class="text-[10px] text-white/20 uppercase font-black tracking-widest text-center">
        Chưa có dữ liệu trinh sát giá.<br/>Bấm nút phía trên để bắt đầu.
      </span>
    </div>
  {/if}
</div>

<style>
  @reference "tailwindcss";
</style>
