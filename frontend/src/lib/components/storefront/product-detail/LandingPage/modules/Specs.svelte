<script lang="ts">
  import type { Product } from '$lib/types';
  import { getIngredientIcon } from '$lib/utils/product';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  interface Props {
    product: Product;
    visibleAttributes: [string, string | number | boolean | null][];
    productInfo: {
      brand: string;
      origin: string;
      weight: string;
      barcode: string;
    };
    onViewFullIngredients?: () => void;
    onTriggerScan?: () => void;
  }

  let { product, visibleAttributes, productInfo, onViewFullIngredients, onTriggerScan }: Props = $props();
  const ui = getClientUi();

  const featuredIngredients = $derived(
    (product.metadata?.featured_ingredients || product.metadata?.ingredients || [])
    .slice(0, 4) as { name: string; icon?: string }[]
  );

  function handleViewIngredients() {
    if (onViewFullIngredients) {
      onViewFullIngredients();
    } else {
      const el = document.getElementById('product-description') || document.querySelector('.description-container');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  }
</script>

<div class="specs-container">
  <!-- Liquid Spec Bar (Elite V2.2) -->
  <div class="spec-bar">
    <div class="spec-item">
      <span class="spec-label">Thương hiệu</span>
      <span class="spec-value">{productInfo.brand || (ui.settings?.basic_info?.site_name || 'osmo.vn')}</span>
    </div>
    <div class="spec-item">
      <span class="spec-label">Xuất xứ</span>
      <span class="spec-value">{productInfo.origin || 'Nhật Bản'}</span>
    </div>
    <div class="spec-item">
      <span class="spec-label">Quy cách</span>
      <span class="spec-value">{productInfo.weight || '30g / Tuýp'}</span>
    </div>
    <button 
      class="spec-item barcode-spec-item cursor-pointer"
      onclick={() => onTriggerScan?.()}
    >
      <span class="spec-label barcode-label">Mã vạch (Verify)</span>
      <span class="spec-value barcode-value">
        {productInfo.barcode || 'N/A'}
        <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
      </span>
    </button>
  </div>

  <!-- Detailed Attributes -->
  <div class="attributes-section">
    <h2 class="section-title">Thông số kỹ thuật {product.name}</h2>
    <div class="bento-attributes-grid">
      {#each visibleAttributes as [key, value]}
        <div class="bento-attr-card {String(value).length > 20 ? 'col-span-2' : 'col-span-1'}">
          <span class="bento-attr-key">{key}</span>
          <span class="bento-attr-val">{value}</span>
        </div>
      {/each}
    </div>
  </div>

  <!-- Ingredients Featured -->
  {#if featuredIngredients.length > 0}
    <div class="ingredients-section">
      <h3 class="section-title">Thành phần nổi bật</h3>
      <div class="ingredients-grid">
        {#each featuredIngredients as ing}
          <div class="ing-card">
            <div class="ing-icon">
              {@html getIngredientIcon(ing.name)}
            </div>
            <span class="ing-name">{ing.name}</span>
          </div>
        {/each}
      </div>
      <button class="view-full-btn" onclick={handleViewIngredients}>
        Xem toàn bộ bảng thành phần
      </button>
    </div>
  {/if}

  {#if featuredIngredients.length === 0}
    <div class="mt-4">
      <button class="view-full-btn" onclick={handleViewIngredients}>
        Xem toàn bộ bảng thành phần
      </button>
    </div>
  {/if}
</div>

<style>
  .specs-container {
    margin-top: 2.5rem;
    padding: 0;
    width: 100%;
  }

  .spec-bar {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin-bottom: 2rem;
  }

  @media (min-width: 768px) {
    .spec-bar {
      grid-template-columns: repeat(4, 1fr);
      gap: 0.75rem;
    }
  }

  .spec-item {
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 0.85rem 0.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.25rem;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .spec-item:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 255, 255, 0.1);
    background: #1e293b;
  }

  .spec-label {
    font-size: 8px;
    font-weight: 850;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: rgba(255, 255, 255, 0.4);
  }

  .spec-value {
    font-size: 12px;
    font-weight: 700;
    color: #f59e0b;
    text-align: center;
    line-height: 1.3;
  }

  .barcode-spec-item {
    background: linear-gradient(135deg, #064e3b 0%, #022c22 100%) !important;
    border-color: rgba(16, 185, 129, 0.15) !important;
  }

  .barcode-spec-item:hover {
    background: linear-gradient(135deg, #047857 0%, #064e3b 100%) !important;
    border-color: rgba(16, 185, 129, 0.3) !important;
  }

  .barcode-label {
    color: rgba(52, 211, 153, 0.7) !important;
  }

  .barcode-value {
    color: #34d399 !important;
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .section-title {
    font-size: 14px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #0f172a;
    margin-bottom: 1.25rem;
    padding-left: 0.75rem;
    border-left: 4px solid #0d9488 !important;
    text-transform: uppercase;
  }

  .bento-attributes-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin-bottom: 2rem;
  }

  @media (min-width: 768px) {
    .bento-attributes-grid {
      grid-template-columns: repeat(3, 1fr);
      gap: 0.75rem;
    }
  }

  .bento-attr-card {
    background: #f8fafc;
    border: 1px solid rgba(0, 0, 0, 0.03);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .bento-attr-card:hover {
    transform: translateY(-2px);
    background: #ffffff;
    border-color: rgba(13, 148, 136, 0.15);
    box-shadow: 0 10px 25px -5px rgba(13, 148, 136, 0.05);
  }

  .bento-attr-card.col-span-1 {
    grid-column: span 1 / span 1;
  }

  .bento-attr-card.col-span-2 {
    grid-column: span 2 / span 2;
  }

  .bento-attr-key {
    font-size: 8px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #94a3b8;
  }

  .bento-attr-val {
    font-size: 13px;
    font-weight: 700;
    color: #334155;
  }

  .ingredients-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }

  @media (min-width: 640px) {
    .ingredients-grid {
      grid-template-columns: repeat(4, 1fr);
      gap: 0.75rem;
    }
  }

  .ing-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 1.25rem 0.75rem;
    background: #f8fafc;
    border: 1px solid rgba(0, 0, 0, 0.03);
    border-radius: 16px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .ing-card:hover {
    border-color: rgba(13, 148, 136, 0.2) !important;
    background: white;
    box-shadow: 0 10px 30px rgba(13, 148, 136, 0.06) !important;
    transform: translateY(-3px);
  }

  .ing-icon {
    width: 2.25rem;
    height: 2.25rem;
    color: #0d9488 !important;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .ing-name {
    font-size: 13px;
    font-weight: 700;
    text-align: center;
    color: #334155;
    line-height: 1.3;
  }

  .view-full-btn {
    width: 100%;
    padding: 0.85rem;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    color: #64748b;
    font-size: 13px;
    font-weight: 700;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .view-full-btn:hover {
    background: #f8fafc;
    color: #0f172a;
    border-color: #cbd5e1;
  }
</style>
