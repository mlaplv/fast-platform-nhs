<script lang="ts">
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { authStore } from "$lib/state/authStore.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { browser } from "$app/environment";
  import { onMount, untrack } from "svelte";
  import { fade } from "svelte/transition";
  import vnDivisions from "$lib/data/vn_divisions.json";
  import SeoHead from "$lib/components/storefront/seo/SeoHead.svelte";

  import TikTokShopLoading from "$lib/components/storefront/product/TikTokShopLoading.svelte";
  import { loyaltyStore } from "$lib/state/commerce/loyalty.svelte";
  import { SHIPPING_CONFIG, LOYALTY_CONFIG } from "$lib/config/commerce";

  import GiftModal from "$lib/components/storefront/ui/GiftModal.svelte";
  import MobileGiftModal from "$lib/components/storefront/ui/MobileGiftModal.svelte";
  import { checkoutState } from "$lib/state/commerce/checkout.svelte";

  // New Desktop/Mobile modular layout components
  import CheckoutDesktop from "./components/CheckoutDesktop.svelte";
  import CheckoutMobile from "./components/CheckoutMobile.svelte";

  // Types
  import type { Voucher } from "$lib/types";
  import type { CustomItem, CustomerLookupResponse } from "$lib/types/commerce/checkout";
  import type { User, UserAddress } from "$lib/state/authStore.svelte";

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  // Immersive layout management: Hide global header/footer on mobile
  if (clientUi.isDetermined && clientUi.isMobile) {
    clientUi.isHeaderHidden = true;
    clientUi.isFooterHidden = true;
  }

  $effect(() => {
    return () => {
      clientUi.isHeaderHidden = false;
      clientUi.isFooterHidden = false;
    };
  });

  type NeuralStatus = "idle" | "verifying" | "encoding" | "submitting" | "success" | "error";
  let neuralStatus = $state<NeuralStatus>("idle");
  let isSubmitting = $derived(
    neuralStatus !== "idle" && neuralStatus !== "success" && neuralStatus !== "error"
  );
  let errorMsg = $state("");
  let invalidFields = $state(new Set<string>());
  let showCoInspectionModal = $state(false);
  let isAddressFormVisible = $state(true);

  let form = $state({
    name: authStore.user?.name || "",
    phone: authStore.user?.phone || "",
    province: "",
    ward: "",
    street: "",
    paymentMethod: "cod" as "cod" | "bank",
    shippingMethod: "standard" as "standard" | "express",
    securePackaging: true,
    pointsRedeemed: 0,
    usePoints: true, // [ELITE V2.2] Auto-Redeem Protocol: Enabled by default
    note: "",
  });

  let showNote = $state(false);
  let customItems = $state<CustomItem[]>([]);
  let showCustomItemForm = $state(false);

  // [ELITE V2.2] User Intent Tracking for Vouchers
  let userInteractedVoucherTypes = $state({ SHIPPING: false, DISCOUNT: false });

  let newCustomItem = $state<CustomItem>({
    id: "",
    name: "",
    image: "",
    price: 0,
    quantity: 1,
  });

  let standardShippingFee = $state(SHIPPING_CONFIG.STANDARD_FEE);

  async function loadDynamicShippingFee() {
    try {
      const res = await apiClient.get<{ default_fee: number }>("/api/v1/client/ctv/shipping");
      if (res && typeof res.default_fee === "number") {
        standardShippingFee = res.default_fee;
      }
    } catch (e) {
      console.error("Failed to load dynamic shipping fee", e);
    }
  }

  // [ELITE V3.1] Persistent Data & Auto-fill Logic
  onMount(async () => {
    loadDynamicShippingFee();
    if (browser) {
      const saved = localStorage.getItem("elite_checkout_draft_v2");
      if (saved) {
        try {
          const decodedDraft = decodeURIComponent(
            atob(saved)
              .split("")
              .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
              .join("")
          );
          const decrypted = JSON.parse(decodedDraft) as {
            form: typeof form;
            customItems: CustomItem[];
          };
          Object.assign(form, decrypted.form);
          customItems = decrypted.customItems || [];
          if (form.note) showNote = true;
        } catch (e: unknown) {
          console.error("Failed to load secure checkout draft", e);
        }
      }

      if (authStore.isAuthenticated) {
        try {
          const user = await apiClient.get<User>("/api/v1/client/user/profile");
          if (user) {
            authStore.syncUser(user);
            const addresses: UserAddress[] = user.extra_metadata?.addresses || [];
            const defaultAddr = addresses.find((a: UserAddress) => a.isDefault);
            const isFormEmpty = !form.province || !form.street;

            if (defaultAddr && isFormEmpty) {
              form.name = defaultAddr.name || form.name || user.name || "";
              form.phone = defaultAddr.phone || form.phone || user.phone || "";
              form.province = defaultAddr.city || "";
              form.ward = defaultAddr.ward || "";
              form.street = defaultAddr.address || "";
            } else if (!form.name || !form.phone) {
              form.name = form.name || user.name || "";
              form.phone = form.phone || user.phone || "";
            }
          }
        } catch (e) {
          console.error("Failed to fetch fresh profile for checkout", e);
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

  function getEligibleSubtotal(v: Voucher): number {
    return cartStore.getEligibleSubtotal(v);
  }

  function getVoucherSavings(v: Voucher, subtotal: number): number {
    if (!cartStore.isVoucherEligible(v)) return -1;
    const eligibleSubtotal = cartStore.getEligibleSubtotal(v);

    if (v.type === "SHIPPING") return v.value || 0;
    if (v.type === "FIXED") return Math.min(v.value || 0, eligibleSubtotal);
    if (v.type === "PERCENT") {
      const savings = (eligibleSubtotal * (v.value || 0)) / 100;
      return v.max_discount ? Math.min(savings, v.max_discount) : savings;
    }
    return 0;
  }

  // [ELITE V2.2] Auto-Stick Protocol: Synchronize with Neural Best-Deals
  $effect.pre(() => {
    const subtotal = cartStore.totalAmountWithoutDiscount;
    const vouchers = cartStore.vouchers;
    const selectedIds = cartStore.selectedVoucherIds;
    const shipInteracted = userInteractedVoucherTypes.SHIPPING;

    if (vouchers.length === 0 || subtotal <= 0) return;

    untrack(() => {
      const activeSelectedIds = [...cartStore.selectedVoucherIds];
      for (const selectedId of activeSelectedIds) {
        const v = vouchers.find((x) => x.id === selectedId);
        if (!v || !cartStore.isVoucherEligible(v)) {
          cartStore.toggleVoucher(selectedId);
        }
      }

      const currentSelectedIds = cartStore.selectedVoucherIds;
      const hasShipSelected = vouchers.some(
        (v) => v.type === "SHIPPING" && currentSelectedIds.includes(v.id)
      );

      if (!hasShipSelected && !shipInteracted) {
        const eligibleShip = vouchers.filter(
          (v) => v.type === "SHIPPING" && cartStore.isVoucherEligible(v)
        );
        if (eligibleShip.length > 0) {
          const bestShip = eligibleShip.sort(
            (a, b) => getVoucherSavings(b, subtotal) - getVoucherSavings(a, subtotal)
          )[0];
          if (bestShip && !currentSelectedIds.includes(bestShip.id)) {
            cartStore.toggleVoucher(bestShip.id);
          }
        }
      }

      const eligibleDiscounts = vouchers.filter(
        (v) => ["FIXED", "PERCENT"].includes(v.type) && cartStore.isVoucherEligible(v)
      );

      if (eligibleDiscounts.length > 0) {
        const sortedDiscounts = [...eligibleDiscounts].sort((a, b) => {
          const diff = getVoucherSavings(b, subtotal) - getVoucherSavings(a, subtotal);
          if (diff !== 0) return diff;
          if (b.is_default !== a.is_default) return b.is_default ? 1 : -1;
          return (b.priority || 0) - (a.priority || 0);
        });

        const absoluteBest = sortedDiscounts[0];
        const currentSelectedDiscount = vouchers.find(
          (v) => ["FIXED", "PERCENT"].includes(v.type) && currentSelectedIds.includes(v.id)
        );

        if (absoluteBest) {
          if (!currentSelectedDiscount) {
            cartStore.toggleVoucher(absoluteBest.id);
          } else if (currentSelectedDiscount.id !== absoluteBest.id) {
            const currentSavings = getVoucherSavings(currentSelectedDiscount, subtotal);
            const bestSavings = getVoucherSavings(absoluteBest, subtotal);
            if (bestSavings > currentSavings) {
              cartStore.toggleVoucher(absoluteBest.id);
            }
          }
        }
      }
    });
  });

  // ELITE V2.2: Dynamic Tier Notification System
  let prevTierMap = new Map<string, string>();
  $effect.pre(() => {
    for (const item of cartStore.items) {
      if (!item.selected) continue;
      const comboVariants =
        item.product?.variants?.filter((v) => v.attributes && v.attributes.combo_qty) || [];
      if (comboVariants.length === 0) continue;

      const sortedTiers = [...comboVariants].sort(
        (a, b) => Number(b.attributes?.combo_qty || 0) - Number(a.attributes?.combo_qty || 0)
      );
      const reachedTier = sortedTiers.find((v) => Number(v.attributes?.combo_qty || 0) <= item.quantity);
      const tierId = reachedTier?.id || "base";

      const lastId = prevTierMap.get(item.id);
      if (lastId && lastId !== tierId && reachedTier) {
        clientUi.showToast(
          `Chúc mừng! Bạn đã đạt mức giá ưu đãi gói ${reachedTier.attributes?.combo_qty || ""} món cho ${item.product.name}`,
          "success"
        );
      }
      prevTierMap.set(item.id, tierId);
    }
  });

  // [ELITE V2.2] STEALTH PERSISTENCE PROTOCOL
  $effect(() => {
    const currentForm = $state.snapshot(form);
    const currentItems = $state.snapshot(customItems);
    const cartItemsCount = cartStore.items.length;

    if (browser) {
      untrack(() => {
        const hasData = currentForm.province || currentForm.street || currentItems.length > 0;
        if (cartItemsCount > 0 && hasData) {
          const draft = { form: currentForm, customItems: currentItems };
          const draftStr = JSON.stringify(draft);
          const encodedDraft = btoa(
            encodeURIComponent(draftStr).replace(/%([0-9A-F]{2})/g, (_, p1) =>
              String.fromCharCode(parseInt(p1, 16))
            )
          );
          localStorage.setItem("elite_checkout_draft_v2", encodedDraft);
        } else if (cartItemsCount === 0) {
          localStorage.removeItem("elite_checkout_draft_v2");
        }
      });
    }
  });

  function addCustomItem() {
    if (!newCustomItem.name) {
      clientUi.showToast("Vui lòng nhập tên sản phẩm!", "error");
      return;
    }
    customItems.push({ ...newCustomItem, id: crypto.randomUUID() });
    newCustomItem = { id: "", name: "", image: "", price: 0, quantity: 1 };
    showCustomItemForm = false;
    clientUi.showToast("Đã thêm yêu cầu sản phẩm!", "success");
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

  const normalize = (s: string) => s.normalize("NFC").toLowerCase().trim();
  const validProvinces = $derived(
    (vnDivisions as unknown as Division[]).filter((p) => "id" in p)
  );
  const selectedProvinceData = $derived(
    validProvinces.find((p) => p.name === form.province)
  );

  const canExpress = $derived.by(() => {
    if (!selectedProvinceData?.has_express || !form.ward) return false;
    const normWard = normalize(form.ward);
    return (
      selectedProvinceData.express_supported_wards?.some(
        (w: string) => normalize(w) === normWard
      ) || false
    );
  });

  $effect.pre(() => {
    if (canExpress && form.shippingMethod !== "express") {
      form.shippingMethod = "express";
    } else if (!canExpress && form.shippingMethod === "express") {
      form.shippingMethod = "standard";
    }
  });

  const shippingFee = $derived.by(() => {
    let baseFee = standardShippingFee;
    if (form.shippingMethod === "express" && selectedProvinceData?.express_fee) {
      baseFee = selectedProvinceData.express_fee;
    }

    const hasShippingDiscount = cartStore.selectedVoucherIds.some((id: string) => {
      const v = cartStore.vouchers.find((v: Voucher) => v.id === id);
      return v?.type === "SHIPPING";
    });

    if (hasShippingDiscount) return 0;
    if (cartStore.totalAmountWithoutDiscount >= SHIPPING_CONFIG.FREE_THRESHOLD) return 0;
    return baseFee;
  });

  const deliveryEstimate = $derived.by(() => {
    if (!form.province) return null;
    if (form.shippingMethod === "express") return "Trong 2 giờ tới";

    const now = new Date();
    let minDays = 3, maxDays = 5;

    if (canExpress) {
      minDays = 1;
      maxDays = 2;
    } else if (
      ["Thành phố Đà Nẵng", "Thành phố Hải Phòng", "Thành phố Cần Thơ"].includes(form.province)
    ) {
      minDays = 2;
      maxDays = 3;
    }

    const fmt = (d: Date) => `${d.getDate()}/${d.getMonth() + 1}`;
    const minD = new Date(now.getTime() + minDays * 86400000);
    const maxD = new Date(now.getTime() + maxDays * 86400000);
    return `${fmt(minD)} - ${fmt(maxD)}`;
  });

  const originalSubtotal = $derived.by(() => {
    return cartStore.items
      .filter((i) => i.selected)
      .reduce(
        (acc: number, item) =>
          acc + (item.variant?.price ?? item.product.price ?? 0) * item.quantity,
        0
      );
  });

  const productSavings = $derived(originalSubtotal - cartStore.totalAmountWithoutDiscount);
  const totalSavings = $derived(originalSubtotal - cartStore.totalAmount);

  const availablePoints = $derived(loyaltyStore.data?.available_points || 0);
  const maxPointsAllowed = $derived(Math.floor((cartStore.totalAmount * 0.01) / 1000));
  const pointsToRedeem = $derived(form.usePoints ? Math.min(availablePoints, maxPointsAllowed) : 0);
  const pointDiscount = $derived(pointsToRedeem * 1000);
  const finalTotal = $derived(cartStore.totalAmount + shippingFee - pointDiscount);

  $effect.pre(() => {
    const shippingVoucherDiscount = (cartStore.vouchers || [])
      .filter((v) => (cartStore.selectedVoucherIds || []).includes(v.id) && v.type === "SHIPPING")
      .reduce((acc, v) => acc + v.value, 0);

    checkoutState.breakdown = {
      ...cartStore.breakdown,
      base_shipping_fee: shippingFee,
      shipping_discount: shippingVoucherDiscount,
      final_shipping_fee: Math.max(0, shippingFee - shippingVoucherDiscount),
      points_redeemed: pointsToRedeem,
      point_discount_amount: pointDiscount,
      final_payable: finalTotal,
    };
  });

  const helenAdvice = $derived.by(() => {
    const selectedItems = cartStore.items.filter((i) => i.selected);
    if (selectedItems.length === 0) return "Dạ chào Sếp, em là Helen. Hãy chọn sản phẩm Sếp muốn thanh toán để em tối ưu hóa ưu đãi nhé!";

    const advices: { gravity: number; text: string }[] = [];
    const reachedCombos: string[] = [];
    let giftMessage = "";

    for (const item of selectedItems) {
      const advice = cartStore.getPromotionAdvice(item.product, item.quantity);
      if (advice.nextTier && advice.text) {
         advices.push({ gravity: advice.gap, text: advice.text });
      } else {
         const activeVariant = cartStore.getEffectiveVariant(item.id);
         if (activeVariant) {
            const comboName = cartStore.getVariantName(item.product, activeVariant);
            if (comboName) reachedCombos.push(`"${comboName}" (${item.product.name})`);
            
            const gifts = activeVariant.attributes?.gifts?.length 
               ? activeVariant.attributes.gifts 
               : activeVariant.gifts?.length 
                  ? activeVariant.gifts 
                  : [];
            if (gifts.length > 0) {
               const giftStrings = gifts.map((g: any) => `${g.qty || g.quantity || 1} ${g.name}`);
               giftMessage += ` (Nhận ngay quà tặng: ${giftStrings.join(', ')} miễn phí!)`;
            }
         }
      }
    }

    if (advices.length > 0) {
      return advices.sort((a, b) => a.gravity - b.gravity)[0].text;
    }

    if (reachedCombos.length > 0) {
      return `Tuyệt vời! Đơn hàng đã kích hoạt thành công combo ${reachedCombos.join(", ")}${giftMessage} với ưu đãi giá cực tốt. Helen cam kết bảo vệ quyền lợi và đóng gói cẩn thận cho Sếp! ✨`;
    }

    return "Tuyệt vời! Đơn hàng của bạn đã đạt mức giá tối ưu cho tất cả liệu trình. Helen cam kết bảo vệ quyền lợi và chất lượng sản phẩm cho bạn.";
  });

  function toggleVoucher(voucher: Voucher) {
    const applicableIds = voucher.metadata_json?.applicable_product_ids || [];
    if (applicableIds && applicableIds.length > 0) {
      const hasApplicableItem = cartStore.items.some(
        (item) =>
          item.selected &&
          (applicableIds.includes(item.product.id) || applicableIds.includes(item.product.slug))
      );
      if (!hasApplicableItem) {
        clientUi.showToast("Mã giảm giá không áp dụng cho sản phẩm trong giỏ hàng!", "error");
        return;
      }
    }

    const eligibleSubtotal = getEligibleSubtotal(voucher);
    if (eligibleSubtotal < (voucher.min_spend || 0)) {
      clientUi.showToast(
        `Cần mua thêm ${formatCurrency((voucher.min_spend || 0) - eligibleSubtotal)} cho các sản phẩm áp dụng mã này!`,
        "info"
      );
      return;
    }

    if (voucher.type === "SHIPPING") userInteractedVoucherTypes.SHIPPING = true;
    else userInteractedVoucherTypes.DISCOUNT = true;

    cartStore.toggleVoucher(voucher.id);
  }

  function optimizeVouchers() {
    userInteractedVoucherTypes.SHIPPING = false;
    userInteractedVoucherTypes.DISCOUNT = false;
    cartStore.selectedVoucherIds = [];
    clientUi.showToast("Helen đã tối ưu hóa đơn hàng! ✨", "success");
  }

  async function lookupCustomer() {
    if (!authStore.isAuthenticated && form.phone.length < 10) return;
    try {
      const res = await apiClient.post<{ data: CustomerLookupResponse }>(
        "/api/v1/client/checkout/lookup",
        { phone: form.phone }
      );
      if (res.data) {
        const data = res.data;
        if (data.name && !form.name) form.name = data.name;
        const lookupData = data as Record<string, any>;
        if (lookupData.phone && !form.phone) form.phone = lookupData.phone;

        if (lookupData.address && typeof lookupData.address === "string") {
          const parts = lookupData.address.split(",").map((s: string) => s.trim());
          if (parts.length >= 3) {
            form.province = parts[parts.length - 1];
            form.ward = parts[parts.length - 2];
            form.street = parts.slice(0, parts.length - 2).join(", ");
          }
        } else if (!form.province && !form.street) {
          Object.assign(form, data);
        }
      }
    } catch (e) {
      console.error("[Checkout] Customer lookup failed:", e);
    }
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    if (isSubmitting) return;

    const newInvalid = new Set<string>();
    ["name", "phone", "province", "ward", "street"].forEach((f) => {
      if (!form[f as keyof typeof form]) newInvalid.add(f);
    });
    invalidFields = newInvalid;

    if (newInvalid.size > 0) {
      const msg = "Thông tin vận chuyển chưa hoàn thiện. Vui lòng kiểm tra các trường được đánh dấu.";
      clientUi.showToast(msg, "error");
      isAddressFormVisible = true;

      const firstInvalid = ["name", "phone", "province", "ward", "street"].find(
        (f) => newInvalid.has(f)
      );
      const fieldIdMap: Record<string, string> = {
        name: "checkout-name",
        phone: "checkout-phone",
        province: "checkout-region",
        ward: "checkout-region",
        street: "checkout-street",
      };

      if (firstInvalid) {
        const id = fieldIdMap[firstInvalid];
        setTimeout(() => {
          const el = document.getElementById(id);
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
            if (el instanceof HTMLInputElement || el instanceof HTMLButtonElement) {
              el.focus();
            }
          }
        }, 300);
      }
      return;
    }

    neuralStatus = "verifying";
    errorMsg = "";

    try {
      neuralStatus = "encoding";
      neuralStatus = "submitting";

      let ctvCode: string | null = null;
      if (typeof document !== 'undefined') {
        const match = document.cookie.match(/(?:^|; )__ctv=([^;]*)/);
        if (match) {
          ctvCode = match[1];
        }
      }

      const backendPayload = {
        items: cartStore.items
          .filter((i) => i.selected)
          .map((i) => ({
            product_id: i.product.id,
            variant_id: i.variant?.id,
            quantity: i.quantity,
            price: cartStore.getEffectiveItemPrice(i.id),
          })),
        custom_items: customItems.map((i) => ({
          name: i.name,
          image_url: i.image,
          price: i.price,
          quantity: i.quantity,
        })),
        customer_name: form.name,
        customer_phone: form.phone.replace(/[\s\.\-\+]/g, ""),
        customer_address: `${form.street}, ${form.ward}, ${form.province}`,
        total_amount: cartStore.totalAmount + shippingFee - pointsToRedeem * LOYALTY_CONFIG.POINT_VALUE,
        shipping_fee: shippingFee,
        payment_method: form.paymentMethod,
        note: form.note || null,
        voucher_ids: cartStore.selectedVoucherIds,
        points_redeemed: pointsToRedeem,
        gift_info:
          cartStore.giftInfo?.sender_name && cartStore.giftInfo?.sender_phone
            ? cartStore.giftInfo
            : null,
        ctv_code: ctvCode,
      };

      const res = await apiClient.post<{ id: string; ok: boolean; success?: boolean }>(
        "/api/v1/client/checkout/stealth",
        backendPayload
      );
      if (res.ok || res.success) {
        neuralStatus = "success";
        await clientUi.showToast("Đặt hàng thành công!", "success");
        window.location.href = `/checkout/success/${res.id}?phone=${form.phone}`;
      }
    } catch (e: unknown) {
      neuralStatus = "error";
      errorMsg = e instanceof Error ? e.message : "Lỗi đặt hàng, vui lòng thử lại!";
      clientUi.showToast(errorMsg, "error");
    }
  }

  function formatCurrency(val: number): string {
    return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(val);
  }
</script>

<SeoHead
  title="Thanh toán | {clientUi.settings?.basic_info?.site_name || clientUi.settings?.site_name || 'SmartShop'}"
  robots="noindex, nofollow"
/>

<div class="checkout-viewport min-h-screen bg-[#fafafa]">
  {#if !clientUi.isHydrated}
    <TikTokShopLoading variant="grid" />
  {:else if !clientUi.isMobile}
    <CheckoutDesktop
      bind:form
      bind:customItems
      bind:showCustomItemForm
      bind:newCustomItem
      {invalidFields}
      {neuralStatus}
      {errorMsg}
      {shippingFee}
      {helenAdvice}
      {deliveryEstimate}
      bind:showNote
      bind:isAddressFormVisible
      {canExpress}
      {selectedProvinceData}
      bind:showCoInspectionModal
      {availablePoints}
      {pointsToRedeem}
      {originalSubtotal}
      {productSavings}
      {totalSavings}
      {toggleVoucher}
      {optimizeVouchers}
      {addCustomItem}
      {removeCustomItem}
      {handleSubmit}
      {lookupCustomer}
    />
  {:else}
    <CheckoutMobile
      bind:form
      bind:customItems
      bind:showCustomItemForm
      bind:newCustomItem
      {invalidFields}
      {neuralStatus}
      {errorMsg}
      {shippingFee}
      {helenAdvice}
      {deliveryEstimate}
      bind:showNote
      bind:isAddressFormVisible
      {canExpress}
      {selectedProvinceData}
      bind:showCoInspectionModal
      {availablePoints}
      {pointsToRedeem}
      {finalTotal}
      {isSubmitting}
      {toggleVoucher}
      {optimizeVouchers}
      {addCustomItem}
      {removeCustomItem}
      {handleSubmit}
      {lookupCustomer}
    />
  {/if}
</div>

{#if clientUi.isMobile}
  <MobileGiftModal onClose={() => {}} />
{:else}
  <GiftModal onClose={() => {}} />
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
