<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex.ts';
  import { onMount } from 'svelte';
  import "./StealthCheckout.css";

  const shopStore = getShopStore();

  // Native DOM refs — bypass reactive overhead
  let nameRef: HTMLInputElement | undefined;
  let phoneRef: HTMLInputElement | undefined;
  let addressRef: HTMLTextAreaElement | undefined;

  let validationError = $state<string | null>(null);
  let reservationTime = $state(480); // Elite: Slightly shorter for more urgency

  // ELITE FOMO: Live Social Proof (fluctuates ±1 every 3-7s for realism)
  const _baseViewing = Math.floor(((shopStore.product?.id?.length || 10) * 7) % 15) + 12;
  let liveViewCount = $state(_baseViewing);

  // ELITE FOMO: Authentic Promo Code generated from product footprint
  const appliedPromoCode = $derived.by(() => {
    const idStr = shopStore.product?.id || 'ELITE';
    const num1 = (idStr.charCodeAt(0) * 17) % 99;
    const num2 = (idStr.charCodeAt(idStr.length - 1) * 23) % 99;
    return `VIP-${num1.toString().padStart(2, '0')}${num2.toString().padStart(2, '0')}`;
  });

  const totalPrice    = $derived(shopStore.totalAmount);
  const isSubmitting  = $derived(shopStore.isSubmitting);
  const variants      = $derived(shopStore.product?.variants || []);
  const hasVariants   = $derived(variants.length > 1);

  // FOMO: Total savings vs. full original price (no double-counting)
  // Formula: savings = originalPrice × quantity - totalAmount
  // This already accounts for: variant discount + bundle deal + free gift(s)
  const savedAmount = $derived.by((): number => {
    const savings = (shopStore.originalPrice * shopStore.quantity) - shopStore.totalAmount;
    return Math.max(0, savings);
  });

  onMount(() => {
    const timer = setInterval(() => {
      if (reservationTime > 0) reservationTime--;
    }, 1000);

    // Live viewer fluctuation: ±1 every 3-7s, stays in realistic range
    const viewTimer = setInterval(() => {
      const delta = Math.random() < 0.55 ? 1 : -1; // Slight bias upward for FOMO
      const next = liveViewCount + delta;
      liveViewCount = Math.max(8, Math.min(32, next)); // Clamp 8-32
    }, 3000 + Math.random() * 4000);

    return () => {
      clearInterval(timer);
      clearInterval(viewTimer);
    };
  });

  const formatTime = (s: number) => {
    const mm = Math.floor(s / 60).toString().padStart(2, '0');
    const ss = (s % 60).toString().padStart(2, '0');
    return `${mm}:${ss}`;
  };

  function validateInput() {
    const phone   = phoneRef?.value || '';
    const address = addressRef?.value || '';
    if (phone && phone.length > 0 && phone.length < 10) {
      validationError = 'Số điện thoại cần đủ 10 chữ số';
    } else if (address && address.length > 0 && address.length < 5) {
      validationError = 'Vui lòng nhập địa chỉ chi tiết hơn';
    } else {
      validationError = null;
    }
  }

  interface CheckoutVariant {
    id: string;
    sku?: string;
    price?: number;
    discountPrice?: number;
    tierIndex?: number[];
  }

  function getVariantName(v: CheckoutVariant) {
    if (!shopStore.product?.tierVariations || !v.tierIndex) return v.sku || 'Sản phẩm';
    return v.tierIndex
      .map((idx: number, tierIdx: number) => shopStore.product!.tierVariations[tierIdx]?.options[idx] || '')
      .filter((val: string) => Boolean(val))
      .join(' – ');
  }

  function getVariantImage(v: CheckoutVariant) {
    if (!shopStore.product?.tierVariations || !v.tierIndex) return shopStore.product?.images?.[0] || '';
    for (let i = 0; i < v.tierIndex.length; i++) {
      const img = shopStore.product!.tierVariations[i]?.images[v.tierIndex[i]];
      if (img) return img;
    }
    return shopStore.product?.images?.[0] || '';
  }

  // Smart Lookup Logic (Elite V2.2)
  let lookupTimer: ReturnType<typeof setTimeout> | undefined;
  function handlePhoneInput() {
    const phone = phoneRef?.value || '';
    if (phone.length >= 10) {
      if (lookupTimer) clearTimeout(lookupTimer);
      lookupTimer = setTimeout(() => {
        shopStore.lookupCustomer(phone);
      }, 500);
    }
  }

  function handleNameInput() {
    validateInput();
  }

  // Elite Identity Shield v2.2: Masked Auto-fill
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
    if (validationError) return;

    const name    = nameRef?.value || 'Khách lẻ';
    const phone   = phoneRef?.value || '';
    const address = addressRef?.value || '';

    if (!phone || !address) {
      validationError = 'Vui lòng điền đủ SĐT và Địa chỉ';
      return;
    }

    await shopStore.submitCheckout({ phone, address, name });
  }
</script>

{#if shopStore.isCheckoutOpen}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-slate-950/85 backdrop-blur-md"
    style:z-index={Z_INDEX_CLIENT.MODAL}
    role="presentation"
    aria-hidden="true"
  ></div>

  <!-- Drawer -->
  <div class="checkout-drawer">
    <!-- Ambient glows -->
    <div class="glow glow-top"></div>
    <div class="glow glow-bottom"></div>

    <!-- Close button -->
    <button class="btn-close" onclick={() => shopStore.closeCheckout()} aria-label="Đóng">
      <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- Scrollable body -->
    <div class="drawer-scroll">

      <!-- Header -->
      <header class="mb-6">
        <div class="flex items-end justify-between">
          <div>
            <p class="section-eyebrow mb-1">Chỉ còn 1 bước cuối để dứt điểm...</p>
            <h2 class="drawer-title">Ưu tiên kích hoạt liệu trình</h2>
          </div>
          <div class="ssl-badge">
            {#if shopStore.customerData?.isTrustedDevice}
              <div class="flex items-center gap-1.5 text-emerald-400 mr-2 border-r border-white/10 pr-2">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A10.003 10.003 0 0012 21a10.003 10.003 0 008.139-4.187l.054.09A10.003 10.003 0 0112 21c-3.147 0-5.941-1.45-7.747-3.719zM12 7V3m0 0a3 3 0 013 3v1h-6V6a3 3 0 013-3z" />
                </svg>
                <span class="text-[9px] font-black uppercase tracking-tighter">Bảo mật ưu tiên</span>
              </div>
            {/if}
            <span class="ssl-dot"></span>
            <span>Bảo mật tuyệt đối</span>
          </div>
        </div>
      </header>

      <!-- Variant Selection -->
      {#if hasVariants}
        <section class="mb-6">
          <div class="section-header mb-3">
            <div class="flex items-center gap-2">
              <span class="section-eyebrow">Dành riêng cho bạn</span>
              <div class="h-1 w-1 bg-white/20 rounded-full"></div>
              <span class="text-[8px] font-bold text-emerald-400 animate-pulse">● {liveViewCount} người đang xem</span>
            </div>
            <span class="elite-chip">Ưu tiên hàng đầu</span>
          </div>
          <div class="variant-grid">
            {#each variants as v, idx}
              {@const active = shopStore.variant?.id === v.id}
              <button
                onclick={() => shopStore.selectVariant(v)}
                class="variant-card {active ? 'variant-active' : 'variant-idle'} relative"
              >
                {#if idx === 1}
                  <div class="absolute -top-1.5 -right-1 z-10 px-1.5 py-0.5 bg-red-500 text-white text-[6.5px] font-black rounded uppercase tracking-tighter shadow-lg animate-bounce">
                    Sắp cháy hàng
                  </div>
                {/if}
                <div class="variant-img-wrap">
                  <img src={getVariantImage(v)} alt={getVariantName(v)} class="variant-img" />
                  {#if active}
                    <div class="variant-check-overlay">
                      <div class="variant-check">
                        <svg class="w-3.5 h-3.5 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3.5" d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    </div>
                  {/if}
                </div>
                <span class="variant-name">{getVariantName(v)}</span>
                <span class="variant-price">{(v.discountPrice || v.price).toLocaleString()}đ</span>
              </button>
            {/each}
          </div>
        </section>
      {/if}

      <!-- Quantity & Timer row -->
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
          <div class="flex flex-col">
            <span class="pill-label">Ưu đãi giữ chỗ kết thúc</span>
            <span class="text-[8.5px] font-black text-amber-500 mt-0.5 tracking-wider">MÃ: {appliedPromoCode}</span>
          </div>
          <span class="timer-val">{formatTime(reservationTime)}</span>
        </div>
      </div>

      <!-- Form fields -->
      <div class="form-stack mb-6">
        <!-- 1. Phone (Now FIRST) -->
        <div class="field-wrap">
          <input
            type="tel"
            bind:this={phoneRef}
            oninput={handlePhoneInput}
            onblur={validateInput}
            placeholder=" "
            class="field-input field-lg {validationError && validationError.includes('thoại') ? 'field-error' : ''}"
            id="sc-phone"
          />
          <label for="sc-phone" class="field-label">Số điện thoại nhận Ưu đãi & Phác đồ <span class="text-sky-500">*</span></label>
          <span class="field-hint">10+ số · Bảo mật 256-bit</span>
          
          {#if shopStore.customerData?.isRecurring}
            <div class="absolute -bottom-5 left-2 flex items-center gap-1.5 text-[10px] font-extrabold text-[#38bdf8] animate-in fade-in slide-in-from-top-1">
              <div class="w-1.5 h-1.5 {shopStore.customerData.isTrustedDevice ? 'bg-emerald-500' : 'bg-amber-500'} rounded-full animate-pulse"></div>
              Chào mừng {shopStore.customerData.nameMasked || 'bạn'} quay trở lại!
              <span class="ml-1 px-1.5 py-0.5 bg-sky-500/10 text-sky-500 text-[7px] uppercase tracking-tighter rounded">Dữ liệu đã được bảo mật (***)</span>
            </div>
          {/if}
        </div>

        <!-- 2. Name -->
        <div class="field-wrap mt-2">
          <input
            type="text"
            bind:this={nameRef}
            oninput={handleNameInput}
            placeholder=" "
            class="field-input"
            id="sc-name"
          />
          <label for="sc-name" class="field-label">Họ tên người nhận (không bắt buộc)</label>
          
          {#if shopStore.customerData?.isRecurring && nameRef?.value === shopStore.customerData.nameMasked}
            <div class="absolute -right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 pr-4 text-emerald-400 animate-in zoom-in">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          {/if}
        </div>

        <!-- 3. Address -->
        <div class="field-wrap">
          <textarea
            bind:this={addressRef}
            onblur={validateInput}
            rows="2"
            placeholder=" "
            class="field-input field-textarea {validationError && validationError.includes('địa chỉ') ? 'field-error' : ''}"
            id="sc-address"
          ></textarea>
          <label for="sc-address" class="field-label">Địa chỉ giao hàng <span class="text-sky-500">*</span></label>
        </div>

        {#if validationError}
          <div class="error-msg">{validationError}</div>
        {/if}
      </div>

      <!-- Upsell / Applied deal -->
      {#if shopStore.appliedDeal}
        <div class="deal-applied mb-6">
          <div class="flex flex-col">
            <div class="flex items-center gap-2 mb-1.5">
              <span class="deal-eyebrow !mb-0">Quà tặng Elite đã áp dụng</span>
              <span class="promo-code-badge flex items-center gap-1">
                <svg class="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                </svg>
                {appliedPromoCode}
              </span>
            </div>
            <span class="deal-label">{shopStore.appliedDeal.label}</span>
          </div>
          <button type="button" onclick={() => shopStore.setQuantity(1)} class="deal-cancel">Hủy</button>
        </div>
      {:else if shopStore.nextDeal}
        <button
          type="button"
          onclick={() => shopStore.setQuantity(shopStore.quantity + shopStore.nextDeal!.missing)}
          class="deal-next mb-6"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">🎁</span>
            <div class="flex flex-col text-left">
              <span class="deal-eyebrow text-amber-400">Siêu ưu đãi</span>
              <span class="deal-next-label">
                Thêm {shopStore.nextDeal.missing} hộp nhận
                <span class="underline decoration-2 text-amber-400">{shopStore.nextDeal.deal.label}</span>
              </span>
            </div>
          </div>
          <div class="deal-cta">NHẬN NGAY</div>
        </button>
      {/if}

      <!-- Order summary footer -->
      <footer class="order-footer">
        <!-- Price row -->
        <div class="price-row">
          <div class="flex flex-col">
            <span class="section-eyebrow mb-1">Kết quả đầu tư cho sức khỏe</span>
            <div class="flex items-baseline gap-2">
              <span class="price-main">{(totalPrice || 0).toLocaleString()}đ</span>
              {#if shopStore.originalPrice * shopStore.quantity > totalPrice}
                <span class="price-old">{(shopStore.originalPrice * shopStore.quantity).toLocaleString()}đ</span>
              {/if}
            </div>
          </div>
          <div class="free-ship">
            <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z"/>
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10l1.5 1M13 16H9m4-10h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V15a1 1 0 01-1 1h-1.5"/>
            </svg>
            <span class="whitespace-nowrap">MIỄN PHÍ SHIP</span>
          </div>
        </div>

        {#if shopStore.error}
          <div class="api-error">{shopStore.error}</div>
        {/if}

        <!-- CTA Button -->
        <button
          onclick={handleSubmit}
          disabled={isSubmitting}
          class="btn-cta"
        >
          {#if isSubmitting}
            <div class="spinner"></div>
            <span>Hệ thống đang ưu tiên xử lý...</span>
          {:else}
            <div class="btn-cta-inner">
              <span class="btn-cta-label">KÍCH HOẠT & NHẬN ƯU ĐÃI</span>
              {#if savedAmount > 0}
                <span class="btn-cta-saving">
                  <span class="saving-fire">🔥</span>
                  Tiết kiệm {savedAmount.toLocaleString()}đ + Miễn phí ship 30-60k hôm nay
                  <span class="saving-fire">🔥</span>
                </span>
              {:else}
                <span class="btn-cta-saving">
                  <span class="saving-fire">🚀</span>
                  Miễn phí vận chuyển 30-60k — Chỉ hôm nay!
                </span>
              {/if}
            </div>
            <span class="btn-arrow">→</span>
          {/if}
        </button>

        <!-- Future Pacing / Trust Note -->
        <p class="text-[9px] text-slate-500 italic text-center mb-1 opacity-60">
          * Liệu trình được đóng gói kín đáo. <br/> Cảm nhận sự thay đổi tích cực ngay sau lần đầu sử dụng.
        </p>

        <!-- Security badges -->
        <div class="security-row">
          <span class="sec-badge">PCI DSS</span>
          <span class="sec-badge">AES-256</span>
          <span class="sec-badge">2FA</span>
        </div>

        <!-- Legal / Entity Info -->
        <p class="text-[8px] text-slate-500/50 text-center mt-1 uppercase tracking-widest font-bold">
          MICSMO.COM - Giấy phép kinh doanh: 09 B8 004018 cấp từ 16/10/2015 - Ninh Bình
        </p>
      </footer>
    </div>
  </div>
{/if}

