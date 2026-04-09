<script lang="ts">
    import HomeDesktop from './home/HomeDesktop.svelte';
    import HomeMobile from './home/HomeMobile.svelte';
    import HeaderDesktop from './layout/HeaderDesktop.svelte';
    import FooterDesktop from './layout/FooterDesktop.svelte';
    import HeaderMobile from './layout/HeaderMobile.svelte';
    import BottomNavMobile from './layout/BottomNavMobile.svelte';
    import "./home/home.css";

    let { data, isMobile }: { data: any, isMobile: boolean } = $props();
</script>

{#if isMobile}
    <HeaderMobile />
    <HomeMobile videos={data.videos} />
    <BottomNavMobile />
{:else}
    <HeaderDesktop />
    <main>
        <HomeDesktop
            banners={data.banners}
            categories={data.categories}
            products={data.products}
        />
    </main>
    <FooterDesktop />
{/if}
