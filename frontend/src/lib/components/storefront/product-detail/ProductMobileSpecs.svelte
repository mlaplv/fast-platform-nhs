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
  <div class="prose-micsmo pb-6">
    {@html product.short_description || product.description || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
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
  
  /* Elite V2.2: Mobile Premium Prose System */
  :global(.prose-micsmo) {
    font-size: 15px !important;
    line-height: 1.8 !important;
    color: #444 !important;
    font-family: inherit !important;
  }

  :global(.prose-micsmo p) {
    margin-bottom: 0.75rem !important;
    font-family: inherit !important;
  }

  /* Khử margin cho p bên trong li để list items khít nhau */
  :global(.prose-micsmo li p) {
    margin-bottom: 0 !important;
  }

  :global(.prose-micsmo span) {
    font-family: inherit !important;
    font-size: inherit !important;
    line-height: inherit !important;
  }

  :global(.prose-micsmo h2, .prose-micsmo h3) {
    color: #111 !important;
    font-weight: 800 !important;
    margin-top: 1.25rem !important;
    margin-bottom: 0.75rem !important;
    font-family: inherit !important;
    text-transform: uppercase;
  }

  :global(.prose-micsmo h2) { font-size: 17px !important; }
  :global(.prose-micsmo h3) { font-size: 16px !important; }

  :global(.prose-micsmo ul, .prose-micsmo ol) {
    margin-bottom: 1rem !important;
    padding-left: 1.25rem !important;
  }

  :global(.prose-micsmo li) {
    margin-bottom: 0.25rem !important;
    list-style-type: disc;
  }

  :global(.prose-micsmo img) {
    border-radius: 6px;
    margin: 1.5rem 0 !important;
    width: 100% !important;
    height: auto !important;
  }

  .expand-btn { background: none; border: none; color: #ff2556; font-size: 12px; display: flex; align-items: center; justify-content: center; width: 100%; margin-top: 12px; gap: 4px; }
</style>
