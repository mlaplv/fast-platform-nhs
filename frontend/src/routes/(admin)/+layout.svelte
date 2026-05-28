<script lang="ts">
  import "./admin.css";
  import { onMount } from "svelte";
  import { page } from "$app/state";
  
  import SeoHead from "$lib/components/storefront/seo/SeoHead.svelte";
  let { children } = $props();

  onMount(() => {
    try {
      const seo = page.data.shopInfo?.seo_analytics;
      if (seo) {
        if (seo.google_analytics_id) {
          window[`ga-disable-${seo.google_analytics_id}`] = true;
        }
        if (seo.google_tag_manager_id) {
          window[`ga-disable-${seo.google_tag_manager_id}`] = true;
        }
      }
      // Overwrite tracking interfaces with no-op functions to fully seal the admin environment
      window.gtag = function() {};
      window.fbq = function() {};
    } catch (e) {
      console.error("[SECURITY] Failed to disable analytics in Admin Layout:", e);
    }
  });
</script>

<SeoHead title="Admin Control Center" robots="noindex, nofollow" />


<div class="admin-layout min-h-screen relative overflow-hidden">
  {@render children()}
</div>
