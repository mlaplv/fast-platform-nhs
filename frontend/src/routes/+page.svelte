<script lang="ts">
    import type { PageData } from './$types';
    import { onMount, type Component } from 'svelte';
    import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
    import StorefrontHome from '$lib/components/storefront/StorefrontHome.svelte';

    /**
     * ELITE V2.2 - MISSION CONTROL HUB
     * Type-safe tenant router: Admin and Storefront are fully isolated code paths.
     */
    let { data }: { data: PageData } = $props();

    const isAdmin = $derived(data.tenant === 'admin');

    // Admin dashboard is client-only (SPA mode)
    let adminComponent = $state<Component<{ isMobile?: boolean; data?: PageData }> | null>(null);

    onMount(async () => {
        if (isAdmin) {
            // Security: Neutralize all analytics trackers for admin zone
            try {
                const seo = data.shopInfo?.seo_analytics;
                if (seo) {
                    if (seo.google_analytics_id) window[`ga-disable-${seo.google_analytics_id}`] = true;
                    if (seo.google_tag_manager_id) window[`ga-disable-${seo.google_tag_manager_id}`] = true;
                }
                window.gtag = function() {};
                window.fbq = function() {};
            } catch (e) {
                console.error("[SECURITY] Failed to disable analytics for Admin Tenant:", e);
            }

            try {
                const mod = await import("$lib/components/admin/layout/AdminDashboard.svelte");
                adminComponent = mod.default;
            } catch (err) {
                console.error("[SYSTEM FAULT] Admin load failed:", err);
                window.location.reload();
            }
        }
    });

    // SEO Derivation — only computed when storefront (no wasted CPU for admin)
    const shopSettings = $derived(!isAdmin ? data.shopInfo : null);
    const seoSiteName = $derived(
        shopSettings?.basic_info?.site_name || shopSettings?.site_name || "osmo.vn"
    );
    const seoDescription = $derived(
        data.seo_meta?.description || 
        shopSettings?.basic_info?.description ||
        shopSettings?.description ||
        "Mỹ phẩm cao cấp từ Nhật Bản."
    );
    const seoSlogan = $derived(
        shopSettings?.basic_info?.slogan || shopSettings?.slogan || ""
    );
    const seoTitle = $derived(
        data.seo_meta?.title || 
        (seoSlogan ? `${seoSiteName} - ${seoSlogan}` : seoSiteName)
    );
</script>

{#if !isAdmin}
    <SeoHead
        pageType="home"
        title={seoTitle}
        description={seoDescription}
        canonical={data.seo_meta?.canonical_url || "https://osmo.vn/"}
        keywords={data.seo_meta?.keywords || ""}
        robots="index, follow"
        jsonLdScripts={[
            data.seo_meta?.json_ld_string,
            data.seo_meta?.breadcrumb_ld_string
        ].filter(Boolean)}
    />
{/if}

<svelte:head>
    {#if isAdmin}
        <title>Xohi Darkboard</title>
        <meta name="robots" content="noindex, nofollow" />
    {:else}
        {#if data.isMobile}
            {#if data.resolvedMobileLcpUrl}
                <link rel="preload" as="image" href={data.resolvedMobileLcpUrl} fetchpriority="high" type="image/webp" />
            {/if}
        {:else}
            {#if data.resolvedDesktopLcpUrl}
                <link rel="preload" as="image" href={data.resolvedDesktopLcpUrl} fetchpriority="high" type="image/webp" />
            {/if}
        {/if}
    {/if}
</svelte:head>

<div class="page-container md:h-auto md:overflow-visible min-h-dvh overflow-x-hidden {isAdmin ? 'bg-[#020202]' : 'bg-[#fafafa]'}">
    {#if isAdmin}
        {#if adminComponent}
            <div class="flex-1 flex flex-col">
                <svelte:component
                    this={adminComponent}
                    isMobile={data.isMobile}
                    data={data}
                />
            </div>
        {:else}
            <!-- Loading State: Admin-specific spinner -->
            <div class="fixed inset-0 flex items-center justify-center bg-[#020202] text-[#00FFFF] z-[var(--z-modal-overlay)]">
                <div class="relative flex flex-col items-center gap-6">
                    <div class="w-12 h-12 border-2 border-[#00FFFF]/20 border-t-[#00FFFF] rounded-full animate-spin shadow-[0_0_15px_rgba(0,255,255,0.1)]"></div>
                    <div class="text-[9px] font-mono text-[#00FFFF]/50 tracking-[0.4em] animate-pulse">Initializing Neural Link...</div>
                </div>
            </div>
        {/if}
    {:else}
        <div class="flex-1 flex flex-col">
            <StorefrontHome
                data={data}
                isMobile={data.isMobile}
            />
        </div>
    {/if}
</div>

<style>
    .page-container {
        display: flex;
        flex-direction: column;
    }

    /* Ensure the inner transition container grows to fill the page container */
    .page-container > div {
        flex: 1;
        display: flex;
        flex-direction: column;
    }
</style>
