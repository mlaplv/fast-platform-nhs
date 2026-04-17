import { apiClient } from "$lib/utils/apiClient";
import { useNanobot } from "./nanobot.svelte";
import { tick, untrack } from "svelte";
import { xohiActions, cleanHtmlContent } from "./xohiActions";
import type {
    CopyrightResult,
    SEOResult,
    AIInspectResult,
    AnalysisCache,
    CampaignMetrics,
    AnalysisAnnotation,
    GenericResponse,
    CampaignData,
    BulkFixReplacement
} from "$lib/state/types";

export function createAnalysisController(config: {
    campaign_id?: string | null | (() => string | null | undefined);
    getContent?: () => string;
    topic?: string;
    isEditing: boolean | (() => boolean);
    getEditedDraft: () => string;
    getDraftContent: () => string;
    setEditedDraft: (v: string) => void;
    setDraftContent: (v: string) => void;
    analysis_cache: AnalysisCache | (() => AnalysisCache);
    analysis_metrics: CampaignMetrics | (() => CampaignMetrics);
    getIsProcessing?: () => boolean;
}) {
    const nanobot = useNanobot();
    const resolve = <T>(val: T | (() => T)): T => (typeof val === 'function' ? (val as () => T)() : val);

    const isAdhoc = $derived(!resolve(config.campaign_id));
    let copyrightResult = $state<CopyrightResult | null>(null);
    let isCopyrightLoading = $state(false);
    let seoResult = $state<SEOResult | null>(null);
    let isSeoLoading = $state(false);
    let aiReadyResult = $state<AIInspectResult | null>(null);
    let isAiLoading = $state(false);
    let isBulkFixing = $state(false);
    let bulkFixStatus = $state("");
    let bulkFixLogs = $state<string[]>([]);
    let isBoosting = $state(false);
    let activeTab = $state<'copyright' | 'seo' | 'ai' | 'enrich' | null>(null);

    // Sync Pulse logs
    $effect(() => {
        const data = nanobot.currentData as CampaignData;
        const campaignId = resolve(config.campaign_id);
        const msg = data?.progress_msg ?? '';
        if (!data || !campaignId || (data.campaign_id !== campaignId && data.id !== campaignId) || !msg) return;

        untrack(() => {
            if (config.getIsProcessing?.() || isBulkFixing) {
                if (!bulkFixLogs.some(l => l.includes(msg) || msg.includes(l))) {
                    bulkFixLogs = [...bulkFixLogs, msg];
                    if (!bulkFixStatus) bulkFixStatus = "Đang xử lý...";
                }
            }
        });
    });

    let copyrightScore = $derived(copyrightResult ? Math.round(copyrightResult.uniqueness_score * 100) : null);
    let seoScore = $derived(seoResult ? seoResult.total_score : null);
    let aiScore = $derived(aiReadyResult ? aiReadyResult.geo_score : null);
    let seoLocked = $derived(copyrightScore === null || copyrightScore < 55);
    let aiLocked = $derived(seoScore === null || seoScore < 40);

    let editorAnnotations = $derived.by(() => {
        const res = (activeTab === 'copyright' ? copyrightResult?.annotations : 
                     activeTab === 'seo' ? seoResult?.seo_annotations : 
                     activeTab === 'ai' ? aiReadyResult?.ai_annotations : []) || [];
        return res.map((s: AnalysisAnnotation) => ({
            text: s.text || '',
            type: s.type || (activeTab === 'seo' ? 'seo-info' : activeTab === 'ai' ? 'geo-info' : 'copyright'),
            message: s.reason || s.message || 'Cần kiểm tra',
            source: s.source_url || '',
            severity: (s.severity || 'medium').toLowerCase()
        }));
    });

    async function saveBeforeAnalysis() {
        if (isAdhoc) return;
        const cid = resolve(config.campaign_id);
        if (!cid) return;
        const currentText = resolve(config.isEditing) ? config.getEditedDraft() : config.getDraftContent();
        await apiClient.patch(`/api/v1/content/campaigns/${cid}`, { draft_content: currentText });
    }

    async function handleApiResponse<T>(res: GenericResponse<T>, targetSetter: (v: T) => void) {
        if (res?.status === "accepted" && (res.data as any)?.task_id) {
            return 'accepted';
        } else if (res?.data) {
            if (res.logs) bulkFixLogs = [...bulkFixLogs, ...(res.logs.filter(l => !bulkFixLogs.includes(l)))];
            targetSetter(res.data);
            return 'success';
        }
        return 'error';
    }

    async function runCopyrightCheck(force = false, skipSave = false) {
        if (isCopyrightLoading) return;
        isCopyrightLoading = true; isBulkFixing = true; bulkFixStatus = "Đang quét..."; activeTab = 'copyright';
        let isAccepted = false;
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const cid = resolve(config.campaign_id);
            const url = isAdhoc ? `/api/v1/content/analyze/copyright?force=${force}` : `/api/v1/content/campaigns/${cid}/analyze/copyright?force=${force}`;
            const body = isAdhoc ? { content: (config.getContent ?? config.getEditedDraft)() } : undefined;
            const res = await apiClient.post<GenericResponse<CopyrightResult>>(url, body);
            const status = await handleApiResponse(res, (v) => { copyrightResult = v; });
            if (status === 'accepted') isAccepted = true;
        } finally {
            if (!isAccepted) {
                isCopyrightLoading = false;
                setTimeout(() => { if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) isBulkFixing = false; }, 3000);
                setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3200);
            }
        }
    }

    async function runSeoAnalysis(force = false, skipSave = false) {
        if (isSeoLoading) return;
        isSeoLoading = true; isBulkFixing = true; bulkFixStatus = "Đang quét SEO..."; activeTab = 'seo';
        let isAccepted = false;
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const cid = resolve(config.campaign_id);
            const url = isAdhoc ? `/api/v1/content/analyze/seo?force=${force}` : `/api/v1/content/campaigns/${cid}/analyze/seo?force=${force}`;
            const body = isAdhoc ? { content: (config.getContent ?? config.getEditedDraft)(), topic: resolve(config.topic) || '' } : undefined;
            const res = await apiClient.post<GenericResponse<SEOResult>>(url, body);
            const status = await handleApiResponse(res, (v) => { seoResult = v; });
            if (status === 'accepted') isAccepted = true;
        } finally {
            if (!isAccepted) {
                isSeoLoading = false;
                setTimeout(() => { if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) isBulkFixing = false; }, 3000);
                setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3200);
            }
        }
    }

    async function runAiAnalysis(force = false, skipSave = false) {
        if (isAiLoading || aiLocked) return;
        isAiLoading = true; isBulkFixing = true; bulkFixStatus = "Đang quét AI MOD..."; activeTab = 'ai';
        bulkFixLogs = ["🔍 Đang khởi động AI MOD...", "🧠 Đang rà soát dấu vân tay AI..."];
        let isAccepted = false;
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const cid = resolve(config.campaign_id);
            const url = isAdhoc ? `/api/v1/content/analyze/ai-inspect?force=${force}` : `/api/v1/content/campaigns/${cid}/analyze/ai-inspect?force=${force}`;
            const body = isAdhoc ? { content: (config.getContent ?? config.getEditedDraft)() } : undefined;
            const res = await apiClient.post<GenericResponse<AIInspectResult>>(url, body);
            const status = await handleApiResponse(res, (v) => { 
                const oldFixed = (aiReadyResult?.ai_annotations || []).filter(a => a.type === 'fixed-area');
                v.ai_annotations = [...oldFixed, ...(v.ai_annotations || [])];
                aiReadyResult = v;
            });
            if (status === 'accepted') isAccepted = true;
        } finally {
            if (!isAccepted) {
                isAiLoading = false;
                setTimeout(() => { if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) isBulkFixing = false; }, 3000);
                setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3200);
            }
        }
    }

    async function runCleanContent() {
        if (isCopyrightLoading || isSeoLoading || isAiLoading) return null;
        isBulkFixing = true; bulkFixStatus = "Đang dọn dẹp...";
        bulkFixLogs = ["🧹 Đang khởi động Neural Clean...", "🧠 Đang dọn dẹp artifacts..."];
        try {
            const content = (config.getContent ?? config.getEditedDraft)();
            const cleaned = await xohiActions.runClean(content);
            config.setEditedDraft?.(cleaned);
            bulkFixLogs = [...bulkFixLogs, "🎯 Đã dọn dẹp xong ✅"];
            nanobot.showToast("Đã dọn dẹp & tối ưu cấu trúc thành công!", "success");
            return cleaned;
        } finally {
            setTimeout(() => { if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) isBulkFixing = false; }, 3000);
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3200);
        }
    }

    async function runAutoFix(target: string, type: string, msg: string) {
        const cid = resolve(config.campaign_id);
        if (!cid) return null;
        const newText = await xohiActions.runAutoFix(cid, target, type, msg);
        if (newText) {
            const update = (a: AnalysisAnnotation) => {
                const nt = target.replace(/[\s\*\u200B\uFEFF]+/g, '').toLowerCase();
                const na = (a.text || '').replace(/[\s\*\u200B\uFEFF]+/g, '').toLowerCase();
                return (na.includes(nt) || nt.includes(na)) && (a.message === msg || a.reason === msg) && a.type === type;
            };
            if (seoResult) seoResult.seo_annotations = (seoResult.seo_annotations || []).filter(a => !update(a));
            if (aiReadyResult) aiReadyResult.ai_annotations = (aiReadyResult.ai_annotations || []).filter(a => !update(a));
            if (copyrightResult) copyrightResult.annotations = (copyrightResult.annotations || []).filter(a => !update(a));
        }
        return newText;
    }

    async function runBulkFix() {
        if (isBulkFixing || !activeTab) return;
        const cid = resolve(config.campaign_id);
        const category = activeTab === 'copyright' ? 'copyright' : activeTab === 'seo' ? 'seo' : 'ai';
        const annotations = (activeTab === 'copyright' ? copyrightResult?.annotations : activeTab === 'seo' ? seoResult?.seo_annotations : aiReadyResult?.ai_annotations) || [];
        if (annotations.length === 0) return;

        isBulkFixing = true; bulkFixStatus = "Đang phẫu thuật...";
        bulkFixLogs = ["Đang khởi tạo Neural Engine...", "Đang phân tích cấu trúc..."];
        try {
            const payload = isAdhoc ? { content: (config.getContent ?? config.getEditedDraft)(), topic: resolve(config.topic), category, annotations } : { category, annotations };
            const res = await xohiActions.runBulkFix(cid || null, isAdhoc, payload);
            if (res?.status === 'success' && res.data?.new_content) {
                if (res.logs) bulkFixLogs = [...bulkFixLogs, ...res.logs];
                const newHtml = res.data.new_content;
                const replacements = res.data.replacements || [];
                if (!isAdhoc && cid) await apiClient.patch(`/api/v1/content/campaigns/${cid}`, { draft_content: newHtml });
                if (resolve(config.isEditing)) config.setEditedDraft(newHtml);
                else config.setDraftContent(newHtml);
                
                await tick();
                const fixed: AnalysisAnnotation[] = [];
                const remaining: AnalysisAnnotation[] = [];
                for (const a of annotations) {
                    const normT = (a.text || '').normalize('NFC').replace(/[^\p{L}\p{N}]/gu, '').toLowerCase();
                    const rep = replacements.find(r => r.old_text.normalize('NFC').replace(/[^\p{L}\p{N}]/gu, '').toLowerCase() === normT);
                    if (rep) fixed.push({ text: rep.new_text, reason: '✅ Đã sửa', message: '✅ Đã sửa', severity: 'low', type: 'fixed-area' });
                    else remaining.push({ ...a, message: `[CHƯA SỬA] ${a.message || a.reason}` });
                }
                if (activeTab === 'copyright') copyrightResult = { ...copyrightResult!, annotations: [...fixed, ...remaining] };
                else if (activeTab === 'seo') seoResult = { ...seoResult!, seo_annotations: [...fixed, ...remaining] };
                else aiReadyResult = { ...aiReadyResult!, ai_annotations: [...fixed, ...remaining] };
            }
        } finally {
            isBulkFixing = false;
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3000);
        }
    }

    async function runAiBooster() {
        const cid = resolve(config.campaign_id);
        if (isAdhoc || !cid || isBoosting || !seoResult) return;
        isBoosting = true; isBulkFixing = true; bulkFixStatus = "Đang Booster...";
        bulkFixLogs = ["🚀 Đang khởi động Neural Booster™...", "🧠 Đang trinh sát dữ liệu..."];
        try {
            await saveBeforeAnalysis();
            const res = await xohiActions.runEnrich(cid);
            if (res?.status === 'success' && res.data?.new_content) {
                if (res.logs) bulkFixLogs = [...bulkFixLogs, ...res.logs];
                config.setEditedDraft(res.data.new_content);
                if (res.data.annotations?.length) {
                    const ann = res.data.annotations;
                    if (!seoResult) seoResult = { total_score: 0, grade: 'N/A', signals: [], summary: '', quick_wins: [], seo_annotations: ann, logs: [] };
                    else seoResult.seo_annotations = [...(seoResult.seo_annotations || []), ...ann];
                }
                activeTab = 'seo';
                await runSeoAnalysis(true, true);
            }
        } finally {
            isBoosting = false;
            setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; bulkFixLogs = []; }, 3500);
        }
    }

    // Hydrate
    $effect(() => {
        const cache = resolve(config.analysis_cache);
        if (cache && Object.keys(cache).length > 0) {
            untrack(() => {
                if (cache.copyright?.data && !copyrightResult) {
                     copyrightResult = cache.copyright.data as CopyrightResult;
                     if (isCopyrightLoading) { isCopyrightLoading = false; setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; }, 1000); }
                }
                if (cache.seo?.data && !seoResult) {
                     seoResult = cache.seo.data as SEOResult;
                     if (isSeoLoading) { isSeoLoading = false; setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; }, 1000); }
                }
                if (cache.ai_inspect?.data && !aiReadyResult) {
                     aiReadyResult = cache.ai_inspect.data as AIInspectResult;
                     if (isAiLoading) { isAiLoading = false; setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; }, 1000); }
                }
            });
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
        get bulkFixStatus() { return bulkFixStatus; },
        get bulkFixLogs() { return bulkFixLogs; },
        get isBoosting() { return isBoosting; },
        get activeTab() { return activeTab; },
        set activeTab(v) { activeTab = v; },
        get copyrightScore() { return copyrightScore; },
        get seoScore() { return seoScore; },
        get aiScore() { return aiScore; },
        get seoLocked() { return seoLocked; },
        get aiLocked() { return aiLocked; },
        get editorAnnotations() { return editorAnnotations; },
        runCopyrightCheck, runSeoAnalysis, runAiAnalysis, runAutoFix, runCleanContent, runBulkFix, runAiBooster, dispose: () => {
            copyrightResult = null; seoResult = null; aiReadyResult = null; bulkFixLogs = []; bulkFixStatus = ""; activeTab = null;
        }
    };
}
