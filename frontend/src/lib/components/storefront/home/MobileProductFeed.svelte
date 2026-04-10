<!-- MobileProductFeed.svelte -->
<!-- Product filter tabs + 2-column waterfall product grid -->
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
  }

  interface Props {
    products: Product[];
  }

  let { products }: Props = $props();

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
  {#if products && products.length > 0}
    {#each products as product (product.id)}
      {@const discountPct = getDiscountPct(product)}
      <button
        class="product-card"
        onclick={() => navigateProduct(product)}
      >
        <div class="product-img-wrap">
          {#if discountPct > 0}
            <span class="product-discount-badge">-{discountPct}%</span>
          {/if}
          <img
            src={product.image}
            alt={product.name}
            class="product-img"
            loading="lazy"
          />
          <div class="product-watermark">Micsmo</div>
        </div>
        <div class="product-info">
          <p class="product-name">{product.name}</p>
          <div class="product-price-row">
            <span class="product-price">
              <span class="product-price-unit">đ</span>{product.price.toLocaleString('vi-VN')}
            </span>
            {#if product.sales}
              <span class="product-sales">Đã bán {product.sales.toLocaleString()}</span>
            {/if}
          </div>
          {#if product.originalPrice}
            <span class="product-original-price">đ{product.originalPrice.toLocaleString('vi-VN')}</span>
          {/if}
          <div class="product-tags">
            <span class="tag-freeship">FREESHIP</span>
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
    top: var(--mobile-header-total, 126px); /* hérite du parent .mobile-home-root */
    background: #ffffff;
    display: flex;
    align-items: stretch;
    border-bottom: 1px solid #f0f0f0;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  .tab-bar::-webkit-scrollbar { display: none; }

  /* Tab items general */
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

  /* Specific styles for text tabs */
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

  /* Mall Pill Style (TikTok aesthetic) */
  .tab-item--pill {
    padding: 10px 6px; /* slightly tighter padding for pills to fit together */
  }

  .tab-pill-wrap {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    z-index: 1;
  }

  /* The Cyan/Pink shadow effect */
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
    box-shadow: 0 0 0 0.5px #111; /* subtle cover for inner seam */
  }

  /* Voucher style */
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
    color: #00b060; /* Vibrant green */
    letter-spacing: 0.02em;
  }

  /* Indicator line for active text/voucher tabs */
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
    background: #f5f5f5;
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
    transition: opacity 0.15s;
  }
  .product-card:active { opacity: 0.85; }

  .product-img-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
    overflow: hidden;
    background: #f0f0f0;
  }

  .product-discount-badge {
    position: absolute;
    top: 7px;
    left: 7px;
    background: #ee4d2d;
    color: #fff;
    font-size: 10px;
    font-weight: 900;
    padding: 2px 5px;
    border-radius: 3px;
    z-index: 2;
  }

  .product-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.4s ease;
  }
  .product-card:hover .product-img { transform: scale(1.04); }

  .product-watermark {
    position: absolute;
    bottom: 7px;
    left: 7px;
    background: rgba(0, 0, 0, 0.45);
    color: #fff;
    font-size: 8px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 2px 5px;
    border-radius: 2px;
    z-index: 2;
  }

  .product-info {
    padding: 8px 10px 10px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .product-name {
    font-size: 12px;
    color: #333;
    font-weight: 500;
    line-height: 1.4;
    margin: 0;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .product-price-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 2px;
  }

  .product-price {
    font-size: 15px;
    font-weight: 900;
    color: #ee4d2d;
    line-height: 1;
  }

  .product-price-unit {
    font-size: 11px;
  }

  .product-sales {
    font-size: 10px;
    color: #aaa;
  }

  .product-original-price {
    font-size: 11px;
    color: #ccc;
    text-decoration: line-through;
    line-height: 1;
  }

  .product-tags {
    margin-top: 4px;
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .tag-freeship {
    font-size: 9px;
    font-weight: 700;
    color: #ee4d2d;
    border: 1px solid #ee4d2d;
    padding: 1px 5px;
    border-radius: 2px;
    line-height: 1.4;
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
