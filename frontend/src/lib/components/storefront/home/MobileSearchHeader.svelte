<!-- MobileSearchHeader.svelte -->
<!-- Pixel-perfect TikTok Shop header: gradient bg, red-border search, camera, CTA, cart badge -->
<script lang="ts">
  import { goto } from '$app/navigation';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';

  const cartStore = getCartStore();
</script>

<header class="tsh-header" style="z-index:{Z_INDEX_CLIENT.HEADER}">

  <!-- Vùng search + cart trên cùng -->
  <div class="tsh-top-row">

    <!-- Search bar: border đỏ solid, border-image gradient technique -->
    <div class="tsh-search-ring">
      <!-- Inner white zone -->
      <div class="tsh-search-inner">

        <!-- 🔍 icon -->
        <svg class="tsh-icon-search" viewBox="0 0 24 24" fill="none">
          <circle cx="11.5" cy="11.5" r="6.5" stroke="#222" stroke-width="2.2" />
          <path d="M16 16l4 4" stroke="#222" stroke-width="2.2" stroke-linecap="round"/>
        </svg>

        <!-- Placeholder text -->
        <span class="tsh-placeholder">tai nghe bluetooth...</span>

        <!-- Tìm kiếm CTA -->
        <button class="tsh-cta" type="button" onclick={() => goto('/search')}>Tìm kiếm</button>
      </div>
    </div>

    <!-- Cart -->
    <button class="tsh-cart" type="button" onclick={() => goto('/checkout')} aria-label="Giỏ hàng">
      <!-- Trolley styled cart icon -->
      <svg class="tsh-cart-icon" viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="9" cy="20" r="1.5" fill="#111" stroke="none" />
        <circle cx="18" cy="20" r="1.5" fill="#111" stroke="none" />
        <path d="M2.5 4h3l2 11h11.5l2-7H6.5"/>
      </svg>
      {#if cartStore.totalItems > 0}
        <span class="tsh-badge">{cartStore.totalItems > 99 ? '99+' : cartStore.totalItems}</span>
      {/if}
    </button>

  </div>

</header>

<style>
  /* ============================================================
     RESET LOCAL: đảm bảo mọi element trong component
     không vượt ra ngoài viewport
  ============================================================ */
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  /* ============================================================
     HEADER ROOT
  ============================================================ */
  .tsh-header {
    position: sticky;
    top: 0;
    left: 0;
    width: 100%;
    /* gradient background nhạt như TikTok Shop: xanh-hồng */
    background: linear-gradient(135deg, #d0f5f3 0%, #fde8e8 100%);
    overflow: hidden;          /* chặn bất kỳ child nào vượt width */
  }

  /* ============================================================
     ROW 1: SEARCH + CART
  ============================================================ */
  .tsh-top-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    width: 100%;
  }

  /* Search bar wrapper – flex: 1 to fill remaining space */
  .tsh-search-ring {
    flex: 1;
    min-width: 0;
    /* Gradient border technique: border transparent + background-clip */
    border: 1.5px solid transparent;
    border-radius: 10px; /* Reduced from 9999px to match image */
    background-image:
      linear-gradient(white, white),         /* padding-box: inner white */
      linear-gradient(90deg, #06d6d6, #fe2c55); /* border-box: gradient ring cyan -> pink */
    background-origin: border-box;
    background-clip: padding-box, border-box;
  }

  /* Inner row inside search */
  .tsh-search-inner {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 0 10px;
    height: 38px;
    width: 100%;
  }

  .tsh-icon-search {
    width: 22px;
    height: 22px;
    flex-shrink: 0;
  }

  .tsh-placeholder {
    flex: 1;
    min-width: 0;
    font-size: 15px;
    color: #1edddd; /* Match the teal color in screenshot */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    user-select: none;
  }



  .tsh-cta {
    background: none;
    border: none;
    padding: 0 4px 0 0;
    cursor: pointer;
    font-size: 16px;
    font-weight: 800;
    color: #fe2c55; /* Vibrant pink/red from image */
    white-space: nowrap;
    flex-shrink: 0;
  }

  /* Cart button */
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
    background: #fe2c55; /* TikTok vibrant pink/red */
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
    font-family: 'Inter', sans-serif;
  }
</style>
