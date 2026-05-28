<script lang="ts">
  import { onMount } from 'svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import type { Product, Category } from '$lib/types';
  import { browser } from '$app/environment';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  
  import MobileBottomMenu from './MobileBottomMenu.svelte';
  import ProductMobileActions from '../product-detail/MainDetail/modules/ProductMobileActions.svelte';

  const ui = getClientUi();
  const cartStore = getCartStore();

  const hasFreeship = $derived(cartStore.vouchers.some(v => v.is_default && v.type === 'SHIPPING'));

  interface Props {
    isProductMode?: boolean;
    product?: Product | null;
    selectedVariant?: import('$lib/types').ProductVariant | null;
    onAddToCart?: () => void;
    onBuyNow?: () => void;
    onChatOpen?: () => void;
    scrolled?: boolean;
  }
  
  let { 
    isProductMode = false, 
    product = null,
    selectedVariant = null,
    onAddToCart,
    onBuyNow,
    onChatOpen,
    scrolled = false
  }: Props = $props();

  let isShrunk = $state(false);
  let isMini = $state(false);
  let isHidden = $state(false);
  let lastScrollY = 0;
  let isMenuOpen = $state(false);
  let categoriesData = $state<Category[]>([]);
  let homeProducts = $state<Product[]>([]);
  let isLoadingCats = $state(false);
  let activeCategoryId = $state<string | null>(null);
  let brokenImages = $state<Record<string, boolean>>({});

  function getFallbackIcon(name: string): string {
    if (!name) return '✨';
    const n = name.toLowerCase();
    if (n.includes('serum')) return '💧';
    if (n.includes('tinh chất') || n.includes('ampoule')) return '🧪';
    if (n.includes('mắt') || n.includes('eye')) return '👁️';
    if (n.includes('mặt nạ') || n.includes('mask')) return '🎭';
    if (n.includes('rửa mặt')) return '🧼';
    if (n.includes('kem')) return '🧴';
    return '✨'; 
  }

  function isImageUrl(url: string | undefined): boolean {
    if (!url) return false;
    return url.startsWith('http') || url.startsWith('/') || url.includes('.');
  }

  async function toggleMenu() {
    if (isLoadingCats) return;
    isMenuOpen = !isMenuOpen;
    if (isMenuOpen && categoriesData.length === 0) {
      isLoadingCats = true;
      try {
        const res = await fetch('/api/v1/client/home');
        if (res.ok) {
          const result = await res.json();
          categoriesData = result.categories || [];
          homeProducts = result.products || [];
          if (categoriesData.length > 0) activeCategoryId = categoriesData[0].id;
        }
      } catch (e) {
        console.error("[NAV] Error:", e);
      } finally {
        isLoadingCats = false;
      }
    }
  }

  const categoryProducts = $derived.by((): Product[] => {
    if (!activeCategoryId || homeProducts.length === 0) return [];
    return homeProducts.filter((p: Product) => 
      p.categoryId === activeCategoryId || p.category_id === activeCategoryId
    ).slice(0, 9);
  });

  $effect(() => {
    if (browser) document.body.style.overflow = isMenuOpen ? 'hidden' : '';
  });

  $effect(() => {
    if (scrolled !== undefined) {
      isShrunk = scrolled;
    }
  });

  onMount(() => {
    const scroller = document.querySelector('.page-container') || window;
    const handleScroll = () => {
      const currentScrollY = scroller === window ? window.scrollY : (scroller as Element).scrollTop;
      const threshold = 15;
      if (currentScrollY > lastScrollY + threshold && currentScrollY > 80) {
        if (currentScrollY > 280) {
          isHidden = true;
          isMini = true;
          isShrunk = true;
        } else if (currentScrollY > 160) {
          isHidden = false;
          isMini = true;
          isShrunk = true;
        } else {
          isShrunk = true;
          isMini = false;
          isHidden = false;
        }
        if (isMenuOpen) isMenuOpen = false;
        lastScrollY = currentScrollY;
      } else if (currentScrollY < lastScrollY - threshold || currentScrollY <= 80) {
        isHidden = false;
        isMini = false;
        if (currentScrollY <= 80) {
          isShrunk = false;
        } else {
          isShrunk = true;
        }
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

<MobileBottomMenu
  {isMenuOpen}
  {toggleMenu}
  {isLoadingCats}
  {categoriesData}
  {activeCategoryId}
  setActiveCategoryId={(id) => activeCategoryId = id}
  {categoryProducts}
  {getFallbackIcon}
  {isImageUrl}
  {brokenImages}
  handleImgError={(id) => brokenImages[id] = true}
/>

<nav 
  class="tbn-nav {isShrunk ? 'tbn-nav--shrunk' : ''} {isMini ? 'tbn-nav--mini' : ''} {isHidden ? 'tbn-nav--hidden' : ''}" 
  style="z-index: var(--z-mobile-tab-bar, 100);"
>
  <div class="tbn-nav-inner {isProductMode ? 'tbn-nav-inner--product' : ''}">
    {#if !isProductMode}
      <button class="tbn-item {isMenuOpen ? 'tbn-item--active' : ''}" aria-label="Menu" onclick={toggleMenu}>
        <div class="relative flex flex-col items-center">
          <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            {#if isMenuOpen}<path d="M18 6L6 18M6 6l12 12" />{:else}<path d="M4 7h16M9 12h11M4 17h16" />{/if}
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

    <button class="tbn-item tbn-item--ai" aria-label="AI Chat" onclick={() => { if(!isMenuOpen) (onChatOpen ? onChatOpen() : supportAgent.open()); }}>
      <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <defs><linearGradient id="ai-grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#C18F7E" /><stop offset="100%" stop-color="#E3B5A4" /></linearGradient></defs>
        <path d="M12 2l2.4 5.6 5.6 2.4-5.6 2.4L12 18l-2.4-5.6-5.6-2.4 5.6-2.4L12 2z" stroke="url(#ai-grad)" fill="url(#ai-grad)" fill-opacity="0.2"/>
      </svg>
      <span class="tbn-label tbn-label--ai">AI Chat</span>
    </button>

    {#if isProductMode && product}
      <ProductMobileActions {product} {selectedVariant} {hasFreeship} {onAddToCart} {onBuyNow} />
    {/if}

    {#if !isProductMode}
      <button onclick={() => { if (!authStore.isAuthenticated) ui.openLogin(); else window.location.href = '/user/profile'; }} class="tbn-item" aria-label="Tài khoản">
        <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
        </svg>
        <span class="tbn-label">Tôi</span>
      </button>
    {/if}
  </div>
</nav>

<style>
  .tbn-nav {
    position: fixed;
    bottom: max(env(safe-area-inset-bottom), 12px);
    left: 50%;
    translate: -50% 0;
    width: max-content;
    max-width: calc(100vw - 24px);
    height: 50px;
    background: rgba(255, 255, 255, 0.82);
    -webkit-backdrop-filter: blur(20px) saturate(190%);
    backdrop-filter: blur(20px) saturate(190%);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 24px;
    box-shadow: 
      0 12px 40px rgba(0, 0, 0, 0.06), 
      0 2px 4px rgba(0, 0, 0, 0.02),
      inset 0 1px 1px rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    overflow: hidden;
    transition: 
      height 0.45s cubic-bezier(0.34, 1.56, 0.64, 1),
      border-radius 0.45s cubic-bezier(0.34, 1.56, 0.64, 1),
      translate 0.5s cubic-bezier(0.34, 1.56, 0.64, 1),
      scale 0.5s cubic-bezier(0.34, 1.56, 0.64, 1),
      opacity 0.35s ease,
      background-color 0.3s ease,
      box-shadow 0.4s ease;
  }
  .tbn-nav-inner { width: 100%; height: 100%; display: flex; align-items: center; gap: 4px; padding: 0 8px; }
  .tbn-nav-inner--product { padding-right: 0 !important; }
  .tbn-nav--shrunk {
    height: 42px;
    border-radius: 16px;
    translate: -50% 6px;
    background: rgba(255, 255, 255, 0.88);
    box-shadow: 
      0 8px 30px rgba(0, 0, 0, 0.08), 
      0 1px 2px rgba(0, 0, 0, 0.03);
  }
  .tbn-nav--mini {
    scale: 0.86 !important;
    opacity: 0.75;
    translate: -50% 4px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  }
  .tbn-nav--hidden {
    translate: -50% 80px !important;
    scale: 0.25 !important;
    opacity: 0;
    pointer-events: none;
    filter: blur(10px);
  }
  .tbn-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    color: #555;
    transition: 
      scale 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
      opacity 0.25s ease,
      color 0.25s ease;
    height: 100%;
    min-width: 56px;
    padding: 0 8px;
    cursor: pointer;
  }
  .tbn-item:active {
    scale: 0.9 !important;
    opacity: 0.7;
  }
  .tbn-item--active { color: #000 !important; }
  .tbn-icon {
    width: 22px;
    height: 22px;
    margin-bottom: 2px;
    transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  .tbn-label {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.5px;
    transition: 
      opacity 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
      transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
      max-height 0.3s ease,
      margin-top 0.3s ease;
    opacity: 1;
    transform: translateY(0);
  }
  .tbn-nav--shrunk .tbn-label {
    opacity: 0 !important;
    transform: translateY(6px) !important;
    pointer-events: none;
    max-height: 0 !important;
    margin-top: -2px !important;
    overflow: hidden;
  }
  .tbn-nav--shrunk .tbn-icon {
    scale: 0.92;
    margin-bottom: 0;
  }
  .tbn-label--ai { background: linear-gradient(90deg, #C18F7E, #E3B5A4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; }
</style>
