<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import Search from "@lucide/svelte/icons/search";
  import Share2 from "@lucide/svelte/icons/share-2";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";
  import Ticket from "@lucide/svelte/icons/ticket";
  import Tag from "@lucide/svelte/icons/tag";
  import Truck from "@lucide/svelte/icons/truck";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { getSearchStore } from "$lib/state/commerce/search.svelte";
  import SmartSearch from "../product/SmartSearch.svelte";
  import type { Voucher, Product } from "$lib/types";
  import { formatCurrency } from "$lib/utils/format";

  let { vouchers = [], products = [] }: { vouchers: Voucher[]; products: Product[] } = $props();

  const cartStore = getCartStore();
  const searchStore = getSearchStore();

  // Mobile dedicated states
  let copiedId = $state<string | null>(null);
  let activeConditionVoucherId = $state<string | null>(null);

  // Filter tabs state
  type TabId = "ALL" | "DISCOUNT" | "SHIPPING";
  let activeTab = $state<TabId>("ALL");
  const tabs = [
    { id: "ALL" as const, label: "Tất cả", icon: Ticket },
    { id: "DISCOUNT" as const, label: "Giảm giá", icon: Tag },
    { id: "SHIPPING" as const, label: "Miễn ship", icon: Truck },
  ];

  const filtered = $derived(
    activeTab === "ALL"
      ? vouchers
      : vouchers.filter((v) => v.category === activeTab)
  );

  async function copyCode(id: string) {
    try {
      await navigator.clipboard.writeText(id);
      copiedId = id;
      setTimeout(() => {
        copiedId = null;
      }, 2000);
    } catch {
      // Fallback
    }
  }

  function usedPercent(v: Voucher): number {
    if (!v.usage_limit || v.usage_limit <= 0) return 0;
    return Math.min(100, Math.round((v.used_count / v.usage_limit) * 100));
  }

  function isExhausted(v: Voucher): boolean {
    return !!(v.usage_limit && v.used_count >= v.usage_limit);
  }

  function quantityLeft(v: Voucher): number | null {
    if (!v.usage_limit) return null;
    return Math.max(0, v.usage_limit - v.used_count);
  }

  function formatShort(val: number): string {
    if (!val) return "0đ";
    if (val >= 1000000) {
      return `${val / 1000000}Mđ`;
    }
    if (val >= 1000) {
      return `${val / 1000}kđ`;
    }
    return `${val}đ`;
  }

  onMount(() => {
    // Pure static presentation
  });
</script>

<!-- ===== MOBILE TIKTOK STYLE INTERFACE ===== -->
<div class="tiktok-mobile-layout">
  <!-- Top Sticky Detail Header Style -->
  <header class="detail-header">
    <div class="header-main">
      <button type="button" class="icon-btn" onclick={() => history.back()} aria-label="Quay lại">
        <ChevronLeft size={24} />
      </button>
      
      <div
        class="search-bar-wrapper cursor-text"
        role="presentation"
        onclick={() => searchStore.isOverlayOpen = true}
      >
        <Search size={16} class="search-icon shrink-0" />
        <span class="placeholder">Tìm "khuyến mãi, voucher"...</span>
      </div>

      <div class="header-actions">
        <button type="button" class="icon-btn" aria-label="Chia sẻ" onclick={() => {
          if (navigator.share) {
            navigator.share({ title: 'Khuyến mãi OSMO', url: window.location.href });
          } else {
            navigator.clipboard.writeText(window.location.href);
          }
        }}>
          <Share2 size={24} />
        </button>

        <button type="button" class="icon-btn relative" onclick={() => goto('/checkout')} aria-label="Giỏ hàng">
          <ShoppingCart size={24} />
          {#if cartStore.totalItems > 0}
            <span class="badge">{cartStore.totalItems}</span>
          {/if}
        </button>

        <button type="button" class="icon-btn" aria-label="Thêm">
          <MoreHorizontal size={24} />
        </button>
      </div>
    </div>
  </header>

  {#if searchStore.isOverlayOpen}
    <SmartSearch variant="mobile-overlay" />
  {/if}



  <!-- Swipable horizontal tabs -->
  <div class="tiktok-tabs-wrap">
    <div class="tiktok-tabs">
      {#each tabs as tab}
        {@const Icon = tab.icon}
        <button
          class="tiktok-tab-btn {activeTab === tab.id ? 'active' : ''}"
          onclick={() => { activeTab = tab.id; }}
        >
          <span class="tab-icon">
            <Icon size={14} />
          </span>
          <span class="tab-label">{tab.label}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Main Feed / Voucher stream -->
  <div class="tiktok-feed">
    {#if filtered.length === 0}
      <div class="empty-state">
        <div class="empty-icon">🎟️</div>
        <p class="empty-title">Chưa có ưu đãi nào</p>
      </div>
    {:else}
      {#each filtered as v, i (v.id)}
        {@const pct = usedPercent(v)}
        <div class="tiktok-card {isExhausted(v) ? 'exhausted' : ''}">
          <!-- Scallop top left hot badge -->
          {#if pct > 70}
            <div class="tiktok-hot-badge">CỰC HOT x10</div>
          {/if}

          <div class="tiktok-card-inner">
            <!-- Left section: large discount label & SVG speed icon -->
            <div class="tiktok-card-left {v.category === 'SHIPPING' ? 'stub-ship' : 'stub-discount'}">
              <svg class="tiktok-card-svg" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- Speed lines -->
                <line x1="15" y1="38" x2="35" y2="38" stroke="white" stroke-width="6" stroke-linecap="round" />
                <line x1="10" y1="50" x2="35" y2="50" stroke="white" stroke-width="6" stroke-linecap="round" />
                <line x1="15" y1="62" x2="35" y2="62" stroke="white" stroke-width="6" stroke-linecap="round" />
                <!-- Shopping bag -->
                <rect x="42" y="35" width="40" height="40" rx="8" stroke="white" stroke-width="6" />
                <path d="M52 35C52 26 58 20 62 20C66 20 72 26 72 35" stroke="white" stroke-width="6" stroke-linecap="round" />
                <circle cx="62" cy="55" r="7" stroke="white" stroke-width="4" fill="none" />
              </svg>
              <div class="tiktok-card-left-text">OSMO</div>
            </div>

            <!-- Right section: Details -->
            <div class="tiktok-card-right">
              <div class="tiktok-card-title">
                {#if v.type === "PERCENT"}
                  Giảm {v.value}%
                {:else}
                  Giảm {formatShort(v.value)}
                {/if}
              </div>

              <div class="tiktok-card-exclusive">
                <span>Độc quyền - {v.id.substring(0, 8)}...</span>
              </div>

              <p class="tiktok-card-detail">
                {#if v.type === "PERCENT" && v.max_discount}
                  Giảm tối đa {formatShort(v.max_discount)} · 
                {/if}
                Đơn Tối Thiểu {formatShort(v.min_spend)}
              </p>

              <!-- FOMO Glowing Progress Bar -->
              <div class="tiktok-progress-row">
                <div class="tiktok-progress-bar">
                  <div class="tiktok-progress-fill {pct > 70 ? 'danger' : ''}" style="width: {pct}%"></div>
                </div>
                <span class="tiktok-progress-text">🔥 Đã dùng {pct}%</span>
              </div>

              <!-- Footer elements inside card -->
              <div class="tiktok-card-footer">
                <button
                  type="button"
                  class="tiktok-btn-claim {copiedId === v.id ? 'copied' : ''}"
                  onclick={() => copyCode(v.id)}
                  disabled={isExhausted(v)}
                >
                  {copiedId === v.id ? 'ĐÃ LƯU ✓' : 'BỎ TÚI'}
                </button>

                <button
                  type="button"
                  class="tiktok-card-terms"
                  onclick={() => activeConditionVoucherId = activeConditionVoucherId === v.id ? null : v.id}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="width: 10px; height: 10px;">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  Thỏa điều kiện
                </button>
              </div>
            </div>
          </div>

          <!-- Absolute overlay for terms detail inside mobile card -->
          {#if activeConditionVoucherId === v.id}
            <div class="tiktok-condition-overlay" transition:fade={{ duration: 150 }}>
              <div class="tiktok-condition-box">
                <div class="tiktok-condition-header">
                  <span>CHI TIẾT VOUCHER</span>
                  <button class="tiktok-condition-close" onclick={() => activeConditionVoucherId = null}>×</button>
                </div>
                <div class="tiktok-condition-body">
                  <p>🎟️ Mã giảm giá: <strong>{v.id}</strong></p>
                  <p>💸 Tối thiểu: <strong>{formatCurrency(v.min_spend)}</strong></p>
                  {#if v.type === "PERCENT" && v.max_discount}
                    <p>🔥 Giảm tối đa: <strong>{formatCurrency(v.max_discount)}</strong></p>
                  {/if}
                  {#if quantityLeft(v) !== null}
                    <p>⚡ Còn lại: <strong>{quantityLeft(v)}</strong> lượt sử dụng</p>
                  {/if}
                  <p>⏳ Hạn sử dụng: Vui lòng săn ngay trước khi hết lượt</p>
                </div>
                <button class="tiktok-condition-btn-ok" onclick={() => activeConditionVoucherId = null}>ĐÃ HIỂU</button>
              </div>
            </div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>

</div>

<style>
  /* ─── PREMIUM RETAIL MOBILE LAYOUT (LIGHT THEME) ─── */
  .tiktok-mobile-layout {
    background: #f5f5f5;
    color: #222222;
    min-height: 100vh;
    padding-bottom: 95px;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    position: relative;
    overflow-x: hidden;
  }
  .detail-header {
    position: sticky;
    top: 0;
    left: 0;
    right: 0;
    background: #ffffff;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    display: flex;
    flex-direction: column;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    border-bottom: 0.5px solid rgba(0,0,0,0.05);
    z-index: 100;
  }
  .header-main {
    display: flex;
    align-items: center;
    padding: 6px 8px;
    gap: 12px;
    height: 48px;
  }
  .icon-btn {
    background: transparent;
    border: none;
    color: #444444;
    padding: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    position: relative;
  }
  .badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: #ee4d2d;
    color: white;
    font-size: 10px;
    font-weight: 900;
    min-width: 16px;
    height: 16px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  .search-bar-wrapper {
    flex: 1;
    min-width: 0;
    background: #f0f0f0;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    padding: 0 12px;
    gap: 8px;
    color: #888;
    overflow: hidden;
    border: 1px solid rgba(0,0,0,0.02);
  }
  .placeholder {
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .header-actions {
    display: flex;
    gap: 4px;
    align-items: center;
  }
  .tiktok-tabs-wrap {
    padding: 12px 12px 6px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .tiktok-tabs-wrap::-webkit-scrollbar {
    display: none;
  }
  .tiktok-tabs {
    display: flex;
    gap: 8px;
    width: max-content;
  }
  .tiktok-tab-btn {
    display: flex;
    align-items: center;
    gap: 5px;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    color: #555555;
    padding: 6px 14px;
    border-radius: 30px;
    font-size: 11px;
    font-weight: 800;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .tiktok-tab-btn.active {
    background: #ee4d2d;
    color: #ffffff;
    border-color: #ee4d2d;
    box-shadow: 0 4px 12px rgba(238, 77, 45, 0.25);
  }
  .tab-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  .tiktok-feed {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .tiktok-card {
    position: relative;
    background: #ffffff;
    border-radius: 14px;
    border: 1px solid #eaeaea;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s ease;
  }
  .tiktok-card:active {
    transform: scale(0.98);
  }
  .tiktok-hot-badge {
    position: absolute;
    top: 0;
    left: 0;
    background: linear-gradient(90deg, #ff2c55, #fe0979);
    color: #fff;
    font-size: 8px;
    font-weight: 900;
    padding: 3px 8px;
    border-bottom-right-radius: 10px;
    z-index: 10;
    letter-spacing: 0.5px;
  }
  .tiktok-card-inner {
    display: flex;
    min-height: 125px;
  }
  .tiktok-card-left {
    width: 80px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    padding: 12px 4px;
    border-right: 1px dashed #eaeaea;
  }
  .tiktok-card-left.stub-discount {
    background: linear-gradient(135deg, #ff2c55 0%, #fe0979 100%);
  }
  .tiktok-card-left.stub-ship {
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  }
  .tiktok-card-svg {
    width: 32px;
    height: 32px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  }
  .tiktok-card-left-text {
    font-size: 8px;
    font-weight: 900;
    color: #fff;
    letter-spacing: 1px;
    margin-top: 4px;
  }
  .tiktok-card-right {
    flex: 1;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .tiktok-card-title {
    font-size: 18px;
    font-weight: 950;
    color: #111111;
    line-height: 1.2;
  }
  .tiktok-card-exclusive {
    font-size: 8px;
    color: #ee4d2d;
    font-weight: 850;
    border: 1px solid rgba(238, 77, 45, 0.3);
    background: rgba(238, 77, 45, 0.04);
    border-radius: 4px;
    padding: 1px 5px;
    align-self: flex-start;
    margin-top: 2px;
  }
  .tiktok-card-detail {
    font-size: 10px;
    color: #666666;
    margin: 4px 0;
    font-weight: 500;
  }
  .tiktok-progress-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
  }
  .tiktok-progress-bar {
    flex: 1;
    height: 4px;
    background: #f0f0f0;
    border-radius: 3px;
    overflow: hidden;
  }
  .tiktok-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #00f2fe, #ff2c55);
    border-radius: 3px;
  }
  .tiktok-progress-fill.danger {
    background: linear-gradient(90deg, #ff2c55, #fe0979);
  }
  .tiktok-progress-text {
    font-size: 8px;
    color: #888888;
    font-weight: 700;
  }
  .tiktok-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-top: 2px;
  }
  .tiktok-btn-claim {
    flex: 1;
    background: #ee4d2d;
    color: #ffffff;
    border: none;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 900;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: center;
    box-shadow: 0 4px 8px rgba(238, 77, 45, 0.15);
  }
  .tiktok-btn-claim.copied {
    background: #2e7d32 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 8px rgba(46, 125, 50, 0.2);
  }
  .tiktok-card-terms {
    font-size: 9px;
    color: #2e7d32;
    font-weight: 850;
    background: rgba(46, 125, 50, 0.06);
    border: 1px solid rgba(46, 125, 50, 0.2);
    border-radius: 12px;
    padding: 2px 6px;
    display: inline-flex;
    align-items: center;
    gap: 2px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .tiktok-comments-container {
    position: fixed;
    bottom: 90px;
    left: 10px;
    right: 75px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    z-index: 999;
    pointer-events: none;
  }
  .tiktok-comment-bubble {
    background: rgba(18, 18, 20, 0.85);
    backdrop-filter: blur(8px);
    border-radius: 10px;
    padding: 5px 10px;
    font-size: 10px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    animation: comment-slide 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28) both;
    max-width: 100%;
    border: 0.5px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
  }
  @keyframes comment-slide {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .tiktok-hearts-container {
    position: fixed;
    bottom: 90px;
    right: 15px;
    width: 60px;
    height: 320px;
    z-index: 999;
    pointer-events: none;
  }
  .tiktok-heart {
    position: absolute;
    bottom: 0;
    animation: heart-float 1.5s cubic-bezier(0.08, 0.8, 0.24, 0.96) forwards;
    filter: drop-shadow(0 2px 5px currentColor);
    font-size: 24px;
  }
  @keyframes heart-float {
    0% { opacity: 1; transform: translateY(0) scale(0.6) rotate(0deg); }
    20% { transform: translateY(-40px) scale(1.1) rotate(15deg); }
    80% { opacity: 0.8; }
    100% { opacity: 0; transform: translateY(-300px) scale(0.8) rotate(-20deg); }
  }
  .tiktok-floating-like-btn {
    position: fixed;
    bottom: 20px;
    right: 15px;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ff2c55, #fe0979);
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    cursor: pointer;
    z-index: 1000;
    box-shadow: 0 4px 15px rgba(255, 44, 85, 0.35);
    animation: btn-bounce 1s infinite alternate;
  }
  @keyframes btn-bounce {
    from { transform: scale(1); }
    to { transform: scale(1.08); }
  }
  .tiktok-condition-overlay {
    position: absolute;
    inset: 0;
    background: rgba(255, 255, 255, 0.98);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
    z-index: 20;
  }
  .tiktok-condition-box {
    background: #ffffff;
    border: 1px solid #eaeaea;
    border-radius: 12px;
    width: 100%;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }
  .tiktok-condition-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    font-weight: 900;
    color: #222222;
    border-bottom: 1px solid #eee;
    padding-bottom: 4px;
  }
  .tiktok-condition-close {
    background: none;
    border: none;
    color: #999999;
    font-size: 18px;
    cursor: pointer;
  }
  .tiktok-condition-body {
    font-size: 10px;
    color: #555555;
    line-height: 1.5;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .tiktok-condition-btn-ok {
    background: #222222;
    color: #ffffff;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 850;
    cursor: pointer;
  }
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;
    gap: 12px;
  }
  .empty-icon {
    font-size: 48px;
    opacity: 0.3;
  }
  .empty-title {
    font-size: 14px;
    font-weight: 800;
    color: #888888;
  }
</style>
