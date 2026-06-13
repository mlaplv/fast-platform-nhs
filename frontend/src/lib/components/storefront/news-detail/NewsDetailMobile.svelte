<script lang="ts">
  import { onMount } from "svelte";
  import { beforeNavigate } from "$app/navigation";
  import { cubicOut } from "svelte/easing";
  import AudioLines from "@lucide/svelte/icons/audio-lines";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";

  // Svelte 5 safe slide transition workaround to prevent NaNpx errors
  function slide(node: HTMLElement, { duration = 200 } = {}) {
    const style = getComputedStyle(node);
    const opacity = +style.opacity;
    const height = parseFloat(style.height);
    const padding_top = parseFloat(style.paddingTop);
    const padding_bottom = parseFloat(style.paddingBottom);
    const margin_top = parseFloat(style.marginTop);
    const margin_bottom = parseFloat(style.marginBottom);
    const border_top_width = parseFloat(style.borderTopWidth);
    const border_bottom_width = parseFloat(style.borderBottomWidth);

    const h = isNaN(height) ? 0 : height;
    const pt = isNaN(padding_top) ? 0 : padding_top;
    const pb = isNaN(padding_bottom) ? 0 : padding_bottom;
    const mt = isNaN(margin_top) ? 0 : margin_top;
    const mb = isNaN(margin_bottom) ? 0 : margin_bottom;
    const btw = isNaN(border_top_width) ? 0 : border_top_width;
    const bbw = isNaN(border_bottom_width) ? 0 : border_bottom_width;

    return {
      duration,
      easing: cubicOut,
      css: (t: number) => `
        overflow: hidden;
        opacity: ${t * opacity};
        height: ${t * h}px;
        padding-top: ${t * pt}px;
        padding-bottom: ${t * pb}px;
        margin-top: ${t * mt}px;
        margin-bottom: ${t * mb}px;
        border-top-width: ${t * btw}px;
        border-bottom-width: ${t * bbw}px;
      `
    };
  }

  import NewsMobileReviews from "./NewsMobileReviews.svelte";
  import { resolveMediaUrl, resolveOptimizedImageUrl } from "$lib/state/utils";
  interface Props {
    article: {
      id: string;
      title: string;
      author?: string;
      publishedAt?: string;
      content?: string;
      featuredImage?: string;
      category?: string;
      metadata?: {
        faqs?: { question: string; answer: string }[];
      };
    };
  }
  let { article: rawArticle }: Props = $props();

  interface RawArticleExt {
    featured_image?: string;
    created_at?: string;
    published_at?: string;
    author_name?: string;
  }

  // Elite V2.2: Safe API Property Normalization
  const article = $derived.by(() => {
    if (!rawArticle) {
      return {
        id: "",
        title: "",
        featuredImage: "",
        publishedAt: "",
        author: "System",
        content: "",
        category: "",
        metadata: { faqs: [] }
      };
    }
    const ext = rawArticle as Props['article'] & RawArticleExt;
    return {
      ...rawArticle,
      featuredImage: rawArticle.featuredImage || ext.featured_image || "",
      publishedAt: rawArticle.publishedAt || ext.created_at || ext.published_at || "",
      author: rawArticle.author || ext.author_name || "System"
    };
  });

  // SGE Shield V1.0: Deterministic DOM Entropy
  const wrapperTags = ["div", "article", "section", "main"];
  const seedLength = $derived(article?.title ? article.title.length : 10);
  const outerWrapper = $derived(wrapperTags[seedLength % wrapperTags.length]);

  const innerTags = ["div", "section"];
  const innerWrapper = $derived(innerTags[(seedLength + 3) % innerTags.length]);

  // Elite V2.2: Simple Pro Sentence Case
  const formattedTitle = $derived(
    article.title
      ? article.title.charAt(0).toUpperCase() + article.title.slice(1)
      : "",
  );

  // Elite V2.2: Professional Mobile Accordion State
  let activeFaq = $state<number | null>(null);
  let loadBelowFold = $state(false);

  onMount(() => {
    // Defer dynamic loading of below-the-fold modules to maximize FCP & LCP PageSpeed metrics
    if (typeof window !== "undefined") {
      if ("requestIdleCallback" in window) {
        requestIdleCallback(() => {
          loadBelowFold = true;
        });
      } else {
        setTimeout(() => {
          loadBelowFold = true;
        }, 200);
      }
    }
  });

  $effect(() => {
    if (activeFaq === null && article.metadata?.faqs?.length > 0) {
      activeFaq = 0;
    }
  });

  async function toggleFaq(i: number) {
    if (activeFaq === i) {
      activeFaq = null;
      return;
    }

    if (activeFaq !== null) {
      activeFaq = null;
      // Wait for closing slide transition (200ms) + small buffer
      await new Promise((r) => setTimeout(r, 210));
    }

    activeFaq = i;
  }

  // ─────────────────────────────────────────────────────────────────
  // 🎙️ TTS: WEB AUDIO ENGINE (Elite V7.0 - OS-Codec-Free)
  // Ported from MobileProductDetailsModal – adapted for article content
  // ─────────────────────────────────────────────────────────────────
  let contentRef: HTMLElement | null = $state(null);
  const articleId: string = $derived(article?.id || "unknown");

  let isReading: boolean = $state(false);
  let isBuffering: boolean = $state(false);
  let currentAudio: HTMLAudioElement | null = $state(null);
  let abortController: AbortController | null = null;
  const CACHE_NAME: string = "osmo-tts-v2";

  /**
   * Elite V7.1: TTS Text Sanitizer
   * Strips emojis, pictographs, decorative Unicode, Roman numerals
   * that edge-tts reads aloud as gibberish.
   */
  function sanitizeTtsText(raw: string): string {
    const romanMap: Record<string, string> = {
      XX: "hai mươi", XIX: "mười chín", XVIII: "mười tám", XVII: "mười bảy",
      XVI: "mười sáu", XV: "mười lăm", XIV: "mười bốn", XIII: "mười ba",
      XII: "mười hai", XI: "mười một", X: "10", IX: "chín", VIII: "tám",
      VII: "bảy", VI: "sáu", V: "năm", IV: "bốn", III: "ba", II: "hai", I: "một",
    };
    const romanRegex =
      /\b(XX|XIX|XVIII|XVII|XVI|XV|XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)\b/g;

    return raw
      .replace(romanRegex, (match, _u, offset, str) => {
        if (match === "X") {
          const before = str[offset - 1] ?? "";
          const after = str[offset + 1] ?? "";
          const isIsolated =
            (!before || /\s|[.,;!?"'‑-]/.test(before)) &&
            (!after || /\s|[.,;!?"'‑-]/.test(after));
          return isIsolated ? "10" : match;
        }
        return romanMap[match] || match;
      })
      .replace(/\p{Extended_Pictographic}/gu, "")
      .replace(/[\u2600-\u27BF]/g, "")
      .replace(/[\u{1F000}-\u{1FFFF}]/gu, "")
      .replace(/[\uFE00-\uFE0F\u200D]/g, "")
      .replace(/\(\s*[A-Za-z][A-Za-z\s\-']{0,40}\s*\)/g, "")
      .replace(/^\s*[-–—]\s*/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  async function toggleSpeech(): Promise<void> {
    if (isReading || isBuffering) {
      stopSpeech();
      return;
    }

    const proseEl = contentRef?.querySelector(".elite-prose-mobile") as HTMLElement;
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
      const cachedResponse = await cache.match(`/tts/${articleId}`);

      if (cachedResponse) {
        const blob = await cachedResponse.blob();
        if (blob.size > 500 && blob.type.startsWith("audio/")) {
          audioUrl = URL.createObjectURL(blob);
          usedCache = true;
        } else {
          await cache.delete(`/tts/${articleId}`);
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
        audioUrl = `/api/v1/client/tts/stream?id=${id}`;
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
        const savedTime = localStorage.getItem(`tts_pos_${articleId}`);
        if (savedTime) audio.currentTime = parseFloat(savedTime);
      };

      audio.ontimeupdate = () => {
        if (audio.currentTime > 0) {
          localStorage.setItem(`tts_pos_${articleId}`, audio.currentTime.toString());
        }
      };

      audio.onended = () => {
        localStorage.removeItem(`tts_pos_${articleId}`);
        localStorage.setItem(`tts_done_${articleId}`, "true");
        cleanup();
      };

      audio.onerror = () => {
        caches.open(CACHE_NAME).then((c) => c.delete(`/tts/${articleId}`)).catch(() => {});
        cleanup();
      };

      await audio.play();
    } catch (e: unknown) {
      const err = e as Error;
      if (err?.name !== "AbortError") console.error("[TTS] Error:", err);
      caches.open(CACHE_NAME).then((c) => c.delete(`/tts/${articleId}`)).catch(() => {});
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

  // Dispose TTS on page leave / component destroy
  $effect(() => () => cleanup());

  beforeNavigate(() => {
    stopSpeech();
  });
</script>

<svelte:element this={outerWrapper} class="bg-white min-h-screen text-gray-900">
  <!-- Clean Header for All Pages on Mobile -->
  <div class="bg-white border-b border-gray-100 sticky top-0 z-30">
    <div class="flex items-center gap-4 px-4 py-3">
      <button
        onclick={() => history.back()}
        class="w-8 h-8 flex items-center justify-center text-gray-900 active:scale-90 transition-transform"
      >
        <svg
          class="w-6 h-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2.5"
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>
      <h1 class="text-base font-black text-gray-900 tracking-tight truncate flex-1">
        {article.title}
      </h1>
      <!-- 🎙️ TTS Header Capsule -->
      <button
        onclick={toggleSpeech}
        class="tts-pill relative flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-all duration-300 active:scale-90 select-none shrink-0
          {isReading
            ? 'tts-pill--reading'
            : isBuffering
              ? 'tts-pill--buffering'
              : 'tts-pill--idle'}"
        aria-label={isReading ? "Dừng đọc" : "Nghe bài viết"}
      >
        {#if isBuffering}
          <div class="relative w-3.5 h-3.5 shrink-0">
            <div class="absolute inset-0 border-[1.5px] border-white/30 rounded-full"></div>
            <div class="absolute inset-0 border-[1.5px] border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          <span class="text-[11px] font-bold text-white">Đang tải...</span>
        {:else if isReading}
          <div class="flex items-end gap-[2px] h-[14px] shrink-0">
            <div class="w-[2.5px] bg-white rounded-full news-bar-1"></div>
            <div class="w-[2.5px] bg-white/90 rounded-full news-bar-2"></div>
            <div class="w-[2.5px] bg-white rounded-full news-bar-3"></div>
            <div class="w-[2.5px] bg-white/80 rounded-full news-bar-2"></div>
            <div class="w-[2.5px] bg-white rounded-full news-bar-1"></div>
          </div>
          <span class="text-[11px] font-bold text-white">Đang đọc...</span>
        {:else}
          <span class="relative flex shrink-0">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#C18F7E] opacity-50"></span>
            <span class="relative inline-flex"><AudioLines size={14} strokeWidth={2.5} /></span>
          </span>
          <span class="text-[11px] font-bold">Nghe bài</span>
        {/if}
      </button>
    </div>
  </div>

  <!-- News Article Meta Info (Below Header) -->
  {#if article.category !== "Chính sách"}
    <div class="px-[10px] pt-5">
      <div class="flex items-center gap-2 mb-3">
        <span class="bg-[#C18F7E]/10 text-[#C18F7E] px-2.5 py-1 text-[9px] font-black tracking-widest rounded-full uppercase">
          {article.category || "HƯỚNG DẪN CHUYÊN MÔN"}
        </span>
        <span class="bg-gray-100 text-gray-500 px-2.5 py-1 text-[9px] font-black tracking-widest rounded-full uppercase">
          ⏱️ 5 PHÚT ĐỌC
        </span>
      </div>

      <h1 class="text-2xl font-black text-gray-900 leading-[1.25] tracking-tight mb-4">
        {article.title}
      </h1>

      <div class="flex items-center gap-2 pb-1 mb-2">
        <div class="w-5 h-5 rounded-full bg-gradient-to-tr from-[#C18F7E] to-[#E5C3B3] flex items-center justify-center shadow-sm shadow-[#C18F7E]/20 shrink-0">
          <svg class="w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor"/>
          </svg>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-[10px] font-black text-gray-900 tracking-wider">
            {article.author === "Xohi" || article.author === "System" || article.author === "Osmo" ? "Ban biên tập osmo" : article.author}
          </span>
          <span class="text-gray-300 text-[10px] font-light">•</span>
          <span class="text-[9px] font-bold text-gray-400 tracking-tight">
            {article.publishedAt}
          </span>
        </div>
      </div>
    </div>
  {/if}

  <!-- Featured Image (Full-Width, Unrounded) -->
  {#if article.featuredImage && article.featuredImage.trim() !== ""}
    <div class="w-full mb-4 bg-gray-50 flex items-center justify-center">
      <img
        src={resolveOptimizedImageUrl(article.featuredImage, 600)}
        alt={article.title}
        class="w-full h-auto object-contain block"
        loading="eager"
        fetchpriority="high"
        decoding="async"
      />
    </div>
  {/if}

  <!-- Content Reader (Elite Prose) -->
  <div bind:this={contentRef}>
    <svelte:element this={innerWrapper} class="px-[5px] py-0 elite-prose-mobile">
      {@html article.content}
    </svelte:element>
  </div>

  <!-- GEO 2026: FAQ Section (Full Width Redesign) -->
  {#if article.metadata?.faqs && article.metadata.faqs.length > 0}
    <div class="py-8 px-4 bg-gray-50/50 border-y border-gray-100/80">
      <div class="mb-6 flex flex-col gap-1.5 px-1">
        <div class="flex items-center gap-2">
          <span class="w-4 h-[1.5px] bg-[#C18F7E]"></span>
          <span class="text-[9px] font-black tracking-[0.25em] text-[#C18F7E] uppercase">Hỏi đáp chuyên môn</span>
        </div>
        <h2 class="text-[16px] font-black text-[#0f172a] tracking-tight">
          Câu hỏi thường gặp
        </h2>
      </div>

      <div class="space-y-3">
        {#each article.metadata.faqs as faq, i}
          <div
            class="bg-white border border-gray-100/90 rounded-xl overflow-hidden transition-all duration-300 {activeFaq === i ? 'shadow-[0_8px_20px_rgba(193,143,126,0.06)] border-[#C18F7E]/25' : 'shadow-sm'}"
          >
            <button
              class="w-full flex items-start justify-between p-4 cursor-pointer select-none text-left bg-transparent border-none outline-none active:bg-gray-50/40 transition-colors"
              onclick={() => toggleFaq(i)}
            >
              <span
                class="text-[14px] font-bold leading-snug transition-colors duration-200 {activeFaq === i
                  ? 'text-[#C18F7E]'
                  : 'text-[#0f172a]'} pr-4"
              >
                {faq.question}
              </span>
              <ChevronDown
                size={16}
                class="text-[#C18F7E]/80 shrink-0 transition-transform duration-300 mt-0.5 {activeFaq === i ? 'rotate-180' : ''}"
              />
            </button>

            {#if activeFaq === i}
              <div
                class="px-4 pb-4 pt-0 text-[13.5px] text-gray-600 leading-relaxed"
                transition:slide={{ duration: 200 }}
              >
                <div class="pt-3 border-t border-gray-50 flex gap-3">
                  <div class="w-1 bg-gradient-to-b from-[#C18F7E]/40 to-[#C18F7E]/10 rounded-full shrink-0"></div>
                  <div class="flex-1 text-[#344054] leading-relaxed font-medium">
                    {faq.answer}
                  </div>
                </div>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- News Review Integration -->
  {#if article.category !== "Chính sách"}
    {#if loadBelowFold}
      <NewsMobileReviews articleId={article.id} slug={article.title} />
    {:else}
      <div class="h-[150px] bg-white flex flex-col items-center justify-center text-gray-300 gap-2 border-t border-gray-100">
        <div class="w-8 h-8 rounded-full border-2 border-gray-100 animate-spin" style="border-top-color: var(--color-luxury-copper, #C18F7E);"></div>
        <span class="text-[10px] font-black tracking-widest uppercase">Đang tải bình luận...</span>
      </div>
    {/if}
  {/if}

  <!-- Footer Navigation -->
  <div class="p-10 text-center border-t border-gray-100 bg-gray-50">
    <span class="text-[10px] font-black text-gray-300 tracking-[0.4em]"
      >Kết thúc bài viết</span
    >
    <div class="mt-6">
      <a
        href="/bai-viet"
        class="inline-block px-10 py-4 bg-[#0f172a] text-white text-[10px] font-black tracking-widest active:scale-95 transition-all shadow-xl"
      >
        Quay về kho tin
      </a>
    </div>
  </div>


</svelte:element>

<style>
  :global(.elite-prose-mobile) {
    font-size: 1.05rem;
    line-height: 1.6;
    color: #374151;
    word-break: break-word;
    overflow-wrap: break-word;
  }

  :global(.elite-prose-mobile a) {
    color: inherit !important;
    text-decoration: none !important;
    font-weight: inherit !important;
    cursor: pointer;
  }

  :global(.elite-prose-mobile p) {
    margin: 0.75rem 0;
    font-weight: 400;
  }

  :global(.elite-prose-mobile h1) {
    font-size: 1.75rem;
    font-weight: 950;
    color: #111827 !important;
    margin: 2rem 0 0.75rem 0;
    text-transform: none;
    line-height: 1.1;
  }

  :global(.elite-prose-mobile h2) {
    font-size: 1.35rem;
    font-weight: 950;
    color: #0f172a !important;
    margin: 1.5rem 0 0.5rem 0;
    text-transform: none;
    letter-spacing: -0.02em;
    border-left: 4px solid #c18f7e;
    padding-left: 0.75rem;
    line-height: 1.2;
  }

  :global(.elite-prose-mobile strong),
  :global(.elite-prose-mobile b) {
    color: #111827 !important;
    font-weight: 850;
  }

  :global(.elite-prose-mobile h3) {
    font-size: 1.15rem;
    font-weight: 900;
    color: #0f172a !important;
    margin: 1.25rem 0 0.5rem 0;
    text-transform: none;
  }

  /* ELITE V2.2: Viral 2026 Professional Highlights (Luxury Copper) */
  :global(.elite-prose-mobile span[style*="background-color"]),
  :global(.elite-prose-mobile span[style*="background: rgb(226, 244, 255)"]) {
    background-color: #fff0f0 !important;
    padding: 2px 4px !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    color: #c18f7e !important;
  }

  /* Specific callout blocks should use div */
  :global(.elite-prose-mobile div[style*="background-color"]),
  :global(.elite-prose-mobile div[style*="background: rgb(226, 244, 255)"]),
  :global(.elite-prose-mobile section[style*="background-color"]) {
    padding: 1.5rem !important;
    border-radius: 0 !important;
    border-left: 6px solid #c18f7e !important;
    color: #0f172a !important;
    background: linear-gradient(90deg, #fff0f0 0%, #ffffff 100%) !important;
    margin: 2rem 0 !important;
    font-weight: 800 !important;
    line-height: 1.3 !important;
    letter-spacing: -0.02em !important;
    box-shadow: 10px 10px 30px rgba(193, 143, 126, 0.08) !important;
  }

  :global(.elite-prose-mobile [style*="background-color"] *) {
    color: inherit !important;
  }

  :global(.elite-prose-mobile img) {
    border: none !important;
    outline: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    margin: 1rem auto !important;
    max-width: 100% !important;
    height: auto !important;
    display: block !important;
  }

  :global(.elite-prose-mobile blockquote) {
    border-left: 5px solid #c18f7e;
    padding: 1rem 1.25rem;
    font-style: italic;
    font-size: 1.1rem;
    font-weight: 500;
    color: #4b5563;
    background: #fff0f0;
    margin: 1.5rem 0;
  }

  :global(.elite-prose-mobile ul) {
    list-style-type: none;
    padding-left: 0;
    margin: 1rem 0;
  }

  :global(.elite-prose-mobile li) {
    margin-bottom: 0.5rem;
    padding-left: 1.25rem;
    position: relative;
    font-weight: 500;
  }

  /* 🎙️ TTS Pill - Viral FOMO Capsule */
  .tts-pill--idle {
    background: linear-gradient(135deg, #fff5f2 0%, #fff0ee 100%);
    color: #C18F7E;
    border: 1.5px solid rgba(193,143,126,0.3);
    box-shadow: 0 2px 10px rgba(193,143,126,0.12);
  }
  .tts-pill--buffering {
    background: linear-gradient(135deg, #C18F7E 0%, #e8a898 100%);
    color: white;
    border: 1.5px solid transparent;
    box-shadow: 0 4px 20px rgba(193,143,126,0.45);
  }
  .tts-pill--reading {
    background: linear-gradient(135deg, #c47a6a 0%, #C18F7E 50%, #e8a898 100%);
    color: white;
    border: 1.5px solid transparent;
    box-shadow:
      0 4px 24px rgba(193,143,126,0.55),
      0 0 0 4px rgba(193,143,126,0.12),
      0 0 0 8px rgba(193,143,126,0.06);
    animation: tts-glow-pulse 2s infinite ease-in-out;
  }

  @keyframes tts-glow-pulse {
    0%, 100% { box-shadow: 0 4px 24px rgba(193,143,126,0.55), 0 0 0 4px rgba(193,143,126,0.12), 0 0 0 8px rgba(193,143,126,0.06); }
    50%       { box-shadow: 0 6px 32px rgba(193,143,126,0.75), 0 0 0 6px rgba(193,143,126,0.18), 0 0 0 12px rgba(193,143,126,0.08); }
  }

  /* 🎚️ News Equalizer Bars (5 bars, varied rhythm) */
  @keyframes news-bar {
    0%, 100% { height: 3px; }
    50%       { height: 18px; }
  }
  .news-bar-1 { animation: news-bar 0.55s infinite ease-in-out; }
  .news-bar-2 { animation: news-bar 0.75s infinite ease-in-out 0.15s; }
  .news-bar-3 { animation: news-bar 0.65s infinite ease-in-out 0.3s; }

  :global(.elite-prose-mobile li::before) {
    content: "";
    position: absolute;
    left: 0;
    top: 0.7em;
    width: 8px;
    height: 2px;
    background: #c18f7e;
  }
</style>
