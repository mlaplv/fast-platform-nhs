<script lang="ts">
  import { fade, slide, fly } from "svelte/transition";

  import NewsMobileReviews from "./NewsMobileReviews.svelte";
  import { resolveMediaUrl } from "$lib/state/utils";
  interface Props {
    article: {
      id: string;
      title: string;
      author: string;
      publishedAt: string;
      content: string;
      featuredImage: string;
      category?: string;
      metadata?: {
        faqs?: { question: string; answer: string }[];
      };
    };
  }
  let { article: rawArticle }: Props = $props();

  // Elite V2.2: Safe API Property Normalization
  const article = $derived({
    ...rawArticle,
    featuredImage: rawArticle.featuredImage || (rawArticle as any).featured_image || "",
    publishedAt: rawArticle.publishedAt || (rawArticle as any).created_at || (rawArticle as any).published_at || "",
    author: rawArticle.author || (rawArticle as any).author_name || "System"
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
      ? article.title.charAt(0).toUpperCase() +
          article.title.slice(1).toLowerCase()
      : "",
  );

  // Elite V2.2: Professional Mobile Accordion State
  let activeFaq = $state<number | null>(null);
  let showScrollTop = $state(false);

  $effect(() => {
    const handleScroll = () => {
      showScrollTop = window.scrollY > 400;
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
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
      <button
        class="w-8 h-8 flex items-center justify-center text-gray-900 active:scale-90 transition-transform"
      >
        <svg
          class="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2.5"
            d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
          />
        </svg>
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
        src={resolveMediaUrl(article.featuredImage)}
        alt={article.title}
        class="w-full h-auto object-contain block"
        loading="lazy"
      />
    </div>
  {/if}

  <!-- Content Reader (Elite Prose) -->
  <svelte:element this={innerWrapper} class="px-[5px] py-0 elite-prose-mobile">
    {@html article.content}
  </svelte:element>

  <!-- GEO 2026: FAQ Section (Full Width Redesign) -->
  {#if article.metadata?.faqs && article.metadata.faqs.length > 0}
    <div class="py-10 border-t border-gray-100">
      <h2
        class="px-[5px] text-[12px] font-black tracking-[0.2em] text-[#0f172a] mb-6 flex items-center gap-3"
      >
        <div class="w-1.5 h-1.5 bg-[#C18F7E] rounded-full"></div>
        Câu hỏi kỹ thuật
      </h2>
      <div class="divide-y divide-gray-50 border-y border-gray-50">
        {#each article.metadata.faqs as faq, i}
          <div class="bg-white">
            <button
              class="w-full flex items-center justify-between px-[5px] py-6 cursor-pointer select-none text-left bg-transparent border-none outline-none active:bg-gray-50/50 transition-colors"
              onclick={() => toggleFaq(i)}
            >
              <span
                class="text-[14px] font-bold {activeFaq === i
                  ? 'text-[#C18F7E]'
                  : 'text-[#0f172a]'} pr-4 leading-snug transition-colors"
                >{faq.question}</span
              >
              <svg
                class="w-4 h-4 text-[#C18F7E] shrink-0 transition-transform duration-300 {activeFaq ===
                i
                  ? 'rotate-180'
                  : ''}"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="3"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {#if activeFaq === i}
              <div
                class="px-[5px] pb-8 pt-0 text-[14px] text-gray-600 leading-relaxed italic"
                transition:slide={{ duration: 200 }}
              >
                {faq.answer}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- News Review Integration -->
  {#if article.category !== "Chính sách"}
    <NewsMobileReviews articleId={article.id} slug={article.title} />
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

  {#if showScrollTop}
    <button
      class="fixed bottom-6 right-4 w-10 h-10 bg-white/20 backdrop-blur-xl border border-white/40 shadow-xl rounded-full flex items-center justify-center text-gray-900 z-50 active:scale-75 transition-all"
      onclick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      in:fly={{ y: 20, duration: 400 }}
      out:fade
    >
      <svg
        class="w-5 h-5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="3"
          d="M5 15l7-7 7 7"
        />
      </svg>
    </button>
  {/if}
</svelte:element>

<style>
  :global(.elite-prose-mobile) {
    font-size: 1.05rem;
    line-height: 1.6;
    color: #374151;
    word-break: break-word;
    overflow-wrap: break-word;
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
