<script lang="ts">
  import { onMount, untrack, tick } from "svelte";
  import { ShieldCheck, BarChart2, Sparkles, Brain } from "lucide-svelte";
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import CheckResultPanel from "./CheckResultPanel.svelte";
  import { purifyAIContent } from "$lib/utils/purify";
  import { resolveMediaUrl, processContentImages } from "$lib/state/utils";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";

  import { apiClient } from "$lib/utils/apiClient";
  import type { EditorAnnotation } from "$lib/types";
  import type {
    MediaAsset,
    CampaignOutline,
    CampaignSection,
    CampaignMetrics,
    AnalysisCache,
    AnalysisAnnotation,
    CopyrightResult,
    SEOResult,
    AIInspectResult
  } from "$lib/state/types";

  interface Props {
    campaign_id: string;
    isEditing: boolean;
    editedDraft: string;
    draft_content: string;
    outline: CampaignOutline;
    assets: (MediaAsset | string)[];
    isExpanded: boolean;
    editorRef?: TiptapEditor | null;
    analysis_cache: AnalysisCache;
    analysis_metrics: CampaignMetrics;
    copyrightScore: number;
    seoScore: number;
    aiScore: number;
    isProcessing?: boolean;
  }

  let {
    campaign_id,
    isEditing,
    editedDraft = $bindable(),
    draft_content = $bindable(),
    outline = {} as CampaignOutline,
    assets = [] as (MediaAsset | string)[],
    isExpanded,
    editorRef = $bindable(),
    analysis_cache = {} as AnalysisCache,
    analysis_metrics = {} as CampaignMetrics,
    copyrightScore = $bindable(),
    seoScore = $bindable(),
    aiScore = $bindable(),
    isProcessing = false
  }: Props = $props();

  // Rule R82.41: Smart Data Mapping
  let displayContent = $derived.by(() => {
    let base = isEditing ? (editedDraft || draft_content) : draft_content;
    if (!base) {
      if (typeof outline === 'string') {
        base = outline;
      } else {
        const sections = outline?.sections || [];
        if (sections.length > 0) {
          base = sections.map((s: CampaignSection) => {
            const hText = (s.heading || "").replace(/^(H2|H3):/i, "").trim();
            const tag = (s.heading || "").toUpperCase().startsWith("H3") ? "h3" : "h2";
            return `<${tag}>${hText}</${tag}><p>${s.content || ""}</p>`;
          }).join("\n");
        }
      }
    }

    // Rule R82.42: Image Placeholder Replacement (Elite V2.2 Unified)
    const currentAssets = xohiImageStore.assets.length > 0 ? xohiImageStore.assets : assets;
    return processContentImages(base, currentAssets);
  });

  // -- Analysis States --
  let copyrightResult = $state<CopyrightResult | null>(null);
  let isCopyrightLoading = $state(false);
  let seoResult = $state<SEOResult | null>(null);
  let isSeoLoading = $state(false);
  let aiReadyResult = $state<AIInspectResult | null>(null);
  let isAiLoading = $state(false);
  let isBulkFixing = $state(false);

  // -- Tab Filter State --
  let activeTab = $state<'copyright' | 'seo' | 'ai' | 'enrich' | null>(null);

  // -- Gate Score Derived Values --
  let _copyrightScore = $derived<number | null>(
    copyrightResult ? Math.round(copyrightResult.uniqueness_score * 100) : null
  );
  let _seoScore = $derived<number | null>(
    seoResult ? seoResult.total_score : null
  );
  let _aiScore = $derived<number | null>(
    aiReadyResult ? aiReadyResult.geo_score : null
  );

  // -- Sync local analysis results to parent scores (bindable) --
  $effect(() => { if (_copyrightScore !== null) copyrightScore = _copyrightScore; });
  $effect(() => { if (_seoScore !== null) seoScore = _seoScore; });
  $effect(() => { if (_aiScore !== null) aiScore = _aiScore; });
 
  // -- Time Formatting (Senior Architect V2026) --
  let lastAnalyzedTime = $derived.by(() => {
    const val = analysis_metrics?.last_analyzed;
    if (!val) return null;
    try {
      return new Date(val as string).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return null;
    }
  });

  // -- Gate Conditions --
  let seoLocked = $derived(_copyrightScore === null || _copyrightScore < 90);
  let aiLocked = $derived(_seoScore === null || _seoScore < 70);

  // -- Annotations for editor: CHỈ hiển thị annotations của tab đang active --
  let editorAnnotations = $derived<EditorAnnotation[]>(
    activeTab === 'copyright'
      ? (copyrightResult?.annotations || []).map((s: AnalysisAnnotation) => ({
          text: s.text || '',
          type: s.type || 'copyright',
          message: s.reason || 'Cần kiểm tra COPYRIGHT',
          source: s.source_url || '',
          severity: (s.severity || 'medium').toLowerCase()
        }))
      : activeTab === 'seo'
        ? (seoResult?.seo_annotations || []).map((a: AnalysisAnnotation) => ({
            text: a.text || '',
            type: a.type || 'seo-info',
            message: a.message || '',
            severity: (a.severity || 'info').toLowerCase()
          }))
        : activeTab === 'ai'
          ? (aiReadyResult?.ai_annotations || []).map((a: AnalysisAnnotation) => ({
              text: a.text || '',
              type: a.type || 'geo-info',
              message: a.message || '',
              severity: (a.severity || 'info').toLowerCase()
            }))
          : [] // Không có tab active = không highlight gì
  );

  const saveBeforeAnalysis = async () => {
    const currentText = isEditing ? (editedDraft || draft_content) : draft_content;
    if (currentText && campaign_id) {
       try {
         await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, { draft_content: currentText });
       } catch (e) {
         console.warn("[DraftStep] Auto-save before analysis failed:", e);
       }
    }
  };

  onMount(() => {
    // Rule R03: Bindable Safety
    if (editedDraft === undefined) editedDraft = "";
    if (draft_content === undefined) draft_content = "";
    if (copyrightScore === undefined) copyrightScore = 0;
    if (seoScore === undefined) seoScore = 0;
    if (aiScore === undefined) aiScore = 0;

    // Phase 102: Restoration Logic — if metrics exist but result is empty, restore local result
    if (analysis_cache) {
       if (analysis_cache.copyright?.data) {
          copyrightResult = analysis_cache.copyright.data as CopyrightResult;
          activeTab = 'copyright'; // Auto-activate if we have results
       }
       if (analysis_cache.seo?.data) seoResult = analysis_cache.seo.data as SEOResult;
       if (analysis_cache.ai?.data) aiReadyResult = analysis_cache.ai.data as AIInspectResult;
    }
  });
 
  // Auto-scroll to result panel when analysis starts
  let resultPanelEl = $state<HTMLElement | null>(null);
  function scrollToPanel() {
    setTimeout(() => {
      resultPanelEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 50);
  }

  const runCopyrightCheck = async (force: boolean = false) => {
    if (!campaign_id || isCopyrightLoading) return;
    const isForce = force === true;
    isCopyrightLoading = true;
    activeTab = 'copyright'; // Show panel immediately
    scrollToPanel();
    // Phase 114: Don't pre-null — keep old result visible while loading
    copyrightScore = null;
    try {
      await saveBeforeAnalysis();
      const res = await apiClient.post<{ data: CopyrightResult }>(`/api/v1/content/campaigns/${campaign_id}/analyze/copyright?force=${isForce}`);
      if (res?.data) copyrightResult = res.data;
    } catch (e) {
      console.error("[DraftStep] COPYRIGHT check failed:", e);
    } finally {
      isCopyrightLoading = false;
      activeTab = 'copyright';
    }
  };
 
  const runSeoAnalysis = async (force: boolean = false) => {
    if (!campaign_id || isSeoLoading || seoLocked) return;
    const isForce = force === true;
    isSeoLoading = true;
    activeTab = 'seo'; // Show panel immediately
    scrollToPanel();
    // Phase 114: Don't pre-null result — keep showing old while loading new
    // Only clear score so score badge shows spinner
    seoScore = null;
    try {
      await saveBeforeAnalysis();
      const res = await apiClient.post<{ data: SEOResult }>(`/api/v1/content/campaigns/${campaign_id}/analyze/seo?force=${isForce}`);
      if (res?.data) {
        seoResult = res.data; // Atomic update: replaces old result in one tick
      }
    } catch (e) {
      console.error("[DraftStep] SEO analysis failed:", e);
    } finally {
      isSeoLoading = false;
      activeTab = 'seo';
    }
  };

  const runAiAnalysis = async (force: boolean = false) => {
    if (!campaign_id || isAiLoading || aiLocked) return;
    const isForce = force === true;
    isAiLoading = true;
    activeTab = 'ai'; // Show panel immediately
    scrollToPanel();
    // Phase 114: Don't pre-null result
    aiScore = null;
    try {
      await saveBeforeAnalysis();
      const res = await apiClient.post<{ data: AIInspectResult }>(`/api/v1/content/campaigns/${campaign_id}/analyze/ai-inspect?force=${isForce}`);
      if (res?.data) {
        aiReadyResult = res.data;
      }
    } catch (e) {
      console.error("[DraftStep] AI Inspect failed:", e);
    } finally {
      isAiLoading = false;
      activeTab = 'ai';
    }
  };

  const handleTabClick = (tab: 'copyright' | 'seo' | 'ai') => {
    if (tab === 'seo' && seoLocked) return;
    if (tab === 'ai' && aiLocked) return;
    // Rule: Clicking an already active tab does NOT toggle it off (to avoid hiding buttons)
    activeTab = tab;
  };

  const runAutoFix = async (targetSnippet: string, annotationType: string, errorMessage: string): Promise<string | null> => {
    if (!campaign_id) return null;
    try {
      const res = await apiClient.post<{ status: string; data: { new_text: string } }>(`/api/v1/content/campaigns/${campaign_id}/analyze/auto-fix`, {
        target_snippet: targetSnippet,
        annotation_type: annotationType,
        error_message: errorMessage,
      });
      const payload = res?.status === 'success' ? res.data : null;
      if (payload?.new_text) {
        const new_text = payload.new_text;
        setTimeout(() => {
          const normTarget = targetSnippet.replace(/[\s\*\u200B\uFEFF]+/g, '').toLowerCase();
          const updateMatches = (a: AnalysisAnnotation) => {
            if (!a || typeof a.text !== 'string') return false;
            const normText = a.text.replace(/[\s\*\u200B\uFEFF]+/g, '').toLowerCase();
            const msgMatch = (a.message === errorMessage || a.reason === errorMessage);
            const typeMatch = (a.type === annotationType);
            return (normText.includes(normTarget) || normTarget.includes(normText)) && msgMatch && typeMatch;
          };
          if (seoResult?.seo_annotations) {
            seoResult.seo_annotations = seoResult.seo_annotations.map((a: AnalysisAnnotation) =>
              updateMatches(a) ? { ...a, text: new_text, type: 'fixed' } : a
            );
          }
          if (aiReadyResult?.ai_annotations) {
            aiReadyResult.ai_annotations = aiReadyResult.ai_annotations.map((a: AnalysisAnnotation) =>
              updateMatches(a) ? { ...a, text: new_text, type: 'fixed' } : a
            );
          }
          if (copyrightResult?.annotations) {
            copyrightResult.annotations = copyrightResult.annotations.map((s: AnalysisAnnotation) => {
              const isMatch = updateMatches(s);
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

  const runBulkFix = async () => {
    if (!campaign_id || isBulkFixing || !activeTab || editorAnnotations.length === 0) return;
    isBulkFixing = true;
    try {
      // Deduplicate and gather annotations to send
      let category = '';
      let annotationsToSend: AnalysisAnnotation[] = [];
      if (activeTab === 'copyright') {
        category = 'copyright';
        annotationsToSend = copyrightResult?.annotations || [];
      } else if (activeTab === 'seo') {
        category = 'seo';
        annotationsToSend = seoResult?.seo_annotations || [];
      } else if (activeTab === 'ai') {
        category = 'ai';
        annotationsToSend = aiReadyResult?.ai_annotations || [];
      }

      if (annotationsToSend.length === 0) return;

      const res = await apiClient.post<{ status: string; data: { new_content: string } }>(`/api/v1/content/campaigns/${campaign_id}/analyze/bulk-fix`, {
        category: category,
        annotations: annotationsToSend
      });

      if (res?.status === 'success' && res.data?.new_content) {
        // AI returned entirely new content
        const newHtml = res.data.new_content;

        // Save to DB first
        await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, { 
          draft_content: newHtml
        });

        // Update local buffer
        if (isEditing) {
            editedDraft = newHtml;
        } else {
            draft_content = newHtml;
        }

        // Phase 114: Wait for editor to re-render new content before re-analysis
        // This ensures annotation posMap is built against the new doc structure
        await tick();
        await new Promise(resolve => setTimeout(resolve, 200));

        // Re-analysis with force=true (saveBeforeAnalysis skipped — already saved above)
        if (activeTab === 'copyright') {
          await runCopyrightCheck(true);
        } else if (activeTab === 'seo') {
          await runSeoAnalysis(true);
        } else if (activeTab === 'ai') {
          await runAiAnalysis(true);
        }
      }
    } catch (e) {
      console.error('[DraftStep] Bulk Fix failed:', e);
    } finally {
      isBulkFixing = false;
    }
  };

  // ── AI BOOSTER (Phase 115) ─────────────────────────────────
  let isBoosting = $state(false);

  const runAiBooster = async () => {
    if (!campaign_id || isBoosting || !seoResult) return;
    isBoosting = true;
    activeTab = 'enrich'; 
    scrollToPanel();

    try {
      // 1. Double check db is synced
      await saveBeforeAnalysis();

      // 2. Call the new enrich endpoint
      const res = await apiClient.post<{ status: string; data: { new_content: string } }>(`/api/v1/content/campaigns/${campaign_id}/analyze/enrich`);

      if (res?.status === 'success' && res.data?.new_content) {
        const newHtml = res.data.new_content;

        // 3. Update UI
        if (isEditing) {
            editedDraft = newHtml;
        } else {
            draft_content = newHtml;
        }

        // 4. Wait for editor to re-render
        await tick();
        await new Promise(resolve => setTimeout(resolve, 200));

        // 5. Automatically re-check SEO to show the new score
        activeTab = 'seo';
        seoResult = null; // Clear it to force loading UI
        await runSeoAnalysis(true);
      }
    } catch (e) {
      console.error('[DraftStep] AI Booster failed:', e);
    } finally {
      isBoosting = false;
    }
  };

  // Expert Optimizer (V71.30): Hydrate detailed results from cache with reactive sync
  $effect(() => {
    if (analysis_cache) {
      untrack(() => {
        // Phase 112: Use content hash to ensure we only hydrate IF the result matches the current text
        // For now, we trust the cache update from the parent (nanobot sync)
        if (analysis_cache.copyright?.data) copyrightResult = analysis_cache.copyright.data as CopyrightResult;
        if (analysis_cache.seo?.data) seoResult = analysis_cache.seo.data as SEOResult;
        if (analysis_cache.ai?.data) aiReadyResult = analysis_cache.ai.data as AIInspectResult;
        
        // Auto-activate tab if we have data but no active tab
        if (!activeTab) {
          if (copyrightResult) activeTab = 'copyright';
          else if (seoResult) activeTab = 'seo';
          else if (aiReadyResult) activeTab = 'ai';
        }
      });
    }
  });

  $effect(() => {
    if (isEditing && !editedDraft) {
      const fallback = displayContent;
      if (fallback) editedDraft = fallback;
    }
  });

  // Badge helpers - Elite Optimization (Phase 11)
  const copyrightBadge = $derived(
    _copyrightScore !== null ? `${_copyrightScore}%` : null
  );
  const seoBadge = $derived(
    seoResult ? `${seoResult.grade}.${seoResult.total_score}` : null
  );
  const aiBadge = $derived(
    _aiScore !== null ? `${_aiScore}%` : null
  );
</script>

<div class="p-5 md:p-8 space-y-4 flex flex-col">
  <!-- Studio Label -->
  <div class="flex items-center gap-3 shrink-0">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">
      XOHI ·
      <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">NEURAL STUDIO</span>
    </h5>
    {#if _copyrightScore !== null}
      {@const rc = _copyrightScore >= 90 ? 'text-emerald-400' : _copyrightScore >= 70 ? 'text-yellow-400' : 'text-red-400'}
      <span class="text-[9px] font-black uppercase {rc}">· Copyright {_copyrightScore}%</span>
    {/if}
    {#if seoResult}
      {@const gc = seoResult.grade === 'A' ? 'text-emerald-400' : seoResult.grade === 'B' ? 'text-blue-400' : seoResult.grade === 'C' ? 'text-yellow-400' : 'text-red-400'}
      <span class="text-[9px] font-black uppercase {gc}">· SEO {seoResult.grade} ({seoResult.total_score}/100)</span>
    {/if}
    {#if _aiScore !== null}
      {@const ac = _aiScore >= 85 ? 'text-purple-400' : _aiScore >= 65 ? 'text-fuchsia-400' : 'text-red-400'}
      <span class="text-[9px] font-black uppercase {ac}">· AI {_aiScore}%</span>
    {/if}
    {#if lastAnalyzedTime}
      <span class="text-[8px] font-medium text-white/20 ml-auto">
        Lân cuối: {lastAnalyzedTime}
      </span>
    {/if}
  </div>

  <!-- Editor -->
  <div class="flex flex-col relative transition-all duration-500 {isEditing ? 'border border-white/5 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8)] bg-[#09090b]/40 backdrop-blur-2xl' : 'bg-transparent'}">
    {#if isProcessing && !displayContent}
      <div class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950/60 backdrop-blur-md animate-in fade-in duration-700">
        <div class="relative">
          <div class="w-20 h-20 rounded-full border-t-2 border-r-2 border-purple-500/40 animate-spin"></div>
          <div class="absolute inset-0 m-auto w-12 h-12 bg-purple-500/10 rounded-full blur-xl animate-pulse"></div>
        </div>
        <div class="mt-8 flex flex-col items-center gap-2">
          <span class="text-[10px] font-black uppercase tracking-[0.3em] text-purple-400/80 animate-pulse">AI đang chấp bút bản thảo</span>
          <div class="flex gap-1">
             <div class="w-1 h-1 rounded-full bg-purple-500/40 animate-bounce" style="animation-delay: 0s"></div>
             <div class="w-1 h-1 rounded-full bg-purple-500/40 animate-bounce" style="animation-delay: 0.1s"></div>
             <div class="w-1 h-1 rounded-full bg-purple-500/40 animate-bounce" style="animation-delay: 0.2s"></div>
          </div>
        </div>
      </div>
    {/if}
    <TiptapEditor
      bind:this={editorRef}
      content={displayContent}
      assets={assets}
      onChange={(val) => {
        if (isEditing && val !== editedDraft) {
          editedDraft = val;
        }
      }}
      editable={isEditing}
      placeholder="AI đang chấp bút bản thảo..."
      fullScreen={isExpanded}
      toolbarActions={[
        {
          label: isCopyrightLoading ? '...' : '🔍 COPYRIGHT',
          loading: isCopyrightLoading,
          onclick: () => runCopyrightCheck(true)
        },
        {
          label: isSeoLoading ? '...' : '📊 SEO',
          loading: isSeoLoading,
          disabled: seoLocked,
          lockedMsg: seoLocked
            ? `🔒 SEO bị khoá — Cần COPYRIGHT ≥ 90 trước (hiện: ${_copyrightScore !== null ? _copyrightScore + '%' : 'chưa check'})`
            : undefined,
          onclick: () => runSeoAnalysis(true)
        },
        {
          label: isAiLoading ? '...' : '✨ AI MOD',
          loading: isAiLoading,
          disabled: aiLocked,
          lockedMsg: aiLocked
            ? `🔒 AI MOD bị khoá — Cần SEO ≥ 70 trước (hiện: ${_seoScore !== null ? _seoScore + '/100' : 'chưa check'})`
            : undefined,
          onclick: () => runAiAnalysis(true)
        },
        // AI BOOSTER Action — Hiển thị khi SEO chưa đạt 95đ
        ...(seoResult && seoResult.total_score < 95 ? [{
          label: isBoosting ? '🚀 ENRICHING...' : '🚀 AI BOOSTER',
          loading: isBoosting,
          onclick: runAiBooster,
          tooltipDetails: {
            title: 'AI Booster™',
            description: 'Tự động cấy số liệu thực tế, câu quote từ chuyên gia và bảng so sánh để ép bài viết vượt mức 95 điểm SEO.',
            icon: Brain,
            colorClass: 'text-pink-400'
          }
        }] : []),
        // Bulk Fix Action: Viral 2026 — Show if results exist, even if highlighting is brittle
        ...(activeTab && activeTab !== 'enrich' && (
          (activeTab === 'copyright' && (copyrightResult?.annotations || []).filter(a => a.type !== 'fixed').length > 0) ||
          (activeTab === 'seo' && (seoResult?.seo_annotations || []).filter(a => a.type !== 'fixed').length > 0) ||
          (activeTab === 'ai' && (aiReadyResult?.ai_annotations || []).filter(a => a.type !== 'fixed').length > 0)
        ) ? [{
          label: isBulkFixing ? '✨ ĐANG PHẪU THUẬT...' : `✨ SỬA TOÀN BỘ (${
            activeTab === 'copyright' ? (copyrightResult?.annotations || []).filter(a => a.type !== 'fixed').length :
            activeTab === 'seo' ? (seoResult?.seo_annotations || []).filter(a => a.type !== 'fixed').length :
            (aiReadyResult?.ai_annotations || []).filter(a => a.type !== 'fixed').length
          } LỖI ${activeTab.toUpperCase()})`,
          loading: isBulkFixing,
          onclick: runBulkFix
        }] : [])
      ]}
      annotations={editorAnnotations}
      onfix={runAutoFix}
      campaignId={campaign_id}
    />
  </div>

  <!-- Check Tab Buttons + Result Panel -->
  <div class="shrink-0 flex flex-col gap-2">
    <!-- 3 Tab Buttons -->
    <div class="flex items-center gap-2">

      <!-- COPYRIGHT -->
      <div class="relative group/cr">
        <button
          onclick={() => {
            if (!copyrightResult && !isCopyrightLoading) {
              runCopyrightCheck();
            } else {
              handleTabClick('copyright');
            }
          }}
          disabled={isCopyrightLoading}
          class="group relative flex items-center gap-1.5 px-3 py-1.5 transition-all
            {activeTab === 'copyright'
              ? 'bg-orange-500/15 border border-orange-500/40 text-orange-300'
              : 'bg-black/40 border border-white/10 text-white/60 hover:bg-white/5'}
            disabled:opacity-50"
        >
          {#if isCopyrightLoading}
            <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
          {:else}
            <ShieldCheck size={12} />
          {/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">COPYRIGHT</span>
          {#if copyrightBadge}
            {@const badgeColor = (_copyrightScore ?? 0) >= 90 ? 'bg-emerald-500/20 text-emerald-400' : (_copyrightScore ?? 0) >= 70 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}
            <span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {badgeColor}">{copyrightBadge}</span>
          {/if}
        </button>
        <!-- Criteria Tooltip -->
        <div class="criteria-tooltip opacity-0 group-hover/cr:opacity-100 pointer-events-none group-hover/cr:pointer-events-auto absolute bottom-full left-0 mb-2 w-72 bg-gradient-to-br from-orange-950/95 via-slate-950/95 to-slate-900/95 backdrop-blur-2xl border border-orange-500/20 shadow-2xl shadow-orange-500/5 p-4 z-50 transition-all duration-300 translate-y-2 group-hover/cr:translate-y-0">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-6 h-6 rounded-md bg-orange-500/20 flex items-center justify-center"><ShieldCheck size={12} class="text-orange-400" /></div>
            <span class="text-[10px] font-black uppercase tracking-[0.15em] text-orange-400">Plagiarism Cop™</span>
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
      </div>

      <!-- SEO -->
      <div class="relative group/seo">
        <button
          onclick={() => {
            if (!seoResult && !isSeoLoading && !seoLocked) {
              runSeoAnalysis();
            } else {
              handleTabClick('seo');
            }
          }}
          disabled={isSeoLoading || seoLocked}
          class="flex items-center gap-1.5 px-3 py-1.5 transition-all
            {activeTab === 'seo'
              ? 'bg-blue-500/15 border border-blue-500/40 text-blue-300'
              : 'bg-black/40 border border-white/10 text-white/60 hover:bg-white/5'}
            {seoLocked ? 'cursor-not-allowed opacity-50' : ''}
            disabled:opacity-50"
        >
          {#if isSeoLoading}
            <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
          {:else}
            <BarChart2 size={12} />
          {/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">SEO</span>
          {#if seoLocked}
            <span class="text-[8px] opacity-50">🔒</span>
          {:else if seoBadge}
            {@const gc = seoResult?.grade === 'A' ? 'bg-emerald-500/20 text-emerald-400' : seoResult?.grade === 'B' ? 'bg-blue-500/20 text-blue-400' : 'bg-yellow-500/20 text-yellow-400'}
            <span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {gc}">{seoBadge}</span>
          {/if}
        </button>
        <!-- Criteria / Locked Tooltip -->
        <div class="criteria-tooltip opacity-0 group-hover/seo:opacity-100 pointer-events-none group-hover/seo:pointer-events-auto absolute bottom-full left-0 mb-2 w-80 bg-gradient-to-br from-blue-950/95 via-slate-950/95 to-slate-900/95 backdrop-blur-2xl border border-blue-500/20 shadow-2xl shadow-blue-500/5 p-4 z-50 transition-all duration-300 translate-y-2 group-hover/seo:translate-y-0">
          {#if seoLocked}
            <div class="text-[9px] text-orange-400 font-bold">⚠️ Cần COPYRIGHT ≥ 90% trước ({_copyrightScore !== null ? `hiện: ${_copyrightScore}%` : 'chưa kiểm tra'})</div>
            <div class="h-px bg-white/5 my-2"></div>
          {/if}
          <div class="flex items-center gap-2 mb-3">
            <div class="w-6 h-6 rounded-md bg-blue-500/20 flex items-center justify-center"><BarChart2 size={12} class="text-blue-400" /></div>
            <span class="text-[10px] font-black uppercase tracking-[0.15em] text-blue-400">SEO Strategist™</span>
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
      </div>

      <!-- AI MOD -->
      <div class="relative group/ai">
        <button
          onclick={() => {
            if (!aiReadyResult && !isAiLoading && !aiLocked) {
              runAiAnalysis();
            } else {
              handleTabClick('ai');
            }
          }}
          disabled={isAiLoading || aiLocked}
          class="flex items-center gap-1.5 px-3 py-1.5 transition-all
            {activeTab === 'ai'
              ? 'bg-purple-500/15 border border-purple-500/40 text-purple-300'
              : 'bg-black/40 border border-white/10 text-white/60 hover:bg-white/5'}
            {aiLocked ? 'cursor-not-allowed opacity-50' : ''}
            disabled:opacity-50"
        >
          {#if isAiLoading}
            <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
          {:else}
            <Sparkles size={12} />
          {/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">AI MOD</span>
          {#if aiLocked}
            <span class="text-[8px] opacity-50">🔒</span>
          {:else if aiBadge}
            {@const ac = (_aiScore ?? 0) >= 85 ? 'bg-purple-500/20 text-purple-400' : (_aiScore ?? 0) >= 65 ? 'bg-fuchsia-500/20 text-fuchsia-400' : 'bg-red-500/20 text-red-400'}
            <span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {ac}">{aiBadge}</span>
          {/if}
        </button>
        <!-- Criteria / Locked Tooltip -->
        <div class="criteria-tooltip opacity-0 group-hover/ai:opacity-100 pointer-events-none group-hover/ai:pointer-events-auto absolute bottom-full right-0 mb-2 w-[340px] bg-gradient-to-br from-purple-950/95 via-slate-950/95 to-fuchsia-950/95 backdrop-blur-2xl border border-purple-500/20 shadow-2xl shadow-purple-500/10 p-4 z-50 transition-all duration-300 translate-y-2 group-hover/ai:translate-y-0">
          {#if aiLocked}
            <div class="text-[9px] text-blue-400 font-bold">⚠️ Cần SEO ≥ 70 trước ({_seoScore !== null ? `hiện: ${_seoScore}/100` : 'chưa kiểm tra'})</div>
            <div class="h-px bg-white/5 my-2"></div>
          {/if}
          <div class="flex items-center gap-2 mb-3">
            <div class="w-6 h-6 rounded-md bg-purple-500/20 flex items-center justify-center"><Sparkles size={12} class="text-purple-400" /></div>
            <div>
              <span class="text-[10px] font-black uppercase tracking-[0.15em] text-purple-400">Viral Edge™</span>
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
      </div>

    </div>

    <!-- Result Panel (controlled by activeTab) -->
    {#if activeTab !== null}
      <div bind:this={resultPanelEl} class="max-h-52 overflow-y-auto custom-scrollbar">
        <CheckResultPanel
          {activeTab}
          {copyrightResult}
          {isCopyrightLoading}
          {seoResult}
          {isSeoLoading}
          {aiReadyResult}
          {isAiLoading}
          {isBoosting}
          {runCopyrightCheck}
          {runSeoAnalysis}
          {runAiAnalysis}
          {runAiBooster}
          onfix={runAutoFix}
        />
      </div>
    {/if}
  </div>
</div>

<style>
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59,130,246,0.1); border-radius: 0; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) { background: rgba(59,130,246,0.6); }

  @keyframes shimmer { 0% { opacity: 0.3; } 50% { opacity: 0.7; } 100% { opacity: 0.3; } }
  .animate-pulse { animation: shimmer 2s infinite ease-in-out; }
</style>
