<script lang="ts">
  import "./client.css";

  let { children } = $props();
</script>

<svelte:head>
  <!-- [Elite V3.0] Universal AI Core & Model Context Protocol Discovery -->
  <link rel="mcp-server" type="application/json" href="https://api.osmo.vn/.well-known/mcp.json" />
</svelte:head>

{@render children()}
