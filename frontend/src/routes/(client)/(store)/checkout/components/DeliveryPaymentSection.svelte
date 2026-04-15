<script lang="ts">
  import { slide } from 'svelte/transition';
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
    showCoInspectionModal = $bindable()
  } = $props<{
    form: FormState;
    deliveryEstimate: string | null;
    canExpress: boolean;
    selectedProvinceData: ProvinceData | undefined;
    showCoInspectionModal: boolean;
  }>();
</script>

<div class="space-y-6">
  <!-- DELIVERY ESTIMATE FOMO -->
  {#if deliveryEstimate}
    <div class="space-y-3" in:slide>
      <div class="p-4 bg-emerald-50 border-l-4 border-emerald-500 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-white flex items-center justify-center text-emerald-500 shadow-sm animate-bounce">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
          </div>
          <div>
            <div class="text-[10px] font-black uppercase text-emerald-600 tracking-widest">Thời gian giao hàng dự kiến</div>
            <div class="text-sm font-black text-gray-900 italic">Nhận hàng vào: {deliveryEstimate}</div>
          </div>
        </div>
        <div class="hidden md:block text-[9px] font-bold text-emerald-400 uppercase italic">Chắc chắn nhận hàng</div>
      </div>

      <!-- CO-INSPECTION BADGE -->
      <div class="flex items-center justify-between px-4 py-3 bg-gray-50 border border-gray-100">
        <div class="flex items-center gap-2">
          <div class="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
          </div>
          <span class="text-xs font-black text-gray-900 uppercase italic">Được đồng kiểm</span>
          <button type="button" onclick={() => showCoInspectionModal = true} class="text-gray-400 hover:text-blue-500 transition-colors">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </button>
        </div>
        <div class="text-[9px] font-bold text-gray-400 uppercase">Áp dụng cho đơn hàng &lt; 3 triệu</div>
      </div>
    </div>
  {/if}

  <!-- SHIPPING METHOD SELECTION -->
  <div class="pt-6 border-t border-gray-100">
    <h2 class="text-lg font-black uppercase tracking-tighter flex items-center gap-3 mb-5">
      <span class="w-7 h-7 rounded-full bg-[#ee4d2d] text-white flex items-center justify-center text-xs italic">02</span>
      DỊCH VỤ VẬN CHUYỂN
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <button 
        type="button" 
        onclick={() => form.shippingMethod = 'standard'} 
        class="flex items-center justify-between p-4 border-2 transition-all {form.shippingMethod === 'standard' ? 'border-[#ee4d2d] bg-[#fff4f1]' : 'border-gray-100 hover:border-gray-200'}"
      >
        <div class="flex items-center gap-4">
          <div class="w-9 h-9 rounded-full bg-white shadow-sm flex items-center justify-center text-[#ee4d2d]"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 011 1v2a1 1 0 01-1 1h-1m-4-14H5a1 1 0 00-1 1v9a1 1 0 001 1h3m3 3H5a1 1 0 01-1-1v-2a1 1 0 011-1h6" /></svg></div>
          <div class="text-left leading-tight"><span class="block font-black text-xs text-gray-900">TIÊU CHUẨN</span><span class="text-[9px] text-gray-400 uppercase font-bold italic">Miễn phí toàn quốc</span></div>
        </div>
        {#if form.shippingMethod === 'standard'}
          <div class="w-5 h-5 bg-[#ee4d2d] rounded-full flex items-center justify-center shadow-md"><svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" /></svg></div>
        {/if}
      </button>

      <div class="relative group">
        <button 
          type="button" 
          disabled={!canExpress}
          onclick={() => form.shippingMethod = 'express'} 
          class="w-full flex items-center justify-between p-4 border-2 transition-all {!canExpress ? 'opacity-40 grayscale cursor-not-allowed border-gray-100' : (form.shippingMethod === 'express' ? 'border-[#ee4d2d] bg-[#fff4f1]' : 'border-gray-100 hover:border-gray-200')}"
        >
          <div class="flex items-center gap-4">
            <div class="w-9 h-9 rounded-full bg-white shadow-sm flex items-center justify-center text-red-600 {canExpress ? 'animate-pulse' : ''}"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg></div>
            <div class="text-left leading-tight"><span class="block font-black text-xs text-gray-900">HỎA TỐC 2H</span><span class="text-[9px] text-red-500 uppercase font-black italic">Duy nhất tại HN/HCM</span></div>
          </div>
          {#if form.shippingMethod === 'express'}
            <div class="w-5 h-5 bg-[#ee4d2d] rounded-full flex items-center justify-center shadow-md"><svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" /></svg></div>
          {/if}
        </button>
        {#if !canExpress && form.province && selectedProvinceData?.has_express}
           <div class="absolute -top-2 -right-2 bg-gray-900 text-white text-[7px] px-1.5 py-0.5 font-bold rounded uppercase tracking-tighter">NGOẠI THÀNH - CHƯA HỖ TRỢ</div>
        {:else if !canExpress && form.province}
           <div class="absolute -top-2 -right-2 bg-gray-900 text-white text-[7px] px-1.5 py-0.5 font-bold rounded uppercase tracking-tighter">CHƯA HỖ TRỢ VÙNG NÀY</div>
        {/if}
      </div>
    </div>
  </div>

  <!-- PAYMENT METHOD -->
  <div class="pt-6 border-t border-gray-100">
    <h2 class="text-lg font-black uppercase tracking-tighter flex items-center gap-3 mb-5">
      <span class="w-7 h-7 rounded-full bg-[#ee4d2d] text-white flex items-center justify-center text-xs italic">03</span>
      HÌNH THỨC THANH TOÁN
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <button 
        type="button" 
        onclick={() => form.paymentMethod = 'cod'} 
        class="flex items-center justify-between p-4 border-2 transition-all {form.paymentMethod === 'cod' ? 'border-[#ee4d2d] bg-[#fff4f1]' : 'border-gray-100 hover:border-gray-200'}"
      >
        <div class="flex items-center gap-4">
          <div class="w-9 h-9 rounded-full bg-white shadow-sm flex items-center justify-center text-[#ee4d2d]"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg></div>
          <div class="text-left leading-tight"><span class="block font-black text-xs text-gray-900">COD</span><span class="text-[9px] text-gray-400 uppercase font-bold">Thanh toán khi nhận</span></div>
        </div>
        {#if form.paymentMethod === 'cod'}
          <div class="w-5 h-5 bg-[#ee4d2d] rounded-full flex items-center justify-center shadow-md"><svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" /></svg></div>
        {/if}
      </button>
      <button 
        type="button" 
        onclick={() => form.paymentMethod = 'bank'} 
        class="flex items-center justify-between p-4 border-2 transition-all {form.paymentMethod === 'bank' ? 'border-[#ee4d2d] bg-[#fff4f1]' : 'border-gray-100 hover:border-gray-200'}"
      >
        <div class="flex items-center gap-4">
          <div class="w-9 h-9 rounded-full bg-white shadow-sm flex items-center justify-center text-[#ee4d2d]"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg></div>
          <div class="text-left leading-tight"><span class="block font-black text-xs text-gray-900">BANKING</span><span class="text-[9px] text-gray-400 uppercase font-bold">Chuyển khoản an toàn</span></div>
        </div>
        {#if form.paymentMethod === 'bank'}
          <div class="w-5 h-5 bg-[#ee4d2d] rounded-full flex items-center justify-center shadow-md"><svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" /></svg></div>
        {/if}
      </button>
    </div>
  </div>
</div>
