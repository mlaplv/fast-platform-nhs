<script lang="ts">
  import { page } from "$app/state";
  import { fade, fly, scale, slide } from "svelte/transition";
  import Gift from "@lucide/svelte/icons/gift";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { formatCurrency, formatDate } from "$lib/utils/format";
  import SuccessMobile from "$lib/components/mobile/sections/SuccessMobile.svelte";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import vnDivisions from "$lib/data/vn_divisions.json";
  import SimpleTiptap from "$lib/components/storefront/ui/SimpleTiptap.svelte";
  import SearchableCheckoutSelect from "$lib/components/storefront/ui/SearchableCheckoutSelect.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { browser } from "$app/environment";
  import { authStore } from "$lib/state/authStore.svelte";

  let { data } = $props<{ data: { isMobile: boolean } }>();
  const ui = getClientUi();

  // Standardize Layout: Sync header/footer with Elite V3.2 Protocol
  $effect.pre(() => {
    if (ui.isMobile) {
      ui.isHeaderHidden = false; // Show header like product detail
      ui.isFooterHidden = true;
    } else {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    }
    return () => {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  const orderId = page.params.id || "";
  const cartStore = getCartStore();

  // Elite V2.2: Order Status Roadmap
  import type { OrderDetail } from "$lib/types/commerce/order";

  interface VnDivision {
    id: string;
    name: string;
    code: string;
    wards: string[];
    has_express?: boolean;
    express_fee?: number;
    express_supported_wards?: string[];
  }

  const STATUS_STEPS = [
    { key: "PENDING", label: "Tiếp nhận", icon: "📝" },
    { key: "PACKED", label: "Bảo mật", icon: "🛡️" },
    { key: "SHIPPING", label: "Vận chuyển", icon: "🚚" },
    { key: "DELIVERED", label: "Thành công", icon: "🎁" },
  ];

  function getStepIndex(status: string) {
    if (status === "CANCELLED") return -1;
    const idx = STATUS_STEPS.findIndex((s) => s.key === status);
    return idx === -1 ? 0 : idx;
  }

  // Elite V2.2: Retrieve phone from URL or LocalStorage to persist unlock!
  const getSanitizedPhone = () => {
    const raw = page.url.searchParams.get("phone") || 
               (typeof localStorage !== "undefined" ? localStorage.getItem(`order_verify_${orderId}`) : null);
    return (raw && raw !== "undefined" && raw !== "null") ? raw : null;
  };

  const sanitize = (val: any) => {
    if (!val || val === "undefined" || val === "null") return null;
    return val;
  };

  const phoneParam = sanitize(getSanitizedPhone());
  const isTrackingMode = !!phoneParam;

  let order = $state<OrderDetail | null>(null);
  let isLoading = $state(true);
  let isSubmittingAction = $state(false);

  let activePhone = $state(phoneParam || "");
  let isLocked = $state(false);
  let verificationPhone = $state("");

  // Elite V2.2 Toast System!
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

  function copyOrderId() {
    if (typeof navigator !== "undefined") {
      navigator.clipboard.writeText(orderId);
      showToast("Đã sao chép mã đơn hàng");
    }
  }

  // Edit State
  let isEditing = $state(false);
  let editForm = $state({
    name: "",
    phone: "",
    province: "",
    ward: "",
    street: "",
    note: "",
  });

  const validProvinces = $derived.by(() => {
    const rawData = (vnDivisions as any).default || vnDivisions;
    return (rawData as unknown as VnDivision[]).filter((p) => p.id);
  });

  const unifiedOptions = $derived.by(() => {
    return validProvinces
      .flatMap((p) =>
        (p.wards || []).map((w) => {
          const wardName =
            typeof w === "string" ? w : (w as { name: string }).name;
          return `${wardName}, ${p.name}`;
        }),
      )
      .sort((a, b) => a.localeCompare(b, "vi"));
  });

  let unifiedValue = $state("");

  $effect(() => {
    if (editForm.ward && editForm.province) {
      const combined = `${editForm.ward}, ${editForm.province}`;
      if (unifiedValue !== combined) unifiedValue = combined;
    }
  });

  function handleUnifiedChange() {
    if (unifiedValue.includes(", ")) {
      const parts = unifiedValue.split(", ");
      // Elite V2.2: Intelligent Area Mapping
      editForm.ward = parts[0];
      editForm.province = parts[parts.length - 1];
    } else if (!unifiedValue) {
      editForm.ward = "";
      editForm.province = "";
    }
  }

  function parseAddress(fullAddress: string) {
    if (!fullAddress || fullAddress.includes("***"))
      return { province: "", ward: "", street: fullAddress || "" };

    const parts = fullAddress.split(",").map((p) => p.trim());
    
    // Elite V2.2: Adaptive Hierarchy Resolver (R2026 Strategy)
    if (parts.length >= 4) {
      // Format: Street, Ward, District, Province
      // We prioritize the Ward (index -3) for the selector mapping
      return {
        province: parts[parts.length - 1],
        ward: parts[parts.length - 3], 
        street: parts.slice(0, parts.length - 3).join(", ") + ", " + parts[parts.length - 2],
      };
    } else if (parts.length === 3) {
      // Format: Street, Ward/District, Province
      return {
        province: parts[parts.length - 1],
        ward: parts[parts.length - 2],
        street: parts[0],
      };
    }
    
    return { province: "", ward: "", street: fullAddress };
  }

  onMount(async () => {
    cartStore.clearCart();
    // Immediate Security Sync
    if (typeof localStorage !== "undefined") {
      const raw = sanitize(localStorage.getItem(`order_verify_${orderId}`));
      if (raw) {
        activePhone = raw;
      }
    }
    await fetchOrder();
  });

  async function fetchOrder(overridePhone?: string) {
    isLoading = true;
    const phoneToUse = sanitize(
      overridePhone ||
      activePhone ||
      (authStore.isAuthenticated ? authStore.user?.phone : null)
    );

    try {
      console.log(`[Elite-Sync] Fetching order ${orderId} (Phone: ${phoneToUse || "None"})`);
      const res = await apiClient.get<OrderDetail>(
        `/api/v1/client/orders/${orderId}`,
        {
          params: phoneToUse ? { phone: phoneToUse, _t: Date.now() } : { _t: Date.now() },
        },
      );
      if (res) {
        order = res;
        console.log("[Elite-Sync] Order data received:", {
          id: order.id,
          name: order.customerName,
          is_trusted: (order as any).is_trusted_device,
          status: order.status
        });
        isLocked = false;
        // Persist the unlock!
        if (phoneToUse && typeof localStorage !== "undefined") {
          localStorage.setItem(`order_verify_${orderId}`, phoneToUse);
          activePhone = phoneToUse;
        }
      }
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      if (
        e.status === 400 &&
        e.message?.toLowerCase().includes("số điện thoại")
      ) {
        // Elite V2.2: Intelligent Auth Bridge
        // If logged in and has phone, try automatic unlock once!
        if (
          authStore.isAuthenticated &&
          authStore.user?.phone &&
          !overridePhone
        ) {
          await fetchOrder(authStore.user.phone);
          return;
        }
        isLocked = true;
      } else {
        showToast(e.message || "Lỗi tải dữ liệu", "error");
      }
    } finally {
      isLoading = false;
    }
  }

  async function handleVerify() {
    if (!verificationPhone) return;
    try {
      isLoading = true;
      // Elite V4.0: Secure Device Binding
      await apiClient.post(`/api/v1/client/orders/${orderId}/verify-full`, {
        phone: verificationPhone
      }, { params: { _t: Date.now() } });
      
      // Cookie is now set, re-fetch to get unmasked data
      await fetchOrder(verificationPhone);
      isLocked = false;
      
      // Elite V4.0: Seamless Transition - Open form immediately after unlock
      setTimeout(() => startEditing(), 100);
    } catch (err: any) {
      showToast(err.message || "Xác thực thất bại", "error");
    } finally {
      isLoading = false;
    }
  }

  function startEditing() {
    if (!order) return;
    
    // Elite V4.0: Competition Shield
    // If data is masked, force a Full Identity check before opening the form
    const isMasked = order.customer_name?.includes("*") || order.customer_address?.includes("*") || (order as any).customerName?.includes("*");
    
    if (isMasked) {
      isLocked = true;
      verificationPhone = activePhone || "";
      showToast("Vui lòng xác thực danh tính để mở quyền chỉnh sửa", "error");
      return;
    }

    const o = order as any;
    const cName = o.customer_name || o.customerName || o.name_masked || "";
    const cPhone = o.customer_phone || o.customerPhone || "";
    const cAddress = o.customer_address || o.customerAddress || o.address_masked || "";

    const addrParts = parseAddress(cAddress);
    const meta = o?.orderMetadata || o?.order_metadata;

    editForm = {
      name: cName,
      phone: cPhone,
      province: addrParts.province,
      ward: addrParts.ward,
      street: addrParts.street,
      note:
        o?.customer_note ||
        o?.customerNote ||
        order.note ||
        (meta?.customer_note as string) ||
        (meta?.note as string) ||
        "",
    };

    // Explicitly sync area selector with hierarchical fallback
    if (editForm.ward && editForm.province) {
      unifiedValue = `${editForm.ward}, ${editForm.province}`;
    } else {
      unifiedValue = "";
    }

    isEditing = true;
  }

  async function handleCancel() {
    isConfirmCancelOpen = false;
    isSubmittingAction = true;
    if (!activePhone || activePhone === "undefined" || activePhone === "null") {
      showToast("Vui lòng xác thực số điện thoại trước khi hủy", "error");
      isLocked = true;
      isSubmittingAction = false;
      return;
    }

    try {
      console.log(`[Elite-Sync] Cancelling order ${orderId}...`);
      const res = await apiClient.post<OrderDetail>(
        `/api/v1/client/orders/${orderId}/cancel`,
        {},
        { params: { phone: activePhone, _t: Date.now() } },
      );
      if (res) {
        order = res;
        console.log("[Elite-Sync] Cancellation response received:", order);
      }
      showToast("Đã hủy đơn hàng thành công");
    } catch (err: unknown) {
      const e = err as { message?: string };
      showToast(e.message || "Không thể hủy đơn hàng", "error");
    } finally {
      isSubmittingAction = false;
    }
  }

  async function handleSaveEdit() {
    isSubmittingAction = true;
    if (!activePhone || activePhone === "undefined" || activePhone === "null") {
      showToast("Vui lòng xác thực số điện thoại trước khi lưu", "error");
      isLocked = true;
      isSubmittingAction = false;
      return;
    }

    try {
      console.log("[Elite-Sync] Saving edit. Previous data:", {
        name: order.customerName,
        address: order.customerAddress
      });
      const res = await apiClient.patch<OrderDetail>(
        `/api/v1/client/orders/${orderId}`,
        {
          customer_name: editForm.name,
          customer_phone: editForm.phone,
          customer_address: `${editForm.street}, ${editForm.ward}, ${editForm.province}`,
          note: editForm.note,
          order_metadata: {
            ...((order as any).orderMetadata || order.order_metadata || {}),
            customer_note: editForm.note,
          },
        },
        { params: { phone: activePhone, _t: Date.now() } },
      );
      if (res) {
        order = res;
        console.log("[Elite-Sync] Save success. Updated data:", {
          name: order.customerName,
          address: order.customerAddress
        });
      }
      showToast("Đã cập nhật thông tin thành công");
      isEditing = false;
    } catch (err: unknown) {
      const e = err as { message?: string };
      showToast(e.message || "Lỗi cập nhật dữ liệu", "error");
    } finally {
      isSubmittingAction = false;
    }
  }

  const stepIdx = $derived(getStepIndex(order?.status ?? ""));
  let isConfirmCancelOpen = $state(false);

  // Elite V2.2: Reactive Financial Computations
  const subtotal = $derived(
    order?.items?.reduce((acc, it) => acc + (it.total_price || 0), 0) ?? 0,
  );
  const voucherDiscount = $derived(
    Number(order?.order_metadata?.voucher_discount || 0),
  );
  const comboDiscount = $derived(
    Number(order?.order_metadata?.combo_discount || 0),
  );
  const totalSavings = $derived(voucherDiscount + comboDiscount);
  const finalTotal = $derived(
    order?.total_amount ||
      (order as any)?.total ||
      Math.max(0, subtotal - totalSavings),
  );
  const displayNote = $derived.by(() => {
    // Elite V2.2: Dual-Key Resolver (CamelCase API vs SnakeCase Schema)
    const meta = (order as any)?.orderMetadata || (order as any)?.order_metadata;
    return meta?.customer_note || (order as any)?.customer_note || order?.note || "";
  });

  $effect(() => {
    if (displayNote) {
      console.log("LOG customer_note:", displayNote);
    }
  });
</script>

<svelte:head>
  <title
    >{isTrackingMode ? "Tra cứu đơn hàng" : "Đặt hàng thành công"} | osmo</title
  >
</svelte:head>

{#if browser}
  {#if data.isMobile && order}
    <SuccessMobile bind:order {orderId} isLookup={isTrackingMode} />
  {:else}
    <div class="min-h-screen bg-[#fafafa] text-slate-900 pb-20 pt-4 md:pt-10">
      <div class="max-w-[1240px] mx-auto px-4">
        {#if isLoading}
          <div class="py-20 flex flex-col items-center gap-6" in:fade>
            <div
              class="w-16 h-16 border-4 border-slate-100 border-t-[#ee4d2d] rounded-full animate-spin"
            ></div>
            <h1
              class="text-xl font-black text-slate-900 italic tracking-widest"
            >
              Đang kết nối hệ thống...
            </h1>
          </div>
        {:else if isLocked}
          <div class="max-w-md mx-auto" in:fly={{ y: 20, duration: 800 }}>
            <div
              class="bg-white p-10 shadow-2xl border-t-4 border-amber-500 text-center space-y-8"
            >
              <div
                class="w-20 h-20 bg-amber-50 text-amber-500 rounded-full flex items-center justify-center mx-auto border border-amber-100"
              >
                <svg
                  class="w-10 h-10"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  /></svg
                >
              </div>
              <h2 class="text-2xl font-black text-slate-900 italic">
                Cửa ngõ bảo mật
              </h2>
              <div class="space-y-4">
                <input
                  type="tel"
                  bind:value={verificationPhone}
                  placeholder="Nhập Số điện thoại..."
                  class="w-full px-6 py-4 bg-slate-50 border-2 border-slate-100 focus:border-amber-500 outline-none text-center text-lg font-black"
                  onkeydown={(e) => e.key === "Enter" && handleVerify()}
                />
                <button
                  onclick={handleVerify}
                  class="w-full py-4 bg-slate-900 text-white font-black italic tracking-widest"
                  >Xác thực →</button
                >
              </div>
            </div>
          </div>
        {:else if order}
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-7 space-y-4">
              <div class="flex items-center justify-between mb-2">
                <h1 class="text-2xl font-black italic text-slate-900">
                  {isTrackingMode ? "Tra cứu đơn hàng" : "Đặt hàng thành công"}
                </h1>
                  <div class="flex items-center gap-2">
                    {#if order.status === "CANCELLED"}
                      <div class="px-3 py-1 bg-red-50 border border-red-200 text-red-500 text-[10px] font-black italic rounded-lg">
                        ĐÃ HỦY
                      </div>
                    {/if}
                    <div
                      class="flex items-center gap-2 cursor-pointer group"
                      onclick={copyOrderId}
                    >
                      <span class="text-[10px] font-black text-slate-400"
                        >Mã đơn:</span
                      >
                      <span
                        class="text-xs font-black text-slate-900 bg-white px-3 py-1 border border-slate-100 italic rounded-lg shadow-sm"
                        >#{orderId.slice(-6)}</span
                      >
                    </div>
                    {#if order && order.status === "PENDING"}
                      <button
                        onclick={() => (isConfirmCancelOpen = true)}
                        class="text-[9px] font-black text-slate-300 italic tracking-wider hover:text-red-400 transition-colors"
                      >
                        (Hủy đơn hàng)
                      </button>
                    {/if}
                  </div>
              </div>

              {#if order.status === "CANCELLED"}
                <!-- Cancellation Banner -->
                <div class="bg-white p-8 shadow-sm border-t-4 border-red-500 overflow-hidden relative">
                   <div class="absolute -right-4 -top-4 opacity-5 pointer-events-none">
                     <svg class="w-32 h-32 text-red-500" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"/></svg>
                   </div>
                   <div class="flex flex-col items-center text-center space-y-4">
                     <div class="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center text-3xl shadow-inner border border-red-100">
                       ✕
                     </div>
                     <div class="space-y-1">
                       <h3 class="text-xl font-black text-slate-900 italic tracking-widest uppercase">Đơn hàng đã được hủy</h3>
                       <p class="text-sm font-bold text-slate-400 italic">Trạng thái: Vô hiệu hóa</p>
                     </div>
                     {#if order.cancellation_reason}
                        <div class="px-6 py-3 bg-slate-50 border border-slate-100 rounded-xl max-w-md">
                          <p class="text-xs font-black text-slate-400 italic uppercase mb-1">Lý do hủy:</p>
                          <p class="text-sm font-bold text-slate-700 leading-relaxed italic">"{order.cancellation_reason}"</p>
                        </div>
                     {/if}
                   </div>
                </div>
              {:else}
                <!-- Timeline -->
                <div class="bg-white p-8 shadow-sm border-t-4 border-sky-500">
                  <div class="max-w-md mx-auto flex flex-col gap-6">
                    <div class="flex items-center">
                      {#each STATUS_STEPS as step, i}
                        <div class="relative w-12 h-12">
                          <div
                            class="w-full h-full rounded-full flex items-center justify-center text-xl border-2 transition-all duration-500
                              {stepIdx > i
                              ? 'bg-emerald-50 border-emerald-500 text-emerald-600'
                              : stepIdx === i
                                ? 'bg-sky-50 border-sky-500 text-sky-600 scale-110 shadow-lg'
                                : 'bg-slate-50 border-slate-100 text-slate-300'}"
                          >
                            {step.icon}
                          </div>
                        </div>
                        {#if i < STATUS_STEPS.length - 1}
                          <div
                            class="flex-1 h-1 mx-2 bg-slate-100 rounded-full overflow-hidden"
                          >
                            <div
                              class="h-full bg-emerald-500 transition-all duration-1000"
                              style:width={stepIdx > i
                                ? "100%"
                                : stepIdx === i
                                  ? "50%"
                                  : "0%"}
                            ></div>
                          </div>
                        {/if}
                      {/each}
                    </div>
                    <div class="flex justify-between items-start px-1">
                      {#each STATUS_STEPS as step, i}
                        <span
                          class="text-[9px] font-black tracking-widest {stepIdx >=
                          i
                            ? 'text-slate-900'
                            : 'text-slate-300'}">{step.label}</span
                        >
                      {/each}
                    </div>
                  </div>
                  {#if !isTrackingMode}
                    <div
                      class="mt-8 p-4 bg-sky-50 border border-sky-100 text-center"
                    >
                      <p class="text-[10px] text-sky-700 font-bold italic">
                        Tài khoản tự động: <span class="font-black"
                          >{order.customer_phone}</span
                        >
                      </p>
                    </div>
                  {/if}
                </div>
              {/if}

              <!-- Info -->
              <div class="bg-white p-8 shadow-sm border-t-4 border-slate-900">
                <div
                  class="flex items-center justify-between mb-8 border-b border-slate-50 pb-4"
                >
                  <h3 class="text-sm font-black text-slate-900 italic">
                    Thông tin nhận hàng
                  </h3>
                  {#if !isEditing && order.status === "PENDING"}
                    <button
                      onclick={startEditing}
                      class="text-[10px] font-black text-sky-600 italic"
                      >Chỉnh sửa</button
                    >
                  {/if}
                </div>
                {#if !isEditing}
                  <div class="grid md:grid-cols-2 gap-8">
                    <div class="space-y-4">
                      <div>
                        <span
                          class="text-[9px] font-black text-slate-400 block mb-1"
                          >Họ tên:</span
                        >
                        <span class="text-sm font-bold"
                          >{order.name_masked ||
                            order.customer_name ||
                            "Khách hàng"}</span
                        >
                      </div>
                      <div>
                        <span
                          class="text-[9px] font-black text-slate-400 block mb-1"
                          >Số điện thoại:</span
                        >
                        <span class="text-sm font-bold"
                          >{order.customer_phone}</span
                        >
                      </div>
                    </div>
                      <div>
                        <span
                          class="text-[9px] font-black text-slate-400 block mb-1"
                          >Địa chỉ:</span
                        >
                        <span
                          class="text-xs font-bold text-slate-600 leading-snug break-all whitespace-normal block"
                          >{order.address_masked || order.customer_address}</span
                        >
                      </div>
                  </div>
                {:else}
                  <div class="space-y-4">
                    <div class="grid md:grid-cols-2 gap-4">
                      <div>
                        <span
                          class="text-[9px] font-black text-slate-400 block mb-2"
                          >Họ tên</span
                        >
                        <input
                          type="text"
                          bind:value={editForm.name}
                          class="w-full px-4 py-3 bg-slate-50 border border-slate-100 font-bold text-sm text-slate-900 outline-none focus:border-slate-300 transition-colors"
                          placeholder="Nguyễn Văn A"
                        />
                      </div>
                      <div>
                        <span
                          class="text-[9px] font-black text-slate-400 block mb-2"
                          >Số điện thoại</span
                        >
                        <input
                          type="tel"
                          bind:value={editForm.phone}
                          class="w-full px-4 py-3 bg-slate-50 border border-slate-100 font-bold text-sm text-slate-900 outline-none focus:border-slate-300 transition-colors"
                          placeholder="0901234567"
                        />
                      </div>
                    </div>

                    <div>
                      <span
                        class="text-[9px] font-black text-slate-400 block mb-2"
                        >Khu vực (Tỉnh / Quận / Huyện / Xã)</span
                      >
                      <SearchableCheckoutSelect
                        bind:value={unifiedValue}
                        options={unifiedOptions}
                        placeholder="Gõ tên xã, quận, tỉnh để tìm nhanh..."
                        onChange={handleUnifiedChange}
                      />
                    </div>

                    <div>
                      <span
                        class="text-[9px] font-black text-slate-400 block mb-2"
                        >Địa chỉ cụ thể</span
                      >
                      <textarea
                        bind:value={editForm.street}
                        rows="2"
                        class="w-full px-4 py-3 bg-slate-50 border border-slate-100 font-bold text-sm text-slate-900 outline-none focus:border-slate-300 transition-colors resize-none"
                        placeholder="Số nhà, tên đường..."
                      ></textarea>
                    </div>

                    <div>
                      <span
                        class="text-[9px] font-black text-slate-400 block mb-2"
                        >Ghi chú đơn hàng</span
                      >
                      <div class="overflow-hidden">
                        <SimpleTiptap
                          bind:content={editForm.note}
                          placeholder="Ghi chú thêm cho shipper..."
                          minHeight="120px"
                        />
                      </div>
                    </div>

                    <div
                      class="flex gap-4 pt-4 border-t border-slate-50 justify-end"
                    >
                      <button
                        onclick={() => (isEditing = false)}
                        class="px-6 py-2 text-[10px] font-black text-slate-400 tracking-widest hover:text-slate-600 transition-colors"
                        >Hủy bỏ</button
                      >
                      <button
                        onclick={handleSaveEdit}
                        disabled={isSubmittingAction}
                        class="px-8 py-3 bg-slate-900 hover:bg-slate-800 transition-colors text-white text-[10px] font-black tracking-widest disabled:opacity-50"
                      >
                        {isSubmittingAction ? "Đang lưu..." : "Lưu thông tin"}
                      </button>
                    </div>
                  </div>
                {/if}

                {#if !isEditing && displayNote}
                  <div
                    class="mt-8 pt-6 border-t border-slate-50 flex items-start gap-3"
                  >
                    <MessageSquare
                      class="w-5 h-5 text-slate-300 mt-0.5 shrink-0"
                    />
                    <div class="flex-1 min-w-0">
                      <span
                        class="text-[9px] font-black text-slate-500 block mb-1"
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

            <!-- RIGHT -->
            <div class="lg:col-span-5 space-y-6">
              <div
                class="bg-white p-6 shadow-sm border-t-4 border-[#ee4d2d] sticky top-20"
              >
                <div
                  class="flex justify-between items-center mb-6 pb-4 border-b border-slate-50"
                >
                  <h3 class="text-sm font-black text-slate-900 italic">
                    Giỏ hàng
                  </h3>
                  <span class="text-[10px] font-black text-[#ee4d2d]"
                    >SL: {order.items.length}</span
                  >
                </div>
                <div class="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                  {#each order.items as item}
                    <div class="flex items-center gap-4">
                      <div
                        class="w-14 h-14 bg-slate-50 border border-slate-100 rounded-sm flex items-center justify-center overflow-hidden italic"
                      >
                        {#if item.image_url}<img
                            src={item.image_url}
                            alt={item.name}
                            class="w-full h-full object-cover"
                          />{:else}📦{/if}
                      </div>
                      <div class="flex-1 min-w-0">
                        <p
                          class="text-xs font-black text-slate-900 mb-1 leading-snug"
                        >
                          {item.name}
                        </p>
                        <p class="text-[9px] text-slate-400 font-bold italic">
                          {item.quantity || item.qty || 1} × {formatCurrency(
                            item.unit_price || 0,
                          )}
                        </p>
                      </div>
                      <div class="text-right">
                        <span class="text-sm font-black italic"
                          >{formatCurrency(item.total_price || 0)}</span
                        >
                      </div>
                    </div>
                  {/each}
                </div>

                {#if order.order_metadata?.custom_requests && order.order_metadata.custom_requests.length > 0}
                  <div
                    class="pt-6 mt-6 border-t border-dashed border-slate-100"
                  >
                    <p class="text-[9px] font-black text-slate-500 italic mb-4">
                      Yêu cầu bổ sung
                    </p>
                    {#each order.order_metadata.custom_requests as c_item}
                      <div
                        class="bg-amber-50/20 p-3 border border-amber-100/50 flex items-center gap-3 mb-2"
                      >
                        <div
                          class="w-10 h-10 bg-white border border-amber-100 flex items-center justify-center text-lg"
                        >
                          {#if c_item.image_url}<img
                              src={c_item.image_url}
                              alt={c_item.name}
                              class="w-full h-full object-cover"
                            />{:else}🧪{/if}
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-[10px] font-black leading-snug">
                            {c_item.name}
                          </p>
                          <p
                            class="text-[8px] font-bold text-slate-500 italic mt-0.5"
                          >
                            Đang chờ báo giá
                          </p>
                        </div>
                      </div>
                    {/each}
                  </div>
                {/if}

                <div class="mt-6 pt-6 border-t border-slate-100 space-y-3">
                  <div
                    class="flex justify-between text-[11px] font-black text-slate-400 italic"
                  >
                    <span>Tạm tính:</span>
                    <span>{formatCurrency(subtotal)}</span>
                  </div>

                  {#if comboDiscount > 0}
                    <div
                      class="flex justify-between text-[11px] font-black text-emerald-500 italic"
                    >
                      <span>Ưu đãi Combo:</span>
                      <span>-{formatCurrency(comboDiscount)}</span>
                    </div>
                  {/if}

                  {#if voucherDiscount > 0}
                    <div
                      class="flex justify-between text-[11px] font-black text-pink-500 italic"
                    >
                      <span>Voucher giảm giá:</span>
                      <span>-{formatCurrency(voucherDiscount)}</span>
                    </div>
                  {/if}

                  <div
                    class="flex justify-between text-[11px] font-black text-emerald-500 italic"
                  >
                    <span>Vận chuyển:</span>
                    <span>Miễn phí</span>
                  </div>

                  <!-- 🧧 VIRAL SAVINGS BADGE -->
                  {#if totalSavings > 0}
                    <div
                      class="relative py-3 px-4 bg-gradient-to-r from-emerald-500/10 to-transparent border-l-2 border-emerald-500 mt-4 overflow-hidden group"
                      in:fly={{ x: -20, delay: 600 }}
                    >
                      <div class="flex items-center gap-2">
                        <div class="p-1 bg-emerald-500 text-white rounded-full">
                          <Sparkles size={10} class="animate-pulse" />
                        </div>
                        <span
                          class="text-[10px] font-black text-emerald-600 italic tracking-wider"
                        >
                          Chúc mừng! Bạn đã tiết kiệm được {formatCurrency(
                            totalSavings,
                          )}
                        </span>
                      </div>
                      <div
                        class="absolute inset-0 bg-gradient-to-r from-white/0 via-white/30 to-white/0 -translate-x-full animate-[shimmer_2s_infinite]"
                      ></div>
                    </div>
                  {/if}

                  <div class="flex justify-between items-end pt-4">
                    <span class="text-[10px] font-black text-slate-900 italic"
                      >Tổng thanh toán:</span
                    >
                    <span
                      class="text-3xl font-black text-[#ee4d2d] italic tabular-nums"
                      >{formatCurrency(finalTotal)}</span
                    >
                  </div>
                </div>

                {#if order.order_metadata?.gift_info}
                  <div class="pt-6 mt-6 border-t border-slate-100 space-y-4">
                    <div
                      class="bg-pink-50/50 p-4 border border-pink-100/50 italic space-y-1"
                    >
                      <p class="text-[9px] font-black text-pink-500 mb-2">
                        Quà tặng
                      </p>
                      <p class="text-[11px] font-bold text-slate-600">
                        "{order.order_metadata.gift_info.message}"
                      </p>
                      <p class="text-[8px] font-black text-pink-400">
                        Từ: {order.order_metadata.gift_info.sender_name}
                      </p>
                    </div>
                  </div>
                {/if}

                <!-- 🚀 [ELITE V2.2] Thành viên Elite WOW MOMENT -->
                <div
                  class="w-full bg-[#fcfbf9] border border-[#f5f1e8] p-6 rounded-none relative overflow-hidden group shadow-sm transition-all duration-500 hover:shadow-md"
                  in:fly={{ y: 20, delay: 800 }}
                >
                  <div
                    class="absolute -right-4 -bottom-4 w-16 h-16 text-luxury-copper/10 rotate-12 group-hover:scale-125 transition-transform duration-700"
                  >
                    <Gift class="w-full h-full" />
                  </div>
                  <div class="relative z-10 flex items-center gap-4">
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
                        <span
                          class="w-1 h-1 bg-amber-500 rounded-full animate-ping"
                        ></span>
                      </h4>
                      <p
                        class="text-[13px] font-serif italic text-stone-700 leading-none"
                      >
                        Bạn vừa tích được <span
                          class="text-amber-600 font-black"
                          >+{Math.floor(finalTotal / 100000)} điểm</span
                        >
                      </p>
                      <p
                        class="text-[8px] text-stone-400 font-bold mt-2 opacity-60"
                      >
                        Điểm sẽ khả dụng sau khi giao hàng thành công
                      </p>
                    </div>
                  </div>
                </div>

                <div class="pt-2 space-y-3">
                  <a
                    href="/"
                    class="block w-full py-4 bg-slate-900 text-white text-center text-xs font-black italic tracking-widest"
                    >Tiếp tục mua sắm →</a
                  >

                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
{/if}

{#if isConfirmCancelOpen}
  <div
    class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-6"
    style:z-index={Z_INDEX_CLIENT.MODAL_OVERLAY}
    transition:fade
  >
    <div
      class="w-full max-w-sm bg-white shadow-2xl border-t-4 border-red-500 p-10 text-center space-y-6"
      in:scale
    >
      <h3 class="text-xl font-black italic">Xác nhận hủy đơn?</h3>
      <div class="flex flex-col gap-3">
        <button
          onclick={handleCancel}
          class="py-4 bg-red-500 text-white font-black italic tracking-widest"
          >Hủy đơn hàng</button
        >
        <button
          onclick={() => (isConfirmCancelOpen = false)}
          class="py-2 text-[10px] font-black text-slate-400 tracking-widest"
          >Quay lại</button
        >
      </div>
    </div>
  </div>
{/if}

<div
  class="fixed bottom-8 right-8 flex flex-col gap-4 pointer-events-none"
  style:z-index={Z_INDEX_CLIENT.TOAST}
>
  {#each toasts as toast (toast.id)}
    <div
      in:fly={{ x: 50 }}
      out:fade
      class="px-8 py-4 bg-white shadow-2xl border-l-4 {toast.type === 'success'
        ? 'border-emerald-500'
        : 'border-red-500'} flex items-center gap-4 pointer-events-auto"
    >
      <span class="text-[10px] font-black text-slate-900 italic"
        >{toast.message}</span
      >
    </div>
  {/each}
</div>
