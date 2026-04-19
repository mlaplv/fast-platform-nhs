<script lang="ts">
  import { formatCurrency } from '$lib/utils/format';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import type { Voucher } from '$lib/types';

  let { vouchers, toggleVoucher } = $props<{
    vouchers: Voucher[];
    toggleVoucher: (v: Voucher) => void;
  }>();

  const cartStore = getCartStore();
</script>

<div class="pt-2 space-y-3">
  <h2 class="text-sm font-bold uppercase text-gray-800 flex items-center gap-2 mb-2 border-b border-gray-50 pb-2">
    <svg class="w-4 h-4 text-[#fe2c55]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" /></svg>
    Voucher & Ưu đãi
  </h2>
  <div class="grid grid-cols-2 md:grid-cols-2 gap-2">
    {#each vouchers as v}
      {@const isSelected = cartStore.selectedVoucherIds.includes(v.id)}
      {@const isEligible = cartStore.totalAmountWithoutDiscount >= (v.min_spend || 0)}
      <button 
        type="button" 
        onclick={() => toggleVoucher(v)}
        class="relative h-[52px] w-full flex items-center bg-white border {isSelected ? 'border-[#fe2c55] ring-1 ring-[#fe2c55]/10 shadow-sm' : 'border-gray-200'} {!isEligible ? 'opacity-50 grayscale bg-gray-50' : 'hover:border-[#fe2c55]/50'} transition-all rounded-md shadow-sm overflow-hidden"
      >
        <!-- Colorful Stub Section -->
        <div class="w-10 h-full flex items-center justify-center relative border-r border-dashed border-gray-100 {isSelected ? 'bg-gradient-to-b from-[#ff3e63] to-[#fc1b47] text-white' : (isEligible ? 'bg-[#fff0f1] text-[#fe2c55]' : 'bg-gray-100 text-gray-400')}">
          <!-- Left side semi-circle cutouts -->
          <div class="absolute -left-0.5 flex flex-col justify-between h-[80%] py-1">
             <div class="w-1.5 h-1.5 rounded-full bg-white"></div>
             <div class="w-1.5 h-1.5 rounded-full bg-white"></div>
             <div class="w-1.5 h-1.5 rounded-full bg-white"></div>
          </div>
          
          {#if v.type === 'SHIPPING'}
            <svg class="w-4 h-4 z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 011 1v2a1 1 0 01-1 1h-1m-4-14H5a1 1 0 00-1 1v9a1 1 0 001 1h3m3 3H5a1 1 0 01-1-1v-2a1 1 0 011-1h6" /></svg>
          {:else}
            <svg class="w-4 h-4 z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
          {/if}
        </div>
 
        <!-- Content Section -->
        <div class="flex-1 px-2 py-1 text-left min-w-0 flex justify-between items-center h-full relative">
          <div class="flex flex-col justify-center w-full">
            <div class="flex items-center gap-1 mb-0.5">
              {#if isEligible}
                 <span class="px-0.5 py-0.25 bg-[#fe2c55] text-white text-[7px] font-black uppercase rounded-[1px] leading-tight whitespace-nowrap">Độc Quyền</span>
              {/if}
              <div class="text-[10px] font-black text-gray-900 leading-tight truncate">{v.title}</div>
            </div>
            <div class="text-[9px] {isEligible ? 'text-[#fe2c55]' : 'text-gray-400'} font-bold tracking-tightest leading-tight">
              {#if isEligible}
                {v.subtitle || 
                  (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : 
                  (v.type === 'PERCENT' ? `Giảm ${v.value}%` : 
                  (v.value > 100 ? `Giảm ${formatCurrency(v.value)}` : `Giảm ${v.value}%`)))}
              {:else}
                HĐ {formatCurrency(v.min_spend || v.minSpend || 0)}
              {/if}
            </div>
            {#if isEligible}
               <div class="text-[7px] text-gray-400 font-medium">Sắp hết hạn</div>
            {/if}
          </div>
          
          {#if isSelected}
            <div class="absolute bottom-0 right-0 w-0 h-0 border-b-[16px] border-l-[16px] border-b-[#fe2c55] border-l-transparent rounded-br-sm"></div>
            <svg class="w-2.5 h-2.5 text-white absolute bottom-[0.5px] right-[0.5px] z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="4"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
          {/if}
        </div>
 
        <!-- Main divider circle cutouts -->
        <div class="w-3 h-3 rounded-full bg-gray-50 absolute right-[-6px] top-1/2 -translate-y-1/2 border-l border-gray-200"></div>
        <div class="w-2 h-2 rounded-full bg-white absolute left-[33px] top-[-4px] border-b border-gray-100"></div>
        <div class="w-2 h-2 rounded-full bg-white absolute left-[33px] bottom-[-4px] border-t border-gray-100"></div>
      </button>
    {/each}
  </div>
</div>
