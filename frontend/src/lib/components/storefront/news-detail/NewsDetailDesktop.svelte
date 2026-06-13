<script lang="ts">
  import { onMount } from "svelte";
  import { fade, fly, scale } from "svelte/transition";
  import { cubicOut } from "svelte/easing";
  import NewsDetailReviews from "./NewsDetailReviews.svelte";
  import ImageWithFallback from "../ui/ImageWithFallback.svelte";
  import { resolveMediaUrl, resolveOptimizedImageUrl } from "$lib/state/utils";

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

  interface NewsItem {
    id: string;
    title: string;
    slug: string;
    featuredImage?: string;
    featured_image?: string;
    category?: string;
  }

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
    relatedNews?: NewsItem[];
  }

  let { article: rawArticle, relatedNews = [] }: Props = $props();

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

  // ELITE V2.2: Dynamic Sidebar (Zero-Hydration Sync)
  const normalizedRelatedNews = $derived(
    relatedNews.map((news, i) => ({
      title: news.title,
      category: news.category || (i % 2 === 0 ? "LÀM ĐẸP" : "XU HƯỚNG"),
      image: news.featuredImage || news.featured_image || article.featuredImage,
      slug: news.slug,
    }))
  );

  // SGE Shield V1.0: Deterministic DOM Entropy
  const wrapperTags = ["div", "article", "section", "main"];
  const seedLength = $derived(article?.title ? article.title.length : 10);
  const outerWrapper = $derived(wrapperTags[seedLength % wrapperTags.length]);

  const innerTags = ["div", "section", "article"];
  const innerWrapper = $derived(innerTags[(seedLength + 5) % innerTags.length]);

  const proseTags = ["div", "section"];
  const proseWrapper = $derived(proseTags[(seedLength + 7) % proseTags.length]);

  // Elite V2.2: Simple Pro Sentence Case
  const formattedTitle = $derived(
    article.title
      ? article.title.charAt(0).toUpperCase() + article.title.slice(1)
      : "",
  );

  // Elite V2.2: Professional Accordion State
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
</script>

<svelte:element
  this={outerWrapper}
  class="news-detail-content pb-8 text-gray-900"
>
  <!-- BREADCRUMB & ELITE HEADER -->
  <div class="bg-white border-b border-gray-100 mb-8">
    <div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-6">
      <nav
        class="flex items-center gap-2 text-[12px] text-gray-400 mb-4 font-medium tracking-wider"
      >
        <a href="/" class="hover:text-[#ee4d2d] transition-colors">Trang chủ</a>
        <span>/</span>
        <a href="/bai-viet" class="hover:text-[#ee4d2d] transition-colors"
          >Bài viết</a
        >
        <span>/</span>
        <span class="text-gray-900 line-clamp-1">{article.title}</span>
      </nav>

      <div class="flex items-center gap-6" in:fade={{ duration: 800 }}>
        <div
          class="h-px w-12 bg-[#C18F7E]"
          in:scale={{ duration: 1000, start: 0 }}
        ></div>
        <span
          class="text-[10px] font-black text-[#C18F7E] tracking-[0.3em] animate-pulse"
          >Độc quyền Hướng dẫn chuyên môn</span
        >
      </div>
    </div>
  </div>

  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 flex gap-8 items-start">
    <!-- MAIN ARTICLE AREA -->
    <main class="flex-1">
      <svelte:element
        this={innerWrapper}
        class="bg-white border border-gray-100 shadow-[0_20px_60px_rgba(0,0,0,0.04)] overflow-hidden"
        in:fly={{ y: 40, duration: 1000 }}
      >
        <!-- Hero Section -->
        <div class="pl-[10px]">
          <div class="flex items-center gap-4 mb-0">
            <span
              class="bg-black text-white px-3 py-1 text-[10px] font-black tracking-widest"
            >
              {article.category || "Tạp chí Elite"}
            </span>
            <div
              class="flex items-center gap-2 text-[11px] font-black text-gray-500 tracking-widest"
            >
              <span class="text-[#C18F7E] shrink-0"
                >{article.author === "Xohi" ||
                article.author === "System" ||
                article.author === "Osmo"
                  ? "Ban biên tập osmo"
                  : article.author}</span
              >
              <div class="w-1 h-1 bg-gray-300 rounded-full"></div>
              <span>{article.publishedAt}</span>
            </div>
          </div>

          <h1
            class="text-4xl lg:text-5xl font-black text-gray-900 leading-[1.1] tracking-tight mt-[10px] mb-[5px]"
          >
            {formattedTitle}
          </h1>
        </div>

        <!-- Featured Image -->
        {#if article.category !== "Chính sách" || (article.featuredImage && article.featuredImage.trim() !== "")}
          {#if article.featuredImage && article.featuredImage.trim() !== ""}
            <div class="w-full px-0 mb-0 overflow-hidden bg-gray-50 flex items-center justify-center">
              <img
                src={resolveOptimizedImageUrl(article.featuredImage, 1000)}
                alt={article.title}
                class="w-full h-auto object-contain block transition-transform duration-700"
                loading="eager"
                fetchpriority="high"
                decoding="async"
              />
            </div>
          {:else}
            <div class="px-0 mb-0">
              <ImageWithFallback
                src={article.featuredImage}
                alt={article.title}
                aspectRatio="aspect-video"
                class="w-full"
              />
            </div>
          {/if}
        {/if}

        <!-- Content Body (Elite Prose) -->
        <svelte:element
          this={proseWrapper}
          class="pt-[10px] pb-0 px-[10px] news-article-prose"
        >
          {@html article.content}
        </svelte:element>

        <!-- Social Share Bar -->
        <div
          class="px-8 md:px-12 py-8 bg-gray-50/50 border-t border-gray-100 flex items-center justify-between"
        >
          <div class="flex items-center gap-4">
            <span class="text-[10px] font-black text-gray-400 tracking-widest"
              >Chia sẻ bài viết:</span
            >
            <div class="flex gap-2">
              {#each ["FB", "ZL", "CP"] as btn}
                <button
                  class="w-10 h-10 bg-white border border-gray-100 flex items-center justify-center text-[10px] font-black hover:bg-black hover:text-white hover:border-black transition-all"
                >
                  {btn}
                </button>
              {/each}
            </div>
          </div>

          <button
            onclick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            class="text-[10px] font-black tracking-widest text-gray-400 hover:text-black transition-colors flex items-center gap-2"
          >
            Quay lên đầu
            <svg
              class="w-3 h-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="3"
                d="M5 15l7-7 7 7"
              /></svg
            >
          </button>
        </div>
      </svelte:element>

      <!-- Bottom Navigation -->
      <div
        class="mt-8 flex justify-between items-center mb-10 pb-6 border-b border-gray-100"
      >
        <a
          href="/bai-viet"
          class="text-[11px] font-black tracking-widest text-[#C18F7E] flex items-center gap-2 hover:gap-4 transition-all"
        >
          <svg
            class="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="3"
              d="M7 16l-4-4m0 0l4-4m-4 4h18"
            /></svg
          >
          Quay về kho tin học thuật
        </a>
      </div>

      <!-- ELITE V2.2: News Review Integration -->
      {#if article.category !== "Chính sách"}
        {#if loadBelowFold}
          <NewsDetailReviews articleId={article.id} />
        {:else}
          <div class="h-[180px] bg-white border border-gray-100 flex flex-col items-center justify-center text-gray-300 gap-2 mt-8">
            <div class="w-8 h-8 rounded-full border-2 border-gray-100 animate-spin" style="border-top-color: var(--color-luxury-copper, #C18F7E);"></div>
            <span class="text-[10px] font-black tracking-widest uppercase">Đang tải bình luận học thuật...</span>
          </div>
        {/if}
      {/if}
    </main>

    <!-- RIGHT SIDEBAR -->
    <aside
      class="w-[320px] shrink-0 space-y-8 hidden xl:block sticky top-6 self-start"
      in:fade={{ duration: 1000, delay: 500 }}
    >
      <!-- GEO 2026: FAQ Section Relocated to Top Sidebar -->
      {#if article.metadata?.faqs && article.metadata.faqs.length > 0}
        <div class="bg-white border border-gray-100 p-8 shadow-sm">
          <h2
            class="text-[12px] font-black tracking-[0.2em] text-[#0f172a] mb-8 flex items-center gap-3"
          >
            <div
              class="w-1.5 h-1.5 bg-[#C18F7E] rounded-full animate-pulse"
            ></div>
            Câu hỏi thường gặp
          </h2>
          <div class="space-y-4">
            {#each article.metadata.faqs as faq, i}
              <div class="border-b border-gray-50 pb-4 last:border-0 last:pb-0">
                <button
                  class="w-full flex items-center justify-between cursor-pointer select-none hover:text-[#C18F7E] transition-colors bg-transparent border-none p-0 text-left group/faq"
                  onclick={() => toggleFaq(i)}
                >
                  <span
                    class="text-[13px] font-bold {activeFaq === i
                      ? 'text-[#C18F7E]'
                      : 'text-[#0f172a]'} leading-snug pr-4 transition-colors"
                    >{faq.question}</span
                  >
                  <svg
                    class="w-3 h-3 text-gray-300 transition-transform duration-300 {activeFaq ===
                    i
                      ? 'rotate-180 text-[#C18F7E]'
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
                    class="pt-3 text-[12px] text-gray-500 leading-relaxed italic"
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

      <!-- Related News -->
      <div class="bg-white border border-gray-100 p-8">
        <h2
          class="text-[12px] font-black tracking-[0.2em] mb-8 flex items-center gap-3"
        >
          <div
            class="w-1.5 h-1.5 bg-[#C18F7E] rounded-full animate-pulse"
          ></div>
          Kiến thức bổ trợ
        </h2>

        <div class="space-y-8">
          {#each normalizedRelatedNews as news}
            <a href="/{news.slug}.html" class="group block space-y-3">
              <ImageWithFallback
                src={news.image}
                alt={news.title}
                aspectRatio="aspect-video"
                class="border border-gray-100"
              />
              <div>
                <span
                  class="text-[9px] font-black text-[#C18F7E] tracking-widest"
                  >{news.category}</span
                >
                <h3
                  class="text-[14px] font-bold text-[#0f172a] line-clamp-2 leading-snug group-hover:text-[#C18F7E] transition-colors"
                >
                  {news.title}
                </h3>
              </div>
            </a>
          {/each}
        </div>
      </div>

      <!-- Newsletter / Community -->
      <div class="bg-black text-white p-8 relative overflow-hidden group">
        <div
          class="absolute inset-0 bg-gradient-to-br from-red-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"
        ></div>
        <h3 class="text-[11px] font-black tracking-[0.3em] mb-4 relative z-10">
          Cộng đồng Elite
        </h3>
        <p class="text-[13px] text-gray-400 font-medium mb-6 relative z-10">
          Đăng ký nhận những tin bài chuyên sâu về chăm sóc da từ các chuyên gia
          AI.
        </p>
        <div class="relative z-10 space-y-2">
          <input
            type="email"
            placeholder="Email của bạn..."
            class="w-full bg-white/10 border-none px-4 py-3 text-sm focus:ring-1 focus:ring-[#C18F7E] outline-none transition-all placeholder:text-gray-600"
          />
          <button
            class="w-full bg-[#C18F7E] py-3 text-[10px] font-black tracking-widest hover:bg-white hover:text-black transition-all"
            >Tham gia ngay</button
          >
        </div>
      </div>
    </aside>
  </div>


</svelte:element>

<style>
  :global(.news-article-prose) {
    font-size: 1.125rem;
    line-height: 1.6; /* Elite V2.2: Slightly tighter for compact feel */
    color: #374151;
    word-break: break-word;
    overflow-wrap: break-word;
  }

  :global(.news-article-prose a) {
    color: inherit !important;
    text-decoration: none !important;
    font-weight: inherit !important;
    cursor: pointer;
  }

  :global(.news-article-prose p) {
    margin: 0.75rem 0;
    font-weight: 400;
    letter-spacing: -0.011em;
  }

  :global(.news-article-prose h1) {
    font-size: 2rem;
    font-weight: 900;
    color: #111827 !important;
    margin: 0 0 1rem 0 !important;
    text-transform: none;
    line-height: 1.1;
  }

  :global(.news-article-prose h2) {
    font-size: 1.5rem;
    font-weight: 850;
    color: #c18f7e !important;
    margin: 2rem 0 0.75rem 0;
    text-transform: none;
    letter-spacing: -0.02em;
    border-left: 4px solid #c18f7e;
    padding-left: 1rem;
    line-height: 1.2;
  }

  :global(.news-article-prose strong),
  :global(.news-article-prose b) {
    color: #111827 !important;
    font-weight: 800;
  }

  :global(.news-article-prose h3) {
    font-size: 1.25rem;
    font-weight: 800;
    color: #c18f7e !important;
    margin: 1.5rem 0 0.5rem 0;
    text-transform: none;
  }

  /* ELITE V2.2: Viral 2026 Professional Highlights (Luxury Copper) */
  :global(.news-article-prose span[style*="background-color"]),
  :global(.news-article-prose span[style*="background: rgb(226, 244, 255)"]) {
    background-color: #fff0f0 !important;
    padding: 2px 4px !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    color: #c18f7e !important;
  }

  /* Specific callout blocks should use div */
  :global(.news-article-prose div[style*="background-color"]),
  :global(.news-article-prose div[style*="background: rgb(226, 244, 255)"]),
  :global(.news-article-prose section[style*="background-color"]) {
    padding: 2rem !important;
    border-radius: 0 !important;
    border-left: 8px solid #c18f7e !important;
    color: #c18f7e !important;
    background: linear-gradient(90deg, #fff0f0 0%, #ffffff 100%) !important;
    margin: 2.5rem 0 !important;
    font-weight: 800 !important;
    line-height: 1.3 !important;
    letter-spacing: -0.02em !important;
    box-shadow: 15px 15px 40px rgba(193, 143, 126, 0.08) !important;
  }

  :global(.news-article-prose [style*="background-color"] *) {
    color: inherit !important;
  }

  :global(.news-article-prose img) {
    border: none !important;
    outline: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    margin: 1.5rem auto !important; /* Elite V2.2: Professional guide spacing */
    max-width: 100% !important;
    height: auto !important;
    display: block !important;
  }

  :global(.news-article-prose blockquote) {
    border-left: 6px solid #c18f7e;
    padding: 1.5rem 2rem;
    font-style: italic;
    font-size: 1.25rem;
    font-weight: 500;
    color: #4b5563;
    background: #fff0f0; /* Luxury Peach */
    margin: 1.5rem 0;
  }

  :global(.news-article-prose ul) {
    list-style-type: none;
    padding-left: 0;
    margin: 1.5rem 0;
  }

  :global(.news-article-prose li) {
    margin-bottom: 0.75rem;
    padding-left: 1.5rem;
    position: relative;
    font-weight: 500;
  }

  :global(.news-article-prose li::before) {
    content: "";
    position: absolute;
    left: 0;
    top: 0.7em;
    width: 10px;
    height: 2px;
    background: #c18f7e;
  }

  :global(.line-clamp-1) {
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  :global(.line-clamp-2) {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
