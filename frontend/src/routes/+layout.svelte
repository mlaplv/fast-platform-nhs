<script lang="ts">
  import "./layout.css";
  let { children } = $props();

</script>

<svelte:head>
  <link rel="icon" href="/favicon.svg" />
  <title>SmartShop Elite</title>
</svelte:head>

<div class="min-h-screen">
  {@render children()}
</div>
