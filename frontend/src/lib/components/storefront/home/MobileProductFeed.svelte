<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';

  interface Product {
    id: string;
    name: string;
    price: number;
    image: string;
    sales?: number;
    originalPrice?: number;
    slug?: string;
    rating?: number;
    isFlashSale?: boolean;
    isFreeship?: boolean;
    isCOD?: boolean;
    isXtraFreeship?: boolean;
    extraLabel?: string;
  }

  interface Props {
    products: Product[];
  }

  let { products }: Props = $props();

  // Mock data enhancement for preview (Elite 2.2)
  const displayProducts = $derived(
    products.map((p, i) => ({
      ...p,
      rating: 4.5 + (i % 5) * 0.1,
      isFlashSale: i % 2 === 0,
      isFreeship: true,
      isCOD: i % 3 === 0,
      isXtraFreeship: true,
      extraLabel: i % 2 === 0 ? 'lên đến 14%' : 'SIÊU KM',
      sales: p.sales || (100 + i * 50)
    }))
  );

  const tabs = [
    { type: 'text', label: 'Tất cả' },
    { type: 'mall-pill', label: 'Mall Day' },
    { type: 'mall-pill', label: 'Mall' },
    { type: 'voucher', line1: 'VOUCHER', line2: 'EXTRA %' },
    { type: 'text', label: 'Quần áo nữ' }
  ];
  let activeTab = $state(0);

  function navigateProduct(product: Product): void {
    goto(`/${product.slug || slugify(product.name)}`);
  }

  function getDiscountPct(product: Product): number {
    if (!product.originalPrice || product.originalPrice <= product.price) return 0;
    return Math.round((1 - product.price / product.originalPrice) * 100);
  }
</script>

<!-- Tab sub-header (sticky below main header) -->
<div
  class="tab-bar"
  style="z-index: {Z_INDEX_CLIENT.SURFACE};"
>
  {#each tabs as tab, i}
    <button
      class="tab-item {activeTab === i ? 'tab-item--active' : ''} {tab.type === 'mall-pill' ? 'tab-item--pill' : ''} {tab.type === 'voucher' ? 'tab-item--voucher' : ''}"
      onclick={() => activeTab = i}
    >
      {#if tab.type === 'text'}
        <span class="tab-text">{tab.label}</span>
      {:else if tab.type === 'mall-pill'}
        <span class="tab-pill-wrap">
          <span class="tab-pill">{tab.label}</span>
        </span>
      {:else if tab.type === 'voucher'}
        <div class="tab-voucher-col">
          <span class="tab-voucher-l1">{tab.line1}</span>
          <span class="tab-voucher-l2">{tab.line2}</span>
        </div>
      {/if}

      {#if activeTab === i && (tab.type === 'text' || tab.type === 'voucher')}
        <div class="tab-indicator"></div>
      {/if}
    </button>
  {/each}
</div>

<!-- 2-column product grid -->
<div class="product-grid">
  {#if displayProducts && displayProducts.length > 0}
    {#each displayProducts as product (product.id)}
      {@const discountPct = getDiscountPct(product)}
      <button
        class="product-card"
        onclick={() => navigateProduct(product)}
      >
        <div class="product-img-wrap">
          <!-- Discount Badge Top-Right -->
          {#if discountPct > 0}
            <span class="badge-discount-float">-{discountPct}%</span>
          {/if}

          <!-- Custom Embedrone Badge (Decor only) -->
          <div class="badge-brand-decor">
            <svg viewBox="0 0 100 100" class="decor-svg">
              <path d="M50 0 L100 50 L50 100 L0 50 Z" fill="#4a185b" />
              <text x="50" y="55" font-size="20" fill="white" text-anchor="middle" font-weight="bold">Elite</text>
            </svg>
          </div>

          <img
            src={product.image}
            alt={product.name}
            class="product-img"
            loading="lazy"
          />

          <!-- Bottom Overlays (XTRA / EXTRA) -->
          <div class="img-overlay-row">
            {#if product.isXtraFreeship}
              <div class="overlay-badge overlay-badge--xtra">
                <span class="xtra-top">XTRA</span>
                <span class="xtra-bottom">Freeship*</span>
              </div>
            {/if}
            {#if product.extraLabel}
              <div class="overlay-badge overlay-badge--extra">
                <span class="extra-top">EXTRA</span>
                <span class="extra-bottom">{product.extraLabel}</span>
              </div>
            {/if}
            <div class="overlay-qc">QC</div>
          </div>
        </div>

        <div class="product-info">
          <p class="product-name">{product.name}</p>
          
          <div class="price-section">
            <div class="price-row">
              <span class="current-price">
                {product.price.toLocaleString('vi-VN')}<span class="symbol">đ</span>
              </span>
              {#if product.originalPrice}
                <span class="old-price">{product.originalPrice.toLocaleString('vi-VN')}đ</span>
              {/if}
              <!-- Voucher Icon -->
              <div class="voucher-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                   <path d="M15 5l-3 3-3-3m6 14l-3-3-3 3M5 15h14M5 9h14" />
                </svg>
              </div>
            </div>
          </div>

          <div class="utility-badges">
            {#if product.isFlashSale}
              <span class="badge-flash">⚡ Flash Sale</span>
            {/if}
            {#if product.isFreeship}
              <span class="badge-freeship">🚛 Freeship</span>
            {/if}
            {#if product.isCOD}
              <span class="badge-cod">COD</span>
            {/if}
          </div>

          <div class="product-footer">
            {#if product.rating}
              <div class="rating">
                <span class="star">★</span>
                <span class="rating-val">{product.rating}</span>
                <span class="sep">|</span>
              </div>
            {/if}
            <span class="sold-count">Đã bán {product.sales?.toLocaleString()}</span>
          </div>
        </div>
      </button>
    {/each}
  {:else}
    <!-- Skeleton loader while products load -->
    {#each Array.from({ length: 6 }) as _}
      <div class="product-skeleton">
        <div class="skeleton-img"></div>
        <div class="skeleton-body">
          <div class="skeleton-line skeleton-line--wide"></div>
          <div class="skeleton-line skeleton-line--medium"></div>
          <div class="skeleton-line skeleton-line--narrow"></div>
        </div>
      </div>
    {/each}
  {/if}
</div>

<style>
  /* Tab Bar */
  .tab-bar {
    position: sticky;
    top: var(--mobile-header-total, 126px);
    background: #ffffff;
    display: flex;
    align-items: stretch;
    border-bottom: 1px solid #f0f0f0;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  .tab-bar::-webkit-scrollbar { display: none; }

  .tab-item {
    position: relative;
    flex-shrink: 0;
    padding: 12px 12px;
    background: none;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .tab-text {
    font-size: 15px;
    font-weight: 500;
    color: #444;
    white-space: nowrap;
    transition: color 0.2s;
  }

  .tab-item--active .tab-text {
    color: #111;
    font-weight: 700;
  }

  .tab-item--pill {
    padding: 10px 6px;
  }

  .tab-pill-wrap {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    z-index: 1;
  }

  .tab-pill-wrap::before {
    content: '';
    position: absolute;
    inset: 0;
    background: #25f4ee;
    border-radius: 8px;
    transform: translateX(-1.5px);
    z-index: -2;
  }
  .tab-pill-wrap::after {
    content: '';
    position: absolute;
    inset: 0;
    background: #fe2c55;
    border-radius: 8px;
    transform: translateX(1.5px);
    z-index: -1;
  }

  .tab-pill {
    background: #111;
    color: #fff;
    font-size: 11px;
    font-weight: 800;
    padding: 3px 6px;
    border-radius: 8px;
    white-space: nowrap;
    box-shadow: 0 0 0 0.5px #111;
  }

  .tab-item--voucher {
    padding: 8px 12px;
  }
  
  .tab-voucher-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    line-height: 1.1;
  }

  .tab-voucher-l1 {
    font-size: 10px;
    font-weight: 900;
    color: #111;
    letter-spacing: 0.02em;
  }

  .tab-voucher-l2 {
    font-size: 10px;
    font-weight: 900;
    color: #00b060;
    letter-spacing: 0.02em;
  }

  .tab-indicator {
    position: absolute;
    bottom: 0;
    left: 12px;
    right: 12px;
    height: 3px;
    background: #222;
    border-radius: 4px 4px 0 0;
  }

  /* Product Grid */
  .product-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 3px;
    padding: 3px;
    background: #f1f3f4;
  }

  /* Product Card */
  .product-card {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border: none;
    cursor: pointer;
    padding: 0;
    text-align: left;
    border-radius: 4px;
    overflow: hidden;
    transition: transform 0.2s cubic-bezier(0.18, 0.89, 0.32, 1.28), opacity 0.15s;
  }
  .product-card:active { opacity: 0.85; transform: scale(0.98); }

  .product-img-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
    overflow: hidden;
    background: #f0f0f0;
  }

  .badge-discount-float {
    position: absolute;
    top: 0;
    right: 0;
    background: #ff2b54;
    color: #fff;
    font-size: 12px;
    font-weight: 900;
    padding: 4px 6px;
    border-radius: 0 0 0 10px;
    z-index: 5;
  }

  .badge-brand-decor {
    position: absolute;
    top: 8px;
    left: 8px;
    width: 40px;
    height: 40px;
    z-index: 5;
    opacity: 0.9;
  }
  .decor-svg { width: 100%; height: 100%; }

  .product-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  /* Bottom Image Overlays */
  .img-overlay-row {
    position: absolute;
    bottom: 0px;
    left: 0;
    right: 0;
    display: flex;
    align-items: flex-end;
    padding: 4px;
    gap: 0;
  }

  .overlay-badge {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2px 6px;
    line-height: 1;
    border-radius: 4px;
    transform: scale(0.85);
    transform-origin: left bottom;
  }

  .overlay-badge--xtra {
    background: #00c49a;
    color: #fff;
    border-radius: 4px 4px 0 0;
  }
  .xtra-top { font-size: 9px; font-weight: 900; }
  .xtra-bottom { font-size: 7px; font-weight: 600; }

  .overlay-badge--extra {
    background: #ff2b54;
    color: #fff;
    margin-left: -5px; /* Slight overlap */
    border-radius: 4px 4px 4px 0;
    z-index: 2;
  }
  .extra-top { font-size: 8px; font-weight: 900; }
  .extra-bottom { font-size: 7px; font-weight: 600; white-space: nowrap; }

  .overlay-qc {
    margin-left: auto;
    background: rgba(0, 0, 0, 0.4);
    color: #fff;
    font-size: 10px;
    font-weight: 500;
    padding: 1px 4px;
    border-radius: 2px;
    opacity: 0.8;
  }

  .product-info {
    padding: 8px 6px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .product-name {
    font-size: 13px;
    color: #222;
    font-weight: 600;
    line-height: 1.3;
    margin: 0;
    height: 2.6em; /* fixed height for 2 lines */
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .price-section {
    margin-top: 2px;
  }

  .price-row {
    display: flex;
    align-items: baseline;
    gap: 4px;
    flex-wrap: wrap;
  }

  .current-price {
    font-size: 16px;
    font-weight: 900;
    color: #ff2b54;
    line-height: 1;
  }
  .current-price .symbol { font-size: 12px; margin-left: 1px; text-decoration: underline; }

  .old-price {
    font-size: 10px;
    color: #999;
    text-decoration: line-through;
    opacity: 0.8;
  }

  .voucher-icon {
    margin-left: auto;
    width: 20px;
    height: 20px;
    color: #ff2b54;
    border: 1px solid currentColor;
    border-radius: 4px;
    padding: 2px;
  }

  .utility-badges {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    margin: 2px 0;
  }

  .badge-flash {
    background: #fff0f3;
    color: #ff2b54;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .badge-freeship {
    background: #e6f7f4;
    color: #00c49a;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .badge-cod {
    background: #fff9e6;
    color: #ffb800;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .product-footer {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 2px;
  }

  .rating {
    display: flex;
    align-items: center;
    gap: 2px;
  }
  .star { color: #ffb800; font-size: 11px; }
  .rating-val { font-size: 11px; font-weight: 700; color: #555; }
  .sep { color: #ddd; font-size: 10px; margin: 0 1px; }

  .sold-count {
    font-size: 11px;
    color: #888;
    font-weight: 500;
  }

  /* Skeleton */
  .product-skeleton {
    background: #fff;
    border-radius: 4px;
    overflow: hidden;
  }

  .skeleton-img {
    width: 100%;
    aspect-ratio: 1 / 1;
    background: #f0f0f0;
    animation: pulse 1.5s ease-in-out infinite;
  }

  .skeleton-body {
    padding: 8px 10px 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .skeleton-line {
    height: 10px;
    background: #f0f0f0;
    border-radius: 4px;
    animation: pulse 1.5s ease-in-out infinite;
  }

  .skeleton-line--wide   { width: 85%; }
  .skeleton-line--medium { width: 60%; }
  .skeleton-line--narrow { width: 40%; }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.45; }
  }
</style>
