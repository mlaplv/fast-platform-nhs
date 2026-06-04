<script lang="ts">
  import { goto } from '$app/navigation';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import SmartSearch from '../product/SmartSearch.svelte';

  const cartStore = getCartStore();
  const searchStore = getSearchStore();
</script>

<header class="tsh-header" style="z-index:{Z_INDEX_CLIENT.HEADER}">

  <!-- Vùng search + cart trên cùng -->
  <div class="tsh-top-row">

        <!-- Search bar: Integrated with SmartSearch -->
    <div
      class="tsh-search-ring cursor-text"
      onclick={() => searchStore.isOverlayOpen = true}
      role="presentation"
    >
      <div class="tsh-search-inner">
        <svg class="tsh-icon-search" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>

        <input
          type="text"
          readonly
          placeholder={searchStore.searchPlaceholder}
          class="tsh-input-ghost"
        />

        <button class="tsh-cta" type="button">Tìm kiếm</button>
      </div>
    </div>

    <!-- Cart -->
    <button class="tsh-cart" type="button" onclick={() => goto('/checkout')} aria-label="Giỏ hàng">
      <!-- Trolley styled cart icon -->
      <svg class="tsh-cart-icon" viewBox="0 0 24 24" fill="none" stroke="#C18F7E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="9" cy="20" r="1.5" fill="#C18F7E" stroke="none" />
        <circle cx="18" cy="20" r="1.5" fill="#C18F7E" stroke="none" />
        <path d="M2.5 4h3l2 11h11.5l2-7H6.5"/>
      </svg>
      {#if cartStore.totalItems > 0}
        <span class="tsh-badge">{cartStore.totalItems > 99 ? '99+' : cartStore.totalItems}</span>
      {/if}
    </button>

  </div>

</header>

<style>
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  .tsh-header {
    position: sticky;
    top: 0;
    left: 0;
    width: 100%;
    height: 48px;
    background: linear-gradient(135deg, #FFF8F5 0%, #FFF0EA 100%);
    border-bottom: 1.5px solid rgba(193, 143, 126, 0.15);
    overflow: hidden;
    display: flex;
    align-items: center;
  }

  .tsh-top-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    width: 100%;
  }

  .tsh-search-ring {
    height: 36px;
    flex: 1;
    min-width: 0;
    border: 1.5px solid transparent;
    border-radius: 8px; /* TikTok screenshot style */
    overflow: hidden;
    background-image:
      linear-gradient(white, white),
      linear-gradient(90deg, #C18F7E, #E3B5A4);
    background-origin: border-box;
    background-clip: padding-box, border-box;
    transform: translateZ(0);
  }

  .tsh-search-inner {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 0 8px 0 10px;
    height: 100%;
    width: 100%;
  }

  .tsh-icon-search {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    color: #9ca3af;
  }

  .tsh-input-ghost {
    flex: 1;
    min-width: 0;
    font-size: 14px;
    font-weight: 500;
    color: #9ca3af;
    background: transparent;
    border: none;
    outline: none;
    pointer-events: none;
  }

  .tsh-cta {
    background: none;
    border: none;
    padding: 0 4px 0 0;
    cursor: pointer;
    font-size: 15px;
    font-weight: 800;
    color: #C18F7E;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .tsh-cart {
    position: relative;
    background: none;
    border: none;
    padding: 2px;
    cursor: pointer;
    display: flex;
    align-items: center;
    flex-shrink: 0;
  }

  .tsh-cart-icon {
    width: 32px;
    height: 32px;
  }

  .tsh-badge {
    position: absolute;
    top: -2px;
    right: -2px;
    background: #C18F7E;
    color: #fff;
    font-size: 10px;
    font-weight: 800;
    min-width: 16px;
    height: 16px;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
    line-height: 1;
    border: 1.5px solid #fff;
    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  }
</style>

{#if searchStore.isOverlayOpen}
  <SmartSearch variant="mobile-overlay" />
{/if}
