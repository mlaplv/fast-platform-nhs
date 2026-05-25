<script lang="ts">
  import type { Product, ReviewStats } from "$lib/types";
  import { formatCurrency } from "$lib/utils/format";
  import { supportAgent } from "$lib/state/commerce/supportAgent.svelte";
  import { resolveMediaUrl } from "$lib/state/utils";
  import Package from "@lucide/svelte/icons/package";
  import Gift from "@lucide/svelte/icons/gift";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Minus from "@lucide/svelte/icons/minus";
  import Plus from "@lucide/svelte/icons/plus";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import HelenIcon from "$lib/components/client/support/HelenIcon.svelte";
  import ShareToUnlock from "../../shared/ShareToUnlock.svelte";

  interface VoucherUI {
    id: string;
    label: string;
    sub: string;
    type: "ship" | "discount";
  }

  interface Props {
    product: Product;
    stats: ReviewStats | null;
    isFlashSaleActive: boolean;
    timeLeft: { hours: number; minutes: number; seconds: number };
    productVouchers: VoucherUI[];
    selectedVouchers: string[];
    variations: import("$lib/types").TierVariation[];
    selectedIndices: number[];
    quantity: number;
    currentStock: number;
    activePrices: { sale: number | string; original: number | string };
    activeComboQty: number;
    activeGifts: { name: string; qty: number; image?: string; slug?: string }[];
    helenAdvice: string;
    onSelectOption: (tIdx: number, oIdx: number) => void;
    onQuantityChange: (delta: number) => void;
    onToggleVoucher: (id: string) => void;
    onAddToCart: () => void;
    onBuyNow: () => void;
    onWriteReview: () => void;
    onViralUnlock: () => void;
    onTriggerVerify?: () => void;
  }

  let {
    product,
    stats,
    isFlashSaleActive,
    timeLeft,
    productVouchers,
    selectedVouchers,
    variations,
    selectedIndices,
    quantity,
    currentStock,
    activePrices,
    activeComboQty,
    activeGifts,
    helenAdvice,
    onSelectOption,
    onQuantityChange,
    onToggleVoucher,
    onAddToCart,
    onBuyNow,
    onWriteReview,
    onViralUnlock,
    onTriggerVerify,
  }: Props = $props();

  const isMall = $derived(!!product.metadata?.is_mall);
  const displayStockVal = $derived.by(() => {
    const hash = [...String(product.id)].reduce((a, b) => a + b.charCodeAt(0), 0);
    return (hash % 6) + 3;
  });
</script>

<div class="info-container">
  <!-- Mall Label & Title -->
  <div class="header">
    <div class="mall-badge group">
      <div class="shine-effect"></div>
      <span class="badge-text">{isMall ? "Mall" : "Shop"}</span>
    </div>
    <div class="verified-badge group">
      <div class="shine-effect"></div>
      <svg
        class="w-2.5 h-2.5"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="4"
        ><path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M5 13l4 4L19 7"
        /></svg
      >
      <span class="badge-text">Verified</span>
    </div>
    <h1 class="product-title">
      {product.name.replace(/40gr/g, "40g")}
    </h1>
  </div>

  <!-- Stats Row -->
  <div class="stats-row">
    <div class="rating-box">
      <span class="rating-value"
        >{stats?.average_rating || product.metadata?.rating || "5.0"}</span
      >
      <div class="stars">
        {#each Array(5) as _, i}
          <svg
            class="star-icon"
            class:active={i <
              Math.floor(
                stats?.average_rating || Number(product.metadata?.rating) || 5,
              )}
            viewBox="0 0 24 24"
            ><path
              d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"
            /></svg
          >
        {/each}
      </div>
    </div>
    <div class="divider"></div>
    <button
      class="stat-btn"
      onclick={() =>
        document
          .getElementById("product-reviews")
          ?.scrollIntoView({ behavior: "smooth" })}
    >
      <span class="stat-value"
        >{stats?.total_count ?? (product.metadata?.reviews?.length || 0)}</span
      >
      <span class="stat-label">Đánh giá</span>
    </button>
    <div class="divider"></div>
    <div class="stat-item">
      <span class="stat-value"
        >{product.order_count_text || product.orderCount || 0}</span
      >
      <span class="stat-label">Đã bán</span>
    </div>
    <button class="report-btn" onclick={onWriteReview}>Tố cáo</button>
  </div>

  <!-- Price Bar -->
  <div class="price-bar">
    <div class="price-content">
      <div class="original-price-row">
        {#if Number(activePrices.original) > Number(activePrices.sale)}
          <span class="original-price"
            >{formatCurrency(activePrices.original)}</span
          >
          <span class="save-badge">
            Tiết kiệm {formatCurrency(
              Number(activePrices.original) - Number(activePrices.sale),
            )}
          </span>
        {/if}
      </div>
      <div class="sale-price-row">
        <span class="sale-price">{formatCurrency(activePrices.sale)}</span>
      </div>



      {#if helenAdvice}
        <div class="helen-intelligence">
          <div class="helen-header">
            {#if activeComboQty > 1}
              <div class="combo-pill">
                <Package size={10} />
                {activeComboQty} sp đã áp dụng
              </div>
            {/if}
            <div class="helen-tag">
              <HelenIcon size={12} color="#3b82f6" />
              <span class="helen-name">{supportAgent.config.agentName}</span>
              <div class="pulse-dot"></div>
            </div>
          </div>
          <div class="helen-body">
            <p class="advice-text">{helenAdvice}</p>
            <button
              class="helen-verify-btn"
              onclick={() => onTriggerVerify?.()}
            >
              <svg
                class="w-3.5 h-3.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
                ><path d="M3 7V5a2 2 0 0 1 2-2h2" /><path
                  d="M17 3h2a2 2 0 0 1 2 2v2"
                /><path d="M21 17v2a2 2 0 0 1-2 2h-2" /><path
                  d="M7 21H5a2 2 0 0 1-2-2v-2"
                /><line x1="7" y1="12" x2="17" y2="12" /></svg
              >
              Xác thực nguồn gốc
            </button>
          </div>
        </div>
      {/if}
    </div>

    {#if isFlashSaleActive}
      <div class="timer-box">
        <div class="timer-header">
          <div class="ping-dot"></div>
          <span class="timer-label">Kết thúc sau</span>
        </div>
        <div class="countdown">
          <div class="time-unit">
            {timeLeft.hours.toString().padStart(2, "0")}
          </div>
          <span class="time-sep">:</span>
          <div class="time-unit">
            {timeLeft.minutes.toString().padStart(2, "0")}
          </div>
          <span class="time-sep">:</span>
          <div class="time-unit">
            {timeLeft.seconds.toString().padStart(2, "0")}
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Vouchers -->
  <div class="section-row">
    <span class="row-label">Mã giảm giá</span>
    <div class="vouchers-list">
      {#each productVouchers as v}
        {@const isApplied = selectedVouchers.includes(v.id)}
        <button
          onclick={() => onToggleVoucher(v.id)}
          class="voucher-ticket"
          class:applied={isApplied}
        >
          <div class="ticket-notch left"></div>
          <div class="ticket-notch right"></div>
          <div class="ticket-divider"></div>
          <div class="ticket-content">
            <span class="voucher-label">{v.label}</span>
            <span class="voucher-sub">{v.sub || ""}</span>
          </div>
          {#if isApplied}
            <div class="check-badge">
              <svg
                class="check-icon"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="3"
                  d="M5 13l4 4L19 7"
                /></svg
              >
            </div>
          {/if}
        </button>
      {/each}
    </div>
  </div>

  <!-- Share Promo -->
  <div class="section-row promo-row">
    {#key product.id}
      <ShareToUnlock {product} compact={true} onUnlock={onViralUnlock} />
    {/key}
  </div>

  <!-- Shipping -->
  <div class="section-row">
    <span class="row-label">Vận chuyển</span>
    <div class="shipping-info">
      <div class="ship-header">
        <svg
          class="check-icon-green"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 13l4 4L19 7"
          /></svg
        >
        <span class="ship-status">Nhận hàng nhanh chóng</span>
      </div>
      <div class="ship-details">
        <span class="ship-price">Phí ship 0₫</span>
        <p class="ship-desc">
          Miễn phí hỏa tốc giao nhanh toàn quốc, kiểm tra hàng mới thanh toán
        </p>
      </div>
    </div>
  </div>

  <!-- Variations -->
  {#if variations.length > 0}
    <div class="variations-container">
      {#each variations as tier, tIdx}
        <div class="section-row">
          <span class="row-label capitalize">{tier.name}</span>
          <div class="options-list">
            {#each tier.options as option, oIdx}
              {@const isSelected = selectedIndices[tIdx] === oIdx}
              <button
                type="button"
                onclick={() => onSelectOption(tIdx, oIdx)}
                class="option-btn"
                class:selected={isSelected}
              >
                {#if tIdx === 0 && tier.images?.[oIdx]}
                  <img
                    src={tier.images[oIdx]}
                    alt={option}
                    class="option-img"
                  />
                {/if}
                <span class="option-text">{option}</span>
                {#if isSelected}
                  <div class="selected-corner"></div>
                  <svg
                    class="selected-check"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="4"><path d="M20 6L9 17l-5-5" /></svg
                  >
                {/if}
              </button>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Quantity -->
  <div class="section-row quantity-row">
    <span class="row-label">Số lượng</span>
    <div class="quantity-controls">
      <div class="stepper">
        <button
          class="step-btn"
          onclick={() => onQuantityChange(-1)}
          disabled={quantity <= 1}
        >
          <Minus size={14} strokeWidth={3} />
        </button>
        <input type="text" readonly class="qty-input" value={quantity} />
        <button
          class="step-btn"
          onclick={() => onQuantityChange(1)}
          disabled={quantity >= (currentStock || 99)}
        >
          <Plus size={14} strokeWidth={3} />
        </button>
      </div>
      <div class="stock-info">
        <span class="stock-status-title">Số lượng có hạn</span>
        {#if currentStock < 10}
          <span class="stock-warning">
            <span class="ping-dot-red"></span>
            Hàng hiếm, chỉ còn {currentStock} bộ trong kho
          </span>
        {:else}
          <span class="stock-ok">Đang có sẵn tại kho Mall chính hãng</span>
        {/if}
      </div>
    </div>
  </div>

  <!-- Gifts -->
  {#if activeGifts.length > 0}
    <div class="gifts-section">
      <div class="gifts-card group/gift">
        <div class="gift-icon-box">
          <Gift size={20} />
        </div>
        <div class="gifts-content">
          <div class="gifts-header">
            <h3 class="gifts-title">Ưu đãi độc quyền</h3>
            {#if activeComboQty > 1}
              <div class="combo-tag">
                <Package size={10} /> Combo x{activeComboQty}
              </div>
            {/if}
          </div>
          <div class="gifts-list">
            {#each activeGifts as gift}
              {#if gift.slug}
                <a href="/{gift.slug}" class="gift-item hover:opacity-85 transition-opacity cursor-pointer group/gift-item w-full" style="text-decoration: none;">
                  <div class="gift-thumb relative">
                    {#if gift.image}
                      <img
                        src={resolveMediaUrl(gift.image)}
                        alt={gift.name}
                        class="thumb-img"
                      />
                    {:else}
                      <div class="thumb-placeholder"><Sparkles size={16} /></div>
                    {/if}
                  </div>
                  <div class="gift-info flex-1 min-w-0">
                    <span class="gift-name group-hover/gift-item:text-[#ee4d2d] transition-colors truncate" style="color: #111827;">
                      {gift.name}
                      <span class="inline-block text-[8px] font-black text-rose-600 bg-rose-50 px-1 rounded uppercase tracking-wider ml-1">Xem</span>
                    </span>
                    <div class="gift-qty">
                      <span class="qty-label">Số lượng:</span>
                      <span class="qty-val">x{gift.qty}</span>
                    </div>
                  </div>
                </a>
              {:else}
                <div class="gift-item">
                  <div class="gift-thumb">
                    {#if gift.image}
                      <img
                        src={resolveMediaUrl(gift.image)}
                        alt={gift.name}
                        class="thumb-img"
                      />
                    {:else}
                      <div class="thumb-placeholder"><Sparkles size={16} /></div>
                    {/if}
                  </div>
                  <div class="gift-info">
                    <span class="gift-name">{gift.name}</span>
                    <div class="gift-qty">
                      <span class="qty-label">Số lượng:</span>
                      <span class="qty-val">x{gift.qty}</span>
                    </div>
                  </div>
                </div>
              {/if}
            {/each}
          </div>
        </div>
      </div>
    </div>
  {/if}

  <!-- CTAs -->
  <div class="cta-row">
    <button onclick={onAddToCart} class="add-to-cart-btn">
      <ShoppingCart size={20} />
      <span>Thêm vào giỏ hàng</span>
    </button>
    <button onclick={onBuyNow} class="buy-now-btn">Mua ngay</button>
  </div>
</div>

<style>
  .info-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding-top: 0.25rem;
  }

  .header {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
  }

  .mall-badge,
  .verified-badge {
    color: white;
    padding: 0.125rem 0.5rem !important;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.05em;
    position: relative;
    overflow: hidden;
    margin-top: 0.25rem;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    border-radius: 3px;
  }

  .mall-badge {
    background: linear-gradient(135deg, #b91c1c, #991b1b) !important;
    border: 1px solid rgba(253, 224, 71, 0.3) !important;
  }

  .verified-badge {
    background: linear-gradient(135deg, #0d9488, #0f766e) !important;
  }

  .shine-effect {
    position: absolute;
    inset: 0;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.3),
      transparent
    );
    transform: translateX(-100%);
    transition: transform 1s;
  }

  .mall-badge:hover .shine-effect {
    transform: translateX(100%);
  }

  .product-title {
    font-size: 20px;
    font-weight: 500;
    color: #111827;
    line-height: 1.5;
    margin: 0;
  }

  .stats-row {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    font-size: 14px;
    margin-bottom: 1.5rem;
  }

  .rating-box {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    color: #c2410c !important;
    border-bottom: 1px solid rgba(194, 65, 12, 0.2) !important;
    padding-bottom: 0.125rem;
  }

  .rating-value {
    font-weight: 700;
    border-bottom: 1px solid #c2410c !important;
  }

  .stars {
    display: flex;
    gap: 0.125rem;
    margin-left: 0.25rem;
  }

  .star-icon {
    width: 0.75rem;
    height: 0.75rem;
    fill: #d1d5db;
  }

  .star-icon.active {
    fill: #fbbf24;
  }

  .divider {
    width: 1px;
    height: 1rem;
    background: #e5e7eb;
  }

  .stat-btn {
    background: none;
    border: none;
    padding: 0;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    cursor: pointer;
  }

  .stat-value {
    font-weight: 700;
    border-bottom: 1px solid black;
  }

  .stat-label {
    color: #6b7280;
    font-weight: 500;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .report-btn {
    margin-left: auto;
    font-size: 13px;
    color: #9ca3af;
    background: none;
    border: none;
    cursor: pointer;
    transition: color 0.2s;
  }

  .report-btn:hover {
    color: #c2410c;
  }

  .price-bar {
    background: linear-gradient(95deg, #f0fdf4 0%, #fff7ed 100%) !important;
    border-left: 4px solid #0d9488 !important;
    padding: 0.85rem 1.25rem !important;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
    border-top: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    border-radius: 0 8px 8px 0;
  }

  .original-price-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.125rem;
  }

  .original-price {
    font-size: 14px;
    color: #9ca3af;
    text-decoration: line-through;
  }

  .save-badge {
    font-size: 11px;
    font-weight: 900;
    color: white !important;
    background: linear-gradient(135deg, #0d9488, #0f766e) !important;
    padding: 0.25rem 0.5rem !important;
    border-radius: 4px;
    box-shadow: 0 4px 6px -1px rgba(13, 148, 136, 0.2);
  }

  .sale-price {
    font-size: 34px !important;
    font-weight: 900 !important;
    color: #c2410c !important;
    letter-spacing: -0.05em !important;
  }

  .helen-intelligence {
    margin-top: 0.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .helen-header {
    display: flex;
    align-items: center;
    gap: 0.625rem;
  }

  .combo-pill {
    background: #0f172a;
    color: white;
    font-size: 8px;
    font-weight: 900;
    padding: 0.125rem 0.375rem;
    border-radius: 2px;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .helen-tag {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .helen-name {
    font-size: 8px;
    color: #3b82f6;
    font-family: monospace;
    font-weight: 900;
    font-weight: 900;
    letter-spacing: 0.2em;
  }

  .pulse-dot {
    width: 2px;
    height: 2px;
    background: #60a5fa;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .helen-body {
    padding-left: 1rem;
    border-left: 1px solid rgba(191, 219, 254, 0.4);
  }

  .advice-text {
    font-size: 12.5px;
    color: #64748b;
    font-weight: 500;
    line-height: 1.4;
    max-width: 580px;
    margin: 0;
  }

  .helen-verify-btn {
    margin-top: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: white;
    border: 1px solid #3b82f633;
    padding: 0.375rem 0.75rem;
    border-radius: 99px;
    color: #3b82f6;
    font-size: 11px;
    font-weight: 800;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 4px 12px #3b82f61a;
  }

  .helen-verify-btn:hover {
    background: #3b82f60d;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px #3b82f626;
  }

  .timer-box {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }

  .timer-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
  }

  .ping-dot {
    width: 6px;
    height: 6px;
    background: #c2410c;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .timer-label {
    font-size: 10px;
    font-weight: 900;
    color: #6b7280;
    font-weight: 900;
    letter-spacing: 0.2em;
    opacity: 0.8;
  }

  .countdown {
    display: flex;
    gap: 0.25rem;
    color: #1f2937;
    font-weight: 900;
    font-size: 17px;
    font-family: monospace;
  }

  .time-unit {
    background: rgba(229, 231, 235, 0.5);
    padding: 0.125rem 0.375rem;
    min-width: 30px;
    text-align: center;
    border-radius: 2px;
  }

  .time-sep {
    align-self: center;
    opacity: 0.3;
  }

  .section-row {
    padding: 0 1.25rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: flex-start;
  }

  .row-label {
    width: 110px;
    flex-shrink: 0;
    font-size: 14px;
    color: #6b7280;
    margin-top: 0.5rem;
  }

  .vouchers-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .voucher-ticket {
    position: relative;
    background: linear-gradient(135deg, #fff7ed, #fff1f2) !important;
    border: 1px dashed #fda4af !important;
    padding: 0.5rem 1rem 0.5rem 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 2px 8px rgba(253, 224, 71, 0.05);
  }

  .voucher-ticket.applied {
    border: 1.5px solid #e11d48 !important;
    background: #fff1f2 !important;
  }

  .ticket-notch {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 0.5rem;
    height: 0.5rem;
    background: white;
    border-radius: 50%;
    border: 1px solid #f3f4f6;
  }

  .ticket-notch.left {
    left: -0.25rem;
  }
  .ticket-notch.right {
    right: -0.25rem;
  }

  .ticket-divider {
    width: 1px;
    height: 1.5rem;
    border-left: 1px dashed rgba(238, 77, 45, 0.2);
    margin: 0 0.25rem;
  }

  .ticket-content {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    transform: translateX(4px);
  }

  .voucher-label {
    font-size: 12px;
    font-weight: 900;
    color: #e11d48 !important;
  }

  .voucher-sub {
    font-size: 9px;
    color: #9ca3af;
    font-weight: 700;
    font-weight: 700;
    margin-top: 0.25rem;
    letter-spacing: -0.025em;
  }

  .check-badge {
    position: absolute;
    top: -0.5rem;
    right: -0.5rem;
    background: #e11d48;
    color: white;
    border-radius: 50%;
    padding: 0.125rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  .check-icon {
    width: 0.75rem;
    height: 0.75rem;
  }

  .promo-row {
    margin-bottom: 1rem;
  }

  .shipping-info {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .ship-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .check-icon-green {
    width: 1.25rem;
    height: 1.25rem;
    color: #0d9488;
  }

  .ship-status {
    font-size: 14px;
    font-weight: 500;
    color: #1f2937;
  }

  .ship-details {
    font-size: 14px;
  }
  .ship-price {
    color: #0d9488;
    font-weight: 900;
  }
  .ship-desc {
    font-size: 12px;
    color: #9ca3af;
    margin-top: 0.25rem;
  }

  .options-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.625rem;
  }

  .option-btn {
    position: relative;
    min-width: 80px;
    height: 2.5rem;
    padding: 0 1rem;
    border: 1px solid #e5e7eb;
    background: white;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
  }

  .option-btn:hover {
    background: rgba(255, 238, 232, 0.2);
  }
  .option-btn.selected {
    border-color: #c2410c !important;
    color: #c2410c !important;
    box-shadow: inset 0 0 0 1px rgba(194, 65, 12, 0.1) !important;
  }

  .option-img {
    width: 1.5rem;
    height: 1.5rem;
    object-fit: cover;
    margin-right: 0.5rem;
    border: 1px solid #f3f4f6;
  }

  .selected-corner {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 0;
    height: 0;
    border-top: 12px solid transparent;
    border-right: 12px solid #c2410c !important;
  }

  .selected-check {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 0.625rem;
    height: 0.625rem;
    color: white;
  }

  .quantity-row {
    align-items: center;
    margin-bottom: 1rem;
  }

  .quantity-controls {
    display: flex;
    align-items: center;
    gap: 2rem;
  }

  .stepper {
    display: flex;
    align-items: center;
    border: 1px solid #f3f4f6;
    height: 2.25rem;
    background: white;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  .step-btn {
    width: 2.5rem;
    height: 100%;
    background: none;
    border: none;
    color: #d1d5db;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .step-btn:hover:not(:disabled) {
    background: #f9fafb;
    color: black;
  }
  .step-btn:active:not(:disabled) {
    background: #f3f4f6;
  }
  .step-btn:disabled {
    opacity: 0.2;
  }

  .qty-input {
    width: 3rem;
    height: 100%;
    text-align: center;
    border: none;
    border-left: 1px solid #f3f4f6;
    border-right: 1px solid #f3f4f6;
    font-size: 15px;
    font-weight: 900;
    color: #111827;
  }

  .stock-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }
  .stock-status-title {
    font-size: 12px;
    color: #9ca3af;
    font-weight: 900;
    font-style: italic;
    letter-spacing: -0.025em;
  }
  .stock-warning {
    font-size: 11px;
    font-weight: 700;
    color: #c2410c;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
  .ping-dot-red {
    width: 4px;
    height: 4px;
    background: #c2410c;
    border-radius: 50%;
    animation: pulse 1s infinite;
  }
  .stock-ok {
    font-size: 11px;
    color: #0d9488;
    font-weight: 900;
    font-style: italic;
  }

  .gifts-section {
    padding: 0 1.25rem;
    margin-bottom: 1.5rem;
  }

  .gifts-card {
    background: linear-gradient(135deg, #f0fdf4, white) !important;
    border: 2px solid rgba(13, 148, 136, 0.15) !important;
    padding: 1.25rem;
    display: flex;
    gap: 1rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(13, 148, 136, 0.05) !important;
    border-radius: 8px;
  }

  .gift-icon-box {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    background: linear-gradient(135deg, #0d9488, #0f766e) !important;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    box-shadow: 0 10px 15px -3px rgba(13, 148, 136, 0.3) !important;
    flex-shrink: 0;
    margin-top: 0.25rem;
  }

  .gifts-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .gifts-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .gifts-title {
    font-size: 14px;
    font-weight: 900;
    letter-spacing: 0.1em;
    color: #1f2937;
    margin: 0;
  }
  .combo-tag {
    background: linear-gradient(135deg, #0d9488, #0f766e) !important;
    color: white;
    font-size: 10px;
    font-weight: 900;
    padding: 0.25rem 0.625rem;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    gap: 0.375rem;
    box-shadow: 0 4px 6px -1px rgba(13, 148, 136, 0.2) !important;
  }

  .gifts-list {
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
  }
  .gift-item {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(8px);
    padding: 0.5rem;
    border: 1px solid rgba(13, 148, 136, 0.05);
    display: flex;
    gap: 0.75rem;
    transition: all 0.2s;
  }
  .gift-item:hover {
    border-color: rgba(13, 148, 136, 0.2);
  }
  .gift-thumb {
    width: 3rem;
    height: 3rem;
    border-radius: 2px;
    overflow: hidden;
    background: #f9fafb;
    border: 1px solid #f3f4f6;
    flex-shrink: 0;
  }
  .gift-info {
    display: flex;
    flex-direction: column;
  }
  .gift-name {
    font-size: 13px;
    font-weight: 700;
    color: #111827;
    line-height: 1.25;
  }
  .gift-qty {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.125rem;
  }
  .qty-label {
    font-size: 11px;
    color: #6b7280;
    font-weight: 500;
  }
  .qty-val {
    font-size: 11px;
    color: #0d9488 !important;
    font-weight: 900;
    font-style: italic;
  }

  .cta-row {
    padding: 0 1.25rem;
    display: flex;
    gap: 1rem;
    margin-top: auto;
    padding-bottom: 1rem;
  }
  .add-to-cart-btn {
    height: 3.25rem;
    min-width: 210px;
    border: 2px solid #0d9488 !important;
    background: rgba(204, 251, 241, 0.4) !important;
    color: #0f766e !important;
    font-size: 14.5px !important;
    font-weight: 900 !important;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.625rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1) !important;
    border-radius: 6px !important;
    letter-spacing: 0.025em;
  }

  .add-to-cart-btn:hover {
    background: rgba(204, 251, 241, 0.8) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.15) !important;
  }

  .buy-now-btn {
    height: 3.25rem;
    min-width: 180px;
    background: linear-gradient(135deg, #ea580c, #c2410c) !important;
    color: white !important;
    font-size: 14.5px !important;
    font-weight: 900 !important;
    border: none !important;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1) !important;
    box-shadow: 0 8px 25px rgba(234, 88, 12, 0.25) !important;
    border-radius: 6px !important;
    letter-spacing: 0.05em;
  }

  .buy-now-btn:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 12px 30px rgba(234, 88, 12, 0.4) !important;
    filter: brightness(1.05) !important;
  }

  @keyframes pulse {
    0% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.5;
      transform: scale(1.2);
    }
    100% {
      opacity: 1;
      transform: scale(1);
    }
  }
</style>
