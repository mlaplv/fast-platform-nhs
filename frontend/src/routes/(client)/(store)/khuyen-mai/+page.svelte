<script lang="ts">
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import TikTokShopLoading from "$lib/components/storefront/product/TikTokShopLoading.svelte";
  import VouchersDesktop from "$lib/components/storefront/khuyen-mai/VouchersDesktop.svelte";
  import VouchersMobile from "$lib/components/storefront/khuyen-mai/VouchersMobile.svelte";
  import SeoHead from "$lib/components/storefront/seo/SeoHead.svelte";
  import type { PageData } from "./$types";
  import type { Voucher, Product } from "$lib/types";

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();

  const vouchers = $derived((data.vouchers as Voucher[]) ?? []);
  const products = $derived((data.products as Product[]) ?? []);

  // SEO & Metadata settings
  const siteUrl = "https://osmo.vn";
  const seoSiteName = "osmo Elite";
  const seoTitle = "Mã Giảm Giá - Săn Ưu Đãi Độc Quyền | OSMO.VN";
  const seoDescription = "Nhận ngay các mã giảm giá, voucher độc quyền, miễn phí vận chuyển cực hot từ OSMO - Mỹ phẩm Nhật Bản chính hãng!";
</script>

<SeoHead
  pageType="article"
  title={seoTitle}
  description={seoDescription}
  canonical="{siteUrl}/khuyen-mai"
  siteName={seoSiteName}
/>

{#if !ui.isDetermined}
  <TikTokShopLoading variant="home" />
{:else if ui.isMobile}
  <VouchersMobile {vouchers} {products} />
{:else}
  <VouchersDesktop {vouchers} {products} />
{/if}
