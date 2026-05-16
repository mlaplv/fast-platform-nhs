<script lang="ts">
  import { slide } from 'svelte/transition';
  import { formatCurrency } from '$lib/utils/format';
  import type { ProvinceData } from '$lib/types/commerce/checkout';

  interface FormState {
    shippingMethod: 'standard' | 'express';
    paymentMethod: 'cod' | 'bank';
    province: string;
  }

  let {
    form = $bindable(),
    deliveryEstimate,
    canExpress,
    selectedProvinceData,
    showCoInspectionModal = $bindable(),
    shippingFee
  } = $props<{
    form: FormState;
    deliveryEstimate: string | null;
    canExpress: boolean;
    selectedProvinceData: ProvinceData | undefined;
    showCoInspectionModal: boolean;
    shippingFee: number;
  }>();

  const standardLabel = $derived.by(() => {
    if (form.shippingMethod !== 'standard') return 'Miễn phí toàn quốc';
    if (shippingFee === 0) return 'Miễn phí toàn quốc';
    return formatCurrency(shippingFee);
  });
</script>

<div class="space-y-4">
  <!-- DELIVERY ESTIMATE FOMO -->
  {#if deliveryEstimate}
    <div class="space-y-2" in:slide>
      <div class="p-3 bg-emerald-50 rounded border border-emerald-100 flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <svg class="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
          <div>
            <div class="text-[10px] font-bold text-emerald-600">Thời gian giao hàng dự kiến</div>
            <div class="text-[12px] font-semibold text-gray-800">Nhận hàng vào: {deliveryEstimate}</div>
          </div>
        </div>
      </div>

      <!-- CO-INSPECTION BADGE -->
      <div class="flex items-center justify-between px-3 py-2 bg-gray-50 rounded border border-gray-100">
        <div class="flex items-center gap-1.5">
          <svg class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <span class="text-[11px] font-bold text-gray-800">Được đồng kiểm</span>
          <button type="button" onclick={() => showCoInspectionModal = true} class="text-gray-400 hover:text-blue-500 transition-colors ml-1">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </button>
        </div>
        <div class="text-[10px] text-gray-500">Cho đơn &lt; 3 triệu</div>
      </div>
    </div>
  {/if}

  <!-- SHIPPING METHOD SELECTION -->
  <div class="pt-2">
    <h2 class="text-sm font-bold text-gray-800 flex items-center gap-2 mb-2 border-b border-gray-50 pb-2">
      <svg class="w-4 h-4 text-[#fe2c55]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 011 1v2a1 1 0 01-1 1h-1m-4-14H5a1 1 0 00-1 1v9a1 1 0 001 1h3m3 3H5a1 1 0 01-1-1v-2a1 1 0 011-1h6" /></svg>
      Phương thức vận chuyển
    </h2>
    <div class="grid grid-cols-2 gap-2.5">
      <button 
        type="button" 
        onclick={() => form.shippingMethod = 'standard'} 
        class="relative flex items-center justify-center gap-2 p-2.5 border rounded-lg transition-all overflow-hidden {form.shippingMethod === 'standard' ? 'border-[#fe2c55] bg-[#fff0f1] text-[#fe2c55]' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'}"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg>
        <div class="text-left leading-tight">
          <span class="block font-bold text-[12px]">Tiêu chuẩn</span>
          <span class="block text-[9px] font-medium {form.shippingMethod === 'standard' ? 'text-[#fe2c55]/80' : 'text-gray-400'}">
            {standardLabel}
          </span>
        </div>
        {#if form.shippingMethod === 'standard'}
          <div class="absolute bottom-0 right-0 w-0 h-0 border-b-[18px] border-l-[18px] border-b-[#fe2c55] border-l-transparent"></div>
          <svg class="w-2.5 h-2.5 text-white absolute bottom-[1px] right-[1px] z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="4"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
        {/if}
      </button>

      <div class="relative group h-full">
        <button 
          type="button" 
          disabled={!canExpress}
          onclick={() => form.shippingMethod = 'express'} 
          class="h-full w-full relative flex items-center justify-center gap-2 p-2.5 border rounded-lg transition-all overflow-hidden {!canExpress ? 'opacity-50 grayscale cursor-not-allowed border-gray-200 bg-gray-50 text-gray-400' : (form.shippingMethod === 'express' ? 'border-[#fe2c55] bg-[#fff0f1] text-[#fe2c55]' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50')}"
        >
          <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          <div class="text-left leading-tight">
            <span class="block font-bold text-[12px]">Hỏa tốc 2h</span>
            <span class="block text-[9px] font-medium {form.shippingMethod === 'express' ? 'text-[#fe2c55]/80' : 'text-gray-400'}">Duy nhất tại HN/HCM</span>
          </div>
          {#if form.shippingMethod === 'express'}
            <div class="absolute bottom-0 right-0 w-0 h-0 border-b-[18px] border-l-[18px] border-b-[#fe2c55] border-l-transparent"></div>
            <svg class="w-2.5 h-2.5 text-white absolute bottom-[1px] right-[1px] z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="4"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
          {/if}
        </button>
        {#if !canExpress && form.province && selectedProvinceData?.has_express}
           <div class="absolute -top-2 right-1 bg-gray-900 text-white text-[8px] px-1 py-0.5 rounded shadow z-20">Ngoại thành - Trừ</div>
        {:else if !canExpress && form.province}
           <div class="absolute -top-2 right-1 bg-gray-900 text-white text-[8px] px-1 py-0.5 rounded shadow z-20">Chưa hỗ trợ</div>
        {/if}
      </div>
    </div>
  </div>

  <!-- PAYMENT METHOD -->
  <div class="pt-2">
    <h2 class="text-sm font-bold text-gray-800 flex items-center gap-2 mb-2 border-b border-gray-50 pb-2">
      <svg class="w-4 h-4 text-[#fe2c55]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
      Phương thức thanh toán
    </h2>
    <div class="grid grid-cols-2 gap-2.5">
      <button 
        type="button" 
        onclick={() => form.paymentMethod = 'cod'} 
        class="relative flex items-center justify-center gap-2 p-2.5 border rounded-lg transition-all overflow-hidden {form.paymentMethod === 'cod' ? 'border-[#fe2c55] bg-[#fff0f1] text-[#fe2c55]' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'}"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
        <div class="text-left leading-tight">
          <span class="block font-bold text-[12px]">Cod</span>
          <span class="block text-[9px] font-medium {form.paymentMethod === 'cod' ? 'text-[#fe2c55]/80' : 'text-gray-400'}">Thanh toán nhận hàng</span>
        </div>
        {#if form.paymentMethod === 'cod'}
          <div class="absolute bottom-0 right-0 w-0 h-0 border-b-[18px] border-l-[18px] border-b-[#fe2c55] border-l-transparent"></div>
          <svg class="w-2.5 h-2.5 text-white absolute bottom-[1px] right-[1px] z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="4"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
        {/if}
      </button>
      <button 
        type="button" 
        onclick={() => form.paymentMethod = 'bank'} 
        class="relative flex items-center justify-center gap-2 p-2.5 border rounded-lg transition-all overflow-hidden {form.paymentMethod === 'bank' ? 'border-[#fe2c55] bg-[#fff0f1] text-[#fe2c55]' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'}"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
        <div class="text-left leading-tight">
          <span class="block font-bold text-[12px]">Banking</span>
          <span class="block text-[9px] font-medium {form.paymentMethod === 'bank' ? 'text-[#fe2c55]/80' : 'text-gray-400'}">Chuyển khoản an toàn</span>
        </div>
        {#if form.paymentMethod === 'bank'}
          <div class="absolute bottom-0 right-0 w-0 h-0 border-b-[18px] border-l-[18px] border-b-[#fe2c55] border-l-transparent"></div>
          <svg class="w-2.5 h-2.5 text-white absolute bottom-[1px] right-[1px] z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="4"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
        {/if}
      </button>
    </div>
  </div>
</div>
