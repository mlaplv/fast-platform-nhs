<script lang="ts">
    import HomeDesktop from './home/HomeDesktop.svelte';
    import HomeMobile from './home/HomeMobile.svelte';
    import HeaderDesktop from './layout/HeaderDesktop.svelte';
    import FooterDesktop from './layout/FooterDesktop.svelte';
    import "./home/home.css";

    let { data, isMobile }: { data: any, isMobile: boolean } = $props();

    const shopInfo = $derived({
        name: data.settings?.basic_info?.site_name || "Micsmo Elite",
        companyName: data.settings?.contact_info?.company_name || "",
        taxId: data.settings?.contact_info?.tax_id || "",
        businessLicense: data.settings?.contact_info?.business_license || "",
        slogan: "Agentic AI Commerce 2026", // Specific slogan for Elite V2.2
        description: data.settings?.basic_info?.description || "Hệ thống bán hàng AI thế hệ mới",
        hotline: data.settings?.contact_info?.hotline || data.settings?.contact_info?.phone || "1800-MICSMO",
        email: data.settings?.contact_info?.email || "contact@micsmo.com",
        address: data.settings?.contact_info?.address || "TP. Hồ Chí Minh"
    });
</script>

{#if isMobile}
    <HomeMobile 
        banners={data.banners}
        categories={data.categories}
        products={data.products}
        aiProducts={data.ai_products}
        videos={data.videos} 
    />
{:else}
    <HeaderDesktop />
    <main>
        <HomeDesktop
            banners={data.banners}
            categories={data.categories}
            products={data.products}
            aiProducts={data.ai_products}
        />
    </main>
    <FooterDesktop {shopInfo} />
{/if}
