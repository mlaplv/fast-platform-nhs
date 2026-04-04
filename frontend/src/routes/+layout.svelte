<script lang="ts">
  import "./layout.css";
  import { setNanobotContext } from "$lib/state/nanobot.svelte";
  
  // Elite V2.2: Ensure root initialization of context
  setNanobotContext();

  let { children } = $props();

</script>

<svelte:head>
  <link rel="icon" href="/favicon.svg" />
  <title>SmartShop Elite</title>
</svelte:head>

<div class="min-h-screen">
  {@render children()}
</div>
