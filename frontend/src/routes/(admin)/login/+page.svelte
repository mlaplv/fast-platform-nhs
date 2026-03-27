<script lang="ts">
    import AdminLogin from "$lib/components/admin/AdminLogin.svelte";
    let { data } = $props();
</script>

<svelte:head>
    <title>Xohi | Admin Access</title>
</svelte:head>

<AdminLogin />
