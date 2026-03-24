import { apiClient } from "$lib/utils/apiClient";
import { nanobot } from "./nanobot.svelte";
import { tick, untrack } from "svelte";
import type {
    CopyrightResult,
    SEOResult,
    AIInspectResult,
    AnalysisCache,
    CampaignMetrics,
    AnalysisAnnotation,
    EditorAnnotation,
    GenericResponse
} from "$lib/state/types";

export function createAnalysisController(config: {
    campaign_id?: string | null;
    /** Required in adhoc mode: returns the full current HTML for analysis */
    getContent?: () => string;
    /** Optional topic/keyword for SEO analysis in adhoc mode */
    topic?: string;
    isEditing: boolean;
    getEditedDraft: () => string;
    getDraftContent: () => string;
    setEditedDraft: (v: string) => void;
    setDraftContent: (v: string) => void;
    analysis_cache: AnalysisCache;
    analysis_metrics: CampaignMetrics;
}) {
    /** Resolve whether we are operating in Campaign or Adhoc (stateless) mode */
    const isAdhoc = !config.campaign_id;
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

    // Phase 82.90: Live HUD Sync — Syncs real-time messages from global Pulse stream into local HUD logs
    $effect(() => {
        const data = nanobot.currentData as any;
        if (!data || !config.campaign_id || (data.campaign_id !== config.campaign_id && data.id !== config.campaign_id)) return;
        
        const msg = data.progress_msg;
        if (msg) {
            untrack(() => {
                // Only append if it's a new message and something is actually loading
                const currentLoading = isCopyrightLoading || isSeoLoading || isAiLoading || isBulkFixing || isBoosting;
                if (currentLoading && !bulkFixLogs.includes(msg)) {
                    bulkFixLogs = [...bulkFixLogs, msg];
                    // Sync broad status if empty
                    if (!bulkFixStatus) bulkFixStatus = "Đang xử lý...";
                }
            });
        }
    });

    // Derived scores
    let copyrightScore = $derived(copyrightResult ? Math.round(copyrightResult.uniqueness_score * 100) : null);
    let seoScore = $derived(seoResult ? seoResult.total_score : null);
    let aiScore = $derived(aiReadyResult ? aiReadyResult.geo_score : null);

    // Gate conditions
    let seoLocked = $derived(copyrightScore === null || copyrightScore < 55);
    let aiLocked = $derived(seoScore === null || seoScore < 40);

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
        if (isCopyrightLoading) return;
        if (!isAdhoc && !config.campaign_id) return;
        isCopyrightLoading = true;
        isBulkFixing = true; // Trigger NeuralProgressTooltip
        bulkFixStatus = "Đang quét...";
        bulkFixLogs = ["🔍 Đang khởi động hệ thống tầm soát bản quyền...", "🧠 Đang phân tích cấu trúc bài viết..."];
        activeTab = 'copyright';
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const url = isAdhoc
                ? `/api/v1/content/analyze/copyright?force=${force}`
                : `/api/v1/content/campaigns/${config.campaign_id}/analyze/copyright?force=${force}`;
            const body = isAdhoc ? { content: (config.getContent ?? config.getEditedDraft)() } : undefined;
            const res = await apiClient.post<GenericResponse<CopyrightResult>>(url, body);
            
            if (res?.data) {
                // Phase 3.7: Premium Log Replay for Analysis
                if (res.data.logs && res.data.logs.length > 0) {
                    for (const log of res.data.logs) {
                        // Avoid duplicates if initial logs are also in backend logs
                        if (!bulkFixLogs.includes(log)) {
                            bulkFixLogs = [...bulkFixLogs, log];
                            
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
            // CNS V82.9: Delayed release - keep tooltip visible for a few seconds to read the finish log
            setTimeout(() => { if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) isBulkFixing = false; }, 3000);
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3200);
        }
    }

    async function runSeoAnalysis(force: boolean = false, skipSave: boolean = false) {
        if (isSeoLoading) return;
        if (!isAdhoc && !config.campaign_id) return;
        isSeoLoading = true;
        isBulkFixing = true; // CNS V3.5: Trigger NeuralProgressTooltip
        bulkFixStatus = "Đang quét SEO...";
        bulkFixLogs = ["🔍 Đang khởi động máy quét SEO (Phase 82.8)...", "🧠 Đang phân tích mật độ từ khóa & cấu trúc HTML..."];
        const topicName = config.topic ?? '';
        activeTab = 'seo';
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const url = isAdhoc
                ? `/api/v1/content/analyze/seo?force=${force}`
                : `/api/v1/content/campaigns/${config.campaign_id}/analyze/seo?force=${force}`;
            const body = isAdhoc ? { content: (config.getContent ?? config.getEditedDraft)(), topic: topicName } : undefined;
            
            const res = await apiClient.post<GenericResponse<SEOResult>>(url, body);
            if (res?.data) {
                if (res.data.logs && res.data.logs.length > 0) {
                    for (const log of res.data.logs) {
                        if (!bulkFixLogs.includes(log)) {
                            bulkFixLogs = [...bulkFixLogs, log];
                        }
                    }
                }
                
                // Salvage green highlights (fixed-area) as requested by user
                const oldFixed = (seoResult?.seo_annotations || []).filter((a: AnalysisAnnotation) => a.type === 'fixed-area');
                res.data.seo_annotations = [...oldFixed, ...(res.data.seo_annotations || [])];
                
                seoResult = res.data;
            }
        } catch (e) {
            console.error("SEO analysis failed:", e);
            bulkFixLogs = [...bulkFixLogs, "⚠️ Lỗi: Không thể hoàn tất thẩm định SEO."];
        } finally {
            isSeoLoading = false;
            setTimeout(() => { if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) isBulkFixing = false; }, 3000);
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3200);
        }
    }

    async function runAiAnalysis(force: boolean = false, skipSave: boolean = false) {
        if (isAiLoading || aiLocked) return;
        if (!isAdhoc && !config.campaign_id) return;
        isAiLoading = true;
        isBulkFixing = true; // CNS V4.0: Trigger NeuralProgressTooltip
        bulkFixStatus = "Đang quét AI MOD...";
        bulkFixLogs = ["🔍 Đang khởi động AI MOD (Phase 82.8)...", "🧠 Đang rà soát dấu vân tay AI & phong cách viết..."];
        activeTab = 'ai';
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const url = isAdhoc
                ? `/api/v1/content/analyze/ai-inspect?force=${force}`
                : `/api/v1/content/campaigns/${config.campaign_id}/analyze/ai-inspect?force=${force}`;
            const body = isAdhoc ? { content: (config.getContent ?? config.getEditedDraft)() } : undefined;
            const res = await apiClient.post<GenericResponse<AIInspectResult>>(url, body);
            if (res?.data) {
                // Phase 4.0: Premium Log Replay
                if (res.data.logs && res.data.logs.length > 0) {
                    for (const log of res.data.logs) {
                        if (!bulkFixLogs.includes(log)) {
                            bulkFixLogs = [...bulkFixLogs, log];
                            
                        }
                    }
                }
                // Salvage green highlights (fixed-area) as requested by user
                const oldFixed = (aiReadyResult?.ai_annotations || []).filter((a: AnalysisAnnotation) => a.type === 'fixed-area');
                res.data.ai_annotations = [...oldFixed, ...(res.data.ai_annotations || [])];
                
                aiReadyResult = res.data;
            }
        } catch (e) {
            console.error("AI Inspect failed:", e);
            bulkFixLogs = [...bulkFixLogs, "⚠️ Lỗi: Không thể hoàn tất thẩm định AI MOD."];
        } finally {
            isAiLoading = false;
            setTimeout(() => { if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) isBulkFixing = false; }, 3000);
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3200);
        }
    }

    async function runCleanContent(): Promise<string | null> {
        if (isCopyrightLoading || isSeoLoading || isAiLoading) return null;
        isBulkFixing = true;
        bulkFixStatus = "Đang dọn dẹp...";
        bulkFixLogs = ["🧹 Đang khởi động Neural Clean (Phase 76.9)...", "🧠 Đang dọn dẹp artifacts & Jaccard dedup..."];
        try {
            const content = (config.getContent ?? config.getEditedDraft)();
            if (!content) return null;
            
            // Phase 82.9: HUD Real-time Log injection
            setTimeout(() => { 
                if (isBulkFixing) bulkFixLogs = [...bulkFixLogs, "🚀 Đang tối ưu cấu trúc & dọn dẹp..."]; 
            }, 1000);

            const res = await apiClient.post<any>('/api/v1/content/clean', { content });
            if (res?.data?.content) {
                const cleaned = res.data.content;
                config.setEditedDraft?.(cleaned);
                bulkFixLogs = [...bulkFixLogs, "🎯 Đã dọn dẹp xong (Deterministic Clean) ✅"];
                nanobot.showToast("Đã dọn dẹp & tối ưu cấu trúc thành công!", "success");
                return cleaned;
            }
        } catch (e) {
            console.error("Neural Clean failed:", e);
            bulkFixLogs = [...bulkFixLogs, "⚠️ Lỗi: Không thể hoàn tất Neural Clean."];
        } finally {
            // CNS V82.9: Consistency in delay
            setTimeout(() => { 
                if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) {
                    isBulkFixing = false;
                }
            }, 3000);
            setTimeout(() => { if (!isBulkFixing) { bulkFixStatus = ""; bulkFixLogs = []; } }, 3200);
        }
        return null;
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
        if (isBulkFixing || !activeTab) return;
        if (!isAdhoc && !config.campaign_id) return;
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
            const bulkUrl = isAdhoc
                ? `/api/v1/content/analyze/bulk-fix`
                : `/api/v1/content/campaigns/${config.campaign_id}/analyze/bulk-fix`;
            const bulkBody = isAdhoc
                ? { content: (config.getContent ?? config.getEditedDraft)(), topic: config.topic ?? '', category, annotations: annotationsToSend }
                : { category, annotations: annotationsToSend };
            const res = await apiClient.post<{ status: string; data: { new_content: string, logs?: string[], replacements?: Array<{old_text: string, new_text: string}> } }>(bulkUrl, bulkBody);

            if (res?.status === 'success' && res.data?.new_content) {
                // Phase 82.80: Premium Log Replay (iPhone 18/Claude Style)
                if (res.data.logs && res.data.logs.length > 0) {
                    for (const log of res.data.logs) {
                        bulkFixLogs = [...bulkFixLogs, log];
                    }
                }

                bulkFixStatus = "Đang lưu...";
                bulkFixLogs = [...bulkFixLogs, "✅ Phẫu thuật hoàn tất!", "Đang đồng bộ bản thảo (Asset Fidelity)...", "Đang ghi đè dữ liệu AI chuẩn xác..."];
                const newHtml = res.data.new_content;
                const replacements = res.data.replacements || []; // Array of { old_text, new_text }
                
                // In campaign mode, also persist fixed content to DB
                if (!isAdhoc && config.campaign_id) {
                    await apiClient.patch(`/api/v1/content/campaigns/${config.campaign_id}`, { draft_content: newHtml });
                }
                if (config.isEditing) config.setEditedDraft(newHtml);
                else config.setDraftContent(newHtml);

                await tick();
                await new Promise(resolve => setTimeout(resolve, 300));

                // NO AUTO-CHECK PER USER REQUEST ("sửa xong đánh dấu đã sửa tôi kiểm tra")
                bulkFixLogs = [...bulkFixLogs, "✅ Đã phẫu thuật xong. Vui lòng bấm Check lại khi CẦN."];

                // Phase C: Extract fixed areas directly from replacements array so Tiptap accurately finds them
                const fixedAnnotations: AnalysisAnnotation[] = [];
                const remainingErrors: AnalysisAnnotation[] = [];

                for (const a of annotationsToSend) {
                    const t = (a.text || '').trim();
                    if (!t) continue;

                    const normalizedT = t.normalize('NFC').replace(/[^\p{L}\p{N}]/gu, '').toLowerCase();
                    const fixRecord = replacements.find((r: any) => {
                        if (!r.old_text) return false;
                        const normOld = r.old_text.normalize('NFC').replace(/[^\p{L}\p{N}]/gu, '').toLowerCase();
                        return normOld === normalizedT;
                    });

                    if (fixRecord && fixRecord.new_text) {
                        fixedAnnotations.push({
                            text: fixRecord.new_text, // EXACT new text so TiptapEditor highlights it correctly!
                            reason: '✅ Đoạn này đã được AI sửa thành công (Chờ thẩm định lại)',
                            message: '✅ Đoạn này đã được AI sửa thành công (Chờ thẩm định lại)',
                            source_url: a.source_url || '',
                            severity: 'low',
                            type: 'fixed-area'
                        });
                    } else {
                        remainingErrors.push({
                            ...a,
                            type: a.type || (activeTab === 'seo' ? 'seo-info' : activeTab === 'ai' ? 'geo-info' : 'copyright'),
                            reason: a.reason ? `[CHƯA SỬA ĐƯỢC] ${a.reason}` : a.reason,
                            message: a.message ? `[CHƯA SỬA ĐƯỢC] ${a.message}` : a.message
                        });
                    }
                }

                if (activeTab === 'copyright' && copyrightResult) {
                    copyrightResult = { ...copyrightResult, annotations: [...fixedAnnotations, ...remainingErrors] };
                } else if (activeTab === 'seo' && seoResult) {
                    seoResult = { ...seoResult, seo_annotations: [...fixedAnnotations, ...remainingErrors] };
                } else if (activeTab === 'ai' && aiReadyResult) {
                    aiReadyResult = { ...aiReadyResult, ai_annotations: [...fixedAnnotations, ...remainingErrors] };
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
        // AI Booster requires a persistent campaign context (enrich endpoint needs campaign record in DB)
        if (isAdhoc || !config.campaign_id || isBoosting || !seoResult) return;
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
            bulkFixLogs = [...bulkFixLogs, "❌ Lỗi: " + (e instanceof Error ? e.message : "Không thể kết nối AI Booster.")];
            setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; bulkFixLogs = []; }, 4000);
        } finally {
            isBoosting = false;
        }
    }

    // Hydrate from cache (CNS V82.52: Reactive Sync)
    $effect(() => {
        const cache = config.analysis_cache;
        if (cache && Object.keys(cache).length > 0) {
            untrack(() => {
                if (cache.copyright?.data && (copyrightResult === null || copyrightResult === undefined)) {
                    copyrightResult = cache.copyright.data as CopyrightResult;
                }
                if (cache.seo?.data && (seoResult === null || seoResult === undefined)) {
                    seoResult = cache.seo.data as SEOResult;
                }
                if (cache.ai_inspect?.data && (aiReadyResult === null || aiReadyResult === undefined)) {
                    aiReadyResult = cache.ai_inspect.data as AIInspectResult;
                }

                // Force initial active tab if missing (Ensures "Fix All" button visibility)
                if (!activeTab) {
                    if (copyrightResult && (copyrightResult.annotations?.length || 0) > 0) activeTab = 'copyright';
                    else if (seoResult && (seoResult.seo_annotations?.length || 0) > 0) activeTab = 'seo';
                    else if (aiReadyResult && (aiReadyResult.ai_annotations?.length || 0) > 0) activeTab = 'ai';
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
        runCopyrightCheck,
        runSeoAnalysis,
        runAiAnalysis,
        runAutoFix,
        runCleanContent,
        runBulkFix,
        runAiBooster
    };
}
