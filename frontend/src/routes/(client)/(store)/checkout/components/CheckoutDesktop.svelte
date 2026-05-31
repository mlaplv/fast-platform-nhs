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
    originalSubtotal,
    productSavings,
    totalSavings,

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
    originalSubtotal: number;
    productSavings: number;
    totalSavings: number;

    toggleVoucher: (v: Voucher) => void;
    optimizeVouchers: () => void;
    addCustomItem: () => void;
    removeCustomItem: (idx: number) => void;
    handleSubmit: (e: SubmitEvent) => void;
    lookupCustomer: () => void;
  }>();

  import { fade, slide } from "svelte/transition";
  import Countdown from "$lib/components/storefront/ui/Countdown.svelte";
  import AddressSection from "./AddressSection.svelte";
  import DeliveryPaymentSection from "./DeliveryPaymentSection.svelte";
  import VoucherSection from "./VoucherSection.svelte";
  import CheckoutItems from "./CheckoutItems.svelte";
  import OrderSummarySection from "./OrderSummarySection.svelte";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";

  const cartStore = getCartStore();
</script>

<div class="pb-20 pt-4 md:pt-10">
  <div class="max-w-[1240px] mx-auto px-4">
    {#if cartStore.items.length === 0}
      <div class="py-20 text-center space-y-6" in:fade>
        <div
          class="w-24 h-24 bg-white rounded-full flex items-center justify-center mx-auto shadow-sm"
        >
          <svg
            class="w-12 h-12 text-gray-200"
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
        <h1 class="text-xl font-black text-gray-900 italic tracking-widest">
          Giỏ hàng đang trống
        </h1>
        <p class="text-xs text-gray-400 font-bold tracking-widest">
          Bạn chưa chọn sản phẩm nào để thanh toán.
        </p>
        <a
          href="/"
          class="inline-block px-10 py-4 bg-gray-900 text-white font-black text-xs tracking-[0.3em] hover:bg-[#ee4d2d] transition-colors"
          >Quay lại cửa hàng</a
        >
      </div>
    {:else}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div class="lg:col-span-7 space-y-6">
          <div class="flex items-center justify-between mb-2">
            <h1
              class="text-2xl font-black italic text-gray-900 tracking-tighter"
            >
              Xác nhận đơn hàng
            </h1>
            <div class="flex items-center gap-2">
              <span class="text-[9px] font-bold text-gray-400"
                >Sale kết thúc:</span
              >
              <Countdown
                initialSeconds={3600 + Math.floor(Math.random() * 3600)}
              />
            </div>
          </div>

          {#if errorMsg}
            <div
              class="p-5 bg-white border-l-4 border-[#ee4d2d] shadow-[0_10px_30px_rgba(238,77,45,0.1)] flex items-start gap-4 mb-6"
              in:slide
            >
              <div
                class="w-10 h-10 rounded-full bg-[#fff0f1] flex items-center justify-center shrink-0"
              >
                <svg
                  class="w-5 h-5 text-[#ee4d2d]"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  /></svg
                >
              </div>
              <div>
                <h3 class="text-sm font-black text-gray-900 mb-1 italic">
                  Helen AI: Yêu cầu bổ sung thông tin
                </h3>
                <p
                  class="text-xs text-gray-500 font-medium leading-relaxed"
                >
                  Thông tin vận chuyển chưa hoàn thiện. Helen đã đánh dấu
                  các trường dữ liệu cần kiểm tra bằng màu đỏ để dễ dàng bổ
                  sung.
                </p>
              </div>
            </div>
          {/if}

          <div class="space-y-6">
            {#if isAddressFormVisible}
              <div transition:slide>
                <AddressSection
                  bind:form
                  {invalidFields}
                  bind:showNote
                  bind:orderNote={form.note}
                  {lookupCustomer}
                />
              </div>
            {:else}
              <div
                class="bg-white p-6 shadow-sm flex items-center justify-between"
              >
                <div>
                  <h3 class="text-sm font-bold text-gray-800">
                    Thông tin nhận hàng
                  </h3>
                  <p class="text-sm text-gray-600 mt-1">
                    {form.name} · {form.phone}
                  </p>
                  <p class="text-sm text-gray-500 mt-0.5">
                    {form.street}, {form.ward}, {form.province}
                  </p>
                </div>
                <button
                  onclick={() => (isAddressFormVisible = true)}
                  class="text-sm font-bold text-[#ee4d2d]">Chỉnh sửa</button
                >
              </div>
            {/if}

            <DeliveryPaymentSection
              bind:form
              {deliveryEstimate}
              {canExpress}
              {selectedProvinceData}
              bind:showCoInspectionModal
              {shippingFee}
            />
            <VoucherSection
              vouchers={cartStore.vouchers}
              {toggleVoucher}
              onOptimize={optimizeVouchers}
            />
          </div>
        </div>

        <div class="lg:col-span-5">
          <div
            class="bg-white p-6 shadow-sm md:sticky md:top-20 border-t-4 border-[#ee4d2d] space-y-6"
          >
            <CheckoutItems
              bind:customItems
              bind:showCustomItemForm
              bind:newCustomItem
              {addCustomItem}
              {removeCustomItem}
            />
            <OrderSummarySection
              bind:form
              {originalSubtotal}
              {productSavings}
              {shippingFee}
              {totalSavings}
              {helenAdvice}
              {neuralStatus}
              {availablePoints}
              pointsRedeemed={pointsToRedeem}
              {handleSubmit}
            />
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>
