<script lang="ts">
  import { goto } from '$app/navigation';
  import { trimProductName, formatCurrency } from '$lib/utils/format';
  import type { Product } from '$lib/types';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  interface Props {
    product: Product;
    index: number;
  }

  let { product, index }: Props = $props();

  const hasDiscount = $derived(!!product.discountPrice && product.discountPrice > 0 && product.discountPrice < product.price);
  const finalPrice = $derived(hasDiscount ? product.discountPrice! : product.price);
  const oldPrice = $derived(hasDiscount ? product.price : 0);
  const discountPercent = $derived(hasDiscount ? Math.round((1 - product.discountPrice! / product.price) * 100) : 0);

  // Elite V2.2: Universal Sanitization
  const cleanName = $derived(trimProductName(product.name));
  const soldStr = $derived(product.orderCountText || product.order_count_text || product.metadata?.reviews_count_text || (product.orderCount || product.order_count ? `${product.orderCount || product.order_count}` : ''));

  // R00 Compliant: Chỉ dùng real DB data — không fake/seed
  const ratingDisplay = $derived(
    product.metadata?.reviews_trust_score || product.metadata?.rating || null
  );
  const reviewCountDisplay = $derived(product.metadata?.reviews_count_text || null);

  function navigateProduct(): void {
    goto(`/${product.slug || product.id}`);
  }
</script>

<button class="product-card" onclick={navigateProduct}>
  <div class="product-img-wrap">
    <!-- Image -->
    <img
      src={product.images?.[0] || ''}
      alt={product.name}
      class="product-img"
      loading="lazy"
    />

    <!-- Stickers/Badges -->
    {#if hasDiscount}
      <div class="discount-sticker">
        <span class="d-label">SALE</span>
        <div class="d-num-row">
          <span class="d-minus">−</span><span class="d-num">{discountPercent}</span><span class="d-pct">%</span>
        </div>
      </div>
    {/if}

    <!-- Bottom Overlays -->
    <div class="img-overlay-row">
      {#if product.metadata?.is_freeship !== false}
        <div class="overlay-badge freeship">
          <span class="badge-text">FREESHIP</span>
          <span class="badge-sub">XTRA</span>
        </div>
      {/if}
      
      {#if product.metadata?.reviews_trust_score}
        <div class="overlay-rating">
          <span class="star">★</span>
          <span class="rating-val">{product.metadata.reviews_trust_score}</span>
        </div>
      {/if}
    </div>
  </div>

  <div class="product-info">
    <h3 class="product-name">{cleanName}</h3>

    <!-- 🌟 Rating - chỉ hiện khi có real DB data -->
    {#if ratingDisplay}
      <div class="product-rating">
        <span class="rating-stars">★★★★★</span>
        <span class="rating-score">{ratingDisplay}</span>
        {#if reviewCountDisplay}
          <span class="rating-sep">&middot;</span>
          <span class="rating-count">{reviewCountDisplay} đánh giá</span>
        {/if}
      </div>
    {/if}

    <div class="price-section">
      <div class="price-row">
        <span class="current-price">
          {formatCurrency(finalPrice)}
        </span>
        {#if soldStr}
          <span class="sold-count">
            {soldStr.includes('Đã bán') ? soldStr : `Đã bán ${soldStr}`}
          </span>
        {/if}
      </div>
    </div>

    <div class="product-footer">
      {#if product.metadata?.location}
        <div class="location-badge">
          {product.metadata.location}
        </div>
      {/if}
    </div>
  </div>
</button>

<style>
  .product-card {
    display: flex;
    flex-direction: column;
    background: #fff;
    border: none;
    cursor: pointer;
    text-align: left;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s cubic-bezier(0.18, 0.89, 0.32, 1.28);
    padding: 0;
  }
  .product-card:active { transform: scale(0.97); opacity: 0.9; }

  .product-img-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
    background: #f8f8f8;
    overflow: hidden;
  }

  .product-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  /* ⚡ Viral FOMO Discount Badge */
  @keyframes fomo-glow {
    0%, 100% { box-shadow: 0 0 8px rgba(238,77,45,0.5), 0 2px 6px rgba(238,77,45,0.3); }
    50%       { box-shadow: 0 0 20px rgba(238,77,45,0.85), 0 2px 14px rgba(238,77,45,0.55); }
  }
  .discount-sticker {
    position: absolute;
    top: 0;
    right: 0;
    background: linear-gradient(150deg, #ee4d2d 0%, #ff6b35 100%);
    color: #fff;
    padding: 5px 7px 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-radius: 0 0 0 12px;
    z-index: var(--z-product-card-content);
    animation: fomo-glow 2s infinite ease-in-out;
    min-width: 40px;
    box-shadow: 0 2px 8px rgba(238,77,45,0.45);
  }
  .d-label {
    font-size: 7px;
    font-weight: 900;
    letter-spacing: 0.12em;
    line-height: 1;
    opacity: 0.85;
  }
  .d-num-row {
    display: flex;
    align-items: flex-start;
    line-height: 1;
    margin-top: 1px;
  }
  .d-minus { font-size: 12px; font-weight: 900; margin-top: 1px; }
  .d-num   { font-size: 20px; font-weight: 950; letter-spacing: -0.05em; line-height: 0.9; }
  .d-pct   { font-size: 10px; font-weight: 900; margin-top: 2px; }

  .img-overlay-row {
    position: absolute;
    bottom: 6px;
    left: 6px;
    right: 6px;
    display: flex;
    align-items: flex-end;
    gap: 6px;
  }

  .overlay-badge {
    padding: 2px 6px;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    line-height: 1;
  }
  .overlay-badge.freeship {
    background: #00c49a;
    color: #fff;
  }
  .badge-text { font-size: 8px; font-weight: 900; }
  .badge-sub { font-size: 6px; font-weight: 600; }

  .overlay-rating {
    margin-left: auto;
    background: rgba(0, 0, 0, 0.7);
    color: #fff;
    padding: 2px 6px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 2px;
    font-size: 10px;
    font-weight: 800;
  }
  .star { color: #ffd839; font-size: 11px; }

  .product-info {
    padding: 10px 5px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .product-name {
    font-size: 13px;
    color: #333;
    font-weight: 600;
    line-height: 1.4;
    height: 2.8em;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    margin: 0;
  }

  .price-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 4px;
  }

  .current-price {
    font-size: 16px;
    font-weight: 900;
    color: #ee4d2d;
  }
  .symbol { font-size: 12px; text-decoration: underline; font-weight: 900; }



  .product-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 4px;
  }

  .sold-count {
    font-size: 11px;
    color: #888;
    font-weight: 500;
  }

  .location-badge {
    font-size: 10px;
    color: #999;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
  }
  .pulse-soft { animation: pulse 1.5s infinite ease-in-out; }

  /* 🌟 Compact Viral Rating */
  .product-rating {
    display: flex;
    align-items: center;
    gap: 3px;
    margin-top: -2px;
    margin-bottom: 2px;
  }
  .rating-stars {
    font-size: 10px;
    color: #FF5722;
    letter-spacing: -0.1em;
    line-height: 1;
  }
  .rating-score {
    font-size: 10px;
    font-weight: 900;
    color: #FF5722;
    line-height: 1;
  }
  .rating-sep {
    font-size: 8px;
    color: #ccc;
    font-weight: 700;
  }
  .rating-count {
    font-size: 9px;
    color: #aaa;
    font-weight: 600;
    line-height: 1;
  }
</style>
