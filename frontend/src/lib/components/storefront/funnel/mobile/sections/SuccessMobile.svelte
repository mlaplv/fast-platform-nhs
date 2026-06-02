<script lang="ts">
  import { fade, fly, slide } from "svelte/transition";
  import FileText from "@lucide/svelte/icons/file-text";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import Package from "@lucide/svelte/icons/package";
  import Truck from "@lucide/svelte/icons/truck";
  import Phone from "@lucide/svelte/icons/phone";
  import Gift from "@lucide/svelte/icons/gift";
  import Home from "@lucide/svelte/icons/home";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Edit3 from "@lucide/svelte/icons/edit-3";
  import { formatCurrency, formatDate } from "$lib/utils/format";
  import { goto } from "$app/navigation";
  import { SHOP_CONFIG } from "$lib/constants/shop";
  import { apiClient } from "$lib/utils/apiClient";
  import { page } from "$app/state";
  import vnDivisions from "$lib/data/vn_divisions.json";
  import AddressSelector from "../checkout/AddressSelector.svelte";
  import SimpleTiptap from "$lib/components/storefront/ui/SimpleTiptap.svelte";
  import HeaderMobile from "$lib/components/storefront/layout/HeaderMobile.svelte";

  import type { OrderDetail, OrderItem } from "$lib/types/commerce/order";

  interface GiftItem {
    name: string;
    qty: number;
    image?: string;
  }

  function resolveItemGifts(item: OrderItem): GiftItem[] {
    if (item.gifts && Array.isArray(item.gifts) && item.gifts.length > 0) {
      return item.gifts as GiftItem[];
    }
    
    // Fallback identical to checkout items promo gifts logic
    const variantName = (item.variant_name || "").toLowerCase();
    const qty = item.qty || item.quantity || 1;
    const isMiccosmoVirginWhite = item.id === "prod_miccosmo_virgin_white" || (item.name || "").toLowerCase().includes("virgin white");
    
    if (isMiccosmoVirginWhite) {
      if (variantName.includes("dứt điểm") || qty === 3 || variantName.includes("mua 3")) {
        return [
          {
            name: `${item.name} (Tặng thêm)`,
            qty: 1,
            image: item.image || item.image_url || "/uploads/2026/04/535e0488-bca7-4035-935d-a8c3c022ab63.webp"
          }
        ];
      }
    }
    return [];
  }
  let {
    order = $bindable(),
    orderId,
    isLookup,
  } = $props<{ order: OrderDetail; orderId: string; isLookup: boolean }>();

  // --- Elite V2.2: Edit Logic ---
  let isEditing = $state(false);
  let isSubmittingAction = $state(false);
  let editForm = $state({
    name: "",
    phone: "",
    province: "",
    ward: "",
    street: "",
    note: "",
  });
  let isSubmittingVerify = $state(false);
  let showVerificationDialog = $state(false);
  let verificationPhone = $state("");
  let activePhone = $state("");

  const isLocked = $derived.by(() => {
    if (order.status !== "PENDING") return false;
    const nameMasked = order.name_masked?.includes("*") || order.customerName?.includes("*");
    const addrMasked = order.address_masked?.includes("*") || order.customerAddress?.includes("*");
    return nameMasked || addrMasked;
  });

  interface VnDivision {
    id: string;
    name: string;
    code: string;
    wards: string[];
  }

  function parseAddress(fullAddress: string) {
    if (!fullAddress) return { province: "", ward: "", street: "" };
    const parts = fullAddress.split(",").map((p) => p.trim());
    if (parts.length >= 3) {
      return {
        province: parts[parts.length - 1],
        ward: parts[parts.length - 2],
        street: parts.slice(0, parts.length - 2).join(", "),
      };
    }
    return { province: "", ward: "", street: fullAddress };
  }

  function startEditing() {
    // Elite V4.0: Competition Shield
    if (isLocked) {
      showVerificationDialog = true;
      return;
    }
    // Elite V2.2: Dual-Layer Identity Recognition (Handles both camelCase and snake_case from API)
    const rawName = order.customer_name || order.customerName || "";
    const rawPhone = order.customer_phone || order.customerPhone || "";
    const rawAddress = order.customer_address || order.customerAddress || "";
    const meta = order.order_metadata || order.orderMetadata;
    const rawNote = meta?.customer_note || meta?.note || order.note || "";

    const addrParts = parseAddress(rawAddress);
    editForm = {
      name: rawName,
      phone: rawPhone,
      province: addrParts.province,
      ward: addrParts.ward,
      street: addrParts.street,
      note: rawNote,
    };
    isEditing = true;
  }

  async function handleVerify() {
    if (!verificationPhone) {
      showToast("Vui lòng nhập số điện thoại", "error");
      return;
    }
    isSubmittingVerify = true;
    try {
      console.log(`[Elite-Sync] Verifying identity for ${orderId}...`);
      await apiClient.post(`/api/v1/client/orders/${orderId}/verify-full`, {
        phone: verificationPhone
      }, { params: { _t: Date.now() } });
      
      // Cookie is now set, re-fetch unmasked data
      const res = await apiClient.get<OrderDetail>(
        `/api/v1/client/orders/${orderId}`,
        { params: { phone: verificationPhone, _t: Date.now() } }
      );
      if (res) {
        order = res;
        activePhone = verificationPhone;
        if (typeof localStorage !== "undefined") {
          localStorage.setItem(`order_verify_${orderId}`, verificationPhone);
        }
      }
      showVerificationDialog = false;
      showToast("Xác thực thành công");
      // Seamless transition
      setTimeout(() => startEditing(), 100);
    } catch (err: unknown) {
      const e = err as { message?: string };
      showToast(e.message || "Xác thực thất bại", "error");
    } finally {
      isSubmittingVerify = false;
    }
  }

  // Local Elite Toast System
  let toasts = $state<
    { id: number; type: "success" | "error"; message: string }[]
  >([]);
  let toastId = 0;

  function showToast(message: string, type: "success" | "error" = "success") {
    const id = toastId++;
    toasts.push({ id, type, message });
    setTimeout(() => {
      const idx = toasts.findIndex((t) => t.id === id);
      if (idx !== -1) toasts.splice(idx, 1);
    }, 4000);
  }

  async function handleSaveEdit() {
    isSubmittingAction = true;
    try {
      const raw = page.url.searchParams.get("phone") ||
        (typeof localStorage !== "undefined"
          ? localStorage.getItem(`order_verify_${orderId}`)
          : null);
      const phoneParam = (raw && raw !== "undefined" && raw !== "null") ? raw : null;

      if (!phoneParam) {
        showToast("Vui lòng xác thực số điện thoại để cập nhật", "error");
        isSubmittingAction = false;
        return;
      }

      console.log(`[Elite-Sync] Saving mobile edit for ${orderId}...`);
      console.log("[Elite-Sync] Previous data:", {
        name: order.customer_name || order.customerName,
        address: order.customer_address || order.customerAddress
      });

      const res = await apiClient.patch(
        `/api/v1/client/orders/${orderId}`,
        {
          customer_name: editForm.name,
          customer_phone: editForm.phone,
          customer_address: `${editForm.street}, ${editForm.ward}, ${editForm.province}`,
          note: editForm.note,
          order_metadata: {
            ...(order.order_metadata || order.orderMetadata || {}),
            customer_note: editForm.note,
          },
        },
        { params: { phone: phoneParam, _t: Date.now() } },
      );

      // Refresh local data from response
      if (res) {
        order = res;
        console.log("[Elite-Sync] Save success. Updated data:", order);
      } else {
        order.customer_name = editForm.name;
        order.customer_phone = editForm.phone;
        order.customer_address = `${editForm.street}, ${editForm.ward}, ${editForm.province}`;
        order.note = editForm.note;
        if (!order.order_metadata) order.order_metadata = {};
        order.order_metadata.customer_note = editForm.note;
      }

      showToast("Đã cập nhật thông tin thành công");
      isEditing = false;
    } catch (err) {
      console.error("Failed to save", err);
      showToast((err as Error).message || "Lỗi cập nhật dữ liệu", "error");
    } finally {
      isSubmittingAction = false;
    }
  }

  let isConfirmCancelOpen = $state(false);

  async function handleCancel() {
    isConfirmCancelOpen = false;
    isSubmittingAction = true;
    
    // Elite V2.2: Identity Gate
    const raw = page.url.searchParams.get("phone") || 
               (typeof localStorage !== "undefined" ? localStorage.getItem(`order_verify_${orderId}`) : null);
    const sanitizedPhone = (raw && raw !== "undefined" && raw !== "null") ? raw : null;

    if (!sanitizedPhone) {
      showToast("Vui lòng xác thực số điện thoại để hủy đơn", "error");
      isSubmittingAction = false;
      return;
    }

    try {
      console.log(`[Elite-Sync] Cancelling order ${orderId}...`);
      const res_cancel = await apiClient.post<OrderDetail>(
        `/api/v1/client/orders/${orderId}/cancel`,
        {},
        { params: { phone: sanitizedPhone, _t: Date.now() } },
      );
      if (res_cancel) order = res_cancel;

      showToast("Đã hủy đơn hàng thành công");
      // Reload order data for full sync
      const res = await apiClient.get<OrderDetail>(
        `/api/v1/client/orders/${orderId}`,
        {
          params: { phone: sanitizedPhone, _t: Date.now() },
        },
      );
      if (res) {
        order = res;
        console.log("[Elite-Sync] Cancellation sync complete:", order);
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      showToast(e.message || "Không thể hủy đơn hàng", "error");
    } finally {
      isSubmittingAction = false;
    }
  }

  function handleAddressSelect(data: { province: string; ward: string }) {
    editForm.province = data.province;
    editForm.ward = data.ward;
  }

  const STATUS_STEPS = [
    { key: "PENDING", label: "Tiếp nhận", icon: FileText },
    { key: "PACKED", label: "Bảo mật", icon: ShieldCheck },
    { key: "SHIPPING", label: "Vận chuyển", icon: Truck },
    { key: "DELIVERED", label: "Thành công", icon: Gift },
  ];

  function getStepIndex(status: string) {
    if (status === "CANCELLED") return -1;
    const idx = STATUS_STEPS.findIndex((s) => s.key === status);
    return idx === -1 ? 0 : idx;
  }

  const currentStepIdx = $derived(getStepIndex(order?.status || "PENDING"));

  let copied = $state(false);
  let copyTimer: ReturnType<typeof setTimeout> | undefined;

  function copyOrderId() {
    if (typeof navigator !== "undefined") {
      const shortId = orderId.slice(-6).toUpperCase();
      navigator.clipboard.writeText(shortId);
      copied = true;
      if (copyTimer) clearTimeout(copyTimer);
      copyTimer = setTimeout(() => (copied = false), 2000);
    }
  }

  const items = $derived(order?.items || []);
  const customerNameDisplay = $derived(
    order?.name_masked ||
      order.customer_name ||
      order.customerName ||
      "Khách hàng",
  );
  const customerAddressDisplay = $derived(
    order?.address_masked ||
      order.customer_address ||
      order.customerAddress ||
      "Địa chỉ bảo mật",
  );

  // Elite V2.2: Reactive Financial Breakdown
  const meta = $derived(order?.order_metadata || order?.orderMetadata);
  const voucherDiscount = $derived(
    Number(meta?.voucher_discount || meta?.voucherDiscount || 0),
  );
  const comboDiscount = $derived(
    Number(meta?.combo_discount || meta?.comboDiscount || 0),
  );
  const shippingFee = $derived(
    Number(meta?.shipping_fee || meta?.shippingFee || 0),
  );
  const appliedVouchers = $derived(
    (meta?.voucher_ids || meta?.voucherIds) && Array.isArray(meta?.voucher_ids || meta?.voucherIds)
      ? (meta?.voucher_ids || meta?.voucherIds) as string[]
      : []
  );
  const totalSavings = $derived(voucherDiscount + comboDiscount);
  const displayNote = $derived.by(() => {
    // Elite V2.2: Dual-Key Resolver (CamelCase API vs SnakeCase Schema)
    const meta = order.order_metadata || order.orderMetadata;
    return meta?.customer_note || meta?.note || order.note || "";
  });

  $effect(() => {
    // Elite V2.2: Minimalist Logger as per Sếp's request
    if (displayNote) {
      console.log("LOG customer_note:", displayNote);
    }
  });
</script>

<div
  class="min-h-screen bg-[#fafafa] text-slate-900 flex flex-col w-full relative"
>
  <HeaderMobile />
  <!-- Cinematic Background Bloom -->
  <div
    class="fixed top-0 left-1/2 -translate-x-1/2 w-full h-[300px] {order?.status === 'CANCELLED' 
      ? 'bg-red-500/10' 
      : isLookup ? 'bg-sky-500/10' : 'bg-emerald-500/10'} blur-[80px] pointer-events-none"
  ></div>

  <div class="relative pt-8 flex flex-col items-center text-center">
    <div class="px-4 w-full">
      <p
        class="text-slate-400 text-[10px] tracking-[0.2em] font-black mb-8 italic"
      >
        {order?.status === "CANCELLED"
          ? "Rất tiếc vì liệu trình không được tiếp tục"
          : isLookup
            ? "Cập nhật trạng thái mới nhất"
            : "Cảm ơn quý khách đã tin tưởng"}
      </p>
    </div>

    {#if order?.status === "CANCELLED"}
      <div class="w-full px-4 mb-4">
         <div class="bg-white p-6 shadow-sm border-t-4 border-red-500 flex flex-col items-center gap-4 text-center">
            <div class="w-12 h-12 bg-red-50 text-red-500 rounded-full flex items-center justify-center text-2xl border border-red-100">✕</div>
            <div>
              <h3 class="text-sm font-black text-slate-900 italic tracking-widest uppercase">Đơn hàng đã được hủy</h3>
              <p class="text-[10px] font-bold text-slate-400 italic">Trạng thái: Vô hiệu hóa</p>
            </div>
            {#if order.cancellation_reason}
              <div class="w-full p-3 bg-slate-50 border border-slate-100 rounded-lg">
                <p class="text-[8px] font-black text-slate-400 italic uppercase mb-1">Lý do:</p>
                <p class="text-[11px] font-bold text-slate-700 italic">"{order.cancellation_reason}"</p>
              </div>
            {/if}
         </div>
      </div>
    {:else}
      <div class="w-full mb-4 px-4">
        <div class="stepper-row flex items-center justify-between pb-8">
          {#each STATUS_STEPS as step, i}
            <div class="relative flex flex-col items-center gap-2">
              <div
                class="w-9 h-9 rounded-full flex items-center justify-center text-xl border-2 transition-all duration-500
                {i < currentStepIdx
                  ? 'bg-emerald-50 border-emerald-500 text-emerald-600'
                  : i === currentStepIdx
                    ? 'bg-sky-50 border-sky-500 text-sky-600 scale-110 shadow-lg'
                    : 'bg-slate-50 border-slate-100 text-slate-300'}"
              >
                <step.icon class="w-4 h-4" />
              </div>
              <span
                class="text-[8px] font-black tracking-widest {i <= currentStepIdx
                  ? 'text-slate-900'
                  : 'text-slate-300'}">{step.label}</span
              >
            </div>
            {#if i < STATUS_STEPS.length - 1}
              <div class="flex-1 h-[2px] mx-1 bg-slate-100 relative">
                <div
                  class="absolute inset-y-0 left-0 bg-emerald-500 transition-all duration-1000"
                  style:width={i < currentStepIdx
                    ? "100%"
                    : i === currentStepIdx
                      ? "50%"
                      : "0%"}
                ></div>
              </div>
            {/if}
          {/each}
        </div>
      </div>
    {/if}

    <div
      class="w-full bg-white shadow-sm border-t-4 border-[#ee4d2d] p-6 mb-2 text-left space-y-8"
    >
      <div class="flex flex-col gap-6 pb-6 border-b border-slate-50">
        <div class="flex justify-between items-start">
          <div>
            <span class="text-[9px] font-black text-slate-500 block mb-1"
              >Mã đơn hàng</span
            >
            <div class="flex items-center gap-2">
              <div
                class="bg-slate-50 px-2 py-1 border border-slate-100 flex items-center gap-2 cursor-pointer"
                onclick={copyOrderId}
                role="button"
                tabindex="0"
              >
                <span class="text-xs font-black text-slate-900 tracking-widest italic">
                  {copied ? "Đã sao chép!" : `#${orderId.slice(-6)}`}
                </span>
              </div>
              {#if order.status === "CANCELLED"}
                <div class="px-2 py-0.5 bg-red-50 border border-red-100 text-red-500 text-[8px] font-black italic rounded">ĐÃ HỦY</div>
              {/if}
              {#if order.status !== "CANCELLED"}
                <button
                  onclick={() => (isConfirmCancelOpen = true)}
                  class="text-[9px] font-black text-slate-300 italic tracking-wider hover:text-red-400 transition-colors ml-1"
                >
                  (Hủy đơn)
                </button>
              {/if}
            </div>
          </div>
          <div class="text-right">
            <span class="text-[9px] font-black text-slate-400 block mb-1"
              >Tổng thanh toán</span
            >
            <span class="text-xl font-black text-[#ee4d2d] italic tabular-nums"
              >{formatCurrency(order?.total || order?.total_amount || 0)}</span
            >
          </div>
        </div>

        <!-- 🚀 [ELITE V2.2] Viral Savings Breakdown -->

        {#if totalSavings > 0}
          <div
            class="py-4 px-4 bg-emerald-500/5 border-l-2 border-emerald-500 rounded-r-lg group relative overflow-hidden"
            in:fly={{ x: -20, delay: 400 }}
          >
            <div class="flex items-center gap-3">
              <div
                class="w-7 h-7 bg-emerald-500 text-white rounded-full flex items-center justify-center shadow-lg shadow-emerald-500/20"
              >
                <Sparkles size={14} class="animate-pulse" />
              </div>
              <div class="flex flex-col">
                <span
                  class="text-[8px] font-black text-slate-400 tracking-widest leading-none mb-1"
                  >Siêu ưu đãi</span
                >
                <span class="text-[10px] font-black text-emerald-600 italic"
                  >Tiết kiệm {formatCurrency(totalSavings)}</span
                >
              </div>
            </div>
            <div
              class="absolute inset-0 bg-gradient-to-r from-white/0 via-white/40 to-white/0 -translate-x-full animate-[shimmer_2.5s_infinite]"
            ></div>
          </div>
        {/if}
      </div>

      <div class="space-y-6">
        <div class="flex items-start gap-3">
          <Package class="w-5 h-5 text-slate-300 mt-0.5 shrink-0" />
          <div class="flex-1 min-w-0">
            <span class="text-[9px] font-black text-slate-500 block mb-1"
              >Sản phẩm chi tiết</span
            >
            <div class="space-y-3.5">
              {#each items as item}
                {@const resolvedItemImage = item.image_url || item.image}
                {@const itemGifts = resolveItemGifts(item)}
                <div class="border-b border-slate-50 pb-3 last:border-b-0 last:pb-0">
                  <div class="flex items-start gap-3">
                    <!-- Product Thumbnail -->
                    <div class="w-12 h-12 bg-slate-50 border border-slate-100 rounded overflow-hidden shrink-0 flex items-center justify-center shadow-sm">
                      {#if resolvedItemImage}
                        <img
                          src={resolvedItemImage}
                          alt={item.name}
                          class="w-full h-full object-cover"
                        />
                      {:else}
                        📦
                      {/if}
                    </div>
                    
                    <div class="flex-1 min-w-0">
                      <p class="text-[12px] font-bold text-slate-900 leading-snug">
                        {item.name}
                      </p>
                      {#if item.variant_name}
                        <p class="text-[9px] text-[#fe2c55] font-black mt-0.5 leading-none">
                          Phân loại: {item.variant_name}
                        </p>
                      {/if}
                      <p class="text-[10px] text-slate-500 font-medium italic mt-1 leading-none">
                        {item.quantity || item.qty || 1} x {formatCurrency(
                          item.unit_price || 0,
                        )}
                      </p>
                    </div>
                    
                    <div class="text-right shrink-0">
                      <span class="text-[12px] font-black italic text-slate-900">
                        {formatCurrency(item.total_price || 0)}
                      </span>
                    </div>
                  </div>

                  <!-- 🎁 MOBILE GIFTS FOR THIS ITEM -->
                  {#if itemGifts && itemGifts.length > 0}
                    <div class="mt-2 bg-[#fff0f1]/90 border border-[#fecdd3] rounded p-2 flex flex-col gap-2 relative overflow-hidden shadow-sm" style="margin-left: 3.75rem;">
                      <div class="absolute inset-0 bg-gradient-to-r from-[#ffe4e6]/40 to-transparent pointer-events-none"></div>
                      <span class="text-[9px] font-black text-[#fe2c55] flex items-center gap-1 leading-none relative z-10 italic">
                        🎁 Quà tặng kèm:
                      </span>
                      <div class="space-y-2 relative z-10 pl-0.5">
                        {#each itemGifts as gift}
                          <div class="flex items-center gap-2">
                            <div class="w-7 h-7 bg-white border border-[#fecdd3] rounded-[2px] overflow-hidden shrink-0 flex items-center justify-center shadow-sm">
                              {#if gift.image}
                                <img src={gift.image} alt={gift.name} class="w-full h-full object-cover" />
                              {:else}
                                🎁
                              {/if}
                            </div>
                            <div class="flex-1 flex items-center justify-between min-w-0">
                              <span class="text-[#fe2c55] font-black text-[10px] tracking-tight truncate pr-2">
                                {gift.name}
                              </span>
                              <span class="text-[#fe2c55] font-extrabold text-[9px] shrink-0 bg-[#ffe4e6] px-1 rounded italic">
                                x{gift.qty}
                              </span>
                            </div>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}
                </div>
              {/each}
            </div>

            <!-- 💸 MOBILE PRICING BREAKDOWN (Elite V2.2) -->
            <div class="mt-4 pt-4 border-t border-slate-100/60 space-y-2.5">
              <div class="flex justify-between text-[11px] font-bold text-slate-400 italic">
                <span>Tạm tính:</span>
                <span class="text-slate-700">{formatCurrency(items.reduce((acc, it) => acc + (it.total_price || 0), 0))}</span>
              </div>

              {#if comboDiscount > 0}
                <div class="flex justify-between text-[11px] font-black text-emerald-500 italic">
                  <span>Ưu đãi Combo:</span>
                  <span>-{formatCurrency(comboDiscount)}</span>
                </div>
              {/if}

              {#if voucherDiscount > 0}
                <div class="flex justify-between text-[11px] font-black text-[#fe2c55] italic">
                  <span>Voucher giảm giá:</span>
                  <span>-{formatCurrency(voucherDiscount)}</span>
                </div>
              {/if}

              <!-- 🎟️ APPLIED VOUCHERS LIST -->
              {#if appliedVouchers && appliedVouchers.length > 0}
                <div class="flex flex-wrap gap-1 pt-0.5 pb-1">
                  {#each appliedVouchers as code}
                    <div class="flex items-center gap-1 bg-[#fff0f1] text-[#fe2c55] text-[8.5px] font-black px-1.5 py-0.5 rounded border border-dashed border-[#fecdd3] shadow-sm select-none" style="text-transform: uppercase;">
                      <span class="inline-block w-1 h-1 bg-[#fe2c55] rounded-full"></span>
                      <span>🎟️ {code}</span>
                    </div>
                  {/each}
                </div>
              {/if}

              <div class="flex justify-between text-[11px] font-bold text-slate-400 italic">
                <span>Vận chuyển:</span>
                <span class={shippingFee > 0 ? "text-slate-700" : "text-emerald-500 font-black"}>
                  {shippingFee > 0 ? formatCurrency(shippingFee) : 'Miễn phí'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <Truck class="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[9px] font-black text-slate-500"
                >Địa chỉ nhận hàng</span
              >
              {#if order.status === "PENDING"}
                <button
                  onclick={startEditing}
                  class="text-[9px] font-black text-sky-600 italic"
                  >Chỉnh sửa</button
                >
              {/if}
            </div>
            <p
              class="text-[12px] font-black text-slate-900 italic leading-tight mb-1"
            >
              {customerNameDisplay}
            </p>
            <p class="text-[10px] font-bold text-slate-500 leading-relaxed">
              {customerAddressDisplay}
            </p>
          </div>
        </div>

        {#if displayNote}
          <div class="flex items-start gap-3 pt-4 border-t border-slate-50">
            <MessageSquare class="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
            <div class="flex-1 min-w-0">
              <span class="text-[9px] font-black text-slate-500 block mb-1"
                >Ghi chú đơn hàng</span
              >
              <div
                class="text-[11px] font-bold text-slate-600 leading-relaxed italic tiptap-render-content"
              >
                {@html displayNote}
              </div>
            </div>
          </div>
        {/if}
      </div>


    </div>

    <!-- 🚀 [ELITE V2.2] CONFIRM CANCEL MODAL MOBILE -->
    {#if isConfirmCancelOpen}
      <div
        class="fixed inset-0 bg-slate-900/60 backdrop-blur-md flex items-end justify-center p-0 z-[3000]"
        transition:fade
      >
        <div
          class="w-full bg-white rounded-t-[32px] p-8 pb-12 space-y-8 shadow-2xl border-t border-slate-100"
          in:fly={{ y: 100, duration: 600 }}
        >
          <div class="w-12 h-1.5 bg-slate-100 rounded-full mx-auto"></div>
          <div class="text-center space-y-3">
            <h3 class="text-2xl font-black italic text-slate-900 tracking-tight">
              Xác nhận hủy đơn?
            </h3>
            <p class="text-[11px] font-bold text-slate-400 leading-relaxed px-10">
              Hành động này không thể hoàn tác. Bạn chắc chắn muốn dừng đơn hàng
              này?
            </p>
          </div>

          <div class="flex flex-col gap-3">
            <button
              onclick={handleCancel}
              class="w-full py-4 bg-[#ee4d2d] text-white font-black italic tracking-widest rounded-2xl shadow-lg shadow-red-500/20 active:scale-95 transition-all"
            >
              Đồng ý hủy đơn
            </button>
            <button
              onclick={() => (isConfirmCancelOpen = false)}
              class="w-full py-2 text-[10px] font-black text-slate-400 tracking-widest"
            >
              Quay lại
            </button>
          </div>
        </div>
      </div>
    {/if}

    <div class="w-full space-y-4 mb-20">
      <!-- 🚀 [ELITE V2.2] Thành viên Elite WOW MOMENT MOBILE -->
      <div
        class="w-full bg-white shadow-sm p-6 rounded-none relative overflow-hidden group transition-all duration-500"
        in:fly={{ y: 20, delay: 600 }}
      >
        <div
          class="absolute -right-4 -bottom-4 w-16 h-16 text-luxury-copper/10 rotate-12 transition-transform duration-700"
        >
          <Gift class="w-full h-full" />
        </div>
        <div class="relative z-10 flex items-center gap-4 text-left">
          <div
            class="w-12 h-12 rounded-full bg-gradient-to-tr from-amber-500 to-amber-200 flex items-center justify-center text-white shadow-lg shadow-amber-500/20"
          >
            <Sparkles class="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h4
              class="text-[10px] font-black text-stone-900 tracking-[2px] leading-none mb-1.5 flex items-center gap-2"
            >
              Thành viên
              <span class="w-1 h-1 bg-amber-500 rounded-full animate-ping"
              ></span>
            </h4>
            <p
              class="text-[14px] font-serif italic text-stone-700 leading-none"
            >
              Tích được <span class="text-amber-600 font-black"
                >+{Math.floor(
                  (order?.total || order?.total_amount || 0) / 100000,
                )} điểm</span
              >
            </p>
            <p class="text-[8px] text-stone-400 font-bold mt-2 opacity-60">
              Khả dụng sau khi giao hàng
            </p>
          </div>
        </div>
      </div>

    <a
      href="tel:{SHOP_CONFIG.pharmacy.phone.replace(/\s+/g, '')}"
      class="fixed bottom-8 right-4 z-50 px-6 py-4 bg-[#ee4d2d] text-white font-black italic tracking-widest text-center shadow-[0_20px_40px_rgba(238,77,45,0.3)] flex items-center gap-2 group active:scale-95 transition-all"
    >
      Gọi xác nhận ngay 
      <span class="group-hover:translate-x-1 transition-transform">→</span>
    </a>
    <div class="px-4 text-center">
      <p class="text-[10px] font-bold text-slate-400 italic">
        Hệ thống osmo đang xử lý yêu cầu...
      </p>
    </div>
    </div>
  </div>
</div>

{#if isEditing}
  <div
    class="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[2000] flex flex-col justify-end"
  >
    <div
      class="w-full bg-white rounded-t-[32px] p-6 pb-[calc(24px+env(safe-area-inset-bottom))] space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto"
      in:fly={{ y: 300, duration: 500 }}
    >
      <div
        class="flex items-center justify-between pb-2 border-b border-slate-50"
      >
        <h2 class="text-lg font-black text-slate-900 italic tracking-tighter">
          Cập nhật thông tin
        </h2>
        <button
          onclick={() => (isEditing = false)}
          class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500"
          >✕</button
        >
      </div>

      <div class="space-y-4">
        <!-- Basic Info -->
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1">
            <label class="text-[10px] font-black text-slate-400 ml-1"
              >Tên người nhận</label
            >
            <input
              type="text"
              bind:value={editForm.name}
              style="color: #0f172a !important;"
              class="w-full p-3.5 bg-slate-50 border border-slate-100 font-bold text-sm text-slate-900 rounded-xl outline-none focus:border-sky-500 transition-all"
            />
          </div>
          <div class="space-y-1">
            <label class="text-[10px] font-black text-slate-400 ml-1"
              >Số điện thoại</label
            >
            <input
              type="tel"
              bind:value={editForm.phone}
              style="color: #0f172a !important;"
              class="w-full p-3.5 bg-slate-50 border border-slate-100 font-bold text-sm text-slate-900 rounded-xl outline-none focus:border-sky-500 transition-all"
            />
          </div>
        </div>

        <!-- Area Selector (Elite V2.2 Professional) -->
        <div class="space-y-1">
          <label class="text-[10px] font-black text-slate-400 ml-1"
            >Khu vực (Tỉnh / Phường)</label
          >
          <div
            class="bg-slate-50 rounded-2xl shadow-sm border border-slate-100"
          >
            <AddressSelector
              value={{ province: editForm.province, ward: editForm.ward }}
              onSelect={handleAddressSelect}
              light={true}
            />
          </div>
        </div>

        <!-- Detailed Address -->
        <div class="space-y-1">
          <label class="text-[10px] font-black text-slate-400 ml-1"
            >Địa chỉ chi tiết</label
          >
          <input
            type="text"
            bind:value={editForm.street}
            style="color: #0f172a !important;"
            placeholder="Số nhà, tên đường..."
            class="w-full p-3.5 bg-slate-50 border border-slate-100 font-bold text-sm text-slate-900 rounded-xl outline-none focus:border-sky-500 transition-all"
          />
        </div>

        <div class="space-y-1">
          <label class="text-[10px] font-black text-slate-400 ml-1"
            >Ghi chú đơn hàng</label
          >
          <div class="overflow-hidden">
            <SimpleTiptap
              bind:content={editForm.note}
              placeholder="Ghi chú thêm cho shipper (VD: Giao giờ hành chính...)"
              minHeight="120px"
            />
          </div>
        </div>
      </div>

      <div class="pt-4 flex flex-col gap-3">
        <button
          onclick={handleSaveEdit}
          disabled={isSubmittingAction}
          class="w-full py-4 bg-slate-900 text-white font-black italic tracking-widest rounded-2xl shadow-xl shadow-slate-900/20 active:scale-95 transition-all flex items-center justify-center gap-2"
        >
          {#if isSubmittingAction}
            <div
              class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"
            ></div>
          {/if}
          Xác nhận cập nhật
        </button>
        <button
          onclick={() => (isEditing = false)}
          class="w-full py-2 text-[10px] font-black text-slate-400 tracking-widest"
          >Đóng cửa sổ</button
        >
      </div>
    </div>
  </div>
{/if}
 
{#if showVerificationDialog}
  <div
    class="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[3000] flex flex-col justify-end"
  >
    <div
      class="w-full bg-white rounded-t-[32px] p-6 pb-[calc(24px+env(safe-area-inset-bottom))] space-y-6 shadow-2xl"
      in:fly={{ y: 300, duration: 500 }}
    >
      <div class="text-center space-y-2">
        <div class="w-16 h-16 bg-sky-50 text-sky-500 rounded-full flex items-center justify-center mx-auto border border-sky-100">
           <ShieldCheck size={32} />
        </div>
        <h2 class="text-xl font-black text-slate-900 italic tracking-tighter">Xác thực danh tính</h2>
        <p class="text-[11px] font-bold text-slate-400">Vui lòng nhập số điện thoại đặt hàng để mở quyền chỉnh sửa thông tin PII.</p>
      </div>

      <div class="space-y-4">
        <div class="space-y-1">
          <label class="text-[10px] font-black text-slate-400 ml-1">Số điện thoại</label>
          <input
            type="tel"
            bind:value={verificationPhone}
            placeholder="09xx xxx xxx"
            class="w-full p-4 bg-slate-50 border border-slate-100 font-bold text-lg text-slate-900 rounded-2xl outline-none focus:border-sky-500 transition-all text-center tracking-widest"
          />
        </div>

        <button
          onclick={handleVerify}
          disabled={isSubmittingVerify}
          class="w-full py-4 bg-sky-600 text-white font-black italic tracking-widest rounded-2xl shadow-xl shadow-sky-600/20 active:scale-95 transition-all flex items-center justify-center gap-2"
        >
          {#if isSubmittingVerify}
            <div class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
          {/if}
          Xác nhận danh tính
        </button>
        <button
          onclick={() => (showVerificationDialog = false)}
          class="w-full py-2 text-[10px] font-black text-slate-400 tracking-widest"
        >Quay lại</button>
      </div>
    </div>
  </div>
{/if}
