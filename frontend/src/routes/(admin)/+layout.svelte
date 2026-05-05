<script lang="ts">
  import "./admin.css";
  
  let { children } = $props();
</script>

<svelte:head>
</svelte:head>

<div class="admin-layout min-h-screen relative overflow-hidden">
  {@render children()}
</div>
