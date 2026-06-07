<script lang="ts">
  import Package from "@lucide/svelte/icons/package";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import CheckSquare from "@lucide/svelte/icons/check-square";
  import Square from "@lucide/svelte/icons/square";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Play from "@lucide/svelte/icons/play";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import X from "@lucide/svelte/icons/x";
  import StarIcon from "@lucide/svelte/icons/star";
  import { fade } from "svelte/transition";
  import { portal } from "$lib/core/actions/portal";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { formatCurrency } from "$lib/utils/format";
  import type { Product } from "$lib/types";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { getAuthToken } from "$lib/state/permissions.svelte";

  function isVideoUrl(url: string): boolean {
    if (!url) return false;
    const clean = url.split('?')[0].toLowerCase();
    return /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(clean);
  }

  let {
    products,
    selectedIds,
    statusMap,
    onToggleSelect,
    onToggleSelectAll,
    onEdit,
    onDelete,
    onSyncMarket,
    onOpenReviewLab,
  } = $props<{
    products: Product[];
    selectedIds: Set<string>;
    statusMap: Record<string, { label: string; color: string }>;
    onToggleSelect: (id: string) => void;
    onToggleSelectAll: () => void;
    onEdit: (p: Product) => void;
    onDelete: (id: string) => void;
    onSyncMarket: (id: string) => Promise<void>;
    onOpenReviewLab: (product: { id: string; name: string }) => void;
  }>();

  let syncingStates = $state<Record<string, boolean>>({});
  let fullViewMarketData = $state<Product["market_data"] | null>(null);
  let isHoveringPopover = $state(false);
  let activeIntelId = $state<string | null>(null);
  let activeIntelPos = $state({ x: 0, y: 0, height: 0 });
  let popoverPlacement = $state<'top' | 'bottom'>('top');
  let activeIntelData = $state<any>(null);

  async function handleSync(id: string) {
    if (syncingStates[id]) return;
    syncingStates[id] = true;
    try {
      await onSyncMarket(id);
    } catch (err) {
      // Error is handled in onSyncMarket toast, but we need to stop spinning
    } finally {
      syncingStates[id] = false;
    }
  }

  function closeMarketReport() {
    fullViewMarketData = null;
    activeIntelId = null;
    activeIntelData = null;
    isHoveringPopover = false;
  }

  const isAllSelected = $derived(products.length > 0 && products.every(p => selectedIds.has(p.id)));

  $effect(() => {
    if (fullViewMarketData) {
      activeIntelId = null;
      isHoveringPopover = false;
    }
  });

  $effect(() => {
    const action = nanobot.commandAction;
    if (action?.entity === "product") {
      if (action.verb === "edit" && action.args) {
        const target = products.find(
          (p) =>
            p.id === action.args ||
            p.name.toLowerCase().includes(action.args.toLowerCase()) ||
            p.sku.toLowerCase() === action.args.toLowerCase(),
        );
        if (target && nanobot.consumeCommand("edit", "product")) {
          onEdit(target);
        }
      }
      if (action.verb === "delete" && action.args) {
        const target = products.find(
          (p) =>
            p.id === action.args ||
            p.name.toLowerCase().includes(action.args.toLowerCase()) ||
            p.sku.toLowerCase() === action.args.toLowerCase(),
        );
        if (target && nanobot.consumeCommand("delete", "product")) {
          onDelete(target.id);
        }
      }
    }
  });
</script>

<!-- Responsive Table Header (Hidden on Mobile) -->
<div class="hidden md:grid grid-cols-[40px_minmax(250px,2fr)_1fr_1fr_1fr_1fr_100px] gap-4 px-4 py-4 sticky top-0 bg-black/80 border-b border-[#FFB800]/20 tracking-widest text-[9px] font-extrabold font-mono text-[#FFB800] shadow-2xl"
     style="z-index: {Z_INDEX_ADMIN.STICKY_HEADER}; backdrop-filter: blur(16px);">
  <div class="text-center flex justify-center items-center">
    <button
      onclick={(e) => { e.stopPropagation(); onToggleSelectAll(); }}
      class="text-gray-600 hover:text-[#FFB800] transition-colors"
      title={isAllSelected ? "Bỏ chọn tất cả" : "Chọn tất cả trang này"}
    >
      {#if isAllSelected}<CheckSquare size={16} />{:else}<Square size={16} />{/if}
    </button>
  </div>
  <div>Product Details</div>
  <div>Registry ID</div>
  <div>Valuation</div>
  <div>Quantity</div>
  <div>System Status</div>
  <div class="text-right">Operations</div>
</div>

<div class="flex flex-col flex-1 pb-10">
  <div class="flex flex-col xs:gap-2 gap-4 divide-y md:divide-y-[1px] divide-white/[0.02] md:divide-white/[0.05] md:gap-0 px-2 sm:px-4 md:px-0">
    {#each products as product (product.id)}
      {@const status = statusMap[product.status] || {
        label: product.status,
        color: "#666",
      }}
      <div
        class="group relative flex flex-col md:grid md:grid-cols-[40px_minmax(250px,2fr)_1fr_1fr_1fr_1fr_100px] md:gap-4 md:items-center bg-[#0a0a0a] md:bg-transparent border border-white/5 md:border-none p-3 sm:p-4 rounded-xl md:rounded-none hover:bg-white/[0.03] transition-colors duration-300"
      >
        <div class="absolute top-2 left-2 md:relative md:top-auto md:left-auto md:flex md:justify-center"
             style="z-index: var(--z-surface);">
          <button
            onclick={(e: MouseEvent) => { e.stopPropagation(); onToggleSelect(product.id); }}
            class="text-gray-600 hover:text-[#FFB800] transition-colors"
          >
            {#if selectedIds.has(product.id)}<CheckSquare size={16} />{:else}<Square size={16} />{/if}
          </button>
        </div>

        <div class="flex items-start md:items-center gap-4 md:pl-0 pl-6 w-full">
          <div
            class="w-14 h-14 md:w-12 md:h-12 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center shrink-0 overflow-hidden relative group-hover:border-[#FFB800]/30 transition-all duration-300 shadow-[inset_0_0_15px_rgba(0,0,0,0.5)]"
          >
            {#if product.images && product.images.length > 0 && product.images[0].includes('/')}
              {#if isVideoUrl(product.images[0])}
                <video
                  src={product.images[0]}
                  class="w-full h-full object-cover opacity-80 group-hover:opacity-100 pointer-events-none"
                  muted
                  playsinline
                  preload="metadata"
                />
                <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div class="w-6 h-6 rounded-full bg-black/70 flex items-center justify-center">
                    <Play size={10} class="text-white ml-0.5" />
                  </div>
                </div>
              {:else}
                <img 
                  src={product.images[0]} 
                  alt={product.name}
                  class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 opacity-80 group-hover:opacity-100"
                />
              {/if}
            {:else}
              <div class="w-full h-full bg-gradient-to-br from-[#FFB800]/10 to-transparent flex items-center justify-center">
                <Package size={20} class="text-[#FFB800]/40" />
              </div>
            {/if}
            <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none"></div>
          </div>
          <div class="min-w-0 flex flex-col justify-center flex-1">
            <div class="text-[14px] md:text-[13px] font-bold text-gray-100 truncate group-hover:text-[#FFB800] transition-colors tracking-wide flex items-center gap-2">
              {product.name}
              {#if product.isAiFeatured || product.is_ai_featured}
                <Sparkles size={12} class="text-[#00FFFF] animate-pulse shrink-0" />
              {/if}
            </div>
            <div class="text-[10px] font-mono text-gray-500 mt-1 tracking-[0.2em] flex items-center flex-wrap gap-2">
              <span class="px-2 py-0.5 rounded-lg bg-white/5 border border-white/5 text-[8px] text-[#FFB800]/70">{product.category || "General_Node"}</span>
              
              {#if product.metadata?.analysis_metrics}
                {@const metrics = product.metadata.analysis_metrics}
                {#if metrics.unique_score !== undefined}
                  <span class="px-1.5 py-0.5 rounded-md bg-orange-500/10 border border-orange-500/30 text-[8px] text-orange-400 font-black shadow-[0_0_10px_rgba(249,115,22,0.1)]" title="Tiêu chí vàng: Copyright Certificate">
                    © {Math.round(metrics.unique_score * 100)}%
                  </span>
                {/if}
                {#if metrics.seo_score !== undefined}
                  <span class="px-1.5 py-0.5 rounded-md bg-blue-500/10 border border-blue-500/30 text-[8px] text-blue-400 font-black shadow-[0_0_10px_rgba(59,130,246,0.1)]" title="Tiêu chí vàng: SEO Certificate">
                    📊 {metrics.seo_score}
                  </span>
                {/if}
                {#if metrics.ai_ready_score !== undefined}
                  <span class="px-1.5 py-0.5 rounded-md bg-purple-500/10 border border-purple-500/30 text-[8px] text-purple-400 font-black shadow-[0_0_10px_rgba(168,85,247,0.1)]" title="Tiêu chí vàng: AI Mod Ready">
                    🤖 {metrics.ai_ready_score}
                  </span>
                {/if}
              {/if}

              <span class="px-1.5 py-0.5 rounded-md bg-white/5 border border-white/10 text-[8px] text-gray-400 font-black" title="Lượt xem (Views)">
                👁️ {product.views || 0}
              </span>
              <span class="px-1.5 py-0.5 rounded-md bg-white/5 border border-white/10 text-[8px] text-gray-400 font-black" title="Đánh giá (Reviews)">
                ⭐ {product.review_count || 0}
              </span>
              <span class="px-1.5 py-0.5 rounded-md bg-white/5 border border-white/10 text-[8px] text-gray-400 font-black" title="Lượt mua (Orders)">
                🛒 {product.order_count || product.orderCount || 0}
              </span>

              <span class="md:hidden text-gray-800">/</span>
              <span class="md:hidden text-gray-600 font-bold">{product.sku}</span>
            </div>
          </div>
        </div>

        <div class="hidden md:block text-[10px] font-mono text-gray-500 tracking-wider group-hover:text-gray-300 transition-colors truncate">
          {product.sku}
        </div>

        <div class="pl-[72px] md:pl-0 mt-3 md:mt-0 flex md:flex-none items-center justify-between md:justify-start">
          <span class="md:hidden text-[9px] font-mono text-gray-500 tracking-widest ">Price</span>
          <div class="flex flex-col items-start gap-1">
            <div class="flex items-center gap-2">
              {#if product.discount_price || product.discountPrice}
                <span class="text-[11px] font-bold font-mono text-[#FFB800] group-hover:text-white transition-colors tracking-wider">
                  {formatCurrency(product.discount_price || product.discountPrice || 0)}
                </span>
                <span class="text-[9px] font-mono text-gray-500 line-through opacity-60">
                  {formatCurrency(product.price)}
                </span>
              {:else}
                <span class="text-xs font-bold font-mono text-[#00FFFF] group-hover:text-white transition-colors tracking-wider">
                  {formatCurrency(product.price)}
                </span>
              {/if}
              
              <button
                onclick={(e) => { e.stopPropagation(); handleSync(product.id); }}
                disabled={syncingStates[product.id]}
                class="p-1 rounded-md bg-white/5 border border-white/5 hover:border-emerald-500/30 hover:text-emerald-400 transition-all group/sync {syncingStates[product.id] ? 'opacity-50' : ''}"
                title="Trinh sát giá thị trường"
              >
                <RefreshCw size={10} class={syncingStates[product.id] ? "animate-spin" : "group-hover/sync:rotate-180 transition-transform duration-500"} />
              </button>
            </div>

            {#if (product.market_data && product.market_data.analysis_overview) || (product.marketData && product.marketData.analysis_overview)}
              {@const m = product.market_data || product.marketData}
              {@const allResults = [...(m.ads || []), ...(m.organic_results || [])]}
              {@const prices = allResults.map(r => r.price).filter(p => p && p > 0) as number[]}
              {@const bestPrice = prices.length > 0 ? Math.min(...prices) : null}
              
              <div class="group/intel relative"
                   onmouseenter={(e) => {
                     activeIntelId = product.id;
                     activeIntelData = product.market_data || product.marketData;
                     const rect = e.currentTarget.getBoundingClientRect();
                     activeIntelPos = { x: rect.left, y: rect.top, height: rect.height };
                     popoverPlacement = rect.top > (window.innerHeight / 2) ? 'top' : 'bottom';
                   }}
                   onmouseleave={() => {
                     setTimeout(() => {
                       if (!isHoveringPopover) {
                         activeIntelId = null;
                         activeIntelData = null;
                       }
                     }, 100);
                   }}>
                <div class="flex flex-col gap-1 px-2 py-1 rounded-lg bg-emerald-500/5 border border-emerald-500/20 hover:border-emerald-500/50 transition-all cursor-help">
                  <div class="flex items-center gap-1.5">
                    <TrendingUp size={10} class="text-emerald-400 shrink-0" />
                    <span class="text-[9px] font-black text-emerald-400 tracking-widest">Tình báo giá</span>
                  </div>
                  {#if bestPrice}
                    <div class="flex items-center gap-2">
                       <span class="text-[10px] font-mono font-black text-emerald-400">
                         {formatCurrency(bestPrice)}
                       </span>
                       <span class="text-[7px] font-mono text-white/20 tracking-tighter">[Best]</span>
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        </div>

        <!-- Quantity -->
        <div class="pl-[72px] md:pl-0 mt-1 md:mt-0 flex md:flex-none items-center justify-between md:justify-start">
          <span class="md:hidden text-[9px] font-mono text-gray-500 tracking-widest ">Stock</span>
          <span class="px-2.5 py-1 rounded bg-black/40 xl:bg-transparent xl:border-none md:px-0 md:py-0 border border-white/5 shadow-inner md:shadow-none text-[11px] font-mono font-bold {
            product.stock === 0 ? 'text-red-400 border-red-500/20' : 
            product.stock < 20 ? 'text-[#FFB800] border-[#FFB800]/20' : 
            'text-gray-300'
          }">
            {product.stock}
            <span class="text-[9px] text-gray-600 ml-1">UNITS</span>
          </span>
        </div>

        <!-- System Status -->
        <div class="pl-[72px] md:pl-0 mt-3 md:mt-0 flex md:flex-none justify-start items-center">
          <span
            class="px-3 py-1 md:py-1.5 rounded-lg text-[9px] font-bold font-mono tracking-widest shadow-inner inline-flex"
            style:color={status.color}
            style:border="1px solid {status.color}40"
            style:background="{status.color}15"
          >
            {status.label}
          </span>
        </div>

        <!-- Operations / Actions -->
        <div class="absolute bottom-3 right-3 md:relative md:bottom-auto md:right-auto md:flex shadow-[-20px_0_20px_-5px_transparent]">
          <div class="flex items-center gap-1.5 justify-end md:translate-x-2 md:group-hover:translate-x-0 w-full bg-[#0a0a0a] md:bg-transparent pl-2">
            <a
              href="/{product.slug}"
              target="_blank"
              class="p-2 text-[#FFB800] hover:text-white transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-[#FFB800]/20 hover:border-[#FFB800]/40 shadow-sm"
              title="View Landing Page"
              onclick={(e: MouseEvent) => e.stopPropagation()}
            >
              <ExternalLink size={14} />
            </a>
            <a
              href={getAuthToken() ? `/${product.slug}?live_edit=true&token=${getAuthToken()}` : '#'}
              target={getAuthToken() ? "_blank" : undefined}
              aria-disabled={!getAuthToken()}
              class="p-2 transition-colors rounded-xl md:bg-black/40 bg-white/5 border shadow-sm {getAuthToken() ? 'text-[#00FFFF] hover:text-white border-[#00FFFF]/20 hover:border-[#00FFFF]/40' : 'text-white/20 border-white/5 cursor-not-allowed'}"
              title={getAuthToken() ? "Edit Live (Supper Admin Only)" : "Chưa xác thực — vui lòng đăng nhập lại"}
              onclick={(e: MouseEvent) => { e.stopPropagation(); if (!getAuthToken()) e.preventDefault(); }}
            >
              <Sparkles size={14} />
            </a>
            <button
              onclick={(e: MouseEvent) => { e.stopPropagation(); onOpenReviewLab({ id: product.id, name: product.name }); }}
              class="p-2 text-[#FFD700]/60 md:text-gray-500 hover:text-[#FFD700] transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-[#FFD700]/20 shadow-sm"
              title="Review Lab"
              id="review-lab-btn-{product.id}"
            >
              <StarIcon size={14} />
            </button>
            <button
              onclick={(e: MouseEvent) => { e.stopPropagation(); onEdit(product); }}
              class="p-2 text-gray-400 md:text-gray-500 hover:text-[#00FFFF] transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-[#00FFFF]/20 shadow-sm"
              title="Edit Product"
            >
              <Pencil size={14} />
            </button>
            <button
              onclick={(e: MouseEvent) => { e.stopPropagation(); onDelete(product.id); }}
              class="p-2 text-red-500 md:text-gray-500 hover:text-red-400 transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-red-500/20 shadow-sm"
              title="Delete Product"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      </div>
    {/each}
  </div>
</div>

<!-- Intelligence Display Layer (Elite V2.2: Zero-Overlap Architecture) -->
{#if fullViewMarketData}
  <!-- Full View Modal (Elite V2.2) -->
  <div class="fixed inset-0 bg-black/90 backdrop-blur-xl flex items-center justify-center p-4 md:p-8 pointer-events-auto" 
       style="z-index: {Z_INDEX_ADMIN.SUPREME_POWER};"
       onclick={(e) => { if (e.target === e.currentTarget) closeMarketReport(); }}>
    <div class="w-full max-w-4xl max-h-[80vh] bg-[#0a0a0a] border border-emerald-500/30 rounded-3xl overflow-hidden flex flex-col shadow-[0_0_100px_rgba(0,0,0,0.5)]">
      <div class="flex items-center justify-between p-6 border-b border-white/5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
            <TrendingUp size={20} class="text-emerald-400" />
          </div>
          <div class="flex flex-col">
            <h2 class="text-lg font-black text-white tracking-tight">BÁO CÁO TRINH SÁT THỊ TRƯỜNG</h2>
            <p class="text-[10px] font-mono text-white/40 tracking-[0.2em]">Deep Intel v2.2 | XoHi Neural Engine</p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-8 grid grid-cols-1 lg:grid-cols-2 gap-8 custom-scrollbar">
        <!-- Left: Analysis & Overview -->
        <div class="flex flex-col gap-6">
          <div class="p-6 rounded-2xl bg-emerald-500/[0.03] border border-emerald-500/10 relative overflow-hidden group">
            <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Sparkles size={60} class="text-emerald-400" />
            </div>
            <div class="flex items-center gap-2 mb-4">
              <ShieldCheck size={16} class="text-emerald-400" />
              <span class="text-[10px] font-black text-emerald-400 tracking-widest">Phân tích từ XOHI</span>
            </div>
            <div class="flex flex-col gap-3">
              <p class="text-sm text-white/80 leading-relaxed italic font-serif">
                "{fullViewMarketData.analysis_overview || fullViewMarketData.analysis || 'AI đang tổng hợp dữ liệu...'}"
              </p>
              {#if fullViewMarketData.critical_analysis}
                <div class="mt-2 pt-2 border-t border-emerald-500/10">
                  <span class="text-[9px] font-black text-amber-400/60 block mb-1">Phản biện:</span>
                  <p class="text-xs text-white/60 italic leading-relaxed">{fullViewMarketData.critical_analysis}</p>
                </div>
              {/if}
              {#if fullViewMarketData.optimization_strategy}
                <div class="mt-2 pt-2 border-t border-emerald-500/10">
                  <span class="text-[9px] font-black text-cyan-400/60 block mb-1">Chiến lược tối ưu:</span>
                  <p class="text-xs text-white/60 italic leading-relaxed">{fullViewMarketData.optimization_strategy}</p>
                </div>
              {/if}
            </div>
          </div>

          <!-- Quick Stats -->
          <div class="grid grid-cols-2 gap-4">
             <div class="p-4 rounded-xl bg-white/5 border border-white/5">
                <span class="text-[8px] text-white/30 font-black block mb-1">Ads Count</span>
                <span class="text-2xl font-mono text-amber-400">{(fullViewMarketData.ads || []).length}</span>
             </div>
             <div class="p-4 rounded-xl bg-white/5 border border-white/5">
                <span class="text-[8px] text-white/30 font-black block mb-1">Organic Results</span>
                <span class="text-2xl font-mono text-emerald-400">{(fullViewMarketData.organic_results || []).length}</span>
             </div>
          </div>
        </div>

        <!-- Right: Detailed List -->
        <div class="flex flex-col gap-6">
          <!-- Sponsored -->
          {#if fullViewMarketData.ads && fullViewMarketData.ads.length > 0}
            <div class="flex flex-col gap-3">
              <div class="flex items-center gap-2 text-[10px] font-black text-amber-400 tracking-[0.2em]">
                 🔥 Quảng cáo (Sponsored/Ads)
              </div>
              <div class="flex flex-col gap-2">
                 {#each fullViewMarketData.ads as ad}
                   <a 
                     href={ad.link} 
                     target="_blank"
                     class="flex items-center justify-between p-4 rounded-xl bg-amber-500/5 border border-amber-500/10 hover:border-amber-500/40 transition-all group/link"
                   >
                     <div class="flex flex-col min-w-0">
                       <span class="text-xs font-bold text-white/80 truncate group-hover/link:text-amber-400">{ad.title}</span>
                       <span class="text-[9px] text-white/30 tracking-widest">{ad.platform}</span>
                     </div>
                     <div class="flex items-center gap-4 shrink-0">
                       <span class="text-sm font-mono text-amber-400 font-black">{ad.price ? formatCurrency(ad.price) : 'N/A'}</span>
                       <ExternalLink size={14} class="text-white/10 group-hover/link:text-amber-400" />
                     </div>
                   </a>
                 {/each}
              </div>
            </div>
          {/if}

          <!-- Organic -->
          {#if fullViewMarketData.organic_results && fullViewMarketData.organic_results.length > 0}
            <div class="flex flex-col gap-3">
              <div class="flex items-center gap-2 text-[10px] font-black text-emerald-400 tracking-[0.2em]">
                 🌐 Top 10 Kết quả Tự nhiên
              </div>
              <div class="flex flex-col gap-2">
                 {#each fullViewMarketData.organic_results as res}
                   <a 
                     href={res.link} 
                     target="_blank"
                     class="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:border-emerald-500/40 transition-all group/link"
                   >
                     <div class="flex flex-col min-w-0">
                       <span class="text-xs font-bold text-white/70 truncate group-hover/link:text-emerald-400">{res.title}</span>
                       <span class="text-[9px] text-white/20 tracking-widest">{res.platform}</span>
                     </div>
                     <div class="flex items-center gap-4 shrink-0">
                       <span class="text-sm font-mono text-emerald-400 font-black">{res.price ? formatCurrency(res.price) : 'N/A'}</span>
                       <ExternalLink size={14} class="text-white/10 group-hover/link:text-emerald-400" />
                     </div>
                   </a>
                 {/each}
              </div>
            </div>
          {/if}
        </div>
      </div>
      
      <div class="p-6 border-t border-white/5 flex justify-end relative z-20">
         <button 
           type="button"
           onclick={(e) => { 
             e.preventDefault();
             e.stopPropagation();
             closeMarketReport();
           }}
           class="px-8 py-3 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-[11px] font-black text-emerald-400 hover:bg-emerald-500/30 hover:text-emerald-300 hover:scale-105 active:scale-95 transition-all cursor-pointer shadow-[0_0_20px_rgba(16,185,129,0.2)]"
         >
           ĐÓNG BÁO CÁO
         </button>
      </div>
    </div>
  </div>
{:else if activeIntelId && activeIntelData}
  <!-- Singleton Intelligence Popover (Elite V2.2) -->
  {@const m = activeIntelData}
  {@const allResults = [...(m.ads || []), ...(m.organic_results || [])]}
  <div class="fixed w-[340px] pointer-events-auto flex flex-col"
       onmouseenter={() => isHoveringPopover = true}
       onmouseleave={() => { isHoveringPopover = false; activeIntelId = null; activeIntelData = null; }}
       style="z-index: {Z_INDEX_ADMIN.POPOVER}; 
              left: {activeIntelPos.x}px; 
              top: {popoverPlacement === 'top' ? activeIntelPos.y : activeIntelPos.y + activeIntelPos.height}px; 
              max-height: {popoverPlacement === 'top' ? activeIntelPos.y - 20 : window.innerHeight - (activeIntelPos.y + activeIntelPos.height) - 20}px;
              transform: {popoverPlacement === 'top' ? 'translateY(-100%) translateY(-10px)' : 'translateY(10px)'};">
    <!-- Invisible bridge to prevent disappearing on hover -->
    <div class="absolute inset-x-0 {popoverPlacement === 'top' ? 'bottom-0 translate-y-full' : 'top-0 -translate-y-full'} h-4"></div>
    
    <div class="p-4 rounded-2xl bg-black/95 border border-emerald-500/30 backdrop-blur-xl flex flex-col min-h-0">
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between border-b border-white/5 pb-2">
          <div class="flex flex-col">
            <span class="text-[10px] font-black text-white/40 tracking-[0.2em]">Dữ liệu trinh sát</span>
            <span class="text-[8px] font-mono text-white/20 ">{allResults.length} kết quả</span>
          </div>
          <button 
            onclick={(e) => { 
              e.preventDefault();
              e.stopPropagation(); 
              fullViewMarketData = { ...activeIntelData };
            }}
            class="px-2 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[8px] font-black hover:bg-emerald-500/20 transition-all"
          >
            FULL VIEW
          </button>
        </div>

        <div class="flex flex-col gap-3 overflow-y-auto custom-scrollbar pr-2 min-h-0">
          <!-- Ads -->
          {#if m.ads && m.ads.length > 0}
            <div class="flex flex-col gap-1.5">
              <div class="text-[8px] font-black text-amber-400/60 ">🔥 Quảng cáo (Ads)</div>
              {#each m.ads as ad}
                <a href={ad.link} target="_blank" onclick={(e) => e.stopPropagation()}
                   class="flex items-center justify-between p-2 rounded-lg bg-amber-500/5 border border-amber-500/10 hover:border-amber-500/40 transition-all group/link">
                  <div class="flex flex-col min-w-0">
                    <span class="text-[9px] font-bold text-white/80 truncate group-hover/link:text-amber-400">{ad.title}</span>
                    <span class="text-[7px] text-white/30 tracking-widest">{ad.platform}</span>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <span class="text-[10px] font-mono text-amber-400 font-black">{ad.price ? formatCurrency(ad.price) : 'N/A'}</span>
                    <ExternalLink size={10} class="text-white/10 group-hover/link:text-amber-400" />
                  </div>
                </a>
              {/each}
            </div>
          {/if}

          <!-- Analysis -->
          <div class="flex flex-col gap-1.5">
            <div class="text-[8px] font-black text-emerald-400/60 ">💡 Phân tích từ XoHi</div>
            <p class="text-[9px] text-white/70 leading-relaxed italic line-clamp-3">
              "{m.analysis_overview}"
            </p>
          </div>

          <!-- Organic -->
          {#if m.organic_results && m.organic_results.length > 0}
            <div class="flex flex-col gap-1.5">
              <div class="text-[8px] font-black text-emerald-400/60 ">🌐 Top 10 Tự nhiên</div>
              {#each m.organic_results.slice(0, 3) as res}
                <a href={res.link} target="_blank" onclick={(e) => e.stopPropagation()}
                   class="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/5 hover:border-emerald-500/40 transition-all group/link">
                  <div class="flex flex-col min-w-0">
                    <span class="text-[9px] font-bold text-white/70 truncate group-hover/link:text-emerald-400">{res.title}</span>
                    <span class="text-[7px] text-white/20 tracking-widest">{res.platform}</span>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <span class="text-[10px] font-mono text-emerald-400 font-black">{res.price ? formatCurrency(res.price) : 'N/A'}</span>
                    <ExternalLink size={10} class="text-white/10 group-hover/link:text-emerald-400" />
                  </div>
                </a>
              {/each}
              {#if m.organic_results.length > 3}
                <span class="text-[7px] text-center text-white/20 ">Và {m.organic_results.length - 3} kết quả khác...</span>
              {/if}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}
