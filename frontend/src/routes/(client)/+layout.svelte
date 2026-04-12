<script lang="ts">
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { onMount, type Snippet } from "svelte";
  import { authStore } from "$lib/state/authStore.svelte";
  import { fade } from "svelte/transition";
  import "./client.css";

  let { children }: { children: Snippet } = $props();

  const ui = getClientUi();

  const siteName = $derived(ui.settings?.basic_info?.site_name || ui.settings?.site_name || "Micsmo Elite");
  const metaDescription = $derived(`${siteName} - Hệ thống phân phối sản phẩm chăm sóc sức khỏe Elite V2.2`);
</script>

<svelte:head>
  <meta name="description" content={metaDescription} />
</svelte:head>

{@render children()}
