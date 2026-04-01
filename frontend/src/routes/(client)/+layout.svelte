<script lang="ts">
  import { setClientUi } from "$lib/state/commerce/ui.svelte";
  import "./client.css";
  let { children } = $props();

  const ui = setClientUi();
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />

</svelte:head>

<div class="client-layout min-h-screen flex flex-col">
  <main class="flex-grow">
    {@render children()}
  </main>
  
</div>
