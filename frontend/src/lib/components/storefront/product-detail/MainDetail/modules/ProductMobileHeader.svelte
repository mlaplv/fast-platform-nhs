<script lang="ts">
    import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import Search from "@lucide/svelte/icons/search";
  import Share2 from "@lucide/svelte/icons/share-2";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";
  import { goto } from '$app/navigation';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import SmartSearch from '../../../product/SmartSearch.svelte';
  import type { Product } from '$lib/types';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  interface Props {
    product: Product;
    showTabs: boolean;
    activeTab: string;
    onScrollToSection: (id: string) => void;
    onShare?: () => void;
  }

  let { product, showTabs, activeTab, onScrollToSection, onShare }: Props = $props();
  const cartStore = getCartStore();
  const searchStore = getSearchStore();

  async function handleShare() {
    if (onShare) {
      onShare();
      return;
    }
    // Fallback: Native Share API
    if (typeof navigator !== 'undefined' && navigator.share) {
      try {
        await navigator.share({
          title: product.name,
          text: `Xem ngay ${product.name}!`,
          url: window.location.href
        });
      } catch (_e) {
        // User cancelled
      }
    } else if (typeof navigator !== 'undefined' && navigator.clipboard) {
      await navigator.clipboard.writeText(window.location.href);
    }
  }
</script>

<header class="detail-header" style="z-index: var(--z-header, 100);">
  <div class="header-main">
    <button type="button" class="icon-btn" onclick={() => history.back()} aria-label="Quay lại">
      <ChevronLeft size={24} />
    </button>
    
    <div
      class="search-bar-wrapper cursor-text"
      role="presentation"
      onclick={() => searchStore.isOverlayOpen = true}
    >
      <Search size={16} class="search-icon shrink-0" />
      <span class="placeholder">Tìm "{product.name}"...</span>
    </div>

    <div class="header-actions">
      <button type="button" class="icon-btn" aria-label="Chia sẻ" onclick={handleShare}>
        <Share2 size={24} />
      </button>
      <button type="button" class="icon-btn relative" onclick={() => goto('/checkout')} aria-label="Giỏ hàng">
        <ShoppingCart size={24} />
        {#if cartStore.totalItems > 0}
          <span class="badge">{cartStore.totalItems}</span>
        {/if}
      </button>
      <button type="button" class="icon-btn" aria-label="Thêm">
        <MoreHorizontal size={24} />
      </button>
    </div>
  </div>

  <!-- ADVANCED STICKY TABS (TikTok Style: Hidden by default, slides down) -->
  <nav class="tabs-nav" class:visible={showTabs}>
    {#each ['overview', 'reviews', 'description', 'recommendations'] as id}
      {@const label = id === 'overview' ? 'Tổng quan' : id === 'reviews' ? 'Đánh giá' : id === 'description' ? 'Mô tả' : 'Đề xuất'}
      <button type="button" class="tab-item" class:active={activeTab === id} onclick={() => onScrollToSection(id)}>
        {label}
        {#if activeTab === id}<div class="active-indicator"></div>{/if}
      </button>
    {/each}
  </nav>
</header>

{#if searchStore.isOverlayOpen}
  <SmartSearch variant="mobile-overlay" />
{/if}

<style>
  .detail-header {
    position: sticky;
    top: 0;
    left: 0;
    right: 0;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    display: flex;
    flex-direction: column;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    border-bottom: 0.5px solid rgba(0,0,0,0.05);
  }

  .header-main {
    display: flex;
    align-items: center;
    padding: 6px 8px;
    gap: 12px;
    height: 48px;
  }

  .tabs-nav {
    display: flex;
    height: 0;
    opacity: 0;
    overflow: hidden;
    background: white;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border-bottom: 0.5px solid #f5f5f5;
  }

  .tabs-nav.visible {
    height: 30px;
    opacity: 1;
  }

  .tab-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: #666;
    position: relative;
    background: none;
    border: none;
    padding: 0;
  }

  .tab-item.active {
    color: var(--color-luxury-copper, #C18F7E);
    font-weight: 900;
  }

  .active-indicator {
    position: absolute;
    bottom: 0;
    width: 30px;
    height: 2px;
    background: var(--color-luxury-copper, #C18F7E);
    border-radius: 2px;
  }

  .icon-btn {
    background: transparent;
    border: none;
    color: #444;
    padding: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: linear-gradient(135deg, #C18F7E 0%, #E3B5A4 100%);
    color: white;
    font-size: 10px;
    font-weight: 900;
    min-width: 16px;
    height: 16px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .search-bar-wrapper {
    flex: 1;
    min-width: 0;
    background: rgba(0,0,0,0.04);
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    padding: 0 12px;
    gap: 8px;
    color: #888;
    overflow: hidden;
    border: 1px solid rgba(0,0,0,0.02);
  }

  .placeholder {
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .header-actions {
    display: flex;
    gap: 4px;
  }
</style>
