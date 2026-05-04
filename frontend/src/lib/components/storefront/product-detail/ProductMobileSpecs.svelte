<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { ChevronDown, ChevronUp } from 'lucide-svelte';
  import type { Product } from '$lib/types';
  import InteractiveDashboard from '$lib/components/ui/InteractiveDashboard.svelte';

  function isJson(str: string) {
    if (typeof str !== 'string') return false;
    try {
      const parsed = JSON.parse(str);
      return typeof parsed === 'object' && parsed !== null && ('hero_headline' in parsed || 'spec_bento' in parsed);
    } catch (e) {
      return false;
    }
  }

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
  <div class="spec-infographic">
    {#if product.metadata?.brand}
      <div class="info-tag">
        <span class="tag-label">Thương hiệu</span>
        <span class="tag-val text-[#ee4d2d]">{product.metadata.brand}</span>
      </div>
    {/if}
    {#if product.metadata?.origin}
      <div class="info-tag">
        <span class="tag-label">Xuất xứ</span>
        <span class="tag-val">{product.metadata.origin}</span>
      </div>
    {/if}
    {#if product.metadata?.weight}
      <div class="info-tag">
        <span class="tag-label">Quy cách</span>
        <span class="tag-val">{product.metadata.weight}</span>
      </div>
    {/if}
    <div class="info-tag">
      <span class="tag-label">Danh mục</span>
      <span class="tag-val text-[#0384ff]">{product.category || 'Chăm sóc da'}</span>
    </div>
    {#if product.sku && product.sku !== 'N/A'}
      <div class="info-tag col-span-2">
        <span class="tag-label">Mã vạch (Barcode)</span>
        <span class="tag-val tracking-widest">{product.sku}</span>
      </div>
    {/if}
  </div>

  {#if product.attributes && Object.keys(product.attributes).length > 0}
    <div class="mt-4 grid grid-cols-2 gap-2">
      {#each Object.entries(product.attributes) as [key, val]}
        {@const k = key.toLowerCase().replace(/_/g, ' ').trim()}
        {#if !( ((k === 'thương hiệu' || k === 'brand') && product.metadata?.brand) || ((k === 'xuất xứ' || k === 'origin') && product.metadata?.origin) || ((k === 'trọng lượng' || k === 'quy cách' || k === 'weight') && product.metadata?.weight) || ((k === 'mã vạch' || k === 'barcode') && product.sku) )}
          <div class="flex flex-col p-2 bg-gray-50/50 rounded-lg">
            <span class="text-[10px] text-gray-400 uppercase font-bold">{key.replace(/_/g, ' ')}</span>
            <span class="text-[12px] text-gray-800 font-medium">{val}</span>
          </div>
        {/if}
      {/each}
    </div>
  {/if}
  
  <h2 class="section-title mt-6">Mô tả sản phẩm</h2>
  
  <div 
    class="description-wrapper {(!isExpanded && hasMore) ? 'collapsed' : ''}"
    style:max-height={isExpanded ? (containerRef?.scrollHeight + 'px') : (hasMore ? truncatedHeight + 'px' : 'none')}
  >
    <div bind:this={containerRef} class="prose-osmo pb-4">
      {#if isJson(product.short_description || product.description)}
         <InteractiveDashboard data={product.short_description || product.description} compact={true} />
      {:else}
         {@html product.short_description || product.description || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
      {/if}
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

  <!-- GEO 2026: Mobile FAQ Section -->
  {#if product.metadata?.faqs && product.metadata.faqs.length > 0}
    <div class="mt-8 border-t border-gray-100 pt-6">
      <h2 class="section-title">Câu hỏi thường gặp</h2>
      <div class="flex flex-col gap-3 mt-4">
        {#each product.metadata.faqs as faq}
          <div class="bg-gray-50/50 border border-gray-100 rounded-lg p-3">
            <h3 class="text-[13px] font-bold text-gray-900 mb-1.5 leading-tight">{faq.question}</h3>
            <p class="text-[12px] text-gray-600 leading-relaxed">{faq.answer}</p>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</section>

<style>
  .content-section { background: white; padding: 16px; overflow: hidden; }
  .section-title { font-size: 14px; font-weight: 800; color: #222; margin-bottom: 16px; text-transform: uppercase; letter-spacing: -0.01em; border-left: 4px solid #ee4d2d; padding-left: 10px; }
  
  .spec-infographic { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1px; background: #f0f0f0; border: 1px solid #f0f0f0; border-radius: 8px; overflow: hidden; }
  .info-tag { background: white; padding: 12px; display: flex; flex-direction: column; gap: 4px; }
  .tag-label { font-size: 11px; color: #888; font-weight: 500; }
  .tag-val { font-size: 13px; color: #222; font-weight: 800; }

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
    z-index: var(--z-surface);
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
  :global(.prose-osmo) {
    font-size: 15px !important;
    line-height: 1.8 !important;
    color: #333 !important;
    font-family: inherit !important;
  }

  :global(.prose-osmo p) {
    margin-bottom: 0.75rem !important;
    font-family: inherit !important;
  }

  :global(.prose-osmo li p) {
    margin-bottom: 0 !important;
  }

  :global(.prose-osmo span) {
    font-family: inherit !important;
    font-size: inherit !important;
    line-height: inherit !important;
  }

  :global(.prose-osmo h2, .prose-osmo h3) {
    color: var(--color-luxury-copper, #C18F7E) !important;
    font-weight: 900 !important;
    margin-top: 1.25rem !important;
    margin-bottom: 0.75rem !important;
    font-family: inherit !important;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  :global(.prose-osmo h2) { font-size: 17px !important; }
  :global(.prose-osmo h3) { font-size: 16px !important; }

  :global(.prose-osmo ul, .prose-osmo ol) {
    margin-bottom: 1rem !important;
    padding-left: 1.25rem !important;
  }

  :global(.prose-osmo li) {
    margin-bottom: 0.25rem !important;
    list-style-type: disc;
    color: #444;
  }

  :global(.prose-osmo img) {
    border-radius: 8px;
    margin: 1.5rem 0 !important;
    width: 100% !important;
    height: auto !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  }
</style>
