import { xohiImageStore } from "./xohiImage.svelte";
import { processContentImages } from "./utils";
import type { MediaAsset } from "./types";

export interface OutlineSection {
    heading?: string;
    H2?: string;
    H3?: string;
    title?: string;
    Title?: string;
    content?: string;
    Content?: string;
    body?: string;
    text?: string;
    description?: string;
}

export type RawOutline = {
    html?: string;
    sections?: OutlineSection[];
    outline?: {
        sections?: OutlineSection[];
    };
    outline_data?: {
        sections?: OutlineSection[];
    };
} | OutlineSection[] | string;

export function createOutlineController(config: {
    getOutline: () => RawOutline;
    getEditedOutline: () => string;
    getAssets: () => (MediaAsset | string)[];
    setEditedOutline: (v: string) => void;
}) {
    const getStructuredOutline = (): string => {
        const outline = config.getOutline();
        if (typeof outline === 'string') return outline;

        const isPlainObject = (val: unknown): val is Record<string, unknown> =>
            typeof val === 'object' && val !== null && !Array.isArray(val);

        if (isPlainObject(outline) && 'html' in outline && typeof outline.html === 'string') {
            return outline.html;
        }

        const sections: OutlineSection[] =
            isPlainObject(outline)
                ? ((outline.sections as OutlineSection[]) ||
                    (outline.outline as any)?.sections ||
                    (outline.outline_data as any)?.sections || [])
                : (Array.isArray(outline) ? outline : []);

        if (sections.length > 0) {
            return sections.map((s) => {
                const header = s.heading || s.H2 || s.H3 || s.title || s.Title || "";
                const body = s.content || s.Content || s.body || s.description || s.text || "";

                // R110: Robust strip of H2/H3 prefixes and markdown artifacts
                let hText = header.replace(/^[*\-\s]*(H2|H3)[:\-\s]*/i, "").trim();
                hText = hText.replace(/[*\-_~`]+/g, "").trim(); // Strip leftover bold/italic marks
                
                const tag = header.toUpperCase().includes("H3") ? "h3" : "h2";
                
                // Fallback: If stripping left us empty, use the whole header
                if (!hText) hText = header || "Mục không tên";

                return `<${tag}>${hText}</${tag}><p>${body}</p>`;
            }).join("\n");
        }
        return "";
    };

    const displayContent = $derived.by(() => {
        const base = config.getEditedOutline() || getStructuredOutline();
        const currentAssets = xohiImageStore.assets.length > 0 ? xohiImageStore.assets : config.getAssets();
        return processContentImages(base, currentAssets);
    });

    function syncInitialDraft() {
        if (!config.getEditedOutline()) {
            const fallback = getStructuredOutline();
            if (fallback) config.setEditedOutline(fallback);
        }
    }

    return {
        get displayContent() { return displayContent; },
        syncInitialDraft,
        getStructuredOutline
    };
}
