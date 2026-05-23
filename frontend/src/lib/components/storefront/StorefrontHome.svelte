<script lang="ts">
    import type { HomeData, ShopInfo, Product, Category, Banner } from '$lib/types';
    import { getClientUi } from '$lib/state/commerce/ui.svelte';
    import { onMount, type Component } from 'svelte';
    import "./home/home.css";
    
    const ui = getClientUi();

    let { data, isMobile }: { data: HomeData, isMobile: boolean } = $props();

    // Elite V2.2: Dynamic components to prevent overlapping loading
    let headerComponent = $state<Component<{ settings: ShopInfo | null | undefined }> | null>(null);
    let homeComponent = $state<Component<{
        banners: Banner[];
        categories: Category[];
        products: Product[];
        aiProducts?: Product[];
        videos?: Array<{ id: string; url: string; title: string; likes: number; image: string }>;
    }> | null>(null);
    let footerComponent = $state<Component<{ shopInfo: {
        name: string;
        companyName: string;
        taxId: string;
        businessLicense: string;
        slogan: string;
        subslogan: string;
        description: string;
        hotline: string;
        email: string;
        address: string;
    } }> | null>(null);

    onMount(async () => {
        try {
            if (isMobile) {
                const mod = await import('./home/HomeMobile.svelte');
                homeComponent = mod.default;
            } else {
                const [headerMod, homeMod, footerMod] = await Promise.all([
                    import('./layout/HeaderDesktop.svelte'),
                    import('./home/HomeDesktop.svelte'),
                    import('./layout/FooterDesktop.svelte')
                ]);
                headerComponent = headerMod.default;
                homeComponent = homeMod.default;
                footerComponent = footerMod.default;
            }
        } catch (e) {
            console.error("[SYSTEM FAULT] Dynamic storefront components failed to load:", e);
        }
    });

    $effect(() => {
        if (data.settings) {
            ui.settings = data.settings as ShopInfo;
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
    {#if homeComponent}
        <svelte:component 
            this={homeComponent}
            banners={data.banners}
            categories={data.categories}
            products={data.products}
            videos={data.videos} 
        />
    {/if}
{:else}
    {#if headerComponent}
        <svelte:component this={headerComponent} settings={data.settings} />
    {/if}
    <main>
        {#if homeComponent}
            <svelte:component
                this={homeComponent}
                banners={data.banners}
                categories={data.categories}
                products={data.products}
                aiProducts={data.ai_products}
            />
        {/if}
    </main>
    {#if footerComponent}
        <svelte:component this={footerComponent} shopInfo={shopInfo} />
    {/if}
{/if}
