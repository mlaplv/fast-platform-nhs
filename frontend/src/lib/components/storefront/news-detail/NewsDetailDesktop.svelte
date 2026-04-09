<script lang="ts">
  interface Props {
    article: { title: string; author: string; publishedAt: string; content: string; image: string };
  }
  let { article }: Props = $props();
</script>

<article class="max-w-4xl mx-auto p-6 md:p-12 bg-white rounded-3xl shadow-sm border border-slate-100 mt-8">
  <div class="mb-10 text-center">
    <h1 class="text-4xl md:text-5xl font-black text-slate-900 mb-6 tracking-tighter leading-tight">{article.title}</h1>
    <div class="flex items-center justify-center gap-4 text-slate-500 text-xs uppercase font-bold tracking-widest">
      <span class="text-red-600">{article.author}</span>
      <span class="text-slate-300">•</span>
      <span>{article.publishedAt}</span>
    </div>
  </div>

  <div class="aspect-video w-full overflow-hidden bg-slate-100 rounded-3xl mb-12 shadow-xl">
    <img src={article.image} alt={article.title} class="w-full h-full object-cover" />
  </div>

  <div class="prose prose-slate prose-lg max-w-none text-slate-700 leading-relaxed font-medium">
    {article.content}
  </div>
</article>