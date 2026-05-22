<script lang="ts">
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import type { Product } from '$lib/types';
  import ProductGrid from '../../product/ProductGrid.svelte';
  import { getRecentlyViewedStore } from '$lib/state/commerce/recentlyViewed.svelte';
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Flame from "@lucide/svelte/icons/flame";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import History from "@lucide/svelte/icons/history";
  import Sparkles from "@lucide/svelte/icons/sparkles";

  interface Props {
    product: Product;
    isMobile?: boolean;
    initialProducts?: Product[];
  }
  let { product, isMobile = false, initialProducts = [] }: Props = $props();

  // Elite Performance Fix P2.2: Dùng dữ liệu từ server nếu có
  let categoryProducts = $state<Product[]>(initialProducts);
  let brandProducts = $state<Product[]>([]);
  let recentProducts = $state<Product[]>([]);
  let isLoading = $state(initialProducts.length === 0);
  let isInitialized = $state(initialProducts.length > 0);
  let activeTab = $state<string | null>(null);

  const recentlyViewed = getRecentlyViewedStore();

  // Elite V2.2: Intelligent Tab Discovery - Sharp & Professional Liquid Glass
  const availableTabs = $derived.by(() => {
    const list = [];
    if (categoryProducts.length > 0) {
      list.push({ 
        id: 'category', 
        label: 'Cùng danh mục', 
        reasoning: `Dựa trên sở thích chăm sóc ${product.category_name || 'chuyên sâu'} của Bạn`,
        icon: Flame, 
        color: '#ee4d2d' 
      });
    }
    if (brandProducts.length > 0) {
      const brand = product.metadata?.brand || product.attributes?.brand || product.attributes?.['Thương hiệu'] || 'osmo Elite';
      list.push({ 
        id: 'brand', 
        label: 'Thương hiệu', 
        reasoning: `Khám phá hệ sinh thái sản phẩm ${brand}`,
        icon: ShieldCheck, 
        color: '#1890ff' 
      });
    }
    if (recentProducts.length > 0) {
      list.push({ 
        id: 'recent', 
        label: 'Vừa xem', 
        reasoning: 'Gợi ý dựa trên lịch sử quan tâm của Bạn',
        icon: History, 
        color: '#52c41a' 
      });
    }
    return list;
  });

  async function fetchAllRelated() {
    isLoading = true;
    try {
      const categoryId = product.categoryId || product.category_id;
      const brandName = product.metadata?.brand || product.attributes?.brand || product.attributes?.['Thương hiệu'];
      const recentIds = recentlyViewed.items.filter(id => id !== product.id);

      const fetchPromises = [];

      if (categoryId) {
        fetchPromises.push(
          fetch(`/api/v1/client/products?category_id=${categoryId}&limit=11`)
            .then(res => res.json())
            .then((data: { data?: Product[] }) => {
              categoryProducts = (data.data || []).filter(p => p.id !== product.id).slice(0, 10);
            })
        );
      }

      if (brandName) {
        fetchPromises.push(
          fetch(`/api/v1/client/products?search=${encodeURIComponent(String(brandName))}&limit=11`)
            .then(res => res.json())
            .then((data: { data?: Product[] }) => {
              brandProducts = (data.data || []).filter(p => p.id !== product.id).slice(0, 10);
            })
        );
      }

      if (recentIds.length > 0) {
        fetchPromises.push(
          fetch(`/api/v1/client/products?ids=${recentIds.join(',')}&limit=12`)
            .then(res => res.json())
            .then((data: { data?: Product[] }) => {
              const fetched = data.data || [];
              recentProducts = recentIds
                .map(id => fetched.find(p => p.id === id))
                .filter((p): p is Product => !!p && p.id !== product.id);
              recentlyViewed.products = recentProducts;
            })
        );
      }

      await Promise.allSettled(fetchPromises);
      
      if (availableTabs.length > 0 && !activeTab) {
        activeTab = availableTabs[0].id;
      }
    } catch (e) {
      console.error('Failed to initialize related products', e);
    } finally {
      isLoading = false;
      isInitialized = true;
    }
  }

  onMount(() => {
    recentlyViewed.addProduct(product.id);
    // Chỉ fetch nếu chưa có dữ liệu hoặc để cập nhật brand/recent
    fetchAllRelated();
  });

  $effect(() => {
    if (isInitialized && availableTabs.length > 0) {
      if (!activeTab || !availableTabs.find(t => t.id === activeTab)) {
        activeTab = availableTabs[0].id;
      }
    }
  });

  let displayProducts = $derived.by(() => {
    if (activeTab === 'category') return categoryProducts;
    if (activeTab === 'brand') return brandProducts;
    if (activeTab === 'recent') return recentProducts;
    return [];
  });

  const seeMoreLink = $derived.by(() => {
    if (activeTab === 'category') return `/${product.category_slug || product.categorySlug || ''}/`;
    if (activeTab === 'brand') {
       const brand = product.metadata?.brand || product.attributes?.brand || product.attributes?.['Thương hiệu'];
       return `/search?q=${encodeURIComponent(String(brand || ''))}`;
    }
    return '/search';
  });
</script>

{#if isInitialized && availableTabs.length > 0}
  <section class="related-section {isMobile ? 'mobile-mode' : 'desktop-mode'}">
    <!-- Sharp Liquid Navigator -->
    <div class="tabs-nav no-scrollbar">
      <div class="sharp-track">
        {#each availableTabs as tab}
          <button 
            class="tab-sharp {activeTab === tab.id ? 'active' : ''}"
            onclick={() => activeTab = tab.id}
          >
            <div class="sharp-bg"></div>
            <span class="icon-wrap" style="color: {activeTab === tab.id ? '#000' : tab.color}">
              <tab.icon size={18} strokeWidth={2.5} />
            </span>
            <div class="flex flex-col items-start">
              <span class="label">{tab.label}</span>
              {#if activeTab === tab.id}
                <span class="reasoning" in:fade>{tab.reasoning}</span>
              {/if}
            </div>
          </button>
        {/each}
      </div>
    </div>

    <div class="content-area">
      <div class="grid-wrapper">
        <ProductGrid products={displayProducts} />
      </div>
      
      <div class="footer-actions">
        <a href={seeMoreLink} class="btn-sharp">
          <Sparkles size={16} class="mr-2" />
          <span>Xem thêm ưu đãi</span>
          <ChevronRight size={18} class="ml-1" />
        </a>
      </div>
    </div>
  </section>
{:else if isLoading}
  <div class="loading-placeholder">
    <div class="shimmer-box"></div>
  </div>
{/if}

<style>
  .related-section {
    background: #ffffff;
    margin-top: 0;
    padding: 1.25rem; /* Standard p-5 alignment */
    padding-bottom: 2rem;
    margin-bottom: 6rem; /* Preserve footer distance (mb-24) */
    animation: sharpFade 0.6s ease;
  }

  @keyframes sharpFade {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .desktop-mode {
    max-width: 1200px; /* Match parent container exactly */
    margin-left: auto;
    margin-right: auto;
  }

  .mobile-mode {
    padding: 1rem;
    margin-bottom: 3rem;
  }

  .tabs-nav {
    margin-bottom: 2rem;
    display: flex;
    justify-content: flex-start;
    overflow-x: auto;
    padding: 2px 0;
  }

  .sharp-track {
    display: flex;
    gap: 0;
    background: #fdfdfd;
    border: 1px solid #f0f0f0;
  }

  .tab-sharp {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.8rem 1.5rem;
    background: transparent;
    border: none;
    border-right: 1px solid #f0f0f0;
    cursor: pointer;
    position: relative;
    white-space: nowrap;
    transition: all 0.3s;
    border-radius: 0 !important;
    outline: none !important;
    box-shadow: none !important;
  }

  .tab-sharp:last-child {
    border-right: none;
  }

  .tab-sharp .label {
    font-size: 14px;
    font-weight: 700;
    color: #666;
    transition: color 0.3s;
  }

  .tab-sharp.active .label {
    color: #000;
    margin-bottom: -2px;
  }

  .reasoning {
    font-size: 10px;
    color: rgba(0,0,0,0.5);
    font-weight: 500;
    white-space: nowrap;
    margin-top: -2px;
  }

  .sharp-bg {
    position: absolute;
    inset: 0;
    background: transparent;
    transition: all 0.3s;
    z-index: -1;
    border-radius: 0 !important;
  }

  .tab-sharp.active .sharp-bg {
    background: #ee4d2d; /* OSMO Brand Color */
  }

  .tab-sharp:not(.active):hover .sharp-bg {
    background: rgba(238, 77, 45, 0.05);
  }

  .icon-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s;
  }

  .footer-actions {
    display: flex;
    justify-content: center;
    margin-top: 2.5rem;
  }

  .btn-sharp {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 1rem 3.5rem;
    background: #ee4d2d; /* OSMO Brand Color */
    color: white;
    font-size: 14px;
    font-weight: 800;
    text-decoration: none;
    border-radius: 0 !important;
    transition: all 0.3s;
    border: 1px solid #ee4d2d;
  }

  .btn-sharp:hover {
    background: #fff;
    color: #ee4d2d;
  }

  .loading-placeholder {
    padding: 3rem;
    display: flex;
    justify-content: center;
  }

  .shimmer-box {
    height: 45px;
    width: 350px;
    background: #f0f0f0;
    animation: shimmer 1.5s infinite linear;
  }

  @keyframes shimmer {
    0% { opacity: 0.5; }
    50% { opacity: 1; }
    100% { opacity: 0.5; }
  }

  /* Custom grid override */
  :global(.related-section .grid) {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 1.5rem !important;
  }

  @media (min-width: 768px) {
    :global(.related-section .grid) {
      grid-template-columns: repeat(5, 1fr) !important;
      gap: 2rem !important;
    }
  }

  /* Force sharp images and cards */
  :global(.related-section .product-card),
  :global(.related-section img),
  :global(.related-section .badge) {
    border-radius: 0 !important;
  }

  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
