<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { formatCurrency } from '$lib/utils/format';
  import { apiClient } from '$lib/utils/apiClient';
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';
  import { slide, fade } from 'svelte/transition';
  import vnDivisions from '$lib/data/vn_divisions.json';
  import { Menu } from 'lucide-svelte';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import UserHeaderMobile from '$lib/components/storefront/user/UserHeaderMobile.svelte';

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
    CheckoutResponse,
    CustomerLookupResponse
  } from '$lib/types/commerce/checkout';
  import type { User } from '$lib/state/authStore.svelte.ts';

  const cartStore = getCartStore();
  const clientUi = getClientUi();
  let isMenuOpen = $state(false);

  // Immersive layout management: Hide global header/footer on mobile
  $effect(() => {
    if (clientUi.isMobile) {
      clientUi.isHeaderHidden = true;
      clientUi.isFooterHidden = true;
    } else {
      clientUi.isHeaderHidden = false;
      clientUi.isFooterHidden = false;
    }
    return () => {
      clientUi.isHeaderHidden = false;
      clientUi.isFooterHidden = false;
    };
  });

  let isSubmitting = $state(false);
  let errorMsg = $state('');
  let invalidFields = $state(new Set<string>());
  let showCoInspectionModal = $state(false);

  let form = $state({
    name: authStore.user?.name || '',
    phone: authStore.user?.phone || '',
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

  // [ELITE V3.1] Persistent Data & Auto-fill Logic
  onMount(async () => {
    if (browser) {
      // Step 1: Load Draft from localStorage
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

      // Step 2: Fetch Fresh Profile & Apply Default Address
      if (authStore.isAuthenticated) {
        try {
           const user = await apiClient.get<User>('/api/v1/client/user/profile');

           if (user) {
              authStore.syncUser(user);

              const addresses = user.extra_metadata?.addresses || [];
              const defaultAddr = addresses.find(a => a.isDefault);

              const isFormEmpty = !form.province || !form.street;

              if (defaultAddr && isFormEmpty) {
                console.log('📦 [Elite Checkout] Auto-filling from Default Address:', defaultAddr.name);
                form.name = defaultAddr.name || form.name || user.name;
                form.phone = defaultAddr.phone || form.phone || user.phone;
                form.province = defaultAddr.city || '';
                form.ward = defaultAddr.ward || '';
                form.street = defaultAddr.address || '';
              } else if (!form.name || !form.phone) {
                form.name = form.name || user.name || '';
                form.phone = form.phone || user.phone || '';
              }
           }
        } catch (e) {
           console.error('Failed to fetch fresh profile for checkout', e);
           if (!form.province) lookupCustomer();
        }
      }

      if (cartStore.selectedVoucherIds.length === 0 && !cartStore.selectedVoucherIds.includes('SHIP0')) {
        cartStore.selectedVoucherIds.push('SHIP0');
      }
    }
  });

  $effect(() => {
    if (browser) {
      localStorage.setItem('elite_checkout_draft', JSON.stringify({
        form: $state.snapshot(form),
        customItems: $state.snapshot(customItems)
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
    if (!authStore.isAuthenticated && form.phone.length < 10) return;
    try {
      const res = await apiClient.post<{ data: CustomerLookupResponse }>('/api/v1/client/checkout/lookup', { phone: form.phone });
      if (res.data) {
        const data = res.data;

        if (data.name && !form.name) form.name = data.name;
        if (data.phone && !form.phone) form.phone = data.phone;

        if (data.address) {
          const parts = data.address.split(',').map((s: string) => s.trim());
          if (parts.length >= 3) {
            form.province = parts[parts.length - 1];
            form.ward = parts[parts.length - 2];
            form.street = parts.slice(0, parts.length - 2).join(', ');
          }
        } else if (!form.province && !form.street) {
          Object.assign(form, data);
        }
      }
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
      const backendPayload = {
        items: cartStore.items.filter(i => i.selected).map(i => ({
          product_id: i.product.id,
          variant_id: i.variant?.id,
          quantity: i.quantity,
          price: (i.variant?.discountPrice ?? i.variant?.price ?? i.product.discountPrice ?? i.product.price ?? 0)
        })),
        custom_items: customItems.map(i => ({
          name: i.name,
          image_url: i.image,
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
    } catch (e: unknown) {
      errorMsg = e instanceof Error ? e.message : 'Lỗi đặt hàng, vui lòng thử lại!';
      clientUi.showToast(errorMsg, 'error');
    } finally {
      isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>Thanh toán bảo mật | Micsmo.com</title>
</svelte:head>

{#if browser}
  {#if !clientUi.isMobile}
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
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title="Thanh Toán" bind:isMenuOpen />
    <div class="h-[48px]"></div> <!-- Spacer for fixed header -->

    <div class="pt-6 pb-20 px-4 max-w-md mx-auto">
      {#if cartStore.items.length === 0}
        <div class="py-20 text-center space-y-6" in:fade>
          <div class="w-20 h-20 bg-white rounded-full flex items-center justify-center mx-auto shadow-sm">
            <svg class="w-10 h-10 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
          </div>
          <h1 class="text-lg font-black text-gray-900 uppercase italic tracking-widest">GIỎ HÀNG ĐANG TRỐNG</h1>
          <p class="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Bạn chưa chọn sản phẩm nào để thanh toán.</p>
          <a href="/" class="inline-block px-8 py-3.5 bg-gray-900 text-white font-black uppercase text-[10px] tracking-[0.3em] hover:bg-[#ee4d2d] transition-colors shadow-lg">QUAY LẠI CỬA HÀNG</a>
        </div>
      {:else}
        <div class="space-y-6">
          <div class="flex items-center justify-between px-1">
            <h1 class="text-xl font-black italic text-gray-900 tracking-tighter uppercase">THANH TOÁN</h1>
            <div class="flex items-center gap-1.5 bg-gray-900 text-white px-2 py-1 rounded-sm scale-90">
              <span class="text-[7px] font-black uppercase tracking-tighter">HẾT HẠN:</span>
              <Countdown initialSeconds={1234} />
            </div>
          </div>

          {#if errorMsg}
            <div class="p-3 bg-red-50 border-l-4 border-red-500 text-red-600 text-[10px] font-black uppercase italic flex items-center gap-2" in:slide>
              <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              {errorMsg}
            </div>
          {/if}

          <div class="space-y-6">
            <div class="bg-white shadow-sm overflow-hidden rounded-sm border-t-2 border-gray-900">
              <AddressSection bind:form {invalidFields} bind:showNote bind:orderNote={form.note} {lookupCustomer} />
            </div>

            <div class="bg-white shadow-sm overflow-hidden rounded-sm border-t-2 border-gray-900 p-6">
              <DeliveryPaymentSection bind:form {deliveryEstimate} {canExpress} {selectedProvinceData} bind:showCoInspectionModal />
            </div>

            <div class="bg-white shadow-sm overflow-hidden rounded-sm border-t-2 border-gray-900 p-6">
              <VoucherSection {vouchers} {toggleVoucher} />
            </div>

            <div class="bg-white shadow-sm overflow-hidden rounded-sm border-t-2 border-gray-900">
               <CheckoutItems bind:customItems bind:showCustomItemForm bind:newCustomItem {addCustomItem} {removeCustomItem} />
            </div>

            <div class="bg-white p-6 shadow-sm overflow-hidden rounded-sm border-t-4 border-[#ee4d2d] mb-10">
               <OrderSummarySection bind:form {originalSubtotal} {productSavings} {shippingFee} {totalSavings} {isSubmitting} {handleSubmit} />
            </div>
          </div>
        </div>
      {/if}
    </div>
  {/if}
{/if}
<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
<GiftModal />