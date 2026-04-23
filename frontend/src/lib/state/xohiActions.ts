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
