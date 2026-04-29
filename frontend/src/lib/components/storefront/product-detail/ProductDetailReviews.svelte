<script lang="ts">
  import EliteReviewSystem from './reviews/EliteReviewSystem.svelte';
  
  interface Props {
    product: { id: string; name: string };
    entityType?: 'PRODUCT' | 'CATEGORY' | 'NEWS';
  }
  let { product, entityType = 'PRODUCT' }: Props = $props();
</script>

<div class="product-reviews-wrapper bg-white border-t border-gray-50" id="reviews">
  <div class="container mx-auto px-4 py-16">
    <EliteReviewSystem 
      entityId={product.id} 
      {entityType} 
      title="Cảm nhận về {product.name}" 
    />
  </div>
</div>

<style>
  .product-reviews-wrapper {
    position: relative;
    z-index: 1;
  }
</style>
