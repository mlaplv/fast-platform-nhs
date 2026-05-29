<script lang="ts">
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import ChevronUp from "@lucide/svelte/icons/chevron-up";
  import Beaker from "@lucide/svelte/icons/beaker";
  import Info from "@lucide/svelte/icons/info";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import type { Product } from "$lib/types";
  import InteractiveDashboard from "$lib/components/ui/InteractiveDashboard.svelte";
  import {
    getIngredientIcon,
    parseDescriptionAndCommitments,
  } from "$lib/utils/product";

  let {
    product,
    onTriggerScan,
  }: {
    product: Product;
    onTriggerScan?: () => void;
  } = $props();

  let isExpanded = $state(false);
  let isIngredientsExpanded = $state(false);
  let containerRef = $state<HTMLElement>();
  let hasMore = $state(false);
  let activeMobileFaq = $state<number | null>(0);
  let mounted = $state(false);
  const truncatedHeight = 180;

  const parsedDescription = $derived(
    parseDescriptionAndCommitments(product.description),
  );

  import { onMount } from "svelte";
  onMount(() => {
    mounted = true;
  });

  $effect(() => {
    if (containerRef) {
      hasMore = containerRef.scrollHeight > truncatedHeight;
    }
  });

  function isJson(str: string | null | undefined): boolean {
    if (typeof str !== "string" || !str) return false;
    try {
      const parsed = JSON.parse(str);
      return (
        typeof parsed === "object" &&
        parsed !== null &&
        ("hero_headline" in parsed || "spec_bento" in parsed)
      );
    } catch {
      return false;
    }
  }

  const brand = $derived(
    product.attributes?.["Thương hiệu"] ||
      product.attributes?.["Brand"] ||
      product.metadata?.brand,
  );

  import AudioLines from "@lucide/svelte/icons/audio-lines";
  import { onDestroy } from "svelte";

  // 🎙️ TTS: WEB AUDIO ENGINE (Elite V7.0 - OS-Codec-Free)
  let isReading = $state(false);
  let isBuffering = $state(false);
  let abortController: AbortController | null = null;
  let currentAudio = $state<HTMLAudioElement | null>(null);

  const CACHE_NAME = "osmo-tts-v2";
  const productSlug = $derived(product?.slug || "unknown");

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
      X: "mười",
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
        .replace(romanRegex, (match) => romanMap[match] || match)
        // Strip all Emoji except digits/ASCII
        .replace(/\p{Extended_Pictographic}/gu, "")
        // Strip Miscellaneous Symbols & Dingbats blocks
        .replace(/[\u2600-\u27BF]/g, "")
        // Strip enclosed/supplemental alphanumerics & symbols
        .replace(/[\u{1F000}-\u{1FFFF}]/gu, "")
        // Strip zero-width joiners & variation selectors left over
        .replace(/[\uFE00-\uFE0F\u200D]/g, "")
        // Strip English-only parenthetical labels
        .replace(/\(\s*[A-Za-z][A-Za-z\s\-']{0,40}\s*\)/g, "")
        // Strip leading dash/hyphen left over
        .replace(/^\s*[-–—]\s*/gm, "")
        // Collapse multiple blank lines
        .replace(/\n{3,}/g, "\n\n")
        .trim()
    );
  }

  async function toggleSpeech(): Promise<void> {
    if (isReading || isBuffering) {
      stopSpeech();
      return;
    }

    if (!containerRef) return;
    const tempEl = containerRef.cloneNode(true) as HTMLElement;
    tempEl.querySelectorAll("figcaption").forEach((el) => el.remove());
    const rawText = tempEl.innerText || "";
    const text = sanitizeTtsText(rawText);
    if (text.length < 10) return;

    isBuffering = true;

    try {
      let audioUrl = "";
      let usedCache = false;

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
        abortController = new AbortController();
        const prepRes = await fetch("/api/v1/client/tts/prepare", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text.slice(0, 20000) }),
          signal: abortController.signal,
        });

        if (!prepRes.ok) throw new Error(`Prepare failed: ${prepRes.status}`);
        const { id } = await prepRes.json();
        if (!id) throw new Error("No stream ID returned");

        audioUrl = `/api/v1/client/tts/stream?id=${id}`;
      }

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

  onDestroy(() => {
    stopSpeech();
  });
</script>

<section class="content-section">
  {#if product.attributes && Object.entries(product.attributes).length > 0}
    <div class="mb-[10px] grid grid-cols-2 gap-x-6 gap-y-1">
      {#each Object.entries(product.attributes) as [key, val]}
        {@const isBrandKey = key === "Thương hiệu" || key === "Brand" || key === "brand"}
        <div
          class="flex flex-col py-1.5 border-b border-gray-50/50 overflow-hidden"
        >
          <span class="text-[10px] text-gray-400 font-medium truncate"
            >{key.replace(/_/g, " ")}</span
          >
          {#if isBrandKey && val}
            <a
              href="/search?q={encodeURIComponent(String(val))}"
              class="text-[12px] text-[#ee4d2d] font-bold truncate hover:underline"
            >{val}</a>
          {:else}
            <span class="text-[12px] text-gray-800 font-bold truncate">{val}</span>
          {/if}
        </div>
      {/each}
    </div>
  {/if}

  {#if product.metadata?.desc_semantic}
    <div class="mb-[10px] pb-[10px] border-b border-gray-100">
      <div class="prose max-w-none text-[13.5px] text-gray-700 semantic-summary">
        {@html product.metadata.desc_semantic}
      </div>
    </div>
  {/if}

  <!-- Elite V2.2: Featured Ingredients (Viral Cards) -->
  {#if product.metadata?.featured_ingredients && product.metadata.featured_ingredients.length > 0}
    <div class="mb-[10px]">
      <h2 class="section-title">Thành phần nổi bật</h2>
      <div class="grid grid-cols-1 gap-2">
        {#each product.metadata.featured_ingredients as ing}
          <div
            class="group bg-[#fdf2f2]/40 border border-[#ee4d2d]/10 p-2 rounded-xl flex items-center gap-3 transition-all hover:bg-white hover:shadow-md"
          >
            <div
              class="w-10 h-10 shrink-0 bg-white border border-[#ee4d2d]/10 rounded-xl flex items-center justify-center text-[18px] shadow-sm group-hover:scale-110 transition-transform"
            >
              {ing.icon || getIngredientIcon(ing.name)}
            </div>
            <div class="flex flex-col justify-center">
              <span class="text-[14px] font-bold text-gray-900 leading-tight"
                >{ing.name}</span
              >
              <p class="text-[12px] text-gray-500 leading-normal mt-0.5">
                {ing.benefit}
              </p>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Elite V2.2: Full Ingredients (Mobile Transparency) -->
  {#if product.metadata?.ingredients}
    <div class="mt-[10px] mb-[10px] flex flex-col gap-2">
      <h2
        class="flex items-center gap-2 text-[16px] font-bold text-gray-800 tracking-tight"
      >
        <Beaker size={16} class="text-teal-500" /> Bảng thành phần
      </h2>
      
      {#if product.metadata?.ingredients_groups && product.metadata.ingredients_groups.length > 0}
        <button
          type="button"
          class="bg-gray-50/50 border border-gray-100 p-4 rounded-xl text-left relative overflow-hidden transition-all duration-500"
          onclick={() => (isIngredientsExpanded = !isIngredientsExpanded)}
          style:max-height={isIngredientsExpanded ? "none" : "180px"}
        >
          <div class="flex flex-col gap-3 {!isIngredientsExpanded ? 'line-clamp-4' : ''}">
            {#each product.metadata.ingredients_groups as grp}
              <div class="flex flex-col gap-1">
                <div class="flex items-center justify-between border-b border-gray-100/50 pb-0.5">
                  <span class="text-[10px] font-black text-teal-600 uppercase tracking-wider">{grp.group}</span>
                  <span class="text-[9px] font-black text-gray-400">{grp.items.length} chất</span>
                </div>
                <div class="flex flex-wrap gap-1 mt-0.5 font-mono">
                  {#each grp.items as item}
                    <span class="text-[10px] text-gray-600 px-1.5 py-0.5 rounded bg-white border border-gray-100/80">{item}</span>
                  {/each}
                </div>
              </div>
            {/each}
          </div>

          {#if !isIngredientsExpanded}
            <div
              class="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-gray-50/95 to-transparent flex items-end justify-center pb-1"
            >
              <div class="flex items-center gap-1 text-gray-400 font-sans">
                <span class="text-[11px] font-medium">Xem thêm phân nhóm</span>
                <ChevronDown size={12} />
              </div>
            </div>
          {:else}
            <div class="mt-3 flex justify-center">
              <div class="flex items-center gap-1 text-gray-400 font-sans">
                <span class="text-[11px] font-medium">Thu gọn</span>
                <ChevronUp size={12} />
              </div>
            </div>
          {/if}
        </button>
      {:else}
        <button
          type="button"
          class="bg-gray-50/50 border border-gray-100 p-4 rounded-xl text-left relative overflow-hidden transition-all duration-500"
          onclick={() => (isIngredientsExpanded = !isIngredientsExpanded)}
          style:max-height={isIngredientsExpanded ? "none" : "100px"}
        >
          <p
            class="text-[12px] text-gray-600 font-mono leading-relaxed tracking-tight {!isIngredientsExpanded
              ? 'line-clamp-3'
              : ''}"
          >
            {product.metadata.ingredients}
          </p>
          {#if !isIngredientsExpanded}
            <div
              class="absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-gray-50/95 to-transparent flex items-end justify-center pb-1"
            >
              <div class="flex items-center gap-1 text-gray-400 font-sans">
                <span class="text-[11px] font-medium">Xem thêm</span>
                <ChevronDown size={12} />
              </div>
            </div>
          {:else}
            <div class="mt-2 flex justify-center">
              <div class="flex items-center gap-1 text-gray-400 font-sans">
                <span class="text-[11px] font-medium">Thu gọn</span>
                <ChevronUp size={12} />
              </div>
            </div>
          {/if}
        </button>
      {/if}
      <div class="mt-1 flex items-center gap-2 px-1">
        <Info size={10} class="text-blue-500" />
        <span class="text-[9px] text-gray-400 font-bold italic"
          >Phân tích thành phần bằng AI, sắp xếp theo độ ưu tiên giảm dần</span
        >
      </div>
    </div>
  {/if}

  <div class="flex items-center justify-between mt-[10px] mb-[4px] pr-1">
    <h2 class="section-title !mb-0 !mt-0">Chi tiết</h2>
    <!-- 🎙️ NEURAL VOICE CAPSULE (Elite V6.4 Lite) -->
    <button
      type="button"
      onclick={toggleSpeech}
      class="flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-all duration-300 active:scale-95 border {isReading ||
      isBuffering
        ? 'bg-[#ee4d2d]/10 text-[#ee4d2d] border-[#ee4d2d]/20'
        : 'bg-gray-50 border-gray-200 text-gray-600'}"
      aria-label={isReading ? "Dừng đọc" : "Đọc thông tin"}
    >
      {#if isBuffering}
        <div class="relative w-3.5 h-3.5 flex items-center justify-center">
          <div
            class="absolute inset-0 border-[1.5px] border-gray-300 rounded-full"
          ></div>
          <div
            class="absolute inset-0 border-[1.5px] border-[#ee4d2d] border-t-transparent rounded-full animate-spin"
          ></div>
        </div>
      {:else if isReading}
        <div class="flex items-end gap-[2px] h-3">
          <div class="w-[2px] bg-[#ee4d2d] animate-voice-bar-1"></div>
          <div class="w-[2px] bg-[#ee4d2d] animate-voice-bar-2"></div>
          <div class="w-[2px] bg-[#ee4d2d] animate-voice-bar-3"></div>
        </div>
      {:else}
        <AudioLines size={13} strokeWidth={2.5} class="text-gray-500" />
      {/if}
      <span class="text-[11px] font-extrabold tracking-tight leading-none">
        {isBuffering ? "..." : isReading ? "Dừng" : "Nghe"}
      </span>
    </button>
  </div>

  <div
    class="description-wrapper {!isExpanded && hasMore ? 'collapsed' : ''}"
    style:max-height={isExpanded
      ? "none"
      : hasMore
        ? truncatedHeight + "px"
        : "none"}
  >
    <div bind:this={containerRef} class="prose-osmo pb-4">
      {#if isJson(product.description)}
        <InteractiveDashboard data={product.description} compact={true} />
      {:else}
        {@html parsedDescription.cleanDescription ||
          "Chưa có mô tả chi tiết cho sản phẩm này."}
      {/if}

      <!-- Elite V2.2: Premium OSMO Purity & CRO Guarantee Bento (Mobile-Optimized - Borderless & Super Compact) -->
      <div class="mt-[10px] pt-[10px] border-t border-gray-100/60">
        <div class="py-2.5 bg-white relative select-none">
          
          <!-- Decorative Mobile backlight -->
          <div class="absolute -top-12 -right-12 w-24 h-24 rounded-full bg-[#ee4d2d]/3 blur-2xl pointer-events-none"></div>

          <!-- Section Title & Badges in 2 neat rows to prevent any wrapping on narrow screens -->
          <div class="relative z-10 flex flex-col gap-1.5 pb-2.5">
            <div class="flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-[#ee4d2d] shrink-0"></span>
              <div class="text-[12.5px] font-black text-slate-800 uppercase tracking-wider whitespace-nowrap">OSMO Cam Kết Vàng</div>
            </div>
            <div class="flex flex-wrap items-center gap-1.5">
              <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#ee4d2d]/5 text-[#ee4d2d] text-[9.5px] font-black uppercase tracking-wider whitespace-nowrap select-none">
                ✦ Lành tính & An toàn
              </span>
              <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/5 text-emerald-600 text-[9.5px] font-black uppercase tracking-wider whitespace-nowrap select-none">
                ✓ "3 Không" Nhật Bản
              </span>
            </div>
          </div>

          <!-- Vertical Stack of "3 Không" (Borderless & Compact) -->
          <div class="relative z-10 flex flex-col gap-3 my-3">
            <!-- 1. Không Paraben -->
            <div class="flex items-start gap-3 py-1.5 bg-transparent transition-all duration-300">
              <span class="w-5.5 h-5.5 rounded-full bg-[#ee4d2d]/5 flex items-center justify-center text-[#ee4d2d] shrink-0 font-black text-[10px] mt-0.5">01</span>
              <div class="flex flex-col min-w-0">
                <span class="text-[11.5px] font-black text-slate-800 uppercase tracking-tight leading-snug">KHÔNG PARABEN</span>
                <span class="text-[10px] text-gray-500 font-medium leading-normal mt-0.5">An toàn tuyệt đối cho sức khỏe lâu dài.</span>
              </div>
            </div>
            <!-- 2. Không dầu khoáng -->
            <div class="flex items-start gap-3 py-1.5 bg-transparent transition-all duration-300">
              <span class="w-5.5 h-5.5 rounded-full bg-[#ee4d2d]/5 flex items-center justify-center text-[#ee4d2d] shrink-0 font-black text-[10px] mt-0.5">02</span>
              <div class="flex flex-col min-w-0">
                <span class="text-[11.5px] font-black text-slate-800 uppercase tracking-tight leading-snug">KHÔNG DẦU KHOÁNG</span>
                <span class="text-[10px] text-gray-500 font-medium leading-normal mt-0.5">Thông thoáng, không gây bí tắc lỗ chân lông.</span>
              </div>
            </div>
            <!-- 3. Không màu nhân tạo -->
            <div class="flex items-start gap-3 py-1.5 bg-transparent transition-all duration-300">
              <span class="w-5.5 h-5.5 rounded-full bg-[#ee4d2d]/5 flex items-center justify-center text-[#ee4d2d] shrink-0 font-black text-[10px] mt-0.5">03</span>
              <div class="flex flex-col min-w-0">
                <span class="text-[11.5px] font-black text-slate-800 uppercase tracking-tight leading-snug">KHÔNG MÀU NHÂN TẠO</span>
                <span class="text-[10px] text-gray-500 font-medium leading-normal mt-0.5">Tinh khiết nguyên bản chuẩn dược liệu Nhật Bản.</span>
              </div>
            </div>
          </div>

          <!-- Bottom Mobile Guarantees & FOMO -->
          <div class="relative z-10 pt-3.5 border-t border-gray-100/40 flex flex-col gap-3">
            <div class="flex items-center justify-between gap-1 py-0.5">
              <!-- Item 1: Đổi trả -->
              <div class="flex items-center gap-1 text-[10px] font-black text-slate-700">
                <svg class="w-3.5 h-3.5 text-[#ee4d2d]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 6H16" />
                </svg>
                <span>Đổi trả 7 ngày</span>
              </div>
              <!-- Item 2: Free Ship -->
              <div class="flex items-center gap-1 text-[10px] font-black text-slate-700">
                <svg class="w-3.5 h-3.5 text-[#ee4d2d]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span>Freeship toàn quốc</span>
              </div>
              <!-- Item 3: Hoàn tiền -->
              <div class="flex items-center gap-1 text-[10px] font-black text-slate-700">
                <svg class="w-3.5 h-3.5 text-[#ee4d2d]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <span>Hoàn tiền nhanh</span>
              </div>
            </div>
            
            <!-- Bottom pink ribbon -->
            <div class="bg-[#ee4d2d]/5 text-[#ee4d2d] py-2 px-3 rounded-lg text-center font-black text-[10px] tracking-wider animate-pulse flex items-center justify-center gap-1 select-none">
              🔥 GIỚI HẠN: ĐẶT HÀNG HÔM NAY ĐỂ NHẬN ƯU ĐÃI!
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>

  {#if mounted && hasMore}
    <button
      type="button"
      class="expand-btn-elite"
      onclick={() => (isExpanded = !isExpanded)}
    >
      {#if isExpanded}
        Thu gọn <ChevronUp size={16} />
      {:else}
        Xem thêm <ChevronDown size={16} />
      {/if}
    </button>
  {/if}

  {#if parsedDescription.commitments}
    {@const commitments = parsedDescription.commitments}
    <div
      class="commitment-card-luxury mt-[10px] p-4 rounded-xl border border-emerald-500/10 bg-white/40 relative overflow-hidden shadow-[0_10px_20px_rgba(4,120,87,0.01)] backdrop-blur-md transition-all duration-300"
    >
      <!-- Subtle Mobile backlights -->
      <div
        class="absolute -top-6 -right-6 w-20 h-20 rounded-full bg-emerald-100/20 blur-xl pointer-events-none"
      ></div>
      <div
        class="absolute -bottom-6 -left-6 w-20 h-20 rounded-full bg-teal-100/20 blur-xl pointer-events-none"
      ></div>

      <div class="relative z-10 flex flex-col gap-2">
        <!-- Mobile Header: Optimized flex wrapper - Prevent title compression -->
        <div class="flex flex-col gap-1 pb-2 border-b border-emerald-500/10">
          <div class="flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"
            ></span>
            <span
              class="text-[11px] font-black text-slate-800 uppercase tracking-wider whitespace-nowrap shrink-0"
              >{commitments.title}</span
            >
          </div>
          {#if commitments.subtitle}
            <span class="text-[10px] font-bold text-[#ee4d2d] leading-normal"
              >{commitments.subtitle}</span
            >
          {/if}
        </div>

        <!-- Mobile Items: 3 compact rows -->
        <div class="flex flex-col gap-1 my-1">
          {#each commitments.items as item}
            {@const parts = item.split(":")}
            {@const boldPart = parts[0]}
            {@const normalPart = parts.slice(1).join(":")}
            <div
              class="flex items-center gap-2 px-2 py-1 bg-white/70 border border-emerald-500/5 rounded-lg"
            >
              <svg
                class="w-3 h-3 text-emerald-500 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="3.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <div class="flex flex-col min-w-0 leading-normal py-0.5">
                <span
                  class="text-[10.5px] font-black text-slate-800 leading-tight"
                  >{boldPart.trim()}</span
                >
                {#if normalPart}
                  <span class="text-[9.5px] text-gray-500 leading-tight mt-0.5"
                    >{normalPart.trim()}</span
                  >
                {/if}
              </div>
            </div>
          {/each}
        </div>

        <!-- Mobile Slate FOMO Ribbon (Clickable entire ribbon) -->
        <a
          href="/chinh-sach-doi-tra-hoan-tien.html"
          class="flex items-center justify-between gap-3 pt-2 border-t border-emerald-500/10 mt-1 group no-underline text-slate-700 hover:text-emerald-600 transition-all duration-300"
        >
          <div class="flex items-center gap-1.5 relative z-10 min-w-0">
            <svg
              class="w-3.5 h-3.5 text-emerald-500 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            <span
              class="text-[9.5px] font-black text-slate-800 uppercase tracking-wider shrink-0"
              >FREESHIP:</span
            >
            <span class="text-[10px] font-medium text-gray-500 truncate"
              >{commitments.fomo}</span
            >
          </div>

          <div
            class="flex items-center gap-0.5 relative z-10 shrink-0 text-emerald-600 text-[10px] font-bold group-hover:translate-x-1 transition-transform duration-300"
          >
            <span>Xem thêm</span>
            <svg
              class="w-2.5 h-2.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="3"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
        </a>
      </div>
    </div>
  {/if}

  <!-- GEO 2026: Mobile FAQ Section -->
  {#if product.metadata?.faqs && product.metadata.faqs.length > 0}
    <div class="mt-[10px] border-t border-gray-100 pt-[10px]">
      <h2 class="section-title">Câu hỏi thường gặp</h2>
      <div class="flex flex-col gap-2 mt-4">
        {#each product.metadata.faqs as faq, i}
          <div
            class="bg-gray-50/50 border border-gray-100 rounded-[5px] overflow-hidden transition-all {activeMobileFaq ===
            i
              ? 'border-[#ee4d2d]/30 bg-white shadow-sm'
              : ''}"
          >
            <button
              class="w-full flex items-center justify-between p-3 text-left bg-transparent border-none"
              onclick={() =>
                (activeMobileFaq = activeMobileFaq === i ? null : i)}
            >
              <h3
                class="text-[14px] font-bold text-gray-900 leading-tight pr-4"
              >
                {faq.question}
              </h3>
              <ChevronDown
                size={14}
                class="text-gray-400 transition-transform {activeMobileFaq === i
                  ? 'rotate-180 text-[#ee4d2d]'
                  : ''}"
              />
            </button>
            {#if activeMobileFaq === i}
              <div class="px-3 pb-3 animate-[fadeIn_0.2s_ease-out]">
                <p
                  class="text-[12px] text-gray-600 leading-relaxed border-t border-gray-50 pt-2"
                >
                  {faq.answer}
                </p>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</section>

<style>
  .content-section {
    padding: 6px 5px 10px 5px;
    background: white;
    overflow: hidden;
  }
  .section-title {
    font-size: 16px;
    font-weight: 700;
    color: #111;
    margin-bottom: 4px;
    border-left: 4px solid #ee4d2d;
    padding-left: 6px;
    text-transform: none;
    letter-spacing: -0.02em;
  }

  /* Elite V2.2: Smooth Description Truncation */
  .description-wrapper {
    position: relative;
    overflow: hidden;
    transition: max-height 0.8s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .description-wrapper.collapsed::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: linear-gradient(to bottom, transparent, white 90%);
    pointer-events: none;
  }

  .expand-btn-elite {
    background: transparent;
    border: none;
    color: #ee4d2d;
    font-size: 13px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin-top: 4px;
    padding: 6px;
    gap: 4px;
    border-radius: 0;
    box-shadow: none;
  }

  :global(.prose-osmo) {
    font-size: 14px !important; /* Sleek mobile e-commerce standard (Lazada/Shopee) */
    line-height: 1.6 !important;
    color: #374151 !important;
  }

  :global(.prose-osmo > *:first-child) {
    margin-top: 0 !important;
    padding-top: 0 !important;
  }

  :global(.prose-osmo p) {
    margin-bottom: 0.75rem !important;
    font-weight: 400 !important;
    letter-spacing: -0.011em !important;
  }

  /* Khử margin và tránh block-break gây vỡ hàng cho p trong li */
  :global(.prose-osmo li p) {
    display: inline !important;
    margin-bottom: 0 !important;
  }

  :global(.prose-osmo h2, .prose-osmo h3) {
    color: #6b7280 !important;
    font-weight: 900 !important;
    margin-top: 1rem !important;
    margin-bottom: 0.3rem !important;
    line-height: 1.3 !important;
  }

  :global(.prose-osmo ul) {
    margin-bottom: 1rem !important;
    padding-left: 0 !important;
    list-style: none !important;
  }

  :global(.prose-osmo ol) {
    counter-reset: osmo-counter;
    margin-bottom: 1rem !important;
    padding-left: 0 !important;
    list-style: none !important;
  }

  :global(.prose-osmo ul li) {
    margin-bottom: 0.5rem !important;
    position: relative !important;
    padding-left: 0 !important;
  }

  :global(.prose-osmo ol li) {
    margin-bottom: 0.5rem !important;
    position: relative !important;
    padding-left: 0 !important;
  }

  :global(.prose-osmo ul > li::before) {
    content: "✦" !important;
    position: static !important;
    display: inline-block !important;
    color: #ee4d2d !important;
    font-weight: bold !important;
    margin-right: 0.35rem !important;
  }

  :global(.prose-osmo ol > li) {
    counter-increment: osmo-counter;
  }

  :global(.prose-osmo ol > li::before) {
    content: counter(osmo-counter) "." !important;
    position: static !important;
    display: inline-block !important;
    color: #ee4d2d !important;
    font-weight: 900 !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    margin-right: 0.35rem !important;
  }

  :global(.prose-osmo img) {
    border-radius: 12px;
    margin: 1rem 0 !important;
    width: 100% !important;
    height: auto !important;
  }

  :global(.prose-osmo figure) {
    margin: 1rem 0 !important;
    display: block !important;
    text-align: center !important;
  }

  :global(.prose-osmo figure img) {
    margin-top: 0 !important;
    margin-bottom: 0.25rem !important;
  }

  :global(.prose-osmo figcaption) {
    text-align: center !important;
    display: block !important;
    margin-top: 0.25rem !important;
    font-size: 12px !important;
    color: #6b7280 !important;
    font-style: italic !important;
    line-height: 1.4 !important;
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

  /* Google SGE Highlights Styling (GEO 2026) */
  :global(.semantic-summary h2) {
    font-size: 15px !important;
    font-weight: 800 !important;
    color: #1f2937 !important;
    margin-top: 0 !important;
    margin-bottom: 10px !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
  }
  :global(.semantic-summary h2::first-letter) {
    text-transform: none !important;
  }
  :global(.semantic-summary .product-highlights) {
    list-style-type: none !important;
    padding-left: 0 !important;
    margin: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 6px !important;
  }
  :global(.semantic-summary .product-highlights li) {
    position: relative !important;
    padding-left: 18px !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
    color: #4b5563 !important;
  }
  :global(.semantic-summary .product-highlights li::before) {
    content: "•" !important;
    position: absolute !important;
    left: 4px !important;
    top: 0 !important;
    color: #10b981 !important; /* HSL Emerald Green Bullet */
    font-size: 16px !important;
    line-height: 1.1 !important;
  }
</style>
