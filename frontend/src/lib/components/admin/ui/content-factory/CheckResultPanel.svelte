<script lang="ts">
  import { ShieldCheck, BarChart2, Sparkles } from "lucide-svelte";
  import type { CopyrightResult, SEOResult, AIInspectResult, AnalysisAnnotation } from "$lib/state/types";

  let {
    activeTab,
    copyrightResult,
    isCopyrightLoading,
    seoResult,
    isSeoLoading,
    aiReadyResult,
    isAiLoading,
    runCopyrightCheck,
    runSeoAnalysis,
    runAiAnalysis,
    onfix = null
  }: {
    activeTab: 'copyright' | 'seo' | 'ai' | null;
    copyrightResult: CopyrightResult | null;
    isCopyrightLoading: boolean;
    seoResult: SEOResult | null;
    isSeoLoading: boolean;
    aiReadyResult: AIInspectResult | null;
    isAiLoading: boolean;
    runCopyrightCheck: () => void;
    runSeoAnalysis: () => void;
    runAiAnalysis: () => void;
    onfix?: ((snippet: string, type: string, message: string) => Promise<string | null>) | null;
  } = $props();

  let isFixing = $state<string | null>(null);

  async function handleInternalFix(snippet: string, type: string, message: string) {
    if (!onfix || isFixing) return;
    isFixing = snippet;
    try {
      await onfix(snippet, type, message);
    } finally {
      isFixing = null;
    }
  }
</script>

<div class="shrink-0 flex flex-col gap-2">

  <!-- Copyright Panel -->
  {#if activeTab === 'copyright'}
    {#if isCopyrightLoading}
      <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-orange-500/5 border border-orange-500/10 text-[9px] text-orange-400/70 animate-pulse">
        <span class="inline-block w-2.5 h-2.5 border border-orange-400/40 border-t-transparent rounded-full animate-spin"></span>
        Google Search → Gemini AI đang phân tích đạo văn...
      </div>
    {:else if copyrightResult}
      {@const pct = Math.round(copyrightResult.uniqueness_score * 100)}
      {@const riskColor = copyrightResult.risk_level === 'LOW' ? '#10b981' : copyrightResult.risk_level === 'MEDIUM' ? '#f59e0b' : '#ef4444'}
      <div class="px-3 py-2 rounded-xl border flex items-center gap-4"
        style="background: {riskColor}08; border-color: {riskColor}20;"
      >
        <div class="relative w-12 h-12 shrink-0">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="4"/>
            <circle cx="24" cy="24" r="19" fill="none" stroke={riskColor}
              stroke-width="4"
              stroke-dasharray={2 * Math.PI * 19}
              stroke-dashoffset={2 * Math.PI * 19 * (1 - copyrightResult.uniqueness_score)}
              stroke-linecap="round"
              style="transition:stroke-dashoffset 1s ease"
            />
          </svg>
          <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black" style="color:{riskColor}">{pct}%</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-[9px] font-black uppercase" style="color:{riskColor}">
              🔍 Bản quyền — {copyrightResult.risk_level === 'LOW' ? 'Rủi ro thấp ✅' : copyrightResult.risk_level === 'MEDIUM' ? 'Cần cải thiện ⚠️' : 'Rủi ro cao 🚨'}
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
                     style="border-color: {annHex}20"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="flex items-center gap-1.5">
                      <span class="text-[7px] font-black px-1 py-0.5 rounded uppercase"
                        style="background: {annHex}20; color: {annHex}">
                        {isInternal ? '🔁 TRÙNG LẶP NỘI BỘ' : `🚨 BẢN QUYỀN ${ann.severity?.toUpperCase()}`}
                      </span>
                    </div>

                    <button
                      onclick={() => handleInternalFix(ann.text, ann.type || 'copyright', ann.reason || 'Cần kiểm tra bản quyền')}
                      disabled={!!isFixing}
                      class="shrink-0 flex items-center gap-1 px-2 py-0.5 rounded border border-white/10 hover:bg-white/10 text-[7px] font-black uppercase transition-all disabled:opacity-40"
                    >
                      {#if isFixing === ann.text}
                        <span class="w-2 h-2 border border-white/30 border-t-white rounded-full animate-spin"></span>
                        FIXING...
                      {:else if ann.type === 'fixed'}
                        <ShieldCheck size={8} class="text-emerald-400" />
                        ĐÃ SỬA
                      {:else}
                        <Sparkles size={8} class="text-yellow-400" />
                        SỬA LỖI
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
        Nhấn <span class="text-orange-400/70 font-bold">Bản Quyền</span> để phân tích đạo văn.
      </div>
    {/if}
  {/if}

  <!-- SEO Panel -->
  {#if activeTab === 'seo'}
    {#if isSeoLoading}
      <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-500/5 border border-blue-500/10 text-[9px] text-blue-400/70 animate-pulse">
        <span class="inline-block w-2.5 h-2.5 border border-blue-400/40 border-t-transparent rounded-full animate-spin"></span>
        Gemini AI đang chấm điểm 7 tín hiệu SEO 2026...
      </div>
    {:else if seoResult}
      {@const gradeColor = seoResult.grade === 'A' ? '#10b981' : seoResult.grade === 'B' ? '#3b82f6' : seoResult.grade === 'C' ? '#f59e0b' : '#ef4444'}
      <div class="px-3 py-2 rounded-xl border flex flex-col gap-2"
        style="background: {gradeColor}08; border-color: {gradeColor}20;"
      >
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
        Nhấn <span class="text-blue-400/70 font-bold">SEO</span> để chấm điểm 7 tín hiệu SEO 2026.
      </div>
    {/if}
  {/if}

  <!-- AI 2026 Panel -->
  {#if activeTab === 'ai'}
    {#if isAiLoading}
      <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-500/5 border border-purple-500/10 text-[9px] text-purple-400/70 animate-pulse">
        <span class="inline-block w-2.5 h-2.5 border border-purple-400/40 border-t-transparent rounded-full animate-spin"></span>
        Gemini AI đang phân tích mức độ thân thiện với LLM Crawler...
      </div>
    {:else if aiReadyResult}
      {@const aiPct = aiReadyResult.geo_score}
      {@const aiColor = aiPct >= 85 ? '#a855f7' : aiPct >= 65 ? '#d946ef' : '#ef4444'}
      <div class="px-3 py-2 rounded-xl border flex items-center gap-4"
        style="background: {aiColor}08; border-color: {aiColor}20;"
      >
        <div class="relative w-12 h-12 shrink-0">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="4"/>
            <circle cx="24" cy="24" r="19" fill="none" stroke={aiColor}
              stroke-width="4"
              stroke-dasharray={2 * Math.PI * 19}
              stroke-dashoffset={2 * Math.PI * 19 * (1 - aiPct/100)}
              stroke-linecap="round"
              style="transition:stroke-dashoffset 1s ease"
            />
          </svg>
          <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black" style="color:{aiColor}">{aiPct}%</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-[9px] font-black uppercase tracking-wider" style="color:{aiColor}">✨ AI Readiness</span>
            <button onclick={() => runAiAnalysis()} class="text-[8px] text-white/20 hover:text-purple-400 transition-colors" title="Chạy lại">↻</button>
          </div>
          <p class="text-[9px] text-white/50 leading-relaxed line-clamp-2">{aiReadyResult.summary}</p>
        </div>
      </div>
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">
        Nhấn <span class="text-purple-400/70 font-bold">AI 2026</span> để kiểm tra mức độ thân thiện với AI Crawler.
      </div>
    {/if}
  {/if}

</div>
