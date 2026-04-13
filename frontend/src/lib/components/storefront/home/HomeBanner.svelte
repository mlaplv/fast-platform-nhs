<script lang="ts">
  import type { Banner } from '$lib/types';

  interface Props {
    banners: Banner[];
  }
  let { banners }: Props = $props();

  // Elite V2.2: Neural Link Intelligence
  // Tự động chuẩn hóa link: Nếu chỉ là slug -> /product/slug, nếu là full url -> giữ nguyên
  function getProductLink(url?: string) {
    if (!url) return '#';
    if (url.startsWith('http') || url.startsWith('/')) return url;
    return `/${url}`; // Mặc định là slug sản phẩm vì đã bỏ tiền tố /product ở route
  }

  // Chỉ lấy banner đầu tiên ở mỗi vị trí (giới hạn 1 slide)
  const mainBanner = $derived(banners.find(b => b.position === 'home_main') ?? null);
  let sideBanners = $derived(banners.filter(b => b.position === 'home_side'));
</script>

<!-- Desktop Layout: Micsmo Hero Premium 2026 -->
<div class="hidden md:grid grid-cols-3 gap-[5px] w-full" style="aspect-ratio: 1200 / 235;">
  <!-- Main Banner (1 slide duy nhất) -->
  <div 
    class="col-span-2 relative h-full rounded-[2px] overflow-hidden bg-[#eee]"
    role="region"
    aria-label="banner-chinh"
  >
    {#if mainBanner}
      <a href={getProductLink(mainBanner.link_url)} class="w-full h-full block">
        <img src={mainBanner.image_url} alt={mainBanner.title || "Main Banner"} class="w-full h-full object-cover" />
      </a>
    {/if}
  </div>

  <!-- Side Banners -->
  <div class="flex flex-col gap-[5px] h-full">
    {#each sideBanners as banner}
      <!-- Micsmo style hover effect -->
      <a href={getProductLink(banner.link_url)} class="flex-1 relative rounded-[2px] overflow-hidden group block bg-[#eee]">
        <img src={banner.image_url} alt={banner.title || "Side Banner"} class="w-full h-full object-cover transition-opacity duration-300 hover:opacity-95 active:opacity-90" />
      </a>
    {/each}
  </div>
</div>

<!-- Mobile Layout: 1 banner duy nhất -->
<div class="md:hidden relative h-[90px] w-full mb-4 rounded-none overflow-hidden bg-white shadow-sm">
  {#if mainBanner}
    <a href={getProductLink(mainBanner.link_url)} class="w-full h-full block">
      <img src={mainBanner.image_url} alt={mainBanner.title || "Banner"} class="w-full h-full object-cover" />
    </a>
  {/if}
</div>
