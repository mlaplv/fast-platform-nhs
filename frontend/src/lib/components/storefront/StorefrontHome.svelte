<script lang="ts">
    import HomeDesktop from './home/HomeDesktop.svelte';
    import HomeMobile from './home/HomeMobile.svelte';
    import HeaderDesktop from './layout/HeaderDesktop.svelte';
    import FooterDesktop from './layout/FooterDesktop.svelte';
    import "./home/home.css";

    let { data, isMobile }: { data: any, isMobile: boolean } = $props();
</script>

{#if isMobile}
    <HomeMobile 
        banners={data.banners}
        categories={data.categories}
        products={data.products}
        aiProducts={data.ai_products}
        videos={data.videos} 
    />
{:else}
    <HeaderDesktop />
    <main>
        <HomeDesktop
            banners={data.banners}
            categories={data.categories}
            products={data.products}
            aiProducts={data.ai_products}
        />
    </main>
    <FooterDesktop />
{/if}
