<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { ChevronDown, ChevronUp } from 'lucide-svelte';
  import type { Product } from '$lib/types';

  interface Props {
    product: Product;
  }

  let { product }: Props = $props();

  let isExpanded = $state(false);
  let truncatedHeight = $state(450); // Mặc định nếu không tính được
  let containerRef = $state<HTMLElement>();
  let hasMore = $state(false);

  async function calculateTruncation() {
    if (!containerRef) return;
    
    // Tìm cái hình đầu tiên trong mô tả
    const images = containerRef.querySelectorAll('img');
    if (images.length > 0) {
      const firstImg = images[0];
      
      // Nếu hình chưa load xong thì height = 0, cần đợi load xong mới chuẩn
      if (firstImg.complete) {
        updateHeight(firstImg);
      } else {
        firstImg.onload = () => updateHeight(firstImg);
      }
    } else {
      // Nếu không có hình, mặc định cắt ở mức 400px
      truncatedHeight = 400;
      checkHasMore();
    }
  }

  function updateHeight(img: HTMLImageElement) {
    // Chiều cao cắt = Vị trí top của hình + chiều cao của hình + một chút padding
    truncatedHeight = img.offsetTop + img.offsetHeight + 24;
    checkHasMore();
  }

  function checkHasMore() {
    if (!containerRef) return;
    // Nếu chiều cao thực tế lớn hơn mốc cần cắt thì mới hiện nút "Xem thêm"
    hasMore = containerRef.scrollHeight > truncatedHeight + 50;
  }

  onMount(async () => {
    await tick();
    calculateTruncation();
  });
</script>

<section id="description" class="content-section">
  <h2 class="section-title">Chi tiết sản phẩm</h2>
  <div class="spec-table">
    {#if product.metadata?.brand}
      <div class="spec-row">
        <span class="label">Thương hiệu</span>
        <span class="val">{product.metadata.brand}</span>
      </div>
    {/if}
    {#if product.metadata?.origin}
      <div class="spec-row">
        <span class="label">Xuất xứ</span>
        <span class="val">{product.metadata.origin}</span>
      </div>
    {/if}
    {#if product.metadata?.weight}
      <div class="spec-row">
        <span class="label">Trọng lượng</span>
        <span class="val">{product.metadata.weight}</span>
      </div>
    {/if}
    {#if product.sku && product.sku !== 'N/A'}
      <div class="spec-row">
        <span class="label">Mã vạch</span>
        <span class="val">{product.sku}</span>
      </div>
    {/if}
    {#if product.attributes}
      {#each Object.entries(product.attributes) as [key, val]}
        {@const k = key.toLowerCase().replace(/_/g, ' ').trim()}
        {#if !( ((k === 'thương hiệu' || k === 'brand') && product.metadata?.brand) || ((k === 'xuất xứ' || k === 'origin') && product.metadata?.origin) || ((k === 'trọng lượng' || k === 'quy cách' || k === 'weight') && product.metadata?.weight) || ((k === 'mã vạch' || k === 'barcode') && product.sku && product.sku !== 'N/A') )}
        <div class="spec-row">
          <span class="label capitalize">{key.replace(/_/g, ' ')}</span>
          <span class="val">{val}</span>
        </div>
        {/if}
      {/each}
    {/if}
  </div>
  
  <h2 class="section-title mt-6">Mô tả sản phẩm</h2>
  
  <div 
    class="description-wrapper {(!isExpanded && hasMore) ? 'collapsed' : ''}"
    style:max-height={isExpanded ? (containerRef?.scrollHeight + 'px') : (hasMore ? truncatedHeight + 'px' : 'none')}
  >
    <div bind:this={containerRef} class="prose-micsmo pb-4">
      {@html product.short_description || product.description || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
    </div>
  </div>

  {#if hasMore}
    <button 
      class="expand-btn-elite" 
      onclick={() => isExpanded = !isExpanded}
    >
      {#if isExpanded}
        Thu gọn <ChevronUp size={16} />
      {:else}
        Xem thêm <ChevronDown size={16} />
      {/if}
    </button>
  {/if}
</section>

<style>
  .content-section { background: white; padding: 16px; overflow: hidden; }
  .section-title { font-size: 14px; font-weight: 800; color: #222; margin-bottom: 12px; text-transform: uppercase; letter-spacing: -0.01em; }
  .spec-table { display: flex; flex-direction: column; gap: 8px; }
  .spec-row { display: flex; justify-content: space-between; font-size: 13px; border-bottom: 1px solid #f5f5f5; padding-bottom: 8px; }
  .spec-row:last-child { border-bottom: none; }
  .label { color: #888; font-weight: 500; }
  .val { color: #222; font-weight: 700; text-align: right; }

  /* Elite V2.2: Smooth Description Truncation */
  .description-wrapper {
    position: relative;
    overflow: hidden;
    transition: max-height 0.8s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .description-wrapper.collapsed::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 120px;
    background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.8) 50%, white 100%);
    pointer-events: none;
    z-index: 10;
  }

  .expand-btn-elite {
    background: none;
    border: 1px solid #f0f0f0;
    color: var(--color-luxury-copper, #C18F7E);
    font-size: 11px;
    font-weight: 900;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin-top: 16px;
    padding: 12px;
    gap: 6px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-radius: 12px;
    transition: all 0.3s ease;
  }

  .expand-btn-elite:active {
    scale: 0.98;
    background: #fafafa;
  }

  /* Elite V2.2: Mobile Premium Prose System */
  :global(.prose-micsmo) {
    font-size: 15px !important;
    line-height: 1.8 !important;
    color: #333 !important;
    font-family: inherit !important;
  }

  :global(.prose-micsmo p) {
    margin-bottom: 0.75rem !important;
    font-family: inherit !important;
  }

  :global(.prose-micsmo li p) {
    margin-bottom: 0 !important;
  }

  :global(.prose-micsmo span) {
    font-family: inherit !important;
    font-size: inherit !important;
    line-height: inherit !important;
  }

  :global(.prose-micsmo h2, .prose-micsmo h3) {
    color: var(--color-luxury-copper, #C18F7E) !important;
    font-weight: 900 !important;
    margin-top: 1.25rem !important;
    margin-bottom: 0.75rem !important;
    font-family: inherit !important;
    text-transform: uppercase;
    letter-spacing: 0.02em;
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
    color: #444;
  }

  :global(.prose-micsmo img) {
    border-radius: 8px;
    margin: 1.5rem 0 !important;
    width: 100% !important;
    height: auto !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  }
</style>
