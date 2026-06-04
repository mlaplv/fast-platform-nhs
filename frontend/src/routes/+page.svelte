<script lang="ts">
    import type { PageData } from './$types';
    import { onMount, type Component } from 'svelte';

    /**
     * ELITE V2.2 - MISSION CONTROL HUB
     * Type-safe tenant router: Admin and Storefront are fully isolated code paths.
     * SeoHead is lazy-loaded only for storefront to avoid wasted JS parse on admin.
     */
    let { data }: { data: PageData } = $props();

    const isAdmin = $derived(data.tenant === 'admin');

    // Type-safe component slots: separated by tenant to prevent prop mismatch bombs
    let adminComponent = $state<Component<{ isMobile?: boolean; data?: PageData }> | null>(null);
    let storefrontComponent = $state<Component<{ data: PageData; isMobile: boolean }> | null>(null);

    // Lazy-loaded SeoHead — zero JS parse cost for admin tenant
    let SeoHead = $state<Component<Record<string, unknown>> | null>(null);

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
                window.dispatchEvent(new Event('app-ready'));
            } catch (err) {
                console.error("[SYSTEM FAULT] Admin load failed:", err);
                window.dispatchEvent(new Event('app-ready'));
                window.location.reload();
            }
        } else {
            try {
                // Parallel load: SeoHead + StorefrontHome simultaneously
                const [seoMod, storeMod] = await Promise.all([
                    import('$lib/components/storefront/seo/SeoHead.svelte'),
                    import('$lib/components/storefront/StorefrontHome.svelte')
                ]);
                SeoHead = seoMod.default;
                storefrontComponent = storeMod.default;
                // StorefrontHome dispatches app-ready itself after sub-components mount
            } catch (err) {
                console.error("[SYSTEM FAULT] Storefront load failed:", err);
                window.dispatchEvent(new Event('app-ready'));
                window.location.reload();
            }
        }
    });

    // SEO Derivation — only computed when storefront (no wasted CPU for admin)
    const shopSettings = $derived(!isAdmin ? data.shopInfo : null);
    const seoSiteName = $derived(
        shopSettings?.basic_info?.site_name || shopSettings?.site_name || "osmo Elite"
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

<!-- SEO: Only rendered for storefront, lazy-loaded -->
{#if !isAdmin && SeoHead}
    <svelte:component this={SeoHead}
        pageType="HOMEPAGE_ELITE"
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
    {/if}
</svelte:head>

<div class="page-container md:h-auto md:overflow-visible min-h-dvh overflow-x-hidden {isAdmin ? 'bg-[#020202]' : 'bg-[#fafafa]'}">
    {#if isAdmin && adminComponent}
        <div class="flex-1 flex flex-col">
            <svelte:component
                this={adminComponent}
                isMobile={data.isMobile}
                data={data}
            />
        </div>
    {:else if !isAdmin && storefrontComponent}
        <div class="flex-1 flex flex-col">
            <svelte:component
                this={storefrontComponent}
                data={data}
                isMobile={data.isMobile}
            />
        </div>
    {:else}
        <!-- Loading State: Tenant-specific spinner -->
        <div class="fixed inset-0 flex items-center justify-center {isAdmin ? 'bg-[#020202] text-[#00FFFF]' : 'bg-[#fafafa] text-[#C5A25D]'} z-[var(--z-modal-overlay)]">
            <div class="relative flex flex-col items-center gap-6">
                {#if isAdmin}
                    <div class="w-12 h-12 border-2 border-[#00FFFF]/20 border-t-[#00FFFF] rounded-full animate-spin shadow-[0_0_15px_rgba(0,255,255,0.1)]"></div>
                    <div class="text-[9px] font-mono text-[#00FFFF]/50 tracking-[0.4em] animate-pulse">Initializing Neural Link...</div>
                {:else}
                    <div class="w-16 h-16 border-[1px] border-[#C5A25D]/10 border-t-[#C5A25D] rounded-full animate-spin duration-[2s]"></div>
                    <div class="absolute inset-0 flex items-center justify-center">
                         <div class="w-8 h-8 border-[1px] border-[#C5A25D]/5 border-b-[#C5A25D] rounded-full animate-spin-reverse duration-[3s]"></div>
                    </div>
                    <div class="text-[10px] font-serif italic text-[#C5A25D]/60 tracking-[0.5em] animate-pulse">Loading...</div>
                {/if}
            </div>
        </div>
    {/if}
</div>

<style>
    .page-container {
        display: flex;
        flex-direction: column;
    }
    
    @keyframes spin-reverse {
        from { transform: rotate(0deg); }
        to { transform: rotate(-360deg); }
    }
    .animate-spin-reverse {
        animation: spin-reverse 3s linear infinite;
    }

    /* Ensure the inner transition container grows to fill the page container */
    .page-container > div {
        flex: 1;
        display: flex;
        flex-direction: column;
    }
</style>
