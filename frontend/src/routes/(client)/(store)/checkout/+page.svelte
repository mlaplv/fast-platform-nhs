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
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import Wallet from "@lucide/svelte/icons/wallet";
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  // Satellite Components (Elite V2.2 Composition)
  import AddressSection from './components/AddressSection.svelte';
  import DeliveryPaymentSection from './components/DeliveryPaymentSection.svelte';
  import VoucherSection from './components/VoucherSection.svelte';
  import CheckoutItems from './components/CheckoutItems.svelte';
  import OrderSummarySection from './components/OrderSummarySection.svelte';

  import Countdown from '$lib/components/storefront/ui/Countdown.svelte';
import GiftModal from '$lib/components/storefront/ui/GiftModal.svelte';
import MobileGiftModal from '$lib/components/storefront/ui/MobileGiftModal.svelte';
import NeuralGuardian from '$lib/components/storefront/ui/NeuralGuardian.svelte';
import { checkoutState } from '$lib/state/commerce/checkout.svelte';

  // Types
  import type {
    CustomItem,
    Voucher,
    CheckoutPayload,
    CheckoutResponse,
    CustomerLookupResponse
  } from '$lib/types/commerce/checkout';
  import type { User, UserAddress } from '$lib/state/authStore.svelte';

  const cartStore = getCartStore();
  const clientUi = getClientUi();


  // Immersive layout management: Hide global header/footer on mobile
  $effect.pre(() => {
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

  type NeuralStatus = 'idle' | 'verifying' | 'encoding' | 'submitting' | 'success' | 'error';
  let neuralStatus = $state<NeuralStatus>('idle');
  let isSubmitting = $derived(neuralStatus !== 'idle' && neuralStatus !== 'success' && neuralStatus !== 'error');
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
    pointsRedeemed: 0,
    usePoints: true, // [ELITE V2.2] Auto-Redeem Protocol: Enabled by default
    note: ''
  });

  let showNote = $state(false);
  let customItems = $state<CustomItem[]>([]);
  let showCustomItemForm = $state(false);
  
  // [ELITE V2.2] User Intent Tracking for Vouchers
  // Track if user has manually deselected a category to prevent auto-stick fighting
  let userInteractedVoucherTypes = $state({ SHIPPING: false, DISCOUNT: false });

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

              const addresses: UserAddress[] = user.extra_metadata?.addresses || [];
              const defaultAddr = addresses.find((a: UserAddress) => a.isDefault);

              const isFormEmpty = !form.province || !form.street;

              if (defaultAddr && isFormEmpty) {
                form.name = defaultAddr.name || form.name || user.name || '';
                form.phone = defaultAddr.phone || form.phone || user.phone || '';
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
      
      if (authStore.isAuthenticated) {
        loyaltyStore.fetchLoyalty();
      }
    }
  });

  /**
   * [NEURAL INTELLIGENCE V3.0] Value-First Voucher Resolution
   * Calculates actual VND savings for a given voucher and subtotal.
   */
  function getVoucherSavings(v: Voucher, subtotal: number): number {
    if (subtotal < (v.min_spend || 0)) return -1; // Ineligible
    
    if (v.type === 'SHIPPING') {
      // For shipping vouchers, the saving is either the voucher value or the actual shipping fee
      // (simplified to v.value for sorting purposes)
      return v.value || 0;
    }
    
    if (v.type === 'FIXED') return v.value || 0;
    
    if (v.type === 'PERCENT') {
       const savings = (subtotal * (v.value || 0)) / 100;
       return v.max_discount ? Math.min(savings, v.max_discount) : savings;
    }
    
    return 0;
  }

  // [ELITE V2.2] Auto-Stick Protocol: Synchronize with Neural Best-Deals
  $effect.pre(() => {
    const subtotal = cartStore.totalAmountWithoutDiscount;
    if (cartStore.vouchers.length > 0 && subtotal > 0) {
      
      // 1. Resolve Shipping Channel (Value-Based)
      const hasShippingSelected = cartStore.selectedVoucherIds.some((id: string) => 
        cartStore.vouchers.find((v: Voucher) => v.id === id)?.type === 'SHIPPING'
      );
      
      if (!hasShippingSelected && !userInteractedVoucherTypes.SHIPPING) {
        const bestShip = cartStore.vouchers
          .filter((v: Voucher) => v.type === 'SHIPPING' && subtotal >= (v.min_spend || 0))
          .sort((a, b) => {
             const diff = getVoucherSavings(b, subtotal) - getVoucherSavings(a, subtotal);
             if (diff !== 0) return diff;
             // Tie-breakers: Default flag -> Priority
             if (b.is_default !== a.is_default) return b.is_default ? 1 : -1;
             return (b.priority || 0) - (a.priority || 0);
          })[0];
          
        if (bestShip) {
          cartStore.toggleVoucher(bestShip.id);
        }
      }

      // 2. Resolve Discount Channel (Value-Based)
      const hasDiscountSelected = cartStore.selectedVoucherIds.some((id: string) => 
        ['FIXED', 'PERCENT'].includes(cartStore.vouchers.find((v: Voucher) => v.id === id)?.type || '')
      );

      if (!hasDiscountSelected && !userInteractedVoucherTypes.DISCOUNT) {
        const bestDiscount = cartStore.vouchers
          .filter((v: Voucher) => ['FIXED', 'PERCENT'].includes(v.type) && subtotal >= (v.min_spend || 0))
          .sort((a, b) => {
             const diff = getVoucherSavings(b, subtotal) - getVoucherSavings(a, subtotal);
             if (diff !== 0) return diff;
             // Tie-breakers: Default flag -> Priority
             if (b.is_default !== a.is_default) return b.is_default ? 1 : -1;
             return (b.priority || 0) - (a.priority || 0);
          })[0];
          
        if (bestDiscount) {
          cartStore.toggleVoucher(bestDiscount.id);
        }
      }
    }
  });

  // ELITE V2.2: Dynamic Tier Notification System
  let prevTierMap = new Map<string, string>();
  $effect.pre(() => {
    for (const item of cartStore.items) {
      if (!item.selected) continue;
      const comboVariants = item.product?.variants?.filter(v => v.attributes && v.attributes.combo_qty) || [];
      if (comboVariants.length === 0) continue;

      const sortedTiers = [...comboVariants].sort((a, b) => Number(b.attributes?.combo_qty || 0) - Number(a.attributes?.combo_qty || 0));
      const reachedTier = sortedTiers.find(v => Number(v.attributes?.combo_qty || 0) <= item.quantity);
      const tierId = reachedTier?.id || 'base';

      const lastId = prevTierMap.get(item.id);
      if (lastId && lastId !== tierId && reachedTier) {
        clientUi.showToast(`Chúc mừng! Bạn đã đạt mức giá ưu đãi gói ${reachedTier.attributes?.combo_qty || ''} món cho ${item.product.name}`, 'success');
      }
      prevTierMap.set(item.id, tierId);
    }
  });

  $effect.pre(() => {
    if (browser) {
      localStorage.setItem('elite_checkout_draft', JSON.stringify({
        form: $state.snapshot(form),
        customItems: $state.snapshot(customItems)
      }));
    }
  });

  $effect.pre(() => {
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

  interface Division {
    id: string | number;
    name: string;
    has_express?: boolean;
    express_supported_wards?: string[];
    express_fee?: number;
  }

  const normalize = (s: string) => s.normalize('NFC').toLowerCase().trim();
  const validProvinces = $derived((vnDivisions as unknown as Division[]).filter(p => 'id' in p));
  const selectedProvinceData = $derived(validProvinces.find(p => p.name === form.province));

  const canExpress = $derived.by(() => {
    if (!selectedProvinceData?.has_express || !form.ward) return false;
    const normWard = normalize(form.ward);
    return selectedProvinceData.express_supported_wards?.some((w: string) => normalize(w) === normWard) || false;
  });

  $effect(() => {
    if (canExpress && form.shippingMethod !== 'express') {
      form.shippingMethod = 'express';
    } else if (!canExpress && form.shippingMethod === 'express') {
      form.shippingMethod = 'standard';
    }
  });

  const STANDARD_SHIPPING_FEE = 30000;

  const shippingFee = $derived.by(() => {
    // Determine Base Fee
    let baseFee = STANDARD_SHIPPING_FEE;
    
    if (form.shippingMethod === 'express' && selectedProvinceData?.express_fee) {
       baseFee = selectedProvinceData.express_fee;
    }

    // Elite V2.2: Check if a shipping voucher is applied to zero out the fee
    const hasShippingDiscount = cartStore.selectedVoucherIds.some((id: string) => {
      const v = cartStore.vouchers.find((v: Voucher) => v.id === id);
      return v?.type === 'SHIPPING';
    });
    
    if (hasShippingDiscount) return 0;
    
    // Elite V2.5: Store-wide Free Shipping Threshold (e.g., 2,000,000 VND)
    if (cartStore.totalAmountWithoutDiscount >= 2000000) return 0;

    return baseFee;
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
      .reduce((acc: number, item) => acc + ((item.variant?.price ?? item.product.price ?? 0) * item.quantity), 0);
  });

  const productSavings = $derived(originalSubtotal - cartStore.totalAmountWithoutDiscount);
  const totalSavings = $derived(originalSubtotal - cartStore.totalAmount);
  
  // [ELITE V2.2] Professional Automatic Points Calculation
  const availablePoints = $derived(loyaltyStore.data?.available_points || 0);
  const maxPointsAllowed = $derived(Math.floor((cartStore.totalAmount * 0.01) / 1000));
  const pointsToRedeem = $derived(form.usePoints ? Math.min(availablePoints, maxPointsAllowed) : 0);
  const pointDiscount = $derived(pointsToRedeem * 1000);
  
  const finalTotal = $derived(cartStore.totalAmount + shippingFee - pointDiscount);

  // [ELITE V5.0] Ground Truth Sync: Leverage unified breakdown from CartStore
  $effect(() => {
    const shippingVoucherDiscount = cartStore.vouchers
      .filter(v => cartStore.selectedVoucherIds.includes(v.id) && v.type === 'SHIPPING')
      .reduce((acc, v) => acc + v.value, 0);

    checkoutState.breakdown = {
      ...cartStore.breakdown,
      base_shipping_fee: shippingFee,
      shipping_discount: shippingVoucherDiscount,
      final_shipping_fee: Math.max(0, shippingFee - shippingVoucherDiscount),
      points_redeemed: pointsToRedeem,
      point_discount_amount: pointDiscount,
      final_payable: finalTotal
    };
  });


  // --- HELEN AI PRICE INTELLIGENCE (CHECKOUT CONTEXT) ---
  const helenAdvice = $derived.by(() => {
    const selectedItems = cartStore.items.filter(i => i.selected);
    if (selectedItems.length === 0) return "";

    const advices: { gravity: number; text: string }[] = [];

    for (const item of selectedItems) {
      const comboVariants = item.product?.variants?.filter(v => v.attributes && v.attributes.combo_qty) || [];
      if (comboVariants.length === 0) continue;

      const sortedTiers = [...comboVariants].sort((a, b) => Number(a.attributes?.combo_qty || 0) - Number(b.attributes?.combo_qty || 0));
      const nextTier = sortedTiers.find(t => Number(t.attributes?.combo_qty || 0) > item.quantity);

      if (nextTier) {
        const gap = Number(nextTier.attributes?.combo_qty || 0) - item.quantity;
        const nextUnitPrice = nextTier.discountPrice || nextTier.discount_price || nextTier.price || 0;
        
        // Calculate current effective unit price for this item
        const reachedTier = [...sortedTiers].reverse().find(v => Number(v.attributes?.combo_qty || 0) <= item.quantity);
        const currentUnitPrice = reachedTier?.discountPrice || item.variant?.discountPrice || item.product.discountPrice || item.product.price || 0;
        
        const savingsPerUnit = currentUnitPrice - nextUnitPrice;
        
        if (savingsPerUnit > 0) {
          advices.push({
            gravity: savingsPerUnit * (item.quantity + gap),
            text: `Thêm ${gap} sp ${item.product.name} để giảm thêm ${formatCurrency(savingsPerUnit)}/sp. Tiết kiệm ngay ${formatCurrency(nextUnitPrice)}/món!`
          });
        }
      }
    }

    if (advices.length > 0) {
      return advices.sort((a, b) => b.gravity - a.gravity)[0].text;
    }

    return "Tuyệt vời! Đơn hàng của bạn đã đạt mức giá tối ưu cho tất cả liệu trình. Helen cam kết bảo vệ quyền lợi và chất lượng sản phẩm cho bạn.";
  });

  function toggleVoucher(voucher: Voucher) {
    if (cartStore.totalAmountWithoutDiscount < (voucher.min_spend || 0)) {
      clientUi.showToast(`Cần mua thêm ${formatCurrency((voucher.min_spend || 0) - cartStore.totalAmountWithoutDiscount)}!`, 'info');
      return;
    }
    
    // Record interaction to prevent Auto-Stick protocol from overstepping
    if (voucher.type === 'SHIPPING') userInteractedVoucherTypes.SHIPPING = true;
    else userInteractedVoucherTypes.DISCOUNT = true;
    
    cartStore.toggleVoucher(voucher.id);
  }

  function optimizeVouchers() {
    // 1. Reset user interaction flags to allow Auto-Stick protocol to run
    userInteractedVoucherTypes.SHIPPING = false;
    userInteractedVoucherTypes.DISCOUNT = false;
    
    // 2. Clear current selections to trigger a clean auto-selection
    cartStore.selectedVoucherIds = [];
    
    // 3. Show "Neural" feedback
    clientUi.showToast('Helen đã tối ưu hóa đơn hàng giúp Sếp! ✨', 'success');
  }

  async function lookupCustomer() {
    if (!authStore.isAuthenticated && form.phone.length < 10) return;
    try {
      const res = await apiClient.post<{ data: CustomerLookupResponse }>('/api/v1/client/checkout/lookup', { phone: form.phone });
      if (res.data) {
        const data = res.data;

        if (data.name && !form.name) form.name = data.name;
        // @ts-ignore - legacy field support
        if (data.phone && !form.phone) form.phone = data.phone;

        // @ts-ignore - legacy field support
        if (data.address) {
          // @ts-ignore
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
    } catch (e) { 
      console.error('[Checkout] Customer lookup failed:', e);
    }
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

    neuralStatus = 'verifying';
    errorMsg = '';
    
    try {
      neuralStatus = 'encoding';
      neuralStatus = 'submitting';

      const backendPayload = {
        items: cartStore.items.filter(i => i.selected).map(i => ({
          product_id: i.product.id,
          variant_id: i.variant?.id,
          quantity: i.quantity,
          price: cartStore.getEffectiveItemPrice(i.id)
        })),
        custom_items: customItems.map(i => ({
          name: i.name,
          image_url: i.image,
          price: i.price,
          quantity: i.quantity
        })),
        customer_name: form.name,
        customer_phone: form.phone.replace(/[\s\.\-\+]/g, ''),
        customer_address: `${form.street}, ${form.ward}, ${form.province}`,
        total_amount: cartStore.totalAmount + shippingFee - (pointsToRedeem * 1000),
        shipping_fee: shippingFee,
        payment_method: form.paymentMethod,
        note: form.note || null,
        voucher_ids: cartStore.selectedVoucherIds,
        points_redeemed: pointsToRedeem,
        gift_info: (cartStore.giftInfo?.sender_name && cartStore.giftInfo?.sender_phone) ? cartStore.giftInfo : null
      };

      const res = await apiClient.post<{ id: string, ok: boolean, success?: boolean }>('/api/v1/client/checkout/stealth', backendPayload);
      if (res.ok || res.success) {
        neuralStatus = 'success';
        await clientUi.showToast('Đặt hàng thành công!', 'success');
        window.location.href = `/checkout/success/${res.id}?phone=${form.phone}`;
      }
    } catch (e: unknown) {
      neuralStatus = 'error';
      errorMsg = e instanceof Error ? e.message : 'Lỗi đặt hàng, vui lòng thử lại!';
      clientUi.showToast(errorMsg, 'error');
    }
  }
</script>

<svelte:head>
  <title>Thanh toán bảo mật | osmo</title>
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
            <h1 class="text-xl font-black text-gray-900 italic tracking-widest">Giỏ hàng đang trống</h1>
            <p class="text-xs text-gray-400 font-bold tracking-widest">Bạn chưa chọn sản phẩm nào để thanh toán.</p>
            <a href="/" class="inline-block px-10 py-4 bg-gray-900 text-white font-black text-xs tracking-[0.3em] hover:bg-[#ee4d2d] transition-colors">Quay lại cửa hàng</a>
          </div>
        {:else}
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-7 space-y-6">
              <div class="flex items-center justify-between mb-2">
                <h1 class="text-2xl font-black italic text-gray-900 tracking-tighter">Xác nhận đơn hàng</h1>
                <div class="flex items-center gap-2">
                  <span class="text-[9px] font-bold text-gray-400">Sale kết thúc:</span>
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
                      <h3 class="text-sm font-bold text-gray-800">Thông tin nhận hàng</h3>
                      <p class="text-sm text-gray-600 mt-1">{form.name} · {form.phone}</p>
                      <p class="text-sm text-gray-500 mt-0.5">{form.street}, {form.ward}, {form.province}</p>
                    </div>
                    <button onclick={() => isAddressFormVisible = true} class="text-sm font-bold text-[#ee4d2d]">Chỉnh sửa</button>
                  </div>
                {/if}
                
                <DeliveryPaymentSection bind:form {deliveryEstimate} {canExpress} {selectedProvinceData} bind:showCoInspectionModal />
                <VoucherSection vouchers={cartStore.vouchers} {toggleVoucher} onOptimize={optimizeVouchers} />
              </div>
            </div>

            <div class="lg:col-span-5">
               <div class="bg-white p-6 shadow-sm md:sticky md:top-20 border-t-4 border-[#ee4d2d] space-y-6">
                  <CheckoutItems bind:customItems bind:showCustomItemForm bind:newCustomItem {addCustomItem} {removeCustomItem} />
                  <OrderSummarySection 
                    bind:form 
                    {originalSubtotal} 
                    {productSavings} 
                    {shippingFee} 
                    {totalSavings} 
                    {helenAdvice}
                    {neuralStatus}
                    {availablePoints}
                    pointsRedeemed={pointsToRedeem}
                    {handleSubmit} 
                  />
                  <!-- Points section moved to main column -->
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
      <div 
        class="bg-white pt-[env(safe-area-inset-top)] pb-2 px-3 sticky top-0 shadow-sm"
        style:z-index={Z_INDEX_CLIENT.HEADER}
      >
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
            {#if cartStore.items.some(i => i.product.discountPrice)}
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
                  <img src={item.product.images?.[0] || '/uploads/img/osmo/sp1.png'} alt={item.product.name} class="w-full h-full object-cover" />
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
                         {formatCurrency(cartStore.getEffectiveItemPrice(item.id))}
                         {#if cartStore.getEffectiveItemPrice(item.id) < (item.variant?.discountPrice ?? item.product.discountPrice ?? item.variant?.price ?? item.product.price ?? 0)}
                           <span class="text-[8px] bg-[#fe2c55] text-white px-1 py-0.5 rounded-[2px] font-black italic tracking-tighter shadow-sm animate-pulse-subtle">Combo</span>
                         {/if}
                      </div>
                      <div class="flex items-center gap-1 mt-1">
                         {#if cartStore.getEffectiveItemPrice(item.id) < (item.variant?.discountPrice ?? item.product.discountPrice ?? 0)}
                           <span class="text-[11px] text-gray-400 line-through shrink-0 italic">{formatCurrency(item.variant?.discountPrice ?? item.product.discountPrice ?? 0)}</span>
                         {:else if (item.variant?.discountPrice || item.product.discountPrice) && (item.variant?.price || item.product.price)}
                           <span class="text-[11px] text-gray-400 line-through shrink-0 text-center">{formatCurrency(item.variant?.price ?? item.product.price ?? 0)}</span>
                         {/if}
                         
                         {#if (item.variant?.discountPrice || item.product.discountPrice) && (item.variant?.price || item.product.price)}
                           <span class="bg-[#fff0f1] text-[#fe2c55] text-[9px] px-1 py-0.5 rounded-sm font-bold shrink-0">
                             -{Math.round(100 - (cartStore.getEffectiveItemPrice(item.id) / (item.variant?.price ?? item.product.price ?? 1) * 100))}%
                           </span>
                         {/if}
                      </div>
                    </div>
                    
                    <!-- Qty Control matches TikTok design: border, compact -->
                    <div class="flex items-center border border-gray-200 rounded shrink-0 bg-white">
                       <button type="button" onclick={() => cartStore.updateQuantity(item.id, item.quantity - 1)} class="w-7 h-6 flex items-center justify-center text-gray-500 font-medium active:bg-gray-100 border-r border-gray-200">-</button>
                       <span class="text-[13px] font-medium min-w-[24px] text-center bg-gray-50">{item.quantity}</span>
                       <button type="button" onclick={() => cartStore.updateQuantity(item.id, item.quantity + 1)} class="w-7 h-6 flex items-center justify-center text-gray-500 font-medium active:bg-gray-100 border-l border-gray-200">+</button>
                    </div>
                  </div>

                  <!-- QUÀ TẶNG KÈM THEO MOBILE -->
                  {#if item.variant?.attributes?.gifts && item.variant.attributes.gifts.length > 0}
                    <div class="mt-2.5 bg-[#fef2f2] border border-[#fecdd3] rounded-sm p-1.5 flex flex-col gap-1 w-full relative overflow-hidden">
                      <div class="absolute inset-0 bg-gradient-to-r from-[#ffe4e6]/50 to-transparent pointer-events-none"></div>
                      <span class="text-[10px] font-bold text-[#e11d48] flex items-center gap-1 leading-none relative z-10">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" /></svg>
                        Quà tặng kèm:
                      </span>
                      {#each item.variant.attributes.gifts as gift}
                        <div class="flex items-center justify-between text-[11px] relative z-10 px-1">
                          <span class="text-gray-600 font-medium tracking-tight truncate max-w-[140px]">- {gift.name}</span>
                          <span class="text-[#e11d48] font-bold shrink-0 min-w-[16px] text-center">x{gift.qty * item.quantity}</span>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              </div>
            {/each}

            <!-- MAPPED CUSTOM ITEMS ON MOBILE -->
            {#if customItems.length > 0}
              <div class="px-3 pb-3 space-y-2 border-t border-gray-100 pt-3">
                <h3 class="text-[10px] font-black text-gray-400 tracking-widest flex items-center gap-1.5">
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
                      <h4 class="text-[10px] font-bold text-gray-800 line-clamp-1">{item.name}</h4>
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
                  <span class="text-[11px] font-bold tracking-wide">Yêu cầu thêm sản phẩm khác</span>
                </button>
              {:else}
                <div class="p-3 bg-gray-50 border border-gray-100 rounded-lg space-y-3" transition:slide>
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-bold text-gray-800 flex items-center gap-1.5">
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
                  <button type="button" onclick={addCustomItem} class="w-full py-2.5 bg-gray-900 text-white text-[11px] font-bold tracking-wider hover:bg-[#fe2c55] transition-colors rounded">
                    Xác nhận thêm
                  </button>
                </div>
              {/if}
            </div>
          </div>

          <!-- AGENTIC AI OVERSIGHT (MOBILE - TỔNG HỢP SAU GIỎ HÀNG) -->
          <!-- [ELITE V2.2] Professional Loyalty Toggle Mobile -->
          {#if authStore.isAuthenticated && availablePoints > 0}
            <div class="px-2 mb-3 mt-1" in:slide>
              <div 
                class="bg-white rounded-xl shadow-sm overflow-hidden select-none"
              >
                <!-- Toggle Row -->
                <div 
                  class="p-4 flex items-center justify-between active:bg-gray-50 transition-colors cursor-pointer"
                  onclick={() => form.usePoints = !form.usePoints}
                >
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center {form.usePoints ? 'bg-amber-500/10 text-amber-600' : 'bg-gray-100 text-gray-400'} transition-all">
                      <Wallet class="w-5 h-5" />
                    </div>
                    <div>
                      <span class="text-[13px] font-bold text-gray-800 tracking-widest leading-none">Dùng {availablePoints} điểm tích lũy</span>
                      <p class="text-[11px] text-gray-500 mt-0.5 font-medium italic">Tiết kiệm {formatCurrency(pointsToRedeem * 1000)} cho đơn này</p>
                    </div>
                  </div>
                  
                  <div class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none {form.usePoints ? 'bg-[#fe2c55]' : 'bg-gray-200'}">
                    <span class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 {form.usePoints ? 'translate-x-5' : 'translate-x-0'}"></span>
                  </div>
                </div>

                <!-- Mobile FOMO Tip (Always visible, compact) -->
                <div class="px-4 pb-3 pt-0 border-t border-gray-50">
                  <div class="flex items-start gap-2 bg-amber-50/80 rounded-lg p-2.5 mt-2">
                    <div class="w-4 h-4 shrink-0 mt-0.5">
                      <svg class="w-4 h-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    </div>
                    <div>
                      <p class="text-[10px] text-gray-700 font-bold leading-relaxed">
                        🔥 Đơn này tích thêm <span class="text-[#fe2c55] font-black">+{Math.floor(finalTotal / 100000)} Pts</span>. Mua thêm combo để <span class="bg-[#fe2c55] text-white px-1 rounded-sm text-[9px] font-black">X2 TÍCH LŨY</span>
                      </p>
                      <p class="text-[9px] text-gray-400 font-medium mt-1 italic">Luật: Giảm tối đa 1% đơn hàng · #StayElite</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          {/if}

          <div class="px-2 mb-3 mt-1">
             <NeuralGuardian status={neuralStatus} advice={helenAdvice} />
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
             <VoucherSection vouchers={cartStore.vouchers} {toggleVoucher} onOptimize={optimizeVouchers} />
          </div>
        </div>

        <!-- Terms and Conditions -->
        <div class="px-3 pb-2 pt-2 text-[10.5px] leading-snug text-gray-400 text-center">
          Bằng cách đặt đơn hàng, bạn đồng ý với <a href="/terms" class="font-bold text-gray-700 hover:underline">Điều khoản sử dụng và bán hàng của osmo</a> và đồng ý rằng dữ liệu của bạn sẽ được xử lý theo <a href="/privacy" class="font-bold text-gray-700 hover:underline">Chính sách quyền riêng tư của osmo</a>.
        </div>

        {#if errorMsg}
           <div 
             class="fixed top-[60px] left-1/2 -translate-x-1/2 bg-gray-900/90 text-white text-[12px] px-4 py-2 rounded-full shadow-lg flex items-center gap-2 whitespace-nowrap" 
             style:z-index={Z_INDEX_CLIENT.POPUP}
             in:slide
           >
             <svg class="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
             {errorMsg}
           </div>
        {/if}

        <!-- Fixed Bottom Bar -->
        <div 
          class="fixed bottom-0 left-0 w-full bg-white border-t border-gray-100 px-3 py-2 flex items-center justify-between pb-[calc(10px+env(safe-area-inset-bottom))]"
          style:z-index={Z_INDEX_CLIENT.HEADER}
        >
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
                   {formatCurrency(finalTotal)}
                   <svg class="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
                </div>
              </div>
              <button 
                type="button" 
                onclick={(e) => handleSubmit(e as unknown as SubmitEvent)}
                disabled={isSubmitting || cartStore.selectedItemsCount === 0}
                class="px-5 py-3 bg-[#fe2c55] text-white text-[15px] font-semibold rounded-lg min-w-[140px] shadow-sm shadow-[#fe2c55]/30 disabled:opacity-50 disabled:cursor-not-allowed active:bg-[#e0264b] transition-colors flex justify-center items-center overflow-hidden relative group"
               >
                {#if neuralStatus === 'verifying'}
                  <div class="flex items-center gap-2" in:slide={{axis: 'y'}}>
                    <div class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                    <span class="text-[11px] font-black tracking-widest leading-none">Neural Verifying...</span>
                  </div>
                {:else if neuralStatus === 'encoding'}
                  <div class="flex items-center gap-2" in:slide={{axis: 'y'}}>
                    <div class="flex gap-0.5">
                       <div class="w-1 h-1 bg-white/60 animate-bounce"></div>
                       <div class="w-1 h-1 bg-white/60 animate-bounce" style:animation-delay="0.1s"></div>
                       <div class="w-1 h-1 bg-white/60 animate-bounce" style:animation-delay="0.2s"></div>
                    </div>
                    <span class="text-[11px] font-black tracking-widest leading-none">Stealth Encoding...</span>
                  </div>
                {:else if neuralStatus === 'submitting'}
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
{#if clientUi.isMobile}
  <MobileGiftModal onClose={() => {}} />
{:else}
  <GiftModal onClose={() => {}} />
{/if}