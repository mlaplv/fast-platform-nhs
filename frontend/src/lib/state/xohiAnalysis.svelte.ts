import { apiClient } from "$lib/utils/apiClient";
import { useNanobot } from "./nanobot.svelte";
import { tick, untrack } from "svelte";
import { xohiActions } from "./xohiActions";
import { robustNormalize, refinementStitch, extractBoostedText, stripBoostTags } from "./xohiAnalysisLogic";
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
    TaskAcceptedResponse,
    CleanOptions,
    ClinicalSource   // CNS V92.0
} from "$lib/state/types";

export function createAnalysisController(config: {
    campaign_id?: string | null | (() => string | null | undefined);
    contentType?: string | (() => string);
    getMetadata?: () => Record<string, string | number | boolean | null> | null;
    getContent?: () => string;
    topic?: string | (() => string);
    isEditing: boolean | (() => boolean);
    getEditedDraft: () => string;
    getDraftContent: () => string;
    setEditedDraft: (v: string) => void;
    setDraftContent: (v: string) => void;
    analysis_cache: AnalysisCache | (() => AnalysisCache);
    analysis_metrics: CampaignMetrics | (() => CampaignMetrics);
    analysis_report?: Record<string, Record<string, unknown>> | (() => Record<string, Record<string, unknown>> | undefined);
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
    let isRewriting = $state(false);
    let bulkFixStatus = $state("");
    let bulkFixLogs = $state<string[]>([]);
    let currentAnalysisStep = $state<number | null>(null);
    let isBoosting = $state(false);
    let userPlanNote = $state("");
    let activeTab = $state<'copyright' | 'seo' | 'ai' | 'enrich' | null>(null);
    let boosterAnnotations = $state<AnalysisAnnotation[]>([]);
    let clinicalSources = $state<ClinicalSource[]>([]);  // CNS V92.0
    // CNS V87.0: SSE Streaming state — typewriter effect
    let streamingText = $state<string>("");        // Text đang stream từng chunk
    let streamingTarget = $state<string | null>(null); // Annotation text đang được sửa
    let _sseAbort: AbortController | null = null;  // CLAUDE.md: dispose resource khi xong

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
                const isSuccess = data.status === 'WAITING_FOR_REVIEW' || data.status === 'COMPLETED' || data.status === 'SUCCESS';
                const isError = data.status === 'ERROR';
                
                // [CNS V92.2] Worker-Result Auto-Fetch: Khi worker xong, pull kết quả mới từ DB cache
                // (skipSave=true vì worker đã lưu sẵn, force=false để lấy từ cache không tốn thêm AI token)
                if (isSuccess) {
                    const wasLoadingCopyright = isCopyrightLoading;
                    const wasLoadingSeo       = isSeoLoading;
                    const wasLoadingAi        = isAiLoading;
                    if (wasLoadingCopyright) {
                        addTerminalLog("🔄 Worker hoàn tất — đang tải kết quả mới từ Neural Vault...");
                        runCopyrightCheck(false, true).catch(() => {});
                    } else if (wasLoadingSeo) {
                        addTerminalLog("🔄 Worker hoàn tất — đang tải kết quả SEO mới...");
                        runSeoAnalysis(false, true).catch(() => {});
                    } else if (wasLoadingAi) {
                        addTerminalLog("🔄 Worker hoàn tất — đang tải kết quả AI mới...");
                        runAiAnalysis(false, true).catch(() => {});
                    }
                }

                // [CNS V90.0] Fire Toast BEFORE resetting loading flags to ensure condition matches
                if (isSuccess && (isBulkFixing || isCopyrightLoading || isSeoLoading || isAiLoading)) {
                    nanobot.showToast(data.progress_msg || "Xử lý hoàn tất thành công!", "success");
                    console.log("[Neural Terminal] Success Toast fired.");
                } else if (isError) {
                    nanobot.showToast(data.progress_msg || "Xử lý thất bại.", "error");
                    console.log("[Neural Terminal] Error Toast fired.");
                }

                // Update bulkFixLogs one last time
                if (data.progress_msg) {
                    bulkFixLogs = [...bulkFixLogs, `✅ ${data.progress_msg}`];
                }

                // CNS V85.8: Persistence logic — giữ trạng thái "Hoàn tất" lâu hơn
                // Chỉ reset ngay nếu KHÔNG phải đang auto-fetch (isSuccess với loading flags)
                if (!isSuccess && (isBulkFixing || isCopyrightLoading || isSeoLoading || isAiLoading)) {
                    bulkFixStatus = "Thất bại ❌";
                    setTimeout(() => {
                        isCopyrightLoading = false; isSeoLoading = false; isAiLoading = false; isBulkFixing = false; isBoosting = false;
                        bulkFixStatus = "";
                    }, 2500);
                }
            });
        }

        if (!msg) return;

        untrack(() => {
            if (config.getIsProcessing?.() || isBulkFixing || isCopyrightLoading || isSeoLoading || isAiLoading) {
                // CNS V90.5: Internal log helper to prevent duplicate messages and maintain order
                const timestamp = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
                const fullMsg = `[${timestamp}] ${msg}`;
                
                if (!bulkFixLogs.some(l => l.includes(msg))) {
                    bulkFixLogs = [...bulkFixLogs, fullMsg];
                }
                
                // Always update status to reflect current step, ensuring HUD doesn't feel 'stuck'
                bulkFixStatus = msg;
                if (typeof data.step === 'number') {
                    if (currentAnalysisStep === null || data.step > currentAnalysisStep) {
                        currentAnalysisStep = data.step;
                    }
                }
            }
        });
    });

    /**
     * CNS V90.5: Unified Terminal Logger
     * Prepends stable timestamp to ensure terminal logs don't 'drift' on re-render.
     */
    function addTerminalLog(msg: string) {
        const timestamp = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        bulkFixLogs = [...bulkFixLogs, `[${timestamp}] ${msg}`];
    }

    let copyrightScore = $derived(copyrightResult ? Math.round(copyrightResult.uniqueness_score * 100) : null);
    let seoScore = $derived(seoResult ? seoResult.total_score : null);
    let aiScore = $derived(aiReadyResult ? aiReadyResult.geo_score : null);
    
    // CNS V91.0: Professional Hierarchical Locks (Elite V2.2)
    let seoLocked = $derived(copyrightScore === null || copyrightScore < 60);
    let aiLocked = $derived(seoScore === null || seoScore < 60);
    let enrichLocked = $derived(aiScore === null || aiScore < 70);


    let editorAnnotations = $derived.by(() => {
        const tab = activeTab;
        if (!tab) return [];

        let source: AnalysisAnnotation[] = [];
        if (tab === 'copyright') source = copyrightResult?.annotations || [];
        else if (tab === 'seo') source = seoResult?.seo_annotations || [];
        else if (tab === 'ai') source = aiReadyResult?.ai_annotations || [];
        else if (tab === 'enrich') source = boosterAnnotations || [];

        return source.map((s: AnalysisAnnotation) => {
            const annotationType = s.type || (
                tab === 'seo' ? 'seo-info' : 
                tab === 'ai' ? 'geo-info' : 
                tab === 'enrich' ? 'enrich' : 
                'copyright'
            );
            return {
                text: s.text || '',
                type: annotationType,
                message: s.reason || s.message || 'Cần kiểm tra',
                source: s.source_url || '',
                severity: (s.severity || 'medium').toLowerCase()
            };
        });
    });
    
    // R110: Sync results back to parent for persistence (Product/Adhoc mode)
    $effect(() => {
        if (!config.onUpdate) return;
        // Trigger on any result change
        // CNS V87.5: Trigger reactivity for persistent sync
        const _trigger = [copyrightResult, seoResult, aiReadyResult, boosterAnnotations];
        
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
            if (boosterAnnotations && boosterAnnotations.length > 0) {
                cache.enrich = { hash: contentHash, at: now, data: $state.snapshot(boosterAnnotations) };
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

    async function saveAnalysisEvidence(category: string, data: Record<string, unknown> | unknown[]) {
        try {
            const cid = resolve(config.campaign_id);
            if (!cid || cid === 'adhoc') return;

            // [CNS V90.0] Batch Save: gộp save-report + metadata thành 1 HTTP call
            // Trước: 2 POST (save-report + metadata) = 2 RTT
            // Sau: 1 POST (batch-save) = 1 RTT — giảm 50% DB calls per analysis
            const dataObj = Array.isArray(data) ? {} as Record<string, unknown> : data;
            const score = category === 'copyright'
                ? (dataObj.uniqueness_score as number || 0)
                : category === 'seo'
                ? (dataObj.total_score as number || 0)
                : category === 'ai_inspect'
                ? (dataObj.geo_score as number || 0)
                : 0;

            const reportKey = category as 'copyright' | 'seo' | 'ai_inspect' | 'enrich' | 'rewrite';
            await xohiActions.batchSave(
                cid,
                { [reportKey]: data },
                {
                    [category]: {
                        timestamp: new Date().toISOString(),
                        score,
                        data
                    }
                }
            );
        } catch (e) {
            console.error("[Neural Vault] Batch save failed:", e);
        }
    }

    async function handleApiResponse<T>(res: GenericResponse<T | TaskAcceptedResponse>, targetSetter: (v: T) => void, category?: string) {
        const cid = resolve(config.campaign_id);
        if (res?.status === "accepted" && res.data && typeof res.data === 'object' && 'task_id' in res.data) {
            return 'accepted';
        } else if (res?.status === 'success' && res.data) {
            if (res.logs) bulkFixLogs = [...bulkFixLogs, ...(res.logs.filter(l => !bulkFixLogs.includes(l)))];
            targetSetter(res.data as T);
            bulkFixLogs = [...bulkFixLogs, "✅ Phân tích hoàn tất. Đã nạp dữ liệu Intelligence."];

            // [CNS V90.0] Batch Save: gom cả save-report lẫn evidence vào 1 call (thay 2 POST cũ)
            if (cid && cid !== 'adhoc' && category) {
                await saveAnalysisEvidence(category, res.data as Record<string, unknown>);
            }
            return 'success';
        }
        
        // Handle Error status
        const errorMsg = (res as unknown as Record<string, unknown>)?.message || "Lỗi phản hồi từ Neural Engine";
        console.error(`[Neural Engine] ${category} Error:`, res);
        bulkFixLogs = [...bulkFixLogs, `❌ Lỗi: ${errorMsg}`];
        return 'error';
    }

    // CNS V87.0: Real-time Thinking Feed — consumed directly from backend logs
    function startThinkingLogs(type: 'copyright' | 'seo' | 'ai') {
        // Mock intervals removed. HUD now renders bulkFixLogs which are updated 
        // in real-time from the backend stream.
    }
    function stopThinkingLogs() {
        // CNS V87.0: No-op, mock interval was removed.
    }

    async function runCopyrightCheck(force = false, skipSave = false) {
        if (isCopyrightLoading) return;
        if (isAdhoc) nanobot.updateCurrentData({ campaign_id: 'adhoc' });
        isCopyrightLoading = true; isBulkFixing = true; bulkFixStatus = "Đang quét..."; activeTab = 'copyright';
        boosterAnnotations = []; currentAnalysisStep = 0;
        bulkFixLogs = [];
        addTerminalLog("--- NEW SCAN: COPYRIGHT ---");
        addTerminalLog("🧠 Đang khởi động Neural Engine...");
        addTerminalLog("🔍 Đang trinh sát dữ liệu...");
        startThinkingLogs('copyright');
        let status: 'success' | 'accepted' | 'error' = 'error';
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const cid = resolve(config.campaign_id);
            const url = isAdhoc ? `/api/v1/content/analyze/copyright?force=${force}` : `/api/v1/content/campaigns/${cid}/analyze/copyright?force=${force}`;
            const body = isAdhoc ? { 
                content: (config.getContent ?? config.getEditedDraft)(),
                topic: resolve(config.topic) || '',
                content_type: resolve(config.contentType)
            } : undefined;
            const res = await apiClient.post<GenericResponse<CopyrightResult>>(url, body);
            status = await handleApiResponse<CopyrightResult>(res, (v) => { copyrightResult = v; }, 'copyright');
        } catch (e: unknown) {
            status = 'error';
            const errorObj = e as Error;
            bulkFixLogs = [...bulkFixLogs, `❌ Lỗi hệ thống: ${errorObj.message || String(e)}`];
            nanobot.showToast(`Lỗi Copyright: ${errorObj.message || String(e)}`, 'error');
        } finally {
            stopThinkingLogs();
            if (status !== 'accepted') {
                isCopyrightLoading = false;
                bulkFixStatus = status === 'success' ? "Hoàn tất ✅" : "Thất bại ❌";
                setTimeout(() => {
                    if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) {
                        isBulkFixing = false;
                        bulkFixStatus = "";
                    }
                }, 4000);
            }
        }
    }

    async function runSeoAnalysis(force = false, skipSave = false) {
        if (isSeoLoading) return;
        if (seoLocked) {
            nanobot.showToast(`[LOCK] Cấp độ tác chiến chưa đạt: Cần Uniqueness > 60% để mở khóa SEO Scan. (Hiện tại: ${copyrightScore ?? 0}%)`, "warning");
            return;
        }
        if (isAdhoc) nanobot.updateCurrentData({ campaign_id: 'adhoc' });
        isSeoLoading = true; isBulkFixing = true; bulkFixStatus = "Đang phân tích SEO..."; activeTab = 'seo';
        boosterAnnotations = []; currentAnalysisStep = 0;
        bulkFixLogs = [];
        addTerminalLog("--- NEW SCAN: SEO ---");
        addTerminalLog("🚀 Đang nạp bộ lọc SEO...");
        addTerminalLog("📊 Đang đánh giá tín hiệu...");
        startThinkingLogs('seo');
        let status: 'success' | 'accepted' | 'error' = 'error';
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const cid = resolve(config.campaign_id);
            const url = isAdhoc ? `/api/v1/content/analyze/seo?force=${force}` : `/api/v1/content/campaigns/${cid}/analyze/seo?force=${force}`;
            const body = isAdhoc ? { 
                content: (config.getContent ?? config.getEditedDraft)(), 
                topic: resolve(config.topic) || '',
                content_type: resolve(config.contentType)
            } : undefined;
            const res = await apiClient.post<GenericResponse<SEOResult>>(url, body);
            status = await handleApiResponse<SEOResult>(res, (v) => { seoResult = v; }, 'seo');
        } catch (e: unknown) {
            status = 'error';
            const errorObj = e as Error;
            bulkFixLogs = [...bulkFixLogs, `❌ Lỗi hệ thống: ${errorObj.message || String(e)}`];
            nanobot.showToast(`Lỗi SEO: ${errorObj.message || String(e)}`, 'error');
        } finally {
            stopThinkingLogs();
            if (status !== 'accepted') {
                isSeoLoading = false;
                bulkFixStatus = status === 'success' ? "Hoàn tất ✅" : "Thất bại ❌";
                setTimeout(() => {
                    if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) {
                        isBulkFixing = false;
                        bulkFixStatus = "";
                    }
                }, 4000);
            }
        }
    }

    async function runAiAnalysis(force = false, skipSave = false) {
        if (isAiLoading) return;
        if (aiLocked) {
            nanobot.showToast(`[LOCK] Tín hiệu SEO chưa đủ mạnh: Cần SEO Score > 60 để kích hoạt AI Mod. (Hiện tại: ${seoScore ?? 0})`, "warning");
            return;
        }
        if (isAdhoc) nanobot.updateCurrentData({ campaign_id: 'adhoc' });
        isAiLoading = true; isBulkFixing = true; bulkFixStatus = "Đang kiểm định AI..."; activeTab = 'ai';
        boosterAnnotations = []; currentAnalysisStep = 0;
        bulkFixLogs = [];
        addTerminalLog("--- NEW SCAN: VIRAL ---");
        addTerminalLog("🧠 Đang mở cổng Neural AI...");
        addTerminalLog("⚡ Đang kiểm tra Viral Edge...");
        startThinkingLogs('ai');
        let status: 'success' | 'accepted' | 'error' = 'error';
        try {
            if (!skipSave) await saveBeforeAnalysis();
            const cid = resolve(config.campaign_id);
            const url = isAdhoc ? `/api/v1/content/analyze/ai-inspect?force=${force}` : `/api/v1/content/campaigns/${cid}/analyze/ai-inspect?force=${force}`;
            const body = isAdhoc ? { 
                content: (config.getContent ?? config.getEditedDraft)(),
                topic: resolve(config.topic) || '',
                content_type: resolve(config.contentType)
            } : undefined;
            const res = await apiClient.post<GenericResponse<AIInspectResult>>(url, body);
            status = await handleApiResponse<AIInspectResult>(res, (v) => { 
                const oldFixed = (aiReadyResult?.ai_annotations || []).filter(a => a.type === 'fixed-area');
                v.ai_annotations = [...oldFixed, ...(v.ai_annotations || [])];
                aiReadyResult = v;
            }, 'ai_inspect');
        } catch (e: unknown) {
            status = 'error';
            const errorObj = e as Error;
            bulkFixLogs = [...bulkFixLogs, `❌ Lỗi hệ thống: ${errorObj.message || String(e)}`];
            nanobot.showToast(`Lỗi AI Mod: ${errorObj.message || String(e)}`, 'error');
        } finally {
            stopThinkingLogs();
            if (status !== 'accepted') {
                isAiLoading = false;
                bulkFixStatus = status === 'success' ? "Hoàn tất ✅" : "Thất bại ❌";
                setTimeout(() => {
                    if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) {
                        isBulkFixing = false;
                        bulkFixStatus = "";
                    }
                }, 4000);
            }
        }
    }

    // CNS V88.4: rawContent is passed directly from TiptapEditor (current editor HTML)
    // to avoid stale editBuffer. TiptapEditor handles applying the result to the editor.
    async function runCleanContent(options?: CleanOptions, rawContent?: string) {
        if (_bulkFixRunning) return null;
        _bulkFixRunning = true;
        isBulkFixing = true; bulkFixStatus = "Đang dọn dẹp...";
        bulkFixLogs = [];
        addTerminalLog("🚀 Đang khởi động Neural clean...");
        addTerminalLog("🧠 Đang dọn dẹp artifacts...");
        try {
            // Prefer rawContent (from editor) over editBuffer to avoid stale state
            const content = rawContent ?? (config.getContent ?? config.getEditedDraft)?.() ?? '';
            const cleaned = await xohiActions.runClean(content, options);
            
            if (cleaned && cleaned !== content) {
                // Always sync editBuffer/content for persistence — TiptapEditor applies to editor separately
                if (resolve(config.isEditing)) config.setEditedDraft(cleaned);
                else config.setDraftContent(cleaned);
                addTerminalLog("🎯 Đã dọn dẹp & tối ưu cấu trúc thành công ✅");
                nanobot.showToast("Đã dọn dẹp & tối ưu cấu trúc thành công!", "success");
            } else {
                addTerminalLog("✨ Nội dung đã ở trạng thái tối ưu, không cần dọn dẹp thêm.");
                nanobot.showToast("Nội dung đã ở trạng thái tối ưu.", "info");
            }
            bulkFixStatus = "Hoàn tất ✅";
            return cleaned; // TiptapEditor's handleClean uses this return value to applyContentToEditor
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            addTerminalLog(`❌ Lỗi: ${msg}`);
            bulkFixStatus = "Thất bại ❌";
            nanobot.showToast(`Lỗi dọn dẹp: ${msg}`, 'error');
            return null;
        } finally {
            _bulkFixRunning = false;
            setTimeout(() => { 
                if (!isCopyrightLoading && !isSeoLoading && !isAiLoading) {
                    isBulkFixing = false;
                    bulkFixStatus = "";
                }
            }, 4000);
        }
    }

    async function runAutoFix(target: string, type: string, msg: string) {
        // Guard: prevent double-call (CLAUDE.md)
        if (streamingTarget) return null;

        const cid = resolve(config.campaign_id);
        const topic = resolve(config.topic) ?? '';
        const content = (config.getContent ?? config.getEditedDraft)?.() ?? '';

        // CNS V87.0: Dùng SSE streaming để typewriter effect ngay trong annotation row
        return new Promise<string | null>((resolve_p) => {
            streamingTarget = target;
            streamingText = '';

            const cleanup = async (newText: string | null) => {
                // CLAUDE.md: Dispose SSE resource ngay khi xong
                _sseAbort?.abort();
                _sseAbort = null;
                streamingTarget = null;

                if (newText) {
                    // CNS V88.2: Surgical apply với Neural Stitching (HTML-Aware)
                    const currentContent = (config.getContent ?? config.getEditedDraft)?.() ?? '';
                    const updated = refinementStitch(currentContent, target, newText);
                    
                    if (updated !== currentContent) {
                        if (resolve(config.isEditing)) config.setEditedDraft(updated);
                        else config.setDraftContent(updated);
                        
                        // [CRITICAL] Đồng bộ ngay lên DB để tránh F5 bị mất
                        if (cid && cid !== 'adhoc') {
                            apiClient.patch(`/api/v1/content/campaigns/${cid}`, { draft_content: updated }).catch(e => {
                                console.error("[Neural Vault] Persistence failed:", e);
                            });
                        }
                    }
                    // Xóa annotation đã sửa
                    // CNS V88.2: Robust Matcher using alphanumeric normalization
                    const match = (a: AnalysisAnnotation) => {
                        const nt = robustNormalize(target);
                        const na = robustNormalize(a.text || '');
                        const nm = (a.message || a.reason || '').toLowerCase().trim();
                        const targetM = (msg || '').toLowerCase().trim();
                        
                        const textMatch = (na.includes(nt) || nt.includes(na)) && nt.length > 5;
                        const msgMatch = nm.includes(targetM) || targetM.includes(nm);
                        const typeMatch = a.type?.split('-')[0] === type?.split('-')[0]; // Allow seo-warning to match seo

                        return textMatch && (msgMatch || typeMatch);
                    };

                    if (seoResult) {
                        seoResult.seo_annotations = (seoResult.seo_annotations || []).filter(a => !match(a));
                        saveAnalysisEvidence('seo', $state.snapshot(seoResult));
                    }
                    if (aiReadyResult) {
                        aiReadyResult.ai_annotations = (aiReadyResult.ai_annotations || []).filter(a => !match(a));
                        saveAnalysisEvidence('ai_inspect', $state.snapshot(aiReadyResult));
                    }
                    if (copyrightResult) {
                        copyrightResult.annotations = (copyrightResult.annotations || []).filter(a => !match(a));
                        saveAnalysisEvidence('copyright', $state.snapshot(copyrightResult));
                    }

                    // CNS V96.0: Handle Booster Annotations (Lock button & Keep Highlight)
                    if (boosterAnnotations.length > 0) {
                        boosterAnnotations = boosterAnnotations.map(a => {
                            if (match(a)) {
                                return { 
                                    ...a, 
                                    is_applied: true, 
                                    // CNS V96.5: Surgical Highlight — only highlight the NEW part
                                    text: extractBoostedText(a.replacement_string || a.text)
                                };
                            }
                            return a;
                        });
                        saveAnalysisEvidence('enrich', boosterAnnotations);
                    }
                }
                resolve_p(newText);
            };

            // Campaign mode: có campaign_id thì dùng SSE stream
            // Ad-hoc mode: không có campaign_id cũng dùng SSE stream (endpoint mới hỗ trợ cả 2)
            _sseAbort = xohiActions.streamAutoFix(
                content,
                target,
                msg,
                topic,
                (chunk) => { streamingText += chunk; },
                (fullText) => { cleanup(fullText || null); },
                (err) => { nanobot.showToast(`Lỗi sửa: ${err}`, 'error'); cleanup(null); },
            );
        });
    }

    let _bulkFixRunning = false; // CNS V88.3: Dedicated guard — tách khỏi isBulkFixing (HUD indicator)
    async function runBulkFix() {
        if (_bulkFixRunning || !activeTab) return;
        const cid = resolve(config.campaign_id);
        const category = activeTab === 'copyright' ? 'copyright' : activeTab === 'seo' ? 'seo' : 'ai';
        const annotations = ((activeTab === 'copyright' ? copyrightResult?.annotations : activeTab === 'seo' ? seoResult?.seo_annotations : aiReadyResult?.ai_annotations) || []).filter(a => a.type !== 'fixed-area');
        if (annotations.length === 0) {
            nanobot.showToast("Không tìm thấy vấn đề nào cần sửa", "info");
            return;
        }

        _bulkFixRunning = true; // CNS V88.3: Guard chặn double-click
        isBulkFixing = true; bulkFixStatus = "Đang tinh chỉnh..."; currentAnalysisStep = 0;
        if (isAdhoc) nanobot.updateCurrentData({ campaign_id: 'adhoc' });
        bulkFixLogs = [];
        addTerminalLog("Đang khởi tạo Neural Engine...");
        addTerminalLog("Đang phân tích cấu trúc...");
        console.log(`[Neural Engine] Starting Bulk Fix for category: ${category}, Ad-hoc: ${isAdhoc}`);

        try {
            const payload = isAdhoc 
                ? { content: (config.getContent ?? config.getEditedDraft)(), topic: resolve(config.topic), category, annotations } 
                : { category, annotations };
            
            const res = await xohiActions.runBulkFix(cid || null, isAdhoc, payload);
            
            if (res?.status === 'success' && res.data?.new_content) {
                console.log("[Neural Engine] Bulk Fix successful, applying patches...");
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
                if (activeTab === 'copyright') {
                    // Update annotations temporarily to show "Đã sửa" status
                    copyrightResult = { ...copyrightResult!, annotations: [...fixed, ...remaining] };
                    await saveAnalysisEvidence('copyright', $state.snapshot(copyrightResult));
                    
                    // CNS V96: Auto-trigger Copyright Check to update the score and verdict
                    bulkFixLogs = [...bulkFixLogs, "⏳ Đang chạy lại kiểm định bản quyền để cập nhật báo cáo..."];
                    setTimeout(() => {
                        runCopyrightCheck(true);
                    }, 500);
                }
                else if (activeTab === 'seo') {
                    seoResult = { ...seoResult!, seo_annotations: [...fixed, ...remaining] };
                    await saveAnalysisEvidence('seo', $state.snapshot(seoResult));
                    setTimeout(() => { runSeoAnalysis(true); }, 500);
                }
                else {
                    aiReadyResult = { ...aiReadyResult!, ai_annotations: [...fixed, ...remaining] };
                    await saveAnalysisEvidence('ai_inspect', $state.snapshot(aiReadyResult));
                    setTimeout(() => { runAiAnalysis(true); }, 500);
                }
                addTerminalLog("✅ Tinh chỉnh hoàn tất. Dữ liệu Neural Intelligence đã được cập nhật.");
                bulkFixStatus = "Hoàn tất ✅";
            } else {
                const msg = (res as { message?: string })?.message || "Không thể thực hiện tinh chỉnh hàng loạt";
                console.error("[Neural Engine] Bulk Fix Error:", res);
                bulkFixLogs = [...bulkFixLogs, `❌ Lỗi: ${msg}`];
                bulkFixStatus = "Thất bại ❌";
                nanobot.showToast(msg, "error");
            }
        } catch (e: unknown) {
            console.error("[Neural Engine] Bulk Fix Critical Error:", e);
            const errorObj = e as Error;
            const errorMsg = errorObj.message || String(e);
            bulkFixLogs = [...bulkFixLogs, `❌ Lỗi hệ thống: ${errorMsg}`];
            bulkFixStatus = "Thất bại ❌";
            nanobot.showToast(`Lỗi Neural Engine: ${errorMsg}`, "error");
        } finally {
            _bulkFixRunning = false; // CNS V88.3: Mở khóa guard
            // CNS V87.4: 'Treo' (Persist) the HUD for 4s after completion so user can read logs
            setTimeout(() => { 
                isBulkFixing = false;
                if (bulkFixStatus === "Hoàn tất ✅" || bulkFixStatus === "Thất bại ❌") {
                    bulkFixStatus = ""; 
                }
            }, 4000);
        }
    }

    async function runAiBooster() {
        if (isBoosting) return;
        if (enrichLocked) {
            nanobot.showToast(`[LOCK] Chưa đạt AI Readiness: Cần Viral Score > 70 để sử dụng AI Booster. (Hiện tại: ${aiScore ?? 0})`, "warning");
            return;
        }
        const cid = resolve(config.campaign_id);
        const content = (config.getContent ?? config.getEditedDraft)?.() ?? '';
        const topic = resolve(config.topic) ?? '';
        isBoosting = true; isBulkFixing = true; bulkFixStatus = "Đang tinh chỉnh..."; activeTab = 'enrich'; currentAnalysisStep = 0;
        bulkFixLogs = [];
        addTerminalLog("🚀 Neural Booster khởi động...");
        addTerminalLog("🧠 Đang phân tích cấu trúc nội dung...");

        try {
            if (!isAdhoc && cid) {
                // [CNS V90.0 Plan B] Campaign mode: Enrich — KHÔNG chain runSeoAnalysis nữa!
                // Trước: Enrich + runSeoAnalysis(force=true) = 2 Google + 2 LLM calls
                // Sau: Enrich only, merge annotations vào seoResult = 1 Google + 1 LLM call
                await saveBeforeAnalysis();
                const res = await xohiActions.runEnrich(cid);
                if (res?.status === 'success' && res.data?.new_content) {
                    if (res.logs) bulkFixLogs = [...bulkFixLogs, ...res.logs];
                    
                    // CNS V96.5: Strip surgical tags from the final content before setting to editor
                    const cleanHtml = stripBoostTags(res.data.new_content);
                    config.setEditedDraft(cleanHtml);

                    if (res.data.annotations?.length) {
                        const ann = res.data.annotations.map(a => ({
                            ...a,
                            // If backend already applied it, we ensure highlight is surgical
                            text: extractBoostedText(a.replacement_string || a.text)
                        }));
                        if (!seoResult) seoResult = { total_score: 0, grade: 'N/A', signals: [], summary: '', quick_wins: [], seo_annotations: ann, logs: [] };
                        else seoResult = { ...seoResult, seo_annotations: [...(seoResult.seo_annotations || []), ...ann] };
                    }
                    activeTab = 'seo';
                    // [CNS V91.2] Save enriched seoResult to DB immediately
                    if (seoResult) await saveAnalysisEvidence('seo', $state.snapshot(seoResult));
                    bulkFixStatus = "Hoàn tất ✅";
                    bulkFixLogs = [...bulkFixLogs, "🎯 AI Booster hoàn tất. Nội dung đã được làm giàu."];
                    nanobot.showToast("AI Booster đã làm giàu nội dung!", "success");
                } else {
                    const msg = (res as GenericResponse).message || "Enrichment failed";
                    bulkFixLogs = [...bulkFixLogs, `❌ Lỗi: ${msg}`];
                    bulkFixStatus = "Thất bại ❌";
                    nanobot.showToast(msg, 'error');
                }
            } else {
                // [CNS V90.0 Plan B] Ad-hoc mode — Surgeon Booster (không cần Google Search)
                // CNS V92.1: Truyền contentType để backend phân biệt đúng product vs article
                const contentType = resolve(config.contentType) || 'article';
                const res = await xohiActions.runNeuralBoost(content, topic, contentType);
                if (res?.status === 'success' && res.data?.patches) {
                    bulkFixLogs = [...bulkFixLogs, `✅ Hoàn tất! Đã tìm thấy ${res.data.patches.length} điểm tinh chỉnh.`, ...res.data.logs];

                    // CNS V92.0: Lưu clinical sources (nguồn lâm sàng đã dịch VI)
                    const rawSources = (res.data as unknown as Record<string, unknown>)?.clinical_sources;
                    if (Array.isArray(rawSources) && rawSources.length > 0) {
                        clinicalSources = rawSources as ClinicalSource[];
                        bulkFixLogs = [...bulkFixLogs, `📚 Đã trinh sát ${clinicalSources.length} nghiên cứu & bài báo uy tín (J-STAGE / PubMed / PMDA / Cosme).`];
                    } else {
                        clinicalSources = [];
                    }
                    
                    // CNS V96.0: Stop auto-apply. Just store patches for user review ("Duyệt nới thêm vào")
                    const newAnnotations: AnalysisAnnotation[] = [];
                    
                    for (const patch of res.data.patches) {
                        // Always add to annotations so user can see what AI suggested, 
                        // but only highlight if it still exists in content
                        newAnnotations.push({
                            text: patch.search_string, // Anchor to original text
                            type: 'enrich',
                            message: patch.rationale,
                            severity: 'low',
                            search_string: patch.search_string,
                            replacement_string: patch.replacement_string
                        });
                    }

                    if (newAnnotations.length > 0) {
                        boosterAnnotations = newAnnotations;
                        activeTab = 'enrich';
                        
                        bulkFixStatus = "Hoàn tất ✅";
                        await saveAnalysisEvidence('enrich', boosterAnnotations);
                        nanobot.showToast(`Phát hiện ${newAnnotations.length} cơ hội bổ sung dữ liệu`, 'success');
                    } else {
                        bulkFixLogs = [...bulkFixLogs, "⚠️ Không tìm thấy cơ hội bổ sung dữ liệu nào."];
                        bulkFixStatus = "Hoàn tất ✅";
                    }
                } else {
                    const msg = (res as unknown as Record<string, unknown>)?.message || "Surgeon Booster failed";
                    bulkFixLogs = [...bulkFixLogs, `❌ Lỗi: ${msg}`];
                    bulkFixStatus = "Thất bại ❌";
                    nanobot.showToast(msg as string, 'error');
                }
            }
        } catch (e: unknown) {
            console.error("[Neural Engine] AI Booster Error:", e);
            const errorObj = e as Error;
            bulkFixLogs = [...bulkFixLogs, `❌ Lỗi hệ thống: ${errorObj.message || String(e)}`];
            bulkFixStatus = "Thất bại ❌";
            nanobot.showToast(`Lỗi Booster: ${errorObj.message || String(e)}`, 'error');
        } finally {
            isBoosting = false;
            setTimeout(() => { 
                isBulkFixing = false; 
                if (bulkFixStatus === "Hoàn tất ✅") {
                    bulkFixStatus = ""; 
                }
            }, 3500);
        }
    }

    async function runBulkBoosterFix() {
        if (isBulkFixing || boosterAnnotations.length === 0) return;
        const pending = boosterAnnotations.filter(a => !a.is_applied);
        if (pending.length === 0) {
            nanobot.showToast("Tất cả đã được duyệt ✅", "info");
            return;
        }

        isBulkFixing = true;
        bulkFixStatus = "Đang phẫu thuật tổng thể...";
        bulkFixLogs = [...bulkFixLogs, `🚀 Khởi động quy trình duyệt hàng loạt (${pending.length} điểm)...` ];

        try {
            let content = (config.getContent ?? config.getEditedDraft)?.() ?? '';
            let appliedCount = 0;

            // Deep clone annotations to update them reactively
            const updatedAnnotations = boosterAnnotations.map(a => ({ ...a }));

            for (const ann of updatedAnnotations) {
                if (ann.is_applied) continue;

                const target = ann.search_string || ann.text;
                const replacement = ann.replacement_string || '';
                
                if (content.includes(target) || robustNormalize(content).includes(robustNormalize(target))) {
                    content = refinementStitch(content, target, replacement);
                    ann.is_applied = true;
                    // CNS V96.5: Surgical Highlight — only highlight the NEW part
                    ann.text = extractBoostedText(replacement); 
                    appliedCount++;
                    addTerminalLog(`✅ Đã phẫu thuật: ${ann.message?.slice(0, 30)}...`);
                }
            }

            if (appliedCount > 0) {
                if (resolve(config.isEditing)) config.setEditedDraft(content);
                else config.setDraftContent(content);

                boosterAnnotations = updatedAnnotations;
                await saveAnalysisEvidence('enrich', boosterAnnotations);
                
                // Persistence
                const cid = resolve(config.campaign_id);
                if (cid && cid !== 'adhoc') {
                    await apiClient.patch(`/api/v1/content/campaigns/${cid}`, { draft_content: content }).catch(e => {
                        console.error("[Neural Vault] Persistence failed:", e);
                    });
                }

                nanobot.showToast(`Đã duyệt & nối thêm ${appliedCount} đoạn văn thành công!`, "success");
                bulkFixStatus = "Hoàn tất ✅";
            }
        } catch (e) {
            console.error("[Neural Engine] Bulk Booster Error:", e);
            bulkFixStatus = "Thất bại ❌";
        } finally {
            setTimeout(() => { isBulkFixing = false; bulkFixStatus = ""; }, 3000);
        }
    }

    async function runNeuralRewrite(overrideContent?: string) {
        if (isBulkFixing || !copyrightResult) return;
        
        const cid = resolve(config.campaign_id);
        const topic = resolve(config.topic) ?? '';
        const content = overrideContent ?? (config.getContent ?? config.getEditedDraft)?.() ?? '';
        const feedback = copyrightResult.verdict;
        const contentType = resolve(config.contentType) ?? 'article';
        const metadata = resolve(config.getMetadata) ?? null;

        isRewriting = true;
        isBulkFixing = true;
        bulkFixStatus = "Đang múa bút...";
        bulkFixLogs = [];
        addTerminalLog("🔥 Kích hoạt Xohi Creative Rewrite...");
        addTerminalLog("🧠 Đang nạp luận điểm phản biện...");
        addTerminalLog("🖋️ Đang tái cấu trúc nội dung sáng tạo...");

        try {
            const payload = { 
                content, 
                topic, 
                feedback,
                content_type: contentType,
                metadata,
                user_note: userPlanNote // CNS V90.1: Pass user-guided plan notes
            };
            const res = await apiClient.post<GenericResponse<{ new_content: string }>>(`/api/v1/content/analyze/neural-rewrite${cid ? `?campaign_id=${cid}` : ''}`, payload);

            if (res?.status === 'success' && res.data?.new_content) {
                const newHtml = res.data.new_content;
                
                if (!isAdhoc && cid) {
                    await apiClient.patch(`/api/v1/content/campaigns/${cid}`, { draft_content: newHtml });
                }
                
                if (resolve(config.isEditing)) config.setEditedDraft(newHtml);
                else config.setDraftContent(newHtml);

                bulkFixLogs = [...bulkFixLogs, "✅ Hoàn tất tinh chỉnh sáng tạo!", "✨ Bài viết mới đã được cập nhật."];
                bulkFixStatus = "Hoàn tất ✅";

                // [CNS V91.2] Save rewrite evidence so dashboard knows this content was AI-rewritten
                await saveAnalysisEvidence('rewrite', { rewritten_at: new Date().toISOString(), topic });
                
                // CNS V91.0: Invalidate stale results after rewrite
                copyrightResult = null;
                seoResult = null;
                aiReadyResult = null;

                nanobot.showToast("Xohi đã viết lại bài mới thành công!", "success");
            } else {
                const msg = res?.message || "Không thể viết lại nội dung";
                bulkFixLogs = [...bulkFixLogs, `❌ Lỗi: ${msg}`];
                bulkFixStatus = "Thất bại ❌";
                nanobot.showToast(msg, 'error');
            }
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            bulkFixLogs = [...bulkFixLogs, `❌ Lỗi hệ thống: ${msg}`];
            bulkFixStatus = "Thất bại ❌";
            nanobot.showToast(`Lỗi Rewrite: ${msg}`, 'error');
        } finally {
            setTimeout(() => { 
                isRewriting = false;
                isBulkFixing = false; 
                if (bulkFixStatus === "Hoàn tất ✅" || bulkFixStatus === "Thất bại ❌") {
                    bulkFixStatus = ""; 
                }
            }, 4000);
        }
    }

    // CNS V86.5/V87.0: Hydrate — Khôi phục kết quả phân tích từ DB (ưu tiên) hoặc cache sau F5
    // CRITICAL FIX: One-shot hydration — chỉ nạp 1 lần khi mount, KHÔNG BAO GIỜ đè kết quả real-time
    let _hydrated = false;
    $effect(() => {
        const cache = resolve(config.analysis_cache);
        const dbReport = (resolve(config.campaign_id) ? resolve(config.analysis_report) : null) as Record<string, Record<string, unknown>> | null;
        
        untrack(() => {
            // Guard: Nếu đã hydrate rồi hoặc đang có analysis chạy, KHÔNG đè
            if (_hydrated) return;
            if (isCopyrightLoading || isSeoLoading || isAiLoading || isBulkFixing) return;

            // Helper để lấy data: ưu tiên DB report nếu có, fallback về cache
            const getD = (key: string) => {
                if (dbReport?.[key]?.data) return dbReport[key].data;
                if (cache?.[key]?.data) return cache[key].data;
                return null;
            };

            const cr = getD('copyright');
            if (cr && !copyrightResult) {
                copyrightResult = cr as CopyrightResult;
            }

            const sr = getD('seo');
            if (sr && !seoResult) {
                seoResult = sr as SEOResult;
            }

            const ar = getD('ai_inspect');
            if (ar && !aiReadyResult) {
                aiReadyResult = ar as AIInspectResult;
            }

            const en = getD('enrich');
            if (en && (!boosterAnnotations || boosterAnnotations.length === 0)) {
                boosterAnnotations = en as AnalysisAnnotation[];
            }

            // Tự động chọn tab nếu chưa có
            if (activeTab === null) {
                if (copyrightResult?.annotations?.length) activeTab = 'copyright';
                else if (seoResult?.seo_annotations?.length) activeTab = 'seo';
                else if (aiReadyResult?.ai_annotations?.length) activeTab = 'ai';
                else if (boosterAnnotations?.length) activeTab = 'enrich';
            }

            // Đánh dấu đã hydrate xong — không bao giờ chạy lại
            _hydrated = true;
        });
    });


    $effect(() => {
        if (bulkFixLogs.length > 0) {
            const lastLog = bulkFixLogs[bulkFixLogs.length - 1];
            const isDone = lastLog.includes("ĐÃ XỬ LÝ XONG") || 
                           lastLog.includes("ĐANG ĐỒNG BỘ GIAO DIỆN") || 
                           lastLog.includes("Đã dọn dẹp xong") ||
                           lastLog.includes("hoàn tất!") ||
                           lastLog.includes("sẵn sàng.");

            if (isDone) {
                untrack(() => {
                    if (isCopyrightLoading) isCopyrightLoading = false;
                    if (isSeoLoading) isSeoLoading = false;
                    if (isAiLoading) isAiLoading = false;
                    
                    if (isBulkFixing) {
                        bulkFixStatus = "Hoàn tất ✅";
                        setTimeout(() => {
                            isBulkFixing = false;
                            bulkFixStatus = "";
                        }, 4000);
                    }
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
        get currentAnalysisStep() { return currentAnalysisStep; },
        get isBoosting() { return isBoosting; },
        get isRewriting() { return isRewriting; },
        get activeTab() { return activeTab; },
        set activeTab(v) { activeTab = v; },
        get userPlanNote() { return userPlanNote; },
        set userPlanNote(v) { userPlanNote = v; },
        get copyrightScore() { return copyrightScore; },
        get seoScore() { return seoScore; },
        get aiScore() { return aiScore; },
        get seoLocked() { return seoLocked; },
        get aiLocked() { return aiLocked; },
        get editorAnnotations() { return editorAnnotations; },
        get boosterAnnotations() { return boosterAnnotations; },
        get clinicalSources() { return clinicalSources; },  // CNS V92.0
        // CNS V87.0: expose streaming state cho UI typewriter effect
        get streamingText() { return streamingText; },
        get streamingTarget() { return streamingTarget; },
        runCopyrightCheck, runSeoAnalysis, runAiAnalysis, runAutoFix, runCleanContent, runBulkFix, runAiBooster, runBulkBoosterFix, runNeuralRewrite, dispose: () => {
            // CLAUDE.md: dispose SSE resource khi component unmount
            _sseAbort?.abort(); _sseAbort = null;
            copyrightResult = null; seoResult = null; aiReadyResult = null; bulkFixStatus = ""; activeTab = null;
            streamingText = ""; streamingTarget = null; clinicalSources = [];  // CNS V92.0: reset
        }
    };
}
