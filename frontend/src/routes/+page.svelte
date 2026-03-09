<script lang="ts">
    import AdminDashboard from "$lib/components/admin/layout/AdminDashboard.svelte";
    import StorefrontHome from "$lib/components/storefront/StorefrontHome.svelte";

    let { data } = $props();
</script>

<svelte:head>
    <title>{data.tenant === 'admin' ? 'Xohi Darkboard' : 'SmartShop Storefront'}</title>
</svelte:head>

{#if data.tenant === 'admin'}
    <AdminDashboard 
        userEmail={data.user?.email} 
        isMobile={data.isMobile}
    />
{:else}
    <StorefrontHome />
{/if}
