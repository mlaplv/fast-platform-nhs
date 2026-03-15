<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { ShieldCheck, BarChart2, Sparkles } from "lucide-svelte";
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import CheckResultPanel from "./CheckResultPanel.svelte";

  import { apiClient } from "$lib/utils/apiClient";
  import type {
    EditorAnnotation,
    MediaAsset,
    CampaignOutline,
    CampaignSection,
    CopyrightResult,
    SEOResult,
    AIInspectResult,
    AnalysisAnnotation
  } from "$lib/types";

  let {
    campaign_id,
    isEditing,
    editedDraft = $bindable(""),
    draft_content = $bindable(""),
    outline = {} as CampaignOutline,
    assets = [] as (MediaAsset | string)[],
    isExpanded,
    editorRef = $bindable(null),
    analysis_cache = {} as Record<string, any>,
    analysis_metrics = {} as Record<string, any>,
    copyrightScore = $bindable<number | null>(null),
    seoScore = $bindable<number | null>(null),
    aiScore = $bindable<number | null>(null)
  } = $props();

  // Rule R82.41: Smart Data Mapping
  let displayContent = $derived.by(() => {
    let base = isEditing ? (editedDraft || draft_content) : draft_content;
    if (!base) {
      const sections = outline?.sections || [];
      if (sections.length > 0) {
        base = sections.map((s: CampaignSection) => {
          const hText = (s.heading || "").replace(/^(H2|H3):/i, "").trim();
          const tag = (s.heading || "").toUpperCase().startsWith("H3") ? "h3" : "h2";
          return `<${tag}>${hText}</${tag}><p>${s.content || ""}</p>`;
        }).join("\n");
      }
    }
    if (base && base.includes("[IMAGE_")) {
      const assetList = Array.isArray(assets) ? assets : [];
      assetList.forEach((asset, i) => {
        const url = typeof asset === 'string' ? asset : asset.url;
        const placeholder = `[IMAGE_${i + 1}]`;
        // Surgical replacement: Handle markers inside src first
        const srcPattern = new RegExp(`(src|href)=["']\\s*${placeholder.replace('[', '\\[').replace(']', '\\]')}\\s*["']`, 'g');
        base = base.replace(srcPattern, `$1="${url}"`);

        // Then handle standalone markers (even if wrapped in figure by AI)
        const figurePattern = new RegExp(`(<figure[^>]*>\\s*)?${placeholder.replace('[', '\\[').replace(']', '\\]')}(\\s*<\\/figure>)?`, 'g');
        base = base.replace(figurePattern, `<figure class="content-image"><img src="${url}" alt="content image" loading="lazy" /></figure>`);
      });
      base = base.replace(/\[IMAGE_\d+\]/g, "");
    }
    return base || "";
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
  let activeTab = $state<'copyright' | 'seo' | 'ai' | null>(null);

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

  // -- Sync scores to parent (bindable) --
  $effect(() => { copyrightScore = _copyrightScore; });
  $effect(() => { seoScore = _seoScore; });
  $effect(() => { aiScore = _aiScore; });

  // -- Gate Conditions --
  let seoLocked = $derived(_copyrightScore === null || _copyrightScore < 90);
  let aiLocked = $derived(_seoScore === null || _seoScore < 70);

  // -- Annotations for editor: CHỈ hiển thị annotations của tab đang active --
  let editorAnnotations = $derived<EditorAnnotation[]>(
    activeTab === 'copyright'
      ? (copyrightResult?.annotations || []).map((s: AnalysisAnnotation) => ({
          text: s.text || '',
          type: s.type || 'copyright',
          message: s.reason || 'Cần kiểm tra bản quyền',
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

  const runCopyrightCheck = async (force: boolean = false) => {
    if (!campaign_id || isCopyrightLoading) return;
    const isForce = force === true;
    isCopyrightLoading = true;
    copyrightResult = null;
    try {
      await saveBeforeAnalysis();
      const res = await apiClient.post<{ data: CopyrightResult }>(`/api/v1/content/campaigns/${campaign_id}/analyze/copyright?force=${isForce}`);
      if (res?.data) copyrightResult = res.data;
    } catch (e) {
      console.error("[DraftStep] Copyright check failed:", e);
    } finally {
      isCopyrightLoading = false;
      activeTab = 'copyright';
    }
  };

  const runSeoAnalysis = async (force: boolean = false) => {
    if (!campaign_id || isSeoLoading || seoLocked) return;
    const isForce = force === true;
    isSeoLoading = true;
    seoResult = null;
    try {
      await saveBeforeAnalysis();
      const res = await apiClient.post<{ data: SEOResult }>(`/api/v1/content/campaigns/${campaign_id}/analyze/seo?force=${isForce}`);
      if (res?.data) seoResult = res.data;
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
    aiReadyResult = null;
    try {
      await saveBeforeAnalysis();
      const res = await apiClient.post<{ data: AIInspectResult }>(`/api/v1/content/campaigns/${campaign_id}/analyze/ai-inspect?force=${isForce}`);
      if (res?.data) aiReadyResult = res.data;
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

        // Let the editor reactivity naturally pick it up through editedDraft/draft_content binding
        if (isEditing) {
            editedDraft = newHtml;
        } else {
            draft_content = newHtml;
        }

        // Wait a small tick so Svelte can sync the draft content to the editor before we re-analyze
        await new Promise(r => setTimeout(r, 300));

        // Rerun the analysis with force=true to guarantee fresh scores and highlights!
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

      if (res?.status === 'success' && res.data?.new_content) {
        // AI returned entirely new content
        const newHtml = res.data.new_content;
        
        // Let the editor reactivity naturally pick it up through editedDraft/draft_content binding
        if (isEditing) {
            editedDraft = newHtml;
        } else {
            draft_content = newHtml;
        }
        
        // Wait a small tick so Svelte can sync the draft content to the editor before we re-analyze
        await new Promise(r => setTimeout(r, 300));

        // Rerun the analysis with force=true to guarantee fresh scores and highlights!
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

  // Expert Optimizer (V71.30): Analysis Hydration from DB Cache
  $effect(() => {
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

  $effect(() => {
    if (isEditing && !editedDraft) {
      const fallback = displayContent;
      if (fallback) editedDraft = fallback;
    }
  });

  // Badge helpers
  const copyrightBadge = $derived(
    _copyrightScore !== null ? `${_copyrightScore}%` : null
  );
  const seoBadge = $derived(
    seoResult ? `${seoResult.grade}·${seoResult.total_score}` : null
  );
  const aiBadge = $derived(
    _aiScore !== null ? `${_aiScore}%` : null
  );
</script>

<div class="flex-1 overflow-hidden flex flex-col gap-3">
  <!-- Studio Label -->
  <div class="flex items-center gap-3 shrink-0">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-purple-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-purple-400">Content Studio 2026</h5>
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
    {#if analysis_metrics?.last_analyzed}
      <span class="text-[8px] font-medium text-white/20 ml-auto">
        Lân cuối: {new Date(analysis_metrics.last_analyzed).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
      </span>
    {/if}
  </div>

  <!-- Editor -->
  <div class="flex-1 flex flex-col relative transition-all overflow-hidden min-h-0 {isEditing ? 'border border-white/10 shadow-2xl ring-2 ring-purple-500/30 bg-black/40' : 'bg-transparent'}">
    <TiptapEditor
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
        {
          label: isCopyrightLoading ? '...' : '🔍 Bản Quyền',
          loading: isCopyrightLoading,
          onclick: () => runCopyrightCheck()
        },
        {
          label: isSeoLoading ? '...' : '📊 SEO',
          loading: isSeoLoading,
          disabled: seoLocked,
          lockedMsg: seoLocked
            ? `🔒 SEO bị khoá — Cần Bản Quyền ≥ 90 trước (hiện: ${_copyrightScore !== null ? _copyrightScore + '%' : 'chưa check'})`
            : undefined,
          onclick: () => runSeoAnalysis()
        },
        {
          label: isAiLoading ? '...' : '✨ AI 2026',
          loading: isAiLoading,
          disabled: aiLocked,
          lockedMsg: aiLocked
            ? `🔒 AI 2026 bị khoá — Cần SEO ≥ 70 trước (hiện: ${_seoScore !== null ? _seoScore + '/100' : 'chưa check'})`
            : undefined,
          onclick: () => runAiAnalysis()
        },
        // Bulk Fix Action rendered only IF there's an active tab and errors
        ...(activeTab && editorAnnotations.filter(a => a.type !== 'fixed').length > 0 ? [{
          label: isBulkFixing ? '✨ ĐANG PHẪU THUẬT...' : `✨ SỬA TOÀN BỘ (${editorAnnotations.filter(a => a.type !== 'fixed').length} LỖI ${activeTab.toUpperCase()})`,
          loading: isBulkFixing,
          onclick: runBulkFix
        }] : [])
      ]}
      annotations={editorAnnotations}
      onfix={runAutoFix}
    />
  </div>

  <!-- Check Tab Buttons + Result Panel -->
  <div class="shrink-0 flex flex-col gap-2">
    <!-- 3 Tab Buttons -->
    <div class="flex items-center gap-2">

      <!-- BẢN QUYỀN -->
      <button
        onclick={() => {
          if (activeTab !== 'copyright' && !copyrightResult && !isCopyrightLoading) {
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
        title={null}
      >
        {#if isCopyrightLoading}
          <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
        {:else}
          <ShieldCheck size={12} />
        {/if}
        <span class="text-[10px] uppercase font-bold tracking-wider">Bản Quyền</span>
        {#if copyrightBadge}
          {@const badgeColor = (_copyrightScore ?? 0) >= 90 ? 'bg-emerald-500/20 text-emerald-400' : (_copyrightScore ?? 0) >= 70 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}
          <span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {badgeColor}">{copyrightBadge}</span>
        {/if}
      </button>

      <!-- SEO -->
      <div class="relative group/seo">
        <button
          onclick={() => {
            if (activeTab !== 'seo' && !seoResult && !isSeoLoading && !seoLocked) {
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
        <!-- Tooltip khi locked -->
        {#if seoLocked}
          <div class="absolute bottom-full left-0 mb-1.5 px-2 py-1 bg-black/90 border border-white/10 text-[8px] text-orange-400 whitespace-nowrap opacity-0 group-hover/seo:opacity-100 transition-opacity pointer-events-none z-10">
            ⚠️ Cần Bản Quyền ≥ 90 trước ({_copyrightScore !== null ? `hiện: ${_copyrightScore}%` : 'chưa kiểm tra'})
          </div>
        {/if}
      </div>

      <!-- AI 2026 -->
      <div class="relative group/ai">
        <button
          onclick={() => {
            if (activeTab !== 'ai' && !aiReadyResult && !isAiLoading && !aiLocked) {
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
          title="Kiểm tra mức độ thân thiện với LLM/AI Crawlers"
        >
          {#if isAiLoading}
            <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
          {:else}
            <Sparkles size={12} />
          {/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">AI 2026</span>
          {#if aiLocked}
            <span class="text-[8px] opacity-50">🔒</span>
          {:else if aiBadge}
            {@const ac = (_aiScore ?? 0) >= 85 ? 'bg-purple-500/20 text-purple-400' : (_aiScore ?? 0) >= 65 ? 'bg-fuchsia-500/20 text-fuchsia-400' : 'bg-red-500/20 text-red-400'}
            <span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {ac}">{aiBadge}</span>
          {/if}
        </button>
        <!-- Tooltip khi locked -->
        {#if aiLocked}
          <div class="absolute bottom-full left-0 mb-1.5 px-2 py-1 bg-black/90 border border-white/10 text-[8px] text-blue-400 whitespace-nowrap opacity-0 group-hover/ai:opacity-100 transition-opacity pointer-events-none z-10">
            ⚠️ Cần SEO ≥ 70 trước ({_seoScore !== null ? `hiện: ${_seoScore}/100` : 'chưa kiểm tra'})
          </div>
        {/if}
      </div>

    </div>

    <!-- Result Panel (controlled by activeTab) -->
    {#if activeTab !== null}
      <div class="max-h-52 overflow-y-auto custom-scrollbar">
        <CheckResultPanel
          {activeTab}
          {copyrightResult}
          {isCopyrightLoading}
          {seoResult}
          {isSeoLoading}
          {aiReadyResult}
          {isAiLoading}
          {runCopyrightCheck}
          {runSeoAnalysis}
          {runAiAnalysis}
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
</style>
