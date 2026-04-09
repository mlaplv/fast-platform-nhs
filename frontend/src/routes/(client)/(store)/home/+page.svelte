<script lang="ts">
  import { onMount } from 'svelte';
  import "./home.css";
  import HomeDesktop from './HomeDesktop.svelte';
  import HomeMobile from './HomeMobile.svelte';

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
