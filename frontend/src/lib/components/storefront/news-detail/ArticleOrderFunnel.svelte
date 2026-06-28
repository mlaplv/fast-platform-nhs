<script lang="ts">
  import { onMount, tick } from "svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import type { Product } from "$lib/types";
  import ProductDetailDesktop from "$lib/components/storefront/product-detail/MainDetail/Desktop.svelte";
  import ProductDetailMobile from "$lib/components/storefront/product-detail/MainDetail/Mobile.svelte";

  let { productId }: { productId: string } = $props();
  const ui = getClientUi();

  let product = $state<Product | null>(null);
  let loading = $state<boolean>(true);
  let errorMsg = $state<string | null>(null);
  let containerRef = $state<HTMLElement | null>(null);

  onMount(async () => {
    if (!productId) return;
    try {
      const res = await fetch(`/api/v1/client/products/${productId}`);
      if (res.ok) {
        product = await res.json();
      } else {
        errorMsg = "Không thể tải thông tin sản phẩm.";
      }
    } catch (err) {
      console.error("[ArticleOrderFunnel] Failed to fetch product details:", err);
      errorMsg = "Đã xảy ra lỗi khi tải sản phẩm.";
    } finally {
      loading = false;
    }
  });

  // SEO Guard: Convert embedded product H1 -> H2 without changing product detail files
  $effect(() => {
    if (!loading && product && containerRef) {
      tick().then(() => {
        const h1 = containerRef?.querySelector("h1");
        if (h1) {
          const h2 = document.createElement("h2");
          for (const attr of h1.attributes) {
            h2.setAttribute(attr.name, attr.value);
          }
          h2.innerHTML = h1.innerHTML;
          h1.parentNode?.replaceChild(h2, h1);
        }
      });
    }
  });
</script>

{#if !loading && product}
  <div bind:this={containerRef} class="article-order-funnel-wrapper">
    {#if ui.isMobile}
      <div class="embedded-product-funnel-mobile">
        <ProductDetailMobile {product} isEmbedded={true} />
      </div>
    {:else}
      <div class="embedded-product-funnel-desktop">
        <ProductDetailDesktop {product} isEmbedded={true} />
      </div>
    {/if}
  </div>
{:else if loading}
  <div class="flex items-center justify-center p-8">
    <div class="w-8 h-8 rounded-full border-2 border-gray-200 animate-spin border-t-[#854E37]"></div>
  </div>
{/if}

<style>
  .embedded-product-funnel-desktop {
    border: none !important;
    padding-left: 5px !important;
    padding-right: 5px !important;
    box-shadow: none !important;
  }

  .embedded-product-funnel-mobile {
    border: none !important;
    padding-left: 5px !important;
    padding-right: 5px !important;
    box-shadow: none !important;
  }
</style>
