<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';

  import type { CheckoutVariant } from '$lib/types/commerce/checkout';

  let { variants, liveViewCount, labels } = $props<{
    variants: CheckoutVariant[];
    liveViewCount: number;
    labels: { variant_title: string };
  }>();

  const shopStore = getShopStore();

  function getVariantName(v: CheckoutVariant) {
    if (!shopStore.product?.tierVariations || !v.tierIndex) return v.sku || 'Sản phẩm';
    return v.tierIndex
      .map((idx: number, tierIdx: number) => shopStore.product!.tierVariations[tierIdx]?.options[idx] || '')
      .filter((val: string) => Boolean(val))
      .join(' – ');
  }

  function getVariantImage(v: any) {
    if (!shopStore.product?.tierVariations || !v.tierIndex) return shopStore.product?.images?.[0] || '';
    for (let i = 0; i < v.tierIndex.length; i++) {
      const img = shopStore.product!.tierVariations[i]?.images[v.tierIndex[i]];
      if (img) return img;
    }
    return shopStore.product?.images?.[0] || '';
  }
</script>

<section class="mb-6">
  <div class="section-header mb-3">
    <div class="flex items-center gap-2">
      <EditableWrapper path="metadata.checkout_variant_title" label="SỬA TIÊU ĐỀ BIẾN THỂ">
        <span class="section-eyebrow">{labels.variant_title}</span>
      </EditableWrapper>
      <div class="h-1 w-1 bg-white/20 rounded-full"></div>
      <span class="text-[8px] font-bold text-emerald-400 animate-pulse">● {liveViewCount} người đang xem</span>
    </div>
    <span class="elite-chip">Ưu tiên hàng đầu</span>
  </div>
  <div class="variant-grid">
    {#each variants as v, idx}
      {@const active = shopStore.variant?.id === v.id}
      <button
        onclick={() => shopStore.selectVariant(v)}
        class="variant-card {active ? 'variant-active' : 'variant-idle'} relative"
      >
        {#if idx === 1}
          <div class="absolute -top-1.5 -right-1 z-10 px-1.5 py-0.5 bg-red-500 text-white text-[7px] font-black rounded uppercase tracking-wide shadow-lg animate-bounce">
            Sắp cháy hàng
          </div>
        {/if}
        <div class="variant-img-wrap">
          <EditableWrapper path="images.0" type="image" label="SỬA ẢNH GIỎ HÀNG">
            <img src={getVariantImage(v)} alt={getVariantName(v)} class="variant-img" />
          </EditableWrapper>
          {#if active}
            <div class="variant-check-overlay">
              <div class="variant-check">
                <svg class="w-3.5 h-3.5 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3.5" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          {/if}
        </div>
        <span class="variant-name">{getVariantName(v)}</span>
        <span class="variant-price">{(v.discountPrice || v.price).toLocaleString()}đ</span>
      </button>
    {/each}
  </div>
</section>
