<script lang="ts">
  import { ChevronRight } from 'lucide-svelte';
  import type { Product } from '$lib/types';

  interface Props {
    product: Product;
  }

  let { product }: Props = $props();
</script>

<section id="description" class="content-section">
  <h2 class="section-title">Chi tiết sản phẩm</h2>
  <div class="spec-table">
    {#if (product.metadata as any)?.brand}
      <div class="spec-row">
        <span class="label">Thương hiệu</span>
        <span class="val">{(product.metadata as any).brand}</span>
      </div>
    {/if}
    {#if product.attributes}
      {#each Object.entries(product.attributes) as [key, val]}
        <div class="spec-row">
          <span class="label capitalize">{key.replace(/_/g, ' ')}</span>
          <span class="val">{val}</span>
        </div>
      {/each}
    {/if}
  </div>
  
  <h2 class="section-title mt-4">Mô tả sản phẩm</h2>
  <div class="product-desc line-clamp-4">
    {product.short_description || product.description || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
  </div>
  <button class="expand-btn">Xem thêm <ChevronRight size={14} class="rotate-90" /></button>
</section>

<style>
  .content-section { background: white; padding: 16px; }
  .section-title { font-size: 14px; font-weight: 700; color: #333; margin-bottom: 12px; }
  .spec-table { display: flex; flex-direction: column; gap: 8px; }
  .spec-row { display: flex; justify-content: space-between; font-size: 13px; border-bottom: 1px solid #f5f5f5; padding-bottom: 8px; }
  .spec-row:last-child { border-bottom: none; }
  .label { color: #888; }
  .val { color: #333; font-weight: 500; text-align: right; }
  .product-desc { font-size: 13px; color: #444; line-height: 1.6; margin-top: 8px; }
  .expand-btn { background: none; border: none; color: #ff2556; font-size: 12px; display: flex; align-items: center; justify-content: center; width: 100%; margin-top: 12px; gap: 4px; }
</style>
