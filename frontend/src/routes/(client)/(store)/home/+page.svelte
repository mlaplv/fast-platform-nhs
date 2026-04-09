<script lang="ts">
  import { onMount } from 'svelte';
  import "$lib/components/storefront/home/home.css";
  import HomeDesktop from '$lib/components/storefront/home/HomeDesktop.svelte';
  import HomeMobile from '$lib/components/storefront/home/HomeMobile.svelte';

  let { data } = $props();

  let isMobile = $state(false);

  onMount(() => {
    isMobile = window.innerWidth < 768;
    const handleResize = () => {
      isMobile = window.innerWidth < 768;
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  });
</script>

<div class="home-layout">
  {#if isMobile}
    <HomeMobile videos={data.videos} />
  {:else}
    <HomeDesktop
      banners={data.banners}
      categories={data.categories}
      products={data.products}
    />
  {/if}
</div>
