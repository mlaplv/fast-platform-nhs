<script lang="ts">
  import { onDestroy } from "svelte";
  import { beforeNavigate } from "$app/navigation";
  import type { Product } from "$lib/types";
  import X from "@lucide/svelte/icons/x";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Info from "@lucide/svelte/icons/info";
  import AudioLines from "@lucide/svelte/icons/audio-lines";
  import VolumeX from "@lucide/svelte/icons/volume-x";
  import Beaker from "@lucide/svelte/icons/beaker";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { portal } from "$lib/core/actions/portal";
  import InteractiveDashboard from "$lib/components/ui/InteractiveDashboard.svelte";
  import { getShopStore } from "$lib/state/commerce/shop.svelte";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { fomoStore } from "$lib/state/commerce/fomo.svelte";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import Droplet from "@lucide/svelte/icons/droplet";
  import { formatCurrency } from "$lib/utils/format";
  import { resolveMediaUrl, processContentImages } from "$lib/state/utils";
  import { fly, fade } from "svelte/transition";
  import VerificationCenter from "../../product-detail/shared/VerificationCenter.svelte";
  import MobileVerificationCenter from "../../product-detail/shared/MobileVerificationCenter.svelte";
  import ScannerHUD from "../../product-detail/shared/ScannerHUD.svelte";
  import BottomSheet from "./BottomSheet.svelte";

  function isJson(str: string) {
    if (typeof str !== "string") return false;
    try {
      const parsed = JSON.parse(str);
      return typeof parsed === "object" && parsed !== null;
    } catch (e) {
      return false;
    }
  }

  let scrollContainer: HTMLDivElement | undefined = $state();
  let currentImageIndex = $state(0);
  let carouselWidth = $state(0);

  let imageScrollTicking = false;

  function handleImageScroll(e: Event) {
    if (imageScrollTicking) return;
    imageScrollTicking = true;
    requestAnimationFrame(() => {
      if (scrollContainer) {
        const cw = window.innerWidth || scrollContainer.clientWidth;
        if (cw > 0) {
          const newIndex = Math.round(scrollContainer.scrollLeft / cw);
          if (newIndex !== currentImageIndex && newIndex >= 0) {
            currentImageIndex = newIndex;
          }
        }
      }
      imageScrollTicking = false;
    });
  }

  let { active = $bindable(), product }: { active: boolean; product: Product } =
    $props();

  // Drag-to-Close Logic
  let dragY = $state(0);
  let isDragging = $state(false);
  let startY = 0;
  let contentRef = $state<HTMLElement | null>(null);
  let isAtBottom = $state(false);
  let showSpeechButton = $state(false);

  const shopStore = getShopStore();
  const cartStore = getCartStore();

  let scrollTicking = false;
  function handleScroll(e: Event) {
    if (!contentRef || scrollTicking) return;
    scrollTicking = true;
    const target = e.target as HTMLElement;
    requestAnimationFrame(() => {
      // Check if within 100px of bottom — reads are safe inside rAF (layout stable)
      isAtBottom =
        target.scrollHeight - target.scrollTop <= target.clientHeight + 100;

      const proseEl = target.querySelector(".elite-prose") as HTMLElement;
      if (proseEl) {
        showSpeechButton = target.scrollTop >= proseEl.offsetTop - 150;
      } else {
        showSpeechButton = false;
      }
      scrollTicking = false;
    });
  }

  let showVerification = $state(false);
  let isScanning = $state(false);
  let verificationData = $state<import("$lib/types").BarcodeVerificationResponse | null>(null);

  function triggerScan() {
    isScanning = true;
    showVerification = false;
  }

  function handleScanComplete(event: { verificationData: import("$lib/types").BarcodeVerificationResponse }) {
    isScanning = false;
    verificationData = event.verificationData;
    showVerification = true;
  }

  // Elite V2.2: Reset scroll position when opening to ensure starting at top
  $effect(() => {
    if (active && contentRef) {
      contentRef.scrollTop = 0;
      showSpeechButton = false;
    }
  });

  function onPointerDown(e: PointerEvent) {
    isDragging = true;
    startY = e.clientY;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: PointerEvent) {
    if (!isDragging) return;
    const delta = e.clientY - startY;
    if (delta > 0) dragY = delta;
    else dragY = delta * 0.2;
  }

  function onPointerUp(e: PointerEvent) {
    if (!isDragging) return;
    isDragging = false;
    if (dragY > 120) {
      close();
    }
    dragY = 0;
  }

  function close() {
    active = false;
  }

  // 🎙️ TTS: WEB AUDIO ENGINE (Elite V7.0 - OS-Codec-Free)
  // Uses AudioContext.decodeAudioData to bypass OS-level MP3 decoder requirements.
  // Compatible with Firefox/Linux (no gstreamer-ugly needed), Chrome, Safari.
  let isReading: boolean = $state(false);
  let isBuffering: boolean = $state(false);
  const shouldShowSpeech = $derived(
    showSpeechButton || isReading || isBuffering,
  );
  let abortController: AbortController | null = null;

  // R6.0 Memory State
  const CACHE_NAME: string = "osmo-tts-v2";
  let productSlug: string = $derived(product?.slug || "unknown");

  /**
   * Elite V7.1: TTS Text Sanitizer
   * Strips emojis, pictographs, and decorative Unicode that edge-tts reads aloud
   * as their Unicode description (e.g. ⚡ → "biển báo điện cao thế").
   */
  function sanitizeTtsText(raw: string): string {
    const romanMap: Record<string, string> = {
      XX: "hai mươi",
      XIX: "mười chín",
      XVIII: "mười tám",
      XVII: "mười bảy",
      XVI: "mười sáu",
      XV: "mười lăm",
      XIV: "mười bốn",
      XIII: "mười ba",
      XII: "mười hai",
      XI: "mười một",
      X: "10",
      IX: "chín",
      VIII: "tám",
      VII: "bảy",
      VI: "sáu",
      V: "năm",
      IV: "bốn",
      III: "ba",
      II: "hai",
      I: "một",
    };

    const romanRegex =
      /\b(XX|XIX|XVIII|XVII|XVI|XV|XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)\b/g;

    return (
      raw
        // Translate Roman numerals to Vietnamese
        // Translate Roman numerals to Vietnamese
.replace(romanRegex, (match, _unused, offset, str) => {
  if (match === 'X') {
    const before = str[offset - 1] ?? '';
    const after = str[offset + 1] ?? '';
    const isIsolated = (!before || /\s|[.,;!?"'‑-]/.test(before)) && (!after || /\s|[.,;!?"'‑-]/.test(after));
    return isIsolated ? '10' : match;
  }
  return romanMap[match] || match;
})
        // Strip all Emoji except digits/ASCII (Extended Pictographic)
        .replace(/\p{Extended_Pictographic}/gu, "")
        // Strip Miscellaneous Symbols & Dingbats blocks (☀ ★ ♦ etc.)
        .replace(/[\u2600-\u27BF]/g, "")
        // Strip enclosed/supplemental alphanumerics & symbols
        .replace(/[\u{1F000}-\u{1FFFF}]/gu, "")
        // Strip zero-width joiners & variation selectors left over
        .replace(/[\uFE00-\uFE0F\u200D]/g, "")
        // Strip English-only parenthetical labels: (The Hook), (CTA), (USP), (Hero), etc.
        // Vietnamese TTS reads these phonetically as gibberish ("thẻ hók")
        .replace(/\(\s*[A-Za-z][A-Za-z\s\-']{0,40}\s*\)/g, "")
        // Strip leading dash/hyphen left over after stripping parenthetical (e.g. "- ")
        .replace(/^\s*[-–—]\s*/gm, "")
        // Collapse multiple blank lines into single newline
        .replace(/\n{3,}/g, "\n\n")
        // Trim leading/trailing whitespace
        .trim()
    );
  }

  let currentAudio: HTMLAudioElement | null = $state(null);

  async function toggleSpeech(): Promise<void> {
    if (isReading || isBuffering) {
      stopSpeech();
      return;
    }

    const proseEl = contentRef?.querySelector(".elite-prose") as HTMLElement;
    if (!proseEl) return;
    const tempEl = proseEl.cloneNode(true) as HTMLElement;
    tempEl.querySelectorAll("figcaption").forEach((el) => el.remove());
    const rawText: string = tempEl.innerText || "";
    const text: string = sanitizeTtsText(rawText);
    if (text.length < 10) return;

    isBuffering = true;

    try {
      let audioUrl = "";
      let usedCache = false;

      // 1. Check Cache
      const cache = await caches.open(CACHE_NAME);
      const cachedResponse = await cache.match(`/tts/${productSlug}`);

      if (cachedResponse) {
        const blob = await cachedResponse.blob();
        if (blob.size > 500 && blob.type.startsWith("audio/")) {
          audioUrl = URL.createObjectURL(blob);
          usedCache = true;
        } else {
          await cache.delete(`/tts/${productSlug}`);
        }
      }

      if (!usedCache) {
        // 2. Prepare Stream via POST (saves text to Redis)
        abortController = new AbortController();
        const prepRes: Response = await fetch("/api/v1/client/tts/prepare", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text.slice(0, 20000) }),
          signal: abortController.signal,
        });

        if (!prepRes.ok) throw new Error(`Prepare failed: ${prepRes.status}`);
        const { id } = await prepRes.json();
        if (!id) throw new Error("No stream ID returned");

        // 3. Native Streaming via GET endpoint
        // Browser natively streams chunked MP3 HTTP responses, working flawlessly on all browsers (incl. Firefox)
        audioUrl = `/api/v1/client/tts/stream?id=${id}`;

        // Note: Caching the full file is skipped here because it's a live native stream.
        // We will cache it on the next page reload if needed, but native caching often handles it.
      }

      // 4. Play
      const audio = new Audio();
      audio.src = audioUrl;
      currentAudio = audio;

      audio.onplay = () => {
        isBuffering = false;
        isReading = true;
      };

      audio.onloadedmetadata = () => {
        const savedTime = localStorage.getItem(`tts_pos_${productSlug}`);
        if (savedTime) audio.currentTime = parseFloat(savedTime);
      };

      audio.ontimeupdate = () => {
        if (audio.currentTime > 0) {
          localStorage.setItem(
            `tts_pos_${productSlug}`,
            audio.currentTime.toString(),
          );
        }
      };

      audio.onended = () => {
        localStorage.removeItem(`tts_pos_${productSlug}`);
        localStorage.setItem(`tts_done_${productSlug}`, "true");
        cleanup();
      };

      audio.onerror = () => {
        caches
          .open(CACHE_NAME)
          .then((c) => c.delete(`/tts/${productSlug}`))
          .catch(() => {});
        cleanup();
      };

      await audio.play();
    } catch (e: unknown) {
      const err = e as Error;
      if (err?.name !== "AbortError") console.error("[TTS] Error:", err);
      caches
        .open(CACHE_NAME)
        .then((c) => c.delete(`/tts/${productSlug}`))
        .catch(() => {});
      cleanup();
    }
  }

  function stopSpeech(): void {
    cleanup();
  }

  function cleanup(): void {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.ontimeupdate = null;
      currentAudio.onplay = null;
      currentAudio.onloadedmetadata = null;
      if (currentAudio.src.startsWith("blob:")) {
        URL.revokeObjectURL(currentAudio.src);
      }
      currentAudio.src = "";
      currentAudio = null;
    }
    isReading = false;
    isBuffering = false;
  }

  // Stop speech when modal closes

  let wasActive = false;
  $effect(() => {
    if (wasActive && !active) {
      stopSpeech();
    }
    wasActive = active;
  });

  beforeNavigate(() => {
    stopSpeech();
  });

  onDestroy(() => {
    stopSpeech();
  });
</script>

<div use:portal class="mobile-product-details-modal">
  <button
    type="button"
    class="mobile-overlay border-none outline-none"
    style:--drag-opacity-reduce={active ? Math.min(dragY / 400, 0.5) : 0}
    class:active
    class:dragging={isDragging}
    onclick={close}
    aria-label="Đóng overlay"
  ></button>

  <div
    class="mobile-modal-base"
    class:active
    class:dragging={isDragging}
    style:--drag-y={active ? dragY + "px" : "100%"}
    role="dialog"
    aria-modal="true"
  >
    <!-- 🚀 FLOATING CINEMATIC HEADER (Elite V2.6) -->
    <div class="absolute top-0 left-0 w-full z-[9999] pointer-events-none">
      <!-- Minimalist Drag Handle -->
      <div
        class="w-full flex justify-center pt-1.5 pb-0 touch-none cursor-grab active:cursor-grabbing pointer-events-auto"
        onpointerdown={onPointerDown}
        onpointermove={onPointerMove}
        onpointerup={onPointerUp}
        onpointercancel={onPointerUp}
      >
        <div
          class="w-12 h-[3px] bg-white/40 rounded-full shadow-[0_0_15px_rgba(0,0,0,0.5)]"
        ></div>
      </div>

      <div class="flex items-center justify-between px-3 h-12">
        <!-- 🎙️ NEURAL VOICE CAPSULE (Elite V6.4 Lite) -->
        <button
          onclick={toggleSpeech}
          class="flex items-center gap-2 px-3.5 py-1.5 rounded-full transition-all duration-500 active:scale-95 pointer-events-auto border border-white/10 {isReading ||
          isBuffering
            ? 'bg-pink-500/80 text-white'
            : 'bg-black/25 backdrop-blur-md text-white'} {shouldShowSpeech
            ? 'opacity-100 scale-100'
            : 'opacity-0 scale-90 pointer-events-none'}"
          aria-label={isReading ? "Dừng đọc" : "Đọc thông tin"}
        >
          {#if isBuffering}
            <div class="relative w-3.5 h-3.5">
              <div
                class="absolute inset-0 border-[1.5px] border-white/30 rounded-full"
              ></div>
              <div
                class="absolute inset-0 border-[1.5px] border-white border-t-transparent rounded-full animate-spin"
              ></div>
            </div>
          {:else if isReading}
            <div class="flex items-end gap-[2px] h-3">
              <div class="w-[2px] bg-white animate-voice-bar-1"></div>
              <div class="w-[2px] bg-white animate-voice-bar-2"></div>
              <div class="w-[2px] bg-white animate-voice-bar-3"></div>
            </div>
          {:else}
            <AudioLines size={14} strokeWidth={2} class="text-white" />
          {/if}
          <span class="text-[11px] font-medium tracking-tight leading-none"
            >{isBuffering ? "Loading..." : isReading ? "Reading..." : "Listen"}</span
          >
        </button>

        <!-- Close Button (Elegant Integrated X) -->
        <button
          onclick={close}
          class="text-white transition-all p-1 active:scale-90 outline-none border border-white/10 bg-black/30 backdrop-blur-md rounded-full pointer-events-auto"
          aria-label="Đóng"
        >
          <X size={10} strokeWidth={3} />
        </button>
      </div>
    </div>

    <!-- Scrollable Description Body -->
    <div
      bind:this={contentRef}
      onscroll={handleScroll}
      class="overflow-y-auto custom-scrollbar flex-1 relative select-text !pt-0 !mt-0"
    >
      {#if product}
        <!-- 🖼️ PRODUCT MEDIA GALLERY (Viral 2026 Pro) -->
        {#if (product.images && product.images.length > 0) || (product.mobile_images && product.mobile_images.length > 0)}
          {@const galleryImages = product.mobile_images?.length
            ? product.mobile_images
            : product.images}
          <div
            class="gallery-viewport !mx-0 !mt-0 !mb-0 bg-black overflow-hidden relative group rounded-t-[5px]"
          >
            <div
              bind:this={scrollContainer}
              onscroll={handleImageScroll}
              class="flex overflow-x-auto snap-x snap-mandatory hide-scrollbar"
              style="scrollbar-width: none; -ms-overflow-style: none;"
            >
              {#each galleryImages as img, i}
                <div
                  class="w-full shrink-0 snap-center relative overflow-hidden bg-black"
                >
                  <!-- 📸 CINEMATIC PRODUCT IMAGE -->
                  <!-- 🌫️ Blurred background layer -->
                  <img
                    src={resolveMediaUrl(img)}
                    alt="Phông nền sản phẩm - {product.name}"
                    aria-hidden="true"
                    class="absolute inset-0 w-full h-full object-cover scale-110 blur-2xl opacity-40 z-0 pointer-events-none"
                  />
                  <!-- 📸 Main product image -->
                  <img
                    src={resolveMediaUrl(img)}
                    alt={product.name ||
                      "Miccosmo Beppin Body Virgin White Serum"}
                    class="relative block w-full h-auto z-10 transition-transform duration-700 {currentImageIndex ===
                    i
                      ? 'scale-100 opacity-100'
                      : 'scale-95 opacity-40 blur-sm'}"
                  />
                </div>
              {/each}
            </div>

            <!-- 🏷️ BRAND NAME: Bottom Left -->
            <div
              class="absolute bottom-4 left-4 z-20 pointer-events-none max-w-[65%]"
            >
              <div
                class="text-lg font-black !text-white leading-tight drop-shadow-[0_1px_12px_rgba(0,0,0,0.9)]"
              >
                {product.name}
              </div>
            </div>

            <!-- 📊 INFO PILL: Bottom Right (viewer + image count) -->
            <div
              class="absolute bottom-4 right-4 z-20 flex flex-col items-end gap-1.5"
            >
              <div
                class="flex items-center gap-1.5 bg-black/40 px-2.5 py-1 rounded-full"
              >
                <div
                  class="w-1.5 h-1.5 rounded-full bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.6)]"
                ></div>
                <span class="text-[9px] font-bold text-white/80 leading-none"
                  >{fomoStore.viewers.toLocaleString()} đang xem</span
                >
              </div>
              {#if galleryImages.length > 1}
                <div
                  class="flex items-center gap-1 bg-black/40 px-2.5 py-1 rounded-full"
                >
                  <span class="text-[10px] font-bold text-white/90 font-mono"
                    >{currentImageIndex + 1}</span
                  >
                  <span class="text-[10px] text-white/30 font-mono">/</span>
                  <span class="text-[10px] text-white/30 font-mono"
                    >{galleryImages.length}</span
                  >
                </div>
              {/if}
            </div>

            <!-- Subtle Bottom Vignette -->
            <div
              class="absolute inset-x-0 bottom-0 h-1/3 pointer-events-none bg-gradient-to-t from-black/70 to-transparent z-10"
            ></div>
          </div>
        {/if}

        <!-- 📊 PRODUCT INFO (Elite V3.0 Clean) -->
        <div class="px-[5px] pt-5 pb-2">
          <!-- Specs: Clean inline list -->
          {#if product.metadata}
            {@const specs = [
              product.metadata?.brand && {
                label: "Thương hiệu",
                value: product.metadata.brand,
              },
              product.metadata?.origin && {
                label: "Xuất xứ",
                value: product.metadata.origin,
              },
              product.metadata?.weight && {
                label: "Trọng lượng",
                value: product.metadata.weight,
              },
              (product.metadata?.barcode || product.sku) && {
                label: "Mã vạch",
                value: product.metadata?.barcode || product.sku,
              },
            ].filter(Boolean)}
            {#if specs.length > 0}
              <div class="flex flex-wrap gap-x-5 gap-y-2 mb-4">
                {#each specs as spec}
                  <button
                    class="flex flex-col items-start bg-transparent border-none p-0 text-left active:scale-95 transition-transform"
                    onclick={triggerScan}
                  >
                    <span
                      class="text-[9px] font-semibold {spec.label === 'SKU' ||
                      spec.label === 'Mã vạch'
                        ? 'text-green-400'
                        : 'text-white/35'} tracking-widest leading-none mb-1"
                    >
                      {spec.label === "SKU" || spec.label === "Mã vạch"
                        ? `Mã vạch (Verify)`
                        : spec.label}
                    </span>
                    <span class="text-[13px] font-bold text-white/90"
                      >{spec.value}</span
                    >
                  </button>
                {/each}
              </div>
              <div class="w-full h-px bg-white/8 mb-4"></div>
            {/if}
          {/if}

          <!-- 🧪 INGREDIENTS -->
          {#if product.metadata?.featured_ingredients?.length > 0 || product.metadata?.ingredients}
            <div class="mb-4">
              <h2
                class="text-[12px] font-bold text-white/40 tracking-wider mb-2 flex items-center gap-1.5"
              >
                <Droplet class="w-3.5 h-3.5 text-pink-300/70" />
                Thành phần & Công dụng
              </h2>

              {#if product.metadata?.featured_ingredients?.length > 0}
                <div class="space-y-1 mb-2">
                  {#each product.metadata.featured_ingredients as ing}
                    <div class="py-0.5">
                      <span class="text-[13px] font-bold text-white/90"
                        >{ing.name}</span
                      >
                      <p
                        class="text-[11px] text-white/50 leading-relaxed mt-0.5"
                      >
                        {ing.benefit}
                      </p>
                    </div>
                  {/each}
                </div>
              {/if}

              {#if product.metadata?.ingredients}
                <div class="mt-4 mb-2 flex items-center gap-1.5">
                  <Beaker class="w-3.5 h-3.5 text-teal-300/80" />
                  <span
                    class="text-[11px] font-bold text-white/50 tracking-wider"
                  >
                    Bảng thành phần đầy đủ
                  </span>
                </div>
                <p class="text-[11px] text-white/40 leading-relaxed font-mono">
                  {product.metadata.ingredients}
                </p>
              {/if}
            </div>
            <div class="w-full h-px bg-white/8 mb-4"></div>
          {/if}

          <!-- ELITE V2.2: SCANNER HUD & VERIFICATION CENTER -->
          {#if isScanning}
            <ScannerHUD
              barcode={product.metadata?.barcode || product.sku}
              oncomplete={handleScanComplete}
            />
          {/if}

          {#if showVerification}
            <BottomSheet
              bind:active={showVerification}
              title="Verified"
              fullWidth={true}
              tight={true}
              extraStyle="padding-left: 5px !important; padding-right: 5px !important;"
            >
              <MobileVerificationCenter {product} {verificationData} />
            </BottomSheet>
          {/if}
        </div>

        <div class="px-[5px] elite-prose">
          {#if product.description}
            {#if isJson(product.description)}
              <InteractiveDashboard
                data={product.description}
                compact={true}
                assets={product.images || []}
              />
            {:else}
              <!-- eslint-disable-next-line svelte/no-at-html-tags -->
              {@html processContentImages(
                product.description,
                product.images || [],
              )}
            {/if}
          {:else}
            <div
              class="flex flex-col items-center justify-center h-full text-white/30 space-y-4 pb-20"
            >
              <ShieldCheck class="w-12 h-12 opacity-50" />
              <p class="text-xs tracking-widest font-bold">
                Chưa có thông tin mô tả chi tiết
              </p>
            </div>
          {/if}
        </div>

        <!-- Spacer to prevent floating CTA from overlapping content at the very bottom -->
        <div
          class="h-32 w-full block clear-both shrink-0 pointer-events-none"
        ></div>
      {/if}
    </div>

    <!-- 🛰️ ELITE V2.2: FLOATING STICKY CTA (Conversion Booster) -->
    {#if isAtBottom}
      <div
        class="absolute bottom-10 left-0 w-full px-4 shrink-0 z-[var(--z-surface)] pointer-events-none"
        transition:fly={{ y: 20, duration: 400 }}
      >
        <button
          onclick={() => {
            const variantToBuy = shopStore.variant || product.variants?.[0];
            if (variantToBuy) shopStore.selectVariant(variantToBuy);
            shopStore.openCheckout(cartStore, product);
          }}
          class="w-full h-[65px] rounded-[1.5rem] font-black text-[14px] tracking-[0.1em] flex items-center justify-between px-5 transition-all duration-500 italic active:scale-95 bg-gradient-to-r from-[#ee4d2d] to-[#ff7337] text-white shadow-[0_20px_50px_rgba(238,77,45,0.4)] relative group overflow-hidden pointer-events-auto"
        >
          <div
            class="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"
          ></div>
          <div class="flex flex-col text-left leading-tight">
            <span class="text-[10px] font-black opacity-60">Đặt hàng ngay</span>
            <span class="text-[13px] font-black"
              >Chọn Combo x{shopStore.variant?.attributes?.combo_qty || 1}</span
            >
          </div>

          <div class="flex items-center gap-3">
            <div class="flex flex-col items-end leading-none">
              {#if shopStore.originalPrice * shopStore.quantity > shopStore.totalAmount}
                <span class="text-[9px] text-white/40 line-through font-bold"
                  >{formatCurrency(
                    shopStore.originalPrice * shopStore.quantity,
                  )}</span
                >
              {/if}
              <span
                class="text-[19px] font-[1000] tracking-tighter drop-shadow-sm"
                >{formatCurrency(
                  shopStore.totalAmount || product.variants?.[0]?.price || 0,
                )}</span
              >
            </div>
            <div
              class="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center border border-white/10"
            >
              <ArrowRight class="w-5 h-5 text-white" />
            </div>
          </div>
        </button>
      </div>
    {/if}
  </div>
</div>

<style lang="postcss">
  /* Elite Prose Typography - VIRAL 2026 PREMIUM EDITION */
  .elite-prose {
    font-family: var(--font-main);
    font-size: 15px;
    line-height: 1.5; /* Giảm độ giãn dòng để không bị hở */
    color: rgba(255, 255, 255, 0.95);
    text-align: left !important;
    word-break: break-word;
    letter-spacing: -0.01em;
    margin-bottom: 8px;
  }

  /* 🏆 Premium Headings - VIRAL 2026 ELITE EDITION */
  :global(.elite-prose h1) {
    font-family: var(--font-main);
    font-size: 1.6rem;
    font-weight: 800; /* High-end Bold */
    line-height: 1.2;
    margin-top: 0.5rem; /* Aggressively reduced */
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em; /* Relaxed for readability */
    color: #fff;
    text-transform: none;
    position: relative;
    display: block;
    width: fit-content;
    text-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
  }

  :global(.elite-prose h1::after) {
    content: "";
    display: block;
    width: 40px;
    height: 3px;
    background: linear-gradient(90deg, #ffb7c5, #e8d5b0);
    margin-top: 6px; /* Tightened */
    border-radius: 100px;
  }

  :global(.elite-prose h2, .elite-prose h3) {
    font-family: var(--font-main);
    color: white;
    font-weight: 800;
    line-height: 1.2;
    margin-top: 1rem;
    position: relative;
    padding-bottom: 0.5rem;
    color: #fff;
    letter-spacing: -0.02em;
    width: fit-content;
  }

  :global(.elite-prose h2) {
    font-size: 1.15rem;
    color: #fff;
    border-left: 3px solid #ffb7c5;
    padding-left: 6px;
    margin: 2rem 0 1rem 0;
    font-weight: 800;
    letter-spacing: -0.01em;
  }

  :global(.elite-prose h3) {
    font-size: 0.9rem;
    letter-spacing: 0.08em;
    color: rgba(255, 255, 255, 0.85);
    opacity: 0.9;
  }

  :global(.elite-prose p) {
    margin-bottom: 0.8rem; /* Relaxed for readability */
    opacity: 1;
  }

  /* ⚡ Viral Fix: No gap after images */
  :global(.elite-prose img + *) {
    margin-top: 0 !important;
  }

  :global(.elite-prose > *:first-child) {
    margin-top: 0 !important;
  }

  :global(.elite-prose strong, .elite-prose b) {
    color: #fff !important;
    font-weight: 800;
  }

  /* 🛡️ R1.5: Fix AI Color Leaks - Forces white for any spans with dark inline styles */
  :global(.elite-prose span) {
    color: inherit !important;
  }

  /* Viral Glowy Bullets - ULTRA TIGHT RESET */
  :global(.elite-prose ul),
  :global(.elite-prose ol) {
    list-style-type: none !important;
    padding-left: 0 !important;
    margin-left: 0 !important;
    margin-bottom: 1.5rem;
  }

  :global(.elite-prose li) {
    position: relative;
    padding-left: 20px !important;
    margin-bottom: 0.6rem;
    line-height: 1.6;
    list-style: none !important;
  }

  :global(.elite-prose li::before) {
    content: "";
    position: absolute;
    left: 4px;
    top: 0.6em;
    width: 5px;
    height: 5px;
    background: #ffb7c5;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(255, 183, 197, 0.6);
  }

  /* 🧪 iPhone Minimalist Scrollbar (Scoped to Modal) */
  :global(.mobile-modal-base::-webkit-scrollbar),
  :global(.custom-scrollbar::-webkit-scrollbar) {
    width: 2px !important;
    height: 2px !important;
  }

  :global(.mobile-modal-base::-webkit-scrollbar-thumb),
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) {
    background: rgba(255, 255, 255, 0.25) !important;
    border-radius: 100px !important;
  }

  :global(.mobile-modal-base),
  :global(.custom-scrollbar) {
    scrollbar-width: thin !important;
    scrollbar-color: rgba(255, 255, 255, 0.25) transparent !important;
  }

  :global(.elite-prose a) {
    color: #00a3ff;
    font-weight: 700;
    text-decoration: none;
    transition: all 0.2s;
  }

  :global(.elite-prose a:hover) {
    color: #60a5fa;
  }

  :global(.elite-prose img) {
    display: block; /* Eliminate baseline gap */
    width: calc(
      100% + 10px
    ) !important; /* Full-bleed via negative margin trick */
    max-width: none !important;
    margin-left: -5px !important;
    margin-right: -5px !important;
    height: auto;
    border-radius: 0; /* Full-bleed look */
    margin-top: 0.25rem;
    margin-bottom: 0.5rem;
    box-shadow: none;
    border: none;
  }

  /* 🖼️ Cinematic Gallery Reset (Elite V2.6) */
  .gallery-viewport img {
    margin: 0 !important;
    border-radius: 0 !important;
    border: none !important;
    box-shadow: none !important;
  }

  :global(.elite-prose blockquote) {
    border-left: 3px solid #ffb7c5;
    padding-left: 1rem;
    font-style: italic;
    color: rgba(255, 255, 255, 0.7);
    margin: 1.5rem 0;
    background: linear-gradient(
      90deg,
      rgba(255, 183, 197, 0.1) 0%,
      transparent 100%
    );
    padding: 1rem;
    border-radius: 0 8px 8px 0;
  }

  :global(.elite-prose table) {
    width: 100%;
    margin-bottom: 1.5rem;
    border-collapse: collapse;
  }

  :global(.elite-prose th, .elite-prose td) {
    padding: 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    text-align: left;
  }

  :global(.elite-prose th) {
    background: rgba(255, 255, 255, 0.05);
    font-weight: 700;
    color: white;
  }

  /* 🎙️ Neural Voice Animations */
  @keyframes voice-bar {
    0%,
    100% {
      height: 4px;
    }
    50% {
      height: 12px;
    }
  }

  .animate-voice-bar-1 {
    animation: voice-bar 0.6s infinite ease-in-out;
  }
  .animate-voice-bar-2 {
    animation: voice-bar 0.8s infinite ease-in-out 0.2s;
  }
  .animate-voice-bar-3 {
    animation: voice-bar 0.7s infinite ease-in-out 0.4s;
  }
</style>
