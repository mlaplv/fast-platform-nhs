<script lang="ts">
  import "./admin.css";
  
  import SeoHead from "$lib/components/storefront/seo/SeoHead.svelte";
  let { children } = $props();
</script>

<SeoHead title="Admin Control Center" robots="noindex, nofollow" />


<div class="admin-layout min-h-screen relative overflow-hidden">
  {@render children()}
</div>
