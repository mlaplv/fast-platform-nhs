<script lang="ts">
    import HomeDesktop from './home/HomeDesktop.svelte';
    import HomeMobile from './home/HomeMobile.svelte';
    import HeaderDesktop from './layout/HeaderDesktop.svelte';
    import FooterDesktop from './layout/FooterDesktop.svelte';
    import type { HomeData } from '$lib/types';
    import { getClientUi } from '$lib/state/commerce/ui.svelte';
    import "./home/home.css";
    const ui = getClientUi();

    let { data, isMobile }: { data: HomeData, isMobile: boolean } = $props();

    $effect(() => {
        if (data.settings) {
            ui.settings = data.settings as any;
        }
    });

    const shopInfo = $derived({
        name: data.settings?.basic_info?.site_name || "osmo Elite",
        companyName: data.settings?.contact_info?.company_name || "",
        taxId: data.settings?.contact_info?.tax_id || "",
        businessLicense: data.settings?.contact_info?.business_license || "",
        slogan: data.settings?.basic_info?.slogan || "Agentic AI Commerce 2026", // Dynamic from Settings V2.2
        subslogan: data.settings?.basic_info?.subslogan || "Làn da trắng mịn không chỉ là vẻ đẹp, đó là sự tự tin và kiêu hãnh của mỗi người phụ nữ.",
        description: data.settings?.basic_info?.description || "Mỹ Phẩm Cao Cấp Từ Nhật Bản",
        hotline: data.settings?.contact_info?.hotline || data.settings?.contact_info?.phone || "1800-osmo",
        email: data.settings?.contact_info?.email || "contact@osmo",
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
    <HeaderDesktop settings={data.settings} />
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
