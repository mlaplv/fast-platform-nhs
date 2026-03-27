<script lang="ts">
    let { data } = $props();
    let DynamicComponent = $state<import('svelte').Component | null>(null);

    $effect(() => {
        (async () => {
            if (data.tenant === 'admin') {
                const mod = await import("$lib/components/admin/layout/AdminDashboard.svelte");
                DynamicComponent = mod.default;
            } else {
                const mod = await import("$lib/components/storefront/StorefrontHome.svelte");
                DynamicComponent = mod.default;
            }
        })();
    });
</script>

<svelte:head>
    <title>{data.tenant === 'admin' ? 'Xohi Darkboard' : 'SmartShop Storefront'}</title>
</svelte:head>

{#if DynamicComponent}
    <DynamicComponent 
        userEmail={data.user?.email} 
        isMobile={data.isMobile}
    />
{:else}
    <!-- Minimal Loading State: Standard CSS derived from layout.css -->
    <div class="root-loading-container">
        <div class="loading-spinner"></div>
    </div>
{/if}
