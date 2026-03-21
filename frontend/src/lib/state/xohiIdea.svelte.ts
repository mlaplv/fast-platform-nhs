import { vuiController } from "$lib/vui";
import type { CampaignKeywords } from "./types";

export function createIdeaController(config: {
    getKeywords: () => CampaignKeywords;
    setKeywords: (v: CampaignKeywords) => void;
    getEditedKeywords: () => CampaignKeywords;
    setEditedKeywords: (v: CampaignKeywords) => void;
    getEditedConfig: () => Record<string, any>;
    setEditedConfig: (v: Record<string, any>) => void;
    onSelectKeyword: (kw: string) => void;
}) {
    function addSecondaryKeyword(val: string) {
        const current = config.getEditedKeywords();
        const arr = [...(current.secondary_keywords || []), val];
        config.setEditedKeywords({ ...current, secondary_keywords: arr });
        vuiController.speak(`Đã thêm từ khóa ${val}.`);
    }

    function removeSecondaryKeyword(idx: number) {
        const current = config.getEditedKeywords();
        const arr = [...(current.secondary_keywords || [])];
        const removed = arr.splice(idx, 1);
        config.setEditedKeywords({ ...current, secondary_keywords: arr });
        vuiController.speak(`Đã xóa từ khóa ${removed}.`);
    }

    function handleSecondaryKeydown(e: KeyboardEvent) {
        if ((e.key === 'Enter' || e.key === ',') && (e.currentTarget as HTMLInputElement).value.trim()) {
            e.preventDefault();
            const val = (e.currentTarget as HTMLInputElement).value.trim();
            addSecondaryKeyword(val);
            (e.currentTarget as HTMLInputElement).value = '';
        }
    }

    return {
        addSecondaryKeyword,
        removeSecondaryKeyword,
        handleSecondaryKeydown
    };
}
