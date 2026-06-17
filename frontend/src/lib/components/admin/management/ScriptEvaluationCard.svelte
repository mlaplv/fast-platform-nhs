<script lang="ts">
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Play from "@lucide/svelte/icons/play";
  import AlertTriangle from "@lucide/svelte/icons/alert-triangle";
  import CheckCircle from "@lucide/svelte/icons/check-circle";
  import XCircle from "@lucide/svelte/icons/x-circle";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import HelpCircle from "@lucide/svelte/icons/help-circle";
  import type { VideoScript } from "$lib/types";

  interface Props {
    activeScript: VideoScript;
    isEvaluating: boolean;
    isOptimizing: boolean;
    onEvaluate: () => Promise<void>;
    onOptimize: () => Promise<void>;
  }

  let {
    activeScript,
    isEvaluating,
    isOptimizing,
    onEvaluate,
    onOptimize
  }: Props = $props();

  const criteria = [
    { key: 'hook_retention', label: 'Hook & Giữ Chân 3s/10s', color: 'text-orange-400', border: 'border-orange-500/20', bg: 'bg-orange-950/10', text: 'orange' },
    { key: 'audio_visual_harmony', label: 'Đồng bộ Nghe - Nhìn', color: 'text-cyan-400', border: 'border-cyan-500/20', bg: 'bg-cyan-950/10', text: 'cyan' },
    { key: 'ai_generation_viability', label: 'Độ Khả Thi Prompt AI', color: 'text-purple-400', border: 'border-purple-500/20', bg: 'bg-purple-950/10', text: 'purple' },
    { key: 'platform_optimization', label: 'Tối Ưu Hóa Nền Tảng', color: 'text-pink-400', border: 'border-pink-500/20', bg: 'bg-pink-950/10', text: 'pink' },
    { key: 'brand_integrity', label: 'Bảo Toàn Thương Hiệu', color: 'text-emerald-400', border: 'border-emerald-500/20', bg: 'bg-emerald-950/10', text: 'emerald' },
  ] as const;

  let evalReport = $derived(activeScript?.structured_script?.evaluation);

  function getScoreStatus(score: number) {
    if (score >= 8) return { label: 'ĐẠT CHUẨN', color: 'text-emerald-400 bg-emerald-950/30 border-emerald-500/20' };
    if (score >= 5) return { label: 'CẦN TỐI ƯU', color: 'text-yellow-400 bg-yellow-950/30 border-yellow-500/20' };
    return { label: 'LỖI SẢN XUẤT', color: 'text-red-400 bg-red-950/30 border-red-500/20' };
  }
</script>

<div class="space-y-6">
  <!-- Status Wrapper -->
  {#if !evalReport && !isEvaluating}
    <!-- Empty State / Direct CTA to Evaluate -->
    <div class="border border-dashed border-gray-800 bg-black/40 rounded-xl p-8 text-center flex flex-col items-center justify-center gap-4 relative overflow-hidden group">
      <div class="absolute inset-0 bg-radial-at-c from-cyan-500/5 via-transparent to-transparent opacity-30"></div>
      
      <div class="w-12 h-12 rounded-2xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-center text-cyan-400 relative group-hover:scale-105 transition-transform duration-300">
        <Sparkles class="w-5 h-5 text-cyan-400 animate-pulse" />
      </div>
      
      <div>
        <h4 class="text-xs font-bold text-gray-200 uppercase tracking-widest font-mono">Kịch Bản Chưa Được Kiểm Định AI</h4>
        <p class="text-[10px] text-gray-500 max-w-sm mx-auto mt-1 leading-relaxed">
          Chạy đánh giá để kiểm nghiệm độ tương thích của các cảnh quay với Runway/Midjourney, đo nhịp điệu chuyển cảnh và tính bảo toàn nhận diện thương hiệu.
        </p>
      </div>
      
      <button
        onclick={onEvaluate}
        class="mt-2 flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-purple-600 hover:from-cyan-500 hover:to-purple-500 border border-cyan-400/20 rounded-lg text-xs font-mono font-bold tracking-wider text-white shadow-lg shadow-cyan-500/10 hover:shadow-cyan-500/20 active:scale-98 transition-all"
      >
        <Play class="w-3.5 h-3.5 fill-current" />
        <span>KÍCH HOẠT ĐÁNH GIÁ KỊCH BẢN</span>
      </button>
    </div>
  {:else if isEvaluating}
    <!-- Analyzing Loading State -->
    <div class="border border-cyan-500/20 bg-cyan-950/5 rounded-xl p-8 text-center flex flex-col items-center justify-center gap-4 animate-pulse">
      <Loader2 class="w-8 h-8 text-cyan-400 animate-spin" />
      <div>
        <h4 class="text-xs font-bold text-cyan-400 uppercase tracking-widest font-mono font-bold">ĐẠO DIỄN AI ĐANG PHÂN TÍCH...</h4>
        <div class="text-[9px] font-mono text-gray-500 mt-2 space-y-1">
          <p>• Đang đo lường nhịp độ chuyển cảnh & Pacing lời thoại...</p>
          <p>• Đang kiểm duyệt từ ngữ trừu tượng không khả thi cho Runway/Midjourney...</p>
          <p>• Đang xác minh tính nhất quán bao bì và logo thương hiệu...</p>
        </div>
      </div>
    </div>
  {:else if evalReport}
    <!-- Score Dashboard -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-3">
      {#each criteria as item}
        {@const criterion = evalReport[item.key]}
        {#if criterion}
          {@const status = getScoreStatus(criterion.score)}
          <div class="border {item.border} {item.bg} rounded-xl p-3.5 flex flex-col justify-between gap-3 relative group">
            <span class="text-[8px] font-mono font-bold tracking-wider text-gray-500 uppercase">{item.label}</span>
            <div class="flex items-baseline gap-1 mt-1">
              <span class="text-2xl font-black font-mono tracking-tight {item.color}">{criterion.score}</span>
              <span class="text-[10px] font-mono text-gray-600">/10</span>
            </div>
            <span class="text-[8px] font-mono font-bold py-0.5 px-1.5 rounded border self-start mt-2 {status.color}">
              {status.label}
            </span>
          </div>
        {/if}
      {/each}
    </div>

    <!-- AI Optimization Controller (Auto-Fix) Panel -->
    <div class="border border-purple-500/20 bg-purple-950/5 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 relative overflow-hidden group">
      <div class="absolute -right-20 -top-20 w-44 h-44 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition-all"></div>
      
      <div class="flex items-start gap-3">
        <div class="w-10 h-10 rounded-xl bg-purple-950/20 border border-purple-500/25 flex items-center justify-center text-purple-400 shrink-0">
          <Sparkles class="w-4 h-4 animate-pulse" />
        </div>
        <div>
          <h4 class="text-xs font-bold text-purple-300 uppercase tracking-wide">Tự Động Chữa Lỗi & Tối Ưu Bằng AI</h4>
          <p class="text-[10px] text-gray-500 mt-0.5 leading-relaxed max-w-xl">
            Tự động viết lại các mô tả trừu tượng thành Prompt chỉ dẫn vật lý cho Runway/Midjourney, hiệu chỉnh độ dài lời thoại khớp thời lượng và chia tách phân cảnh bị lỗi pacing.
          </p>
        </div>
      </div>
      
      <div class="flex items-center gap-2 shrink-0 w-full md:w-auto">
        <button
          onclick={onOptimize}
          disabled={isOptimizing || isEvaluating}
          class="flex-1 md:flex-none flex items-center justify-center gap-1.5 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 border border-purple-400/20 rounded text-xs font-mono font-bold uppercase tracking-wider text-white shadow-md shadow-purple-500/5 hover:shadow-purple-500/20 disabled:opacity-50 active:scale-98 transition-all"
        >
          {#if isOptimizing}
            <Loader2 class="w-3.5 h-3.5 animate-spin" />
            <span>ĐANG VÁ LỖI KỊCH BẢN...</span>
          {:else}
            <Sparkles class="w-3.5 h-3.5 text-purple-200" />
            <span>AI TỰ SỬA TOÀN BỘ LỖI</span>
          {/if}
        </button>

        <button
          onclick={onEvaluate}
          disabled={isOptimizing || isEvaluating}
          class="flex items-center justify-center p-2 bg-gray-950/40 hover:bg-gray-800/40 border border-gray-800 rounded text-gray-400 hover:text-gray-200 font-mono text-xs disabled:opacity-50 transition-colors"
          title="Đánh giá lại kịch bản"
        >
          {#if isEvaluating}
            <span>ĐANG QUÉT...</span>
          {:else}
            <span>ĐÁNH GIÁ LẠI</span>
          {/if}
        </button>
      </div>
    </div>

    <!-- Overall Recommendation from Director -->
    {#if evalReport.overall_recommendation}
      <div class="border border-gray-900 bg-black/40 rounded-xl p-4 space-y-2">
        <span class="text-[9px] font-mono text-yellow-400/80 uppercase tracking-wider font-bold block mb-1">🎬 ĐẠO DIỄN AI KHUYÊN:</span>
        <p class="text-xs text-gray-300 leading-relaxed font-sans whitespace-pre-line">
          {evalReport.overall_recommendation}
        </p>
      </div>
    {/if}

    <!-- Detailed Bento Grid for Criteria -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {#each criteria as item}
        {@const criterion = evalReport[item.key]}
        {#if criterion}
          {@const hasBugs = criterion.cons && criterion.cons.length > 0}
          <div class="border {item.border} {item.bg} rounded-xl p-5 space-y-4">
            <div class="flex items-center justify-between border-b border-gray-900/60 pb-2.5">
              <span class="text-[10px] font-mono font-bold tracking-wider {item.color} uppercase">
                {item.label}
              </span>
              <span class="text-[11px] font-mono font-bold {criterion.score >= 8 ? 'text-emerald-400' : criterion.score >= 5 ? 'text-yellow-400' : 'text-red-400'}">
                {criterion.score}/10
              </span>
            </div>

            <div class="space-y-3">
              <!-- Pros -->
              {#if criterion.pros && criterion.pros.length > 0}
                <div class="space-y-1">
                  <span class="text-[8px] font-mono text-emerald-400/80 uppercase tracking-widest font-bold block">✓ Điểm mạnh sản xuất:</span>
                  <ul class="space-y-1">
                    {#each criterion.pros as pro}
                      <li class="text-[11px] text-gray-300 leading-relaxed font-sans flex items-start gap-1.5">
                        <CheckCircle class="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{pro}</span>
                      </li>
                    {/each}
                  </ul>
                </div>
              {/if}

              <!-- Cons -->
              {#if hasBugs}
                <div class="space-y-1">
                  <span class="text-[8px] font-mono text-red-400/80 uppercase tracking-widest font-bold block">✗ Lỗi kỹ thuật phát hiện:</span>
                  <ul class="space-y-1">
                    {#each criterion.cons as con}
                      <li class="text-[11px] text-red-200/90 leading-relaxed font-sans flex items-start gap-1.5">
                        <XCircle class="w-3.5 h-3.5 text-red-500 shrink-0 mt-0.5" />
                        <span>{con}</span>
                      </li>
                    {/each}
                  </ul>
                </div>
              {/if}

              <!-- Suggestions -->
              {#if criterion.suggestions && criterion.suggestions.length > 0}
                <div class="space-y-1">
                  <span class="text-[8px] font-mono text-yellow-400/80 uppercase tracking-widest font-bold block">💡 Giải pháp đề xuất:</span>
                  <ul class="space-y-1">
                    {#each criterion.suggestions as suggestion}
                      <li class="text-[11px] text-yellow-100/90 leading-relaxed font-sans flex items-start gap-1.5">
                        <Sparkles class="w-3.5 h-3.5 text-yellow-400 shrink-0 mt-0.5" />
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
  {/if}
</div>
