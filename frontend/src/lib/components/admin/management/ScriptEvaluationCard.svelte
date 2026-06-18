<script lang="ts">
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Play from "@lucide/svelte/icons/play";
  import CheckCircle from "@lucide/svelte/icons/check-circle";
  import XCircle from "@lucide/svelte/icons/x-circle";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Zap from "@lucide/svelte/icons/zap";
  import type { VideoScript, VideoScriptEvaluation, EvaluationCriterion } from "$lib/types";

  interface Props {
    activeScript: VideoScript;
    isEvaluating: boolean;
    isOptimizing: boolean;
    onEvaluate: () => Promise<void>;
    onForceEvaluate: () => Promise<void>;
    onOptimize: (focusCriterion?: string) => Promise<void>;
    isScriptModified: boolean;
  }

  let {
    activeScript,
    isEvaluating,
    isOptimizing,
    onEvaluate,
    onForceEvaluate,
    onOptimize,
    isScriptModified
  }: Props = $props();

  interface CriterionItem {
    readonly key: keyof VideoScriptEvaluation;
    readonly label: string;
    readonly icon: string;
    readonly color: string;
    readonly border: string;
    readonly bg: string;
    readonly weight: number;
  }

  // Trọng số đánh giá — tổng = 1.0
  // ai_generation_viability cao nhất vì đây là hệ thống sinh prompt
  const criteria: readonly CriterionItem[] = [
    { key: 'ai_generation_viability',  label: 'Prompt AI (Runway/MJ/Kling)', icon: '🤖', color: 'text-purple-400',  border: 'border-purple-500/25', bg: 'bg-purple-950/10', weight: 0.18 },
    { key: 'hook_retention',           label: 'Hook & Giữ Chân 3s',          icon: '⚡', color: 'text-orange-400',  border: 'border-orange-500/25', bg: 'bg-orange-950/10', weight: 0.14 },
    { key: 'emotional_arc',            label: 'Kiến Trúc Cảm Xúc',           icon: '🎭', color: 'text-rose-400',    border: 'border-rose-500/25',   bg: 'bg-rose-950/10',   weight: 0.12 },
    { key: 'tts_sync_compliance',      label: 'TTS Sync (Từ/Giây)',           icon: '🎙️', color: 'text-sky-400',    border: 'border-sky-500/25',    bg: 'bg-sky-950/10',    weight: 0.12 },
    { key: 'audio_visual_harmony',     label: 'Đồng Bộ Nghe-Nhìn',           icon: '🎬', color: 'text-cyan-400',   border: 'border-cyan-500/25',   bg: 'bg-cyan-950/10',   weight: 0.11 },
    { key: 'cta_effectiveness',        label: 'Hiệu Quả CTA',                 icon: '🎯', color: 'text-amber-400',  border: 'border-amber-500/25',  bg: 'bg-amber-950/10',  weight: 0.11 },
    { key: 'duration_compliance',      label: 'Tuân Thủ Thời Lượng',          icon: '⏱️', color: 'text-yellow-400', border: 'border-yellow-500/25', bg: 'bg-yellow-950/10', weight: 0.10 },
    { key: 'platform_optimization',    label: 'Tối Ưu Nền Tảng',             icon: '📱', color: 'text-pink-400',   border: 'border-pink-500/25',   bg: 'bg-pink-950/10',   weight: 0.07 },
    { key: 'brand_integrity',          label: 'Bảo Toàn Thương Hiệu',         icon: '🏷️', color: 'text-emerald-400',border: 'border-emerald-500/25',bg: 'bg-emerald-950/10',weight: 0.05 },
  ];

  let evalReport = $derived(activeScript?.structured_script?.evaluation);
  let overallScore = $derived(evalReport?.overall_score);

  // Sắp xếp criteria theo điểm thấp nhất lên đầu (ưu tiên lỗi)
  let sortedCriteria = $derived.by(() => {
    if (!evalReport) return [...criteria];
    return [...criteria].sort((a, b) => {
      const sa = (evalReport[a.key] as EvaluationCriterion)?.score ?? 10;
      const sb = (evalReport[b.key] as EvaluationCriterion)?.score ?? 10;
      return sa - sb; // lỗi nghiêm trọng (điểm thấp) lên đầu
    });
  });

  // Đếm số tiêu chí cần tối ưu (< 8 điểm)
  let errorCount = $derived.by(() => {
    if (!evalReport) return 0;
    return criteria.filter(c => ((evalReport[c.key] as EvaluationCriterion)?.score ?? 10) < 8).length;
  });

  // Đếm tổng số lỗi chi tiết cần sửa (tổng số lượng cons trong các tiêu chí có điểm < 8)
  let detailedErrorCount = $derived.by(() => {
    if (!evalReport) return 0;
    return criteria.reduce((sum, c) => {
      const crit = evalReport[c.key] as EvaluationCriterion;
      if (crit && crit.score < 8 && Array.isArray(crit.cons)) {
        return sum + crit.cons.length;
      }
      return sum;
    }, 0);
  });

  let criticalCount = $derived.by(() => {
    if (!evalReport) return 0;
    return criteria.filter(c => ((evalReport[c.key] as EvaluationCriterion)?.score ?? 10) < 5).length;
  });

  function getScoreStatus(score: number) {
    if (score >= 8) return { label: 'ĐẠT CHUẨN', color: 'text-emerald-400 bg-emerald-950/30 border-emerald-500/20', bar: 'bg-emerald-500' };
    if (score >= 6) return { label: 'KHÁ TỐT', color: 'text-yellow-400 bg-yellow-950/30 border-yellow-500/20', bar: 'bg-yellow-500' };
    if (score >= 4) return { label: 'CẦN TỐI ƯU', color: 'text-orange-400 bg-orange-950/30 border-orange-500/20', bar: 'bg-orange-500' };
    return { label: 'LỖI NGHIÊM TRỌNG', color: 'text-red-400 bg-red-950/30 border-red-500/20', bar: 'bg-red-500' };
  }

  function getGradeInfo(score: number) {
    if (score >= 8.5) return { label: 'PRODUCTION READY', sub: 'Sẵn sàng sản xuất', cls: 'from-emerald-500 to-cyan-500', ring: 'stroke-emerald-400' };
    if (score >= 7)   return { label: 'NEARLY READY', sub: 'Gần đạt chuẩn sản xuất', cls: 'from-yellow-500 to-orange-500', ring: 'stroke-yellow-400' };
    if (score >= 5)   return { label: 'NEEDS WORK', sub: 'Cần tối ưu thêm', cls: 'from-orange-500 to-red-500', ring: 'stroke-orange-400' };
    return { label: 'CRITICAL ISSUES', sub: 'Có lỗi nghiêm trọng', cls: 'from-red-600 to-pink-600', ring: 'stroke-red-400' };
  }

  // SVG ring gauge — 120px, circumference = 2π×48 ≈ 301.6
  const CIRC = 301.6;
  let ringOffset = $derived(overallScore !== undefined ? CIRC * (1 - overallScore / 10) : CIRC);
</script>

<div class="space-y-5">
  <!-- ─── EMPTY STATE ─── -->
  {#if !evalReport && !isEvaluating}
    <div class="border border-dashed border-gray-800 bg-black/40 rounded-2xl p-10 text-center flex flex-col items-center gap-5 relative overflow-hidden group">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,theme(colors.cyan.500/5%),transparent_70%)] pointer-events-none"></div>
      <div class="w-14 h-14 rounded-2xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-center group-hover:scale-105 transition-transform duration-300">
        <Sparkles class="w-6 h-6 text-cyan-400 animate-pulse" />
      </div>
      <div class="space-y-1.5">
        <h4 class="text-xs font-black text-gray-200 uppercase tracking-widest font-mono">Kịch Bản Chưa Được Kiểm Định AI</h4>
        <p class="text-[10px] text-gray-500 max-w-[340px] mx-auto leading-relaxed">
          Đánh giá 9 tiêu chí chuyên nghiệp: chất lượng prompt Runway/Midjourney, TTS sync, emotional arc, CTA, brand integrity và hơn thế nữa.
        </p>
      </div>
      <button
        onclick={onEvaluate}
        class="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-purple-600 hover:from-cyan-500 hover:to-purple-500 border border-cyan-400/20 rounded-xl text-xs font-mono font-bold tracking-wider text-white shadow-lg shadow-cyan-500/10 hover:shadow-cyan-500/25 active:scale-95 transition-all"
      >
        <Play class="w-3.5 h-3.5 fill-current" />
        KÍCH HOẠT ĐÁNH GIÁ 9 TIÊU CHÍ
      </button>
    </div>

  <!-- ─── LOADING STATE ─── -->
  {:else if isEvaluating}
    <div class="border border-cyan-500/20 bg-cyan-950/5 rounded-2xl p-8 text-center flex flex-col items-center gap-4">
      <div class="relative w-12 h-12">
        <div class="absolute inset-0 rounded-full border border-cyan-500/20 border-t-cyan-400 animate-spin"></div>
        <Sparkles class="absolute inset-0 m-auto w-5 h-5 text-cyan-400 animate-pulse" />
      </div>
      <div>
        <h4 class="text-xs font-black text-cyan-400 uppercase tracking-widest font-mono">ĐẠO DIỄN AI ĐANG PHÂN TÍCH 9 TIÊU CHÍ...</h4>
        <div class="text-[9px] font-mono text-gray-500 mt-2 space-y-0.5 text-left max-w-[320px] mx-auto">
          <p>• Đo TTS word-per-second từng phân cảnh...</p>
          <p>• Kiểm tra prompt Runway/MJ — lọc từ trừu tượng...</p>
          <p>• Phân tích emotional arc: Hook→Pain→Solution→CTA...</p>
          <p>• Xác minh tuân thủ thời lượng ±10%...</p>
          <p>• Đánh giá hiệu quả CTA & yếu tố khẩn cấp...</p>
        </div>
      </div>
    </div>

  <!-- ─── RESULTS ─── -->
  {:else if evalReport}

    <!-- Overall Score Ring + Summary -->
    {#if overallScore !== undefined}
      {@const grade = getGradeInfo(overallScore)}
      <div class="bg-gradient-to-br from-gray-950 to-black border border-gray-800 rounded-2xl p-5 flex items-center gap-6">
        <!-- SVG Ring Gauge -->
        <div class="relative shrink-0 w-[96px] h-[96px]">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 112 112">
            <!-- Track -->
            <circle cx="56" cy="56" r="48" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="8"/>
            <!-- Progress -->
            <circle
              cx="56" cy="56" r="48" fill="none"
              stroke-width="8" stroke-linecap="round"
              class="{grade.ring} transition-all duration-700"
              stroke-dasharray="{CIRC}"
              stroke-dashoffset="{ringOffset}"
            />
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <span class="text-2xl font-black font-mono text-white leading-none">{overallScore.toFixed(1)}</span>
            <span class="text-[8px] font-mono text-gray-500 mt-0.5">/10</span>
          </div>
        </div>

        <!-- Grade Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-2">
            <span class="inline-block px-2.5 py-0.5 rounded-md text-[9px] font-black font-mono uppercase tracking-widest bg-gradient-to-r {grade.cls} text-black">
              {grade.label}
            </span>
          </div>
          <p class="text-xs text-gray-300 font-semibold">{grade.sub}</p>
          <p class="text-[10px] text-gray-500 mt-1">9 tiêu chí · {criteria.length - errorCount} đạt chuẩn · <span class="{errorCount > 0 ? 'text-orange-400' : 'text-emerald-400'}">{errorCount} cần tối ưu</span>{#if criticalCount > 0} · <span class="text-red-400 font-bold">{criticalCount} lỗi nghiêm trọng</span>{/if}</p>

          <!-- Mini progress bars cho các tiêu chí ưu tiên cao -->
          <div class="mt-3 space-y-1">
            {#each criteria.slice(0, 3) as item}
              {@const crit = evalReport[item.key] as EvaluationCriterion}
              {#if crit}
                {@const st = getScoreStatus(crit.score)}
                <div class="flex items-center gap-2">
                  <span class="text-[7px] font-mono text-gray-600 w-28 truncate">{item.label}</span>
                  <div class="flex-1 h-1 bg-gray-900 rounded-full overflow-hidden">
                    <div class="h-full {st.bar} rounded-full transition-all duration-500" style="width:{crit.score * 10}%"></div>
                  </div>
                  <span class="text-[8px] font-mono font-bold {crit.score >= 8 ? 'text-emerald-400' : crit.score >= 5 ? 'text-orange-400' : 'text-red-400'}">{crit.score}</span>
                </div>
              {/if}
            {/each}
          </div>
        </div>
      </div>
    {/if}

    <!-- 9-Criteria Score Grid — sắp xếp lỗi lên trên -->
    <div class="grid grid-cols-3 gap-2">
      {#each sortedCriteria as item}
        {@const criterion = evalReport[item.key] as EvaluationCriterion}
        {#if criterion}
          {@const status = getScoreStatus(criterion.score)}
          <div class="border {item.border} {item.bg} rounded-xl p-3 flex flex-col gap-1.5 relative">
            <!-- Badge lỗi nghiêm trọng -->
            {#if criterion.score < 5}
              <span class="absolute -top-1.5 -right-1.5 w-3.5 h-3.5 bg-red-500 rounded-full border-2 border-black flex items-center justify-center">
                <span class="text-[5px] font-black text-white">!</span>
              </span>
            {/if}
            <span class="text-base leading-none">{item.icon}</span>
            <span class="text-[7px] font-mono font-bold tracking-wide text-gray-500 uppercase leading-tight">{item.label}</span>
            <div class="flex items-baseline gap-0.5">
              <span class="text-2xl font-black font-mono {item.color} leading-none">{criterion.score}</span>
              <span class="text-[8px] font-mono text-gray-700">/10</span>
            </div>
            <!-- Progress bar -->
            <div class="h-0.5 bg-gray-900 rounded-full overflow-hidden">
              <div class="h-full {status.bar} rounded-full transition-all" style="width:{criterion.score * 10}%"></div>
            </div>
            <span class="text-[6px] font-mono font-black py-0.5 px-1 rounded border self-start {status.color}">{status.label}</span>
          </div>
        {/if}
      {/each}
    </div>

    <!-- Action Buttons Row -->
    <div class="flex items-center gap-2">
      <button
        onclick={() => onOptimize()}
        disabled={isOptimizing || isEvaluating}
        class="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 border border-purple-400/20 rounded-xl text-xs font-mono font-black uppercase tracking-wider text-white shadow-md shadow-purple-500/10 disabled:opacity-50 active:scale-95 transition-all"
      >
        {#if isOptimizing}
          <Loader2 class="w-3.5 h-3.5 animate-spin" />
          <span>ĐANG TỐI ƯU HÓA...</span>
        {:else}
          <Zap class="w-3.5 h-3.5" />
          <span>AI TỰ SỬA {detailedErrorCount > 0 ? `${detailedErrorCount} LỖI` : 'TOÀN BỘ'}</span>
        {/if}
      </button>
      <button
        onclick={onForceEvaluate}
        disabled={isOptimizing || isEvaluating}
        title="Đánh giá lại (bắt buộc)"
        class="flex items-center justify-center gap-1.5 px-4 py-2.5 bg-gray-900/60 hover:bg-gray-800/60 border border-gray-800 hover:border-gray-700 rounded-xl text-gray-400 hover:text-gray-200 font-mono text-xs font-bold disabled:opacity-50 transition-all active:scale-95"
      >
        {#if isEvaluating}
          <Loader2 class="w-3.5 h-3.5 animate-spin" />
        {:else}
          <RefreshCw class="w-3.5 h-3.5" />
        {/if}
        <span>ĐÁNH GIÁ LẠI</span>
      </button>
    </div>

    <!-- Overall Director Recommendation -->
    {#if evalReport.overall_recommendation}
      <div class="border border-yellow-500/15 bg-yellow-950/5 rounded-xl p-4 space-y-1.5">
        <span class="text-[9px] font-mono text-yellow-400/80 uppercase tracking-widest font-black block">🎬 CHIẾN LƯỢC TỪ ĐẠO DIỄN AI:</span>
        <p class="text-[11px] text-gray-300 leading-relaxed font-sans whitespace-pre-line">{evalReport.overall_recommendation}</p>
      </div>
    {/if}

    <!-- Detailed Breakdown — sắp xếp theo lỗi -->
    <div class="space-y-3">
      <div class="flex items-center gap-2">
        <span class="text-[9px] font-mono text-gray-500 uppercase tracking-widest font-bold">Chi Tiết Từng Tiêu Chí</span>
        <div class="flex-1 h-px bg-gray-900"></div>
        <span class="text-[8px] font-mono text-gray-600">{errorCount > 0 ? `Ưu tiên ${errorCount} lỗi` : 'Tất cả đạt chuẩn'}</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        {#each sortedCriteria as item}
          {@const criterion = evalReport[item.key] as EvaluationCriterion}
          {#if criterion}
            {@const status = getScoreStatus(criterion.score)}
            {@const hasBugs = criterion.cons?.length > 0}
            <div class="border {item.border} {item.bg} rounded-xl p-4 space-y-3">
              <!-- Header -->
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-base">{item.icon}</span>
                  <span class="text-[10px] font-mono font-black {item.color} uppercase tracking-wide">{item.label}</span>
                </div>
                <div class="flex items-center gap-3">
                  <!-- Score with bar -->
                  <div class="flex items-center gap-1.5">
                    <div class="w-16 h-1 bg-gray-900 rounded-full overflow-hidden">
                      <div class="h-full {status.bar} transition-all" style="width:{criterion.score * 10}%"></div>
                    </div>
                    <span class="text-[11px] font-black font-mono {criterion.score >= 8 ? 'text-emerald-400' : criterion.score >= 6 ? 'text-yellow-400' : criterion.score >= 4 ? 'text-orange-400' : 'text-red-400'}">{criterion.score}/10</span>
                  </div>
                  
                  {#if criterion.score < 10}
                    <button
                      onclick={() => onOptimize(item.key)}
                      disabled={isOptimizing || isEvaluating}
                      class="flex items-center gap-1 px-2 py-0.5 rounded bg-purple-950/40 hover:bg-purple-900/50 border border-purple-500/30 hover:border-purple-400/40 text-purple-400 hover:text-purple-300 font-mono text-[8px] font-black uppercase tracking-wide transition-all active:scale-95 disabled:opacity-50 shrink-0 shadow-sm shadow-purple-500/5"
                      title="Chỉ tập trung sửa đúng lỗi tiêu chí này qua AI"
                    >
                      <Zap class="w-2.5 h-2.5 fill-current animate-pulse" />
                      SỬA LỖI NÀY
                    </button>
                  {/if}
                </div>
              </div>

              <div class="space-y-2.5">
                <!-- Pros -->
                {#if criterion.pros?.length > 0}
                  <div class="space-y-1">
                    <span class="text-[8px] font-mono text-emerald-400/70 uppercase tracking-widest font-bold block">✓ Điểm tốt:</span>
                    <ul class="space-y-0.5">
                      {#each criterion.pros as pro}
                        <li class="text-[10px] text-gray-400 leading-relaxed font-sans flex items-start gap-1.5">
                          <CheckCircle class="w-3 h-3 text-emerald-500/70 shrink-0 mt-0.5" />
                          <span>{pro}</span>
                        </li>
                      {/each}
                    </ul>
                  </div>
                {/if}

                <!-- Cons -->
                {#if hasBugs}
                  <div class="space-y-1">
                    <span class="text-[8px] font-mono text-red-400/70 uppercase tracking-widest font-bold block">✗ Lỗi cần sửa:</span>
                    <ul class="space-y-0.5">
                      {#each criterion.cons as con}
                        <li class="text-[10px] text-red-200/80 leading-relaxed font-sans flex items-start gap-1.5">
                          <XCircle class="w-3 h-3 text-red-500/70 shrink-0 mt-0.5" />
                          <span>{con}</span>
                        </li>
                      {/each}
                    </ul>
                  </div>
                {/if}

                <!-- Suggestions -->
                {#if criterion.suggestions?.length > 0}
                  <div class="space-y-1">
                    <span class="text-[8px] font-mono text-amber-400/70 uppercase tracking-widest font-bold block">💡 Đề xuất sửa:</span>
                    <ul class="space-y-0.5">
                      {#each criterion.suggestions as suggestion}
                        <li class="text-[10px] text-amber-100/80 leading-relaxed font-sans flex items-start gap-1.5">
                          <Sparkles class="w-3 h-3 text-amber-400/70 shrink-0 mt-0.5" />
                          <span>{suggestion}</span>
                        </li>
                      {/each}
                    </ul>
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        {/each}
      </div>
    </div>

  {/if}
</div>
