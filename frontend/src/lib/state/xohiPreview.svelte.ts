import { xohiImageStore } from "./xohiImage.svelte";
import { processContentImages, resolveMediaUrl } from "./utils";
import { purifyAIContent } from "$lib/utils/purify";
import type { MediaAsset, CampaignKeywords, CopyrightResult, SEOResult, AIInspectResult, AnalysisCache } from "./types";

export function createPreviewController(config: {
    getDraftContent: () => string;
    getAssets: () => (MediaAsset | string)[];
    getKeywords: () => CampaignKeywords;
    getAnalysisCache: () => AnalysisCache | undefined;
}) {
    let previewMode = $state<'desktop' | 'mobile'>('desktop');

    const title = $derived.by(() => {
        const keywords = config.getKeywords();
        const draft_content = config.getDraftContent();
        const analysis_cache = config.getAnalysisCache();

        let base = keywords?.primary_keyword ? `Bài viết chuẩn SEO về: ${keywords.primary_keyword}` : "Tiêu đề bài viết";
        if (analysis_cache?.seo?.data) {
            const h1Match = draft_content.match(/<h1[^>]*>(.*?)<\/h1>/i);
            if (h1Match) base = h1Match[1].replace(/<[^>]+>/g, '').trim();
        }
        return base;
    });

    const thumbnail = $derived.by(() => {
        const currentAssets = xohiImageStore.assets.length > 0 ? xohiImageStore.assets : config.getAssets();
        if (currentAssets.length === 0) return "https://via.placeholder.com/600x315?text=No+Image";
        const primary = currentAssets.find(a => typeof a === 'object' && a.is_primary);
        const first = primary || currentAssets[0];
        const url = typeof first === 'string' ? first : (first.file_path || first.url);
        return resolveMediaUrl(url);
    });

    const processedContent = $derived.by(() => {
        const currentAssets = xohiImageStore.assets.length > 0 ? xohiImageStore.assets : config.getAssets();
        return processContentImages(config.getDraftContent(), currentAssets);
    });

    const description = $derived.by(() => {
        return purifyAIContent(config.getDraftContent())
            .replace(/<[^>]+>/g, ' ')
            .replace(/\s+/g, ' ')
            .substring(0, 160) + "...";
    });

    return {
        get previewMode() { return previewMode; },
        set previewMode(v) { previewMode = v; },
        get title() { return title; },
        get thumbnail() { return thumbnail; },
        get processedContent() { return processedContent; },
        get description() { return description; }
    };
}
