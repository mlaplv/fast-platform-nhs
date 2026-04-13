<script lang="ts">
  import { onMount } from 'svelte';
  import "$lib/components/storefront/home/home.css";
  import HomeDesktop from '$lib/components/storefront/home/HomeDesktop.svelte';
  import HomeMobile from '$lib/components/storefront/home/HomeMobile.svelte';

  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  let { data } = $props();
  const ui = getClientUi();
</script>

<div class="home-layout">
  {#if ui.isMobile}
    <HomeMobile
      banners={data.banners}
      categories={data.categories}
      products={data.products}
      videos={data.videos}
    />
  {:else}
    <HomeDesktop
      banners={data.banners}
      categories={data.categories}
      products={data.products}
      aiProducts={data.ai_products}
    />
  {/if}
</div>
