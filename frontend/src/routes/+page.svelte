<script lang="ts">
    import type { PageData } from './$types';
    import { fade } from 'svelte/transition';
    import { onMount, type Component } from 'svelte';
    import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
    import DailyCheckinLanding from '$lib/components/storefront/loyalty/DailyCheckinLanding.svelte';

    /**
     * ELITE V2.2 - MISSION CONTROL HUB
     * Logic: Zero-latency component selection based on verified tenant data.
     * Rule: Static Typing (No 'any'), Rune-based reactivity.
     */
    let { data }: { data: PageData } = $props();

    // ELITE V2.2: Dynamic Component State (Post-Mount Resolution)
    let activeComponent = $state<Component<{ data: PageData; isMobile: boolean }> | null>(null);

    const loadAdmin = () => import("$lib/components/admin/layout/AdminDashboard.svelte");
    const loadStorefront = () => import("$lib/components/storefront/StorefrontHome.svelte");

    onMount(async () => {
        // Disable GA/GTM/Pixel tracking early if in admin tenant mode to prevent data leak
        if (data.tenant === 'admin') {
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
        }

        try {
            if (data.tenant === 'admin') {
                const mod = await loadAdmin();
                activeComponent = mod.default;
            } else {
                const mod = await loadStorefront();
                activeComponent = mod.default;
            }
        } catch (err) {
            console.error("[SYSTEM FAULT] DYNAMIC_LOAD_FAILED:", err);
            if (typeof window !== 'undefined') {
                console.warn("[RECOVER] Chunk loading failed. Reloading page to force synchronization...");
                window.location.reload();
            }
        }
    });

    // ELITE V2.2: SEO Derivation logic (Zero-Latency Sync)
    const shopSettings = $derived(data.shopInfo);
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

{#if data.tenant !== 'admin'}
    <SeoHead
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
{:else}
    <SeoHead title="Admin Control Center" robots="noindex, nofollow" />
{/if}

<svelte:head>
    {#if data.tenant === 'admin'}
        <title>Xohi Darkboard</title>
    {/if}
</svelte:head>

<div class="page-container md:h-auto md:overflow-visible h-dvh overflow-x-hidden overflow-y-auto bg-[#010101]">
    {#if activeComponent}
        <div in:fade={{ duration: 300 }} class="flex-1 flex flex-col">
            <svelte:component
                this={activeComponent}
                data={data}
                isMobile={data.isMobile}
            />
        </div>
        {#if data.tenant !== 'admin'}
            <DailyCheckinLanding />
        {/if}
    {:else}
        <!-- Luxury Storefront/Admin Loading State (Elite V2.2) -->
        <div class="fixed inset-0 flex items-center justify-center bg-[#020202] z-[var(--z-modal-overlay)]">
            <div class="relative flex flex-col items-center gap-6">
                {#if data.tenant === 'admin'}
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
