<script lang="ts">
  import { formatCurrency } from "$lib/utils/format";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import type { Voucher } from "$lib/types";
  import { cleanString, isViralVoucher, getVoucherDisplayValue } from "$lib/utils/commerce/voucher";

  let { vouchers, toggleVoucher, onOptimize } = $props<{
    vouchers: Voucher[];
    toggleVoucher: (v: Voucher) => void;
    onOptimize?: () => void;
  }>();

  const cartStore = getCartStore();

  let activeCategory = $state("ALL");
  const categories = [
    {
      id: "ALL",
      label: "Tất cả",
      icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
    },
    {
      id: "SHIPPING",
      label: "Vận chuyển",
      icon: "M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 011 1v2a1 1 0 01-1 1h-1m-4-14H5a1 1 0 00-1 1v9a1 1 0 001 1h3m3 3H5a1 1 0 01-1-1v-2a1 1 0 011-1h6",
    },
    {
      id: "DISCOUNT",
      label: "Giảm giá",
      icon: "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z",
    },
    {
      id: "GIFT",
      label: "Quà tặng",
      icon: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4",
    },
  ];

  const sortedVouchers = $derived.by(() => {
    const subtotal = cartStore.totalAmountWithoutDiscount || 1;

    // Sort by value descending
    const sorted = [...vouchers].sort((a, b) => {
      const valA = getVoucherDisplayValue(a, subtotal, vouchers);
      const valB = getVoucherDisplayValue(b, subtotal, vouchers);
      return valB - valA;
    });

    // Grouping by type (Single Pass O(N) optimization)
    const viralVouchers: any[] = [];
    const regularDiscount: any[] = [];
    const regularShipping: any[] = [];

    for (const v of sorted) {
      if (isViralVoucher(v)) {
        viralVouchers.push(v);
      } else if (v.type === "SHIPPING") {
        regularShipping.push(v);
      } else {
        regularDiscount.push(v);
      }
    }

    return [...viralVouchers, ...regularDiscount, ...regularShipping];
  });

  let filteredVouchers = $derived.by(() => {
    if (activeCategory === "ALL") return sortedVouchers;
    return sortedVouchers.filter((v) => {
      if (activeCategory === "SHIPPING") {
        return v.category === "SHIPPING" || v.type === "SHIPPING";
      }
      if (activeCategory === "DISCOUNT") {
        return (v.category === "DISCOUNT" || v.type !== "SHIPPING") && v.category !== "GIFT";
      }
      return v.category === activeCategory;
    });
  });
</script>

<div class="pt-2 space-y-4">
  <div class="flex items-center justify-between border-b border-gray-50 pb-2">
    <h2 class="text-sm font-bold text-gray-800 flex items-center gap-2">
      <svg
        class="w-4 h-4 text-[#fe2c55]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        ><path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"
        /></svg
      >
      Kho voucher
    </h2>
    <!-- <span class="text-[10px] font-bold text-[#fe2c55] bg-[#fff0f1] px-2 py-0.5 rounded-full">Elite V2.2</span> -->
  </div>

  <!-- Viral TikTok-Style Grid (5 Columns) -->
  <div class="grid grid-cols-5 gap-2 pb-1">
    {#each categories as cat}
      <button
        type="button"
        onclick={() => (activeCategory = cat.id)}
        class="flex flex-col items-center gap-1.5 group transition-all"
      >
        <!-- Icon Container -->
        <div
          class="w-10 h-10 rounded-2xl flex items-center justify-center transition-all border {activeCategory ===
          cat.id
            ? 'bg-gray-900 border-gray-900 text-white shadow-md'
            : 'bg-white border-gray-100 text-gray-500 hover:border-gray-300'}"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              d={cat.icon}
            /></svg
          >
        </div>
        <!-- Subtext -->
        <span
          class="text-[9px] font-black tracking-tighter text-center leading-none {activeCategory ===
          cat.id
            ? 'text-gray-900'
            : 'text-gray-400'}"
        >
          {cat.label === "Tất cả"
            ? "Tất cả"
            : cat.label === "Vận chuyển"
              ? "Ship"
              : cat.label === "Giảm giá"
                ? "Giảm giá"
                : "Quà tặng"}
        </span>
      </button>
    {/each}

    <!-- AI Optimize Button (The 5th Column) -->
    <button
      type="button"
      onclick={onOptimize}
      class="flex flex-col items-center gap-1.5 group transition-all active:scale-95 relative"
    >
      <!-- FOMO Tooltip -->
      <div
        class="absolute -top-8 left-1/2 -translate-x-1/2 bg-[#fe2c55] text-white text-[7px] font-black px-2 py-1 rounded shadow-[0_0_8px_rgba(254,44,85,0.6)] whitespace-nowrap z-20 animate-bounce"
      >
        Tối ưu chọn mã tốt nhất
        <!-- tooltip arrow -->
        <div
          class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[3px] border-l-transparent border-r-[3px] border-r-transparent border-t-[4px] border-t-[#fe2c55]"
        ></div>
      </div>
      <!-- AI Icon Container (Neural Gradient) -->
      <div
        class="w-10 h-10 rounded-2xl flex items-center justify-center bg-gradient-to-br from-[#fe2c55] via-[#ff4760] to-[#ff8a00] text-white shadow-md group-hover:shadow-lg relative overflow-hidden"
      >
        <div
          class="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-700"
        ></div>
        <svg
          class="w-5 h-5 animate-pulse"
          fill="currentColor"
          viewBox="0 0 24 24"
          ><path
            d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
          /></svg
        >
      </div>
      <!-- AI Subtext -->
      <span
        class="text-[9px] font-black tracking-tighter text-[#fe2c55] text-center leading-none"
      >
        AI Tối ưu
      </span>
    </button>
  </div>

  <div class="grid grid-cols-2 md:grid-cols-2 gap-2">
    {#each filteredVouchers as v}
      {@const isSelected = cartStore.selectedVoucherIds.includes(v.id)}
      {@const isEligible = cartStore.isVoucherEligible(v)}
      <button
        type="button"
        onclick={() => toggleVoucher(v)}
        class="relative h-[52px] w-full flex items-center bg-white border {isSelected
          ? 'border-[#fe2c55] ring-1 ring-[#fe2c55]/10 shadow-sm'
          : 'border-gray-200'} {!isEligible
          ? 'opacity-50 grayscale bg-gray-50'
          : 'hover:border-[#fe2c55]/50'} transition-all rounded-md shadow-sm overflow-hidden"
      >
        <!-- Colorful Stub Section -->
        <div
          class="w-10 h-full flex items-center justify-center relative border-r border-dashed border-gray-100 {isSelected
            ? 'bg-gradient-to-b from-[#ff3e63] to-[#fc1b47] text-white'
            : isEligible
              ? 'bg-[#fff0f1] text-[#fe2c55]'
              : 'bg-gray-100 text-gray-400'}"
        >
          <!-- Left side semi-circle cutouts -->
          <div
            class="absolute -left-0.5 flex flex-col justify-between h-[80%] py-1"
          >
            <div class="w-1.5 h-1.5 rounded-full bg-white"></div>
            <div class="w-1.5 h-1.5 rounded-full bg-white"></div>
            <div class="w-1.5 h-1.5 rounded-full bg-white"></div>
          </div>

          {#if v.type === "SHIPPING"}
            <svg
              class="w-4 h-4 z-10"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 011 1v2a1 1 0 01-1 1h-1m-4-14H5a1 1 0 00-1 1v9a1 1 0 001 1h3m3 3H5a1 1 0 01-1-1v-2a1 1 0 011-1h6"
              /></svg
            >
          {:else}
            <svg
              class="w-4 h-4 z-10"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
              /></svg
            >
          {/if}
        </div>

        <!-- Content Section -->
        <div
          class="flex-1 px-2 py-1 text-left min-w-0 flex justify-between items-center h-full relative"
        >
          <div class="flex flex-col justify-center w-full">
            <div class="flex items-center gap-1 mb-0.5">
              {#if isEligible}
                <span
                  class="px-0.5 py-0.25 bg-[#fe2c55] text-white text-[7px] font-black rounded-[1px] leading-tight whitespace-nowrap"
                  >Độc quyền</span
                >
              {/if}
              <div
                class="text-[10px] font-black text-gray-900 leading-tight truncate"
              >
                {v.title || v.id}
              </div>
            </div>
            <div
              class="text-[9px] {isEligible
                ? 'text-[#fe2c55]'
                : 'text-gray-400'} font-bold tracking-tightest leading-tight"
            >
              {v.subtitle ||
                (v.type === "SHIPPING"
                  ? "Miễn phí vận chuyển"
                  : v.type === "PERCENT"
                    ? `Giảm ${v.value}%`
                    : `Giảm ${formatCurrency(v.value)}`)}
              {#if !isEligible || (v.min_spend || v.minSpend)}
                <span class="text-gray-400 font-medium block text-[7px] mt-0.5">
                  Đơn tối thiểu {formatCurrency(v.min_spend || v.minSpend || 0)}
                </span>
              {/if}
            </div>
            {#if isEligible}
              <div class="text-[7px] text-gray-400 font-medium">
                Sắp hết hạn
              </div>
            {/if}
          </div>

          {#if isSelected}
            <div
              class="absolute bottom-0 right-0 w-0 h-0 border-b-[16px] border-l-[16px] border-b-[#fe2c55] border-l-transparent rounded-br-sm"
            ></div>
            <svg
              class="w-2.5 h-2.5 text-white absolute bottom-[0.5px] right-[0.5px] z-10"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="4"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M5 13l4 4L19 7"
              /></svg
            >
          {/if}
        </div>

        <!-- Main divider circle cutouts -->
        <div
          class="w-3 h-3 rounded-full bg-gray-50 absolute right-[-6px] top-1/2 -translate-y-1/2 border-l border-gray-200"
        ></div>
        <div
          class="w-2 h-2 rounded-full bg-white absolute left-[33px] top-[-4px] border-b border-gray-100"
        ></div>
        <div
          class="w-2 h-2 rounded-full bg-white absolute left-[33px] bottom-[-4px] border-t border-gray-100"
        ></div>
      </button>
    {/each}
  </div>
</div>
