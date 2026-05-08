<script lang="ts">
  /**
   * ELITE V2.2: Desktop Storefront Landingpage (Architectural Hardening)
   * Status: Fully Modularized & Cleaned
   */
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  
  // Types
  import type { Product, ProductVariant, ReviewStats } from '$lib/types';
  
  // State & Stores
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  
  // Modules
  import LandingProductGallery from './modules/LandingProductGallery.svelte';
  import LandingProductInfo from './modules/LandingProductInfo.svelte';
  import LandingProductSpecs from './modules/LandingProductSpecs.svelte';
  import LandingProductDescription from './modules/LandingProductDescription.svelte';
  
  // Global Components
  import ProductDetailReviews from './ProductDetailReviews.svelte';
  import ProductDetailRelated from './ProductDetailRelated.svelte';
  import InteractiveDashboard from '$lib/components/ui/InteractiveDashboard.svelte';
  
  // Utils
  import { apiClient } from '$lib/utils/apiClient';
  import { formatCurrency } from '$lib/utils/format';

  interface Props {
    product: Product;
  }

  interface VoucherUI {
    id: string;
    label: string;
    sub: string;
    type: 'ship' | 'discount';
  }

  let { product }: Props = $props();
  const cartStore = getCartStore();
  const ui = getClientUi();

  // --- STATE MANAGEMENT (RUNES) ---
  let stats = $state<ReviewStats | null>(null);
  let activeImageIndex = $state(0);
  let selectedIndices = $state<number[]>([]);
  let quantity = $state(1);
  let selectedVouchers = $state<string[]>([]);
  let isViralUnlocked = $state(false);

  // Time for Flash Sale
  let timeLeft = $state({ hours: 0, minutes: 0, seconds: 0 });

  // --- DERIVED INTELLIGENCE ---
  const likeCount = $derived(Number(product.metadata?.viral_suite?.likes_count || product.metadata?.likes || 0));
  const isFlashSaleActive = $derived(!!product.metadata?.is_flash_sale);
  const pVariants = $derived((product.variants || []) as ProductVariant[]);
  
  const currentStock = $derived.by(() => {
    if (selectedIndices.length > 0) {
      const v = pVariants.find(pv => pv.id === product.id); // Simple case
      return v?.stock || product.stock || 0;
    }
    return product.stock || 0;
  });

  const pDiscountPrice = $derived(product.discountPrice || product.discount_price);
  
  const productInfo = $derived({
    barcode: (product.sku as string) || '',
    brand: (product.metadata?.brand as string) || (product.attributes?.brand as string) || (product.attributes?.['Thương hiệu'] as string) || 'Osmo Elite',
    origin: (product.metadata?.origin as string) || (product.attributes?.origin as string) || (product.attributes?.['Xuất xứ'] as string) || 'Nhật Bản',
    weight: (product.metadata?.weight as string) || (product.attributes?.weight as string) || (product.attributes?.['Trọng lượng'] as string) || '30g',
    originalPrice: pDiscountPrice ? (product.price || product.base_price || 0) : (product.price || 0) * 1.55,
    salePrice: (pDiscountPrice as number) || (product.price as number) || 0
  });

  const activePrices = $derived({
    sale: productInfo.salePrice,
    original: productInfo.originalPrice
  });

  const visibleAttributes = $derived(
    product.attributes ? Object.entries(product.attributes).filter(([k]) => {
      const key = k.toLowerCase();
      return !(['xuất xứ', 'origin', 'trọng lượng', 'quy cách', 'weight', 'mã vạch', 'barcode', 'thương hiệu', 'brand'].includes(key));
    }) as [string, string | number | boolean | null][] : []
  );

  const productVouchers = $derived.by(() => {
    let vouchers: VoucherUI[] = [];
    if (product.metadata?.vouchers) {
       vouchers = product.metadata.vouchers as VoucherUI[];
    } else {
      vouchers = cartStore.vouchers.map(v => ({
        id: v.id,
        label: v.title || v.id,
        sub: v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : `Giảm ${formatCurrency(v.value)}`),
        type: v.type === 'SHIPPING' ? 'ship' : 'discount'
      } as VoucherUI));
    }
    return vouchers.filter(v => {
      const isViral = v.id.includes('VIRAL') || v.label.toUpperCase().includes('VIRAL');
      return !isViral || isViralUnlocked;
    });
  });

  const activeGifts = $derived(product.metadata?.gifts || []);
  const activeComboQty = $derived(1); // Simplified for refactor

  const helenAdvice = $derived.by(() => {
    return "Cơ hội sở hữu liệu trình chuyên sâu với ưu đãi độc quyền. Hãy chọn số lượng phù hợp để tối ưu kết quả.";
  });

  const currentImage = $derived.by(() => {
    const pImages = product.images || [];
    return pImages[activeImageIndex] || pImages[0] || (product.metadata?.image_url as string) || '';
  });

  // --- ACTIONS ---
  function handleSelectOption(tIdx: number, oIdx: number) {
    selectedIndices[tIdx] = oIdx;
    if (tIdx === 0) activeImageIndex = oIdx;
  }

  function handleQuantityChange(delta: number) {
    const next = quantity + delta;
    if (next >= 1 && next <= (currentStock || 99)) {
      quantity = next;
    }
  }

  function toggleVoucher(id: string) {
    if (selectedVouchers.includes(id)) {
      selectedVouchers = selectedVouchers.filter(v => v !== id);
    } else {
      selectedVouchers = [...selectedVouchers, id];
    }
  }

  async function handleAddToCart() {
    ui.showLoading(true);
    try {
      await cartStore.addItem(product.id, quantity);
      ui.showToast('Đã thêm vào giỏ hàng', 'success');
    } catch (e) {
      ui.showToast('Không thể thêm sản phẩm', 'error');
    } finally {
      ui.showLoading(false);
    }
  }

  function handleBuyNow() {
    handleAddToCart().then(() => {
      window.location.href = '/checkout';
    });
  }

  // --- LIFECYCLE ---
  onMount(async () => {
    isViralUnlocked = !!localStorage.getItem(`viral_unlocked_${product.id}`);
    
    if (product?.id) {
      try {
        stats = await apiClient.get<ReviewStats>(`/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`);
      } catch (e) {
        console.error("Failed to load review stats", e);
      }
    }

    if (isFlashSaleActive) {
      const timer = setInterval(() => {
        const now = new Date();
        timeLeft = {
          hours: 23 - now.getHours(),
          minutes: 59 - now.getMinutes(),
          seconds: 59 - now.getSeconds()
        };
      }, 1000);
      return () => clearInterval(timer);
    }
  });
</script>

<div class="elite-landing-container" in:fade={{ duration: 400 }}>
  <!-- Main Product Section -->
  <div class="product-main-card">
    <div class="content-grid">
      <!-- Left: Gallery Module -->
      <LandingProductGallery 
        {product}
        {currentImage}
        {activeImageIndex}
        {isFlashSaleActive}
        {likeCount}
        {productInfo}
        onThumbnailClick={(idx) => activeImageIndex = idx}
      />

      <!-- Right: Info Module -->
      <LandingProductInfo 
        {product}
        {stats}
        {isFlashSaleActive}
        {timeLeft}
        {productVouchers}
        {selectedVouchers}
        variations={pVariants}
        {selectedIndices}
        {quantity}
        {currentStock}
        {activePrices}
        {activeComboQty}
        {activeGifts}
        {helenAdvice}
        onSelectOption={handleSelectOption}
        onQuantityChange={handleQuantityChange}
        onToggleVoucher={toggleVoucher}
        onAddToCart={handleAddToCart}
        onBuyNow={handleBuyNow}
        onWriteReview={() => document.getElementById('product-reviews')?.scrollIntoView({ behavior: 'smooth' })}
        onViralUnlock={() => isViralUnlocked = true}
      />
    </div>

    <!-- Specs Module -->
    <LandingProductSpecs 
      {product}
      {visibleAttributes}
      {productInfo}
      onViewFullIngredients={() => ui.showToast('Đang tải danh sách thành phần...', 'info')}
    />

    <!-- Description & FAQ Module -->
    <LandingProductDescription {product} />

    <!-- Reviews Section -->
    <div id="product-reviews" class="reviews-section">
      <ProductDetailReviews {product} />
    </div>

    <!-- Related Products -->
    <div class="related-section">
      <ProductDetailRelated {product} />
    </div>
  </div>

  <!-- Interactive Dashboard (Fixed HUD) -->
  <InteractiveDashboard {product} />
</div>

<style>
  .elite-landing-container {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1rem;
    font-family: 'Be Vietnam Pro', sans-serif;
  }

  .product-main-card {
    background: white;
    border-radius: 4px;
    box-shadow: 0 1px 1px rgba(0, 0, 0, 0.05);
    overflow: hidden;
  }

  .content-grid {
    display: grid;
    grid-template-columns: 450px 1fr;
    gap: 2.5rem;
    padding: 1.25rem;
  }

  .reviews-section, .related-section {
    padding: 2.5rem 1.25rem;
    border-top: 1px solid #f3f4f6;
    background: #f9fafb;
  }

  @media (max-width: 1024px) {
    .content-grid {
      grid-template-columns: 1fr;
    }
    
    .product-main-card {
      box-shadow: none;
    }
  }
</style>
