<script lang="ts">
    import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import BarChart2 from "@lucide/svelte/icons/bar-chart-2";
  import Sparkles from "@lucide/svelte/icons/sparkles";

  interface Props {
    type: 'copyright' | 'seo' | 'ai';
    score?: number | null;
    locked?: boolean;
    seoResult?: any;
  }

  let { type, score, locked, seoResult }: Props = $props();
</script>

{#if type === 'copyright'}
  <div class="criteria-tooltip opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto absolute bottom-full left-0 mb-2 w-72 bg-gradient-to-br from-orange-950/95 via-slate-950/95 to-slate-900/95 backdrop-blur-2xl border border-orange-500/20 shadow-2xl shadow-orange-500/5 p-4 z-50 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
    <div class="flex items-center gap-2 mb-3">
      <div class="w-6 h-6 rounded-md bg-orange-500/20 flex items-center justify-center"><ShieldCheck size={12} class="text-orange-400" /></div>
      <span class="text-[10px] font-black tracking-[0.15em] text-orange-400">Plagiarism Cop™</span>
    </div>
    <div class="space-y-2 text-[9px] leading-relaxed text-white/70">
      <div class="flex items-start gap-2"><span class="text-orange-400 font-black mt-px">01</span><span><b class="text-white/90">Duplicate Detection</b> — So sánh từng câu với Top 10 Google, phát hiện trùng lặp ≥5 từ liên tiếp</span></div>
      <div class="flex items-start gap-2"><span class="text-orange-400 font-black mt-px">02</span><span><b class="text-white/90">Structural Similarity</b> — Phát hiện xào nấu cấu trúc (đổi từ đồng nghĩa nhưng giữ khung)</span></div>
      <div class="flex items-start gap-2"><span class="text-orange-400 font-black mt-px">03</span><span><b class="text-white/90">Source Attribution</b> — Truy vết URL gốc của đoạn trùng lặp</span></div>
      <div class="flex items-start gap-2"><span class="text-orange-400 font-black mt-px">04</span><span><b class="text-white/90">Internal Dedup</b> — Phát hiện lặp ý trong chính bài viết</span></div>
    </div>
    <div class="mt-3 pt-2 border-t border-white/5 flex items-center justify-between">
      <span class="text-[8px] text-white/30 italic">Powered by Google Custom Search API</span>
      <span class="text-[8px] font-black text-orange-400/60">≥90% = PASS</span>
    </div>
  </div>
{:else if type === 'seo'}
  <div class="criteria-tooltip opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto absolute bottom-full left-0 mb-2 w-80 bg-gradient-to-br from-blue-950/95 via-slate-950/95 to-slate-900/95 backdrop-blur-2xl border border-blue-500/20 shadow-2xl shadow-blue-500/5 p-4 z-50 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
    {#if locked}
      <div class="text-[9px] text-orange-400 font-bold">⚠️ Cần COPYRIGHT ≥ 90% trước ({score !== null ? `hiện: ${score}%` : 'chưa kiểm tra'})</div>
      <div class="h-px bg-white/5 my-2"></div>
    {/if}
    <div class="flex items-center gap-2 mb-3">
      <div class="w-6 h-6 rounded-md bg-blue-500/20 flex items-center justify-center"><BarChart2 size={12} class="text-blue-400" /></div>
      <span class="text-[10px] font-black tracking-[0.15em] text-blue-400">SEO Strategist™</span>
    </div>
    <div class="space-y-1.5 text-[9px] leading-relaxed text-white/70">
      <div class="flex items-start gap-2"><span class="text-blue-400 font-black shrink-0 w-8">20%</span><span><b class="text-white/90">Search Intent</b> — Giải quyết nỗi đau user tốt hơn đối thủ</span></div>
      <div class="flex items-start gap-2"><span class="text-blue-400 font-black shrink-0 w-8">20%</span><span><b class="text-white/90">E-E-A-T</b> — Chuyên gia, kinh nghiệm, nguồn uy tín</span></div>
      <div class="flex items-start gap-2"><span class="text-blue-400 font-black shrink-0 w-8">15%</span><span><b class="text-white/90">Entity Coverage</b> — Bao phủ đầy đủ concept so với Top 5</span></div>
      <div class="flex items-start gap-2"><span class="text-blue-400 font-black shrink-0 w-8">15%</span><span><b class="text-white/90">AI Naturalness</b> — Văn phong mượt, tránh lặp máy móc</span></div>
      <div class="flex items-start gap-2"><span class="text-blue-400 font-black shrink-0 w-8">15%</span><span><b class="text-white/90">Snippet Potential</b> — Cấu trúc sắc bén để AI trích dẫn</span></div>
      <div class="flex items-start gap-2"><span class="text-blue-400 font-black shrink-0 w-8">10%</span><span><b class="text-white/90">Semantic Richness</b> — Thuật ngữ chuyên sâu, không phổ thông</span></div>
      <div class="flex items-start gap-2"><span class="text-blue-400 font-black shrink-0 w-8">5%</span><span><b class="text-white/90">Technical SEO</b> — H1/H2/H3 structure, CTA rõ ràng</span></div>
    </div>
    <div class="mt-3 pt-2 border-t border-white/5 flex items-center justify-between">
      <span class="text-[8px] text-white/30 italic">So sánh Top 5 Google Real-time</span>
      <span class="text-[8px] font-black text-blue-400/60">A ≥ 85 · B ≥ 70</span>
    </div>
  </div>
{:else if type === 'ai'}
  <div class="criteria-tooltip opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto absolute bottom-full right-0 mb-2 w-[340px] bg-gradient-to-br from-purple-950/95 via-slate-950/95 to-fuchsia-950/95 backdrop-blur-2xl border border-purple-500/20 shadow-2xl shadow-purple-500/10 p-4 z-50 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
    {#if locked}
      <div class="text-[9px] text-blue-400 font-bold">⚠️ Cần SEO ≥ 70 trước ({score !== null ? `hiện: ${score}/100` : 'chưa kiểm tra'})</div>
      <div class="h-px bg-white/5 my-2"></div>
    {/if}
    <div class="flex items-center gap-2 mb-3">
      <div class="w-6 h-6 rounded-md bg-purple-500/20 flex items-center justify-center"><Sparkles size={12} class="text-purple-400" /></div>
      <div>
        <span class="text-[10px] font-black tracking-[0.15em] text-purple-400">Viral Edge™</span>
        <span class="text-[7px] text-white/30 ml-1">AI Search Optimization</span>
      </div>
    </div>
    <div class="space-y-1.5 text-[9px] leading-relaxed text-white/70">
      <div class="flex items-start gap-2"><span class="text-purple-400 font-black shrink-0 w-8">15%</span><span><b class="text-white/90">Search Intent</b> — Match chính xác câu hỏi user gõ vào Google</span></div>
      <div class="flex items-start gap-2"><span class="text-purple-400 font-black shrink-0 w-8">15%</span><span><b class="text-white/90">E-E-A-T Authority</b> — Chuyên gia, trích dẫn, bằng chứng thực tế</span></div>
      <div class="flex items-start gap-2"><span class="text-purple-400 font-black shrink-0 w-8">15%</span><span><b class="text-white/90">Information Gain</b> — Insight mới so với đối thủ Top 5</span></div>
      <div class="flex items-start gap-2"><span class="text-fuchsia-400 font-black shrink-0 w-8">15%</span><span><b class="text-white/90">AI Overview Ready</b> — Cấu trúc sẵn sàng cho Google AI Overview</span></div>
      <div class="flex items-start gap-2"><span class="text-fuchsia-400 font-black shrink-0 w-8">10%</span><span><b class="text-white/90">Featured Snippet</b> — Direct answer ≤40 từ, list, bảng so sánh</span></div>
      <div class="flex items-start gap-2"><span class="text-fuchsia-400 font-black shrink-0 w-8">10%</span><span><b class="text-white/90">Entity Density</b> — NLP entity: tên riêng, số liệu, thuật ngữ</span></div>
      <div class="flex items-start gap-2"><span class="text-pink-400 font-black shrink-0 w-8">10%</span><span><b class="text-white/90">Fluff Penalty</b> — Trừ điểm cho câu sáo rỗng, lặp ý</span></div>
      <div class="flex items-start gap-2"><span class="text-pink-400 font-black shrink-0 w-8">10%</span><span><b class="text-white/90">Citation Pattern</b> — Perplexity / ChatGPT / Gemini trích dẫn</span></div>
    </div>
    <div class="mt-3 pt-2 border-t border-white/5 flex items-center justify-between">
      <span class="text-[8px] text-white/30 italic">Powered by Gemini AI · 8 Criteria</span>
      <span class="text-[8px] font-black text-purple-400/60">&gt;85 = TOP 1</span>
    </div>
  </div>
{/if}
