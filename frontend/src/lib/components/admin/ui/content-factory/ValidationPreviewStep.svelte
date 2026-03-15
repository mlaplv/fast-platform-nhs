<script lang="ts">
  import { onMount } from "svelte";

  import type { MediaAsset } from "$lib/state/types";

  let {
    draft_content = "",
    assets = [] as (MediaAsset | string)[],
    keywords = {},
    copyrightScore = null,
    seoScore = null,
    aiScore = null,
    analysis_cache = null,
    isExpanded = false
  } = $props();

  let previewMode = $state<'desktop' | 'mobile'>('desktop');
  
  // Computed Data
  let title = $derived(keywords?.primary_keyword ? `Bài viết chuẩn SEO về: ${keywords.primary_keyword}` : "Tiêu đề bài viết");
  if (analysis_cache?.seo?.data?.signals) {
       // Try to extract actual title from SEO checks if available or parse from HTML
       const h1Match = draft_content.match(/<h1[^>]*>(.*?)<\/h1>/i);
       if (h1Match) title = h1Match[1].replace(/<[^>]+>/g, '').trim();
  }
  
  let thumbnail = $derived.by(() => {
    if (assets.length === 0) return "https://via.placeholder.com/600x315?text=No+Image";
    const primary = assets.find(a => typeof a === 'object' && a.is_primary);
    const first = primary || assets[0];
    return typeof first === 'string' ? first : first.url;
  });
  let description = $derived(draft_content.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').substring(0, 160) + "...");

</script>

<div class="w-full h-full flex flex-col md:flex-row gap-6 p-2 animate-in fade-in duration-700">
  
  <!-- LEFT PANEL: NEWS ARTICLE PREVIEW -->
  <div class="flex-[1.5] bg-black/40 border border-white/10 flex flex-col overflow-hidden relative shadow-2xl">
    <div class="h-14 border-b border-white/10 bg-white/5 flex items-center justify-between px-6 shrink-0">
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-red-500/80"></div>
        <div class="w-3 h-3 rounded-full bg-yellow-500/80"></div>
        <div class="w-3 h-3 rounded-full bg-green-500/80"></div>
        <span class="ml-4 text-xs font-semibold text-white/50 tracking-wider">PREVIEW MODE</span>
      </div>
      <div class="flex bg-black/50 p-1 border border-white/5 disabled-group">
         <button 
           class="px-4 py-1.5 text-xs font-bold transition-all {previewMode === 'desktop' ? 'bg-white/20 text-white shadow-sm' : 'text-white/40 hover:text-white/80'}"
           onclick={() => previewMode = 'desktop'}
         >
           Desktop
         </button>
         <button 
           class="px-4 py-1.5 text-xs font-bold transition-all {previewMode === 'mobile' ? 'bg-white/20 text-white shadow-sm' : 'text-white/40 hover:text-white/80'}"
           onclick={() => previewMode = 'mobile'}
         >
           Mobile
         </button>
      </div>
    </div>
    
    <div class="flex-1 overflow-y-auto custom-scrollbar flex items-start justify-center p-4 md:p-8 bg-[#f8f9fa] dark:bg-[#0c0a0f]">
       <!-- Adaptive Container -->
       <div class="transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] {previewMode === 'mobile' ? 'w-[375px] max-w-full min-h-[812px] bg-white text-black shadow-2xl p-6 border-[8px] border-zinc-800' : 'w-full max-w-3xl bg-white text-black shadow-xl p-8 md:p-12'}">
          <!-- Mock Header like VNExpress -->
          <div class="border-b-2 border-red-600 pb-4 mb-8 flex justify-between items-end">
             <div class="text-3xl font-black text-red-600 tracking-tighter uppercase">BAOMOI.COM</div>
             <div class="text-xs font-bold text-gray-500">{new Date().toLocaleDateString('vi-VN')}</div>
          </div>
          
          <div class="prose prose-lg prose-red max-w-none break-words" style="font-family: 'Merriweather', serif;">
            {@html draft_content || "<p class='text-gray-400 italic'>Chưa có nội dung bản thảo...</p>"}
          </div>
       </div>
    </div>
  </div>

  <!-- RIGHT PANEL: CERTIFICATION DASHBOARD -->
  <div class="flex-1 flex flex-col gap-6 overflow-y-auto custom-scrollbar pb-10">
    
    <!-- 1. TRUST BADGES -->
    <div class="bg-gradient-to-br from-indigo-900/40 to-purple-900/40 border border-purple-500/30 p-6 relative overflow-hidden group shrink-0">
      <div class="absolute -right-10 -top-10 w-40 h-40 bg-purple-500/20 blur-3xl rounded-full"></div>
      
      <h3 class="text-sm font-black text-purple-300 uppercase tracking-widest mb-4 flex items-center gap-2">
        <span class="text-lg">🛡️</span> Chứng Nhận Thuật Toán
      </h3>
      
      <div class="grid grid-cols-3 gap-3">
        <div class="bg-black/50 border border-emerald-500/30 p-4 flex flex-col items-center justify-center text-center gap-1 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
           <span class="text-2xl">✨</span>
           <span class="text-[10px] text-emerald-400/80 font-bold uppercase tracking-wider">Bản Quyền</span>
           <span class="text-xl font-black text-emerald-400">{copyrightScore ?? '--'}%</span>
        </div>
        <div class="bg-black/50 border border-blue-500/30 p-4 flex flex-col items-center justify-center text-center gap-1 shadow-[0_0_15px_rgba(59,130,246,0.1)]">
           <span class="text-2xl">⚡</span>
           <span class="text-[10px] text-blue-400/80 font-bold uppercase tracking-wider">Chuẩn SEO</span>
           <span class="text-xl font-black text-blue-400">{seoScore ?? '--'}</span>
        </div>
        <div class="bg-black/50 border border-fuchsia-500/30 p-4 flex flex-col items-center justify-center text-center gap-1 shadow-[0_0_15px_rgba(217,70,239,0.1)]">
           <span class="text-2xl">🤖</span>
           <span class="text-[10px] text-fuchsia-400/80 font-bold uppercase tracking-wider">AI 2026</span>
           <span class="text-xl font-black text-fuchsia-400">{aiScore ?? '--'}%</span>
        </div>
      </div>
      {#if copyrightScore >= 90 && seoScore >= 70}
         <div class="mt-4 text-center">
            <div class="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold">
               ✓ Sẵn sàng xuất bản phân phối toàn cầu
            </div>
         </div>
      {/if}
    </div>

    <!-- 2. GOOGLE SERP SIMULATOR -->
    <div class="bg-white p-6 shadow-xl border border-gray-100 flex flex-col gap-3 shrink-0">
       <h3 class="text-xs font-black text-gray-400 uppercase tracking-widest flex items-center gap-2 mb-2">
         <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
         Google Search Preview
       </h3>
       <div class="font-sans">
          <div class="flex items-center gap-3 mb-1">
             <div class="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center text-xs font-bold text-gray-500">X</div>
             <div>
                <div class="text-sm font-medium text-gray-900 leading-tight">XoHi Content Hub</div>
                <div class="text-[12px] text-gray-500 leading-tight">https://your-domain.com › thong-tin-chi-tiet</div>
             </div>
          </div>
          <div class="text-[20px] text-[#1a0dab] group-hover:underline cursor-pointer leading-tight mb-1" style="font-family: arial, sans-serif;">
             {title}
          </div>
          <div class="text-[14px] text-[#4d5156] leading-snug line-clamp-2" style="font-family: arial, sans-serif;">
             {description}
          </div>
       </div>
    </div>
    
    <!-- 3. GOOGLE SGE SIMULATOR -->
    {#if analysis_cache?.seo?.data?.signals || title.length > 5}
    <div class="bg-gradient-to-b from-[#e8f0fe] to-white p-6 shadow-xl border border-blue-100 flex flex-col gap-3 relative overflow-hidden shrink-0">
       <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 via-purple-400 to-red-400"></div>
       <h3 class="text-xs font-black text-gray-500 uppercase flex items-center gap-2 mb-2">
         ✨ AI Overview Simulator
       </h3>
       <div class="text-sm text-gray-800 leading-relaxed font-sans">
          Theo các nguồn đáng tin cậy, <b>{title.split(' ').slice(0, 5).join(' ')}</b> được đánh giá cao nhờ {keywords?.primary_keyword ? `các phân tích về ${keywords.primary_keyword}.` : 'tính thực tiễn cao.'}
          Đáng chú ý:
          <ul class="list-disc pl-5 mt-2 space-y-1 text-gray-700">
             <li>Nội dung được cấu trúc logic chuẩn SEO.</li>
             <li>Thông tin độc đáo, không trùng lặp (Uniqueness: {copyrightScore ?? 95}%).</li>
          </ul>
       </div>
       <div class="mt-2 flex gap-2">
          <div class="bg-white border border-gray-200 p-2 w-32 shadow-sm shrink-0 flex gap-2 items-center cursor-pointer hover:bg-gray-50">
             <img src={thumbnail} alt="thumb" class="w-8 h-8 rounded-lg object-cover" />
             <div class="text-[10px] font-bold text-gray-800 leading-tight line-clamp-2">{title}</div>
          </div>
       </div>
    </div>
    {/if}

    <!-- 4. SOCIAL MEDIA PREVIEW -->
    <div class="bg-white outline outline-1 outline-gray-200 shadow-xl overflow-hidden flex flex-col font-sans shrink-0">
       <div class="p-4 border-b border-gray-100 flex items-center gap-2 bg-gray-50">
          <div class="w-2 h-2 rounded-full bg-blue-600"></div>
          <h3 class="text-xs font-black text-gray-400 uppercase">Facebook / Zalo Share Preview</h3>
       </div>
       <div class="w-full h-48 bg-gray-100 relative">
          <img src={thumbnail} alt="Social Thumbnail" class="w-full h-full object-cover" />
       </div>
       <div class="p-4 bg-[#f2f3f5]">
          <div class="text-[12px] text-gray-500 uppercase tracking-wide font-semibold mb-1">YOUR-DOMAIN.COM</div>
          <div class="text-[16px] font-bold text-black leading-tight mb-1">{title}</div>
          <div class="text-[14px] text-gray-600 leading-snug line-clamp-1">{description}</div>
       </div>
    </div>

  </div>
</div>

<style>
  /* Local overrides for VNExpress style */
  :global(.prose-red img) {
    border-radius: 0;
    width: 100%;
    margin-top: 2rem;
    margin-bottom: 2rem;
  }
  :global(.prose-red h2) {
    color: #b91c1c; 
    font-weight: 900;
    margin-top: 2.5rem;
    font-size: 1.5rem;
  }
  :global(.prose-red h3) {
    color: #1f2937;
    font-weight: 800;
    font-size: 1.25rem;
  }
  :global(.prose-red p) {
    font-size: 1.125rem;
    line-height: 1.75;
    color: #374151;
  }
</style>
