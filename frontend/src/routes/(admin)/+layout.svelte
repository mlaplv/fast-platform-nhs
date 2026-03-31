<script lang="ts">
  import "./admin.css";
  let { children } = $props();
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet" />
</svelte:head>

<div class="admin-layout min-h-screen relative overflow-hidden">
  {@render children()}
</div>
