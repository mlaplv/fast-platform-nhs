<script lang="ts">
    import { onMount } from 'svelte';
    import type { HomeData, ShopInfo, Product, Category, Banner } from '$lib/types';
    import { getClientUi } from '$lib/state/commerce/ui.svelte';
    import HeaderDesktop from './layout/HeaderDesktop.svelte';
    import FooterDesktop from './layout/FooterDesktop.svelte';
    import HomeMobile from './home/HomeMobile.svelte';
    import HomeDesktop from './home/HomeDesktop.svelte';
    import "./home/home.css";
    
    const ui = getClientUi();

    let { data, isMobile }: { data: HomeData, isMobile: boolean } = $props();

    // Lazy client-side products to save SSR memory and database connection load
    let products = $state<Product[]>([]);
    let aiProducts = $state<Product[]>([]);

    $effect(() => {
        if (data.settings) {
            ui.settings = data.settings as ShopInfo;
        }
    });

    onMount(async () => {
        try {
            const res = await fetch('/api/v1/client/home');
            if (res.ok) {
                const fullData = await res.json();
                products = fullData.products || [];
                aiProducts = fullData.ai_products || [];
            }
        } catch (e) {
            console.error("Failed to dynamically load storefront products:", e);
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
        products={products}
        videos={data.videos} 
        resolvedLcpUrl={data.resolvedMobileLcpUrl}
    />
{:else}
    <HeaderDesktop settings={data.settings} />
    <main>
        <HomeDesktop
            banners={data.banners}
            categories={data.categories}
            products={products}
            aiProducts={aiProducts}
            resolvedLcpUrl={data.resolvedDesktopLcpUrl}
        />
    </main>
    <FooterDesktop shopInfo={shopInfo} />
{/if}
