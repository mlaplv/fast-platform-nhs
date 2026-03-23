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
    let bulkFixStatus = $state("");
    let bulkFixLogs = $state<string[]>([]);
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

    async function runCopyrightCheck(force: boolean = false, skipSave: boolean = false) {
        if (!config.campaign_id || isCopyrightLoading) return;
        isCopyrightLoading = true;
        isBulkFixing = true; // Trigger NeuralProgressTooltip
        bulkFixStatus = "Đang quét...";
        bulkFixLogs = ["🔍 Đang khởi động hệ thống tầm soát bản quyền...", "🧠 Đang phân tích cấu trúc bài viết..."];
        activeTab = 'copyright';
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const res = await apiClient.post<{ data: { uniqueness_score: number, risk_level: string, annotations: any[], logs?: string[] } }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/copyright?force=${force}`);
            
            if (res?.data) {
                // Phase 3.7: Premium Log Replay for Analysis
                if (res.data.logs && res.data.logs.length > 0) {
                    for (const log of res.data.logs) {
                        // Avoid duplicates if initial logs are also in backend logs
                        if (!bulkFixLogs.includes(log)) {
                            bulkFixLogs = [...bulkFixLogs, log];
                            await new Promise(r => setTimeout(r, 400));
                        }
                    }
                }
                copyrightResult = res.data;
            }
        } catch (e) {
            console.error("Copyright check failed:", e);
            bulkFixLogs = [...bulkFixLogs, "⚠️ Lỗi: Không thể hoàn tất thẩm định bản quyền."];
        } finally {
            isCopyrightLoading = false;
            isBulkFixing = false;
            // Clear status after delay
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3000);
        }
    }

    async function runSeoAnalysis(force: boolean = false, skipSave: boolean = false) {
        if (!config.campaign_id || isSeoLoading || seoLocked) return;
        isSeoLoading = true;
        isBulkFixing = true; // CNS V4.0: Trigger NeuralProgressTooltip
        bulkFixStatus = "Đang quét SEO...";
        bulkFixLogs = ["🔍 Đang khởi động SEO Optimizer (Phase 82.8)...", "🧠 Đang phân tích mật độ từ khóa & cấu trúc bài..."];
        activeTab = 'seo';
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const res = await apiClient.post<{ data: { geo_score: number, summary: string, ai_annotations: any[], logs?: string[] } }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/seo?force=${force}`);
            if (res?.data) {
                // Phase 4.0: Premium Log Replay
                if (res.data.logs && res.data.logs.length > 0) {
                    for (const log of res.data.logs) {
                        if (!bulkFixLogs.includes(log)) {
                            bulkFixLogs = [...bulkFixLogs, log];
                            await new Promise(r => setTimeout(r, 400));
                        }
                    }
                }
                seoResult = res.data;
            }
        } catch (e) {
            console.error("SEO analysis failed:", e);
            bulkFixLogs = [...bulkFixLogs, "⚠️ Lỗi: Không thể hoàn tất thẩm định SEO."];
        } finally {
            isSeoLoading = false;
            isBulkFixing = false;
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3000);
        }
    }

    async function runAiAnalysis(force: boolean = false, skipSave: boolean = false) {
        if (!config.campaign_id || isAiLoading || aiLocked) return;
        isAiLoading = true;
        isBulkFixing = true; // CNS V4.0: Trigger NeuralProgressTooltip
        bulkFixStatus = "Đang quét AI MOD...";
        bulkFixLogs = ["🔍 Đang khởi động AI MOD (Phase 82.8)...", "🧠 Đang rà soát dấu vân tay AI & phong cách viết..."];
        activeTab = 'ai';
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const res = await apiClient.post<{ data: { geo_score: number, summary: string, ai_annotations: any[], logs?: string[] } }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/ai-inspect?force=${force}`);
            if (res?.data) {
                // Phase 4.0: Premium Log Replay
                if (res.data.logs && res.data.logs.length > 0) {
                    for (const log of res.data.logs) {
                        if (!bulkFixLogs.includes(log)) {
                            bulkFixLogs = [...bulkFixLogs, log];
                            await new Promise(r => setTimeout(r, 400));
                        }
                    }
                }
                aiReadyResult = res.data;
            }
        } catch (e) {
            console.error("AI Inspect failed:", e);
            bulkFixLogs = [...bulkFixLogs, "⚠️ Lỗi: Không thể hoàn tất thẩm định AI MOD."];
        } finally {
            isAiLoading = false;
            isBulkFixing = false;
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3000);
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
                    seoResult.seo_annotations = seoResult.seo_annotations.filter((a: AnalysisAnnotation) => !updateMatches(a));
                }
                if (aiReadyResult?.ai_annotations) {
                    aiReadyResult.ai_annotations = aiReadyResult.ai_annotations.filter((a: AnalysisAnnotation) => !updateMatches(a));
                }
                if (copyrightResult?.annotations) {
                    copyrightResult.annotations = copyrightResult.annotations.filter((a: AnalysisAnnotation) => !updateMatches(a));
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
        bulkFixLogs = ["Đang khởi tạo Neural Engine...", "Đang nạp ngữ chuẩn Viral Edge 2026...", "Đang phân tích cấu trúc bài viết..."];
        try {
            let category = '';
            let annotationsToSend: AnalysisAnnotation[] = [];
            if (activeTab === 'copyright') { category = 'copyright'; annotationsToSend = copyrightResult?.annotations || []; }
            else if (activeTab === 'seo') { category = 'seo'; annotationsToSend = seoResult?.seo_annotations || []; }
            else if (activeTab === 'ai') { category = 'ai'; annotationsToSend = aiReadyResult?.ai_annotations || []; }

            if (annotationsToSend.length === 0) {
                bulkFixLogs = [...bulkFixLogs, "⚠️ Không tìm thấy lỗi nào cần sửa cho mục này."];
                isBulkFixing = false;
                setTimeout(() => { bulkFixStatus = ""; bulkFixLogs = []; }, 3000);
                return;
            }

            // Phase A: Snapshot old annotation texts for fixed-area comparison later
            bulkFixStatus = "Đang phẫu thuật...";
            bulkFixLogs = [...bulkFixLogs, `Phát hiện ${annotationsToSend.length} phân đoạn cần tối ưu.`, "Đang kích hoạt quy trình 'Surgical Precision' (Chỉ sửa phần lỗi)..."];
            const oldAnnotationTexts = new Set(
                annotationsToSend.map(a => (a.text || '').trim()).filter(t => t.length > 5)
            );

            let initialLogs: string[] = [];
            if (category === 'copyright') {
                initialLogs = ["🎯 Đang kích hoạt Copyright Neural (Phase 82.8)...", "🧠 Đang phân tích cấu trúc & nội dung lặp lại...", "🔍 Đang trinh sát nguồn dữ liệu đối chiếu..."];
            } else if (category === 'seo') {
                initialLogs = ["🎯 Đang kích hoạt SEO Optimizer (Phase 82.8)...", "🧠 Đang phân tích mật độ từ khóa & cấu trúc bài...", "🔍 Đang trinh sát dữ liệu từ Google cho top keyword..."];
            } else {
                initialLogs = ["🎯 Đang kích hoạt AI MOD (Phase 82.8)...", "🧠 Đang rà soát dấu vân tay AI & phong cách viết...", "🔍 Đang phẫu thuật để tăng tính 'Human' cho bài viết..."];
            }

            bulkFixLogs = [...bulkFixLogs, ...initialLogs];
            const res = await apiClient.post<{ status: string; data: { new_content: string, logs?: string[] } }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/bulk-fix`, {
                category: category,
                annotations: annotationsToSend
            });

            if (res?.status === 'success' && res.data?.new_content) {
                // Phase 82.80: Premium Log Replay (iPhone 18/Claude Style)
                if (res.data.logs && res.data.logs.length > 0) {
                    for (const log of res.data.logs) {
                        bulkFixLogs = [...bulkFixLogs, log];
                        await new Promise(r => setTimeout(r, 450)); // iOS-style micro-animation delay
                    }
                }

                bulkFixStatus = "Đang lưu...";
                bulkFixLogs = [...bulkFixLogs, "✅ Phẫu thuật hoàn tất!", "Đang đồng bộ bản thảo (Asset Fidelity)...", "Đang ghi đè dữ liệu AI chuẩn xác..."];
                const newHtml = res.data.new_content;
                // Phase B: Persist AI-fixed content (both DB and editor state)
                await apiClient.patch(`/api/v1/content/campaigns/${config.campaign_id}`, { draft_content: newHtml });
                if (config.isEditing) config.setEditedDraft(newHtml);
                else config.setDraftContent(newHtml);

                // Phase C: Clear old annotations so highlights are removed cleanly
                if (activeTab === 'copyright' && copyrightResult) copyrightResult = { ...copyrightResult, annotations: [] };
                else if (activeTab === 'seo' && seoResult) seoResult = { ...seoResult, seo_annotations: [] };
                else if (activeTab === 'ai' && aiReadyResult) aiReadyResult = { ...aiReadyResult, ai_annotations: [] };

                await tick();
                await new Promise(resolve => setTimeout(resolve, 300));

                // Phase D: Re-check with skipSave=true (content already saved above)
                bulkFixStatus = "Đang thẩm định...";
                bulkFixLogs = [...bulkFixLogs, "Đang khởi động bộ máy thẩm định độc lập...", "Đang đối chiếu dữ liệu mới sau phẫu thuật..."];
                if (activeTab === 'copyright') await runCopyrightCheck(true, true);
                else if (activeTab === 'seo') await runSeoAnalysis(true, true);
                else if (activeTab === 'ai') await runAiAnalysis(true, true);
                
                bulkFixLogs = [...bulkFixLogs, "✅ Đã thẩm định. Kết quả đang được cập nhật..."];

                // Phase E: Inject fixed-area annotations (green highlights for repaired segments)
                if (activeTab === 'copyright' && copyrightResult) {
                    const newTexts = new Set(copyrightResult.annotations.map((a: AnalysisAnnotation) => (a.text || '').trim()));
                    const fixedAnnotations: AnalysisAnnotation[] = [...oldAnnotationTexts]
                        .filter(t => t && !newTexts.has(t))
                        .map(t => ({
                            text: t,
                            reason: '✅ Đoạn này đã được AI sửa thành công',
                            source_url: '',
                            severity: 'low',
                            type: 'fixed-area'
                        }));
                    if (fixedAnnotations.length > 0) {
                        copyrightResult = {
                            ...copyrightResult,
                            annotations: [...fixedAnnotations, ...copyrightResult.annotations]
                        };
                    }
                }
            }
        } catch (e) {
            console.error('Bulk Fix failed:', e);
            bulkFixLogs = [...bulkFixLogs, "⚠️ Lỗi: Không thể hoàn tất phẫu thuật."];
        } finally {
            isBulkFixing = false;
            // Clear status but keep logs for a brief moment in the UI
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3000);
        }
    }

    async function runAiBooster() {
        if (!config.campaign_id || isBoosting || !seoResult) return;
        isBoosting = true;
        isBulkFixing = true; // CNS V3.6: Trigger NeuralProgressTooltip
        bulkFixStatus = "Đang Booster...";
        bulkFixLogs = ["🚀 Đang khởi động Neural Booster™ (Phase 82.85)...", "🧠 Đang phân tích chiến lược trinh sát dữ liệu..."];
        activeTab = 'enrich';
        try {
            await saveBeforeAnalysis();
            const res = await apiClient.post<{ status: string; data: { new_content: string, logs?: string[] } }>(`/api/v1/content/campaigns/${config.campaign_id}/analyze/enrich`);
            if (res?.status === 'success' && res.data?.new_content) {
                // Phase 3.6: Premium Log Replay for Booster
                if (res.data.logs && res.data.logs.length > 0) {
                    for (const log of res.data.logs) {
                        bulkFixLogs = [...bulkFixLogs, log];
                        await new Promise(r => setTimeout(r, 600)); // Premium feel
                    }
                }
                
                bulkFixStatus = "Đang lưu...";
                bulkFixLogs = [...bulkFixLogs, "✅ Đã tổng hợp dữ liệu thành công!", "Đang đồng bộ bản thảo tối ưu..."];
                const newHtml = res.data.new_content;
                if (config.isEditing) config.setEditedDraft(newHtml);
                else config.setDraftContent(newHtml);
                await tick();
                await new Promise(resolve => setTimeout(resolve, 300));
                
                bulkFixStatus = "Đang thẩm định...";
                bulkFixLogs = [...bulkFixLogs, "Đang khởi động bộ máy thẩm định SEO...", "Đang đối chiếu điểm số mới..."];
                activeTab = 'seo';
                await runSeoAnalysis(true);
                bulkFixLogs = [...bulkFixLogs, "🎯 AI Booster hoàn tất! Điểm SEO đã được cải thiện."];
                setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; bulkFixLogs = []; }, 3500);
            }
        } catch (e) {
            console.error('AI Booster failed:', e);
            bulkFixLogs = [...bulkFixLogs, "❌ Lỗi: " + (e?.message || "Không thể kết nối AI Booster.")];
            setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; bulkFixLogs = []; }, 4000);
        } finally {
            isBoosting = false;
        }
    }

    // Hydrate from cache
    $effect(() => {
        const cache = config.analysis_cache;
        if (cache) {
            // CNS V82.50: Use untrack to prevent recursive loops if results trigger more effects
            if (cache.copyright?.data && !copyrightResult) copyrightResult = cache.copyright.data as CopyrightResult;
            if (cache.seo?.data && !seoResult) seoResult = cache.seo.data as SEOResult;
            if (cache.ai_inspect?.data && !aiReadyResult) aiReadyResult = cache.ai_inspect.data as AIInspectResult;

            // CNS V82.51: Force initial active tab if missing (Ensures "Fix All" button visibility)
            if (!activeTab) {
                if (copyrightResult && (copyrightResult.annotations?.length || 0) > 0) activeTab = 'copyright';
                else if (seoResult && (seoResult.seo_annotations?.length || 0) > 0) activeTab = 'seo';
                else if (aiReadyResult && (aiReadyResult.ai_annotations?.length || 0) > 0) activeTab = 'ai';
                else if (copyrightResult) activeTab = 'copyright'; // Fallback to first available
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
        runCopyrightCheck,
        runSeoAnalysis,
        runAiAnalysis,
        runAutoFix,
        runBulkFix,
        runAiBooster
    };
}
