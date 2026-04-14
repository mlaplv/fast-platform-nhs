<script lang="ts">
  import { formatCurrency } from '$lib/utils/format';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import type { Voucher } from '$lib/types/commerce/checkout';

  let { vouchers, toggleVoucher } = $props<{
    vouchers: Voucher[];
    toggleVoucher: (v: Voucher) => void;
  }>();

  const cartStore = getCartStore();
</script>

<div class="pt-6 border-t border-gray-100 space-y-4">
  <h2 class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 flex items-center gap-2">
    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" /></svg>
    ƯU ĐÃI ĐÃ CHỌN
  </h2>
  
  <div class="flex flex-wrap gap-3">
    {#each vouchers as v}
      {@const isSelected = cartStore.selectedVoucherIds.includes(v.id)}
      {@const isEligible = cartStore.totalAmountWithoutDiscount >= v.minSpend}
      <button 
        type="button" 
        onclick={() => toggleVoucher(v)}
        class="relative h-[56px] min-w-[200px] flex items-center bg-[#fff4f1] border {isSelected ? 'border-[#ee4d2d] ring-1 ring-[#ee4d2d]/20 shadow-md' : 'border-orange-100 shadow-sm'} {!isEligible ? 'opacity-50 grayscale' : ''} group transition-all rounded-sm overflow-hidden"
      >
        <!-- Perforated Stub Section -->
        <div class="w-8 h-full flex items-center justify-center relative border-r border-dashed border-orange-200">
          <div class="w-4 h-4 rounded-full bg-white absolute -left-2 top-1/2 -translate-y-1/2"></div>
          <div class="w-1.5 h-1.5 rounded-full bg-white absolute -right-[0.75px] -top-[0.2px]"></div>
          <div class="w-1.5 h-1.5 rounded-full bg-white absolute -right-[0.75px] -bottom-[0.2px]"></div>
          {#if v.type === 'shipping'}
            <svg class="w-4 h-4 text-[#ee4d2d]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 011 1v2a1 1 0 01-1 1h-1m-4-14H5a1 1 0 00-1 1v9a1 1 0 001 1h3m3 3H5a1 1 0 01-1-1v-2a1 1 0 011-1h6" /></svg>
          {:else}
            <svg class="w-4 h-4 text-[#ee4d2d]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
          {/if}
        </div>

        <!-- Content Section -->
        <div class="flex-1 px-3 py-1.5 text-left min-w-0 flex flex-col justify-center">
          <div class="text-[10px] font-bold text-[#ee4d2d] leading-tight mb-0.5">{v.title}</div>
          <div class="text-[8px] {isEligible ? 'text-gray-400' : 'text-red-400'} font-bold uppercase tracking-tight">
            {#if isEligible}
              {v.desc}
            {:else}
              Mua thêm {formatCurrency(v.minSpend - cartStore.totalAmountWithoutDiscount)}
            {/if}
          </div>
        </div>

        <!-- Selected Badge -->
        {#if isSelected}
          <div class="absolute top-0 right-0 bg-[#ee4d2d] text-white px-1 py-0.5 rounded-bl-sm">
            <svg class="w-2 h-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="4"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
          </div>
        {/if}
        
        <!-- Right circle cutout -->
        <div class="w-3 h-3 rounded-full bg-white absolute -right-1.5 top-1/2 -translate-y-1/2"></div>
      </button>
    {/each}
  </div>
</div>
