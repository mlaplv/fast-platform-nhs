<script lang="ts">
  import { goto } from '$app/navigation';
  import type { Product } from '$lib/types';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';

  interface Props {
    product: Product;
    index: number;
  }

  let { product, index }: Props = $props();

  const hasDiscount = $derived(!!product.discountPrice && product.discountPrice > 0 && product.discountPrice < product.price);
  const finalPrice = $derived(hasDiscount ? product.discountPrice! : product.price);
  const oldPrice = $derived(hasDiscount ? product.price : 0);
  const discountPercent = $derived(hasDiscount ? Math.round((1 - product.discountPrice! / product.price) * 100) : 0);

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
      <div class="discount-sticker pulse-soft">
        <span class="discount-label">GIẢM</span>
        <span class="discount-percent">{discountPercent}%</span>
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
    <h3 class="product-name">{product.name}</h3>

    <div class="price-section">
      <div class="price-row">
        <span class="current-price">
          {finalPrice.toLocaleString('vi-VN')}<span class="symbol">đ</span>
        </span>
        {#if oldPrice > 0}
          <span class="old-price">{oldPrice.toLocaleString('vi-VN')}đ</span>
        {/if}
      </div>
    </div>

    <div class="product-footer">
      <span class="sold-count">
        {product.metadata?.reviews_count_text || '2.140+ Lượt mua'}
      </span>
      <div class="location-badge">
        Hà Nội
      </div>
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

  .discount-sticker {
    position: absolute;
    top: 0;
    right: 0;
    background: linear-gradient(135deg, #ffd839, #ffbe0b);
    color: #ff2b54;
    padding: 4px 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    border-radius: 0 0 0 12px;
    z-index: 5;
  }
  .discount-label { font-size: 8px; font-weight: 900; line-height: 1; }
  .discount-percent { font-size: 13px; font-weight: 950; line-height: 1; }

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
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    padding: 2px 6px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 2px;
    font-size: 10px;
    font-weight: 800;
    backdrop-filter: blur(4px);
  }
  .star { color: #ffd839; font-size: 11px; }

  .product-info {
    padding: 10px 8px;
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
    gap: 4px;
  }

  .current-price {
    font-size: 16px;
    font-weight: 900;
    color: #ff2b54;
  }
  .symbol { font-size: 12px; margin-left: 1px; text-decoration: underline; }

  .old-price {
    font-size: 11px;
    color: #bbb;
    text-decoration: line-through;
  }

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
</style>
