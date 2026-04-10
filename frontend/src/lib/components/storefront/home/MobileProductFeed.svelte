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

  interface Category {
    id: string;
    name: string;
    slug: string;
  }

  interface Props {
    products: Product[];
    categories?: Category[];
  }

  let { products, categories = [] }: Props = $props();

  // Neon palettes for "Elite 2.2" vibrancy with unique backgrounds
  const palettes = [
    { bg: 'linear-gradient(135deg, #25f4ee, #00c49a)', text: '#004d40', shadow: '#25f4ee' }, // Teal
    { bg: 'linear-gradient(135deg, #7d2ae8, #ff00c1)', text: '#ffffff', shadow: '#7d2ae8' }, // Purple-Magenta
    { bg: 'linear-gradient(135deg, #ffd6a5, #ffadad)', text: '#800000', shadow: '#ffadad' }, // Soft Peach
    { bg: 'linear-gradient(135deg, #00ff87, #60efff)', text: '#004d40', shadow: '#00ff87' }, // Mint
    { bg: 'linear-gradient(135deg, #bdb2ff, #7d2ae8)', text: '#ffffff', shadow: '#bdb2ff' }, // Violet
    { bg: 'linear-gradient(135deg, #60efff, #0061ff)', text: '#ffffff', shadow: '#0061ff' }, // Ocean
    { bg: 'linear-gradient(135deg, #ff2b54, #ff00c1)', text: '#ffffff', shadow: '#ff2b54' }  // Flashy Red
  ];

  // Combine static Elite tabs with dynamic DB categories
  const tabs = $derived([
    { type: 'text', label: 'Tất cả', style: palettes[0] },
    ...categories.map((cat, i) => {
      const isHot = cat.name.toLowerCase().includes('kem dưỡng');
      // Special "Hot" style for Kem dưỡng
      const style = isHot 
        ? { bg: 'linear-gradient(135deg, #ffbe0b, #fb5607)', text: '#ffffff', shadow: '#ffbe0b' }
        : palettes[(i + 1) % palettes.length];
      return { 
        type: 'mall-pill', 
        label: cat.name, 
        slug: cat.slug,
        isHot,
        style
      };
    })
  ]);

  // Mock data enhancement for preview (Elite 2.2)
  const displayProducts = $derived(
    products.map((p, i) => ({
      ...p,
      // Đảm bảo luôn có giá gốc cao hơn giá KM để hiện % giảm giá và gạch ngang
      originalPrice: p.originalPrice || Math.round(p.price * 1.35), 
      rating: 4.5 + (i % 5) * 0.1,
      isFlashSale: i % 2 === 0,
      isFreeship: true,
      isCOD: i % 3 === 0,
      isXtraFreeship: true,
      extraLabel: i % 2 === 0 ? 'lên đến 14%' : 'SIÊU KM',
      sales: p.sales || (100 + i * 50)
    }))
  );
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
      class="tab-item {activeTab === i ? 'tab-item--active' : ''} {tab.type === 'mall-pill' ? 'tab-item--pill' : ''}"
      style="--pill-bg: {tab.style?.bg}; --pill-txt: {tab.style?.text}; --pill-glow: {tab.style?.shadow};"
      onclick={() => activeTab = i}
    >
      {#if tab.type === 'text'}
        <span class="tab-text" style={activeTab === i ? `color: ${tab.style?.text}` : ''}>{tab.label}</span>
      {:else if tab.type === 'mall-pill'}
        <div class="tab-pill-wrap {tab.isHot ? 'tab-pill-wrap--hot' : ''}">
          <span class="tab-pill" style="background: var(--pill-bg); color: var(--pill-txt);">{tab.label}</span>
          {#if tab.isHot}
            <span class="hot-tag">HOT</span>
          {/if}
        </div>
      {/if}

      {#if activeTab === i && tab.type === 'text'}
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
          <!-- High FOMO Discount Badge (Top-Left) -->
          {#if discountPct > 0}
            <div class="badge-fomo-discount pulse-fomo">
              <span class="fomo-label">GIẢM</span>
              <span class="fomo-percent">-{discountPct}%</span>
            </div>
          {/if}

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
            <!-- FOMO Rating instead of QC -->
            <div class="overlay-rating">
              <span class="star-mini">★</span>
              <span class="rating-num">{product.rating}</span>
            </div>
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
              <!-- Intuitive Voucher Ticket Icon -->
              <div class="voucher-ticket">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20 12V6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a3 3 0 010 6v2a2 2 0 002 2h12a2 2 0 002-2v-2a3 3 0 010-6zM9 13a2 2 0 112-2 2 2 0 01-2 2zm6 0a2 2 0 112-2 2 2 0 01-2 2z" />
                </svg>
                <span class="ticket-perc">%</span>
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
    padding: 12px 2px; /* Set to minimum */
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
    padding: 10px 1px; /* Maximum density */
  }

  .tab-pill-wrap {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    z-index: 1;
  }

  .tab-pill {
    position: relative;
    font-size: 12px;
    font-weight: 800;
    padding: 4px 8px; /* Reduced from 6px 14px */
    border-radius: 12px;
    white-space: nowrap;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
  }

  .hot-tag {
    position: absolute;
    top: -8px;
    right: -6px;
    background: #ff2b54;
    color: #fff;
    font-size: 7px;
    font-weight: 950;
    padding: 1px 3px;
    border-radius: 4px;
    z-index: 10;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    animation: bounce-hot 1s infinite alternate;
  }

  @keyframes bounce-hot {
    from { transform: translateY(0) scale(1); }
    to { transform: translateY(-2px) scale(1.1); }
  }

  .tab-indicator {
    position: absolute;
    bottom: 4px;
    left: 12px;
    right: 12px;
    height: 3px;
    background: #222;
    border-radius: 4px 4px 4px 4px;
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

  .badge-fomo-discount {
    position: absolute;
    top: 0;
    left: 0;
    background: linear-gradient(135deg, #ffd839, #ffbe0b);
    color: #ff2b54;
    padding: 4px 8px;
    border-radius: 0 0 12px 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    z-index: 10;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.15);
  }

  .fomo-label {
    font-size: 7px;
    font-weight: 900;
    line-height: 1;
    margin-bottom: 1px;
    letter-spacing: 0.05em;
  }

  .fomo-percent {
    font-size: 13px;
    font-weight: 950;
    line-height: 1;
  }

  @keyframes pulse-fomo {
    0%, 100% { transform: scale(1); filter: brightness(1); }
    50% { transform: scale(1.05); filter: brightness(1.1); }
  }
  .pulse-fomo {
    animation: pulse-fomo 1.2s infinite ease-in-out;
  }

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

  .overlay-rating {
    margin-left: auto;
    background: rgba(0, 0, 0, 0.55);
    color: #ffd839; /* Yellow star color text */
    font-size: 11px;
    font-weight: 900;
    padding: 2px 6px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 2px;
    backdrop-filter: blur(2px);
    border: 0.5px solid rgba(255,255,255,0.2);
  }
  .star-mini { font-size: 10px; }
  .rating-num { color: #fff; }

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

  .voucher-ticket {
    margin-left: auto;
    width: 24px;
    height: 18px;
    background: #fff;
    color: #ff2b54;
    border: 1px dashed #ff2b54;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    padding: 0 2px;
  }
  .voucher-ticket svg { width: 12px; height: 12px; }
  .ticket-perc { font-size: 9px; font-weight: 900; margin-left: 1px; }

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
