<script lang="ts">
  import type { Product } from '$lib/types';
  import { getIngredientIcon } from '$lib/utils/product';
  import VerificationCenter from '../../shared/VerificationCenter.svelte';
  import ScannerHUD from '../../shared/ScannerHUD.svelte';
  import X from "@lucide/svelte/icons/x";
  import { fly, fade, scale } from 'svelte/transition';

  interface Props {
    product: Product;
    visibleAttributes: [string, string | number | boolean | null][];
    productInfo: {
      brand: string;
      origin: string;
      weight: string;
      barcode: string;
    };
    onViewFullIngredients: () => void;
    onTriggerScan?: () => void;
  }
 
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  let { product, visibleAttributes, productInfo, onViewFullIngredients, onTriggerScan }: Props = $props();

  const featuredIngredients = $derived(
    (product.metadata?.featured_ingredients || product.metadata?.ingredients || [])
    .slice(0, 4) as { name: string; icon?: string }[]
  );
</script>

<div class="specs-container">
  <!-- Liquid Spec Bar (Elite V2.2) -->
  <div class="spec-bar">
    <div class="spec-item">
      <span class="spec-label">Thương hiệu</span>
      <span class="spec-value">{productInfo.brand || 'Osmo Elite'}</span>
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
        class="spec-item group/barcode cursor-pointer hover:bg-white/5 transition-colors bg-transparent border-none p-0"
        onclick={() => onTriggerScan?.()}
      >
        <span class="spec-label group-hover/barcode:text-green-400">Mã vạch (Verify)</span>
        <span class="spec-value group-hover/barcode:text-white">{productInfo.barcode}</span>
      </button>
  </div>

  <!-- Removed local scanner/modal logic to use shared Desktop state -->

  <!-- Detailed Attributes -->
  <div class="attributes-section">
    <h2 class="section-title text-[14px]">Thông số kỹ thuật {product.name}</h2>
    <div class="attributes-grid">
      {#each visibleAttributes as [key, value]}
        <div class="attribute-row">
          <span class="attr-key">{key}</span>
          <span class="attr-val">{value}</span>
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
      <button class="view-full-btn" onclick={onViewFullIngredients}>
        Xem toàn bộ bảng thành phần
      </button>
    </div>
  {/if}
</div>

<style>
  .specs-container {
    margin-top: 2rem;
    padding: 0 1.25rem;
  }

  .spec-bar {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    display: flex;
    justify-content: space-around;
    padding: 1.5rem 0.75rem;
    margin-bottom: 2.5rem;
    position: relative;
    box-shadow: 0 12px 35px rgba(15, 23, 42, 0.08) !important;
    border-radius: 8px !important;
  }

  .spec-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
    position: relative;
  }

  .spec-item:not(:last-child)::after {
    content: '';
    position: absolute;
    right: 0;
    top: 20%;
    height: 60%;
    width: 1px;
    background: linear-gradient(to bottom, transparent, rgba(255, 255, 255, 0.1), transparent);
  }

  .spec-label {
    font-size: 8px;
    font-weight: 900;
    letter-spacing: 0.2em;
    color: rgba(255, 255, 255, 0.5) !important;
  }

  .spec-value {
    font-size: 13px;
    font-weight: 700;
    color: #f59e0b !important;
    text-align: center;
    line-height: 1.2;
  }

  .section-title {
    font-size: 14px;
    font-weight: 900;
    letter-spacing: 0.1em;
    color: #111827;
    margin-bottom: 1.25rem;
    padding-left: 0.75rem;
    border-left: 4px solid #0d9488 !important;
  }

  .attributes-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 2.5rem;
  }

  .attribute-row {
    display: flex;
    padding: 0.5rem 0.75rem;
    font-size: 14px;
  }

  .attribute-row:nth-child(odd) {
    background: #f9fafb;
  }

  .attr-key {
    width: 150px;
    flex-shrink: 0;
    color: #6b7280;
  }

  .attr-val {
    flex: 1;
    color: #111827;
    font-weight: 500;
  }

  .ingredients-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .ing-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 0.5rem;
    background: #f9fafb;
    border: 1px solid #f3f4f6;
    transition: all 0.3s;
  }

  .ing-card:hover {
    border-color: #0d9488 !important;
    background: white;
    box-shadow: 0 10px 20px rgba(13, 148, 136, 0.08) !important;
    transform: translateY(-2px);
  }

  .ing-icon {
    width: 2.5rem;
    height: 2.5rem;
    color: #0d9488 !important;
  }

  .ing-name {
    font-size: 11px;
    font-weight: 700;
    text-align: center;
    color: #374151;
    letter-spacing: -0.01em;
  }

  .view-full-btn {
    width: 100%;
    padding: 0.75rem;
    background: white;
    border: 1px solid #e5e7eb;
    color: #6b7280;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .view-full-btn:hover {
    background: #f9fafb;
    color: #111827;
    border-color: #d1d5db;
  }
</style>
