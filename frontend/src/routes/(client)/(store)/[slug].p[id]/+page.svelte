<script lang="ts">
  import NewsDetailDesktop from '$lib/components/storefront/news-detail/NewsDetailDesktop.svelte';
  import NewsDetailMobile from '$lib/components/storefront/news-detail/NewsDetailMobile.svelte';
  import { onMount } from 'svelte';

  let { data }: { data: any } = $props();

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

<div class="news-detail-wrapper bg-[#F5F5F5] pb-8">
  {#if isMobile}
    <NewsDetailMobile article={data.article} />
  {:else}
    <NewsDetailDesktop article={data.article} />
  {/if}
</div>