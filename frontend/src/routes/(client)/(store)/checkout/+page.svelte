<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { formatCurrency } from '$lib/utils/format';
  import { apiClient } from '$lib/utils/apiClient';
  import Countdown from '$lib/components/storefront/ui/Countdown.svelte';
  import SearchableCheckoutSelect from '$lib/components/storefront/ui/SearchableCheckoutSelect.svelte';
  import { fade, fly, slide } from 'svelte/transition';
  import { portal } from '$lib/core/actions/portal';
  import vnDivisions from '$lib/data/vn_divisions.json';

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  let isSubmitting = $state(false);
  let errorMsg = $state('');
  let showCoInspectionModal = $state(false);

  // Form State
  let form = $state({
    name: '',
    phone: '',
    province: '',
    ward: '',
    street: '',
    paymentMethod: 'cod' as 'cod' | 'bank',
    shippingMethod: 'standard' as 'standard' | 'express',
    securePackaging: true
  });

  // Derived Address Data
  const validProvinces = $derived(vnDivisions.filter(p => 'id' in p));

  const currentWards = $derived.by(() => {
    if (!form.province) return [];
    const province = validProvinces.find(p => p.name === form.province);
    if (!province) return [];
    
    const wards = [...(province?.wards || [])];
    if (!province.has_express || !province.express_supported_wards?.length) return wards;
    
    const supported = province.express_supported_wards;
    return wards.sort((a, b) => {
      const aSupported = supported.some(w => normalize(w) === normalize(a));
      const bSupported = supported.some(w => normalize(w) === normalize(b));
      if (aSupported && !bSupported) return -1;
      if (!aSupported && bSupported) return 1;
      return 0;
    });
  });

  // Shipping & Delivery Logic
  const selectedProvinceData = $derived(validProvinces.find(p => p.name === form.province));
  
  const normalize = (s: string) => s.normalize('NFC').toLowerCase().trim();

  const canExpress = $derived.by(() => {
    if (!selectedProvinceData?.has_express || !form.ward) return false;
    const normWard = normalize(form.ward);
    return selectedProvinceData.express_supported_wards?.some(w => normalize(w) === normWard) || false;
  });
  
  // Reset or Auto-select shipping method based on eligibility
  $effect(() => {
    if (canExpress && form.shippingMethod !== 'express') {
      form.shippingMethod = 'express';
      clientUi.showToast('Ưu tiên: Chế độ Hỏa tốc 2h đã được kích hoạt!', 'success');
    } else if (!canExpress && form.shippingMethod === 'express') {
      form.shippingMethod = 'standard';
      clientUi.showToast('Vùng này chưa hỗ trợ Hỏa tốc 2h. Đã chuyển về Giao hàng tiêu chuẩn.', 'info');
    }
  });

  const getWardBadge = (wardName: string) => {
    if (!selectedProvinceData?.has_express) return null;
    const normWard = normalize(wardName);
    const isSupported = selectedProvinceData.express_supported_wards?.some(w => normalize(w) === normWard);
    if (!isSupported) return { text: 'Tiêu chuẩn', type: 'default' };
    return { text: 'Hỏa tốc 2h', type: 'success' };
  };

  const shippingFee = $derived.by(() => {
    if (form.shippingMethod === 'express' && selectedProvinceData?.express_fee) {
      return selectedProvinceData.express_fee;
    }
    return 0;
  });

  const deliveryEstimate = $derived.by(() => {
    if (!form.province) return null;
    const now = new Date();
    
    if (form.shippingMethod === 'express') {
      return 'Trong 2 giờ tới';
    }

    let minDays = 3;
    let maxDays = 5;

    if (canExpress) {
      minDays = 1;
      maxDays = 2;
    } else if (['Thành phố Đà Nẵng', 'Thành phố Hải Phòng', 'Thành phố Cần Thơ'].includes(form.province)) {
      minDays = 2;
      maxDays = 3;
    }

    const minDate = new Date(now.getTime() + minDays * 24 * 60 * 60 * 1000);
    const maxDate = new Date(now.getTime() + maxDays * 24 * 60 * 60 * 1000);

    const fmt = (d: Date) => `${d.getDate()}/${d.getMonth() + 1}`;
    return `${fmt(minDate)} - ${fmt(maxDate)}`;
  });

  const isEligibleForCoInspection = $derived(cartStore.totalAmount < 3000000);

  // Elite Savings Arithmetic
  const originalSubtotal = $derived.by(() => {
    return cartStore.items
      .filter(i => i.selected)
      .reduce((acc, item) => {
        const op = item.variant?.price ?? item.product.price ?? 0;
        return acc + (op * item.quantity);
      }, 0);
  });

  const productSavings = $derived(originalSubtotal - cartStore.totalAmount);
  const totalSavings = $derived(productSavings + cartStore.totalDiscount);

  // Auto-lookup for returning customers
  async function lookupCustomer() {
    if (form.phone.length < 10) return;
    try {
      const res = await apiClient.get(`/api/v1/client/checkout/lookup?phone=${form.phone}`);
      if (res.data) {
        form.name = res.data.name || form.name;
        form.province = res.data.province || form.province;
        form.ward = res.data.ward || form.ward;
        form.street = res.data.street || form.street;
      }
    } catch (e) { /* Silent fail */ }
  }

  const vouchers = [
    { id: 'SHIP0', title: 'MIỄN PHÍ VẬN CHUYỂN', desc: 'Đơn tối thiểu ₫0', type: 'shipping', value: 30000, minSpend: 0 },
    { id: 'SALE30K', title: 'GIẢM GIÁ ₫30.000', desc: 'Đơn tối thiểu ₫150.000', type: 'discount', value: 30000, minSpend: 150000 },
    { id: 'SALE60K', title: 'GIẢM GIÁ ₫60.000', desc: 'Đơn tối thiểu ₫300.000', type: 'discount', value: 60000, minSpend: 300000 }
  ];

  // Auto-select Freeship by default
  $effect(() => {
    if (cartStore.selectedVoucherIds.length === 0) {
      const freeship = vouchers.find(v => v.type === 'shipping');
      if (freeship) cartStore.selectedVoucherIds.push(freeship.id);
    }
  });

  function toggleVoucher(voucher: typeof vouchers[0]) {
    // Check eligibility
    if (cartStore.totalAmountWithoutDiscount < voucher.minSpend) {
      clientUi.showToast(`Bạn cần mua thêm ${formatCurrency(voucher.minSpend - cartStore.totalAmountWithoutDiscount)} để dùng mã này!`, 'info');
      return;
    }

    const currentIdx = cartStore.selectedVoucherIds.indexOf(voucher.id);
    
    if (currentIdx > -1) {
      // Unselect
      cartStore.selectedVoucherIds.splice(currentIdx, 1);
    } else {
      // Select & Replace same type
      const sameTypeVoucher = vouchers.find(v => v.type === voucher.type && cartStore.selectedVoucherIds.includes(v.id));
      if (sameTypeVoucher) {
        const sameTypeIdx = cartStore.selectedVoucherIds.indexOf(sameTypeVoucher.id);
        cartStore.selectedVoucherIds[sameTypeIdx] = voucher.id;
      } else {
        cartStore.selectedVoucherIds.push(voucher.id);
      }
    }
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    if (isSubmitting) return;

    if (!form.name || !form.phone || !form.province || !form.ward || !form.street) {
      errorMsg = 'Vui lòng điền đủ thông tin nhận hàng!';
      return;
    }

    isSubmitting = true;
    errorMsg = '';

    try {
      const payload = {
        ...form,
        items: cartStore.items.filter(i => i.selected).map(i => ({
          product_id: i.product.id,
          variant_id: i.variant?.id,
          quantity: i.quantity
        })),
        voucher_id: cartStore.selectedVoucherId,
        shipping_fee: shippingFee
      };

      const res = await apiClient.post('/api/v1/client/checkout/stealth', payload);
      if (res.success) {
        cartStore.clearCart();
        window.location.href = `/checkout/success/${res.data.id}`;
      } else {
        errorMsg = res.message || 'Lỗi xử lý đơn hàng!';
      }
    } catch (e: any) {
      errorMsg = e.message || 'Lỗi hệ thống!';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="min-h-screen bg-[#f5f5f5] text-gray-900 pt-16 pb-12 px-4 md:px-8 font-sans">
  <!-- MODAL ĐỒNG KIỂM -->
  {#if showCoInspectionModal}
    <div class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" in:fade out:fade>
      <div class="bg-white w-full max-w-xl shadow-2xl relative" in:fly={{ y: 20 }}>
        <div class="flex items-center justify-between p-6 border-b border-gray-100">
          <h3 class="text-xl font-black text-gray-900 uppercase italic">Khi nào tôi được đồng kiểm?</h3>
          <button onclick={() => showCoInspectionModal = false} class="text-gray-400 hover:text-gray-900 transition-colors">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        
        <div class="p-8 space-y-6 text-sm text-gray-600 leading-relaxed font-bold">
          <ul class="space-y-4 list-disc pl-5">
            <li>Đơn hàng có giá trị nhỏ hơn <span class="text-red-500">3,000,000 VNĐ</span> (tổng giá trị đơn hàng với giá khuyến mãi nếu có, không bao gồm Voucher, Shopee Xu và phí vận chuyển).</li>
            <li>Đơn hàng <span class="text-gray-900">KHÔNG</span> có sản phẩm thuộc nhóm "không đồng kiểm".</li>
            <li>Đơn hàng <span class="text-gray-900">KHÔNG</span> vận chuyển bởi Viettel Post, VN Post, VN Post Tiết Kiệm, kênh Người Bán tự vận chuyển, kênh Hỏa Tốc - 4 Giờ, kênh Hỏa Tốc - Trong Ngày.</li>
            <li>Người dùng <span class="text-gray-900">KHÔNG</span> có dấu hiệu lạm dụng chương trình hoặc vi phạm chính sách của Micsmo.</li>
          </ul>
          
          <div class="pt-4 border-t border-gray-50 flex justify-between items-center">
             <span class="text-gray-400 italic">Tìm hiểu thêm Thể lệ <button class="text-blue-500 underline">tại đây</button></span>
             <button onclick={() => showCoInspectionModal = false} class="px-8 py-3 bg-gray-900 text-white font-black uppercase text-xs tracking-widest hover:bg-black transition-colors">Đã rõ</button>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <div class="max-w-[1200px] mx-auto">
    {#if cartStore.items.filter(item => item.selected).length === 0}
      <div class="text-center py-16 bg-white shadow-sm border border-gray-100" in:fade>
        <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg class="w-12 h-12 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
        </div>
        <h2 class="text-2xl font-black text-gray-900 mb-2 italic">GIỎ HÀNG TRỐNG</h2>
        <p class="text-gray-400 mb-8">Hãy chọn những siêu phẩm ngay hôm nay!</p>
        <a href="/" class="inline-flex items-center px-8 py-4 bg-[#ee4d2d] text-white font-black uppercase tracking-widest hover:brightness-110 shadow-lg">
          MUA SẮM NGAY
        </a>
      </div>
    {:else}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <!-- LEFT: INFO -->
        <div class="lg:col-span-7 space-y-6">
          
          <!-- Compact Status Bar -->
          <div class="flex items-center justify-between bg-white px-5 py-3 shadow-sm border-l-4 border-[#ee4d2d]">
            <div class="flex items-center gap-2">
              <span class="flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-red-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
              </span>
              <span class="text-[10px] font-black uppercase text-gray-400 tracking-wider">GIAO DỊCH ĐANG ĐƯỢC ƯU TIÊN</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[9px] font-bold text-gray-400">SALE KẾT THÚC:</span>
              <Countdown initialSeconds={1234} />
            </div>
          </div>

          <div class="bg-white p-6 md:p-8 shadow-sm">
            <h2 class="text-lg font-black uppercase tracking-tighter flex items-center gap-3 mb-6">
              <span class="w-7 h-7 rounded-full bg-[#ee4d2d] text-white flex items-center justify-center text-xs italic">01</span>
              THÔNG TIN VẬN CHUYỂN
            </h2>

            {#if errorMsg}
              <div class="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 text-xs font-bold flex items-center gap-2" in:slide>
                <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                {errorMsg}
              </div>
            {/if}

            <form onsubmit={handleSubmit} class="space-y-6">
              <!-- Address Matrix -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div class="space-y-1">
                  <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Họ và Tên</label>
                  <input type="text" bind:value={form.name} placeholder="Nhập họ tên người nhận..." class="w-full bg-gray-50 border border-gray-100 px-4 py-3 text-sm focus:border-[#ee4d2d] outline-none font-bold" />
                </div>
                <div class="space-y-1">
                  <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Số điện thoại</label>
                  <input type="tel" bind:value={form.phone} onblur={lookupCustomer} placeholder="Số điện thoại liên hệ..." class="w-full bg-gray-50 border border-gray-100 px-4 py-3 text-sm focus:border-[#ee4d2d] outline-none font-bold" />
                </div>
                <div class="space-y-1">
                  <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Tỉnh / Thành phố</label>
                  <SearchableCheckoutSelect 
                    bind:value={form.province} 
                    options={validProvinces.map(p => p.name)} 
                    placeholder="Chọn Tỉnh/Thành" 
                    onChange={() => form.ward = ''}
                  />
                </div>
                <div class="space-y-1">
                  <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Phường / Xã</label>
                  <SearchableCheckoutSelect 
                    bind:value={form.ward} 
                    options={currentWards} 
                    placeholder="Chọn Phường/Xã" 
                    disabled={!form.province}
                    getBadge={getWardBadge}
                  />
                </div>
                <div class="md:col-span-2 space-y-1">
                  <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Địa chỉ chi tiết</label>
                  <input type="text" bind:value={form.street} placeholder="Số nhà, tên đường..." class="w-full bg-gray-50 border border-gray-100 px-4 py-3 text-sm focus:border-[#ee4d2d] outline-none font-bold" />
                </div>
              </div>

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
                  <button type="button" onclick={() => form.shippingMethod = 'standard'} class="flex items-center justify-between p-4 border-2 transition-all {form.shippingMethod === 'standard' ? 'border-[#ee4d2d] bg-[#fff4f1]' : 'border-gray-100 hover:border-gray-200'}">
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
                        <div class="w-9 h-9 rounded-full bg-white shadow-sm flex items-center justify-center text-red-600 animate-pulse"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg></div>
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
                  <button type="button" onclick={() => form.paymentMethod = 'cod'} class="flex items-center justify-between p-4 border-2 transition-all {form.paymentMethod === 'cod' ? 'border-[#ee4d2d] bg-[#fff4f1]' : 'border-gray-100 hover:border-gray-200'}">
                    <div class="flex items-center gap-4">
                      <div class="w-9 h-9 rounded-full bg-white shadow-sm flex items-center justify-center text-[#ee4d2d]"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg></div>
                      <div class="text-left leading-tight"><span class="block font-black text-xs text-gray-900">COD</span><span class="text-[9px] text-gray-400 uppercase font-bold">Thanh toán khi nhận</span></div>
                    </div>
                    {#if form.paymentMethod === 'cod'}
                      <div class="w-5 h-5 bg-[#ee4d2d] rounded-full flex items-center justify-center shadow-md"><svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" /></svg></div>
                    {/if}
                  </button>
                  <button type="button" onclick={() => form.paymentMethod = 'bank'} class="flex items-center justify-between p-4 border-2 transition-all {form.paymentMethod === 'bank' ? 'border-[#ee4d2d] bg-[#fff4f1]' : 'border-gray-100 hover:border-gray-200'}">
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

              <!-- Vouchers -->
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
                      class="relative h-[52px] min-w-[160px] flex items-center bg-[#fff4f1] border {isSelected ? 'border-[#ee4d2d] ring-1 ring-[#ee4d2d]/20 shadow-md' : 'border-orange-100 shadow-sm'} {!isEligible ? 'opacity-50 grayscale' : ''} group transition-all rounded-sm overflow-hidden"
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
                      <div class="flex-1 px-3 py-2 text-left min-w-0 flex flex-col justify-center">
                        <div class="text-[10px] font-black text-[#ee4d2d] leading-none mb-1 truncate">{v.title}</div>
                        <div class="text-[8px] {isEligible ? 'text-gray-400' : 'text-red-400'} font-bold uppercase tracking-tight truncate">
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

              <button type="submit" disabled={isSubmitting} class="w-full py-4.5 bg-[#ee4d2d] text-white font-black text-lg uppercase italic tracking-widest hover:brightness-110 shadow-xl flex items-center justify-center gap-3 group">
                {#if isSubmitting}<div class="w-5 h-5 border-3 border-white/20 border-t-white rounded-full animate-spin"></div>{:else}<span>ĐẶT HÀNG NGAY</span><svg class="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>{/if}
              </button>
            </form>
          </div>
        </div>

        <!-- RIGHT: SUMMARY -->
        <div class="lg:col-span-5">
          <div class="bg-white p-6 shadow-sm md:sticky md:top-20 border-t-4 border-[#ee4d2d]">
            <h2 class="text-lg font-black uppercase text-gray-900 mb-6 pb-4 border-b border-gray-100 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <svg class="w-5 h-5 text-[#ee4d2d]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
                <span class="italic">GIỎ HÀNG</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-[10px] bg-gray-50 px-2 py-1 text-gray-400 font-bold uppercase tracking-widest">{cartStore.selectedItemsCount} SẢN PHẨM</span>
                <button 
                  onclick={async () => { 
                    const confirmed = await clientUi.openConfirm({
                      title: 'DỌN DẸP GIỎ HÀNG',
                      message: 'Bạn có chắc chắn muốn xóa giỏ hàng không? Hành động này không thể hoàn tác.',
                      confirmLabel: 'XÓA GIỎ HÀNG',
                      cancelLabel: 'ĐỂ LẠI'
                    });
                    if (confirmed) cartStore.clearCart(); 
                  }} 
                  class="p-1.5 hover:bg-red-50 text-gray-300 hover:text-red-500 transition-colors group/clear"
                  title="Xóa tận gốc giỏ hàng"
                >
                  <svg class="w-3.5 h-3.5 group-hover/clear:rotate-12 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>
            </h2>

            <!-- Items -->
            <div class="space-y-4 max-h-[350px] overflow-y-auto pr-2 custom-scrollbar mb-6">
              {#each cartStore.items.filter(i => i.selected) as item}
                <div class="flex gap-4 group bg-gray-50/50 p-2 border border-transparent hover:border-gray-100 transition-all">
                  <div class="w-16 h-16 bg-white border border-gray-100 overflow-hidden shrink-0 relative">
                    <img 
                      src={item.product.image || item.product.images?.[0] || '/uploads/img/micsmo/sp1.png'} 
                      alt={item.product.name} 
                      class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" 
                    />
                    <div class="absolute bottom-0 right-0 bg-gray-900/80 text-white text-[8px] px-1 font-black">x{item.quantity}</div>
                  </div>
                  <div class="flex-1 min-w-0 flex flex-col justify-between py-0.5">
                    <div class="space-y-0.5">
                      <h4 class="text-[10px] font-bold text-gray-800 leading-tight uppercase italic line-clamp-2 antialiased">{item.product.name}</h4>
                      {#if item.variant}
                        <div class="flex items-center gap-1.5 mt-1">
                          <span class="text-[7px] font-black text-white bg-gray-400 px-1.5 py-0.5 uppercase tracking-tighter">PHÂN LOẠI</span>
                          <span class="text-[8px] font-bold text-gray-500 uppercase">{item.variant.sku}</span>
                        </div>
                      {/if}
                    </div>
                    <div class="flex items-center justify-between mt-1">
                      <div class="flex items-center gap-1">
                         <button onclick={() => cartStore.updateQuantity(item.id, item.quantity - 1)} class="w-5 h-5 flex items-center justify-center bg-white border border-gray-100 text-gray-400 hover:text-[#ee4d2d] text-[10px] font-black">-</button>
                         <span class="text-[10px] font-black w-4 text-center">{item.quantity}</span>
                         <button onclick={() => cartStore.updateQuantity(item.id, item.quantity + 1)} class="w-5 h-5 flex items-center justify-center bg-white border border-gray-100 text-gray-400 hover:text-[#ee4d2d] text-[10px] font-black">+</button>
                      </div>
                      <div class="flex flex-col items-end gap-0">
                        {#if (item.variant?.discountPrice || item.product.discountPrice) && (item.variant?.price || item.product.price)}
                          <span class="text-[9px] text-gray-400 line-through font-bold">
                            {formatCurrency((item.variant?.price ?? item.product.price ?? 0) * item.quantity)}
                          </span>
                        {/if}
                        <span class="text-sm font-black text-[#ee4d2d] italic tracking-tightest antialiased">
                          {formatCurrency((item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0) * item.quantity)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
            </div>

            <!-- Summary -->
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
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 011 1v2a1 1 0 01-1 1h-1m-4-14H5a1 1 0 00-1 1v9a1 0 001 1h3m3 3H5a1 1 0 01-1-1v-2a1 1 0 011-1h6" /></svg>
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
                  <span class="font-black italic text-sm relative z-10">-{formatCurrency(cartStore.totalDiscount)}</span>
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
                      
                      <div class="mt-3 space-y-1">
                        <div class="flex items-center gap-1.5 text-[8px] font-black text-[#ee4d2d]/80 uppercase italic">
                          <svg class="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
                          Bảo mật tên sản phẩm
                        </div>
                        <div class="flex items-center gap-1.5 text-[8px] font-black text-[#ee4d2d]/80 uppercase italic">
                          <svg class="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
                          Đóng gói kín đáo 3 lớp
                        </div>
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

                <div class="flex items-center gap-2 text-[8px] text-gray-400 font-bold mt-4 uppercase tracking-tighter italic">
                  <span>An toàn</span>
                  <span class="w-1 h-1 bg-gray-200 rounded-full"></span>
                  <span>Bảo mật 256-bit</span>
                  <span class="w-1 h-1 bg-gray-200 rounded-full"></span>
                  <span>Đã bao gồm VAT</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 3px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: #eee; border-radius: 10px; }
  .tracking-tightest { letter-spacing: -0.05em; }
  
  :global(body) {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
  }
</style>
