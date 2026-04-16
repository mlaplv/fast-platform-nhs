<script lang="ts">
  import { onMount } from 'svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import type { Product } from '$lib/types';
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { Hash, ChevronRight, Droplet, Sparkles, Eye, Leaf, Smile, Waves, Pill } from 'lucide-svelte';
  import { browser } from '$app/environment';

  const ui = getClientUi();

  interface Props {
    isProductMode?: boolean;
    product?: Product | null;
    onAddToCart?: () => void;
    onBuyNow?: () => void;
    onChatOpen?: () => void;
  }
  let { 
    isProductMode = false, 
    product = null,
    onAddToCart,
    onBuyNow,
    onChatOpen
  }: Props = $props();

  let isShrunk = $state(false);
  let lastScrollY = 0;

  // State menu 
  let isMenuOpen = $state(false);
  let categoriesData = $state<Category[]>([]);
  let homeProducts = $state<Product[]>([]);
  let isLoadingCats = $state(false);
  let activeCategoryId = $state<string | null>(null);

  // Icon mapping thông minh (Dùng Emoji màu sắc cho Elite V2.2)
  function getFallbackIcon(name: string) {
    if (!name) return '✨';
    const n = name.toLowerCase();
    if (n.includes('serum') || n.includes('tinh chất')) return '💧';
    if (n.includes('mắt') || n.includes('eye')) return '👁️';
    if (n.includes('mặt nạ') || n.includes('mask')) return '🎭';
    if (n.includes('rửa mặt') || n.includes('sữa')) return '🧼';
    if (n.includes('dưỡng')) return '🧴';
    if (n.includes('trị mụn') || n.includes('mụn') || n.includes('thuốc')) return '💊';
    if (n.includes('môi') || n.includes('lip')) return '💄';
    return '✨'; 
  }

  // Theo dõi lỗi ảnh để fallback
  let brokenImages = $state<Record<string, boolean>>({});
  function handleImgError(id: string) {
    brokenImages[id] = true;
  }

  async function toggleMenu() {
    isMenuOpen = !isMenuOpen;
    if (isMenuOpen && categoriesData.length === 0 && !isLoadingCats) {
      isLoadingCats = true;
      try {
        const res = await fetch('/api/v1/client/home');
        if (res.ok) {
           const result = await res.json();
           categoriesData = result.categories || [];
           homeProducts = result.products || [];
           if (categoriesData.length > 0) {
             activeCategoryId = categoriesData[0].id;
           }
        }
      } catch (e) {
        console.error("Lỗi lấy danh mục:", e);
      } finally {
        isLoadingCats = false;
      }
    }
  }

  const activeCategory = $derived(categoriesData.find(c => c.id === activeCategoryId));
  
  // Tinh gọn sản phẩm của danh mục được chọn
  const categoryProducts = $derived.by(() => {
    if (!activeCategoryId || homeProducts.length === 0) return [];
    // Elite V2.2: Dùng == để so sánh linh hoạt ID string/number
    return homeProducts.filter(p => 
      p.categoryId === activeCategoryId || 
      p.category_id === activeCategoryId || 
      p.category_ids?.some((id: string) => id === activeCategoryId) ||
      p.categories?.some((c: {id: string}) => c.id === activeCategoryId)
    ).slice(0, 6);
  });

  $effect(() => {
    if (browser) {
      document.body.style.overflow = isMenuOpen ? 'hidden' : '';
    }
  });

  onMount(() => {
    const scroller = document.querySelector('.page-container') || window;
    const handleScroll = () => {
      const currentScrollY = scroller === window ? window.scrollY : (scroller as Element).scrollTop;
      if (currentScrollY > lastScrollY + 10 && currentScrollY > 80) {
        if (!isShrunk) isShrunk = true;
        if (isMenuOpen) toggleMenu(); // Auto close
        lastScrollY = currentScrollY;
      } else if (currentScrollY < lastScrollY - 10 || currentScrollY <= 80) {
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
  <!-- Overlay -->
  <button 
    class="tbn-bubble-overlay" 
    style="z-index: {Z_INDEX_CLIENT.MOBILE_TAB_BAR - 1}"
    aria-label="Đóng menu"
    onclick={toggleMenu}
    in:fade={{ duration: 300 }} 
    out:fade={{ duration: 250 }}
  ></button>

  <!-- Bubble Menu iOS 26 Glass (No border radius, viền mỏng sáng) -->
  <div 
    class="tbn-bubble-glass"
    style="z-index: {Z_INDEX_CLIENT.MOBILE_TAB_BAR - 1}"
    in:fly={{ y: 80, duration: 400, opacity: 0, easing: cubicOut }}
    out:fly={{ y: 80, duration: 300, opacity: 0 }}
  >
     <div class="tbn-bubble-inner">
       <div class="tbn-bubble-glow" aria-hidden="true"></div>
       
       <!-- Sidebar -->
       <div class="tbn-sidebar">
          {#if isLoadingCats && categoriesData.length === 0}
             {#each Array(6) as _}
               <div class="tbn-skeleton-side"></div>
             {/each}
          {:else}
             {#each categoriesData as cat}
               <button 
                 class="tbn-side-btn {activeCategoryId === cat.id ? 'active' : ''}"
                 onclick={() => activeCategoryId = cat.id}
               >
                 {#if (cat.icon || cat.thumbnail || cat.image) && !brokenImages[cat.id]}
                   <img 
                     src={cat.icon || cat.thumbnail || cat.image} 
                     class="tbn-side-icon" 
                     alt={cat.name} 
                     loading="lazy" 
                     onerror={() => handleImgError(cat.id)}
                   />
                 {:else}
                   <div class="tbn-side-icon-placeholder">
                     <span class="text-xl">{getFallbackIcon(cat.name)}</span>
                   </div>
                 {/if}
                 <span class="tbn-side-txt line-clamp-2">{cat.name}</span>
               </button>
             {/each}
          {/if}
       </div>

       <!-- Grid Content -->
       <div class="tbn-content">
          <div class="tbn-content-header">
             <h3 class="tbn-content-title">
               {activeCategory?.name || 'Danh mục'}
             </h3>
             <a href={`/${activeCategory?.slug || ''}`} onclick={toggleMenu} class="tbn-content-link group">
               <span class="text-xs font-medium text-gray-500 group-hover:text-luxury-copper transition-colors">Xem tất cả</span>
               <ChevronRight class="w-3.5 h-3.5 text-gray-400 group-hover:text-luxury-copper transform group-hover:translate-x-0.5 transition-all" />
             </a>
          </div>

          <div class="tbn-content-grid">
             {#if isLoadingCats && categoriesData.length === 0}
                {#each Array(6) as _}
                  <div class="tbn-skeleton-card"></div>
                {/each}
             {:else}
                <!-- 1. Ưu tiên danh mục con -->
                {#if activeCategory?.children && activeCategory.children.length > 0}
                  {#each activeCategory.children as child}
                    <a href={`/${child.slug}`} onclick={toggleMenu} class="tbn-cat-card active:scale-[0.96]">
                      <div class="tbn-cat-img-wrapper">
                        {#if (child.image || child.thumbnail || child.icon) && !brokenImages[child.id]}
                          <img 
                            src={child.image || child.thumbnail || child.icon} 
                            alt={child.name} 
                            loading="lazy" 
                            onerror={() => handleImgError(child.id)}
                          />
                        {:else}
                          <div class="tbn-cat-noimg scale-125">
                            {getFallbackIcon(child.name)}
                          </div>
                        {/if}
                      </div>
                      <span class="tbn-cat-title">{child.name}</span>
                    </a>
                  {/each}
                
                <!-- 2. Không có con -> Hiển thị Sản phẩm Tinh gọn -->
                {:else if categoryProducts && categoryProducts.length > 0}
                  {#each categoryProducts as prod}
                    <a href={`/${prod.slug}`} onclick={toggleMenu} class="tbn-cat-card active:scale-[0.96]">
                      <div class="tbn-cat-img-wrapper">
                         <!-- Backend có thể trả `images` list hoặc `thumbnail` hoặc `image` string tùy model Pydantic -->
                         {#if Array.isArray(prod.images) && prod.images.length > 0}
                           <img src={prod.images[0]} alt={prod.name} loading="lazy" />
                         {:else if prod.thumbnail || prod.image}
                           <img src={prod.thumbnail || prod.image} alt={prod.name} loading="lazy" />
                         {:else}
                           <div class="tbn-cat-noimg text-luxury-copper"><Sparkles class="w-5 h-5"/></div>
                         {/if}
                      </div>
                      <span class="tbn-cat-title text-left !font-bold pt-1">{prod.name}</span>
                      <span class="text-[8px] font-black text-luxury-copper">
                        {(prod.discountPrice || prod.discount_price || prod.price || 0).toLocaleString('vi-VN')}₫
                      </span>
                    </a>
                  {/each}
                
                <!-- 3. Rỗng hoàn toàn -->
                {:else}
                    <div class="tbn-cat-empty">
                       <Sparkles class="w-8 h-8 text-stone-300 mb-2" />
                       <p>Đang cập nhật</p>
                    </div>
                {/if}
             {/if}
          </div>
       </div>

     </div>
  </div>
{/if}

<!-- ... giữ nguyên nav ... -->
<nav class="tbn-nav {isShrunk ? 'tbn-nav--shrunk' : ''}" style="z-index: {Z_INDEX_CLIENT.MOBILE_TAB_BAR};">
  <div class="tbn-nav-inner">
    {#if !isProductMode}
      <button class="tbn-item {isMenuOpen ? 'tbn-item--active' : ''}" aria-label="Menu" onclick={toggleMenu}>
        <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          {#if isMenuOpen}
             <path d="M18 6L6 18M6 6l12 12" />
          {:else}
             <path d="M4 7h16M9 12h11M4 17h16" />
          {/if}
        </svg>
        <span class="tbn-label">{isMenuOpen ? 'Đóng' : 'Menu'}</span>
      </button>
    {/if}

    <button class="tbn-item" aria-label="Hotline" onclick={() => window.location.href = 'tel:0968123159'}>
      <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
      </svg>
      <span class="tbn-label">Hotline</span>
    </button>

    <button class="tbn-item tbn-item--ai {isMenuOpen ? 'opacity-30' : ''}" aria-label="AI Chat" onclick={() => { if(!isMenuOpen) onChatOpen?.(); }}>
      <div class="tbn-ai-tooltip"><span class="tbn-ai-tooltip-text">AI agentic hỗ trợ</span></div>
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
          <span class="buy-sub">{(product.discount_price || product.price).toLocaleString('vi-VN')}₫ | Freeship</span>
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

  /* OVERLAY */
  .tbn-bubble-overlay {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    width: 100vw; height: 100vh;
    background: rgba(255, 255, 255, 0.2); 
    backdrop-filter: blur(20px) saturate(150%); -webkit-backdrop-filter: blur(20px) saturate(150%);
    border: none; cursor: default;
  }

  /* IOS 26 LIQUID GLASS: No border radius, viền mỏng siêu sáng */
  .tbn-bubble-glass {
    position: fixed;
    bottom: calc(max(env(safe-area-inset-bottom), 12px) + 54px);
    left: 12px; right: 12px;
    height: 52vh;
    background: rgba(255, 255, 255, 0.7); 
    backdrop-filter: saturate(250%) blur(50px); -webkit-backdrop-filter: saturate(250%) blur(50px);
    /* Bỏ border-radius, hoặc để 0px */
    border-radius: 0px; 
    border: 0.5px solid rgba(255, 255, 255, 0.95);
    box-shadow: 
      0 30px 60px rgba(0, 0, 0, 0.15),
      inset 0 1px 2px rgba(255, 255, 255, 1);
    overflow: hidden;
    transform-origin: center bottom;
  }

  .tbn-bubble-inner {
    display: flex; height: 100%; width: 100%; position: relative;
  }

  .tbn-bubble-glow {
    position: absolute; top: -50px; left: -50px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(193, 143, 126, 0.15) 0%, transparent 60%);
    pointer-events: none;
  }

  /* SIDEBAR */
  .tbn-sidebar {
    width: 86px; flex-shrink: 0; height: 100%;
    overflow-y: auto; overflow-x: hidden;
    background: rgba(240, 240, 240, 0.4);
    border-right: 0.5px solid rgba(0, 0, 0, 0.05);
    scrollbar-width: none; padding-bottom: 20px;
  }
  .tbn-sidebar::-webkit-scrollbar { display: none; }

  .tbn-side-btn {
    width: 100%; padding: 14px 4px; display: flex; flex-direction: column; align-items: center; gap: 6px;
    border: none; background: transparent; cursor: pointer; transition: all 0.25s ease; position: relative;
  }
  .tbn-side-btn.active { background: rgba(255, 255, 255, 0.7); box-shadow: inset 3px 0 0 #c18f7e; }

  /* Bỏ border-radius của icon để đồng bộ iOS 26 Sharp glass */
  .tbn-side-icon, .tbn-side-icon-placeholder {
    width: 32px; height: 32px; border-radius: 0; 
    object-fit: cover; box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    background: #fff; padding: 2px; transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    border: 0.5px solid rgba(0,0,0,0.05); /* Viền mỏng */
  }

  .tbn-side-icon-placeholder { display: flex; align-items: center; justify-content: center; color: #777; background: rgba(255,255,255,0.5); }
  .tbn-side-btn.active .tbn-side-icon, .tbn-side-btn.active .tbn-side-icon-placeholder {
    transform: scale(1.12) translateY(-2px); box-shadow: 0 8px 16px rgba(193, 143, 126, 0.25);
  }

  .tbn-side-txt { font-size: 9px; font-weight: 700; color: #777; text-align: center; line-height: 1.2; transition: color 0.2s ease; }
  .tbn-side-btn.active .tbn-side-txt { color: #c18f7e; font-weight: 900; }

  /* GRID CONTENT */
  .tbn-content {
    flex: 1; overflow-y: auto; overflow-x: hidden; position: relative; padding: 14px 16px 20px 16px; scrollbar-width: none;
  }
  .tbn-content::-webkit-scrollbar { display: none; }

  .tbn-content-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
  .tbn-content-title { font-size: 11px; font-weight: 900; color: #222; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; padding-right: 6px; }
  .tbn-content-link { font-size: 9px; font-weight: 800; color: #c18f7e; text-transform: uppercase; display: flex; align-items: center; gap: 2px; text-decoration: none; white-space: nowrap; }

  .tbn-content-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px 10px; }
  .tbn-cat-card { display: flex; flex-direction: column; align-items: center; gap: 6px; text-decoration: none; -webkit-tap-highlight-color: transparent; transition: transform 0.2s ease; }

  /* Loại bỏ border-radius hình ảnh, bo viền mỏng sáng iOS 26 */
  .tbn-cat-img-wrapper {
    width: 100%; aspect-ratio: 1; border-radius: 0;
    overflow: hidden; background: #fff;
    box-shadow: 0 4px 10px rgba(0,0,0,0.06);
    border: 0.5px solid rgba(255, 255, 255, 1); /* Sáng bong bóng */
    outline: 0.5px solid rgba(0,0,0,0.03); /* Chống lẹm màu */
  }

  .tbn-cat-img-wrapper img { width: 100%; height: 100%; object-fit: cover; }
  .tbn-cat-noimg { width: 100%; height: 100%; background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(245,245,245,0.5)); display: flex; align-items: center; justify-content: center; color: #aaa; }
  .tbn-cat-title { font-size: 9px; font-weight: 600; color: #444; line-height: 1.2; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-align: center; }
  .tbn-cat-empty { grid-column: span 3; display: flex; flex-direction: column; align-items: center; justify-content: center; opacity: 0.5; padding: 30px 0; color: #888; }

  /* SKELETON */
  .tbn-skeleton-side { width: calc(100% - 12px); height: 50px; margin: 6px; border-radius: 0; background: rgba(0,0,0,0.05); animation: pulse 1.5s infinite; }
  .tbn-skeleton-card { width: 100%; aspect-ratio: 1; border-radius: 0; background: rgba(0,0,0,0.05); animation: pulse 1.5s infinite; }
  @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 0.3; } 100% { opacity: 0.6; } }

  /* NAV (Bottom Bar Original) */
  .tbn-nav { position: fixed; bottom: max(env(safe-area-inset-bottom), 12px); left: 50%; translate: -50% 0; width: max-content; max-width: calc(100vw - 16px); height: 44px; background: rgba(255, 255, 255, 0.98); backdrop-filter: saturate(180%) blur(20px); -webkit-backdrop-filter: saturate(180%) blur(20px); border: 1px solid rgba(0, 0, 0, 0.05); border-radius: 16px; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15), 0 2px 4px rgba(0,0,0,0.05); display: flex; align-items: center; justify-content: center; overflow: visible; transform-origin: center bottom; transition: all 0.35s cubic-bezier(0.25, 1, 0.5, 1); }
  .tbn-nav-inner { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; gap: 4px; padding: 0 6px; }
  .tbn-nav--shrunk { height: 34px; border-radius: 17px; translate: -50% 4px; background: rgba(255, 255, 255, 0.6); }
  .tbn-item { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; background: none; border: none; cursor: pointer; color: #444; transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1); height: 100%; flex: 0 0 auto; padding: 0 10px; min-width: 54px; }
  .tbn-item--active { color: #c18f7e !important; }
  .tbn-item--active .tbn-icon { transform: scale(1.1); color: #c18f7e; }
  .tbn-item:active { opacity: 0.6; transform: scale(0.95); }
  .tbn-icon { width: 20px; height: 20px; transition: transform 0.3s ease; }
  .tbn-label { font-size: 9px; font-weight: 700; line-height: 1; white-space: nowrap; transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1); transform-origin: top center; }
  .tbn-nav--shrunk .tbn-label { opacity: 0; height: 0; transform: scaleY(0); margin-top: 0; }
  .tbn-nav--shrunk .tbn-item { gap: 0; padding: 0 6px; min-width: 38px; }
  .tbn-nav--shrunk .tbn-nav-inner { gap: 0px; padding: 0 6px; }
  .tbn-nav--shrunk .tbn-icon { transform: scale(1.05); color: #111; }

  /* AI CHAT */
  .tbn-label--ai { background: linear-gradient(90deg, #C18F7E, #E3B5A4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; }
  .tbn-ai-tooltip { position: absolute; top: -38px; right: -18px; background: rgba(255, 255, 255, 0.95); backdrop-filter: saturate(200%) blur(30px); -webkit-backdrop-filter: saturate(200%) blur(30px); border: none; height: 28px; padding: 0 14px; display: flex; align-items: center; justify-content: center; border-radius: 16px; white-space: nowrap; filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.12)); pointer-events: none; transition: all 0.35s cubic-bezier(0.25, 1, 0.5, 1); animation: floatTooltip 2.5s infinite ease-in-out; }
  .tbn-ai-tooltip-text { background: linear-gradient(90deg, #C18F7E, #E3B5A4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 11px; font-weight: 900; line-height: 1; margin-top: 1px; }
  .tbn-ai-tooltip::after { content: ''; position: absolute; bottom: -6px; right: 38px; border-width: 6px 7px 0; border-style: solid; border-color: rgba(255, 255, 255, 0.95) transparent transparent transparent; }
  @keyframes floatTooltip { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
  .tbn-nav--shrunk .tbn-ai-tooltip { opacity: 0; transform: translateY(12px) scale(0.6); }

  /* FUSED CAPSULE */
  .tbn-action-group { display: flex; flex: 1; height: 100%; margin-left: 8px; margin-right: -6px; border-radius: 0 16px 16px 0; overflow: hidden; background: transparent; transform: translateZ(0); }
  .tbn-nav--shrunk .tbn-action-group { border-radius: 0 17px 17px 0; }
  .tbn-action-split { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; border: none; cursor: pointer; overflow: hidden; }
  .tbn-action-split::after { content: ''; position: absolute; inset: 0; background: currentColor; opacity: 0; transition: opacity 0.2s ease; }
  .tbn-action-split:active::after { opacity: 0.15; }
  .tbn-action-split--cart { width: 44px; background: transparent; color: #C18F7E; border-right: 1px dashed rgba(193, 143, 126, 0.15); }
  .tbn-action-split--buy { flex: 1; background: linear-gradient(110deg, #C18F7E 0%, #E3B5A4 100%); color: white; padding: 0 16px; }
  .buy-text { font-size: 13px; font-weight: 900; line-height: 1.1; text-shadow: 0 1px 2px rgba(0,0,0,0.1); letter-spacing: -0.2px; text-transform: uppercase; }
  .buy-sub { font-size: 9px; font-weight: 700; opacity: 0.95; letter-spacing: -0.1px; }

  :global(.text-luxury-copper) { color: #c18f7e; }
</style>
