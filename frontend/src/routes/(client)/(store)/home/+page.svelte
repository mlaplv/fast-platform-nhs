<script lang="ts">
  import { onMount } from 'svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';
  import "$lib/components/storefront/home/home.css";
  import HomeDesktop from '$lib/components/storefront/home/HomeDesktop.svelte';
  import HomeMobile from '$lib/components/storefront/home/HomeMobile.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { buildWebSiteLd, buildOrganizationLd } from '$lib/utils/seo';

  let { data } = $props();
  const ui = getClientUi();

  // Elite V2.2: Derive SEO data from shop settings
  const shopSettings = $derived(data.shopInfo || ui.settings);
  const seoSiteName = $derived(
    shopSettings?.basic_info?.site_name || shopSettings?.site_name || "osmo Elite"
  );
  const seoDescription = $derived(
    shopSettings?.basic_info?.description ||
    shopSettings?.description ||
    `${seoSiteName} - Hệ thống phân phối sản phẩm chăm sóc sức khỏe chính hãng`
  );
  const seoSlogan = $derived(
    shopSettings?.basic_info?.slogan || shopSettings?.slogan || ""
  );
  const seoTitle = $derived(
    seoSlogan ? `${seoSiteName} - ${seoSlogan}` : seoSiteName
  );

  // GEO 2026: JSON-LD for Homepage
  const siteUrl = "https://osmo.vn";
  const webSiteLd = $derived(buildWebSiteLd(seoSiteName, siteUrl));
  const organizationLd = $derived(buildOrganizationLd({
    name: shopSettings?.contact_info?.company_name || seoSiteName,
    url: siteUrl,
    logo: `${siteUrl}/favicon.svg`,
    description: seoDescription,
    hotline: shopSettings?.contact_info?.hotline || shopSettings?.hotline || "",
    email: shopSettings?.contact_info?.email || shopSettings?.email || "",
    address: shopSettings?.contact_info?.address || shopSettings?.address || "",
    socialLinks: shopSettings?.social_links,
  }));
</script>

<SeoHead
  pageType="home"
  title={seoTitle}
  description={seoDescription}
  canonical="{siteUrl}/home"
  siteName={seoSiteName}
  jsonLdScripts={[webSiteLd, organizationLd]}
/>

<div class="home-layout">
  {#if !ui.isDetermined}
    <TikTokShopLoading variant="home" />
  {:else if ui.isMobile}
    <HomeMobile
      banners={data.banners}
      categories={data.categories}
      products={data.products}
      videos={data.videos}
    />
  {:else}
    <HomeDesktop
      banners={data.banners}
      categories={data.categories}
      products={data.products}
      aiProducts={data.ai_products}
    />
  {/if}
</div>
