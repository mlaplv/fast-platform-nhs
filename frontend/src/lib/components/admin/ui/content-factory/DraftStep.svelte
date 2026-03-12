<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { ShieldCheck, BarChart2, Sparkles } from "lucide-svelte";
  import RichTextEditor from "../RichTextEditor.svelte";
  import CheckResultPanel from "./CheckResultPanel.svelte";

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
    analysis_metrics = {},
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
        base = sections.map((s: any) => {
          const hText = (s.heading || "").replace(/^(H2|H3):/i, "").trim();
          const tag = (s.heading || "").toUpperCase().startsWith("H3") ? "h3" : "h2";
          return `<${tag}>${hText}</${tag}><p>${s.content || ""}</p>`;
        }).join("\n");
      }
    }
    if (base && base.includes("[IMAGE_")) {
      const assetList = Array.isArray(assets) ? assets : [];
      assetList.forEach((url, i) => {
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
  let copyrightResult = $state<any>(null);
  let isCopyrightLoading = $state(false);
  let seoResult = $state<any>(null);
  let isSeoLoading = $state(false);
  let aiReadyResult = $state<any>(null);
  let isAiLoading = $state(false);

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
      ? (copyrightResult?.annotations || []).map((s: any) => ({
          text: s.text || '',
          type: s.type || 'copyright',
          message: s.reason || 'Cần kiểm tra bản quyền',
          source: s.source_url || '',
          severity: (s.severity || 'medium').toLowerCase()
        }))
      : activeTab === 'seo'
        ? (seoResult?.seo_annotations || []).map((a: any) => ({
            text: a.text || '',
            type: a.type || 'seo-info',
            message: a.message || '',
            severity: (a.severity || 'info').toLowerCase()
          }))
        : activeTab === 'ai'
          ? (aiReadyResult?.ai_annotations || []).map((a: any) => ({
              text: a.text || '',
              type: a.type || 'geo-info',
              message: a.message || '',
              severity: (a.severity || 'info').toLowerCase()
            }))
          : [] // Không có tab active = không highlight gì
  );

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
      activeTab = 'copyright';
    }
  };

  const runSeoAnalysis = async () => {
    if (!campaign_id || isSeoLoading || seoLocked) return;
    isSeoLoading = true;
    seoResult = null;
    try {
      const res = await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/seo`);
      if (res?.data) seoResult = res.data;
    } catch (e) {
      console.error("[DraftStep] SEO analysis failed:", e);
    } finally {
      isSeoLoading = false;
      activeTab = 'seo';
    }
  };

  const runAiAnalysis = async () => {
    if (!campaign_id || isAiLoading || aiLocked) return;
    isAiLoading = true;
    aiReadyResult = null;
    try {
      const res = await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/ai-inspect`);
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
    activeTab = activeTab === tab ? null : tab;
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
    <div class="w-8 h-px bg-gradient-to-r from-transparent to-purple-500/50"></div>
    <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-purple-400">Content Studio 2026</h5>
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
        {
          label: isCopyrightLoading ? '...' : '🔍 Bản Quyền',
          loading: isCopyrightLoading,
          onclick: runCopyrightCheck
        },
        {
          label: isSeoLoading ? '...' : '📊 SEO',
          loading: isSeoLoading,
          disabled: seoLocked,
          lockedMsg: seoLocked
            ? `🔒 SEO bị khoá — Cần Bản Quyền ≥ 90 trước (hiện: ${_copyrightScore !== null ? _copyrightScore + '%' : 'chưa check'})`
            : undefined,
          onclick: runSeoAnalysis
        },
        {
          label: isAiLoading ? '...' : '✨ AI 2026',
          loading: isAiLoading,
          disabled: aiLocked,
          lockedMsg: aiLocked
            ? `🔒 AI 2026 bị khoá — Cần SEO ≥ 70 trước (hiện: ${_seoScore !== null ? _seoScore + '/100' : 'chưa check'})`
            : undefined,
          onclick: runAiAnalysis
        }
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
        class="group relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all
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
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all
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
          <div class="absolute bottom-full left-0 mb-1.5 px-2 py-1 rounded-lg bg-black/90 border border-white/10 text-[8px] text-orange-400 whitespace-nowrap opacity-0 group-hover/seo:opacity-100 transition-opacity pointer-events-none z-10">
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
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all
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
          <div class="absolute bottom-full left-0 mb-1.5 px-2 py-1 rounded-lg bg-black/90 border border-white/10 text-[8px] text-blue-400 whitespace-nowrap opacity-0 group-hover/ai:opacity-100 transition-opacity pointer-events-none z-10">
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
        />
      </div>
    {/if}
  </div>
</div>

<style>
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59,130,246,0.1); border-radius: 20px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) { background: rgba(59,130,246,0.6); }
</style>
