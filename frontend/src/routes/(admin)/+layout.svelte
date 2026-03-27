<script lang="ts">
  import "./admin.css";
  let { children } = $props();
</script>

<div class="admin-layout min-h-screen">
  {@render children()}
</div>
