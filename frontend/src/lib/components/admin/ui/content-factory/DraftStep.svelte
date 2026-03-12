<script lang="ts">
  import { onMount, untrack } from "svelte";
  import {
    FileText,
    ShieldCheck,
    BarChart2,
    Sparkles
  } from "lucide-svelte";
  import RichTextEditor from "../RichTextEditor.svelte";

  import { apiClient } from "$lib/utils/apiClient";
  import type { EditorAnnotation } from "$lib/types";

  let { 
    campaign_id,
    isEditing, 
    editedDraft = $bindable(""), 
    draft_content = $bindable(""), 
    outline = {},
    assets,
    isExpanded,
    editorRef = $bindable(null),
    analysis_cache = {},
    analysis_metrics = {}
  } = $props();

  // Rule R82.41: Smart Data Mapping — Map structured sections to editor content if draft is empty
  let displayContent = $derived.by(() => {
    // Priority 1: Use draft_content if viewing or editedDraft if editing and NOT empty
    let base = isEditing ? (editedDraft || draft_content) : draft_content;
    
    // Fallback: Convert structured outline to readable string (Phase 28 fallback)
    if (!base) {
        const sections = outline?.sections || [];
        if (sections.length > 0) {
          base = sections.map((s: any) => {
            const hText = (s.heading || "").replace(/^(H2|H3):/i, "").trim();
            const tag = (s.heading || "").toUpperCase().startsWith("H3") ? "h3" : "h2";
            return `<${tag}>${hText}</${tag}><p>${s.content || ""}</p>`;
          }).join("\n");
        }
    }

    // Ultra-Resilience (V70.0): Ensure [IMAGE_N] are replaced on frontend too
    if (base && base.includes("[IMAGE_")) {
      const assetList = Array.isArray(assets) ? assets : [];
      assetList.forEach((url, i) => {
        const placeholder = `[IMAGE_${i + 1}]`;
        
        // Match 1: Placeholder inside an existing img src (e.g., from new backend format)
        const srcPattern = new RegExp(`src=["']\\s*${placeholder.replace('[', '\\[').replace(']', '\\]')}\\s*["']`, 'g');
        if (base.includes(placeholder) && srcPattern.test(base)) {
            base = base.replace(srcPattern, `src="${url}"`);
        }

        // Match 2: Bare placeholder or placeholder inside figure (original fallback)
        const figurePattern = new RegExp(`(<figure[^>]*>\\s*)?\\[IMAGE_${i + 1}\\](\\s*<\\/figure>)?`, 'g');
        base = base.replace(figurePattern, `<figure class="content-image"><img src="${url}" alt="content image" loading="lazy" /></figure>`);
      });
      // Safety: strip any broken placeholders
      base = base.replace(/\[IMAGE_\d+\]/g, "");
    }

    return base || "";
  });

  // -- Analysis States --
  let copyrightResult = $state<any>(null);
  let isCopyrightLoading = $state(false);
  let seoResult = $state<any>(null);
  let isSeoLoading = $state(false);
  let aiReadyResult = $state<any>(null);
  let isAiLoading = $state(false);

  // -- Computed Editor Annotations --
  let editorAnnotations = $derived<EditorAnnotation[]>([
    ...((copyrightResult?.annotations || []).map((s: any) => ({
      text: s.text || '',
      type: s.type || 'copyright',
      message: s.reason || 'Cần kiểm tra bản quyền',
      source: s.source_url || '',
      severity: (s.severity || 'medium').toLowerCase()
    }))),
    ...((seoResult?.seo_annotations || []).map((a: any) => ({
      text: a.text || '',
      type: a.type || 'seo-info',
      message: a.message || '',
      severity: (a.severity || 'info').toLowerCase()
    }))),
    ...((aiReadyResult?.ai_annotations || []).map((a: any) => ({
      text: a.text || '',
      type: a.type || 'geo-info',
      message: a.message || '',
      severity: (a.severity || 'info').toLowerCase()
    })))
  ]);

  const runCopyrightCheck = async () => {
    if (!campaign_id || isCopyrightLoading) return;
    isCopyrightLoading = true;
    copyrightResult = null;
    try {
      const res = await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/copyright`);
      if (res?.data) copyrightResult = res.data;
    } catch (e) {
      console.error("[DraftStep] Copyright check failed:", e);
    } finally {
      isCopyrightLoading = false;
    }
  };

  const runSeoAnalysis = async () => {
    if (!campaign_id || isSeoLoading) return;
    isSeoLoading = true;
    seoResult = null;
    try {
      const res = await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/seo`);
      if (res?.data) seoResult = res.data;
    } catch (e) {
      console.error("[DraftStep] SEO analysis failed:", e);
    } finally {
      isSeoLoading = false;
    }
  };

  const runAiAnalysis = async () => {
    if (!campaign_id || isAiLoading) return;
    isAiLoading = true;
    aiReadyResult = null;
    try {
      const res = await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/ai-inspect`);
      if (res?.data) aiReadyResult = res.data;
    } catch (e) {
      console.error("[DraftStep] AI Inspect failed:", e);
    } finally {
      isAiLoading = false;
    }
  };

  const runAutoFix = async (targetSnippet: string, annotationType: string, errorMessage: string): Promise<string | null> => {
    if (!campaign_id) return null;
    try {
      const res = (await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/auto-fix`, {
        target_snippet: targetSnippet,
        annotation_type: annotationType,
        error_message: errorMessage,
      })) as any;
      
      const payload = res?.status === 'success' ? res.data : null;
      if (payload?.new_text) {
        const new_text = payload.new_text;
        setTimeout(() => {
          const normTarget = targetSnippet.replace(/[\s\*\u200B\uFEFF]+/g, '').toLowerCase();
          const updateMatches = (text: string) => {
            if (typeof text !== 'string') return false;
            return text.replace(/[\s\*\u200B\uFEFF]+/g, '').toLowerCase() === normTarget;
          };

          if (seoResult?.seo_annotations) {
            seoResult.seo_annotations = seoResult.seo_annotations.map((a: any) => 
              updateMatches(a.text) ? { ...a, text: new_text, type: 'fixed' } : a
            );
          }
          if (aiReadyResult?.ai_annotations) {
            aiReadyResult.ai_annotations = aiReadyResult.ai_annotations.map((a: any) => 
              updateMatches(a.text) ? { ...a, text: new_text, type: 'fixed' } : a
            );
          }
          if (copyrightResult?.annotations) {
            copyrightResult.annotations = copyrightResult.annotations.map((s: any) => {
              const isMatch = updateMatches(s.text);
              return isMatch ? { ...s, text: new_text, type: 'fixed' } : s;
            });
          }
        }, 100);
        return new_text;
      }
    } catch (e) {
      console.error('[DraftStep] Auto-Fix failed:', e);
    }
    return null;
  };

  // Expert Optimizer (V71.30): Analysis Hydration from DB Cache
  $effect(() => {
    // untrack analysis states to avoid infinite loops if results are reactive
    untrack(() => {
      if (analysis_cache) {
        if (analysis_cache.copyright && !copyrightResult) {
          copyrightResult = analysis_cache.copyright.data;
        }
        if (analysis_cache.seo && !seoResult) {
          seoResult = analysis_cache.seo.data;
        }
        if (analysis_cache.ai_inspect && !aiReadyResult) {
          aiReadyResult = analysis_cache.ai_inspect.data;
        }
      }
    });
  });

  // Ensure editedDraft is initialized when entering edit mode if it was empty
  $effect(() => {
    if (isEditing && !editedDraft) {
      const fallback = displayContent;
      if (fallback) editedDraft = fallback;
    }
  });
</script>

<div class="flex-1 overflow-hidden flex flex-col gap-3">
  <!-- Studio Label -->
  <div class="flex items-center gap-3 shrink-0">
    <div class="w-8 h-px bg-gradient-to-r from-transparent to-purple-500/50"></div>
    <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-purple-400">Content Studio 2026</h5>
    {#if copyrightResult}
      {@const rc = copyrightResult.risk_level === 'LOW' ? 'text-emerald-400' : copyrightResult.risk_level === 'MEDIUM' ? 'text-yellow-400' : 'text-red-400'}
      <span class="text-[9px] font-black uppercase {rc}">
        · Copyright {Math.round(copyrightResult.uniqueness_score * 100)}%
      </span>
    {/if}
    {#if seoResult}
      {@const gc = seoResult.grade === 'A' ? 'text-emerald-400' : seoResult.grade === 'B' ? 'text-blue-400' : seoResult.grade === 'C' ? 'text-yellow-400' : 'text-red-400'}
      <span class="text-[9px] font-black uppercase {gc}">
        · SEO {seoResult.grade} ({seoResult.total_score}/100)
      </span>
    {/if}
    {#if aiReadyResult}
      {@const ac = aiReadyResult.geo_score >= 85 ? 'text-purple-400' : aiReadyResult.geo_score >= 65 ? 'text-fuchsia-400' : 'text-red-400'}
      <span class="text-[9px] font-black uppercase {ac}">
        · AI {aiReadyResult.geo_score}%
      </span>
    {/if}
    {#if analysis_metrics?.last_analyzed}
      <span class="text-[8px] font-medium text-white/20 ml-auto">
        Lân cuối: {new Date(analysis_metrics.last_analyzed).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
      </span>
    {/if}
  </div>

  <!-- Editor (always visible, Copyright/SEO buttons injected into toolbar) -->
  <div class="flex-1 rounded-2xl flex flex-col relative transition-all overflow-hidden min-h-0 {isEditing ? 'border border-white/10 shadow-2xl ring-2 ring-purple-500/30 bg-black/40' : 'bg-transparent'}">
    <RichTextEditor
      bind:this={editorRef}
      content={displayContent}
      assets={assets}
      onChange={(val) => {
        if (isEditing) editedDraft = val;
        else draft_content = val;
      }}
      editable={isEditing}
      placeholder="AI đang chấp bút bản thảo..."
      fullScreen={isExpanded}
      toolbarActions={[
        { label: isCopyrightLoading ? '...' : '🔍 Bản Quyền', loading: isCopyrightLoading, onclick: runCopyrightCheck },
        { label: isSeoLoading ? '...' : '📊 SEO', loading: isSeoLoading, onclick: runSeoAnalysis },
        { label: isAiLoading ? '...' : '✨ AI 2026', loading: isAiLoading, onclick: runAiAnalysis }
      ]}
      annotations={editorAnnotations}
      onfix={runAutoFix}
    />
  </div>

  <!-- Analysis Results (compact, scrollable, below editor) -->
  {#if copyrightResult || isCopyrightLoading || seoResult || isSeoLoading || aiReadyResult || isAiLoading}
    <div class="shrink-0 max-h-52 overflow-y-auto custom-scrollbar flex flex-col gap-2">
      
      <div class="flex items-center gap-2">
          <button 
            onclick={runCopyrightCheck}
            disabled={isCopyrightLoading}
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black/40 border {copyrightResult ? 'border-green-500/30 text-green-400' : 'border-white/10 text-white/60'} hover:bg-white/5 transition-colors disabled:opacity-50"
          >
            {#if isCopyrightLoading}
              <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
            {:else}
              <ShieldCheck size={12} />
            {/if}
            <span class="text-[10px] uppercase font-bold tracking-wider">Bản quyền</span>
          </button>

          <button 
            onclick={runSeoAnalysis}
            disabled={isSeoLoading}
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black/40 border {seoResult ? 'border-blue-500/30 text-blue-400' : 'border-white/10 text-white/60'} hover:bg-white/5 transition-colors disabled:opacity-50"
          >
            {#if isSeoLoading}
              <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
            {:else}
              <BarChart2 size={12} />
            {/if}
            <span class="text-[10px] uppercase font-bold tracking-wider">SEO</span>
          </button>

          <button 
            onclick={runAiAnalysis}
            disabled={isAiLoading}
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black/40 border {aiReadyResult ? 'border-purple-500/30 text-purple-400' : 'border-white/10 text-white/60'} hover:bg-white/5 transition-colors disabled:opacity-50"
            title="Kiểm tra mức độ thân thiện với LLM/AI Crawlers"
          >
            {#if isAiLoading}
              <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
            {:else}
              <Sparkles size={12} />
            {/if}
            <span class="text-[10px] uppercase font-bold tracking-wider">AI 2026</span>
          </button>
      </div>

      <!-- Copyright Result -->
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
          <!-- Mini circular gauge -->
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
              <button onclick={runCopyrightCheck} class="text-[8px] text-white/20 hover:text-orange-400 transition-colors">↻</button>
            </div>
            <p class="text-[9px] text-white/50 leading-relaxed truncate">{copyrightResult.verdict}</p>
            {#if copyrightResult.flagged_sentences?.length > 0}
              <p class="text-[8px] text-orange-400/60 mt-0.5">⚠️ {copyrightResult.flagged_sentences.length} đoạn có rủi ro</p>
              <div class="mt-1 flex flex-col gap-0.5">
                {#each copyrightResult.flagged_sentences.slice(0, 3) as sentence}
                  {@const snippetKey = typeof sentence === 'string' ? sentence : (sentence.text || '')}
                  <p class="text-[8px] text-white/30 truncate">• "{snippetKey.slice(0, 50)}..."</p>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      {/if}

      <!-- SEO Result -->
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
                <button onclick={runSeoAnalysis} class="text-[8px] text-white/20 hover:text-blue-400 transition-colors">↻</button>
              </div>
              <p class="text-[9px] text-white/50 leading-relaxed line-clamp-2">{seoResult.summary}</p>
            </div>
          </div>
          <!-- Mini signal bars -->
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
      {/if}

      <!-- AI Readiness Result -->
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
          <!-- Mini circular gauge -->
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
              <span class="text-[9px] font-black uppercase tracking-wider" style="color:{aiColor}">
                ✨ AI Readiness
              </span>
              <button onclick={runAiAnalysis} class="text-[8px] text-white/20 hover:text-purple-400 transition-colors">↻</button>
            </div>
            <p class="text-[9px] text-white/50 leading-relaxed line-clamp-2">{aiReadyResult.summary}</p>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>
