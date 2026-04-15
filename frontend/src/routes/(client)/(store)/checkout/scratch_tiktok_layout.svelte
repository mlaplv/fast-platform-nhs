<div class="bg-[#f5f5f5] min-h-screen text-gray-900 pb-[100px]">
  <!-- Hader -->
  <div class="bg-white px-3 pt-[env(safe-area-inset-top)] pb-2 flex flex-col items-center border-b border-gray-100 z-50 sticky top-0">
    <div class="relative flex items-center justify-center w-full h-[40px]">
       <button class="absolute left-0 p-2" onclick={() => history.back()}>
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
       </button>
       <h1 class="text-base font-bold">Giỏ hàng ({cartStore.items.length})</h1>
       <button class="absolute right-0 p-2 text-sm text-gray-600">Chỉnh sửa</button>
    </div>
    <div class="flex items-center text-xs text-gray-500 max-w-[280px] mt-1" on:click={() => scrollToAddress()}>
       <svg class="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
       <span class="truncate">{form.street ? `${form.street}, ${form.ward}, ${form.province}` : 'Chọn địa chỉ giao hàng...'}</span>
       <svg class="w-3 h-3 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
    </div>
  </div>

  <!-- Freeship banner -->
  <div class="bg-[#eaf8f4] text-[#00604b] text-sm font-semibold px-4 py-2.5 flex items-center gap-2 mb-2">
    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
    Bạn được freeship!
  </div>

  <!-- Gift Banner -->
  <!-- <div class="bg-red-50 text-red-500 text-sm font-semibold px-4 py-2.5 flex items-center justify-between mx-2 rounded-t-xl mt-2 border-b border-red-100">
    <div class="flex items-center gap-2">
      (Gift Icon) Bạn có 2 quà miễn phí
    </div>
    <svg>></svg>
  </div> -->

  <!-- Items Wrapper -->
  <div class="bg-white rounded-b-xl mx-2 shadow-sm mb-3">
     <!-- loop items -->
      <div class="flex items-start gap-3 p-3">
         <!-- Checkbox -->
         <!-- Image -->
         <!-- Details -->
      </div>
  </div>

  <!-- Real payment & address logic (Keep it matching Tiktok style as separate blocks) -->
  <div class="bg-white p-4 mx-2 rounded-xl mb-3 shadow-sm" id="address-section">
     <AddressSection ... />
  </div>
  <div class="bg-white p-4 mx-2 rounded-xl mb-3 shadow-sm">
     <DeliveryPaymentSection ... />
  </div>
  
  <!-- Voucher -->
  <div class="bg-white p-4 mx-2 rounded-xl mb-3 shadow-sm flex justify-between items-center text-sm font-bold text-gray-800">
     <div class="flex items-center text-red-500 gap-2">
       (Voucher Icon) Đã áp dụng giảm {discount}
     </div>
     <svg>></svg>
  </div>

  <!-- Fixed Bottom -->
  <div class="fixed bottom-0 left-0 w-full bg-white border-t border-gray-100 p-2 px-3 flex justify-between items-center z-50">
     <!-- Tất cả checkbox -->
     <!-- Price & Checkout Button -->
  </div>
</div>
