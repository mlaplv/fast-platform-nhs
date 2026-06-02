<script lang="ts">
  import { onMount, tick } from "svelte";
  import vnDivisions from "$lib/data/vn_divisions.json";
  import { fade, fly, scale, blur } from "svelte/transition";
  import { cubicOut, elasticOut, backOut } from "svelte/easing";
  import type { Review, ProductMetadata } from "$lib/types";
  import { getShopStore } from "$lib/state/commerce/shop.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import EditableWrapper from "$lib/components/admin/EditableWrapper.svelte";
  import "./VerifiedReviews.css";

  import { lightLiveEdit } from "$lib/state/commerce/liveEditState.svelte";
  import { authStore } from "$lib/state/authStore.svelte";

  const shopStore = getShopStore();
  const ui = getClientUi();

  interface Props {
    initialReviews?: Review[];
  }
  let { initialReviews = [] }: Props = $props();

  const product = $derived(
    lightLiveEdit.isEditMode && lightLiveEdit.dirtyProduct
      ? lightLiveEdit.dirtyProduct
      : shopStore.product,
  );
  const metadata = $derived(product?.metadata || {});

  interface ReviewApiResponse {
    id: string | number;
    customer_name: string;
    customer_phone?: string;
    customer_location?: string;
    rating: number;
    content: string;
    created_at: string;
  }

  let realReviews = $state<Review[]>(
    initialReviews.length > 0 ? initialReviews : [],
  );
  let isLoading = $state(initialReviews.length === 0);

  const stripTags = (h: string) =>
    h ? h.replace(/<[^>]*>?/gm, "").trim() : "";
  const legacyParts = $derived(metadata.reviews_headline?.split("//") || []);
  const h1 = $derived(
    metadata.reviews_headline_1 ||
      stripTags(legacyParts[0]) ||
      "Đánh giá thực tế",
  );
  const h2 = $derived(
    metadata.reviews_headline_2 ||
      stripTags(legacyParts[1]) ||
      "Miccosmo Beppin Body Virgin White Serum",
  );

  const subheadline = $derived(
    metadata?.reviews_subheadline ||
      "Kiểm chứng công thức số 1 từ Nhật Bản. Thấm nhanh, không bết dính. Hiệu quả rõ rệt sau 2 tuần. Đừng bỏ lỡ siêu phẩm Best-seller!",
  );
  const trustScore = $derived(metadata?.reviews_trust_score || "4.9/5");
  const countText = $derived(
    product?.orderCountText ||
      metadata?.reviews_count_text ||
      (product?.orderCount || product?.order_count
        ? `${(product.orderCount || product.order_count).toLocaleString()}+ LƯỢT MUA`
        : ""),
  );

  // Elite V2.2: Live FOMO Pulse Logic
  let liveViewers = $state(Math.floor(Math.random() * (45 - 12 + 1)) + 12);
  // Elite V2.2: Memory Leak Protection
  const timers = new Set<ReturnType<typeof setTimeout>>();
  function clearTimers() {
    timers.forEach((t) => {
      clearTimeout(t);
      clearInterval(t);
    });
    timers.clear();
  }

  onMount(() => {
    const interval = setInterval(() => {
      const delta = Math.random() > 0.5 ? 1 : -1;
      liveViewers = Math.max(8, Math.min(64, liveViewers + delta));
    }, 5000);
    timers.add(interval);

    return () => {
      clearTimers();
    };
  });

  const labels = $derived({
    trust_score:
      (metadata.reviews_trust_score as string) || trustScore || "4.9/5",
    count_text:
      (metadata.reviews_count_text as string) ||
      countText ||
      (product?.orderCount || product?.order_count
        ? `${(product.orderCount || product.order_count).toLocaleString()}+ lượt mua`
        : ""),
    hud_feedback:
      (metadata.reviews_hud_feedback as string) ||
      "Hệ thống // Phản hồi thực tế",
    label_verified:
      (metadata.reviews_label_verified as string) || "Đã xác thực",
    label_compliant:
      (metadata.reviews_label_compliant as string) || "Đã mua hàng",
    label_store_verified:
      (metadata.reviews_label_store_verified as string) ||
      `Xác thực bởi ${ui.settings?.contact?.name || "Cửa hàng"}`,
    label_secure_encryption:
      (metadata.reviews_label_secure_encryption as string) ||
      "Mã hóa bảo mật [AES-256]",
    label_secure_gate:
      (metadata.reviews_label_secure_gate as string) || "Cổng bảo mật // V2.2",
    cta_write:
      (metadata.reviews_cta_write as string) || "Viết đánh giá của bạn",
    form_title:
      (metadata.reviews_form_title as string) ||
      "Module // Real_Voice_Analysis_V2",
    form_name: (metadata.reviews_form_name_label as string) || "Danh tính",
    form_phone: (metadata.reviews_form_phone_label as string) || "Liên hệ",
    form_location: (metadata.reviews_form_location_label as string) || "Vị trí",
    form_rating:
      (metadata.reviews_form_rating_label as string) || "Đánh giá sao",
    form_content:
      (metadata.reviews_form_content_label as string) || "Trải nghiệm thực tế",
    form_placeholder:
      (metadata.reviews_form_placeholder_content as string) ||
      "Hãy cho chúng tôi biết cảm nhận của bạn... *",
    form_cta:
      (metadata.reviews_form_cta_submit as string) || "Xác nhận gửi đánh giá",
    success_title:
      (metadata.reviews_form_success_title as string) ||
      "Gửi đánh giá thành công!",
    success_msg: (metadata.reviews_form_success_msg ||
      "Hệ thống đã ghi nhận phản hồi của bạn. Đánh giá sẽ hiển thị sau khi được quản trị viên kiểm duyệt.") as string,
  });

  let showFormModal = $state<boolean>(false);
  let isLocationOpen = $state<boolean>(false);

  let nameRef = $state<HTMLInputElement>();
  let phoneRef = $state<HTMLInputElement>();
  let contentRef = $state<HTMLTextAreaElement>();

  let locationSelected = $state<string>("");
  let ratingSelected = $state<number>(5);
  let hoverRating = $state<number>(0);
  let isSubmitting = $state<boolean>(false);
  let showSuccess = $state<boolean>(false);
  let contentLen = $state<number>(0);
  let websiteUrl = $state<string>(""); // BOT_HONEYPOT
  let locationSearch = $state("");

  // Elite Toast System
  let toastMessage = $state<string>("");
  let toastType = $state<"success" | "error" | "info">("info");
  let showToast = $state(false);

  function triggerToast(
    msg: string,
    type: "success" | "error" | "info" = "info",
  ) {
    toastMessage = msg;
    toastType = type;
    showToast = true;
    const t = setTimeout(() => {
      showToast = false;
    }, 4000);
    timers.add(t);
  }

  interface VNDivision {
    name: string;
    code?: string;
    id?: string;
  }

  const locations = (vnDivisions as VNDivision[])
    .slice(1)
    .map((d) =>
      d.name.replace("Thành phố ", "TP. ").replace("Tỉnh ", "").toUpperCase(),
    );

  function normalize(str: string) {
    return str
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/Đ/g, "D")
      .toLowerCase();
  }

  const filteredLocations = $derived.by(() => {
    let query = normalize(locationSearch);
    if (query === "hcm") query = "ho chi minh";
    if (query === "hn") query = "ha noi";

    return locations.filter((loc) => {
      const normalizedLoc = normalize(loc);
      return (
        normalizedLoc.includes(query) ||
        (query === "ho chi minh" && normalizedLoc.includes("hcm"))
      );
    });
  });

  interface ReviewSubmission {
    entity_type: "PRODUCT" | "SHOP";
    entity_id: string | number;
    customer_name: string;
    customer_phone: string;
    customer_location: string;
    rating: number;
    content: string;
  }

  async function fetchRealReviews(): Promise<void> {
    if (!product?.id) return;
    isLoading = true;
    try {
      const res = await fetch(
        `/api/v1/client/reviews?entity_type=PRODUCT&entity_id=${product.id}&status=APPROVED`,
      );
      if (res.ok) {
        const data: { items: ReviewApiResponse[] } = await res.json();
        realReviews = (data.items || []).map((r) => {
          const cleanName = r.customer_name
            ? r.customer_name.split("(")[0].split("-")[0].trim()
            : "Ẩn danh";

          return {
            id: r.id,
            name: cleanName,
            phone: r.customer_phone
              ? "0" + r.customer_phone.slice(-9, -3) + "***"
              : "09x****xxx",
            location: r.customer_location || "Việt Nam",
            rating: r.rating,
            content: r.content,
            initial: cleanName.charAt(0).toUpperCase(),
            created_at: r.created_at,
          };
        });
      }
    } catch (e) {
      console.error("Master Sync Error (Reviews):", e);
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    if (product?.id && realReviews.length === 0) {
      fetchRealReviews();
    }
  });

  // Elite V2.2: Body Scroll Lock System
  $effect(() => {
    if (!authStore.isAuthenticated && showFormModal) {
      showFormModal = false;
    }

    if (showFormModal) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  });

  const setRating = (r: number) => {
    ratingSelected = r;
  };

  const submitReview = async (e: Event) => {
    e.preventDefault();
    if (isSubmitting) return;

    const name = nameRef?.value || "";
    const phone = phoneRef?.value || "";
    const content = contentRef?.value || "";

    if (
      name.length < 2 ||
      phone.length < 10 ||
      content.length < 10 ||
      !locationSelected
    ) {
      triggerToast(
        "Vui lòng nhập đầy đủ Danh tính, Số điện thoại và Nội dung.",
        "error",
      );
      return;
    }

    if (websiteUrl) {
      // SILENT_REJECT: Likely a bot
      console.warn("Security Error: Honeypot triggered.");
      return;
    }

    isSubmitting = true;
    try {
      const res = await fetch("/api/v1/client/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          entity_type: "PRODUCT",
          entity_id: product?.id || "",
          customer_name: name,
          customer_phone: phone,
          customer_location: locationSelected,
          rating: ratingSelected,
          content: content,
        }),
      });

      if (res.ok) {
        showSuccess = true;
        // Confetti start here
        const t = setTimeout(() => {
          showFormModal = false;
          showSuccess = false;
          if (nameRef) nameRef.value = "";
          if (phoneRef) phoneRef.value = "";
          if (contentRef) contentRef.value = "";
          contentLen = 0;
          locationSelected = "";
          ratingSelected = 5;
        }, 5000);
        timers.add(t);
      } else {
        triggerToast("Hệ thống bận, vui lòng thử lại sau.", "error");
      }
    } catch (error) {
      triggerToast("Không thể kết nối máy chủ.", "error");
    } finally {
      isSubmitting = false;
    }
  };

  let scrollContainer = $state<HTMLElement>();
  const scrollNext = () => {
    if (scrollContainer) {
      scrollContainer.scrollBy({
        left: scrollContainer.clientWidth,
        behavior: "smooth",
      });
    }
  };
  const scrollPrev = () => {
    if (scrollContainer) {
      scrollContainer.scrollBy({
        left: -scrollContainer.clientWidth,
        behavior: "smooth",
      });
    }
  };
</script>

<section class="reviews-viewport relative overflow-visible">
  <div
    class="reviews-container container mx-auto px-6 max-w-6xl relative z-surface"
  >
    <!-- Header Section -->
    <div class="text-center mb-0" in:fade>
      <!-- FLOATING HUD: No layout space occupied -->
      <div
        class="absolute top-[-4vh] left-1/2 -translate-x-1/2 elite-status-pill !bg-transparent border-none shadow-none opacity-0 animate-fade-in pointer-events-none"
        style="animation-delay: 0.2s; --status-color: #ef4444;"
      >
        <div class="elite-dot-container">
          <span class="elite-status-dot"></span>
        </div>
        <span
          class="text-[10px] font-black text-red-500 tracking-[0.3em] font-mono whitespace-nowrap"
          >LIVE_ACTIVITY: {liveViewers} KHÁCH ĐANG XEM ĐÁNH GIÁ</span
        >
      </div>

      <div
        class="max-w-4xl mx-auto text-center"
        style:margin-bottom="calc(var(--headline-mb) * 0.5)"
      >
        <h2
          class="elite-session-headline mb-4 text-center flex flex-col items-center"
        >
          <EditableWrapper
            path="metadata.reviews_headline_1"
            type="text"
            label="SỬA TIÊU ĐỀ 1"
            class="inline"
            as="span"
          >
            <span
              class="block text-[11px] md:text-[12px] font-black tracking-[0.4em] text-white/40 mb-4"
              >{h1}</span
            >
          </EditableWrapper>
          <EditableWrapper
            path="metadata.reviews_headline_2"
            type="text"
            label="SỬA TIÊU ĐỀ 2"
            class="inline"
            as="span"
          >
            <span class="block">{h2}</span>
          </EditableWrapper>
        </h2>
      </div>

      <p
        class="section-description text-white/40 text-base md:text-lg max-w-3xl mx-auto leading-relaxed mb-10 text-center"
      >
        <EditableWrapper
          path="metadata.reviews_subheadline"
          type="text"
          label="SỬA MÔ TẢ ĐÁNH GIÁ"
          as="span"
        >
          {product?.metadata?.reviews_subheadline || subheadline}
        </EditableWrapper>
      </p>

      <div class="flex flex-col items-center gap-8">
        <div
          class="trust-indicator-elite inline-flex flex-col sm:flex-row items-center gap-6 px-10 py-6 bg-white/[0.02] backdrop-blur-3xl rounded-[2rem] border border-white/10 shadow-[0_40px_100px_rgba(0,0,0,0.5),inset_0_0_20px_rgba(255,255,255,0.02)]"
        >
          <div
            class="flex items-center gap-6 border-b sm:border-b-0 sm:border-r border-white/10 pb-4 sm:pb-0 sm:pr-8"
          >
            <div class="flex flex-col items-center sm:items-start gap-1">
              <span
                class="text-[9px] font-black text-white/30 tracking-[0.3em] font-mono"
                >PRECISION_RATING</span
              >
              <div class="flex items-center gap-4">
                <EditableWrapper
                  path="metadata.reviews_trust_score"
                  value={labels.trust_score}
                  label="SỬA ĐIỂM TIN CẬY"
                >
                  <span
                    class="text-3xl font-black text-white tracking-tighter italic"
                    >{labels.trust_score}</span
                  >
                </EditableWrapper>
                <div class="flex items-center gap-1">
                  {#each [1, 2, 3, 4, 5] as star}
                    <svg
                      class="w-4 h-4 {star <= 5
                        ? 'text-luxury-gold drop-shadow-[0_0_10px_rgba(232,213,176,0.6)]'
                        : 'text-white/5'}"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
                      />
                    </svg>
                  {/each}
                </div>
              </div>
            </div>
          </div>

          <div class="flex flex-col items-center sm:items-start gap-1">
            <span
              class="text-[9px] font-black text-white/30 tracking-[0.3em] font-mono"
              >GLOBAL_VOLUME</span
            >
            <EditableWrapper
              path="metadata.reviews_count_text"
              value={labels.count_text}
              type="text"
              label="SỬA LƯỢT ĐÁNH GIÁ"
            >
              <span class="text-xl font-bold text-white tracking-wider"
                >{labels.count_text}</span
              >
            </EditableWrapper>
          </div>

          <div class="w-px h-10 bg-white/10 hidden sm:block"></div>

          <div class="flex items-center gap-4">
            <div
              class="w-10 h-10 rounded-full border border-luxury-sakura/20 flex items-center justify-center bg-luxury-sakura/5"
            >
              <svg
                class="w-5 h-5 text-luxury-sakura"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                /></svg
              >
            </div>
            <div class="flex flex-col">
              <span class="text-[8px] font-black text-white/40 tracking-[0.2em]"
                >ELITE_PROTECTED</span
              >
              <span
                class="text-[10px] font-black text-luxury-sakura tracking-widest"
                >VERIFIED SERVICE</span
              >
            </div>
          </div>
        </div>

        <button
          onclick={() => {
            if (!authStore.isAuthenticated) {
              ui.openLogin(() => (showFormModal = true));
            } else {
              showFormModal = true;
            }
          }}
          class="pulse-btn px-12 py-5 bg-luxury-sakura/10 border border-luxury-sakura/30 rounded-full text-luxury-sakura text-[11px] font-black tracking-[0.4em] hover:bg-luxury-sakura/20 hover:border-luxury-sakura/50 transition-all active:scale-95 shadow-[0_0_50px_rgba(193,143,126,0.1)] group flex items-center gap-4"
        >
          <svg
            class="w-4 h-4 transition-transform group-hover:rotate-12"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
          <EditableWrapper
            path="metadata.reviews_cta_write"
            type="text"
            label="SỬA NÚT CTA"
            class="inline"
            as="span"
          >
            <span class="relative" style="z-index: var(--z-surface);"
              >{labels.cta_write}</span
            >
          </EditableWrapper>
          <div
            class="absolute inset-0 bg-luxury-sakura/5 blur-2xl group-hover:blur-3xl transition-all"
          ></div>
        </button>
      </div>
    </div>

    <!-- Reviews Grid -->
    <div class="bento-hub-frame relative group">
      <div class="reviews-layout relative z-surface">
        <div class="flex items-center justify-between mt-6 mb-10 px-2">
          <div
            class="elite-status-pill !py-1 !px-4 !bg-luxury-sakura/5 text-luxury-sakura border-luxury-sakura/20 animate-fade-in"
          >
            <div class="elite-dot-container">
              <span class="elite-status-dot"></span>
            </div>
            <EditableWrapper
              path="metadata.reviews_hud_feedback"
              type="text"
              label="SỬA NHÃN HUD"
              class="inline"
              as="span"
            >
              <span class="text-luxury-sakura tracking-widest"
                >{labels.hud_feedback.replace("//", "•")}</span
              >
            </EditableWrapper>
          </div>

          <!-- iPad Mini / Tablet Navigation Controls (Elite Delicate) -->
          <div
            class="tablet-nav-controls flex items-center gap-2"
            class:show-desktop={realReviews.length > 3}
          >
            <button
              onclick={scrollPrev}
              class="nav-delicate group/nav p-2 transition-all active:scale-90"
              aria-label="Previous"
            >
              <svg
                class="w-6 h-6 text-white/10 group-hover/nav:text-luxury-sakura transition-all"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1"
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>

            <div class="w-px h-3 bg-white/5 mx-1"></div>

            <button
              onclick={scrollNext}
              class="nav-delicate group/nav p-2 transition-all active:scale-90"
              aria-label="Next"
            >
              <svg
                class="w-6 h-6 text-white/10 group-hover/nav:text-luxury-sakura transition-all"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>
        </div>

        <div
          class="reviews-scroll-wrapper scrollbar-hide w-full"
          class:grid-mode={realReviews.length <= 3}
          class:slider-mode={realReviews.length > 3}
          bind:this={scrollContainer}
        >
          {#if isLoading && realReviews.length === 0}
            <div class="flex flex-col items-center justify-center p-24 gap-6">
              <div
                class="w-12 h-12 border-2 border-luxury-sakura/20 border-t-luxury-sakura rounded-full animate-spin"
              ></div>
              <span
                class="text-luxury-sakura/40 font-mono text-[10px] tracking-[0.4em]"
                >Syncing_Real_Voices...</span
              >
            </div>
          {:else if realReviews.length === 0}
            <div
              class="flex flex-col items-center justify-center p-24 gap-4 opacity-30"
            >
              <svg
                class="w-12 h-12 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                /></svg
              >
              <span class="text-[10px] font-mono tracking-widest"
                >No_Signal_Detected</span
              >
            </div>
          {:else}
            {#each realReviews as review, i}
              <div
                class="review-card group/card snap-center"
                in:fly={{ y: 20, delay: i * 100, duration: 800 }}
              >
                <div
                  class="review-header flex items-start justify-between gap-4 mb-4"
                >
                  <div class="flex items-center gap-4">
                    <div
                      class="avatar-circle relative group-hover/card:scale-110 transition-transform duration-500"
                    >
                      {review.initial}
                      <div
                        class="absolute inset-0 bg-luxury-sakura/20 blur-lg rounded-full opacity-0 group-hover/card:opacity-100 transition-opacity"
                      ></div>
                    </div>
                    <div class="user-meta flex flex-col min-w-0">
                      <div class="flex items-center gap-2 mb-0.5">
                        <span
                          class="user-name font-black text-base text-white/95 tracking-tight truncate"
                          >{review.name}</span
                        >
                        <span
                          class="text-[10px] text-white/20 font-mono italic shrink-0 leading-none"
                          >{review.phone}</span
                        >
                        <div
                          class="verified-badge-mini text-luxury-sakura shrink-0"
                        >
                          <svg
                            class="w-3.5 h-3.5"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fill-rule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                              clip-rule="evenodd"
                            />
                          </svg>
                        </div>
                      </div>
                      <div class="flex items-center gap-2">
                        <span
                          class="text-[8px] text-white/30 tracking-[0.2em] font-black font-mono leading-none"
                          >{review.location}</span
                        >
                      </div>
                      <div class="flex items-center gap-0.5 mt-1.5">
                        {#each [0, 1, 2, 3, 4] as starIdx}
                          <svg
                            class="w-3 h-3 {starIdx < (review.rating || 5)
                              ? 'text-luxury-gold drop-shadow-[0_0_5px_rgba(232,213,176,0.4)]'
                              : 'text-white/5'}"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
                            />
                          </svg>
                        {/each}
                      </div>
                    </div>
                  </div>
                </div>

                <div class="review-content relative overflow-hidden">
                  <div
                    class="text-slate-200 leading-relaxed text-base italic font-medium tracking-tight"
                  >
                    {#if review.content.includes("<")}
                      {@html review.content}
                    {:else}
                      "{review.content}"
                    {/if}
                  </div>
                </div>

                <div
                  class="clinical-verify mt-auto pt-4 flex items-center justify-between border-t border-white/5 mt-5"
                >
                  <div class="compliance-tag flex items-center gap-2">
                    <div
                      class="w-2 h-2 rounded-full border border-white/20"
                    ></div>
                    <EditableWrapper
                      path="metadata.reviews_label_compliant"
                      type="text"
                      label="SỬA TAG COMPLIANT"
                      class="inline"
                      as="span"
                    >
                      <span
                        class="text-[8px] font-black text-white/20 tracking-[0.3em]"
                        >{labels.label_compliant}</span
                      >
                    </EditableWrapper>
                  </div>
                  <div
                    class="buy-check flex items-center gap-2.5 px-3.5 py-2 bg-luxury-sakura/10 rounded-xl border border-luxury-sakura/20 shadow-[0_0_15px_rgba(193,143,126,0.1)] transition-all hover:border-luxury-sakura/40"
                  >
                    <div class="relative">
                      <svg
                        class="w-4 h-4 text-luxury-sakura"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="3"
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <div
                        class="absolute inset-0 bg-luxury-sakura blur-md opacity-20"
                      ></div>
                    </div>
                    <div class="flex flex-col">
                      <span
                        class="text-[7px] font-black text-luxury-sakura/50 tracking-[0.2em] leading-none mb-0.5"
                        >AUTH_STATUS</span
                      >
                      <EditableWrapper
                        path="metadata.reviews_label_store_verified"
                        type="text"
                        label="SỬA TAG VERIFIED"
                        class="inline"
                        as="span"
                      >
                        <span
                          class="text-[9px] font-black text-luxury-sakura tracking-widest leading-none"
                          >{labels.label_store_verified}</span
                        >
                      </EditableWrapper>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- Decorative Background Elements -->
  <div
    class="absolute -top-64 -right-64 w-[600px] h-[600px] bg-luxury-sakura/10 blur-[150px] rounded-full mix-blend-overlay animate-pulse"
  ></div>
  <div
    class="absolute -bottom-64 -left-64 w-[600px] h-[600px] bg-luxury-gold/5 blur-[150px] rounded-full mix-blend-overlay animate-pulse"
    style:animation-delay="2s"
  ></div>

  <!-- Dynamic Line Wave Divider - High Impact Edition! -->
  <div class="wave-container">
    <svg
      viewBox="0 0 1440 320"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient
          id="wave-gradient-reviews"
          x1="0%"
          y1="0%"
          x2="100%"
          y2="0%"
        >
          <stop offset="0%" stop-color="#C18F7E" stop-opacity="0" />
          <stop offset="50%" stop-color="#E8D5B0" stop-opacity="1" />
          <stop offset="100%" stop-color="#C18F7E" stop-opacity="0" />
        </linearGradient>
      </defs>
      <path
        class="wave-line opacity-20"
        d="M0,160 C320,300 420,20 720,160 C1020,300 1120,20 1440,160"
      />
      <path
        class="wave-line"
        d="M0,200 C320,340 420,60 720,200 C1020,340 1120,60 1440,200"
      />
      <path
        class="wave-line secondary"
        d="M0,240 C320,100 420,380 720,240 C1020,100 1120,380 1440,240"
      />
      <path
        class="wave-line opacity-30"
        d="M0,100 C320,240 420,-40 720,100 C1020,240 1120,-40 1440,100"
      />
    </svg>
  </div>
</section>

{#if showFormModal}
  <div
    class="modal-overlay fixed inset-0 flex items-center justify-center p-4 backdrop-blur-2xl z-modal"
    transition:fade={{ duration: 400 }}
    onclick={(e) => {
      if (e.target === e.currentTarget && !isSubmitting) showFormModal = false;
    }}
  >
    <div
      class="modal-content-frame w-full max-w-[900px] mt-20 sm:mt-0 bg-slate-950/95 border border-white/10 rounded-3xl sm:rounded-[3.5rem] shadow-[0_0_120px_rgba(0,0,0,0.9)] overflow-hidden relative"
      transition:fly={{ y: 50, duration: 800, easing: cubicOut }}
    >
      <!-- Confetti Effect Layer -->
      {#if showSuccess}
        <div
          class="absolute inset-0 pointer-events-none"
          style="z-index: var(--z-header);"
        >
          {#each Array(40) as _, i}
            <div
              class="confetti-particle absolute"
              style:--left="{Math.random() * 100}%"
              style:--delay="{Math.random() * 2}s"
              style:--duration="{2 + Math.random() * 3}s"
              style:--color={["#C18F7E", "#E8D5B0", "#E3B5A4", "#fff"][
                Math.floor(Math.random() * 4)
              ]}
              style:--size="{4 + Math.random() * 6}px"
              style:--x="{(Math.random() - 0.5) * 400}px"
            ></div>
          {/each}
        </div>
      {/if}

      <button
        onclick={() => (showFormModal = false)}
        disabled={isSubmitting}
        class="absolute top-4 right-4 sm:top-8 sm:right-8 w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-all active:scale-90 z-20"
      >
        <svg
          class="w-5 h-5 text-white/50"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>

      <div class="review-form-container p-5 sm:p-10 md:p-12">
        <div class="form-truth-layout relative">
          {#if showSuccess}
            <div
              class="success-overlay absolute inset-0 bg-slate-950/95 backdrop-blur-3xl flex flex-col items-center justify-center text-center p-12 z-50 rounded-[3.5rem]"
              transition:fade
            >
              <div
                class="w-32 h-32 bg-luxury-sakura/20 rounded-full flex items-center justify-center mb-10 border-2 border-luxury-sakura/40 shadow-[0_0_60px_rgba(193,143,126,0.3)]"
                transition:scale={{ duration: 1000, easing: elasticOut }}
              >
                <svg
                  class="w-16 h-16 text-luxury-sakura"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="4"
                  transition:fly={{ y: 20, duration: 600 }}
                  ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M5 13l4 4L19 7"
                  /></svg
                >
              </div>
              <h4
                class="text-5xl font-black text-white tracking-tighter mb-6 italic"
                in:fly={{ y: 20, duration: 800 }}
              >
                {labels.success_title}
              </h4>
              <p
                class="text-white/60 text-sm max-w-md font-bold tracking-[0.2em] leading-relaxed"
                in:fly={{ y: 20, delay: 200, duration: 800 }}
              >
                {labels.success_msg}
              </p>

              <div
                class="mt-12 w-full max-w-xs h-1 bg-white/5 rounded-full overflow-hidden"
              >
                <div class="h-full bg-luxury-sakura animate-progress"></div>
              </div>
            </div>
          {/if}

          <div
            class="flex flex-col sm:flex-row items-center justify-between mb-4 sm:mb-8 pb-3 sm:pb-6 border-b border-white/5 sm:pr-10 gap-2 sm:gap-4"
          >
            <div
              class="elite-status-pill !py-1 !px-4 !bg-luxury-sakura/5 text-luxury-sakura border-luxury-sakura/10"
            >
              <div
                class="elite-dot-container"
                style="--status-color: var(--luxury-gold);"
              >
                <span class="elite-status-dot"></span>
              </div>
              <span
                class="text-[10px] font-black tracking-[0.2em] whitespace-nowrap"
                >{labels.form_title}</span
              >
            </div>
            <div
              class="text-[8px] sm:text-[9px] font-black tracking-[0.1em] sm:tracking-[0.2em] text-white/20 font-mono italic"
            >
              {labels.label_secure_encryption}
            </div>
          </div>

          <form onsubmit={submitReview} class="space-y-4 sm:space-y-8">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-8">
              <div class="space-y-4 sm:space-y-6">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <div class="space-y-1.5">
                    <label
                      for="review-name"
                      class="text-[9px] font-black text-white/20 tracking-[0.2em] ml-2"
                      >{labels.form_name}</label
                    >
                    <input
                      id="review-name"
                      type="text"
                      bind:this={nameRef}
                      placeholder="Họ và Tên *"
                      class="input-liquid px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/10 focus:border-luxury-sakura/50 transition-all outline-none"
                    />
                  </div>
                  <div class="space-y-1.5">
                    <label
                      for="review-phone"
                      class="text-[9px] font-black text-white/20 tracking-[0.2em] ml-2"
                      >{labels.form_phone}</label
                    >
                    <input
                      id="review-phone"
                      type="tel"
                      bind:this={phoneRef}
                      placeholder="Số điện thoại *"
                      class="input-liquid px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/10 focus:border-luxury-sakura/50 transition-all outline-none"
                    />
                  </div>
                </div>

                <div class="space-y-8">
                  <div class="space-y-3 relative">
                    <label
                      for="review-location"
                      class="text-[11px] font-black text-white/30 tracking-[0.3em] ml-4"
                      >{labels.form_location}</label
                    >
                    <button
                      id="review-location"
                      type="button"
                      onclick={() => (isLocationOpen = !isLocationOpen)}
                      class="input-liquid flex items-center justify-between px-6 py-5 rounded-2xl bg-white/5 border border-white/10 text-white transition-all outline-none {isLocationOpen
                        ? 'border-luxury-sakura/50'
                        : ''}"
                    >
                      <span
                        class={locationSelected
                          ? "text-white font-bold"
                          : "text-white/20 text-[11px] font-bold tracking-[0.1em]"}
                      >
                        {locationSelected || "Chọn Tỉnh/Thành"}
                      </span>
                      <svg
                        class="w-5 h-5 text-white/30 transition-transform {isLocationOpen
                          ? 'rotate-180'
                          : ''}"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M19 9l-7 7-7-7"
                        />
                      </svg>
                    </button>

                    {#if isLocationOpen}
                      <div
                        class="absolute top-[calc(100%+8px)] left-0 w-full bg-slate-950 border border-white/20 rounded-2xl shadow-[0_40px_100px_rgba(0,0,0,1)] z-50 overflow-hidden flex flex-col"
                        transition:fly={{
                          y: -10,
                          duration: 300,
                          easing: cubicOut,
                        }}
                        onmouseleave={() => (isLocationOpen = false)}
                      >
                        <!-- Search Header -->
                        <div
                          class="px-6 py-4 border-b border-white/10 bg-white/[0.03] flex items-center gap-4"
                        >
                          <div class="flex-1 relative">
                            <input
                              type="text"
                              bind:value={locationSearch}
                              placeholder="TÌM KIẾM VỊ TRÍ..."
                              class="w-full bg-transparent text-[11px] font-black tracking-[0.2em] text-white outline-none placeholder:text-white/20"
                              autofocus
                            />
                          </div>
                          <button
                            type="button"
                            onclick={() => {
                              isLocationOpen = false;
                              locationSearch = "";
                            }}
                            class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-white/30 hover:text-white transition-all hover:rotate-90"
                          >
                            <svg
                              class="w-4 h-4"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2.5"
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        </div>

                        <div
                          class="max-h-[350px] overflow-y-auto custom-scrollbar scrollbar-hide"
                          onwheel={(e) => e.stopPropagation()}
                          ontouchmove={(e) => e.stopPropagation()}
                        >
                          {#if filteredLocations.length > 0}
                            {#each filteredLocations as loc}
                              <button
                                type="button"
                                onclick={() => {
                                  locationSelected = loc;
                                  isLocationOpen = false;
                                  locationSearch = "";
                                }}
                                class="w-full px-8 py-5 text-left text-[11px] text-white/60 hover:text-white hover:bg-luxury-sakura/10 transition-all border-b border-white/5 last:border-0 font-bold tracking-[0.2em] flex items-center justify-between group"
                              >
                                {loc}
                                {#if locationSelected === loc}
                                  <div
                                    class="w-2 h-2 rounded-full bg-luxury-sakura shadow-[0_0_15px_rgba(193,143,126,0.8)]"
                                  ></div>
                                {/if}
                              </button>
                            {/each}
                          {:else}
                            <div
                              class="py-16 text-center text-[10px] font-black text-white/20 tracking-[0.3em] italic"
                            >
                              NO_RESULTS_FOUND
                            </div>
                          {/if}
                        </div>
                      </div>
                    {/if}
                  </div>

                  <div class="space-y-4">
                    <div class="px-4">
                      <label
                        id="rating-label"
                        class="text-[11px] font-black text-white/30 tracking-[0.3em] whitespace-nowrap"
                        >{labels.form_rating}</label
                      >
                    </div>
                    <div
                      role="group"
                      aria-labelledby="rating-label"
                      class="rating-picker-viral flex items-center justify-center gap-4 sm:gap-6 py-3 sm:py-4 rounded-2xl border border-white/10 bg-white/[0.02] backdrop-blur-xl relative group/picker shadow-[inset_0_0_20px_rgba(255,255,255,0.02)]"
                      onmouseleave={() => (hoverRating = 0)}
                    >
                      {#each Array(5) as _, i}
                        {@const active = (hoverRating || ratingSelected) > i}
                        {@const selected = ratingSelected > i}
                        <button
                          type="button"
                          onclick={() => setRating(i + 1)}
                          onmouseenter={() => (hoverRating = i + 1)}
                          aria-label="Rate {i + 1} stars"
                          class="star-viral-btn relative transition-all duration-500 {active
                            ? 'scale-110'
                            : 'scale-100 opacity-20'}"
                          style="z-index: var(--z-surface);"
                        >
                          <svg
                            class="w-6 h-6 sm:w-8 sm:h-8 transition-all duration-700 {active
                              ? 'drop-shadow-[0_0_20px_rgba(232,213,176,0.8)]'
                              : ''}"
                            viewBox="0 0 24 24"
                            fill="none"
                          >
                            <defs>
                              <linearGradient
                                id="star-grad-viral-{i}"
                                x1="0%"
                                y1="0%"
                                x2="100%"
                                y2="100%"
                              >
                                <stop offset="0%" stop-color="#fbbf24" />
                                <stop offset="100%" stop-color="#C18F7E" />
                              </linearGradient>
                            </defs>
                            <path
                              d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
                              fill={active
                                ? `url(#star-grad-viral-${i})`
                                : "currentColor"}
                            />
                            {#if selected}
                              <circle
                                cx="12"
                                cy="12"
                                r="11"
                                stroke="#E8D5B0"
                                stroke-width="0.5"
                                class="animate-ping opacity-30"
                              />
                            {/if}
                          </svg>
                        </button>
                      {/each}
                    </div>
                  </div>
                </div>

                <!-- BOT_HONEYPOT: HIDDEN FIELD (R82) -->
                <div class="hidden" aria-hidden="true">
                  <input
                    type="text"
                    name="website_url"
                    bind:value={websiteUrl}
                    tabindex="-1"
                    autocomplete="off"
                  />
                </div>
              </div>

              <div class="space-y-4">
                <label
                  for="review-content"
                  class="text-[11px] font-black text-white/30 tracking-[0.3em] ml-4"
                  >{labels.form_content}</label
                >
                <div class="relative h-full pb-0 sm:pb-4">
                  <textarea
                    id="review-content"
                    bind:this={contentRef}
                    oninput={() => (contentLen = contentRef?.value.length || 0)}
                    placeholder={labels.form_placeholder}
                    class="input-liquid resize-none h-[120px] sm:h-[180px] lg:h-[calc(100%-40px)] w-full px-6 py-4 rounded-2xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/10 focus:border-luxury-sakura/50 transition-all outline-none scrollbar-hide"
                  ></textarea>
                  <div
                    class="char-counter absolute bottom-3 right-5 sm:bottom-8 sm:right-6 font-mono text-[8px] text-white/15 tracking-widest"
                  >
                    {contentLen}/5000
                  </div>
                </div>
              </div>
            </div>

            <div class="pt-2 sm:pt-6">
              <button
                type="submit"
                disabled={isSubmitting}
                class="submit-glow-btn w-full py-4 sm:py-6 flex flex-col items-center justify-center gap-1 group/btn relative overflow-hidden rounded-2xl sm:rounded-[2rem] bg-luxury-sakura text-slate-950 transition-all hover:bg-luxury-gold active:scale-[0.98]"
              >
                {#if isSubmitting}
                  <div class="flex items-center gap-3">
                    <div
                      class="w-5 h-5 border-2 border-slate-950/20 border-t-slate-950 rounded-full animate-spin"
                    ></div>
                    <span class="text-sm font-black tracking-[0.4em]"
                      >PROCESSING_DATA...</span
                    >
                  </div>
                {:else}
                  <span
                    class="text-xl font-black tracking-[0.5em] transition-transform group-hover/btn:scale-105 duration-700"
                    >{labels.form_cta}</span
                  >
                  <div
                    class="text-[9px] font-black tracking-[0.2em] opacity-40"
                  >
                    {labels.label_secure_gate}
                  </div>
                {/if}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Premium Toast Notification -->
{#if showToast}
  <div
    class="fixed top-12 left-1/2 -translate-x-1/2 z-toast"
    transition:fly={{ y: -50, duration: 600, easing: cubicOut }}
  >
    <div
      class="px-8 py-4 {toastType === 'error'
        ? 'bg-red-500/20 text-red-400 border-red-500/40'
        : 'bg-luxury-sakura/10 text-white border-luxury-sakura/20'} backdrop-blur-3xl border rounded-full shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex items-center gap-4"
    >
      {#if toastType === "error"}
        <svg
          class="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="3"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          /></svg
        >
      {/if}
      <span class="text-xs font-black tracking-widest">{toastMessage}</span>
    </div>
  </div>
{/if}

<style>
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  @keyframes progress {
    from {
      width: 0%;
    }
    to {
      width: 100%;
    }
  }
  .animate-progress {
    animation: progress 5s linear forwards;
  }

  .confetti-particle {
    width: var(--size);
    height: var(--size);
    background: var(--color);
    left: var(--left);
    top: -20px;
    border-radius: 2px;
    animation: fall var(--duration) var(--delay) linear forwards;
  }

  @keyframes fall {
    to {
      transform: translateY(800px) translateX(var(--x)) rotate(720deg);
      opacity: 0;
    }
  }

  .pulse-btn {
    position: relative;
    overflow: hidden;
  }
  .pulse-btn::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    box-shadow: 0 0 0 0 rgba(255, 183, 197, 0.4);
    animation: pulse-ring 2s infinite;
  }

  @keyframes pulse-ring {
    to {
      box-shadow: 0 0 0 20px rgba(255, 183, 197, 0);
    }
  }

  .z-surface {
    z-index: var(--z-surface);
  }
  .z-modal {
    z-index: var(--z-modal, 100);
  }
  .z-toast {
    z-index: var(--z-toast, 999);
  }
</style>
