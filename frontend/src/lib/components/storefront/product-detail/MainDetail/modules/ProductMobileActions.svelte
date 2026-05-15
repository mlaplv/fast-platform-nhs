<script lang="ts">
  import { formatCurrency } from '$lib/utils/format';
  import type { Product } from '$lib/types';

  interface Props {
    product: Product;
    selectedVariant?: import('$lib/types').ProductVariant | null;
    hasFreeship: boolean;
    onAddToCart?: () => void;
    onBuyNow?: () => void;
  }

  let { product, selectedVariant, hasFreeship, onAddToCart, onBuyNow }: Props = $props();

  const activePrice = $derived(
    selectedVariant 
      ? (selectedVariant.discountPrice || selectedVariant.discount_price || selectedVariant.price)
      : (product.discountPrice || product.discount_price || product.price || 0)
  );
</script>

<div class="tbn-action-group">
  <button class="tbn-action-split tbn-action-split--cart" aria-label="Thêm vào giỏ hàng" onclick={() => onAddToCart?.()}>
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/><path d="M12 9h4M14 7v4" />
    </svg>
  </button>
  <button class="tbn-action-split tbn-action-split--buy" aria-label="Mua ngay" onclick={() => onBuyNow?.()}>
    <span class="buy-text">MUA NGAY</span>
    <span class="buy-sub">{formatCurrency(activePrice)} {hasFreeship ? '| Freeship' : ''}</span>
    <div class="tbn-btn-shine"></div>
  </button>
</div>

<style>
  .tbn-action-group { 
    display: flex; flex: 1; height: 100%; margin-left: 8px; margin-right: -6px; 
    border-radius: 0 18px 18px 0; overflow: hidden; 
    background: #fff; border-left: 1px solid #f5f5f5;
  }
  .tbn-action-split { display: flex; flex-direction: column; align-items: center; justify-content: center; border: none; cursor: pointer; transition: all 0.2s ease; }
  .tbn-action-split:active { opacity: 0.7; transform: scale(0.95); }
  
  .tbn-action-split--cart { 
    width: 52px; background: #fff; color: #ee4d2d; border-right: 1px solid #f5f5f5; 
  }
  .tbn-action-split--buy { 
    flex: 1; position: relative; overflow: hidden;
    background: linear-gradient(135deg, #ee4d2d, #ff7337); color: #FFF; padding: 0 20px; 
  }
  .buy-text { font-size: 13px; font-weight: 1000; letter-spacing: 0.05em; }
  .buy-sub { font-size: 9px; font-weight: 800; opacity: 0.9; margin-top: 1px; }

  .tbn-btn-shine {
    position: absolute; top: 0; left: -100%; width: 50%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    transform: skewX(-25deg);
    animation: tbn-shine 4s infinite;
  }
  @keyframes tbn-shine {
    0% { left: -100%; }
    15% { left: 200%; }
    100% { left: 200%; }
  }
</style>
