<script lang="ts">
    import AdminLogin from "$lib/components/admin/AdminLogin.svelte";
    import StorefrontLogin from "$lib/components/storefront/StorefrontLogin.svelte";

    let { data } = $props();
</script>

<svelte:head>
    <title>{data.tenant === 'admin' ? 'Xohi | Admin Access' : 'Đăng nhập | SmartShop'}</title>
</svelte:head>

{#if data.tenant === 'admin'}
    <AdminLogin />
{:else}
    <StorefrontLogin />
{/if}
