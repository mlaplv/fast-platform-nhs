<script lang="ts">
  import { setClientUi } from "$lib/state/commerce/ui.svelte";
  import "./client.css";
  let { children } = $props();

  const ui = setClientUi();
</script>

<svelte:head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="Nhà Thuốc Hồng Sơn - Hệ thống phân phối sản phẩm chăm sóc sức khỏe Elite V2.2" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
</svelte:head>

<div class="client-layout min-h-screen flex flex-col">
  <main class="flex-grow">
    {@render children()}
  </main>
</div>
