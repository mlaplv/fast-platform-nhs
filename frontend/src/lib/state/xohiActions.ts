import { apiClient } from "$lib/utils/apiClient";
import type { 
    GenericResponse, 
    BulkFixReplacement, 
    AnalysisAnnotation, 
    CopyrightResult, 
    SEOResult, 
    AIInspectResult,
    CleanOptions
} from "$lib/state/types";

// Re-export CleanOptions so components can import it from here (backward compat)
export type { CleanOptions } from "$lib/state/types";




/**
 * Elite V2.2: Core API Actions for Xohi Analysis
 */
export const xohiActions = {
    async runClean(content: string, options?: CleanOptions) {
        const res = await apiClient.post<GenericResponse<{ content: string }>>('/api/v1/content/clean', { 
            content,
            options
        });
        return res?.data?.content || content;
    },

    async runAutoFix(cid: string, targetSnippet: string, annotationType: string, errorMessage: string) {
        const res = await apiClient.post<GenericResponse<{ new_text: string }>>(`/api/v1/content/campaigns/${cid}/analyze/auto-fix`, {
            target_snippet: targetSnippet,
            annotation_type: annotationType,
            error_message: errorMessage,
        });
        return res?.status === 'success' ? res.data?.new_text : null;
    },

    // CNS V86.5: Ad-hoc auto-fix — không cần campaign_id (dùng cho ProductForm/NewsForm)
    async runAdHocAutoFix(content: string, targetSnippet: string, annotationType: string, errorMessage: string, topic?: string) {
        const res = await apiClient.post<GenericResponse<{ new_text: string }>>(`/api/v1/content/analyze/auto-fix`, {
            content,
            target_snippet: targetSnippet,
            annotation_type: annotationType,
            error_message: errorMessage,
            topic: topic ?? '',
        });
        return res?.status === 'success' ? res.data?.new_text : null;
    },

    // CNS V87.0: SSE streaming auto-fix — dùng fetch + ReadableStream (hỗ trợ header auth)
    // onChunk: callback nhận từng text delta; onDone: callback nhận full text
    // Trả về AbortController để caller có thể cancel (CLAUDE.md: dispose resources)
    streamAutoFix(
        content: string,
        targetSnippet: string,
        errorMessage: string,
        topic: string,
        onChunk: (chunk: string) => void,
        onDone: (fullText: string) => void,
        onError: (err: string) => void,
    ): AbortController {
        const controller = new AbortController();
        const url = `/api/v1/content/analyze/auto-fix-stream`;

        (async () => {
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    signal: controller.signal,
                    headers: { 
                        'Accept': 'text/event-stream',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        content: content, // Không slice nữa, POST cân được hết
                        target_snippet: targetSnippet,
                        error_message: errorMessage,
                        topic,
                    }),
                    credentials: 'include',
                });
                if (!res.ok || !res.body) {
                    onError(`HTTP ${res.status}`);
                    return;
                }
                const reader = res.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop() ?? '';
                    for (const line of lines) {
                        if (!line.startsWith('data: ')) continue;
                        try {
                            const parsed = JSON.parse(line.slice(6)) as { chunk?: string; done?: boolean; full?: string; error?: string };
                            if (parsed.error) { onError(parsed.error); return; }
                            if (parsed.chunk) onChunk(parsed.chunk);
                            if (parsed.done && parsed.full) { onDone(parsed.full); return; }
                        } catch { /* skip malformed */ }
                    }
                }
            } catch (err: unknown) {
                if (err instanceof Error && err.name !== 'AbortError') onError(err.message);
            }
        })();

        return controller;
    },

    // CNS V87.0: Neural Boost — tinh chỉnh toàn bộ content, trả về ContentPatch list
    // CNS V92.1: Truyền contentType để phân biệt product vs article
    async runNeuralBoost(content: string, topic: string, contentType: string = 'article') {
        type Patch = { search_string: string; replacement_string: string; rationale: string };
        type Report = { patches: Patch[]; summary: string; logs: string[] };
        const res = await apiClient.post<GenericResponse<Report>>(`/api/v1/content/analyze/neural-boost`, {
            content,
            topic,
            content_type: contentType,
        });
        return res;
    },

    async saveAnalysisReport(cid: string, type: 'copyright' | 'seo' | 'ai_inspect' | 'refinement', data: unknown) {
        const res = await apiClient.post<GenericResponse>(`/api/v1/content/campaigns/${cid}/analyze/save-report`, {
            report_type: type,
            data,
        });
        return res;
    },

    async runBulkFix(cid: string | null, isAdhoc: boolean, payload: { category: string, annotations: AnalysisAnnotation[], content?: string, topic?: string }) {
        const url = isAdhoc ? `/api/v1/content/analyze/bulk-fix` : `/api/v1/content/campaigns/${cid}/analyze/bulk-fix`;
        const res = await apiClient.post<GenericResponse<{ new_content: string, logs?: string[], replacements: BulkFixReplacement[] }>>(url, payload);
        return res;
    },

    async runEnrich(cid: string) {
        const res = await apiClient.post<GenericResponse<{ 
            new_content: string, 
            logs?: string[], 
            items?: Record<string, unknown>[],
            annotations?: AnalysisAnnotation[]
        }>>(`/api/v1/content/campaigns/${cid}/analyze/enrich`, {});
        return res;
    },

    /**
     * [CNS V90.0] Batch Save — Gộp save-report + metadata thành 1 HTTP call.
     * Tiết kiệm 1 HTTP round-trip per analysis (từ 2 POST → 1 POST).
     */
    async batchSave(
        cid: string,
        reports: Partial<Record<'copyright' | 'seo' | 'ai_inspect' | 'refinement' | 'enrich' | 'rewrite', unknown>>,
        evidence: Partial<Record<string, { score: number; timestamp: string; data: unknown }>>
    ) {
        const res = await apiClient.post<GenericResponse>(
            `/api/v1/content/campaigns/${cid}/analyze/batch-save`,
            { reports, evidence }
        );
        return res;
    }
};
