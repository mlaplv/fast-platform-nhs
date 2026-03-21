import { apiClient } from "$lib/utils/apiClient";
import { tick } from "svelte";
import type {
    CopyrightResult,
    SEOResult,
    AIInspectResult,
    AnalysisCache,
    CampaignMetrics,
    AnalysisAnnotation,
    EditorAnnotation
} from "$lib/state/types";

export function createAnalysisController(config: {
    campaign_id: string;
    isEditing: boolean;
    getEditedDraft: () => string;
    getDraftContent: () => string;
    setEditedDraft: (v: string) => void;
    setDraftContent: (v: string) => void;
    analysis_cache: AnalysisCache;
    analysis_metrics: CampaignMetrics;
}) {
    let copyrightResult = $state<CopyrightResult | null>(null);
    let isCopyrightLoading = $state(false);
    let seoResult = $state<SEOResult | null>(null);
    let isSeoLoading = $state(false);
    let aiReadyResult = $state<AIInspectResult | null>(null);
    let isAiLoading = $state(false);
    let isBulkFixing = $state(false);
    let isBoosting = $state(false);
    let activeTab = $state<'copyright' | 'seo' | 'ai' | 'enrich' | null>(null);

    // Derived scores
    let copyrightScore = $derived(copyrightResult ? Math.round(copyrightResult.uniqueness_score * 100) : null);
    let seoScore = $derived(seoResult ? seoResult.total_score : null);
    let aiScore = $derived(aiReadyResult ? aiReadyResult.geo_score : null);

    // Gate conditions
    let seoLocked = $derived(copyrightScore === null || copyrightScore < 90);
    let aiLocked = $derived(seoScore === null || seoScore < 70);

    // Derived annotations for editor
    let editorAnnotations = $derived.by(() => {
        if (activeTab === 'copyright') {
            return (copyrightResult?.annotations || []).map((s: AnalysisAnnotation) => ({
                text: s.text || '',
                type: s.type || 'copyright',
                message: s.reason || 'Cần kiểm tra COPYRIGHT',
                source: s.source_url || '',
                severity: (s.severity || 'medium').toLowerCase()
            }));
        }
        if (activeTab === 'seo') {
            return (seoResult?.seo_annotations || []).map((a: AnalysisAnnotation) => ({
                text: a.text || '',
                type: a.type || 'seo-info',
                message: a.message || '',
                severity: (a.severity || 'info').toLowerCase()
            }));
        }
        if (activeTab === 'ai') {
            return (aiReadyResult?.ai_annotations || []).map((a: AnalysisAnnotation) => ({
                text: a.text || '',
                type: a.type || 'geo-info',
                message: a.message || '',
                severity: (a.severity || 'info').toLowerCase()
            }));
        }
        return [];
    });

    async function saveBeforeAnalysis() {
        const currentText = config.isEditing ? config.getEditedDraft() : config.getDraftContent();
        if (currentText && config.campaign_id) {
            try {
                await apiClient.patch(`/api/v1/content/campaigns/${config.campaign_id}`, { draft_content: currentText });
            } catch (e) {
                console.warn("[AnalysisController] Auto-save failed:", e);
            }
        }
    }

    async function runCopyrightCheck(force: boolean = false) {
        if (!config.campaign_id || isCopyrightLoading) return;
        isCopyrightLoading = true;
        activeTab = 'copyright';
        try {
            await saveBeforeAnalysis();
            const res = await apiClient.post<{ data: CopyrightResult }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/copyright?force=${force}`);
            if (res?.data) copyrightResult = res.data;
        } catch (e) {
            console.error("Copyright check failed:", e);
        } finally {
            isCopyrightLoading = false;
        }
    }

    async function runSeoAnalysis(force: boolean = false) {
        if (!config.campaign_id || isSeoLoading || seoLocked) return;
        isSeoLoading = true;
        activeTab = 'seo';
        try {
            await saveBeforeAnalysis();
            const res = await apiClient.post<{ data: SEOResult }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/seo?force=${force}`);
            if (res?.data) seoResult = res.data;
        } catch (e) {
            console.error("SEO analysis failed:", e);
        } finally {
            isSeoLoading = false;
        }
    }

    async function runAiAnalysis(force: boolean = false) {
        if (!config.campaign_id || isAiLoading || aiLocked) return;
        isAiLoading = true;
        activeTab = 'ai';
        try {
            await saveBeforeAnalysis();
            const res = await apiClient.post<{ data: AIInspectResult }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/ai-inspect?force=${force}`);
            if (res?.data) aiReadyResult = res.data;
        } catch (e) {
            console.error("AI Inspect failed:", e);
        } finally {
            isAiLoading = false;
        }
    }

    async function runAutoFix(targetSnippet: string, annotationType: string, errorMessage: string): Promise<string | null> {
        if (!config.campaign_id) return null;
        try {
            const res = await apiClient.post<{ status: string; data: { new_text: string } }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/auto-fix`, {
                target_snippet: targetSnippet,
                annotation_type: annotationType,
                error_message: errorMessage,
            });
            const payload = res?.status === 'success' ? res.data : null;
            if (payload?.new_text) {
                const new_text = payload.new_text;
                // Update results locally for immediate feedback
                const updateMatches = (a: AnalysisAnnotation) => {
                    const normTarget = targetSnippet.replace(/[\s\*\u200B\uFEFF]+/g, '').toLowerCase();
                    const normText = (a.text || '').replace(/[\s\*\u200B\uFEFF]+/g, '').toLowerCase();
                    const msgMatch = (a.message === errorMessage || a.reason === errorMessage);
                    return (normText.includes(normTarget) || normTarget.includes(normText)) && msgMatch && a.type === annotationType;
                };

                if (seoResult?.seo_annotations) {
                    seoResult.seo_annotations = seoResult.seo_annotations.map(a => updateMatches(a) ? { ...a, text: new_text, type: 'fixed' } : a);
                }
                if (aiReadyResult?.ai_annotations) {
                    aiReadyResult.ai_annotations = aiReadyResult.ai_annotations.map(a => updateMatches(a) ? { ...a, text: new_text, type: 'fixed' } : a);
                }
                if (copyrightResult?.annotations) {
                    copyrightResult.annotations = copyrightResult.annotations.map(a => updateMatches(a) ? { ...a, text: new_text, type: 'fixed' } : a);
                }
                return new_text;
            }
        } catch (e) {
            console.error('Auto-Fix failed:', e);
        }
        return null;
    }

    async function runBulkFix() {
        if (!config.campaign_id || isBulkFixing || !activeTab) return;
        isBulkFixing = true;
        try {
            let category = '';
            let annotationsToSend: AnalysisAnnotation[] = [];
            if (activeTab === 'copyright') { category = 'copyright'; annotationsToSend = copyrightResult?.annotations || []; }
            else if (activeTab === 'seo') { category = 'seo'; annotationsToSend = seoResult?.seo_annotations || []; }
            else if (activeTab === 'ai') { category = 'ai'; annotationsToSend = aiReadyResult?.ai_annotations || []; }

            if (annotationsToSend.length === 0) return;

            const res = await apiClient.post<{ status: string; data: { new_content: string } }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/bulk-fix`, {
                category: category,
                annotations: annotationsToSend
            });

            if (res?.status === 'success' && res.data?.new_content) {
                const newHtml = res.data.new_content;
                await apiClient.patch(`/api/v1/content/campaigns/${config.campaign_id}`, { draft_content: newHtml });
                if (config.isEditing) config.setEditedDraft(newHtml);
                else config.setDraftContent(newHtml);

                await tick();
                await new Promise(resolve => setTimeout(resolve, 200));

                if (activeTab === 'copyright') await runCopyrightCheck(true);
                else if (activeTab === 'seo') await runSeoAnalysis(true);
                else if (activeTab === 'ai') await runAiAnalysis(true);
            }
        } catch (e) {
            console.error('Bulk Fix failed:', e);
        } finally {
            isBulkFixing = false;
        }
    }

    async function runAiBooster() {
        if (!config.campaign_id || isBoosting || !seoResult) return;
        isBoosting = true;
        activeTab = 'enrich';
        try {
            await saveBeforeAnalysis();
            const res = await apiClient.post<{ status: string; data: { new_content: string } }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/enrich`);
            if (res?.status === 'success' && res.data?.new_content) {
                const newHtml = res.data.new_content;
                if (config.isEditing) config.setEditedDraft(newHtml);
                else config.setDraftContent(newHtml);
                await tick();
                await new Promise(resolve => setTimeout(resolve, 200));
                activeTab = 'seo';
                await runSeoAnalysis(true);
            }
        } catch (e) {
            console.error('AI Booster failed:', e);
        } finally {
            isBoosting = false;
        }
    }

    // Hydrate from cache
    $effect(() => {
        const cache = config.analysis_cache;
        if (cache) {
            if (cache.copyright?.data) copyrightResult = cache.copyright.data as CopyrightResult;
            if (cache.seo?.data) seoResult = cache.seo.data as SEOResult;
            if (cache.ai_inspect?.data) aiReadyResult = cache.ai_inspect.data as AIInspectResult;

            if (!activeTab) {
                if (copyrightResult) activeTab = 'copyright';
                else if (seoResult) activeTab = 'seo';
                else if (aiReadyResult) activeTab = 'ai';
            }
        }
    });

    return {
        get copyrightResult() { return copyrightResult; },
        get isCopyrightLoading() { return isCopyrightLoading; },
        get seoResult() { return seoResult; },
        get isSeoLoading() { return isSeoLoading; },
        get aiReadyResult() { return aiReadyResult; },
        get isAiLoading() { return isAiLoading; },
        get isBulkFixing() { return isBulkFixing; },
        get isBoosting() { return isBoosting; },
        get activeTab() { return activeTab; },
        set activeTab(v) { activeTab = v; },
        get copyrightScore() { return copyrightScore; },
        get seoScore() { return seoScore; },
        get aiScore() { return aiScore; },
        get seoLocked() { return seoLocked; },
        get aiLocked() { return aiLocked; },
        get editorAnnotations() { return editorAnnotations; },
        runCopyrightCheck,
        runSeoAnalysis,
        runAiAnalysis,
        runAutoFix,
        runBulkFix,
        runAiBooster
    };
}
