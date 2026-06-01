<script lang="ts">
  import type { Voucher } from "$lib/types";
  import type { CustomItem } from "$lib/types/commerce/checkout";

  let {
    // State
    form = $bindable(),
    customItems = $bindable(),
    showCustomItemForm = $bindable(),
    newCustomItem = $bindable(),
    invalidFields,
    neuralStatus,
    errorMsg,
    shippingFee,
    helenAdvice,
    deliveryEstimate,
    showNote = $bindable(),
    isAddressFormVisible = $bindable(),
    canExpress,
    selectedProvinceData,
    showCoInspectionModal = $bindable(),
    availablePoints,
    pointsToRedeem,
    finalTotal,
    isSubmitting,

    // Methods
    toggleVoucher,
    optimizeVouchers,
    addCustomItem,
    removeCustomItem,
    handleSubmit,
    lookupCustomer,
  } = $props<{
    form: any;
    customItems: CustomItem[];
    showCustomItemForm: boolean;
    newCustomItem: CustomItem;
    invalidFields: Set<string>;
    neuralStatus: string;
    errorMsg: string;
    shippingFee: number;
    helenAdvice: string;
    deliveryEstimate: string | null;
    showNote: boolean;
    isAddressFormVisible: boolean;
    canExpress: boolean;
    selectedProvinceData: any;
    showCoInspectionModal: boolean;
    availablePoints: number;
    pointsToRedeem: number;
    finalTotal: number;
    isSubmitting: boolean;

    toggleVoucher: (v: Voucher) => void;
    optimizeVouchers: () => void;
    addCustomItem: () => void;
    removeCustomItem: (idx: number) => void;
    handleSubmit: (e: SubmitEvent) => void;
    lookupCustomer: () => void;
  }>();

  import { fade, slide } from "svelte/transition";
  import Wallet from "@lucide/svelte/icons/wallet";
  import NeuralGuardian from "$lib/components/storefront/ui/NeuralGuardian.svelte";
  import AddressSection from "./AddressSection.svelte";
  import DeliveryPaymentSection from "./DeliveryPaymentSection.svelte";
  import VoucherSection from "./VoucherSection.svelte";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { authStore } from "$lib/state/authStore.svelte";
  import { formatCurrency } from "$lib/utils/format";
  import { resolveMediaUrl } from "$lib/state/utils";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { loyaltyStore } from "$lib/state/commerce/loyalty.svelte";
  import { LOYALTY_CONFIG } from "$lib/constants/loyalty";

  const cartStore = getCartStore();
</script>

<div class="bg-[#f5f5f5] min-h-[100dvh] pb-[85px] text-gray-900 font-sans">
  <!-- HEADER -->
  <div
    class="bg-white pt-[env(safe-area-inset-top)] pb-2 px-3 sticky top-0 shadow-sm"
    style:z-index={Z_INDEX_CLIENT.HEADER}
  >
    <div class="relative flex items-center justify-center w-full h-[48px]">
      <button
        type="button"
        onclick={() => history.back()}
        class="absolute left-0 p-2 flex items-center justify-center"
        aria-label="Quay lại"
      >
        <svg
          class="w-6 h-6 text-gray-800"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2.5"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M15 19l-7-7 7-7"
          /></svg
        >
      </button>
      <div class="flex flex-col items-center">
        <h1 class="text-[17px] font-bold text-gray-900 relative">
          Giỏ hàng ({cartStore.items.length})
        </h1>
      </div>
      {#if authStore.isAuthenticated}
        <button
          type="button"
          onclick={() => {
            isAddressFormVisible = !isAddressFormVisible;
            if (isAddressFormVisible)
              setTimeout(
                () =>
                  document
                    .getElementById("address-section")
                    ?.scrollIntoView({
                      behavior: "smooth",
                      block: "start",
                    }),
                100,
              );
          }}
          class="absolute right-0 p-2 text-[14px] text-gray-700 font-medium"
          >{isAddressFormVisible ? "Đóng" : "Chỉnh sửa"}</button
        >
      {/if}
    </div>

    <!-- Address Summary (Matches Tiktok Top Bar Address) -->
    <div class="flex items-center justify-center mt-0.5 pb-1">
      <button
        type="button"
        onclick={() => {
          if (authStore.isAuthenticated) isAddressFormVisible = true;
          setTimeout(
            () =>
              document
                .getElementById("address-section")
                ?.scrollIntoView({ behavior: "smooth", block: "start" }),
            100,
          );
        }}
        class="flex items-center text-[12px] text-gray-500 hover:text-gray-800 transition-colors"
      >
        <svg
          class="w-3.5 h-3.5 mr-1 shrink-0 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
          /><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
          /></svg
        >
        <span class="truncate max-w-[200px]"
          >{form.street && form.province
            ? `${form.street}, ${form.ward}, ${form.province}`
            : "Chọn địa chỉ nhận hàng..."}</span
        >
        <svg
          class="w-3.5 h-3.5 ml-0.5 shrink-0 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5l7 7-7 7"
          /></svg
        >
      </button>
    </div>
  </div>

  {#if cartStore.items.length === 0}
    <div class="py-32 text-center space-y-4" in:fade>
      <div
        class="w-20 h-20 bg-white rounded-full flex items-center justify-center mx-auto shadow-sm"
      >
        <svg
          class="w-10 h-10 text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
          /></svg
        >
      </div>
      <p class="text-sm text-gray-500 font-medium">
        Giỏ hàng của bạn trống
      </p>
      <a
        href="/"
        class="inline-block px-10 py-3 bg-[#fe2c55] hover:bg-[#e0264b] transition-colors text-white rounded-md font-semibold text-[15px] shadow-sm"
        >Mua sắm ngay</a
      >
    </div>
  {:else}
    <div class="px-0">
      <!-- Freeship Banner -->
      {#if shippingFee === 0 && cartStore.items.some(i => i.selected)}
        <div
          class="bg-[#eaf8f4] text-[#00a870] text-[13px] font-medium px-4 py-3 flex items-center gap-2 mb-2 mt-2"
        >
          <svg
            class="w-5 h-5 text-[#00a870]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            /></svg
          >
          Bạn được Freeship!
        </div>
      {/if}

      <!-- Items list -->
      <div
        class="bg-white rounded-xl shadow-sm mb-3 mt-1 overflow-hidden mx-2"
      >
        <!-- Gift Banner -->
        {#if cartStore.items.some(item => {
            if (!item.selected) return false;
            const activeVariant = cartStore.getEffectiveVariant(item.id);
            const activeVariantName = activeVariant ? cartStore.getVariantName(item.product, activeVariant) : '';
            const resolvedGifts = activeVariant?.attributes?.gifts?.length ? activeVariant.attributes.gifts : activeVariant?.gifts?.length ? activeVariant.gifts : (activeVariantName === 'Dứt điểm' || activeVariant?.attributes?.combo_qty === 3 || activeVariant?.attributes?.comboQty === 3) ? [1] : item.product?.gifts || [];
            return resolvedGifts.length > 0;
        })}
          <div
            class="bg-[#fff0f1] text-[#fe2c55] text-[13px] font-medium px-3 py-3 flex items-center justify-between border-b border-[#ffe1e3]"
          >
            <div class="flex items-center gap-1.5">
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                /></svg
              >
              Bạn có quà miễn phí
            </div>
            <svg
              class="w-4 h-4 text-[#fe2c55]/80"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 5l7 7-7 7"
              /></svg
            >
          </div>
        {/if}

        {#each cartStore.items as item}
          {@const activeVariant = cartStore.getEffectiveVariant(item.id)}
          {@const activeVariantName = activeVariant ? cartStore.getVariantName(item.product, activeVariant) : ''}
          {@const giftMultiplierMobile = activeVariant?.attributes?.combo_qty ? Math.floor(item.quantity / activeVariant.attributes.combo_qty) : item.quantity}
          {@const resolvedGiftsMobile = activeVariant?.attributes?.gifts?.length
            ? activeVariant.attributes.gifts
            : activeVariant?.gifts?.length
              ? activeVariant.gifts
              : item.product?.gifts || []}
          <div
            class="p-3 border-b border-gray-50 flex items-start gap-3 last:border-b-0 relative"
          >
            <!-- Checkbox -->
            <button
              type="button"
              class="mt-[28px] shrink-0"
              onclick={() => cartStore.toggleItemSelection(item.id)}
            >
              <div
                class="w-[18px] h-[18px] rounded-full flex items-center justify-center border {item.selected
                  ? 'bg-[#fe2c55] border-[#fe2c55]'
                  : 'border-gray-300'} transition-colors"
              >
                {#if item.selected}
                  <svg
                    class="w-3 h-3 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    stroke-width="3"
                    ><path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M5 13l4 4L19 7"
                    /></svg
                  >
                {/if}
              </div>
            </button>

            <!-- Image -->
            <div
              class="w-[88px] h-[88px] bg-gray-50 rounded-lg overflow-hidden shrink-0 border border-gray-100"
            >
              <img
                src={item.product.images?.[0] ||
                  "/favicon.svg"}
                alt={item.product.name}
                class="w-full h-full object-cover"
              />
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <h4
                class="text-[14px] text-gray-800 leading-snug line-clamp-2"
              >
                {item.product.name}
              </h4>

              <div class="mt-1 flex flex-nowrap items-center gap-1.5 min-w-0">
                {#if activeVariant}
                  <button
                    class="flex items-center bg-[#fff0f1] border border-[#fecdd3] text-[#fe2c55] font-bold text-[10px] px-1.5 py-0.5 rounded-[2px] gap-1 active:bg-[#ffe4e6] transition-colors shadow-sm leading-none min-w-0"
                  >
                    <span class="truncate"
                      >Phân loại: {activeVariantName || activeVariant.sku}</span
                    >
                    <svg
                      class="w-3 h-3 shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      ><path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 9l-7 7-7-7"
                      /></svg
                    >
                  </button>
                {/if}
                
                <div class="flex items-center gap-1 shrink-0">
                  <span
                    class="bg-gradient-to-r from-[#ff4760] to-[#fe2c55] text-white text-[9px] font-bold px-1.5 py-[3px] rounded-[2px] shadow-sm leading-none"
                    >Flash Sale</span
                  >
                  {#if item.variant?.discountPrice || item.product.discountPrice}
                    <span
                      class="text-[#fe2c55] text-[9px] font-bold flex items-center gap-0.5 leading-none shrink-0"
                    >
                      <svg
                        class="w-3 h-3 shrink-0"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        ><path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                        /></svg
                      >
                      04:46:42
                    </span>
                  {/if}
                </div>
              </div>

              <div class="flex items-end justify-between mt-2 max-w-full gap-1">
                <div class="flex items-center gap-1 flex-1 min-w-0">
                  <div
                    class="text-[14px] font-bold text-[#fe2c55] leading-none shrink-0 flex items-center gap-0.5"
                  >
                    {formatCurrency(cartStore.getEffectiveItemPrice(item.id))}
                    {#if cartStore.getEffectiveItemPrice(item.id) < (item.variant?.discountPrice || item.product.discountPrice || item.variant?.price || item.product.price || 0)}
                      <span class="text-[8px] bg-[#fe2c55] text-white px-1 py-[1px] rounded-[2px] font-black italic tracking-tighter shadow-sm animate-pulse-subtle leading-none">Combo</span>
                    {/if}
                  </div>
                  <div class="flex items-center gap-0.5 min-w-0">
                    {#if cartStore.getEffectiveItemPrice(item.id) < (item.variant?.discountPrice || item.product.discountPrice || 0)}
                      <span class="text-[10px] text-gray-400 line-through shrink-0 italic">{formatCurrency(item.variant?.discountPrice || item.product.discountPrice || 0)}</span>
                    {:else if (item.variant?.discountPrice || item.product.discountPrice) && (item.variant?.price || item.product.price)}
                      <span class="text-[10px] text-gray-400 line-through shrink-0">{formatCurrency(item.variant?.price || item.product.price || 0)}</span>
                    {/if}
                    {#if (item.variant?.discountPrice || item.product.discountPrice) && (item.variant?.price || item.product.price)}
                      <span class="bg-[#fff0f1] text-[#fe2c55] text-[8px] px-0.5 py-[1px] rounded-[2px] font-bold shrink-0 leading-none">
                        -{Math.round(100 - (cartStore.getEffectiveItemPrice(item.id) / (item.variant?.price ?? item.product.price ?? 1)) * 100)}%
                      </span>
                    {/if}
                  </div>
                </div>

                <!-- Qty Control matches TikTok design: border, compact -->
                <div
                  class="flex items-center border border-gray-200 rounded shrink-0 bg-white"
                >
                  <button
                    type="button"
                    onclick={() =>
                      cartStore.updateQuantity(item.id, item.quantity - 1)}
                    class="w-7 h-6 flex items-center justify-center text-gray-500 font-medium active:bg-gray-100 border-r border-gray-200"
                    >-</button
                  >
                  <span
                    class="text-[13px] font-medium min-w-[24px] text-center bg-gray-50"
                    >{item.quantity}</span
                  >
                  <button
                    type="button"
                    onclick={() =>
                      cartStore.updateQuantity(item.id, item.quantity + 1)}
                    class="w-7 h-6 flex items-center justify-center text-gray-500 font-medium active:bg-gray-100 border-l border-gray-200"
                    >+</button
                  >
                </div>
              </div>

              <!-- QUÀ TẶNG KÈM THEO MOBILE -->
              {#if resolvedGiftsMobile && resolvedGiftsMobile.length > 0}
                <div
                  class="mt-2.5 bg-[#fef2f2] border border-[#fecdd3] rounded-sm p-1.5 flex flex-col gap-1.5 w-full relative overflow-hidden"
                >
                  <div
                    class="absolute inset-0 bg-gradient-to-r from-[#ffe4e6]/50 to-transparent pointer-events-none"
                  ></div>
                  <span
                    class="text-[10px] font-bold text-[#e11d48] flex items-center gap-1 leading-none relative z-10"
                  >
                    <svg
                      class="w-3 h-3"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      ><path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2.5"
                        d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"
                      /></svg
                    >
                    Quà tặng kèm:
                  </span>
                  
                  <div class="space-y-1.5 relative z-10">
                    {#each resolvedGiftsMobile as gift}
                      <div class="flex items-center gap-2 pl-0.5">
                        <!-- 🎁 MOBILE GIFT IMAGE -->
                        <div class="w-6 h-6 bg-white border border-[#fecdd3] rounded-[2px] overflow-hidden shrink-0 flex items-center justify-center">
                          {#if gift.image}
                            <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                          {:else}
                            <svg class="w-3 h-3 text-[#fecdd3]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                          {/if}
                        </div>
                        
                        <div class="flex-1 flex items-center justify-between min-w-0">
                          <span
                            class="text-[#e11d48] font-bold text-[10px] tracking-tight truncate pr-2"
                            >{gift.name}</span
                          >
                          <span
                            class="text-[#e11d48] font-black text-[10px] shrink-0 min-w-[16px] text-center bg-[#ffe4e6] px-1 rounded-[2px]"
                            >x{(gift.qty || gift.quantity || 1) * giftMultiplierMobile}</span
                          >
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          </div>
        {/each}

        <!-- MAPPED CUSTOM ITEMS ON MOBILE -->
        {#if customItems.length > 0}
          <div class="px-3 pb-3 space-y-2 border-t border-gray-100 pt-3">
            <h3
              class="text-[10px] font-black text-gray-400 tracking-widest flex items-center gap-1.5"
            >
              <svg
                class="w-3.5 h-3.5 text-[#fe2c55]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2.5"
                  d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"
                /></svg
              >
              Yêu cầu mua thêm
            </h3>
            {#each customItems as item, idx}
              <div
                class="flex gap-3 bg-[#fff0f1]/50 p-2 border border-[#ffe1e3] rounded relative group"
              >
                <div
                  class="w-10 h-10 bg-white border border-[#ffe1e3] shrink-0 flex items-center justify-center overflow-hidden rounded-sm"
                >
                  {#if item.image && item.image.startsWith("http")}
                    <img
                      src={item.image}
                      alt={item.name}
                      class="w-full h-full object-cover"
                    />
                  {:else}
                    <svg
                      class="w-5 h-5 text-gray-300"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      ><path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="1.5"
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 00-2 2z"
                      /></svg
                    >
                  {/if}
                </div>
                <div class="flex-1 min-w-0 flex flex-col justify-center">
                  <h4
                    class="text-[10px] font-bold text-gray-800 line-clamp-1"
                  >
                    {item.name}
                  </h4>
                  <div class="text-[9px] text-gray-500 font-medium">
                    SL: {item.quantity} ·
                    <span class="text-[#fe2c55]">Chờ báo giá</span>
                  </div>
                </div>
                <button
                  type="button"
                  onclick={() => removeCustomItem(idx)}
                  class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-white border border-gray-200 text-gray-400 hover:text-[#fe2c55] rounded-full flex items-center justify-center shadow-sm"
                >
                  <svg
                    class="w-3 h-3"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    ><path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="3"
                      d="M6 18L18 6M6 6l12 12"
                    /></svg
                  >
                </button>
              </div>
            {/each}
          </div>
        {/if}

        <!-- ADD CUSTOM ITEM BUTTON/FORM ON MOBILE -->
        <div
          class="px-3 pb-3 {customItems.length === 0
            ? 'pt-3 border-t border-gray-50'
            : 'pt-0'}"
        >
          {#if !showCustomItemForm}
            <button
              type="button"
              onclick={() => (showCustomItemForm = true)}
              class="w-full py-3 border-2 border-dashed border-gray-200 text-gray-500 hover:border-[#fe2c55] hover:text-[#fe2c55] hover:bg-[#fff0f1] transition-all flex items-center justify-center gap-2 rounded-lg group"
            >
              <svg
                class="w-4 h-4 transition-transform group-hover:scale-110"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2.5"
                  d="M12 4v16m8-8H4"
                /></svg
              >
              <span class="text-[11px] font-bold tracking-wide"
                >Yêu cầu thêm sản phẩm khác</span
              >
            </button>
          {:else}
            <div
              class="p-3 bg-gray-50 border border-gray-100 rounded-lg space-y-3"
              transition:slide
            >
              <div class="flex items-center justify-between">
                <span
                  class="text-[10px] font-bold text-gray-800 flex items-center gap-1.5"
                >
                  <div class="w-1.5 h-1.5 bg-[#fe2c55] rounded-full"></div>
                  Thông tin sản phẩm muốn thêm
                </span>
                <button
                  type="button"
                  onclick={() => (showCustomItemForm = false)}
                  class="text-gray-400 hover:text-gray-950"
                  ><svg
                    class="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    ><path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"
                    /></svg
                  ></button
                >
              </div>
              <div class="space-y-2">
                <input
                  id="mobile-custom-name"
                  type="text"
                  bind:value={newCustomItem.name}
                  placeholder="VD: Sữa rửa mặt Cerave SA..."
                  class="w-full bg-white border border-gray-200 px-3 py-2 text-[12px] font-medium outline-none focus:border-[#fe2c55] rounded"
                />
                <div class="grid grid-cols-2 gap-2">
                  <input
                    id="mobile-custom-qty"
                    type="number"
                    bind:value={newCustomItem.quantity}
                    placeholder="Số lượng"
                    class="w-full bg-white border border-gray-200 px-3 py-2 text-[12px] font-medium outline-none focus:border-[#fe2c55] rounded"
                  />
                  <input
                    id="mobile-custom-price"
                    type="number"
                    bind:value={newCustomItem.price}
                    placeholder="Giá dự kiến (nếu có)"
                    class="w-full bg-white border border-gray-200 px-3 py-2 text-[12px] font-medium outline-none focus:border-[#fe2c55] rounded"
                  />
                </div>
                <input
                  id="mobile-custom-image"
                  type="text"
                  bind:value={newCustomItem.image}
                  placeholder="Link ảnh hoặc ghi chú..."
                  class="w-full bg-white border border-gray-200 px-3 py-2 text-[12px] font-medium outline-none focus:border-[#fe2c55] rounded"
                />
              </div>
              <button
                type="button"
                onclick={addCustomItem}
                class="w-full py-2.5 bg-gray-900 text-white text-[11px] font-bold tracking-wider hover:bg-[#fe2c55] transition-colors rounded"
              >
                Xác nhận thêm
              </button>
            </div>
          {/if}
        </div>
      </div>

      <!-- AGENTIC AI OVERSIGHT (MOBILE - TỔNG HỢP SAU Giỏ hàng) -->
      <!-- [ELITE V2.2] Professional Loyalty Toggle Mobile -->
      {#if authStore.isAuthenticated && availablePoints > 0}
        <div class="px-2 mb-3 mt-1" in:slide>
          <div
            class="bg-white rounded-xl shadow-sm overflow-hidden select-none"
          >
            <!-- Toggle Row -->
            <div
              class="p-4 flex items-center justify-between active:bg-gray-50 transition-colors cursor-pointer"
              onclick={() => (form.usePoints = !form.usePoints)}
            >
              <div class="flex items-center gap-3">
                <div
                  class="w-10 h-10 rounded-full flex items-center justify-center {form.usePoints
                    ? 'bg-amber-500/10 text-amber-600'
                    : 'bg-gray-100 text-gray-400'} transition-all"
                >
                  <Wallet class="w-5 h-5" />
                </div>
                <div>
                  <span
                    class="text-[13px] font-bold text-gray-800 tracking-widest leading-none"
                    >Dùng {availablePoints} {loyaltyStore.data?.point_unit ?? "điểm"} tích lũy</span
                  >
                  <p
                    class="text-[11px] text-gray-500 mt-0.5 font-medium italic"
                  >
                    Tiết kiệm {formatCurrency(pointsToRedeem * LOYALTY_CONFIG.POINT_VALUE)} cho đơn
                    này
                  </p>
                </div>
              </div>

              <div
                class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none {form.usePoints
                  ? 'bg-[#fe2c55]'
                  : 'bg-gray-200'}"
              >
                <span
                  class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 {form.usePoints
                    ? 'translate-x-5'
                    : 'translate-x-0'}"
                ></span>
              </div>
            </div>

            <!-- Mobile FOMO Tip (Always visible, compact) -->
            <div class="px-4 pb-3 pt-0 border-t border-gray-50">
              <div
                class="flex items-start gap-2 bg-amber-50/80 rounded-lg p-2.5 mt-2"
              >
                <div class="w-4 h-4 shrink-0 mt-0.5">
                  <svg
                    class="w-4 h-4 text-amber-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    ><path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    /></svg
                  >
                </div>
                <div>
                  <p
                    class="text-[10px] text-gray-700 font-bold leading-relaxed"
                  >
                    🔥 Đơn này tích thêm <span
                      class="text-[#fe2c55] font-black"
                      >+{Math.floor(finalTotal / LOYALTY_CONFIG.EARNING_RATE_VND)} {loyaltyStore.data?.point_unit ?? "điểm"}</span
                    >. Mua thêm combo để
                    <span
                      class="bg-[#fe2c55] text-white px-1 rounded-sm text-[9px] font-black"
                      >X2 TÍCH LŨY</span
                    >
                  </p>
                  <p
                    class="text-[9px] text-gray-400 font-medium mt-1 italic"
                  >
                    Luật: Giảm tối đa 1% đơn hàng · #StayElite
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      {/if}

      <div class="px-2 mb-3 mt-1">
        <NeuralGuardian status={neuralStatus} advice={helenAdvice} />
      </div>

      <!-- Extra Fields (Required for Checkout to function) styled conservatively -->
      {#if isAddressFormVisible}
        <div
          id="address-section"
          transition:slide
          class="mb-3 mt-3 mx-2 scroll-mt-[90px]"
        >
          <AddressSection
            bind:form
            {invalidFields}
            bind:showNote
            bind:orderNote={form.note}
            {lookupCustomer}
          />
        </div>
      {/if}

      <div
        class="bg-white rounded-xl shadow-sm mb-3 overflow-hidden p-4 mx-2"
      >
        <DeliveryPaymentSection
          bind:form
          {deliveryEstimate}
          {canExpress}
          {selectedProvinceData}
          bind:showCoInspectionModal
          {shippingFee}
        />
      </div>

      <div
        class="bg-white rounded-xl shadow-sm mb-3 overflow-hidden p-4 mx-2"
      >
        <VoucherSection
          vouchers={cartStore.vouchers}
          {toggleVoucher}
          onOptimize={optimizeVouchers}
        />
      </div>
    </div>

    <!-- Terms and Conditions -->
    <div
      class="px-3 pb-2 pt-2 text-[10.5px] leading-snug text-gray-400 text-center"
    >
      Bằng cách đặt đơn hàng, bạn đồng ý với <a
        href="/terms"
        class="font-bold text-gray-700 hover:underline"
        >Điều khoản sử dụng và bán hàng của cửa hàng</a
      >
      và đồng ý rằng dữ liệu của bạn sẽ được xử lý theo
      <a href="/privacy" class="font-bold text-gray-700 hover:underline"
        >Chính sách quyền riêng tư của cửa hàng</a
      >.
    </div>

    <!-- Fixed Bottom Bar -->
    <div
      class="fixed bottom-0 left-0 w-full bg-white border-t border-gray-100 px-3 py-2 flex items-center justify-between pb-[calc(10px+env(safe-area-inset-bottom))]"
      style:z-index={Z_INDEX_CLIENT.HEADER}
    >
      <label class="flex items-center gap-2">
        <button
          type="button"
          class="shrink-0"
          onclick={() =>
            cartStore.toggleAll(
              cartStore.selectedItemsCount < cartStore.totalItems,
            )}
        >
          <div
            class="w-[18px] h-[18px] rounded-full flex items-center justify-center border {cartStore.selectedItemsCount ===
              cartStore.totalItems && cartStore.totalItems > 0
              ? 'bg-[#fe2c55] border-[#fe2c55]'
              : 'border-gray-300'} transition-colors"
          >
            {#if cartStore.selectedItemsCount === cartStore.totalItems && cartStore.totalItems > 0}
              <svg
                class="w-3.5 h-3.5 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="3"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M5 13l4 4L19 7"
                /></svg
              >
            {/if}
          </div>
        </button>
        <span class="text-[14px] text-gray-600">Tất cả</span>
      </label>

      <div class="flex items-center gap-3">
        <div class="text-right flex flex-col justify-center">
          {#if cartStore.totalDiscount > 0 || shippingFee === 0}
            <div class="text-[11px] text-gray-500 leading-tight">
              {#if shippingFee === 0}Freeship{/if}
              {#if cartStore.totalDiscount > 0}
                · Giảm {formatCurrency(cartStore.totalDiscount)}{/if}
            </div>
          {/if}
          <div
            class="text-[15px] font-bold text-[#fe2c55] leading-tight flex items-center gap-1 justify-end"
          >
            {formatCurrency(finalTotal)}
            <svg
              class="w-3 h-3 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 15l7-7 7 7"
              /></svg
            >
          </div>
        </div>
        <button
          type="button"
          onclick={(e) => handleSubmit(e as unknown as SubmitEvent)}
          disabled={isSubmitting || cartStore.selectedItemsCount === 0}
          class="px-5 py-3 bg-[#fe2c55] text-white text-[15px] font-semibold rounded-lg min-w-[140px] shadow-sm shadow-[#fe2c55]/30 disabled:opacity-50 disabled:cursor-not-allowed active:bg-[#e0264b] transition-colors flex justify-center items-center overflow-hidden relative group"
        >
          {#if neuralStatus === "verifying"}
            <div class="flex items-center gap-2" in:slide={{ axis: "y" }}>
              <div
                class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"
              ></div>
              <span
                class="text-[11px] font-black tracking-widest leading-none"
                >Neural Verifying...</span
              >
            </div>
          {:else}
            Thanh toán ({cartStore.selectedItemsCount})
          {/if}
        </button>
      </div>
    </div>
  {/if}
</div>
