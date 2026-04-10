<script lang="ts">
  import type { Product, Category } from '$lib/types';
  import CategoryPills from './CategoryPills.svelte';
  import ProductCard   from './ProductCard.svelte';

  interface Props {
    products: Product[];
    categories?: Category[];
  }

  let { products, categories = [] }: Props = $props();

  let activeTab = $state(0);

  // Elite 2.2: Dynamic Filtering & Category Mapping
  const filteredProducts = $derived.by(() => {
    if (activeTab === 0) return products;
    
    // index 0 is "Tất cả", so cat index is activeTab - 1
    const selectedCategory = categories[activeTab - 1];
    if (!selectedCategory) return products;

    return products.filter(p => 
      p.categoryId === selectedCategory.id || 
      p.category === selectedCategory.name
    );
  });

  function handleTabChange(index: number) {
    activeTab = index;
    // Elite UX: Scroll slightly to the top of the feed if user is deep in scroll
    if (typeof window !== 'undefined') {
       // Optional: Add logic to smooth scroll into view if needed
    }
  }
</script>

<div class="mobile-feed-root">
  <!-- Dynamic Category Pills extracted to child component -->
  <CategoryPills {categories} {activeTab} onTabChange={handleTabChange} />

  <!-- High-Density Product Grid -->
  <div class="product-grid">
    {#each filteredProducts as product, i (product.id)}
      <ProductCard {product} index={i} />
    {/each}
  </div>

  <!-- Loading State (Conditional) -->
  {#if filteredProducts.length === 0}
    <div class="empty-state">
      <img src="https://cdn-icons-png.flaticon.com/512/7486/7486744.png" alt="no-data" />
      <p>Không tìm thấy sản phẩm phù hợp</p>
    </div>
  {/if}
</div>

<style>
  .mobile-feed-root {
    width: 100%;
    background: #f1f3f4;
  }

  /* Product Grid: 2-column high density */
  .product-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 4px;
    padding: 4px 8px;
  }

  .empty-state {
    padding: 60px 20px;
    text-align: center;
    color: #999;
  }
  .empty-state img {
    width: 64px;
    opacity: 0.5;
    margin-bottom: 12px;
  }
  .empty-state p {
    font-size: 14px;
    font-weight: 500;
  }
</style>
