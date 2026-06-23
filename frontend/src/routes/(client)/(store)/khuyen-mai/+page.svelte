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
  const siteUrl = $derived(ui.settings?.basic_info?.domain ? (ui.settings.basic_info.domain.startsWith("http") ? ui.settings.basic_info.domain : `https://${ui.settings.basic_info.domain}`) : "https://osmo.vn");
  const siteName = $derived(ui.settings?.basic_info?.site_name || "osmo.vn");
  const seoTitle = $derived(`Mã Giảm Giá - Săn Ưu Đãi Độc Quyền | ${siteName.toUpperCase()}`);
  const seoDescription = $derived(`Nhận ngay các mã giảm giá, voucher độc quyền, miễn phí vận chuyển cực hot từ ${siteName} - Mỹ phẩm chính hãng!`);
</script>

<SeoHead
  pageType="default"
  title={seoTitle}
  description={seoDescription}
  canonical="{siteUrl}/khuyen-mai"
  siteName={siteName}
/>

{#if !ui.isDetermined}
  <TikTokShopLoading variant="home" />
{:else if ui.isMobile}
  <VouchersMobile {vouchers} {products} />
{:else}
  <VouchersDesktop {vouchers} {products} />
{/if}
