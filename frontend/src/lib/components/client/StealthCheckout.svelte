<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { Z_INDEX } from '$lib/core/constants/zIndex.ts';
  import { onMount } from 'svelte';

  const shopStore = getShopStore();

  // Native DOM refs — bypass reactive overhead
  let nameRef: HTMLInputElement | undefined;
  let phoneRef: HTMLInputElement | undefined;
  let addressRef: HTMLTextAreaElement | undefined;

  let validationError = $state<string | null>(null);
  let reservationTime = $state(501);

  const totalPrice    = $derived(shopStore.totalAmount);
  const isSubmitting  = $derived(shopStore.isSubmitting);
  const variants      = $derived(shopStore.product?.variants || []);
  const hasVariants   = $derived(variants.length > 1);

  onMount(() => {
    const timer = setInterval(() => {
      if (reservationTime > 0) reservationTime--;
    }, 1000);
    return () => clearInterval(timer);
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

  function getVariantName(v: any) {
    if (!shopStore.product?.tierVariations) return v.sku || 'Sản phẩm';
    return v.tierIndex
      .map((idx: number, tierIdx: number) => shopStore.product!.tierVariations[tierIdx]?.options[idx] || '')
      .filter(Boolean)
      .join(' – ');
  }

  function getVariantImage(v: any) {
    if (!shopStore.product?.tierVariations) return shopStore.product?.images?.[0] || '';
    for (let i = 0; i < v.tierIndex.length; i++) {
      const img = shopStore.product!.tierVariations[i]?.images[v.tierIndex[i]];
      if (img) return img;
    }
    return shopStore.product?.images?.[0] || '';
  }

  // Smart Lookup Logic (Elite V2.2)
  let lookupTimer: any;
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
    class="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-[1000]"
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
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- Scrollable body -->
    <div class="drawer-scroll">

      <!-- Header -->
      <header class="mb-6">
        <div class="flex items-end justify-between">
          <div>
            <p class="section-eyebrow mb-1">Bước cuối cùng</p>
            <h2 class="drawer-title">Xác nhận<br/>liệu trình</h2>
          </div>
          <div class="ssl-badge">
            {#if shopStore.customerData?.isTrustedDevice}
              <div class="flex items-center gap-1.5 text-emerald-400 mr-2 border-r border-white/10 pr-2">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A10.003 10.003 0 0012 21a10.003 10.003 0 008.139-4.187l.054.09A10.003 10.003 0 0112 21c-3.147 0-5.941-1.45-7.747-3.719zM12 7V3m0 0a3 3 0 013 3v1h-6V6a3 3 0 013-3z" />
                </svg>
                <span class="text-[9px] font-black uppercase tracking-tighter">Trusted Device</span>
              </div>
            {/if}
            <span class="ssl-dot"></span>
            <span>AES-256 SSL</span>
          </div>
        </div>
      </header>

      <!-- Variant Selection -->
      {#if hasVariants}
        <section class="mb-6">
          <div class="section-header mb-3">
            <span class="section-eyebrow">Phân loại liệu trình</span>
            <span class="elite-chip">ELITE CHOICE</span>
          </div>
          <div class="variant-grid">
            {#each variants as v}
              {@const active = shopStore.variant?.id === v.id}
              <button
                onclick={() => shopStore.selectVariant(v)}
                class="variant-card {active ? 'variant-active' : 'variant-idle'}"
              >
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
        <div class="info-pill">
          <span class="pill-label">Giữ hàng</span>
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
          <label for="sc-phone" class="field-label">Số điện thoại nhận tư vấn <span class="text-sky-500">*</span></label>
          <span class="field-hint">10+ số · Bảo mật</span>
          
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
            <span class="deal-eyebrow">Quà tặng Elite đã áp dụng</span>
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
            <span class="section-eyebrow mb-1">Tổng thanh toán</span>
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
            <span>Hệ thống đang xử lý...</span>
          {:else}
            <span>Xác nhận liệu trình</span>
            <span class="btn-arrow">→</span>
          {/if}
        </button>

        <!-- Security badges -->
        <div class="security-row">
          <span class="sec-badge">PCI DSS</span>
          <span class="sec-badge">AES-256</span>
          <span class="sec-badge">2FA</span>
        </div>
      </footer>
    </div>
  </div>
{/if}

<style>
  /* ── Drawer shell ───────────────────────────── */
  .checkout-drawer {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    z-index: 1001;
    background: linear-gradient(180deg, #0f1117 0%, #080b12 100%);
    border: 1px solid rgba(255,255,255,0.07);
    border-bottom: none;
    border-radius: 2rem 2rem 0 0;
    box-shadow: 0 -24px 80px rgba(0,0,0,0.6), 0 -1px 0 rgba(255,255,255,0.04) inset;
    max-height: 95svh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  @media (min-width: 768px) {
    .checkout-drawer {
      top: 50%; left: 50%;
      bottom: auto; right: auto;
      transform: translate(-50%, -50%);
      width: 100%;
      max-width: 520px;
      border-radius: 2rem;
      border: 1px solid rgba(255,255,255,0.07);
      max-height: 92vh;
    }
  }

  /* Ambient backgrounds */
  .glow {
    position: absolute;
    width: 300px; height: 300px;
    border-radius: 50%;
    pointer-events: none;
    opacity: 0.6;
    animation: throb 6s ease-in-out infinite;
  }
  .glow-top    { top: -120px; right: -80px;  background: radial-gradient(circle, rgba(14,165,233,0.12), transparent 70%); }
  .glow-bottom { bottom: -120px; left: -80px; background: radial-gradient(circle, rgba(99,102,241,0.1), transparent 70%); animation-delay: 3s; }

  @keyframes throb {
    0%, 100% { transform: scale(1); }
    50%       { transform: scale(1.15); }
  }

  /* Close button */
  .btn-close {
    position: absolute;
    top: 1.25rem; right: 1.25rem;
    z-index: 20;
    width: 36px; height: 36px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.4);
    display: flex; align-items: center; justify-content: center;
    transition: all 0.2s;
    cursor: pointer;
  }
  .btn-close:hover { background: rgba(255,255,255,0.1); color: white; }

  /* Scrollable body */
  .drawer-scroll {
    position: relative; z-index: 10;
    flex: 1;
    overflow-y: auto;
    padding: 1.75rem 1.5rem 2rem;
    scrollbar-width: thin;
    scrollbar-color: rgba(255,255,255,0.06) transparent;
  }

  /* ── Typography helpers ─────────────────────── */
  .section-eyebrow {
    font-size: 9px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: rgba(255,255,255,0.35);
  }
  .drawer-title {
    font-size: 2.4rem;
    font-weight: 900;
    color: white;
    letter-spacing: -0.035em;
    line-height: 1.05;
    font-style: italic;
    text-transform: uppercase;
  }

  /* SSL badge */
  .ssl-badge {
    display: flex; align-items: center; gap: 6px;
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.18);
    border-radius: 999px;
    padding: 5px 10px;
    font-size: 8px; font-weight: 900;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: rgba(52,211,153,0.7);
    margin-bottom: 4px;
  }
  .ssl-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #10b981;
    animation: pulse 2s ease-in-out infinite;
    box-shadow: 0 0 6px rgba(16,185,129,0.8);
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.5; }
  }

  /* ── Section header row ─────────────────────── */
  .section-header {
    display: flex; align-items: center; justify-content: space-between;
  }
  .elite-chip {
    font-size: 7px; font-weight: 900;
    text-transform: uppercase; letter-spacing: 0.12em;
    color: #38bdf8;
    background: rgba(14,165,233,0.1);
    border: 1px solid rgba(14,165,233,0.2);
    border-radius: 6px;
    padding: 2px 7px;
  }

  /* ── Variant grid ───────────────────────────── */
  .variant-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }
  .variant-card {
    display: flex; flex-direction: column;
    border-radius: 1.25rem;
    border: 2px solid;
    padding: 8px;
    cursor: pointer;
    transition: all 0.25s;
    background: transparent;
  }
  .variant-idle   { border-color: rgba(255,255,255,0.06); opacity: 0.45; }
  .variant-idle:hover { opacity: 0.9; border-color: rgba(255,255,255,0.15); }
  .variant-active { border-color: #0ea5e9; background: rgba(14,165,233,0.08); opacity: 1; }

  .variant-img-wrap {
    aspect-ratio: 1;
    border-radius: 0.75rem;
    overflow: hidden;
    background: #0a0c10;
    margin-bottom: 8px;
    border: 1px solid rgba(255,255,255,0.05);
    position: relative;
  }
  .variant-img {
    width: 100%; height: 100%; object-fit: cover;
    transition: transform 0.6s;
  }
  .variant-card:hover .variant-img { transform: scale(1.08); }

  .variant-check-overlay {
    position: absolute; inset: 0;
    background: rgba(14,165,233,0.12);
    display: flex; align-items: center; justify-content: center;
  }
  .variant-check {
    width: 22px; height: 22px;
    border-radius: 50%;
    background: white;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
  }
  .variant-name {
    font-size: 8.5px; font-weight: 900; text-transform: uppercase;
    color: white; text-align: center;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    display: block; margin-bottom: 3px; padding: 0 2px;
  }
  .variant-price {
    font-size: 10px; font-weight: 900; font-style: italic;
    color: #38bdf8; text-align: center; letter-spacing: -0.02em;
    display: block;
  }

  /* ── Qty / Timer pills ──────────────────────── */
  .row-2col {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  }
  .info-pill {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 1rem;
    padding: 10px 14px;
  }
  .pill-label {
    font-size: 9px; font-weight: 900; text-transform: uppercase;
    letter-spacing: 0.1em; color: rgba(255,255,255,0.3);
  }
  .qty-ctrl {
    display: flex; align-items: center; gap: 10px;
    background: rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 0.65rem;
    padding: 4px 10px;
  }
  .qty-btn {
    font-size: 16px; font-weight: 900;
    color: rgba(255,255,255,0.4);
    transition: color 0.15s;
    cursor: pointer; background: none; border: none; padding: 0;
    line-height: 1;
  }
  .qty-btn:hover { color: white; }
  .qty-val {
    font-size: 14px; font-weight: 900; color: white;
    min-width: 16px; text-align: center; font-variant-numeric: tabular-nums;
  }
  .timer-val {
    font-size: 15px; font-weight: 900; color: white;
    font-variant-numeric: tabular-nums; letter-spacing: -0.02em;
  }

  /* ── Form fields ────────────────────────────── */
  .form-stack { display: flex; flex-direction: column; gap: 12px; }

  .field-wrap { position: relative; }

  .field-input {
    width: 100%;
    padding: 20px 18px 10px;
    background: rgba(255,255,255,0.03);
    border: 1.5px solid rgba(255,255,255,0.07);
    border-radius: 1.25rem;
    outline: none;
    color: white;
    font-size: 13px;
    font-weight: 700;
    transition: border-color 0.25s, background 0.25s, box-shadow 0.25s;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.4);
    resize: none;
    box-sizing: border-box;
  }
  .field-input::placeholder { color: transparent; }
  .field-input:focus {
    border-color: rgba(14,165,233,0.5);
    background: rgba(14,165,233,0.04);
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.4), 0 0 0 3px rgba(14,165,233,0.08);
  }

  /* ── Autofill Correction (Elite V2.2) ───────── */
  .field-input:-webkit-autofill,
  .field-input:-webkit-autofill:hover, 
  .field-input:-webkit-autofill:focus {
    -webkit-text-fill-color: white !important;
    -webkit-box-shadow: 0 0 0px 1000px #0a0c10 inset !important;
    transition: background-color 5000s ease-in-out 0s;
    caret-color: white;
  }
  .field-input.field-error {
    border-color: rgba(239,68,68,0.4);
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.4), 0 0 0 3px rgba(239,68,68,0.07);
  }
  .field-lg { font-size: 17px; padding: 22px 18px 10px; }
  .field-textarea { padding-top: 22px; }

  /* Floating label */
  .field-label {
    position: absolute;
    top: 50%; left: 18px;
    transform: translateY(-50%);
    font-size: 10px; font-weight: 900;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: rgba(255,255,255,0.3);
    pointer-events: none;
    transition: all 0.2s;
  }
  .field-textarea ~ .field-label { top: 16px; transform: none; }

  .field-input:not(:placeholder-shown) ~ .field-label,
  .field-input:focus ~ .field-label {
    top: 9px; transform: none;
    font-size: 8.5px;
    color: rgba(14,165,233,0.7);
  }
  .field-textarea:not(:placeholder-shown) ~ .field-label,
  .field-textarea:focus ~ .field-label {
    font-size: 8.5px;
    color: rgba(14,165,233,0.7);
  }

  /* Hint badge (phone) */
  .field-hint {
    position: absolute;
    right: 16px; top: 50%; transform: translateY(-50%);
    font-size: 8px; font-weight: 900; text-transform: uppercase;
    letter-spacing: 0.08em; color: rgba(255,255,255,0.18);
    pointer-events: none;
  }

  .error-msg {
    font-size: 9px; font-weight: 900; text-transform: uppercase;
    letter-spacing: 0.12em; color: rgba(239,68,68,0.75);
    padding: 0 4px;
  }

  /* ── Deals ──────────────────────────────────── */
  .deal-applied {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(14,165,233,0.07);
    border: 1px solid rgba(14,165,233,0.2);
    border-radius: 1.25rem;
    padding: 14px 18px;
  }
  .deal-eyebrow {
    font-size: 8px; font-weight: 900; text-transform: uppercase;
    letter-spacing: 0.12em; color: rgba(14,165,233,0.65); display: block; margin-bottom: 2px;
  }
  .deal-label {
    font-size: 13px; font-weight: 900; color: white; font-style: italic; text-transform: uppercase;
  }
  .deal-cancel {
    font-size: 9px; font-weight: 900; text-transform: uppercase;
    color: rgba(255,255,255,0.3); border: 1px solid rgba(255,255,255,0.07);
    background: transparent; border-radius: 0.65rem; padding: 6px 12px; cursor: pointer;
    transition: all 0.2s;
  }
  .deal-cancel:hover { color: white; border-color: rgba(255,255,255,0.2); }

  .deal-next {
    display: flex; align-items: center; justify-content: space-between;
    width: 100%;
    background: rgba(245,158,11,0.07);
    border: 1px solid rgba(245,158,11,0.25);
    border-radius: 1.25rem; padding: 14px 18px;
    cursor: pointer; transition: all 0.25s;
  }
  .deal-next:hover { background: rgba(245,158,11,0.13); }
  .deal-next:active { transform: scale(0.98); }
  .deal-next-label {
    font-size: 12px; font-weight: 900; color: white; font-style: italic;
  }
  .deal-cta {
    font-size: 9px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.08em;
    background: #f59e0b; color: #000; padding: 6px 12px; border-radius: 0.65rem;
    transition: transform 0.2s;
    white-space: nowrap;
  }
  .deal-next:hover .deal-cta { transform: scale(1.06); }

  /* ── Order footer ───────────────────────────── */
  .order-footer {
    border-top: 1px solid rgba(255,255,255,0.07);
    padding-top: 20px;
    display: flex; flex-direction: column; gap: 16px;
  }
  .price-row {
    display: flex; align-items: center; justify-content: space-between;
  }
  .price-main {
    font-size: 2.2rem; font-weight: 900; color: white;
    letter-spacing: -0.04em; font-style: italic; font-variant-numeric: tabular-nums;
  }
  .price-old {
    font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.25);
    text-decoration: line-through; font-variant-numeric: tabular-nums;
  }
  .free-ship {
    display: flex; flex-direction: column; align-items: center; gap: 3px;
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.2);
    border-radius: 1rem;
    padding: 10px 14px;
    color: #34d399;
    font-size: 9px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em;
    text-align: center;
    white-space: nowrap;
    transform: rotate(2deg);
  }
  .api-error {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.2);
    border-radius: 1rem;
    padding: 12px 16px;
    font-size: 9px; font-weight: 900; text-transform: uppercase;
    letter-spacing: 0.1em; color: rgba(239,68,68,0.8);
    text-align: center;
  }

  /* CTA button */
  .btn-cta {
    width: 100%;
    padding: 18px 24px;
    background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
    border: none; border-radius: 999px;
    color: white; font-size: 15px; font-weight: 900;
    display: flex; align-items: center; justify-content: center; gap: 12px;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 8px 32px rgba(14,165,233,0.3), 0 2px 0 rgba(255,255,255,0.1) inset;
    letter-spacing: 0.02em;
  }
  .btn-cta:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(14,165,233,0.4), 0 2px 0 rgba(255,255,255,0.1) inset;
  }
  .btn-cta:active:not(:disabled) { transform: translateY(0); }
  .btn-cta:disabled {
    background: rgba(255,255,255,0.08);
    box-shadow: none;
    cursor: not-allowed;
    color: rgba(255,255,255,0.4);
  }
  .btn-arrow {
    width: 38px; height: 38px;
    background: rgba(255,255,255,0.12);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    transition: background 0.2s;
  }
  .btn-cta:hover:not(:disabled) .btn-arrow { background: rgba(255,255,255,0.2); }

  .spinner {
    width: 20px; height: 20px;
    border: 3px solid rgba(255,255,255,0.2);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Security row */
  .security-row {
    display: flex; justify-content: center; gap: 8px;
  }
  .sec-badge {
    font-size: 7px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.12em;
    color: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 5px; padding: 3px 8px;
  }
</style>
