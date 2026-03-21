import { xohiImageStore } from "./xohiImage.svelte";
import { resolveMediaUrl, processContentImages } from "./utils";
import { untrack } from "svelte";
import type { CampaignKeywords, MediaAsset } from "./types";

export function createPublishController(config: {
    campaign_id: string;
    getKeywords: () => CampaignKeywords;
    getDraftContent: () => string;
    getFinalHtml: () => string;
    getAssets: () => (MediaAsset | string)[];
    setSelectedAvatarUrl: (v: string | null) => void;
    setFinalHtml: (v: string) => void;
    apiClient: any;
}) {
    let editingField = $state<string | null>(null);
    let showAvatarPicker = $state(false);

    const displayContent = $derived.by(() => {
        const base = config.getFinalHtml() || config.getDraftContent() || "";
        const currentAssets = xohiImageStore.assets.length > 0 ? xohiImageStore.assets : config.getAssets();
        return processContentImages(base, currentAssets);
    });

    // CNS V80: Automated Store/Avatar Initialization
    function init() {
        const assets = config.getAssets();
        if (assets.length > 0 && xohiImageStore.assets.length === 0) {
            xohiImageStore.initAssets(assets);
        }
    }

    async function saveField() {
        editingField = null;
        try {
            await config.apiClient.patch(`/api/v1/content/campaigns/${config.campaign_id}`, {
                keywords: config.getKeywords(),
                draft_content: config.getDraftContent(),
                final_html: displayContent
            });
        } catch (e) {
            console.error("[PublishController] Save failed", e);
        }
    }

    async function selectAvatar(asset: MediaAsset | string) {
        const url = typeof asset === 'string' ? asset : asset.url;
        config.setSelectedAvatarUrl(url);

        if (typeof asset !== 'string' && asset.id) {
            xohiImageStore.swapPrimary(asset.id);
        }

        showAvatarPicker = false;
        try {
            await config.apiClient.patch(`/api/v1/content/campaigns/${config.campaign_id}`, {
                assets: xohiImageStore.assets,
                avatar: url
            });
        } catch (e) {
            console.error("[PublishController] Avatar sync failed", e);
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') saveField();
        if (e.key === 'Escape') editingField = null;
    }

    return {
        get editingField() { return editingField; },
        set editingField(v) { editingField = v; },
        get showAvatarPicker() { return showAvatarPicker; },
        set showAvatarPicker(v) { showAvatarPicker = v; },
        get displayContent() { return displayContent; },
        init,
        saveField,
        selectAvatar,
        handleKeydown
    };
}
