<script lang="ts">
  import { slide } from 'svelte/transition';
  import { formatCurrency } from '$lib/utils/format';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';

  interface FormState {
    securePackaging: boolean;
  }

  let { 
    form = $bindable(), 
    originalSubtotal, 
    productSavings, 
    shippingFee, 
    totalSavings, 
    isSubmitting,
    handleSubmit 
  } = $props<{
    form: FormState;
    originalSubtotal: number;
    productSavings: number;
    shippingFee: number;
    totalSavings: number;
    isSubmitting: boolean;
    handleSubmit: (e: SubmitEvent) => void;
  }>();

  const cartStore = getCartStore();
</script>

<div class="space-y-3 pt-5 border-t border-gray-100">
  <div class="flex justify-between items-center group">
    <div class="flex items-center gap-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest italic group-hover:text-gray-900 transition-colors">
      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
      <span>Tổng</span>
    </div>
    <div class="flex flex-col items-end">
      {#if productSavings > 0}
        <span class="text-[10px] text-gray-400 line-through font-bold">
          {formatCurrency(originalSubtotal)}
        </span>
      {/if}
      <span class="text-gray-900 italic font-black text-sm">{formatCurrency(cartStore.totalAmount)}</span>
    </div>
  </div>

  <div class="flex justify-between items-center group">
    <div class="flex items-center gap-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest italic group-hover:text-emerald-500 transition-colors">
      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 011 1v2a1 1 0 01-1 1h-1m-4-14H5a1 1 0 00-1 1v9a1 1 0 001 1h3m3 3H5a1 1 0 01-1-1v-2a1 1 0 011-1h6" /></svg>
      <span>Phí vận chuyển</span>
    </div>
    <span class="text-emerald-500 font-black italic text-xs uppercase tracking-tighter">
      {shippingFee > 0 ? formatCurrency(shippingFee) : 'Miễn phí 100%'}
    </span>
  </div>
  
  {#if cartStore.selectedVoucherIds.length > 0}
    <div class="flex justify-between items-center bg-[#ee4d2d]/5 p-3 border-l-4 border-[#ee4d2d] group overflow-hidden relative" in:slide>
      <div class="flex items-center gap-2 text-[10px] font-black text-[#ee4d2d] uppercase italic relative z-10">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" /></svg>
        VOUCHER TIẾT KIỆM
      </div>
      <span class="font-black italic text-sm relative z-10 text-[#ee4d2d]">-{formatCurrency(cartStore.totalDiscount)}</span>
      <div class="absolute inset-0 bg-red-500/5 -translate-x-full group-hover:translate-x-0 transition-transform duration-700"></div>
    </div>
  {/if}

  <div class="pt-6 mt-4 border-t-2 border-dashed border-gray-100 flex flex-col items-end gap-1">
    <div class="flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.3em] text-gray-400 italic">
      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
      TỔNG THANH TOÁN CUỐI CÙNG
    </div>
    <div class="flex flex-col items-end gap-0">
      {#if totalSavings > 0}
        <div class="text-lg font-bold text-gray-300 line-through italic tracking-tightest leading-none mb-1">
          {formatCurrency(originalSubtotal + shippingFee)}
        </div>
      {/if}
      <span class="text-5xl font-black text-[#ee4d2d] italic tracking-tightest drop-shadow-sm">
        {formatCurrency(cartStore.totalAmount + shippingFee)}
      </span>
    </div>

    {#if totalSavings > 0}
      <div class="mt-4 w-full bg-emerald-50 border border-emerald-100 p-3 flex items-center justify-between group overflow-hidden relative" in:slide>
        <div class="flex items-center gap-2 relative z-10">
          <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span class="text-[10px] font-black text-emerald-600 uppercase tracking-widest italic">CHÚC MỪNG! BẠN ĐÃ TIẾT KIỆM ĐƯỢC</span>
        </div>
        <span class="text-lg font-black text-emerald-600 italic relative z-10">
          {formatCurrency(totalSavings)}
        </span>
        <div class="absolute inset-0 bg-white/40 -translate-x-full group-hover:translate-x-0 transition-transform duration-1000"></div>
      </div>
    {/if}
    
    <!-- SECURE PACKAGING (MICSMO THEME) -->
    <div class="w-full mt-6 bg-[#fff4f1] border border-orange-100 p-4 transition-all duration-300">
      <div class="flex items-start gap-3">
        <div class="w-8 h-8 shrink-0 rounded-lg bg-[#ee4d2d] text-white flex items-center justify-center shadow-lg shadow-orange-500/20">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-[10px] font-black text-gray-900 uppercase tracking-widest flex items-center gap-1.5 leading-none">
            Đặc quyền Bảo mật Cao cấp
            <span class="w-1 h-1 bg-orange-300 rounded-full animate-pulse"></span>
          </h3>
          <p class="text-[9px] text-gray-500 mt-1 font-bold leading-tight">Cam kết đóng gói kín đáo & bảo mật quyền riêng tư cá nhân.</p>
          
          <div class="mt-3 grid grid-cols-2 gap-x-2 gap-y-1">
            <div class="flex items-center gap-1.5 text-[8px] font-black text-[#ee4d2d]/80 uppercase italic">
              <svg class="w-2.5 h-2.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
              Bảo mật tên sản phẩm
            </div>
            <a href="/chinh-sach-kiem-hang" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1.5 text-[8px] font-black text-[#ee4d2d]/80 uppercase italic hover:underline">
              <svg class="w-2.5 h-2.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
              Kiểm tra hàng trước nhận
            </a>
            <div class="flex items-center gap-1.5 text-[8px] font-black text-[#ee4d2d]/80 uppercase italic">
              <svg class="w-2.5 h-2.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
              Đóng gói kín đáo 3 lớp
            </div>
            <a href="/chinh-sach-doi-tra-hoan-tien" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1.5 text-[8px] font-black text-[#ee4d2d]/80 uppercase italic hover:underline">
              <svg class="w-2.5 h-2.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
              Đổi trả 7 ngày
            </a>
          </div>
        </div>
        
        <button 
          type="button"
          onclick={() => form.securePackaging = !form.securePackaging}
          class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none {form.securePackaging ? 'bg-[#ee4d2d]' : 'bg-gray-200'}"
        >
          <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 {form.securePackaging ? 'translate-x-4' : 'translate-x-0'}"></span>
        </button>
      </div>
    </div>

    <!-- SUBMIT BUTTON -->
    <button
      type="button"
      onclick={handleSubmit}
      disabled={isSubmitting}
      class="w-full mt-6 py-4.5 bg-[#ee4d2d] text-white font-black text-lg uppercase italic tracking-widest hover:brightness-110 shadow-xl flex items-center justify-center gap-3 group disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {#if isSubmitting}
        <div class="w-5 h-5 border-3 border-white/20 border-t-white rounded-full animate-spin"></div>
      {:else}
        <span>ĐẶT HÀNG NGAY</span>
        <svg class="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
      {/if}
    </button>

    <div class="flex items-center gap-2 text-[8px] text-gray-400 font-bold mt-4 uppercase tracking-tighter italic">
      <span>An toàn</span>
      <span class="w-1 h-1 bg-gray-200 rounded-full"></span>
      <span>Bảo mật 256-bit</span>
      <span class="w-1 h-1 bg-gray-200 rounded-full"></span>
      <span>Đã bao gồm VAT</span>
    </div>
  </div>
</div>

<style>
  .tracking-tightest { letter-spacing: -0.05em; }
</style>
