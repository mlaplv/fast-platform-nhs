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
    BulkFixReplacement,
    TaskAcceptedResponse
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
    onUpdate?: (cache: AnalysisCache, metrics: CampaignMetrics) => void;
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

    // Sync Pulse logs & Auto-close HUD
    $effect(() => {
        const data = nanobot.currentData as CampaignData;
        const campaignId = resolve(config.campaign_id);
        const msg = data?.progress_msg ?? '';
        
        // Ad-hoc progress routing: If no campaignId, we listen for 'adhoc' signals
        const isMatch = campaignId ? (data?.campaign_id === campaignId || data?.id === campaignId) : (data?.campaign_id === 'adhoc');
        if (!data || !isMatch) return;

        // Auto-close loading state if campaign reaches terminal status (Sync with HUD)
        const isTerminal = campaignId 
            ? (data.status === 'WAITING_FOR_REVIEW' || data.status === 'COMPLETED' || data.status === 'ERROR')
            : (data.status === 'SUCCESS' || data.status === 'ERROR'); // Adhoc signals

        if (isTerminal) {
            untrack(() => {
                isCopyrightLoading = false; isSeoLoading = false; isAiLoading = false;
                setTimeout(() => { 
                    if (isBulkFixing) {
                        isBulkFixing = false; 
                        bulkFixStatus = "Hoàn tất ✅"; 
                        setTimeout(() => { bulkFixStatus = "";  }, 1000);
                    }
                }, 1000);
            });
        }

        if (!msg) return;

        untrack(() => {
            if (config.getIsProcessing?.() || isBulkFixing || isCopyrightLoading || isSeoLoading || isAiLoading) {
                if (!bulkFixLogs.some(l => l.includes(msg) || msg.includes(l))) {
                    bulkFixLogs = [...bulkFixLogs, msg];
                }
                // Always update status to reflect current step, ensuring HUD doesn't feel 'stuck'
                bulkFixStatus = msg;
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
    
    // R110: Sync results back to parent for persistence (Product/Adhoc mode)
    $effect(() => {
        if (!config.onUpdate) return;
        // Trigger on any result change
        const _ = [copyrightResult, seoResult, aiReadyResult];
        
        untrack(() => {
            const cache: AnalysisCache = { ...resolve(config.analysis_cache) };
            const metrics: CampaignMetrics = { ...resolve(config.analysis_metrics) };
            const now = new Date().toISOString();
            const contentHash = 'adhoc';

            if (copyrightResult) {
                cache.copyright = { hash: contentHash, at: now, data: $state.snapshot(copyrightResult) };
                metrics.unique_score = copyrightResult.uniqueness_score;
            }
            if (seoResult) {
                cache.seo = { hash: contentHash, at: now, data: $state.snapshot(seoResult) };
                metrics.seo_score = seoResult.total_score;
            }
            if (aiReadyResult) {
                cache.ai_inspect = { hash: contentHash, at: now, data: $state.snapshot(aiReadyResult) };
                metrics.ai_ready_score = aiReadyResult.geo_score;
            }
            
            config.onUpdate?.(cache, metrics);
        });
    });

    async function saveBeforeAnalysis() {
        if (isAdhoc) return;
        const cid = resolve(config.campaign_id);
        if (!cid) return;
        const currentText = resolve(config.isEditing) ? config.getEditedDraft() : config.getDraftContent();
        await apiClient.patch(`/api/v1/content/campaigns/${cid}`, { draft_content: currentText });
    }

    async function saveAnalysisEvidence(category: string, data: any) {
        try {
            const cid = resolve(config.campaign_id);
            if (!cid || cid === 'adhoc') return;
            await apiClient.post(`/api/v1/content/campaigns/${cid}/metadata`, {
                analysis_evidence: {
                    [category]: {
                        timestamp: new Date().toISOString(),
                        score: category === 'copyright' ? data.uniqueness_score : category === 'seo' ? data.score : data.viral_score,
                        data: data
                    }
                }
            });
            console.log(`[Neural Vault] Evidence saved for ${category}`);
        } catch (e) {
            console.error("[Neural Vault] Failed to save evidence:", e);
        }
    }

    async function handleApiResponse<T>(res: GenericResponse<T | TaskAcceptedResponse>, targetSetter: (v: T) => void, category?: string) {
        if (res?.status === "accepted" && res.data && typeof res.data === 'object' && 'task_id' in res.data) {
            return 'accepted';
        } else if (res?.data) {
            if (res.logs) bulkFixLogs = [...bulkFixLogs, ...(res.logs.filter(l => !bulkFixLogs.includes(l)))];
            targetSetter(res.data as T);
            bulkFixLogs = [...bulkFixLogs, "✅ Phân tích hoàn tất. Đã nạp dữ liệu Intelligence."];
            if (category) await saveAnalysisEvidence(category, res.data);
            return 'success';
        }
        return 'error';
    }

    // CNS V85.5: Neural Thinking Engine
    let thinkingInterval: ReturnType<typeof setInterval> | null = null;
    function startThinkingLogs(type: 'copyright' | 'seo' | 'ai') {
        const pools = {
            copyright: [
                "🔍 Đang truy quét cơ sở dữ liệu Google Search...",
                "⚖️ Đang đối soát với 14 triệu bản ghi News/Blog...",
                "🧠 Gemini đang phân tích cấu trúc ngữ nghĩa (Semantics)...",
                "⚙️ Đang bóc tách các cụm từ trùng lặp tiềm năng...",
                "📊 Đang tính toán chỉ số Uniqueness..."
            ],
            seo: [
                "🚀 Đang nạp bộ quy tắc E-E-A-T v2026...",
                "📊 Đang đánh giá mật độ từ khóa (Density)...",
                "🔍 Đang kiểm tra cấu trúc Semantic Headers (H1-H4)...",
                "📈 Đang so sánh với Top 5 đối thủ cùng Topic...",
                "🤖 AI đang chấm điểm trải nghiệm người dùng (UX Score)..."
            ],
            ai: [
                "🧠 Đang mở cổng Neural Inspection...",
                "⚡ Đang đo lường chỉ số Viral Edge...",
                "🧪 Đang kiểm tra tính 'Con người' của văn bản...",
                "🛡️ Đang quét các mẫu câu bị AI-Purge đào thải...",
                "💎 Đang tối ưu hóa Brand Voice & Tone..."
            ]
        };
        const pool = pools[type];
        let idx = 0;
        thinkingInterval = setInterval(() => {
            if (idx < pool.length && !bulkFixLogs.includes(pool[idx])) {
                bulkFixLogs = [...bulkFixLogs, pool[idx]];
                idx++;
            } else {
                clearInterval(thinkingInterval!);
            }
        }, 1200);
    }
    function stopThinkingLogs() {
        if (thinkingInterval) clearInterval(thinkingInterval);
    }

    async function runCopyrightCheck(force = false, skipSave = false) {
        if (isCopyrightLoading) return;
        if (isAdhoc) nanobot.updateCurrentData({ campaign_id: 'adhoc' });
        isCopyrightLoading = true; isBulkFixing = true; bulkFixStatus = "Đang quét..."; activeTab = 'copyright';
        bulkFixLogs = ["🧠 Đang khởi động Neural Engine...", "🔍 Đang trinh sát dữ liệu..."];
        startThinkingLogs('copyright');
        let isAccepted = false;
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const cid = resolve(config.campaign_id);
            const url = isAdhoc ? `/api/v1/content/analyze/copyright?force=${force}` : `/api/v1/content/campaigns/${cid}/analyze/copyright?force=${force}`;
            const body = isAdhoc ? { 
                content: (config.getContent ?? config.getEditedDraft)(),
                topic: resolve(config.topic) || ''
            } : undefined;
            const res = await apiClient.post<GenericResponse<CopyrightResult>>(url, body);
            const status = await handleApiResponse(res, (v) => { copyrightResult = v; }, 'copyright');
            if (status === 'accepted') isAccepted = true;
        } finally {
            stopThinkingLogs();
            if (!isAccepted) {
                isCopyrightLoading = false;
                bulkFixStatus = "Hoàn tất ✅";
                setTimeout(() => {
                    if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) {
                        isBulkFixing = false;
                        bulkFixStatus = "";
                        // CNS V85.22: Keep logs for review until next run starts
                    }
                }, 1500);
            }
        }
    }

    async function runSeoAnalysis(force = false, skipSave = false) {
        if (isSeoLoading || seoLocked) return;
        if (isAdhoc) nanobot.updateCurrentData({ campaign_id: 'adhoc' });
        isSeoLoading = true; isBulkFixing = true; bulkFixStatus = "Đang phân tích SEO..."; activeTab = 'seo';
        bulkFixLogs = ["🚀 Đang nạp bộ lọc SEO...", "📊 Đang đánh giá tín hiệu..."];
        startThinkingLogs('seo');
        let isAccepted = false;
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const cid = resolve(config.campaign_id);
            const url = isAdhoc ? `/api/v1/content/analyze/seo?force=${force}` : `/api/v1/content/campaigns/${cid}/analyze/seo?force=${force}`;
            const body = isAdhoc ? { content: (config.getContent ?? config.getEditedDraft)(), topic: resolve(config.topic) || '' } : undefined;
            const res = await apiClient.post<GenericResponse<SEOResult>>(url, body);
            const status = await handleApiResponse(res, (v) => { seoResult = v; }, 'seo');
            if (status === 'accepted') isAccepted = true;
        } finally {
            stopThinkingLogs();
            if (!isAccepted) {
                isSeoLoading = false;
                bulkFixStatus = "Hoàn tất ✅";
                setTimeout(() => {
                    if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) {
                        isBulkFixing = false;
                        bulkFixStatus = "";
                        
                    }
                }, 1500);
            }
        }
    }

    async function runAiAnalysis(force = false, skipSave = false) {
        if (isAiLoading || aiLocked) return;
        if (isAdhoc) nanobot.updateCurrentData({ campaign_id: 'adhoc' });
        isAiLoading = true; isBulkFixing = true; bulkFixStatus = "Đang kiểm định AI..."; activeTab = 'ai';
        bulkFixLogs = ["🧠 Đang mở cổng Neural AI...", "⚡ Đang kiểm tra Viral Edge..."];
        startThinkingLogs('ai');
        let isAccepted = false;
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const cid = resolve(config.campaign_id);
            const url = isAdhoc ? `/api/v1/content/analyze/ai-inspect?force=${force}` : `/api/v1/content/campaigns/${cid}/analyze/ai-inspect?force=${force}`;
            const body = isAdhoc ? { 
                content: (config.getContent ?? config.getEditedDraft)(),
                topic: resolve(config.topic) || ''
            } : undefined;
            const res = await apiClient.post<GenericResponse<AIInspectResult>>(url, body);
            const status = await handleApiResponse(res, (v) => { 
                const oldFixed = (aiReadyResult?.ai_annotations || []).filter(a => a.type === 'fixed-area');
                v.ai_annotations = [...oldFixed, ...(v.ai_annotations || [])];
                aiReadyResult = v;
            }, 'ai_inspect');
            if (status === 'accepted') isAccepted = true;
        } finally {
            stopThinkingLogs();
            if (!isAccepted) {
                isAiLoading = false;
                bulkFixStatus = "Hoàn tất ✅";
                setTimeout(() => {
                    if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) {
                        isBulkFixing = false;
                        bulkFixStatus = "";
                        
                    }
                }, 1500);
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
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = "";  } }, 3200);
        }
    }

    async function runAutoFix(target: string, type: string, msg: string) {
        const cid = resolve(config.campaign_id);
        const topic = resolve(config.topic) ?? '';
        const content = (config.getContent ?? config.getEditedDraft)?.() ?? '';

        // CNS V86.5: Hỗ trợ cả ad-hoc (không có campaign_id) lẫn campaign mode
        let newText: string | null = null;
        if (cid) {
            newText = await xohiActions.runAutoFix(cid, target, type, msg);
        } else {
            // Ad-hoc mode: truyền content hiện tại để AI có context đầy đủ
            newText = await xohiActions.runAdHocAutoFix(content, target, type, msg, topic);
        }

        if (newText) {
            // Áp dụng kết quả vào editor — surgical replace
            const currentContent = (config.getContent ?? config.getEditedDraft)?.() ?? '';
            const updated = currentContent.replace(target, newText);
            if (updated !== currentContent) {
                if (resolve(config.isEditing)) config.setEditedDraft(updated);
                else config.setDraftContent(updated);
            }

            // Xóa annotation đã sửa khỏi danh sách
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
        if (isAdhoc) nanobot.updateCurrentData({ campaign_id: 'adhoc' });
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
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = "";  } }, 3000);
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
            setTimeout(() => { isBulkFixing = false; bulkFixStatus = "";  }, 3500);
        }
    }

    // CNS V86.5: Hydrate — Khôi phục kết quả phân tích từ cache sau F5
    $effect(() => {
        const cache = resolve(config.analysis_cache);
        if (cache && Object.keys(cache).length > 0) {
            untrack(() => {
                if (cache.copyright?.data) {
                    if (!copyrightResult || isCopyrightLoading) {
                        copyrightResult = cache.copyright.data as CopyrightResult;
                        if (isCopyrightLoading) { isCopyrightLoading = false; setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; }, 1000); }
                    }
                }
                if (cache.seo?.data) {
                    if (!seoResult || isSeoLoading) {
                        seoResult = cache.seo.data as SEOResult;
                        if (isSeoLoading) { isSeoLoading = false; setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; }, 1000); }
                    }
                }
                if (cache.ai_inspect?.data) {
                    if (!aiReadyResult || isAiLoading) {
                        aiReadyResult = cache.ai_inspect.data as AIInspectResult;
                        if (isAiLoading) { isAiLoading = false; setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; }, 1000); }
                    }
                }

                // CNS V86.5: Auto-select tab sau khi hydrate để khôi phục highlights & nút Fix All
                // Ưu tiên: tab đầu tiên có annotations, fallback về tab có dữ liệu
                if (activeTab === null) {
                    if (cache.copyright?.data && (cache.copyright.data as CopyrightResult).annotations?.length > 0) {
                        activeTab = 'copyright';
                    } else if (cache.seo?.data && (cache.seo.data as SEOResult).seo_annotations?.length > 0) {
                        activeTab = 'seo';
                    } else if (cache.ai_inspect?.data && (cache.ai_inspect.data as AIInspectResult).ai_annotations?.length > 0) {
                        activeTab = 'ai';
                    } else if (cache.ai_inspect?.data) {
                        activeTab = 'ai';
                    } else if (cache.seo?.data) {
                        activeTab = 'seo';
                    } else if (cache.copyright?.data) {
                        activeTab = 'copyright';
                    }
                }
            });
        }
    });

    // CNS V85.5: Log-based Completion Detector (Force close when task finishes)
    $effect(() => {
        if (bulkFixLogs.length > 0) {
            const lastLog = bulkFixLogs[bulkFixLogs.length - 1];
            if (lastLog.includes("ĐÃ XỬ LÝ XONG") || lastLog.includes("ĐANG ĐỒNG BỘ GIAO DIỆN") || lastLog.includes("Đã dọn dẹp xong")) {
                // CNS V85.6: Use untrack and direct assignments to prevent loop/freeze
                untrack(() => {
                    if (isCopyrightLoading) isCopyrightLoading = false;
                    if (isSeoLoading) isSeoLoading = false;
                    if (isAiLoading) isAiLoading = false;
                    if (isBulkFixing) isBulkFixing = false; 
                });
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
            copyrightResult = null; seoResult = null; aiReadyResult = null;  bulkFixStatus = ""; activeTab = null;
        }
    };
}
