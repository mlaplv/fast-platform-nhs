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
  let categoryProducts = $state<Record<string, Product[]>>({});
  let loadingCategory = $state(false);

  // Elite 2.2: Lazy fetch category products only on user tab selection (saves DB/CPU)
  $effect(() => {
    if (activeTab > 0) {
      const selectedCategory = categories[activeTab - 1];
      if (selectedCategory && !categoryProducts[selectedCategory.id]) {
        loadingCategory = true;
        fetch(`/api/v1/client/products?category_id=${selectedCategory.id}&limit=20`)
          .then(res => res.json())
          .then(resData => {
            categoryProducts[selectedCategory.id] = resData.data || [];
          })
          .catch(err => console.error("Failed to lazy fetch category products:", err))
          .finally(() => {
            loadingCategory = false;
          });
      }
    }
  });

  const filteredProducts = $derived.by(() => {
    if (activeTab === 0) return products;
    
    const selectedCategory = categories[activeTab - 1];
    if (!selectedCategory) return [];

    return categoryProducts[selectedCategory.id] || [];
  });

  function handleTabChange(index: number) {
    activeTab = index;
  }

  /**
   * LOAD MORE LOGIC (Elite V2.2)
   */
  let visibleLimit = $state(10);
  let autoLoaded = $state(false);
  let triggerEl = $state<HTMLElement | null>(null);

  const displayedProducts = $derived(filteredProducts.slice(0, visibleLimit));
  const hasMoreProducts = $derived(visibleLimit < filteredProducts.length);

  $effect(() => {
    const _ = activeTab;
    visibleLimit = 10;
    autoLoaded = false;
  });

  $effect(() => {
    let observer: IntersectionObserver | null = null;
    if (triggerEl && !autoLoaded && hasMoreProducts) {
      observer = new IntersectionObserver((entries) => {
        const entry = entries[0];
        if (entry && entry.isIntersecting) {
          visibleLimit = 20;
          autoLoaded = true;
        }
      }, {
        rootMargin: '200px'
      });
      observer.observe(triggerEl);
    }
    return () => {
      if (observer) {
        observer.disconnect();
      }
    };
  });

  function handleLoadMore(): void {
    visibleLimit += 10;
  }
</script>

<div class="mobile-feed-root">
  <!-- Dynamic Category Pills extracted to child component -->
  <CategoryPills {categories} {activeTab} onTabChange={handleTabChange} />

  <!-- High-Density Product Grid -->
  <div class="product-grid">
    {#each displayedProducts as product, i (product.id)}
      <ProductCard {product} index={i} />
    {/each}
  </div>

  <!-- Scroll Trigger for Auto Load More (1st time) -->
  {#if !autoLoaded && hasMoreProducts}
    <div bind:this={triggerEl} class="h-2 w-full pointer-events-none opacity-0"></div>
  {/if}

  <!-- Mobile Xem Thêm Button -->
  {#if autoLoaded && hasMoreProducts}
    <div class="flex justify-center py-6 bg-white border-t border-black/[0.03]">
      <button 
          onclick={handleLoadMore}
          class="group/foot relative py-2.5 px-8 overflow-hidden active:scale-95 transition-all bg-black/5 rounded-full border border-black/5 hover:bg-black/10"
      >
          <span class="relative z-10 text-[10px] font-black tracking-[0.3em] uppercase text-black/50 group-hover/foot:text-black transition-all duration-500 flex items-center gap-2">
              Xem thêm
              <svg class="w-3.5 h-3.5 opacity-40 group-hover/foot:opacity-100 group-hover/foot:translate-x-1 transition-all duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
          </span>
      </button>
    </div>
  {/if}

  <!-- Loading State (Conditional) -->
  {#if loadingCategory}
    <div class="empty-state">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-solid border-black/20 border-t-black/80 mb-2"></div>
      <p>Đang tải sản phẩm...</p>
    </div>
  {:else if filteredProducts.length === 0}
    <div class="empty-state">
      <svg class="w-16 h-16 mx-auto mb-3 opacity-30 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
        <path d="M3.3 7 12 12l8.7-5" />
        <path d="M12 22V12" />
      </svg>
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
    padding: 4px 5px;
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
