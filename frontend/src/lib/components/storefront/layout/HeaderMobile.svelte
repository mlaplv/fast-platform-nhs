<script lang="ts">
  import { ChevronLeft, Search, Share2, ShoppingCart, MoreHorizontal, Home } from 'lucide-svelte';
  import { goto } from '$app/navigation';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import SmartSearch from '../product/SmartSearch.svelte';

  const cartStore = getCartStore();
  const searchStore = getSearchStore();

  function goBack() {
    window.location.href = '/';
  }
</script>

<header class="detail-header">
  <div class="header-main">
    <button class="icon-btn" onclick={goBack}>
      <ChevronLeft size={24} />
    </button>
    
    <div
      class="search-bar-wrapper cursor-text"
      role="presentation"
      onclick={() => searchStore.isOverlayOpen = true}
    >
      <Search size={16} class="search-icon shrink-0" />
      <span class="placeholder">Tìm sản phẩm Elite...</span>
    </div>

    <div class="header-actions">
      <!-- Elite V2.2: Simplified for Success Page focus -->
    </div>
  </div>
</header>

{#if searchStore.isOverlayOpen}
  <SmartSearch variant="mobile-overlay" />
{/if}

<style>
  .detail-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: white;
    display: flex;
    flex-direction: column;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    z-index: 1000;
  }

  .header-main {
    display: flex;
    align-items: center;
    padding: 6px 8px;
    gap: 8px;
    height: 56px;
  }

  .icon-btn {
    background: transparent;
    border: none;
    color: #444;
    padding: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s;
  }

  .icon-btn:active {
    scale: 0.9;
  }

  .badge {
    position: absolute;
    top: -2px;
    right: -2px;
    background: #ee4d2d;
    color: white;
    font-size: 9px;
    font-weight: 900;
    min-width: 15px;
    height: 15px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid white;
  }

  .search-bar-wrapper {
    flex: 1;
    min-width: 0;
    background: #f0f0f0;
    height: 38px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    padding: 0 12px;
    gap: 8px;
    color: #888;
    overflow: hidden;
  }

  .placeholder {
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 500;
  }

  .header-actions {
    display: flex;
    gap: 2px;
  }
</style>
