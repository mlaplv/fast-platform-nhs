<script lang="ts">
  import { setClientUi } from "$lib/state/commerce/ui.svelte";
  import { onMount, type Snippet } from "svelte";
  import "./client.css";

  let { children }: { children: Snippet } = $props();

  const ui = setClientUi();

  onMount(() => {
    return ui.initObservers();
  });
  const siteName = $derived(ui.settings?.basic_info?.site_name || ui.settings?.site_name || "Micsmo Elite");
  const metaDescription = $derived(`${siteName} - Hệ thống phân phối sản phẩm chăm sóc sức khỏe Elite V2.2`);
</script>

<svelte:head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0" />
  <meta name="description" content={metaDescription} />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
</svelte:head>

{@render children()}
