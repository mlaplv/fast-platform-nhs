import { apiClient } from "$lib/utils/apiClient";
import { nanobot } from "$lib/state/nanobot.svelte";
import { vuiController } from "$lib/vui";
import { xohiImageStore } from "$lib/state/xohiImage.svelte";
import { processContentImages } from "$lib/state/utils";
import type { CampaignKeywords, MediaAsset, CampaignOutline, CampaignMetrics, AnalysisCache } from "$lib/state/types";

export function createCampaignController(config: {
    campaign_id: string;
    keywords: CampaignKeywords;
    creation_config: Record<string, unknown>;
    outline: CampaignOutline;
    draft_content: string;
    assets: (MediaAsset | string)[];
    reserve_assets: string[];
    selectedAvatarUrl: string | null;
    selectedAssetIndex: number;
    analysis_metrics: CampaignMetrics;
    analysis_cache: AnalysisCache;
}) {
    let isLoading = $state(false);
    let isPublishing = $state(false);

    // Gate scores derived from metrics/cache
    let copyrightScore = $state<number | null>(null);
    let seoScore = $state<number | null>(null);
    let aiScore = $state<number | null>(null);

    // Phase 73: Initialize scores (Single Source of Truth)
    $effect(() => {
        const metrics = config.analysis_metrics;
        const cache = config.analysis_cache;

        if (metrics) {
            if (copyrightScore === null && metrics.unique_score !== undefined) {
                copyrightScore = Math.round(metrics.unique_score * 100);
            }
            if (seoScore === null && metrics.seo_score !== undefined) {
                seoScore = metrics.seo_score;
            }
            if (aiScore === null && metrics.ai_ready_score !== undefined) {
                aiScore = metrics.ai_ready_score;
            }
        }

        if (cache) {
            if (copyrightScore === null && cache.copyright?.data?.uniqueness_score !== undefined) {
                copyrightScore = Math.round(cache.copyright.data.uniqueness_score * 100);
            }
            if (seoScore === null && cache.seo?.data?.total_score !== undefined) {
                seoScore = cache.seo.data.total_score;
            }
            if (aiScore === null && cache.ai_inspect?.data?.geo_score !== undefined) {
                aiScore = cache.ai_inspect.data.geo_score;
            }
        }
    });

    async function approve(viewingStep: number, isEditing: boolean, editedKeywords: CampaignKeywords, editedConfig: Record<string, unknown>, editedOutline: string, editedDraft: string) {
        if (isLoading) return false;

        // Gate Check
        if (viewingStep === 4) {
            if (copyrightScore === null || copyrightScore < 90 || seoScore === null || seoScore < 70) {
                vuiController.speak('Bài viết chưa đủ điều kiện. Vui lòng xem hướng dẫn và sửa lỗi trước khi duyệt.');
                return { gateBlocked: true };
            }
        }

        isLoading = true;
        try {
            let payload: Record<string, unknown> = isEditing ? {
                edited_data: $state.snapshot(viewingStep === 1
                    ? { ...editedKeywords, creation_config: editedConfig }
                    : { html: viewingStep === 3 ? editedOutline : editedDraft })
            } : {};

            if (viewingStep === 5 && config.draft_content) {
                const currentAssets = xohiImageStore.assets.length > 0 ? xohiImageStore.assets : config.assets;
                payload.final_html = processContentImages(config.draft_content, currentAssets);
            }

            await apiClient.post(`/api/v1/content/campaigns/${config.campaign_id}/approve`, payload);

            vuiController.speak("Đã duyệt thành công!");
            return true;
        } catch (e) {
            console.error("Approve failed:", e);
            return false;
        } finally {
            isLoading = false;
        }
    }

    async function retry() {
        if (isLoading) return false;
        isLoading = true;
        
        // CNS Phase 82.25: Instant Global Feedback
        // Force global status to PROCESSING so all widgets show UltraPremiumLoading immediately
        nanobot.updateCurrentData({ 
            status: "PROCESSING", 
            progress_msg: "Đang khởi tạo lại Neural Network cho bước này..." 
        });

        try {
            await apiClient.post(`/api/v1/content/campaigns/${config.campaign_id}/retry`);
            vuiController.speak("Đang chạy lại bước này.");
            return true;
        } catch (e) {
            console.error("Retry failed:", e);
            return false;
        } finally {
            isLoading = false;
        }
    }

    async function updateMetadata(viewingStep: number, editedKeywords: CampaignKeywords, editedConfig: Record<string, unknown>, editedOutline: string, editedDraft: string) {
        if (isLoading) return false;
        isLoading = true;
        try {
            const payload = viewingStep === 1
                ? { keywords: $state.snapshot({ ...editedKeywords, creation_config: editedConfig }) }
                : (viewingStep === 3 ? { outline_data: { html: $state.snapshot(editedOutline) } } : { draft_content: $state.snapshot(editedDraft) });

            await apiClient.patch(`/api/v1/content/campaigns/${config.campaign_id}`, payload);

            if (viewingStep === 1) {
                config.keywords = { ...editedKeywords, creation_config: { ...editedConfig } };
                config.creation_config = { ...editedConfig };
                nanobot.updateCurrentData({ keywords: config.keywords });
            } else if (viewingStep === 3) {
                config.outline.html = editedOutline;
                nanobot.updateCurrentData({ outline: config.outline });
            } else if (viewingStep === 4) {
                config.draft_content = editedDraft;
                nanobot.updateCurrentData({ draft_content: config.draft_content });
            }

            vuiController.speak("Đã lưu thành công.");
            return true;
        } catch (e) {
            console.error("Update failed:", e);
            return false;
        } finally {
            isLoading = false;
        }
    }

    async function publish() {
        if (isPublishing) return false;
        isPublishing = true;
        try {
            await apiClient.post(`/api/v1/content/campaigns/${config.campaign_id}/publish`);
            vuiController.speak("Bài viết đã được xuất bản.");
            return true;
        } catch (e) {
            console.error("Publish failed:", e);
            return false;
        } finally {
            isPublishing = false;
        }
    }

    async function syncAssetChanges(viewingStep: number, newIndex?: number) {
        try {
            const currentAssets = viewingStep === 2 ? xohiImageStore.assets : config.assets;
            const currentAvatar = viewingStep === 2 ? (xohiImageStore.primaryAsset?.file_path || xohiImageStore.primaryAsset?.url) : config.selectedAvatarUrl;

            const payload = {
                assets: $state.snapshot(currentAssets),
                avatar: currentAvatar || config.selectedAvatarUrl,
                selected_index: newIndex ?? config.selectedAssetIndex,
                reserve_assets: $state.snapshot(config.reserve_assets)
            };

            await apiClient.patch(`/api/v1/content/campaigns/${config.campaign_id}`, payload);
            nanobot.updateCurrentData({
                assets: currentAssets,
                selectedAvatarUrl: currentAvatar || config.selectedAvatarUrl,
                selectedAssetIndex: newIndex ?? config.selectedAssetIndex,
                reserve_assets: config.reserve_assets
            });
            return true;
        } catch (e) {
            console.error("Sync failed:", e);
            return false;
        }
    }

    return {
        get isLoading() { return isLoading; },
        set isLoading(v) { isLoading = v; },
        get isPublishing() { return isPublishing; },
        get copyrightScore() { return copyrightScore; },
        set copyrightScore(v) { copyrightScore = v; },
        get seoScore() { return seoScore; },
        set seoScore(v) { seoScore = v; },
        get aiScore() { return aiScore; },
        set aiScore(v) { aiScore = v; },
        approve,
        retry,
        updateMetadata,
        publish,
        syncAssetChanges
    };
}
