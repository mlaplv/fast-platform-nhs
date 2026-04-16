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
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';

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
    if (clientUi.isDetermined && clientUi.isMobile) {
      clientUi.isHeaderHidden = true;
      clientUi.isFooterHidden = true;
    } else if (clientUi.isDetermined) {
      clientUi.isHeaderHidden = false;
      clientUi.isFooterHidden = false;
    } else {
      clientUi.isHeaderHidden = true;
      clientUi.isFooterHidden = true;
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
  let isAddressFormVisible = $state(true);

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

      if (authStore.isAuthenticated && form.street && form.province) {
         isAddressFormVisible = false;
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

  $effect(() => {
    if (browser) {
      // Đổ danh sách voucher xuống lõi CartStore theo chuẩn kiểu dữ liệu của Svelte state
      cartStore.setVouchers(vouchers.map(v => ({
         id: v.id,
         type: v.type === 'discount' ? 'FIXED' : 'SHIPPING',
         value: v.value,
         min_spend: v.minSpend,
         is_active: true,
         used_count: 0
      } as any)));
    }
  });

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
  {#if !clientUi.isDetermined}
    <TikTokShopLoading variant="grid" />
  {:else if !clientUi.isMobile}
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
                {#if isAddressFormVisible}
                  <div transition:slide>
                    <AddressSection bind:form {invalidFields} bind:showNote bind:orderNote={form.note} {lookupCustomer} />
                  </div>
                {:else}
                  <div class="bg-white p-6 shadow-sm flex items-center justify-between">
                    <div>
                      <h3 class="text-sm font-bold text-gray-800 uppercase">Thông tin nhận hàng</h3>
                      <p class="text-sm text-gray-600 mt-1">{form.name} · {form.phone}</p>
                      <p class="text-sm text-gray-500 mt-0.5">{form.street}, {form.ward}, {form.province}</p>
                    </div>
                    <button onclick={() => isAddressFormVisible = true} class="text-sm font-bold text-[#ee4d2d]">Chỉnh sửa</button>
                  </div>
                {/if}
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
    <!-- TIKTOK SHOP MOBILE CART/CHECKOUT THEME -->
    <div class="bg-[#f5f5f5] min-h-[100dvh] pb-[85px] text-gray-900 font-sans">
      <!-- HEADER -->
      <div class="bg-white pt-[env(safe-area-inset-top)] pb-2 px-3 sticky top-0 z-50 shadow-sm">
        <div class="relative flex items-center justify-center w-full h-[48px]">
          <button type="button" onclick={() => history.back()} class="absolute left-0 p-2 flex items-center justify-center" aria-label="Quay lại">
             <svg class="w-6 h-6 text-gray-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
          </button>
          <div class="flex flex-col items-center">
            <h1 class="text-[17px] font-bold text-gray-900 relative">
               Giỏ hàng ({cartStore.items.length})
            </h1>
          </div>
          {#if authStore.isAuthenticated}
            <button type="button" onclick={() => { isAddressFormVisible = !isAddressFormVisible; if(isAddressFormVisible) setTimeout(() => document.getElementById('address-section')?.scrollIntoView({behavior: 'smooth', block: 'start'}), 100) }} class="absolute right-0 p-2 text-[14px] text-gray-700 font-medium">{isAddressFormVisible ? 'Đóng' : 'Chỉnh sửa'}</button>
          {/if}
        </div>
        
        <!-- Address Summary (Matches Tiktok Top Bar Address) -->
        <div class="flex items-center justify-center mt-0.5 pb-1">
          <button type="button" onclick={() => { if(authStore.isAuthenticated) isAddressFormVisible = true; setTimeout(() => document.getElementById('address-section')?.scrollIntoView({behavior: 'smooth', block: 'start'}), 100) }} class="flex items-center text-[12px] text-gray-500 hover:text-gray-800 transition-colors">
            <svg class="w-3.5 h-3.5 mr-1 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            <span class="truncate max-w-[200px]">{form.street && form.province ? `${form.street}, ${form.ward}, ${form.province}` : 'Chọn địa chỉ nhận hàng...'}</span>
            <svg class="w-3.5 h-3.5 ml-0.5 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
          </button>
        </div>
      </div>

      {#if cartStore.items.length === 0}
        <div class="py-32 text-center space-y-4" in:fade>
          <div class="w-20 h-20 bg-white rounded-full flex items-center justify-center mx-auto shadow-sm">
            <svg class="w-10 h-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
          </div>
          <p class="text-sm text-gray-500 font-medium">Giỏ hàng của bạn trống</p>
          <a href="/" class="inline-block px-10 py-3 bg-[#fe2c55] hover:bg-[#e0264b] transition-colors text-white rounded-md font-semibold text-[15px] shadow-sm">Mua sắm ngay</a>
        </div>
      {:else}
        <div class="px-0">
          <!-- Freeship Banner -->
          {#if cartStore.totalAmountWithoutDiscount > 0}
            <div class="bg-[#eaf8f4] text-[#00a870] text-[13px] font-medium px-4 py-3 flex items-center gap-2 mb-2 mt-2">
              <svg class="w-5 h-5 text-[#00a870]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
              Bạn được freeship!
            </div>
          {/if}

          <!-- Items list -->
          <div class="bg-white rounded-xl shadow-sm mb-3 mt-1 overflow-hidden mx-2">
            <!-- Gift Banner -->
            {#if cartStore.items.some((i) => i.product.discountPrice)}
              <div class="bg-[#fff0f1] text-[#fe2c55] text-[13px] font-medium px-3 py-3 flex items-center justify-between border-b border-[#ffe1e3]">
                <div class="flex items-center gap-1.5">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                  Bạn có quà miễn phí
                </div>
                <svg class="w-4 h-4 text-[#fe2c55]/80" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
              </div>
            {/if}

            {#each cartStore.items as item}
              <div class="p-3 border-b border-gray-50 flex items-start gap-3 last:border-b-0 relative">
                <!-- Checkbox -->
                <button type="button" class="mt-[28px] shrink-0" onclick={() => cartStore.toggleItemSelection(item.id)}>
                   <div class="w-[18px] h-[18px] rounded-full flex items-center justify-center border {item.selected ? 'bg-[#fe2c55] border-[#fe2c55]' : 'border-gray-300'} transition-colors">
                      {#if item.selected}
                        <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                      {/if}
                   </div>
                </button>
                
                <!-- Image -->
                <div class="w-[88px] h-[88px] bg-gray-50 rounded-lg overflow-hidden shrink-0 border border-gray-100">
                  <img src={item.product.image || item.product.images?.[0] || '/uploads/img/micsmo/sp1.png'} alt={item.product.name} class="w-full h-full object-cover" />
                </div>
                
                <!-- Info -->
                <div class="flex-1 min-w-0">
                  <h4 class="text-[14px] text-gray-800 leading-snug line-clamp-2">
                    <span class="text-gray-500 font-normal">[ Hàng Xịn ]</span> {item.product.name}
                  </h4>
                  
                  <div class="mt-1 flex flex-wrap gap-1">
                    {#if item.variant}
                      <button class="flex items-center bg-[#f5f5f5] text-gray-600 text-[11px] px-1.5 py-0.5 rounded gap-1 active:bg-gray-200 transition-colors">
                        <span class="max-w-[100px] truncate">{item.variant.sku}</span>
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                      </button>
                    {/if}
                  </div>

                  <div class="mt-1.5 flex items-center gap-2">
                    <span class="bg-gradient-to-r from-[#ff4760] to-[#fe2c55] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-sm shadow-sm">Flash Sale</span>
                    {#if item.variant?.discountPrice || item.product.discountPrice}
                      <span class="text-[#fe2c55] text-[10px] font-bold flex items-center gap-1">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        04:46:42
                      </span>
                    {/if}
                  </div>

                  <div class="flex items-end justify-between mt-2 max-w-full">
                    <div class="flex flex-col items-start min-w-[70px]">
                      <div class="text-[17px] font-bold text-[#fe2c55] leading-none shrink-0 flex items-center gap-1">
                         {formatCurrency(item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0)}
                      </div>
                      {#if (item.variant?.discountPrice || item.product.discountPrice) && (item.variant?.price || item.product.price)}
                        <div class="flex items-center gap-1 mt-1">
                           <span class="text-[11px] text-gray-400 line-through shrink-0 text-center">{formatCurrency(item.variant?.price ?? item.product.price ?? 0)}</span>
                           <span class="bg-[#fff0f1] text-[#fe2c55] text-[9px] px-1 py-0.5 rounded-sm font-bold shrink-0">-98%</span>
                        </div>
                      {/if}
                    </div>
                    
                    <!-- Qty Control matches TikTok design: border, compact -->
                    <div class="flex items-center border border-gray-200 rounded shrink-0 bg-white">
                       <button type="button" onclick={() => cartStore.updateQuantity(item.id, item.quantity - 1)} class="w-7 h-6 flex items-center justify-center text-gray-500 font-medium active:bg-gray-100 border-r border-gray-200">-</button>
                       <span class="text-[13px] font-medium min-w-[24px] text-center bg-gray-50">{item.quantity}</span>
                       <button type="button" onclick={() => cartStore.updateQuantity(item.id, item.quantity + 1)} class="w-7 h-6 flex items-center justify-center text-gray-500 font-medium active:bg-gray-100 border-l border-gray-200">+</button>
                    </div>
                  </div>
                </div>
              </div>
            {/each}

            <!-- MAPPED CUSTOM ITEMS ON MOBILE -->
            {#if customItems.length > 0}
              <div class="px-3 pb-3 space-y-2 border-t border-gray-100 pt-3">
                <h3 class="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5 text-[#fe2c55]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  Yêu cầu mua thêm
                </h3>
                {#each customItems as item, idx}
                  <div class="flex gap-3 bg-[#fff0f1]/50 p-2 border border-[#ffe1e3] rounded relative group">
                    <div class="w-10 h-10 bg-white border border-[#ffe1e3] shrink-0 flex items-center justify-center overflow-hidden rounded-sm">
                      {#if item.image && item.image.startsWith('http')}
                        <img src={item.image} alt={item.name} class="w-full h-full object-cover" />
                      {:else}
                        <svg class="w-5 h-5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 00-2 2z" /></svg>
                      {/if}
                    </div>
                    <div class="flex-1 min-w-0 flex flex-col justify-center">
                      <h4 class="text-[10px] font-bold text-gray-800 uppercase line-clamp-1">{item.name}</h4>
                      <div class="text-[9px] text-gray-500 font-medium">SL: {item.quantity} · <span class="text-[#fe2c55]">Chờ báo giá</span></div>
                    </div>
                    <button type="button" onclick={() => removeCustomItem(idx)} class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-white border border-gray-200 text-gray-400 hover:text-[#fe2c55] rounded-full flex items-center justify-center shadow-sm">
                      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                  </div>
                {/each}
              </div>
            {/if}

            <!-- ADD CUSTOM ITEM BUTTON/FORM ON MOBILE -->
            <div class="px-3 pb-3 {customItems.length === 0 ? 'pt-3 border-t border-gray-50' : 'pt-0'}">
              {#if !showCustomItemForm}
                <button type="button" onclick={() => showCustomItemForm = true} class="w-full py-3 border-2 border-dashed border-gray-200 text-gray-500 hover:border-[#fe2c55] hover:text-[#fe2c55] hover:bg-[#fff0f1] transition-all flex items-center justify-center gap-2 rounded-lg group">
                  <svg class="w-4 h-4 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" /></svg>
                  <span class="text-[11px] font-bold uppercase tracking-wide">Yêu cầu thêm sản phẩm khác</span>
                </button>
              {:else}
                <div class="p-3 bg-gray-50 border border-gray-100 rounded-lg space-y-3" transition:slide>
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-bold text-gray-800 uppercase flex items-center gap-1.5">
                      <div class="w-1.5 h-1.5 bg-[#fe2c55] rounded-full"></div>
                      Thông tin sản phẩm muốn thêm
                    </span>
                    <button type="button" onclick={() => showCustomItemForm = false} class="text-gray-400 hover:text-gray-900"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg></button>
                  </div>
                  <div class="space-y-2">
                    <input type="text" bind:value={newCustomItem.name} placeholder="VD: Sữa rửa mặt Cerave SA..." class="w-full bg-white border border-gray-200 px-3 py-2 text-[12px] font-medium outline-none focus:border-[#fe2c55] rounded" />
                    <div class="grid grid-cols-2 gap-2">
                       <input type="number" bind:value={newCustomItem.quantity} placeholder="Số lượng" class="w-full bg-white border border-gray-200 px-3 py-2 text-[12px] font-medium outline-none focus:border-[#fe2c55] rounded" />
                       <input type="number" bind:value={newCustomItem.price} placeholder="Giá dự kiến (nếu có)" class="w-full bg-white border border-gray-200 px-3 py-2 text-[12px] font-medium outline-none focus:border-[#fe2c55] rounded" />
                    </div>
                    <input type="text" bind:value={newCustomItem.image} placeholder="Link ảnh hoặc ghi chú..." class="w-full bg-white border border-gray-200 px-3 py-2 text-[12px] font-medium outline-none focus:border-[#fe2c55] rounded" />
                  </div>
                  <button type="button" onclick={addCustomItem} class="w-full py-2.5 bg-gray-900 text-white text-[11px] font-bold uppercase tracking-wider hover:bg-[#fe2c55] transition-colors rounded">
                    Xác nhận thêm
                  </button>
                </div>
              {/if}
            </div>
          </div>

          <!-- Extra Fields (Required for Checkout to function) styled conservatively -->
          {#if isAddressFormVisible}
            <div id="address-section" transition:slide class="mb-3 mt-3 mx-2 scroll-mt-[90px]">
               <AddressSection bind:form {invalidFields} bind:showNote bind:orderNote={form.note} {lookupCustomer} />
            </div>
          {/if}

          <div class="bg-white rounded-xl shadow-sm mb-3 overflow-hidden p-4 mx-2">
             <DeliveryPaymentSection bind:form {deliveryEstimate} {canExpress} {selectedProvinceData} bind:showCoInspectionModal />
          </div>

          <div class="bg-white rounded-xl shadow-sm mb-3 overflow-hidden p-4 mx-2">
             <VoucherSection {vouchers} {toggleVoucher} />
          </div>
        </div>

        <!-- Terms and Conditions -->
        <div class="px-3 pb-2 pt-2 text-[10.5px] leading-snug text-gray-400 text-center">
          Bằng cách đặt đơn hàng, bạn đồng ý với <a href="/terms" class="font-bold text-gray-700 hover:underline">Điều khoản sử dụng và bán hàng của micsmo.com</a> và đồng ý rằng dữ liệu của bạn sẽ được xử lý theo <a href="/privacy" class="font-bold text-gray-700 hover:underline">Chính sách quyền riêng tư của micsmo.com</a>.
        </div>

        {#if errorMsg}
           <div class="fixed top-[60px] left-1/2 -translate-x-1/2 bg-gray-900/90 text-white text-[12px] px-4 py-2 rounded-full shadow-lg z-[60] flex items-center gap-2 whitespace-nowrap" in:slide>
             <svg class="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
             {errorMsg}
           </div>
        {/if}

        <!-- Fixed Bottom Bar -->
        <div class="fixed bottom-0 left-0 w-full bg-white border-t border-gray-100 px-3 py-2 flex items-center justify-between z-[100] pb-[calc(10px+env(safe-area-inset-bottom))]">
           <label class="flex items-center gap-2">
              <button type="button" class="shrink-0" onclick={() => cartStore.toggleAll(cartStore.selectedItemsCount < cartStore.totalItems)}>
                 <div class="w-[18px] h-[18px] rounded-full flex items-center justify-center border {cartStore.selectedItemsCount === cartStore.totalItems && cartStore.totalItems > 0 ? 'bg-[#fe2c55] border-[#fe2c55]' : 'border-gray-300'} transition-colors">
                    {#if cartStore.selectedItemsCount === cartStore.totalItems && cartStore.totalItems > 0}
                      <svg class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                    {/if}
                 </div>
              </button>
              <span class="text-[14px] text-gray-600">Tất cả</span>
           </label>

           <div class="flex items-center gap-3">
              <div class="text-right flex flex-col justify-center">
                {#if cartStore.totalDiscount > 0 || shippingFee === 0}
                  <div class="text-[11px] text-gray-500 leading-tight">
                    {#if shippingFee === 0}Freeship{/if}
                    {#if cartStore.totalDiscount > 0} · Giảm {formatCurrency(cartStore.totalDiscount)}{/if}
                  </div>
                {/if}
                <div class="text-[15px] font-bold text-[#fe2c55] leading-tight flex items-center gap-1 justify-end">
                   {formatCurrency(cartStore.totalAmount + shippingFee)}
                   <svg class="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
                </div>
              </div>
              <button 
                type="button" 
                onclick={(e) => handleSubmit(e as unknown as SubmitEvent)}
                disabled={isSubmitting || cartStore.selectedItemsCount === 0}
                class="px-5 py-3 bg-[#fe2c55] text-white text-[15px] font-semibold rounded-lg min-w-[120px] shadow-sm shadow-[#fe2c55]/30 disabled:opacity-50 disabled:cursor-not-allowed active:bg-[#e0264b] transition-colors flex justify-center items-center"
               >
                {#if isSubmitting}
                  <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                {:else}
                  Thanh toán ({cartStore.selectedItemsCount})
                {/if}
              </button>
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