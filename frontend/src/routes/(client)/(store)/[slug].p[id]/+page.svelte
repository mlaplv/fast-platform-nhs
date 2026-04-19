<script lang="ts">
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import type { GenericPageData } from '$lib/types';
  import NewsDetailDesktop from '$lib/components/storefront/news-detail/NewsDetailDesktop.svelte';
  import NewsDetailMobile from '$lib/components/storefront/news-detail/NewsDetailMobile.svelte';

  let { data }: { data: GenericPageData } = $props();
  const ui = getClientUi();
  const isMobile = $derived(ui.isMobile);
</script>

<div class="news-detail-wrapper bg-[#F5F5F5] pb-8">
  {#if isMobile}
    <NewsDetailMobile article={data.article} />
  {:else}
    <NewsDetailDesktop article={data.article} />
  {/if}
</div>