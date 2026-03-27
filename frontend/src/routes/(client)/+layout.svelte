<script lang="ts">
  import "./client.css";
  let { children } = $props();
</script>

<div class="client-layout min-h-screen">
  <main>
    {@render children()}
  </main>
</div>
