<script lang="ts">
  import { fade } from 'svelte/transition';

  import ImageWithFallback from '../ui/ImageWithFallback.svelte';
  import NewsMobileReviews from './NewsMobileReviews.svelte';
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
  let { article }: Props = $props();

  // SGE Shield V1.0: Deterministic DOM Entropy
  const wrapperTags = ['div', 'article', 'section', 'main'];
  const seedLength = $derived(article?.title ? article.title.length : 10);
  const outerWrapper = $derived(wrapperTags[seedLength % wrapperTags.length]);
  
  const innerTags = ['div', 'section'];
  const innerWrapper = $derived(innerTags[(seedLength + 3) % innerTags.length]);
</script>

<svelte:element this={outerWrapper} class="bg-white min-h-screen text-gray-900">
  {#if article.category !== 'Chính sách'}
  <!-- Immersive Hero -->
  <div class="h-[60vh] relative w-full overflow-hidden bg-black">
    <ImageWithFallback src={article.featuredImage} alt={article.title} aspectRatio="aspect-video" class="absolute inset-0 w-full h-full z-0 opacity-80" />
    <div class="absolute inset-0 bg-gradient-to-t from-white via-transparent to-black/40 z-10"></div>
    
    <!-- Top Action Bar -->
    <div class="absolute top-0 left-0 w-full p-6 z-20 flex justify-between items-center">
        <button onclick={() => history.back()} class="w-10 h-10 bg-white/10 backdrop-blur-xl rounded-full flex items-center justify-center border border-white/20">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <button class="w-10 h-10 bg-white/10 backdrop-blur-xl rounded-full flex items-center justify-center border border-white/20">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
        </button>
    </div>

    <!-- Title Overlay -->
    <div class="absolute bottom-0 left-0 w-full p-6 z-20">
        <span class="bg-[#C18F7E] text-white px-2 py-0.5 text-[9px] font-black uppercase tracking-widest mb-3 inline-block">
          Hướng dẫn chuyên môn
        </span>
        <h1 class="text-3xl font-black text-gray-900 leading-tight tracking-tighter drop-shadow-sm mb-0">
          {article.title}
        </h1>
    </div>
  </div>
  {:else}
  <!-- Clean Header for Policy Pages -->
  <div class="bg-white border-b border-gray-100 sticky top-0 z-30">
    <div class="flex items-center gap-4 px-6 py-4">
        <button onclick={() => history.back()} class="w-8 h-8 flex items-center justify-center text-gray-900">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <h1 class="text-lg font-black text-gray-900 tracking-tight truncate flex-1">
          {article.title}
        </h1>
    </div>
  </div>
  {/if}

  {#if article.category !== 'Chính sách'}
  <!-- Article Info -->
  <div class="px-6 py-4 border-b border-gray-50 bg-gray-50/30">
      <div class="flex items-center gap-2 text-[10px] font-black text-gray-500 uppercase tracking-widest overflow-hidden">
        <span class="text-[#C18F7E] shrink-0">{article.author === 'Xohi' || article.author === 'System' || article.author === 'Micsmo' ? 'Ban biên tập osmo' : article.author}</span>
        <div class="w-1 h-1 bg-gray-200 rounded-full shrink-0"></div>
        <span class="truncate">{article.publishedAt}</span>
      </div>
  </div>
  {/if}

  <!-- Content Reader (Elite Prose) -->
  <svelte:element this={innerWrapper} class="px-[5px] py-0 elite-prose-mobile">
      {@html article.content}
  </svelte:element>

  <!-- GEO 2026: FAQ Section (Full Width Redesign) -->
  {#if article.metadata?.faqs && article.metadata.faqs.length > 0}
  <div class="py-10 border-t border-gray-100">
    <h2 class="px-6 text-[12px] font-black uppercase tracking-[0.2em] text-[#0f172a] mb-6 flex items-center gap-3">
      <div class="w-1.5 h-1.5 bg-[#C18F7E] rounded-full"></div>
      Câu hỏi kỹ thuật
    </h2>
    <div class="divide-y divide-gray-50 border-y border-gray-50">
      {#each article.metadata.faqs as faq}
        <details class="group bg-white active:bg-gray-50/50 transition-colors">
          <summary class="flex items-center justify-between p-6 cursor-pointer select-none">
            <span class="text-[14px] font-bold text-[#0f172a] pr-4 leading-snug">{faq.question}</span>
            <svg class="w-4 h-4 text-[#C18F7E] shrink-0 group-open:rotate-180 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7" />
            </svg>
          </summary>
          <div class="px-6 pb-8 pt-0 text-[14px] text-gray-600 leading-relaxed italic" in:fade>
            {faq.answer}
          </div>
        </details>
      {/each}
    </div>
  </div>
  {/if}

  <!-- News Review Integration -->
  {#if article.category !== 'Chính sách'}
  <NewsMobileReviews articleId={article.id} slug={article.title} />
  {/if}

  <!-- Footer Navigation -->
  <div class="p-10 text-center border-t border-gray-100 bg-gray-50">
      <span class="text-[10px] font-black text-gray-300 uppercase tracking-[0.4em]">Kết thúc bài viết</span>
      <div class="mt-6">
          <a href="/bai-viet" class="inline-block px-10 py-4 bg-[#0f172a] text-white text-[10px] font-black uppercase tracking-widest active:scale-95 transition-all shadow-xl">
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
  
  :global(.elite-prose-mobile p) {
    margin: 0.75rem 0;
    font-weight: 400;
  }

  :global(.elite-prose-mobile h1) {
    font-size: 1.75rem;
    font-weight: 950;
    color: #111827 !important;
    margin: 2rem 0 0.75rem 0;
    text-transform: uppercase;
    line-height: 1.1;
  }

  :global(.elite-prose-mobile h2) {
    font-size: 1.35rem;
    font-weight: 950;
    color: #0f172a !important;
    margin: 1.5rem 0 0.5rem 0;
    text-transform: uppercase;
    letter-spacing: -0.02em;
    border-left: 4px solid #C18F7E;
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
    text-transform: uppercase;
  }

  /* ELITE V2.2: Viral 2026 Professional Highlights (Luxury Copper) */
  :global(.elite-prose-mobile span[style*="background-color"]),
  :global(.elite-prose-mobile span[style*="background: rgb(226, 244, 255)"]) {
    background-color: #FFF0F0 !important;
    padding: 2px 4px !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    color: #C18F7E !important;
  }

  /* Specific callout blocks should use div */
  :global(.elite-prose-mobile div[style*="background-color"]),
  :global(.elite-prose-mobile div[style*="background: rgb(226, 244, 255)"]),
  :global(.elite-prose-mobile section[style*="background-color"]) {
    padding: 1.5rem !important;
    border-radius: 0 !important;
    border-left: 6px solid #C18F7E !important;
    color: #0f172a !important;
    background: linear-gradient(90deg, #FFF0F0 0%, #FFFFFF 100%) !important;
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
    border-left: 5px solid #C18F7E;
    padding: 1rem 1.25rem;
    font-style: italic;
    font-size: 1.1rem;
    font-weight: 500;
    color: #4b5563;
    background: #FFF0F0;
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
    background: #C18F7E;
  }
</style>