import { apiClient } from "$lib/utils/apiClient";
import type { 
    GenericResponse, 
    BulkFixReplacement, 
    AnalysisAnnotation, 
    CopyrightResult, 
    SEOResult, 
    AIInspectResult,
    EnrichmentItem
} from "$lib/state/types";

export interface CleanOptions {
    stripFont?: boolean;
    stripAlign?: boolean;
    stripRedundantWrappers?: boolean;
    stripEmpty?: boolean;
}

/**
 * Elite V2.2: Neural Clean (Deterministic logic extracted for maintainability)
 */
export function cleanHtmlContent(content: string, options: CleanOptions = { stripFont: true, stripAlign: true, stripRedundantWrappers: true, stripEmpty: true }): string {
    if (typeof document === 'undefined') return content;
    
    const div = document.createElement('div');
    div.innerHTML = content;

    let changed = true;
    let passes = 0;

    // Deterministic Loop: Repeat until no more changes occur (max 10 passes)
    while (changed && passes < 10) {
        changed = false;
        passes++;

        // Step A: Remove redundant BR tags
        div.querySelectorAll('br + br').forEach(el => { el.remove(); changed = true; });

        // Step B: Bottom-up Recursive Pruning
        const allNodes = Array.from(div.querySelectorAll('*')).reverse();

        allNodes.forEach(node => {
            if (!(node instanceof HTMLElement)) return;

            // Option 1: Strip Font Family
            if (options.stripFont && node.style.fontFamily) {
                node.style.fontFamily = '';
                changed = true;
            }

            // Option 2: Strip Text Align
            if (options.stripAlign && node.style.textAlign) {
                node.style.textAlign = '';
                changed = true;
            }

            // Cleanup empty style attribute
            if (node.getAttribute('style')?.trim() === '' || node.getAttribute('style') === ';') {
                node.removeAttribute('style');
                changed = true;
            }

            const text = node.textContent?.replace(/[\s\u00A0\u200B\uFEFF\t\n\r]+/g, '').trim() || '';
            const hasMedia = node.querySelector('img, iframe, video, audio, picture, canvas, svg, [data-media]');
            const hasFunctional = node.querySelector('input, button, select, textarea');
            const hasMeaningfulAttr = (node.tagName === 'A' && node.getAttribute('href')) || node.getAttribute('id') || node.getAttribute('name');

            // Option 3: Strip Redundant Wrappers (spans/divs without attributes)
            if (options.stripRedundantWrappers && (node.tagName === 'SPAN' || node.tagName === 'DIV') && node.attributes.length === 0) {
                node.replaceWith(...Array.from(node.childNodes));
                changed = true;
                return;
            }

            // Option 4: Prune Empty Containers
            const isContainer = ['P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'STRONG', 'B', 'EM', 'I', 'SPAN', 'BLOCKQUOTE', 'LI', 'SECTION', 'ARTICLE'].includes(node.tagName);
            const isEffectivelyEmpty = !text && !hasMedia && !hasFunctional && !hasMeaningfulAttr;

            if (options.stripEmpty && isContainer && isEffectivelyEmpty) {
                node.remove();
                changed = true;
            } else if (node.tagName === 'BR' && node.parentNode?.childNodes.length === 1 && isContainer) {
                node.parentNode.removeChild(node);
                changed = true;
            }
        });
    }
    return div.innerHTML;
}

/**
 * Elite V2.2: Core API Actions for Xohi Analysis
 */
export const xohiActions = {
    async runClean(content: string, options?: CleanOptions) {
        const preCleaned = cleanHtmlContent(content, options);
        const res = await apiClient.post<GenericResponse<{ content: string }>>('/api/v1/content/clean', { content: preCleaned });
        return res?.data?.content || preCleaned;
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

    // CNS V87.0: Surgeon Boost — phẫu thuật toàn bộ content, trả về ContentPatch list
    async runSurgeonBoost(content: string, topic: string) {
        type Patch = { search_string: string; replacement_string: string; rationale: string };
        type Report = { patches: Patch[]; summary: string; logs: string[] };
        const res = await apiClient.post<GenericResponse<Report>>(`/api/v1/content/analyze/surgeon-boost`, {
            content,
            topic,
        });
        return res;
    },

    async saveAnalysisReport(cid: string, type: 'copyright' | 'seo' | 'ai_inspect' | 'surgeon', data: any) {
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
            items?: EnrichmentItem[],
            annotations?: AnalysisAnnotation[]
        }>>(`/api/v1/content/campaigns/${cid}/analyze/enrich`);
        return res;
    }
};
