<script lang="ts">
  interface Props {
    article: { title: string; author: string; publishedAt: string; content: string; image: string; category?: string };
  }
  let { article }: Props = $props();
</script>

<div class="bg-white min-h-screen text-gray-900">
  {#if article.category !== 'Chính sách'}
  <!-- Immersive Hero -->
  <div class="h-[60vh] relative w-full overflow-hidden bg-black">
    <img src={article.image} alt={article.title} class="absolute inset-0 w-full h-full object-cover z-0 opacity-80" />
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
        <span class="bg-red-600 text-white px-2 py-0.5 text-[9px] font-black uppercase tracking-widest mb-3 inline-block">
          Hướng dẫn nâng cao
        </span>
        <h1 class="text-3xl font-black text-gray-900 leading-tight tracking-tighter uppercase italic drop-shadow-sm">
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
        <h1 class="text-lg font-black text-gray-900 uppercase italic tracking-tight truncate flex-1">
          {article.title}
        </h1>
    </div>
  </div>
  {/if}

  {#if article.category !== 'Chính sách'}
  <!-- Article Info -->
  <div class="px-6 py-6 border-b border-gray-50 bg-gray-50/30">
      <div class="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest overflow-hidden">
        <span class="text-red-600 shrink-0">{article.author === 'Xohi' || article.author === 'System' ? 'Ban biên tập Elite' : article.author}</span>
        <div class="w-1 h-1 bg-gray-200 rounded-full shrink-0"></div>
        <span class="truncate">{article.publishedAt}</span>
      </div>
  </div>
  {/if}

  <!-- Content Reader (Elite Prose) -->
  <div class="px-6 py-10 elite-prose-mobile">
      {@html article.content}
  </div>

  <!-- Footer Navigation -->
  <div class="p-10 text-center border-t border-gray-100 bg-gray-50">
      <span class="text-[10px] font-black text-gray-300 uppercase tracking-[0.4em]">Kết thúc bài viết</span>
      <div class="mt-6">
          <a href="/bai-viet" class="inline-block px-10 py-4 bg-black text-white text-[10px] font-black uppercase tracking-widest active:scale-95 transition-all shadow-xl">
            Quay về tin bài
          </a>
      </div>
  </div>
</div>

<style>
  :global(.elite-prose-mobile) {
    font-size: 1rem;
    line-height: 1.7;
    color: #374151;
  }
  
  :global(.elite-prose-mobile p) {
    margin-bottom: 1.5rem;
  }

  :global(.elite-prose-mobile h2) {
    font-size: 1.5rem;
    font-weight: 900;
    color: #111827;
    margin-top: 2.5rem;
    margin-bottom: 1rem;
    text-transform: uppercase;
  }

  :global(.elite-prose-mobile img) {
    border-radius: 12px;
    margin: 2rem 0;
    width: 100%;
  }

  :global(.elite-prose-mobile blockquote) {
    border-left: 3px solid #ee4d2d;
    padding-left: 1.25rem;
    font-style: italic;
    font-size: 1.1rem;
    color: #1f2937;
    margin: 2rem 0;
  }
</style>