<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { formatCurrency } from '$lib/utils/format';
  import { apiClient } from '$lib/utils/apiClient';
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';
  import { slide, fade } from 'svelte/transition';
  import vnDivisions from '$lib/data/vn_divisions.json';

  // Satellite Components (Elite V2.2 Composition)
  import AddressSection from './components/AddressSection.svelte';
  import DeliveryPaymentSection from './components/DeliveryPaymentSection.svelte';
  import VoucherSection from './components/VoucherSection.svelte';
  import CheckoutItems from './components/CheckoutItems.svelte';
  import OrderSummarySection from './components/OrderSummarySection.svelte';
  
  import Countdown from '$lib/components/storefront/ui/Countdown.svelte';
  import GiftModal from '$lib/components/storefront/ui/GiftModal.svelte';

  // Types
  import type { 
    CustomItem, 
    Voucher, 
    CheckoutPayload, 
    CheckoutResponse 
  } from '$lib/types/commerce/checkout';

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  let isSubmitting = $state(false);
  let errorMsg = $state('');
  let invalidFields = $state(new Set<string>());
  let showCoInspectionModal = $state(false);

  let form = $state({
    name: '',
    phone: '',
    province: '',
    ward: '',
    street: '',
    paymentMethod: 'cod' as 'cod' | 'bank',
    shippingMethod: 'standard' as 'standard' | 'express',
    securePackaging: true,
    note: ''
  });

  let showNote = $state(false);
  let customItems = $state<CustomItem[]>([]);
  let showCustomItemForm = $state(false);
  let newCustomItem = $state<CustomItem>({
    id: '',
    name: '',
    image: '',
    price: 0,
    quantity: 1
  });

  // [ELITE V2.2] Persistence Layer
  onMount(() => {
    if (browser) {
      const saved = localStorage.getItem('elite_checkout_draft');
      if (saved) {
        try {
          const draft = JSON.parse(saved);
          Object.assign(form, draft.form);
          customItems = draft.customItems || [];
          if (form.note) showNote = true;
        } catch (e) {
          console.error('Failed to load checkout draft', e);
        }
      }
      
      // Auto-select Free Shipping voucher by default if none selected
      if (cartStore.selectedVoucherIds.length === 0 && !cartStore.selectedVoucherIds.includes('SHIP0')) {
        cartStore.selectedVoucherIds.push('SHIP0');
      }
    }
  });

  $effect(() => {
    if (browser) {
      localStorage.setItem('elite_checkout_draft', JSON.stringify({
        form: { ...form },
        customItems: [...customItems]
      }));
    }
  });

  $effect(() => {
    if (browser && cartStore.items.length === 0) {
      localStorage.removeItem('elite_checkout_draft');
    }
  });

  function addCustomItem() {
    if (!newCustomItem.name) {
      clientUi.showToast('Vui lòng nhập tên sản phẩm!', 'error');
      return;
    }
    customItems.push({ ...newCustomItem, id: crypto.randomUUID() });
    newCustomItem = { id: '', name: '', image: '', price: 0, quantity: 1 };
    showCustomItemForm = false;
    clientUi.showToast('Đã thêm yêu cầu sản phẩm!', 'success');
  }

  function removeCustomItem(idx: number) {
    customItems.splice(idx, 1);
  }

  const normalize = (s: string) => s.normalize('NFC').toLowerCase().trim();
  const validProvinces = $derived(vnDivisions.filter(p => 'id' in p));
  const selectedProvinceData = $derived(validProvinces.find(p => p.name === form.province));

  const canExpress = $derived.by(() => {
    if (!selectedProvinceData?.has_express || !form.ward) return false;
    const normWard = normalize(form.ward);
    return selectedProvinceData.express_supported_wards?.some(w => normalize(w) === normWard) || false;
  });

  $effect(() => {
    if (canExpress && form.shippingMethod !== 'express') {
      form.shippingMethod = 'express';
    } else if (!canExpress && form.shippingMethod === 'express') {
      form.shippingMethod = 'standard';
    }
  });

  const shippingFee = $derived.by(() => {
    if (form.shippingMethod === 'express' && selectedProvinceData?.express_fee) {
      return selectedProvinceData.express_fee;
    }
    return 0;
  });

  const deliveryEstimate = $derived.by(() => {
    if (!form.province) return null;
    if (form.shippingMethod === 'express') return 'Trong 2 giờ tới';

    const now = new Date();
    let minDays = 3, maxDays = 5;

    if (canExpress) { minDays = 1; maxDays = 2; }
    else if (['Thành phố Đà Nẵng', 'Thành phố Hải Phòng', 'Thành phố Cần Thơ'].includes(form.province)) {
      minDays = 2; maxDays = 3;
    }

    const fmt = (d: Date) => `${d.getDate()}/${d.getMonth() + 1}`;
    const minD = new Date(now.getTime() + minDays * 86400000);
    const maxD = new Date(now.getTime() + maxDays * 86400000);
    return `${fmt(minD)} - ${fmt(maxD)}`;
  });

  const originalSubtotal = $derived.by(() => {
    return cartStore.items
      .filter(i => i.selected)
      .reduce((acc, item) => acc + ((item.variant?.price ?? item.product.price ?? 0) * item.quantity), 0);
  });

  const productSavings = $derived(originalSubtotal - cartStore.totalAmount);
  const totalSavings = $derived(productSavings + cartStore.totalDiscount);

  const vouchers: Voucher[] = [
    { id: 'SHIP0', title: 'MIỄN PHÍ VẬN CHUYỂN', desc: 'Miễn phí vận chuyển cho đơn ₫0', type: 'shipping', value: 30000, minSpend: 0 },
    { id: 'SALE30K', title: 'GIẢM GIÁ ₫30.000', desc: 'Đơn hàng từ ₫150.000', type: 'discount', value: 30000, minSpend: 150000 },
    { id: 'SALE60K', title: 'GIẢM GIÁ ₫60.000', desc: 'Đơn hàng từ ₫300.000', type: 'discount', value: 60000, minSpend: 300000 }
  ];

  function toggleVoucher(voucher: Voucher) {
    if (cartStore.totalAmountWithoutDiscount < voucher.minSpend) {
      clientUi.showToast(`Cần mua thêm ${formatCurrency(voucher.minSpend - cartStore.totalAmountWithoutDiscount)}!`, 'info');
      return;
    }
    const idx = cartStore.selectedVoucherIds.indexOf(voucher.id);
    if (idx > -1) cartStore.selectedVoucherIds.splice(idx, 1);
    else {
      const same = vouchers.find(v => v.type === voucher.type && cartStore.selectedVoucherIds.includes(v.id));
      if (same) cartStore.selectedVoucherIds[cartStore.selectedVoucherIds.indexOf(same.id)] = voucher.id;
      else cartStore.selectedVoucherIds.push(voucher.id);
    }
  }

  async function lookupCustomer() {
    if (form.phone.length < 10) return;
    try {
      const res = await apiClient.post('/api/v1/client/checkout/lookup', { phone: form.phone });
      if (res.data) Object.assign(form, res.data);
    } catch (e) { /* Silent fail */ }
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    if (isSubmitting) return;

    const newInvalid = new Set<string>();
    ['name', 'phone', 'province', 'ward', 'street'].forEach(f => { if (!form[f as keyof typeof form]) newInvalid.add(f); });
    invalidFields = newInvalid;

    if (newInvalid.size > 0) {
      errorMsg = 'Vui lòng điền đủ thông tin nhận hàng!';
      return;
    }

    isSubmitting = true;
    errorMsg = '';

    try {
      const payload: CheckoutPayload = {
        name: form.name,
        phone: form.phone,
        province: form.province,
        ward: form.ward,
        street: form.street,
        shipping_method: form.shippingMethod,
        note: form.note || undefined,
        gift_info: cartStore.giftInfo || undefined,
        custom_items: customItems.length > 0 ? customItems : undefined
      };

      // Step 2: Build the complete Stealth Payload
      const backendPayload = {
        items: cartStore.items.filter(i => i.selected).map(i => ({
          product_id: i.product.id,
          variant_id: i.variant?.id,
          quantity: i.quantity,
          price: (i.variant?.discountPrice ?? i.variant?.price ?? i.product.discountPrice ?? i.product.price ?? 0)
        })),
        custom_items: customItems.map(i => ({
          name: i.name,
          image_url: i.image, // Mapping 'image' to 'image_url' for backend compatibility
          price: i.price,
          quantity: i.quantity
        })),
        customer_name: form.name,
        customer_phone: form.phone,
        customer_address: `${form.street}, ${form.ward}, ${form.province}`,
        total_amount: cartStore.totalAmount + shippingFee,
        shipping_fee: shippingFee,
        payment_method: form.paymentMethod,
        note: form.note || null,
        voucher_id: cartStore.selectedVoucherIds[0] || null,
        gift_info: cartStore.giftInfo || null
      };

      const res = await apiClient.post<CheckoutResponse>('/api/v1/client/checkout/stealth', backendPayload);
      if (res.ok || res.success) {
        await clientUi.showToast('Đặt hàng thành công!', 'success');
        window.location.href = `/checkout/success/${res.id}?phone=${form.phone}`;
      }
    } catch (e: any) {
      errorMsg = e.message || 'Lỗi đặt hàng, vui lòng thử lại!';
      clientUi.showToast(errorMsg, 'error');
    } finally {
      isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>Thanh toán bảo mật | Micsmo.com</title>
</svelte:head>

<div class="min-h-screen bg-[#fafafa] pb-20 pt-4 md:pt-10">
  <div class="max-w-[1240px] mx-auto px-4">
    {#if cartStore.items.length === 0}
      <div class="py-20 text-center space-y-6" in:fade>
        <div class="w-24 h-24 bg-white rounded-full flex items-center justify-center mx-auto shadow-sm">
          <svg class="w-12 h-12 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
        </div>
        <h1 class="text-xl font-black text-gray-900 uppercase italic tracking-widest">GIỎ HÀNG ĐANG TRỐNG</h1>
        <p class="text-xs text-gray-400 font-bold uppercase tracking-widest">Bạn chưa chọn sản phẩm nào để thanh toán.</p>
        <a href="/" class="inline-block px-10 py-4 bg-gray-900 text-white font-black uppercase text-xs tracking-[0.3em] hover:bg-[#ee4d2d] transition-colors">QUAY LẠI CỬA HÀNG</a>
      </div>
    {:else}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <!-- LEFT: FORM -->
        <div class="lg:col-span-7 space-y-6">
          <div class="flex items-center justify-between mb-2">
            <h1 class="text-2xl font-black italic text-gray-900 tracking-tighter uppercase">XÁC NHẬN ĐƠN HÀNG</h1>
            <div class="flex items-center gap-2">
              <span class="text-[9px] font-bold text-gray-400">SALE KẾT THÚC:</span>
              <Countdown initialSeconds={1234} />
            </div>
          </div>

          {#if errorMsg}
            <div class="p-4 bg-red-50 border border-red-100 text-red-600 text-xs font-bold flex items-center gap-2" in:slide>
              <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              {errorMsg}
            </div>
          {/if}

          <div class="space-y-6">
            <AddressSection bind:form {invalidFields} bind:showNote bind:orderNote={form.note} {lookupCustomer} />
            <DeliveryPaymentSection bind:form {deliveryEstimate} {canExpress} {selectedProvinceData} bind:showCoInspectionModal />
            <VoucherSection {vouchers} {toggleVoucher} />
          </div>
        </div>

        <!-- RIGHT: SUMMARY -->
        <div class="lg:col-span-5">
           <div class="bg-white p-6 shadow-sm md:sticky md:top-20 border-t-4 border-[#ee4d2d] space-y-6">
              <CheckoutItems bind:customItems bind:showCustomItemForm bind:newCustomItem {addCustomItem} {removeCustomItem} />
              <OrderSummarySection bind:form {originalSubtotal} {productSavings} {shippingFee} {totalSavings} {isSubmitting} {handleSubmit} />
           </div>
        </div>
      </div>
    {/if}
  </div>
</div>

{#if showCoInspectionModal}
  <div class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm" transition:fade>
    <div class="bg-white max-w-sm w-full p-8 shadow-2xl relative" in:slide>
      <button onclick={() => showCoInspectionModal = false} class="absolute top-4 right-4 text-gray-300 hover:text-gray-900 transition-colors"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg></button>
      <div class="text-center space-y-4">
        <div class="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4"><svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg></div>
        <h3 class="text-lg font-black uppercase italic tracking-widest text-gray-900 text-center">CHÍNH SÁCH ĐỒNG KIỂM</h3>
        <p class="text-[11px] font-bold text-gray-500 uppercase leading-relaxed text-center">Micsmo hỗ trợ khách hàng kiểm tra ngoại quan gói hàng và sản phẩm trước khi thanh toán cho đơn hàng dưới 3.000.000 VNĐ. Cam kết minh bạch, an tâm tuyệt đối.</p>
        <button onclick={() => showCoInspectionModal = false} class="w-full py-4 bg-gray-900 text-white font-black text-xs uppercase tracking-[0.3em] hover:bg-[#ee4d2d] transition-colors">ĐÃ HIỂU</button>
      </div>
    </div>
  </div>
{/if}

<GiftModal />
