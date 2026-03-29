<script lang="ts">
  import type { Product } from '$lib/types';
  import { X } from 'lucide-svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { Z_INDEX } from '$lib/core/constants/zIndex';
  import { portal } from '$lib/core/actions/portal'; // Giả định portal action đã tồn tại

  const shopStore = getShopStore();

  let { active = $bindable(), product }: { active: boolean, product: Product } = $props();

  const metadata = $derived(product?.metadata || {});

  const labels = $derived({
    title: (metadata.mobile_bottom_sheet_title as string) || "Chi tiết sản phẩm",
    cta: (metadata.mobile_bottom_sheet_cta as string) || "MUA NGAY VỚI VOUCHER",
    free_shipping: (metadata.mobile_free_shipping_label as string) || "⚡ FREESHIP TOÀN QUỐC",
    variant_label: (metadata.mobile_variant_selection_label as string) || "Chọn phân loại sản phẩm",
    loading: (metadata.sync_loading_text as string) || "Đang tải cấu hình sản phẩm...",
    view_more: (metadata.mobile_label_view_more as string) || "Xem thêm >",
    aria_close: (metadata.mobile_aria_close as string) || "Đóng"
  });

  function close() {
    active = false;
  }

  function addToCartAndClose() {
    if (product?.id) {
       shopStore.addItem(product);
    }
    close();
  }
</script>

<div use:portal class="mobile-bottom-sheet-root">
  <button
    type="button"
    class="mobile-bottom-sheet-bg border-none outline-none transition-opacity duration-300"
    style="z-index: {Z_INDEX.OVERLAY}"
    class:active
    onclick={close}
    aria-label={labels.aria_close}
  ></button>

  <div
    class="mobile-bottom-sheet transition-transform duration-300 ease-out bg-white rounded-t-[24px] flex flex-col shadow-2xl"
    class:active
    style="z-index: {Z_INDEX.MODAL}; padding-bottom: calc(1rem + env(safe-area-inset-bottom))"
    role="dialog"
    aria-modal="true"
    aria-labelledby="sheet-title"
  >
    <div class="w-full flex justify-center pt-3 pb-1 cursor-grab active:cursor-grabbing">
      <div class="pill-handle w-10 h-1.5 bg-gray-200 rounded-full"></div>
    </div>

    <div class="flex justify-between items-center px-4 pb-3 border-b border-gray-50 relative">
      <h2 id="sheet-title" class="text-[15px] font-bold font-heading w-full text-center text-gray-900">{labels.title}</h2>
      <button
        onclick={close}
        class="absolute right-4 p-2 rounded-full bg-gray-100 hover:bg-gray-200 active:scale-90 transition-all"
        aria-label={labels.aria_close}
      >
        <X class="w-4 h-4 text-gray-600" />
      </button>
    </div>

    <div class="p-5 flex-1 overflow-y-auto w-full max-w-lg mx-auto scrollbar-hide">
      {#if product}
        <div class="flex items-center gap-4 mb-6">
          {#if product.images?.length > 0}
            <div class="relative w-24 h-24 flex-shrink-0">
              <img
                src={product.images[0]}
                alt={product.name}
                class="w-full h-full rounded-2xl object-cover border border-gray-100 shadow-sm"
              />
            </div>
          {/if}
          <div class="flex flex-col justify-center gap-0.5">
            <div class="flex items-baseline gap-2">
              <span class="font-bold text-gray-900 text-2xl tracking-tighter text-[#fe2c55]">
                {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(product.price)}
              </span>
              {#if product.discountPrice}
                <span class="text-sm text-gray-400 line-through decoration-gray-300">
                  {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(product.discountPrice)}
                </span>
              {/if}
            </div>
            <div class="mt-1.5 text-[11px] text-[#fe2c55] font-bold bg-[#fe2c55]/10 px-2.5 flex items-center w-fit rounded h-6 border border-[#fe2c55]/20">
              {labels.free_shipping}
            </div>
            <p class="text-[13px] text-gray-500 mt-2 line-clamp-1">{product.name}</p>
          </div>
        </div>

        <div class="space-y-4">
          <!-- Phân loại / Biến thể (Nếu có) -->
          <div class="bg-gray-50 rounded-xl p-3 flex justify-between items-center group cursor-pointer hover:bg-gray-100 transition-colors">
            <span class="text-[13px] font-medium text-gray-600">{labels.variant_label}</span>
            <span class="text-[13px] text-gray-400">{labels.view_more}</span>
          </div>

          <button
            class="w-full py-4 bg-[#fe2c55] text-white font-bold text-[16px] rounded-2xl active:scale-95 transition-all shadow-lg shadow-[#fe2c55]/20 flex items-center justify-center gap-2"
            onclick={addToCartAndClose}
          >
            {labels.cta}
          </button>
        </div>
      {:else}
        <div class="flex flex-col items-center justify-center py-10 gap-3">
          <div class="w-10 h-10 border-4 border-gray-100 border-t-[#fe2c55] rounded-full animate-spin"></div>
          <p class="text-sm text-gray-400 italic">{labels.loading}</p>
        </div>
      {/if}
    </div>
  </div>
</div>
