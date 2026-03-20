<script lang="ts">
  import { ShieldCheck, BarChart2, Sparkles, Brain, Search, FileText, Cpu, CheckCircle2 } from "lucide-svelte";
  import { onDestroy } from "svelte";
  import type { CopyrightResult, SEOResult, AIInspectResult, AnalysisAnnotation } from "$lib/state/types";

  let {
    activeTab,
    copyrightResult,
    isCopyrightLoading,
    seoResult,
    isSeoLoading,
    aiReadyResult,
    isAiLoading,
    isBoosting = false,
    runCopyrightCheck,
    runSeoAnalysis,
    runAiAnalysis,
    runAiBooster = null,
    onfix = null
  }: {
    activeTab: 'copyright' | 'seo' | 'ai' | 'enrich' | null;
    copyrightResult: CopyrightResult | null;
    isCopyrightLoading: boolean;
    seoResult: SEOResult | null;
    isSeoLoading: boolean;
    aiReadyResult: AIInspectResult | null;
    isAiLoading: boolean;
    isBoosting?: boolean;
    runCopyrightCheck: () => void;
    runSeoAnalysis: () => void;
    runAiAnalysis: () => void;
    runAiBooster?: (() => void) | null;
    onfix?: ((snippet: string, type: string, message: string) => Promise<string | null>) | null;
  } = $props();

  let isFixing = $state<string | null>(null);

  // ── Live Analysis Phase Engine ──────────────────────────────
  const PHASES = {
    copyright: [
      { icon: '🔍', label: 'Quét nội dung bài viết',         duration: 1800 },
      { icon: '🌐', label: 'Tìm kiếm Google Top 10',          duration: 3500 },
      { icon: '🧬', label: 'So sánh cấu trúc ngữ nghĩa',      duration: 3000 },
      { icon: '⚖️', label: 'Đánh giá mức độ trùng lặp',       duration: 2500 },
      { icon: '🤖', label: 'Gemini AI xử lý kết quả',         duration: 2500 },
    ],
    seo: [
      { icon: '📄', label: 'Đọc & phân tích bài viết',        duration: 1500 },
      { icon: '🎯', label: 'Xác định Search Intent',           duration: 2500 },
      { icon: '🏆', label: 'Tải Top 5 đối thủ Google',        duration: 3500 },
      { icon: '🧠', label: 'Đánh giá E-E-A-T & Entity',       duration: 3000 },
      { icon: '✨', label: 'Tính điểm 7 tiêu chí SEO',        duration: 2500 },
    ],
    ai: [
      { icon: '📝', label: 'Đọc & làm sạch nội dung',         duration: 1500 },
      { icon: '🎯', label: 'Phân tích Search Intent',          duration: 2000 },
      { icon: '🏅', label: 'Kiểm tra E-E-A-T & Authority',    duration: 3000 },
      { icon: '🌟', label: 'Đánh giá AI Overview readiness',  duration: 2500 },
      { icon: '📊', label: 'Tính Viral Edge Score (8 tiêu chí)', duration: 2500 },
    ],
    enrich: [
      { icon: '🔍', label: 'Thu thập số liệu từ Google',      duration: 3000 },
      { icon: '🧠', label: 'Phân tích insight đối thủ',       duration: 2500 },
      { icon: '✍️',  label: 'Tổng hợp expert quotes',         duration: 3500 },
      { icon: '📋', label: 'Tạo bảng so sánh tính năng',      duration: 3000 },
      { icon: '🚀', label: 'Inject & polish content',         duration: 3000 },
    ],
  };

  let phaseIndex = $state(0);
  let phaseProgress = $state(0);
  let phaseTimer: ReturnType<typeof setInterval> | null = null;
  let progressTimer: ReturnType<typeof setInterval> | null = null;

  function startPhaseEngine(type: 'copyright' | 'seo' | 'ai' | 'enrich') {
    clearTimers();
    phaseIndex = 0;
    phaseProgress = 0;
    const phases = PHASES[type];

    function runPhase(idx: number) {
      if (idx >= phases.length) return;
      phaseIndex = idx;
      phaseProgress = 0;
      const dur = phases[idx].duration;
      const step = 16;
      progressTimer = setInterval(() => {
        phaseProgress = Math.min(phaseProgress + (step / dur) * 100, 95);
      }, step);
      phaseTimer = setTimeout(() => {
        if (progressTimer) clearInterval(progressTimer);
        phaseProgress = 100;
        setTimeout(() => runPhase(idx + 1), 150);
      }, dur);
    }
    runPhase(0);
  }

  function clearTimers() {
    if (phaseTimer) { clearTimeout(phaseTimer); phaseTimer = null; }
    if (progressTimer) { clearInterval(progressTimer); progressTimer = null; }
  }

  $effect(() => {
    if (activeTab === 'enrich' && isBoosting) startPhaseEngine('enrich');
    else if (isCopyrightLoading) startPhaseEngine('copyright');
    else if (isSeoLoading) startPhaseEngine('seo');
    else if (isAiLoading) startPhaseEngine('ai');
    else clearTimers();
  });

  onDestroy(clearTimers);

  async function handleInternalFix(snippet: string, type: string, message: string) {
    if (!onfix || isFixing) return;
    isFixing = snippet;
    try {
      await onfix(snippet, type, message);
    } finally {
      isFixing = null;
    }
  }

  // Helper
  function currentPhases(tab: 'copyright'|'seo'|'ai'|'enrich') {
    return PHASES[tab] ?? [];
  }
</script>

<div class="shrink-0 flex flex-col gap-2">

  <!-- ═══════════════════════════════════════════
       LIVE LOADING STATE (shared design language)
  ════════════════════════════════════════════ -->
  {#if (activeTab === 'copyright' && isCopyrightLoading) || (activeTab === 'seo' && isSeoLoading) || (activeTab === 'ai' && isAiLoading) || (activeTab === 'enrich' && isBoosting)}
    {@const tab = activeTab}
    {@const phases = currentPhases(tab || 'copyright')}
    {@const accent = tab === 'copyright' ? '#f97316' : tab === 'seo' ? '#3b82f6' : tab === 'enrich' ? '#ec4899' : '#a855f7'}
    {@const accentBg = tab === 'copyright' ? 'from-orange-950/80' : tab === 'seo' ? 'from-blue-950/80' : tab === 'enrich' ? 'from-pink-950/80' : 'from-purple-950/80'}
    {@const accentBorder = tab === 'copyright' ? 'border-orange-500/20' : tab === 'seo' ? 'border-blue-500/20' : tab === 'enrich' ? 'border-pink-500/20' : 'border-purple-500/20'}

    <div class="relative overflow-hidden rounded-xl border {accentBorder} bg-gradient-to-br {accentBg} via-slate-950/90 to-slate-900/90 p-4 live-scanner">
      <!-- Animated scan line -->
      <div class="scan-line" style="--accent: {accent}"></div>
      
      <!-- Header -->
      <div class="flex items-center gap-3 mb-4">
        <div class="relative w-8 h-8">
          <div class="absolute inset-0 rounded-lg animate-ping opacity-20" style="background:{accent}"></div>
          <div class="relative w-8 h-8 rounded-lg flex items-center justify-center" style="background:{accent}20; border:1px solid {accent}30">
            {#if tab === 'copyright'}<ShieldCheck size={14} style="color:{accent}" />
            {:else if tab === 'seo'}<BarChart2 size={14} style="color:{accent}" />
            {:else if tab === 'enrich'}<Brain size={14} style="color:{accent}" />
            {:else}<Sparkles size={14} style="color:{accent}" />{/if}
          </div>
        </div>
        <div>
          <div class="text-[10px] font-black uppercase tracking-[0.15em]" style="color:{accent}">
            {tab === 'copyright' ? 'Plagiarism Cop™' : tab === 'seo' ? 'SEO Strategist™' : tab === 'enrich' ? 'AI Booster™' : 'Viral Edge™'}
          </div>
          <div class="text-[8px] text-white/30">AI đang xử lý...</div>
        </div>
        <!-- Pulsing orb -->
        <div class="ml-auto flex items-center gap-1">
          <div class="w-1.5 h-1.5 rounded-full animate-pulse" style="background:{accent}"></div>
          <div class="w-1 h-1 rounded-full animate-pulse" style="background:{accent}; animation-delay:0.3s"></div>
          <div class="w-1.5 h-1.5 rounded-full animate-pulse" style="background:{accent}; animation-delay:0.6s"></div>
        </div>
      </div>

      <!-- Phase list -->
      <div class="flex flex-col gap-1.5">
        {#each phases as phase, i}
          {@const isDone = i < phaseIndex}
          {@const isActive = i === phaseIndex}
          {@const isPending = i > phaseIndex}
          <div class="flex items-center gap-2.5 transition-all duration-300 {isPending ? 'opacity-25' : 'opacity-100'}">
            <!-- Step icon -->
            <div class="w-5 h-5 rounded-full shrink-0 flex items-center justify-center text-[10px] transition-all duration-300
                {isDone ? 'shadow-glow' : isActive ? 'ring-pulse' : ''}"
              style="{isDone ? `background:${accent}30; border:1px solid ${accent}60` : isActive ? `background:${accent}15; border:1px solid ${accent}40` : 'background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08)'}">
              {#if isDone}
                <span style="color:{accent}">✓</span>
              {:else if isActive}
                <span class="animate-spin inline-block text-[8px]" style="color:{accent}">⟳</span>
              {:else}
                <span class="text-white/20">{i + 1}</span>
              {/if}
            </div>

            <!-- Label & progress -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-2 mb-1">
                <span class="text-[9px] font-medium {isDone ? 'text-white/60' : isActive ? 'text-white/90' : 'text-white/25'}">
                  {phase.icon} {phase.label}
                </span>
                {#if isDone}
                  <span class="text-[8px] font-black shrink-0" style="color:{accent}">100%</span>
                {:else if isActive}
                  <span class="text-[8px] font-black shrink-0" style="color:{accent}">{Math.round(phaseProgress)}%</span>
                {/if}
              </div>
              
              <!-- Progress bar -->
              <div class="h-px rounded-full bg-white/5 overflow-hidden">
                {#if isDone}
                  <div class="h-full w-full rounded-full" style="background:{accent}60"></div>
                {:else if isActive}
                  <div class="h-full rounded-full transition-all duration-100 progress-shimmer"
                    style="width:{phaseProgress}%; background:linear-gradient(90deg, {accent}80, {accent})"></div>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>

      <!-- Footer estimate -->
      <div class="mt-3 pt-2 border-t border-white/5 flex items-center justify-between">
        <span class="text-[8px] text-white/20 italic">
          {tab === 'copyright' ? 'Kết nối Google Search API + Gemini...' : tab === 'seo' ? 'So sánh Top 5 đối thủ real-time...' : tab === 'enrich' ? 'Injecting Real-world data & Expert Quotes...' : '8 tiêu chí Viral Edge đang chạy...'}
        </span>
        <span class="text-[8px] font-black animate-pulse" style="color:{accent}">LIVE</span>
      </div>
    </div>

  <!-- ═══════════════════════════════════════════
       COPYRIGHT RESULT
  ════════════════════════════════════════════ -->
  {:else if activeTab === 'copyright'}
    {#if copyrightResult}
      {@const pct = Math.round(copyrightResult.uniqueness_score * 100)}
      {@const riskColor = copyrightResult.risk_level === 'LOW' ? '#10b981' : copyrightResult.risk_level === 'MEDIUM' ? '#f59e0b' : '#ef4444'}
      <div class="px-3 py-2 rounded-xl border flex items-center gap-4"
        style="background: {riskColor}08; border-color: {riskColor}20;">
        <div class="relative w-12 h-12 shrink-0">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="4"/>
            <circle cx="24" cy="24" r="19" fill="none" stroke={riskColor}
              stroke-width="4"
              stroke-dasharray={2 * Math.PI * 19}
              stroke-dashoffset={2 * Math.PI * 19 * (1 - copyrightResult.uniqueness_score)}
              stroke-linecap="round"
              style="transition:stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)"
            />
          </svg>
          <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black" style="color:{riskColor}">{pct}%</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-[9px] font-black uppercase" style="color:{riskColor}">
              🔍 COPYRIGHT — {copyrightResult.risk_level === 'LOW' ? 'Rủi ro thấp ✅' : copyrightResult.risk_level === 'MEDIUM' ? 'Cần cải thiện ⚠️' : 'Rủi ro cao 🚨'}
            </span>
            <button onclick={() => runCopyrightCheck()} class="text-[8px] text-white/20 hover:text-orange-400 transition-colors" title="Chạy lại">↻</button>
          </div>
          <p class="text-[9px] text-white/50 leading-relaxed truncate">{copyrightResult.verdict}</p>
          {#if copyrightResult.annotations?.length > 0}
            <div class="mt-2 flex flex-col gap-1.5">
              {#each copyrightResult.annotations as ann}
                {@const isInternal = ann.type === 'internal-dedup'}
                {@const annHex = ann.severity === 'high' ? '#ef4444' : ann.severity === 'medium' ? '#f59e0b' : '#eab308'}
                <div class="p-2 rounded-lg border bg-white/[0.02] flex flex-col gap-1.5 transition-all hover:bg-white/[0.04]"
                     style="border-color: {annHex}20">
                  <div class="flex items-start justify-between gap-2">
                    <span class="text-[7px] font-black px-1 py-0.5 rounded uppercase"
                      style="background: {annHex}20; color: {annHex}">
                      {isInternal ? '🔁 TRÙNG LẶP NỘI BỘ' : `🚨 COPYRIGHT ${ann.severity?.toUpperCase()}`}
                    </span>
                    <button
                      onclick={() => handleInternalFix(ann.text, ann.type || 'copyright', ann.reason || 'Cần kiểm tra COPYRIGHT')}
                      disabled={!!isFixing}
                      class="shrink-0 flex items-center gap-1 px-2 py-0.5 rounded border border-white/10 hover:bg-white/10 text-[7px] font-black uppercase transition-all disabled:opacity-40">
                      {#if isFixing === ann.text}
                        <span class="w-2 h-2 border border-white/30 border-t-white rounded-full animate-spin"></span> FIXING...
                      {:else if ann.type === 'fixed'}
                        <CheckCircle2 size={8} class="text-emerald-400" /> ĐÃ SỬA
                      {:else}
                        <Sparkles size={8} class="text-yellow-400" /> SỬA LỖI
                      {/if}
                    </button>
                  </div>
                  <p class="text-[8px] text-white/70 leading-relaxed">
                    <span class="text-white/30 italic">"{ann.text}"</span> — {ann.reason}
                  </p>
                  {#if ann.source_url && !isInternal}
                    <a href={ann.source_url} target="_blank" class="text-[7px] text-blue-400/60 hover:text-blue-400 underline truncate">
                      🔗 Nguồn: {ann.source_url}
                    </a>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">
        Nhấn <span class="text-orange-400/70 font-bold">COPYRIGHT</span> để phân tích đạo văn.
      </div>
    {/if}

  <!-- ═══════════════════════════════════════════
       SEO RESULT
  ════════════════════════════════════════════ -->
  {:else if activeTab === 'seo'}
    {#if seoResult}
      {@const gradeColor = seoResult.grade === 'A' ? '#10b981' : seoResult.grade === 'B' ? '#3b82f6' : seoResult.grade === 'C' ? '#f59e0b' : '#ef4444'}
      <div class="px-3 py-2 rounded-xl border flex flex-col gap-2"
        style="background: {gradeColor}08; border-color: {gradeColor}20;">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-lg shrink-0 flex items-center justify-center font-black text-lg" style="background:{gradeColor}15; color:{gradeColor}">{seoResult.grade}</div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-[9px] font-black uppercase" style="color:{gradeColor}">📊 SEO Score — {seoResult.total_score}/100</span>
              <button onclick={() => runSeoAnalysis()} class="text-[8px] text-white/20 hover:text-blue-400 transition-colors" title="Chạy lại">↻</button>
            </div>
            <p class="text-[9px] text-white/50 leading-relaxed line-clamp-2">{seoResult.summary}</p>
          </div>
        </div>
        {#if seoResult.signals?.length > 0}
          <div class="grid grid-cols-2 gap-1">
            {#each seoResult.signals.slice(0, 4) as signal}
              {@const c = signal.score >= 80 ? '#10b981' : signal.score >= 60 ? '#3b82f6' : signal.score >= 40 ? '#f59e0b' : '#ef4444'}
              <div class="flex items-center gap-1.5">
                <span class="text-[7px] text-white/30 uppercase truncate w-16">{signal.label.replace(/_/g,' ')}</span>
                <div class="flex-1 h-0.5 rounded-full bg-white/5 overflow-hidden">
                  <div class="h-full rounded-full" style="width:{signal.score}%;background:{c}"></div>
                </div>
                <span class="text-[7px] font-black" style="color:{c}">{signal.score}</span>
              </div>
            {/each}
          </div>
        {/if}
        {#if seoResult.quick_wins?.length > 0}
          <p class="text-[8px] text-blue-300/50">⚡ {seoResult.quick_wins[0]}</p>
        {/if}
      </div>
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">
        Nhấn <span class="text-blue-400/70 font-bold">SEO</span> để chấm điểm 7 tín hiệu SEO.
      </div>
    {/if}

  <!-- ═══════════════════════════════════════════
       AI MOD RESULT
  ════════════════════════════════════════════ -->
  {:else if activeTab === 'ai'}
    {#if aiReadyResult}
      {@const aiPct = aiReadyResult.geo_score}
      {@const aiColor = aiPct >= 85 ? '#a855f7' : aiPct >= 65 ? '#d946ef' : '#ef4444'}
      <div class="px-3 py-2 rounded-xl border flex items-center gap-4"
        style="background: {aiColor}08; border-color: {aiColor}20;">
        <div class="relative w-12 h-12 shrink-0">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="4"/>
            <circle cx="24" cy="24" r="19" fill="none" stroke={aiColor}
              stroke-width="4"
              stroke-dasharray={2 * Math.PI * 19}
              stroke-dashoffset={2 * Math.PI * 19 * (1 - aiPct/100)}
              stroke-linecap="round"
              style="transition:stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)"
            />
          </svg>
          <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black" style="color:{aiColor}">{aiPct}%</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-[9px] font-black uppercase tracking-wider" style="color:{aiColor}">✨ Viral Edge™</span>
            <button onclick={() => runAiAnalysis()} class="text-[8px] text-white/20 hover:text-purple-400 transition-colors" title="Chạy lại">↻</button>
          </div>
          <p class="text-[9px] text-white/50 leading-relaxed line-clamp-2">{aiReadyResult.summary}</p>
        </div>
      </div>
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">
        Nhấn <span class="text-purple-400/70 font-bold">AI MOD</span> để kiểm tra Viral Edge Score.
      </div>
    {/if}
  {/if}

</div>

<style>
  .live-scanner {
    position: relative;
    backdrop-filter: blur(16px);
  }

  .scan-line {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    animation: scan 2.5s linear infinite;
    opacity: 0.6;
  }
  @keyframes scan {
    0%   { top: 0%;   opacity: 0; }
    5%   { opacity: 0.6; }
    95%  { opacity: 0.6; }
    100% { top: 100%; opacity: 0; }
  }

  .progress-shimmer {
    position: relative;
    overflow: hidden;
  }
  .progress-shimmer::after {
    content: '';
    position: absolute;
    top: 0; left: -100%; bottom: 0; width: 60%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 1.2s infinite;
  }
  @keyframes shimmer {
    0%   { left: -100%; }
    100% { left: 200%; }
  }

  .shadow-glow {
    box-shadow: 0 0 6px currentColor;
  }
</style>
