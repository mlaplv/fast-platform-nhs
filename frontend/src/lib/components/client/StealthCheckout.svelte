<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex.ts';
  import { onMount } from 'svelte';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import vnDivisions from '$lib/data/vn_divisions.json';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import GiftModal from '$lib/components/storefront/ui/GiftModal.svelte';
  import SimpleTiptap from '$lib/components/storefront/ui/SimpleTiptap.svelte';
  import StealthProcessingOverlay from './StealthProcessingOverlay.svelte';
  import StealthVariantGrid from './StealthVariantGrid.svelte';
  import "./StealthCheckout.css";

  const shopStore = getShopStore();

  // Native DOM refs
  let nameRef = $state<HTMLInputElement | undefined>();
  let phoneRef = $state<HTMLInputElement | undefined>();
  let addressRef = $state<HTMLTextAreaElement | undefined>();

  let orderNote = $state("");
  let quickCustomName = $state("");
  let showNote = $state(false);
  let submissionStep = $state(0);
  let invalidFields = $state(new Set<string>());
  
  const processingSteps = [
    "Khởi tạo mã hóa 256-bit...",
    "Xác thực ưu đãi Elite...",
    "Đang ghi đơn bảo mật...",
    "Thành công! Đang chuyển hướng..."
  ];

  let validationError = $state<string | null>(null);
  let reservationTime = $state(480);
  let liveViewCount = $state(15);

  const totalPrice    = $derived(shopStore.totalAmount);
  const isSubmitting  = $derived(shopStore.isSubmitting);
  const variants      = $derived(shopStore.product?.variants || []);
  const hasVariants   = $derived(variants.length > 1);

  const appliedPromoCode = $derived.by(() => {
    const idStr = shopStore.product?.id || 'ELITE';
    const num1 = (idStr.charCodeAt(0) * 17) % 99;
    const num2 = (idStr.charCodeAt(idStr.length - 1) * 23) % 99;
    return `VIP-${num1.toString().padStart(2, '0')}${num2.toString().padStart(2, '0')}`;
  });

  const savedAmount = $derived.by((): number => {
    const savings = (shopStore.originalPrice * shopStore.quantity) - shopStore.totalAmount;
    return Math.max(0, savings);
  });

  onMount(() => {
    const timer = setInterval(() => { if (reservationTime > 0) reservationTime--; }, 1000);
    const viewTimer = setInterval(() => {
      const delta = Math.random() < 0.55 ? 1 : -1;
      liveViewCount = Math.max(8, Math.min(32, liveViewCount + delta));
    }, 3000 + Math.random() * 4000);
    return () => { clearInterval(timer); clearInterval(viewTimer); };
  });

  const formatTime = (s: number) => {
    const mm = Math.floor(s / 60).toString().padStart(2, '0');
    const ss = (s % 60).toString().padStart(2, '0');
    return `${mm}:${ss}`;
  };

  function validateInput() {
    const phone   = phoneRef?.value || '';
    const address = addressRef?.value || '';
    const newInvalid = new Set<string>();
    
    if (!phone || phone.length < 10) newInvalid.add('phone');
    if (!address || address.length < 5) newInvalid.add('address');
    invalidFields = newInvalid;

    if (phone && phone.length > 0 && phone.length < 10) validationError = 'Số điện thoại cần đủ 10 chữ số';
    else if (address && address.length > 0 && address.length < 5) validationError = 'Vui lòng nhập địa chỉ chi tiết hơn';
    else if (newInvalid.size > 0) validationError = 'Vui lòng điền đủ thông tin nhận hàng!';
    else validationError = null;
  }

  function handlePhoneInput() {
    const phone = phoneRef?.value || '';
    if (phone.length >= 10) {
      setTimeout(() => { shopStore.lookupCustomer(phone); }, 500);
    }
  }

  $effect(() => {
    const data = shopStore.customerData;
    if (data?.isRecurring) {
      if (data.nameMasked && nameRef) nameRef.value = data.nameMasked;
      if (data.addressMasked && addressRef) addressRef.value = data.addressMasked;
      validateInput();
    }
  });

  async function handleSubmit() {
    validateInput();
    if (invalidFields.size > 0 || validationError) return;

    const phone   = phoneRef?.value || '';
    const address = addressRef?.value || '';
    const name    = nameRef?.value || 'Khách lẻ';

    const submissionPromise = shopStore.submitCheckout({ 
      phone, address, name, note: orderNote,
      gift_info: shopStore.giftInfo || undefined,
      custom_items: shopStore.customItems.length > 0 ? shopStore.customItems : undefined
    });

    for (let i = 0; i < processingSteps.length - 1; i++) {
      submissionStep = i;
      await new Promise(r => setTimeout(r, 600 + Math.random() * 400));
    }

    await submissionPromise;
    submissionStep = processingSteps.length - 1;
    await new Promise(r => setTimeout(r, 800));

    if (shopStore.checkoutResult?.id) {
        window.location.href = `/checkout/success/${shopStore.checkoutResult.id}?phone=${encodeURIComponent(phone)}`;
    }
  }

  const labels = $derived({
    headline: shopStore.product?.metadata.checkout_headline || 'Ưu tiên kích hoạt liệu trình',
    subheadline: shopStore.product?.metadata.checkout_subheadline || 'Chỉ còn 1 bước cuối để dứt điểm...',
    cta_text: shopStore.product?.metadata.checkout_cta_text || 'KÍCH HOẠT & NHẬN ƯU ĐÃI',
    variant_title: shopStore.product?.metadata.checkout_variant_title || 'Dành riêng cho bạn'
  });
</script>

{#if shopStore?.isCheckoutOpen}
  <div class="fixed inset-0 bg-slate-950/85 backdrop-blur-md" style:z-index={Z_INDEX_CLIENT.MODAL_OVERLAY} role="presentation" aria-hidden="true"></div>
  
  <div class="checkout-drawer" style:z-index={Z_INDEX_CLIENT.MODAL}>
    <div class="glow glow-top"></div>
    <div class="glow glow-bottom"></div>

    <button class="btn-close" onclick={() => shopStore.closeCheckout()} aria-label="Đóng">
      <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
    </button>

    <div class="drawer-scroll">
      <header class="mb-6">
        <div class="flex items-end justify-between">
          <div>
            <EditableWrapper path="metadata.checkout_subheadline" label="SỬA MÔ TẢ GIỎ HÀNG">
              <p class="section-eyebrow mb-1">{labels.subheadline}</p>
            </EditableWrapper>
            <EditableWrapper path="metadata.checkout_headline" label="SỬA TIÊU ĐỀ GIỎ HÀNG">
              <h2 class="drawer-title">{labels.headline}</h2>
            </EditableWrapper>
          </div>
          <div class="ssl-badge">
            {#if shopStore?.customerData?.isTrustedDevice}<span class="text-emerald-400 mr-2 uppercase tracking-wide text-[8px] font-black">Bảo mật ưu tiên</span>{/if}
            <span class="ssl-dot"></span><span>Bảo mật tuyệt đối</span>
          </div>
        </div>
      </header>

      <StealthVariantGrid {variants} {liveViewCount} {labels} />

      <div class="row-2col mb-6">
        <div class="info-pill">
          <span class="pill-label">Số lượng</span>
          <div class="qty-ctrl">
            <button onclick={() => shopStore.setQuantity(shopStore.quantity - 1)} class="qty-btn">−</button>
            <span class="qty-val">{shopStore.quantity}</span>
            <button onclick={() => shopStore.setQuantity(shopStore.quantity + 1)} class="qty-btn">+</button>
          </div>
        </div>
        <div class="info-pill highlight-timer">
          <div class="flex flex-col"><span class="pill-label">Ưu đãi giữ chỗ kết thúc</span><span class="text-[8.5px] font-black text-amber-500 mt-0.5 tracking-wider">MÃ: {appliedPromoCode}</span></div>
          <span class="timer-val">{formatTime(reservationTime)}</span>
        </div>
      </div>

      <div class="form-stack mb-6">
        <div class="field-wrap">
          <input type="tel" bind:this={phoneRef} oninput={handlePhoneInput} onblur={validateInput} placeholder=" " class="field-input field-lg {invalidFields.has('phone') ? 'field-error' : ''}" id="sc-phone" />
          <label for="sc-phone" class="field-label">Số điện thoại <span class="text-sky-500">*</span></label>
        </div>

        <div class="field-wrap mt-2">
          <input type="text" bind:this={nameRef} oninput={validateInput} placeholder=" " class="field-input" id="sc-name" />
          <label for="sc-name" class="field-label">Họ tên người nhận (không bắt buộc)</label>
        </div>

        <div class="field-wrap">
          <textarea bind:this={addressRef} onblur={validateInput} rows="2" placeholder=" " class="field-input field-textarea {invalidFields.has('address') ? 'field-error' : ''}" id="sc-address"></textarea>
          <label for="sc-address" class="field-label">Địa chỉ giao hàng <span class="text-sky-500">*</span></label>
        </div>

        <div class="gift-trigger-wrap mt-2">
          <button type="button" onclick={() => shopStore?.toggleGiftModal(true)} class="gift-trigger-btn flex items-center justify-between w-full group">
            <div class="flex items-center gap-3">
              <span class="text-xl group-hover:scale-125 transition-transform">🎁</span>
              <div class="flex flex-col text-left"><span class="text-[10px] font-black tracking-widest text-pink-400 uppercase">Gói quà Elite</span><span class="text-xs font-bold text-white">Thêm quà tặng & lời nhắn</span></div>
            </div>
            {#if shopStore?.giftInfo}<span class="text-emerald-400 text-[9px] font-black uppercase tracking-tighter">ĐÃ LƯU</span>{:else}<span class="text-[9px] font-black text-white/30 uppercase">THỰC HIỆN →</span>{/if}
          </button>
        </div>

        {#if showNote}
          <div class="note-editor-wrap mt-2 animate-in fade-in zoom-in-95">
            <SimpleTiptap bind:content={orderNote} variant="dark" placeholder="Ghi chú thêm..." limit={1000} />
          </div>
        {:else}
          <button type="button" onclick={() => showNote = true} class="text-[10px] font-bold text-slate-500 hover:text-white px-2 mt-2"> + GHI CHÚ / YÊU CẦU ĐẶC BIỆT </button>
        {/if}

        {#if validationError}<div class="error-msg">{validationError}</div>{/if}
      </div>

      <footer class="order-footer">
        <div class="price-row">
          <div class="flex flex-col">
            <span class="section-eyebrow mb-1">Kết quả đầu tư</span>
            <div class="flex items-baseline gap-2">
              <span class="price-main">{totalPrice.toLocaleString()}đ</span>
              {#if (shopStore?.originalPrice || 0) * (shopStore?.quantity || 1) > totalPrice}
                <span class="price-old">{((shopStore?.originalPrice || 0) * (shopStore?.quantity || 1)).toLocaleString()}đ</span>
              {/if}
            </div>
          </div>
          <div class="free-ship"><span class="whitespace-nowrap">MIỄN PHÍ SHIP</span></div>
        </div>

        {#if shopStore?.error}<div class="api-error">{shopStore?.error}</div>{/if}

        <button onclick={handleSubmit} disabled={isSubmitting} class="btn-cta">
          {#if isSubmitting}<span>Hệ thống đang xử lý...</span>
          {:else}
            <div class="btn-cta-inner">
              <EditableWrapper path="metadata.checkout_cta_text" label="SỬA NÚT">
                <span class="btn-cta-label">{labels.cta_text}</span>
              </EditableWrapper>
              <span class="btn-cta-saving">{savedAmount > 0 ? `Tiết kiệm ${savedAmount.toLocaleString()}đ` : 'Miễn phí vận chuyển ngay!'}</span>
            </div>
          {/if}
        </button>
        <p class="text-[9px] text-slate-500 italic text-center mt-2 opacity-60">CAM KẾT ĐÓNG GÓI KÍN ĐÁO & BẢO MẬT</p>
      </footer>
    </div>
  </div>

  <GiftModal />
{/if}

<StealthProcessingOverlay {isSubmitting} {submissionStep} {processingSteps} />
