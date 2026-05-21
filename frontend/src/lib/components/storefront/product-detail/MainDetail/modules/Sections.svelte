<script lang="ts">
  import type { Product, BarcodeVerificationResponse } from "$lib/types";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Beaker from "@lucide/svelte/icons/beaker";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Info from "@lucide/svelte/icons/info";
  import X from "@lucide/svelte/icons/x";
  import {
    getIngredientIcon,
    parseDescriptionAndCommitments,
  } from "$lib/utils/product";
  import VerificationCenter from "../../shared/VerificationCenter.svelte";
  import ScannerHUD from "../../shared/ScannerHUD.svelte";
  import { fly, fade } from "svelte/transition";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";

  interface Props {
    product: Product;
    productInfo: {
      barcode: string;
      brand: string;
      origin: string;
      weight: string;
      originalPrice: number;
      salePrice: number;
    };
    visibleAttributes: [string, string | number | object][];
  }

  let { product, productInfo, visibleAttributes }: Props = $props();
  let showVerification = $state(false);
  let isScanning = $state(false);
  let verificationData = $state<BarcodeVerificationResponse | null>(null);
  let activeFaq = $state<number | null>(null);

  const parsedDescription = $derived(
    parseDescriptionAndCommitments(product.description),
  );

  $effect(() => {
    if (activeFaq === null && product.metadata?.faqs?.length > 0) {
      activeFaq = 0;
    }
  });

  function triggerScan() {
    isScanning = true;
    showVerification = false;
  }

  function handleScanComplete(event: {
    verificationData: BarcodeVerificationResponse;
  }) {
    console.log(
      "🧬 [Sections] Scan complete received:",
      $state.snapshot(event),
    );
    isScanning = false;
    verificationData = event.verificationData;
    showVerification = true;
  }

  function isJson(str: string): boolean {
    if (typeof str !== "string" || !str) return false;
    try {
      const parsed: Record<string, unknown> = JSON.parse(str);
      return (
        typeof parsed === "object" &&
        parsed !== null &&
        ("hero_headline" in parsed || "spec_bento" in parsed)
      );
    } catch {
      return false;
    }
  }
</script>

<div class="max-w-[1200px] mx-auto flex flex-col gap-0 mb-0 pt-0">
  <!-- CHI TIẾT SẢN PHẨM -->
  <div
    class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50"
  >
    <div
      class="flex items-center justify-between mb-3 pb-2 border-b border-gray-50"
    >
      <div class="flex items-center gap-3">
        <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
        <h2 class="text-[24px] font-black text-gray-900 tracking-tight">
          Chi tiết
        </h2>
      </div>
      <button
        id="btn-verify-product"
        class="flex flex-col items-end group/sku cursor-pointer hover:scale-105 transition-transform bg-transparent border-none p-0"
        onclick={triggerScan}
      >
        <span
          class="text-[9px] font-black text-gray-400 tracking-widest group-hover/sku:text-[#ee4d2d]"
          >Serial / SKU</span
        >
        <span
          class="text-[12px] font-black text-black tracking-widest group-hover/sku:text-[#ee4d2d]"
          >{product.sku || "N/A"}</span
        >
      </button>
    </div>

    <div
      class="flex items-stretch bg-gray-50/50 border border-gray-100 divide-x divide-gray-100 rounded-none mb-6 overflow-hidden"
    >
      {#if productInfo.brand}
        <div
          class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all group/spec cursor-default"
        >
          <span
            class="text-[9px] text-gray-400 font-black tracking-[0.25em] mb-2 flex items-center gap-2"
          >
            <div class="w-1 h-1 rounded-full bg-amber-400 animate-pulse"></div>
            Thương hiệu
          </span>
          <a
            href="/products?brand={encodeURIComponent(productInfo.brand)}"
            class="text-[14px] font-black text-[#ee4d2d] hover:underline flex items-center gap-1.5 tracking-tight"
          >
            {productInfo.brand}
            <svg
              class="w-3.5 h-3.5 opacity-0 group-hover/spec:opacity-100 transition-all translate-x-[-5px] group-hover/spec:translate-x-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="3"
                d="M9 5l7 7-7 7"
              /></svg
            >
          </a>
        </div>
      {/if}
      {#if productInfo.origin}
        <div
          class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all"
        >
          <span
            class="text-[9px] text-gray-400 font-black tracking-[0.25em] mb-2 flex items-center gap-2"
          >
            <div class="w-1 h-1 rounded-full bg-blue-400"></div>
            Xuất xứ
          </span>
          <span class="text-[14px] font-black text-gray-800 tracking-tighter"
            >{productInfo.origin}</span
          >
        </div>
      {/if}
      {#if productInfo.weight}
        <div
          class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all"
        >
          <span
            class="text-[9px] text-gray-400 font-black tracking-[0.25em] mb-2 flex items-center gap-2"
          >
            <div class="w-1 h-1 rounded-full bg-emerald-400"></div>
            Quy cách
          </span>
          <span class="text-[14px] font-black text-gray-800"
            >{productInfo.weight}</span
          >
        </div>
      {/if}
      <div
        class="flex-[1.5] px-8 py-5 flex flex-col justify-center hover:bg-white transition-all"
      >
        <span
          class="text-[9px] text-gray-400 font-black tracking-[0.25em] mb-2 flex items-center gap-2"
        >
          <div class="w-1 h-1 rounded-full bg-indigo-400"></div>
          Danh mục
        </span>
        <div
          class="flex items-center gap-2 text-[13px] font-bold tracking-tighter"
        >
          <a
            href="/products"
            class="text-gray-400 hover:text-gray-900 transition-colors">osmo</a
          >
          <svg
            class="w-3 h-3 text-gray-200"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="3"
              d="M9 5l7 7-7 7"
            /></svg
          >
          <a
            href="/{product.categorySlug || 'products'}/"
            class="text-gray-900 hover:text-[#ee4d2d] hover:underline transition-colors truncate"
          >
            {product.category || "Chăm sóc da"}
          </a>
        </div>
      </div>

      <!-- THÔNG SỐ KỸ THUẬT KHÁC (Hợp nhất vào 1 hàng) -->
      {#each visibleAttributes as [key, value]}
        <div
          class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all"
        >
          <span
            class="text-[9px] text-gray-400 font-black tracking-[0.25em] uppercase mb-2 flex items-center gap-2"
          >
            <div class="w-1 h-1 rounded-full bg-gray-300"></div>
            {key.replace(/_/g, " ")}
          </span>
          {#if key.toLowerCase().includes("sku") || key
              .toLowerCase()
              .includes("serial") || key.toLowerCase().includes("barcode")}
            <button
              class="text-[14px] text-[#ee4d2d] font-black hover:underline cursor-pointer bg-transparent border-none p-0 flex items-center gap-1 text-left"
              onclick={triggerScan}
            >
              {value}
              <div
                class="w-1.5 h-1.5 bg-green-500 rounded-full animate-ping"
              ></div>
            </button>
          {:else}
            <span class="text-[14px] font-black text-gray-800 tracking-tighter"
              >{value}</span
            >
          {/if}
        </div>
      {/each}
    </div>

    <div class="text-[14px] space-y-10">
      <div class="grid grid-cols-1 gap-6 w-full">
        {#if product.metadata?.featured_ingredients && product.metadata.featured_ingredients.length > 0}
          <div class="flex flex-col gap-3 py-2">
            <h2
              class="flex items-center gap-2 text-[16px] font-bold text-gray-800 tracking-tight"
            >
              <Sparkles size={16} class="text-amber-500" /> Thành phần nổi bật
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              {#each product.metadata.featured_ingredients as ing}
                <div
                  class="flex gap-3 bg-[#fdf2f2]/50 border border-[#ee4d2d]/5 p-3 rounded-none hover:bg-white hover:shadow-xl hover:shadow-[#ee4d2d]/5 transition-all group/ing"
                >
                  <div
                    class="w-10 h-10 shrink-0 bg-white border border-[#ee4d2d]/10 rounded-none flex items-center justify-center text-[18px] group-hover/ing:scale-110 transition-transform shadow-sm"
                  >
                    {ing.icon || getIngredientIcon(ing.name)}
                  </div>
                  <div class="flex flex-col justify-center">
                    <span
                      class="text-[15px] font-bold text-gray-900 leading-tight mb-0.5"
                      >{ing.name}</span
                    >
                    <span class="text-[13px] text-gray-500 leading-normal"
                      >{ing.benefit}</span
                    >
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if product.metadata?.ingredients}
          <div class="flex flex-col gap-2 py-1">
            <div
              class="flex items-center gap-2 text-[16px] font-bold text-gray-800 tracking-tight"
            >
              <Beaker size={16} class="text-teal-500" /> Bảng thành phần
            </div>
            <div
              class="bg-gray-50/50 border border-gray-100 p-4 rounded-none relative overflow-hidden group/inci"
            >
              <div
                class="absolute top-0 right-0 p-2 opacity-10 group-hover/inci:opacity-30 transition-opacity"
              >
                <FlaskConical size={40} />
              </div>
              <p
                class="text-[13px] text-gray-600 font-mono leading-relaxed tracking-tight relative z-10"
              >
                {product.metadata.ingredients}
              </p>
              <div
                class="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2"
              >
                <Info size={12} class="text-blue-500" />
                <span class="text-[11px] text-gray-400 font-bold italic"
                  >Bảng thành phần công bố (chi tiết có trên hộp / tem nhãn sản
                  phẩm chính hãng)</span
                >
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- ELITE V2.2: SCANNER HUD & VERIFICATION CENTER -->
  {#if isScanning}
    <ScannerHUD barcode={product.sku} oncomplete={handleScanComplete} />
  {/if}

  {#if showVerification}
    <div
      class="fixed inset-0 z-[10001] flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl"
      transition:fade
    >
      <div
        class="bg-[#0a0a0a]/90 backdrop-blur-3xl w-full max-w-5xl p-0 shadow-[0_20px_100px_rgba(0,0,0,1)] border border-white/10 rounded-[5px] overflow-hidden relative"
        in:fly={{ y: 50, duration: 600 }}
      >
        <button
          class="absolute top-0 right-0 text-white/40 hover:text-white z-20 transition-all w-8 h-8 flex items-center justify-center hover:bg-white/10 rounded-bl-[5px]"
          onclick={() => (showVerification = false)}
        >
          <X size={18} />
        </button>
        <div
          class="relative z-10 pt-10 px-10 pb-2 max-h-[90vh] overflow-y-auto custom-scrollbar"
        >
          <VerificationCenter {product} {verificationData} />
        </div>
      </div>
    </div>
  {/if}

  <!-- MÔ TẢ SẢN PHẨM -->
  <div
    class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50"
  >
    <div
      class="flex items-center justify-between mb-3 pb-2 border-b border-gray-50"
    >
      <div class="flex items-center gap-3">
        <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
        <h2 class="text-[24px] font-black text-gray-900 tracking-tight">
          Mô tả
        </h2>
      </div>
    </div>
    <div class="px-0 prose-osmo">
      {#if isJson(product.description)}
        <div class="bg-slate-900 text-white p-4 rounded-none">
          <InteractiveDashboard data={product.description} compact={false} />
        </div>
      {:else}
        {@html parsedDescription.cleanDescription ||
          "Chưa có mô tả chi tiết cho sản phẩm này."}
      {/if}
    </div>

    {#if parsedDescription.commitments}
      {@const commitments = parsedDescription.commitments}
      <div
        class="commitment-card-luxury mt-8 p-5 rounded-2xl border border-emerald-500/10 bg-white/40 relative overflow-hidden shadow-[0_15px_30px_rgba(4,120,87,0.02)] backdrop-blur-md transition-all duration-300"
      >
        <!-- Subtle backlights -->
        <div
          class="absolute -top-12 -right-12 w-32 h-32 rounded-full bg-emerald-100/20 blur-2xl pointer-events-none"
        ></div>
        <div
          class="absolute -bottom-12 -left-12 w-32 h-32 rounded-full bg-teal-100/20 blur-2xl pointer-events-none"
        ></div>

        <div class="relative z-10 flex flex-col gap-3">
          <!-- Compact Row 1: Header (title | subtitle) - Prevent title compression -->
          <div class="flex flex-col sm:flex-row sm:items-center gap-2 pb-3 border-b border-emerald-500/10">
            <div class="flex items-center gap-2 shrink-0">
              <span
                class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"
              ></span>
              <span
                class="text-[12px] font-black text-slate-800 uppercase tracking-widest shrink-0 whitespace-nowrap"
                >{commitments.title}</span
              >
            </div>
            {#if commitments.subtitle}
              <span class="text-gray-300 hidden sm:inline shrink-0">|</span>
              <span
                class="text-[11.5px] font-black text-[#ee4d2d] tracking-tight leading-normal"
                >{commitments.subtitle}</span
              >
            {/if}
          </div>

          <!-- Compact Row 2: Grid of 3 items -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {#each commitments.items as item}
              {@const parts = item.split(":")}
              {@const boldPart = parts[0]}
              {@const normalPart = parts.slice(1).join(":")}
              <div
                class="flex items-center gap-2.5 p-2 bg-white/70 border border-emerald-500/5 hover:border-emerald-500/20 hover:bg-white rounded-xl transition-all duration-300 group min-w-0"
              >
                <div
                  class="w-6 h-6 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-600 shrink-0"
                >
                  <svg
                    class="w-3.5 h-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    stroke-width="3"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <div class="flex flex-col min-w-0 leading-tight py-0.5">
                  <span class="text-[11.5px] font-black text-slate-800 leading-normal"
                    >{boldPart.trim()}</span
                  >
                  {#if normalPart}
                    <span class="text-[10px] text-gray-500 leading-normal mt-0.5"
                      >{normalPart.trim()}</span
                    >
                  {/if}
                </div>
              </div>
            {/each}
          </div>

          <!-- Compact Row 3: Simple Minimalist Viral Ribbon (No bg, no border) -->
          <a
            href="/chinh-sach-doi-tra-hoan-tien.html"
            class="flex items-center justify-between gap-4 pt-3 border-t border-emerald-500/10 mt-1 group no-underline text-slate-700 hover:text-emerald-600 transition-all duration-300"
          >
            <div class="flex items-center gap-2 min-w-0">
              <svg
                class="w-4 h-4 text-emerald-500 shrink-0"
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
                class="text-[10px] font-black text-slate-800 uppercase tracking-widest shrink-0"
                >FREESHIP & ĐỔI TRẢ:</span
              >
              <span class="text-[11px] font-medium text-gray-500 truncate"
                >{commitments.fomo}</span
              >
            </div>

            <div
              class="flex items-center gap-0.5 shrink-0 text-emerald-600 text-[11px] font-bold group-hover:translate-x-1 transition-transform duration-300"
            >
              <span>Xem thêm</span>
              <svg
                class="w-3 h-3"
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
  </div>

  <!-- FAQ Section (Elite V2.2 Accordion) -->
  {#if product.metadata?.faqs && product.metadata.faqs.length > 0}
    <div
      class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50"
    >
      <div
        class="flex items-center justify-between mb-3 pb-2 border-b border-gray-50"
      >
        <div class="flex items-center gap-3">
          <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
          <h2 class="text-[24px] font-black text-gray-900 tracking-tight">
            Câu hỏi thường gặp
          </h2>
        </div>
      </div>
      <div class="px-0 flex flex-col gap-2">
        {#each product.metadata.faqs as faq, i}
          <div
            class="border border-gray-100 rounded-[5px] transition-all {activeFaq ===
            i
              ? 'bg-white shadow-md border-[#ee4d2d]/30'
              : 'bg-gray-50/30'}"
          >
            <button
              class="w-full flex items-center justify-between p-4 text-left bg-transparent border-none cursor-pointer group"
              onclick={() => (activeFaq = activeFaq === i ? null : i)}
            >
              <h3
                class="text-[15px] font-bold text-gray-900 group-hover:text-[#ee4d2d] transition-colors"
              >
                {faq.question}
              </h3>
              <ChevronDown
                size={18}
                class="text-gray-400 transition-transform duration-300 {activeFaq ===
                i
                  ? 'rotate-180 text-[#ee4d2d]'
                  : ''}"
              />
            </button>

            {#if activeFaq === i}
              <div class="px-4 pb-4 animate-[fadeIn_0.3s_ease-out]">
                <p
                  class="text-[14px] text-gray-600 leading-relaxed w-full border-t border-gray-100 pt-3"
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
</div>

<style>
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-5px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Elite V2.2: Desktop Prose Heading Optimization */
  :global(.prose-osmo h2, .prose-osmo h3) {
    color: #6b7280 !important;
    font-weight: 900 !important;
    margin-top: 1rem !important;
    margin-bottom: 0.75rem !important;
    letter-spacing: -0.02em !important;
    text-transform: lowercase !important;
  }

  :global(.prose-osmo h2::first-letter, .prose-osmo h3::first-letter) {
    text-transform: uppercase !important;
  }
</style>
