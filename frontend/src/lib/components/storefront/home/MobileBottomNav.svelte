<script lang="ts">
  import { onMount } from 'svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import type { Product, Category } from '$lib/types';
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { Hash, ChevronRight, Droplet, Sparkles, Eye, Leaf, Smile, Waves, Pill } from 'lucide-svelte';
  import { browser } from '$app/environment';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import { formatCurrency } from '$lib/utils/format';

  const ui = getClientUi();
  const cartStore = getCartStore();

  const hasFreeship = $derived(cartStore.vouchers.some(v => v.is_default && v.type === 'SHIPPING'));

  interface Props {
    isProductMode?: boolean;
    product?: Product | null;
    onAddToCart?: () => void;
    onBuyNow?: () => void;
    onChatOpen?: () => void;
  }
  
  // Elite V2.2: Sanitize props with safe defaults (Avoid Svelte 5 Binding Trap)
  let { 
    isProductMode = false, 
    product = null,
    onAddToCart,
    onBuyNow,
    onChatOpen
  }: Props = $props();

  let isShrunk = $state(false);
  let lastScrollY = 0;

  // Elite V2.2: Opaque states with strict types
  let isMenuOpen = $state(false);
  let categoriesData = $state<Category[]>([]);
  let homeProducts = $state<Product[]>([]);
  let isLoadingCats = $state(false);
  let activeCategoryId = $state<string | null>(null);

  /**
   * TikTok Style Emoji Mapping (Mobile 2026)
   */
  function getFallbackIcon(name: string): string {
    if (!name) return '✨';
    const n = name.toLowerCase();
    
    // Ngành hàng Spa & Thẩm mỹ - Tách biệt rõ ràng để tránh trùng lặp
    if (n.includes('serum')) return '💧';
    if (n.includes('tinh chất') || n.includes('ampoule')) return '🧪'; // Tinh chất dùng ống nghiệm cho chuyên nghiệp
    if (n.includes('mắt') || n.includes('eye')) return '👁️';
    if (n.includes('mặt nạ') || n.includes('mask')) return '🎭';
    if (n.includes('rửa mặt') || n.includes('sữa cleanser')) return '🧼';
    if (n.includes('dưỡng ẩm') || n.includes('kem')) return '🧴';
    if (n.includes('trị mụn') || n.includes('mụn') || n.includes('treatment')) return '💊';
    if (n.includes('môi') || n.includes('lip') || n.includes('son')) return '💄';
    if (n.includes('chống nắng') || n.includes('sun')) return '☀️';
    
    // Ngành hàng TPCN & Chăm sóc tóc
    if (n.includes('tóc') || n.includes('hair') || n.includes('gội')) return '💇‍♀️';
    if (n.includes('thực phẩm') || n.includes('vitamin') || n.includes('supplement')) return '🥗';
    if (n.includes('body') || n.includes('tắm')) return '🛁';
    
    return '✨'; 
  }

  // Helper kiểm tra xem chuỗi có phải URL ảnh không
  function isImageUrl(url: string | undefined): boolean {
    if (!url) return false;
    return url.startsWith('http') || url.startsWith('/') || url.includes('.');
  }

  // Theo dõi lỗi ảnh để fallback
  let brokenImages = $state<Record<string, boolean>>({});
  function handleImgError(id: string) {
    brokenImages[id] = true;
  }

  async function toggleMenu() {
    // Elite V2.2: Chặn Double-call khi đang tải
    if (isLoadingCats) return;

    isMenuOpen = !isMenuOpen;
    
    if (isMenuOpen && categoriesData.length === 0) {
      isLoadingCats = true;
      try {
        const res = await fetch('/api/v1/client/home');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        
        const result = await res.json();
        categoriesData = (result.categories || []) as Category[];
        homeProducts = (result.products || []) as Product[];
        
        if (categoriesData.length > 0 && !activeCategoryId) {
          activeCategoryId = categoriesData[0].id;
        }
      } catch (e) {
        // Elite V2.2: No silent fail
        console.error("[NAV] Lỗi lấy danh mục:", e);
      } finally {
        isLoadingCats = false;
      }
    }
  }

  const activeCategory = $derived(categoriesData.find(c => c.id === activeCategoryId));
  
  /**
   * Optimized Product Filtering (Type-safe)
   */
  const categoryProducts = $derived.by((): Product[] => {
    if (!activeCategoryId || homeProducts.length === 0) return [];
    
    return homeProducts.filter((p: Product) => {
      // Hợp nhất các trường ID từ các phiên bản API khác nhau
      const matchId = p.categoryId === activeCategoryId || p.category_id === activeCategoryId;
      const matchIds = p.category_ids?.some(id => id === activeCategoryId);
      const matchObj = p.categories?.some(c => c.id === activeCategoryId);
      return matchId || matchIds || matchObj;
    }).slice(0, 9); // Tăng giới hạn lên 9 sản phẩm cho layout TikTok mới
  });

  // Body scroll lock
  $effect(() => {
    if (browser) {
      document.body.style.overflow = isMenuOpen ? 'hidden' : '';
    }
  });

  onMount(() => {
    // Tìm container cuộn chính hoặc fallback window
    const scroller = document.querySelector('.page-container') || window;
    
    const handleScroll = () => {
      const currentScrollY = scroller === window ? window.scrollY : (scroller as Element).scrollTop;
      
      // Ngưỡng cuộn tối ưu (Elite Scroll)
      const threshold = 15;
      if (currentScrollY > lastScrollY + threshold && currentScrollY > 80) {
        if (!isShrunk) isShrunk = true;
        if (isMenuOpen) toggleMenu(); // Tự động đóng menu khi cuộn xuống
        lastScrollY = currentScrollY;
      } else if (currentScrollY < lastScrollY - threshold || currentScrollY <= 80) {
        if (isShrunk) isShrunk = false;
        lastScrollY = currentScrollY;
      }
    };

    scroller.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
      scroller.removeEventListener('scroll', handleScroll);
      if (browser) document.body.style.overflow = '';
    };
  });
</script>

{#if isMenuOpen && !isProductMode}
  <!-- TikTok Style Black Overlay -->
  <button 
    class="tbn-bottom-sheet-overlay" 
    style="z-index: var(--z-mobile-bottom-sheet-overlay, 20000)"
    aria-label="Đóng menu"
    onclick={toggleMenu}
    in:fade={{ duration: 300 }} 
    out:fade={{ duration: 250 }}
  ></button>

  <!-- TikTok Style Bottom Sheet (Opaque White) -->
  <div 
    class="tbn-bottom-sheet"
    style="z-index: var(--z-mobile-bottom-sheet, 20001)"
    in:fly={{ y: '100%', duration: 400, opacity: 1, easing: cubicOut }}
    out:fly={{ y: '100%', duration: 300, opacity: 1 }}
  >
     <!-- Grab Handle -->
     <div class="tbn-grab-handle-area" onclick={toggleMenu}>
        <div class="tbn-grab-handle"></div>
     </div>

     <div class="tbn-sheet-inner">
       <!-- Sidebar (Opaque Light Gray) -->
       <div class="tbn-sidebar">
          {#if isLoadingCats && categoriesData.length === 0}
             {#each Array(8) as _}
               <div class="tbn-skeleton-side"></div>
             {/each}
          {:else}
             {#each categoriesData as cat}
               <button 
                 class="tbn-cat-item {activeCategoryId === cat.id ? 'active' : ''}"
                 onclick={() => activeCategoryId = cat.id}
               >
                 <div class="tbn-cat-icon-wrap">
                   {#if isImageUrl(cat.image || cat.thumbnail || cat.icon) && !brokenImages[cat.id]}
                     <img 
                       src={cat.image || cat.thumbnail || cat.icon} 
                       alt={cat.name} 
                       class="tbn-cat-img"
                       loading="lazy" 
                       onerror={() => handleImgError(cat.id)}
                     />
                   {:else if cat.icon && !isImageUrl(cat.icon)}
                      <!-- Hiển thị icon trực tiếp nếu là Emoji từ Database (Giống Desktop) -->
                      <div class="tbn-cat-placeholder">
                        <span class="tbn-cat-emoji">{cat.icon}</span>
                      </div>
                   {:else}
                     <!-- Fallback thông minh theo tên nếu Database trống -->
                     <div class="tbn-cat-placeholder">
                       <span class="tbn-cat-emoji">{getFallbackIcon(cat.name)}</span>
                     </div>
                   {/if}
                   
                   {#if activeCategoryId === cat.id}
                      <div class="tbn-cat-glow" in:fade></div>
                   {/if}
                 </div>
                 <span class="tbn-cat-name">{cat.name}</span>
               </button>
             {/each}
          {/if}
       </div>

       <!-- Grid Content (Opaque White) -->
       <div class="tbn-content">
          <div class="tbn-content-header">
             <h3 class="tbn-content-title">
               {activeCategory?.name || 'Danh mục'}
             </h3>
             <a href={`/${activeCategory?.slug || ''}/`} onclick={toggleMenu} class="tbn-content-link group">
               <span>Xem tất cả</span>
               <ChevronRight class="w-3.5 h-3.5" />
             </a>
          </div>

          <div class="tbn-content-grid">
             {#if isLoadingCats && categoriesData.length === 0}
                {#each Array(9) as _}
                  <div class="tbn-skeleton-card"></div>
                {/each}
             {:else}
                <!-- Categorized Children -->
                {#if activeCategory?.children && activeCategory.children.length > 0}
                  {#each activeCategory.children as child}
                    <a href={`/${child.slug}/`} onclick={toggleMenu} class="tbn-cat-card">
                      <div class="tbn-cat-img-wrapper">
                        {#if (child.image || child.thumbnail || child.icon) && !brokenImages[child.id]}
                          <img 
                            src={child.image || child.thumbnail || child.icon} 
                            alt={child.name} 
                            loading="lazy" 
                            onerror={() => handleImgError(child.id)}
                          />
                        {:else}
                          <div class="tbn-cat-noimg text-xl">
                            {getFallbackIcon(child.name)}
                          </div>
                        {/if}
                      </div>
                      <span class="tbn-cat-title">{child.name}</span>
                    </a>
                  {/each}
                
                <!-- Fallback to Products -->
                {:else if categoryProducts && categoryProducts.length > 0}
                  {#each categoryProducts as prod}
                    <a href={`/${prod.slug}/`} onclick={toggleMenu} class="tbn-cat-card">
                      <div class="tbn-cat-img-wrapper">
                         {#if Array.isArray(prod.images) && prod.images.length > 0}
                           <img src={prod.images[0]} alt={prod.name} loading="lazy" />
                         {:else if prod.thumbnail || prod.image}
                           <img src={prod.thumbnail || prod.image} alt={prod.name} loading="lazy" />
                         {:else}
                           <div class="tbn-cat-noimg text-luxury-copper"><Sparkles class="w-5 h-5"/></div>
                         {/if}
                      </div>
                      <span class="tbn-cat-title text-left !font-bold pt-1">{prod.name}</span>
                      <span class="text-[10px] font-black text-luxury-copper mt-0.5">
                        {formatCurrency(prod.discountPrice || prod.discount_price || prod.price || 0)}
                      </span>
                    </a>
                  {/each}
                {:else}
                    <div class="tbn-cat-empty">
                       <Sparkles class="w-8 h-8 text-gray-200 mb-2" />
                       <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Đang cập nhật</p>
                    </div>
                {/if}
             {/if}
          </div>
       </div>

     </div>
  </div>
{/if}

<!-- ... giữ nguyên nav ... -->
<nav class="tbn-nav {isShrunk ? 'tbn-nav--shrunk' : ''}" style="z-index: var(--z-mobile-tab-bar, 100);">
  <div class="tbn-nav-inner">
    {#if !isProductMode}
      <button class="tbn-item {isMenuOpen ? 'tbn-item--active' : ''}" aria-label="Menu" onclick={toggleMenu}>
        <div class="relative flex flex-col items-center">
          <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            {#if isMenuOpen}
               <path d="M18 6L6 18M6 6l12 12" />
            {:else}
               <path d="M4 7h16M9 12h11M4 17h16" />
            {/if}
          </svg>
          <span class="tbn-label">{isMenuOpen ? 'Đóng' : 'Menu'}</span>
        </div>
      </button>
    {/if}

    <button class="tbn-item" aria-label="Hotline" onclick={() => window.location.href = 'tel:0968123159'}>
      <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
      </svg>
      <span class="tbn-label">Hotline</span>
    </button>

    <button class="tbn-item tbn-item--ai {isMenuOpen ? 'opacity-30' : ''}" aria-label="AI Chat" onclick={() => { if(!isMenuOpen) (onChatOpen ? onChatOpen() : supportAgent.open()); }}>
      <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <defs>
          <linearGradient id="ai-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#C18F7E" /><stop offset="100%" stop-color="#E3B5A4" />
          </linearGradient>
        </defs>
        <path d="M12 2l2.4 5.6 5.6 2.4-5.6 2.4L12 18l-2.4-5.6-5.6-2.4 5.6-2.4L12 2z" stroke="url(#ai-grad)" fill="url(#ai-grad)" fill-opacity="0.2"/>
        <path d="M19 19l1.2 2.8 2.8 1.2-2.8 1.2L19 27l-1.2-2.8-2.8-1.2 2.8-1.2z" transform="scale(0.5) translate(22, 12)" stroke="url(#ai-grad)"/>
        <path d="M5 19l1.2 2.8 2.8 1.2-2.8 1.2L5 27l-1.2-2.8-2.8-1.2 2.8-1.2z" transform="scale(0.3) translate(0, 40)" stroke="url(#ai-grad)"/>
      </svg>
      <span class="tbn-label tbn-label--ai">AI Chat</span>
    </button>

    {#if isProductMode && product}
      <div class="tbn-action-group">
        <button class="tbn-action-split tbn-action-split--cart" aria-label="Thêm vào giỏ hàng" onclick={() => onAddToCart?.()}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/><path d="M12 9h4M14 7v4" />
          </svg>
        </button>
        <button class="tbn-action-split tbn-action-split--buy" aria-label="Mua ngay" onclick={() => onBuyNow?.()}>
          <span class="buy-text">Mua ngay</span>
          <span class="buy-sub">{formatCurrency(product.discount_price || product.price || 0)} {hasFreeship ? '| Freeship' : ''}</span>
        </button>
      </div>
    {/if}

    {#if !isProductMode}
      <button onclick={() => { if (!authStore.isAuthenticated) ui.openLogin(); else window.location.href = '/user/profile'; }} class="tbn-item" aria-label="Tài khoản">
        <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
        </svg>
        <span class="tbn-label">Tài khoản</span>
      </button>
    {/if}
  </div>
</nav>

<style>
  *, *::before, *::after { box-sizing: border-box; }

  /* TIKTOK STYLE OVERLAY */
  .tbn-bottom-sheet-overlay {
    position: fixed; inset: 0;
    width: 100vw; height: 100vh;
    background: rgba(0, 0, 0, 0.6); 
    border: none; cursor: default;
    z-index: var(--z-mobile-bottom-sheet-overlay, 20000);
  }

  /* TIKTOK STYLE BOTTOM SHEET (OPAQUE WHITE) */
  .tbn-bottom-sheet {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    height: 88vh;
    background: #FFFFFF; /* Màu trắng đặc theo yêu cầu của Sếp */
    border-radius: 32px 32px 0 0; 
    box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.2);
    overflow: hidden;
    display: flex; flex-direction: column;
    z-index: var(--z-mobile-bottom-sheet, 20001);
  }

  /* Grab Handle TikTok style */
  .tbn-grab-handle-area {
    width: 100%; height: 32px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; cursor: pointer;
  }
  .tbn-grab-handle {
    width: 36px; height: 4px; background: #E5E5E5; border-radius: 2px;
  }

  .tbn-sheet-inner {
    display: flex; flex: 1; width: 100%; overflow: hidden;
  }

  /* SIDEBAR (Light Gray Opaque) */
  .tbn-sidebar {
    width: 90px; flex-shrink: 0; height: 100%;
    overflow-y: auto; overflow-x: hidden;
    background: #F9F9F9; /* Màu đặc, không opacity */
    scrollbar-width: none; padding-bottom: 40px;
  }
  .tbn-sidebar::-webkit-scrollbar { display: none; }

  .tbn-cat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 6px;
    gap: 6px;
    width: 100%;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: none;
    background: transparent;
    cursor: pointer;
  }

  .tbn-cat-item.active {
    background: #FFFFFF;
    position: relative;
  }

  .tbn-cat-item.active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 20%;
    bottom: 20%;
    width: 3px;
    background: #C18F7E;
    border-radius: 0 4px 4px 0;
  }

  .tbn-cat-icon-wrap {
    position: relative;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
  }

  .tbn-cat-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 14px;
    border: 0.5px solid rgba(193, 143, 126, 0.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    background: #fff;
  }

  .tbn-cat-placeholder {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #FDFBFB 0%, #EBEDEE 100%);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 0.5px solid rgba(0, 0, 0, 0.03);
  }

  .tbn-cat-emoji {
    font-size: 20px;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
  }

  .tbn-cat-glow {
    position: absolute;
    inset: -4px;
    background: radial-gradient(circle, rgba(193, 143, 126, 0.25) 0%, transparent 70%);
    z-index: -1;
    border-radius: 20px;
    animation: cat-pulse 2s infinite ease-in-out;
  }

  @keyframes cat-pulse {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.1); }
  }

  .tbn-cat-name {
    font-size: 10px;
    font-weight: 600;
    color: #666;
    text-align: center;
    line-height: 1.2;
    transition: color 0.3s;
  }

  .tbn-cat-item.active .tbn-cat-name {
    color: #C18F7E;
  }

  /* CONTENT AREA (Opaque White) */
  .tbn-content {
    flex: 1; overflow-y: auto; overflow-x: hidden; padding: 20px 16px 140px 16px; scrollbar-width: none; background: #FFFFFF;
  }
  .tbn-content::-webkit-scrollbar { display: none; }

  .tbn-content-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
  .tbn-content-title { font-size: 14px; font-weight: 900; color: #111; text-transform: uppercase; letter-spacing: 0.5px; }
  .tbn-content-link { font-size: 11px; font-weight: 800; color: #c18f7e; display: flex; align-items: center; gap: 4px; text-transform: uppercase; }

  .tbn-content-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px 12px; }
  .tbn-cat-card { display: flex; flex-direction: column; align-items: center; gap: 8px; text-decoration: none; transition: transform 0.15s ease; }
  .tbn-cat-card:active { transform: scale(0.95); }

  .tbn-cat-img-wrapper {
    width: 100%; aspect-ratio: 1; border-radius: 16px;
    overflow: hidden; background: #F5F5F5;
    border: 1px solid #F0F0F0;
  }

  .tbn-cat-img-wrapper img { width: 100%; height: 100%; object-fit: cover; }
  .tbn-cat-noimg { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #DDD; }
  .tbn-cat-title { font-size: 10px; font-weight: 700; color: #333; line-height: 1.3; text-align: center; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

  /* SKELETON */
  .tbn-skeleton-side { width: 60px; height: 60px; margin: 10px auto; border-radius: 12px; background: #F0F0F0; animation: pulse 1.5s infinite; }
  .tbn-skeleton-card { width: 100%; aspect-ratio: 1; border-radius: 16px; background: #F5F5F5; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%, 100% { opacity: 0.8; } 50% { opacity: 0.4; } }

  /* NAV (Bottom Bar Original) */
  .tbn-nav { position: fixed; bottom: max(env(safe-area-inset-bottom), 12px); left: 50%; translate: -50% 0; width: max-content; max-width: calc(100vw - 24px); height: 50px; background: #FFFFFF; border: 1px solid #F0F0F0; border-radius: 20px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1); display: flex; align-items: center; transition: all 0.3s cubic-bezier(0.2, 1, 0.3, 1); }
  .tbn-nav-inner { width: 100%; height: 100%; display: flex; align-items: center; gap: 4px; padding: 0 8px; }
  .tbn-nav--shrunk { height: 40px; border-radius: 14px; translate: -50% 6px; }
  
  .tbn-item { display: flex; flex-direction: column; align-items: center; justify-content: center; background: none; border: none; color: #666; transition: all 0.2s ease; height: 100%; min-width: 56px; padding: 0 8px; }
  .tbn-item--active { color: #000 !important; }
  .tbn-item:active { scale: 0.9; }
  
  .tbn-icon { width: 22px; height: 22px; margin-bottom: 2px; }
  .tbn-label { font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }

  .tbn-nav--shrunk .tbn-label { display: none; }
  .tbn-nav--shrunk .tbn-icon { margin-bottom: 0; scale: 0.9; }
  .tbn-nav--shrunk .tbn-item { min-width: 44px; }

  /* AI CHAT */
  .tbn-label--ai { background: linear-gradient(90deg, #C18F7E, #E3B5A4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; }
  @keyframes floatTooltip { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }

  /* FUSED CAPSULE (ACTION GROUP) */
  .tbn-action-group { display: flex; flex: 1; height: 100%; margin-left: 8px; margin-right: -6px; border-radius: 0 18px 18px 0; overflow: hidden; background: #000; }
  .tbn-action-split { display: flex; flex-direction: column; align-items: center; justify-content: center; border: none; cursor: pointer; transition: opacity 0.2s ease; }
  .tbn-action-split:active { opacity: 0.8; }
  .tbn-action-split--cart { width: 50px; background: #222; color: #FFF; border-right: 1px solid #333; }
  .tbn-action-split--buy { flex: 1; background: #000; color: #FFF; padding: 0 16px; }
  .buy-text { font-size: 13px; font-weight: 900; text-transform: uppercase; }
  .buy-sub { font-size: 9px; font-weight: 600; opacity: 0.7; }

  :global(.text-luxury-copper) { color: #c18f7e; }
</style>
