import type { MediaAsset } from "./types";
import { safeRandomUUID } from "./utils";

export function createXohiImageState() {
    // 1. State: Danh sách toàn bộ ảnh
    let assets = $state<MediaAsset[]>([]);
    let isUploading = $state(false);

    // 2. Derived: Tự động tách biệt Ảnh chính và Ảnh phụ
    const primaryAsset = $derived(assets.find(a => a.is_primary));
    const secondaryAssets = $derived(
        assets
            .filter(a => !a.is_primary)
            .sort((a, b) => a.order_index - b.order_index)
    );

    // 3. Actions: Logic hoán đổi "Master-Slave Swap"
    function swapPrimary(assetId: string) {
        const oldPrimary = assets.find(a => a.is_primary);
        const newPrimary = assets.find(a => a.id === assetId);

        if (!newPrimary) return;

        // Reset toàn bộ primary về false
        assets.forEach(a => {
            if (a.id === assetId) {
                a.is_primary = true;
                a.order_index = -1; // Luôn đứng đầu
            } else if (a.is_primary) {
                a.is_primary = false;
                a.order_index = oldPrimary ? oldPrimary.order_index : 0;
            }
        });

        // Sắp xếp lại order_index để đảm bảo tính liên tục
        recalculateOrder();
    }

    // 4. Action: Cập nhật thứ tự sau khi kéo thả (DND)
    function reorderAssets(orderedIds: string[]) {
        assets.forEach(a => {
            const newIndex = orderedIds.indexOf(a.id);
            if (newIndex !== -1) {
                a.order_index = newIndex;
            }
        });
    }

    function recalculateOrder() {
        secondaryAssets.forEach((a, index) => {
            a.order_index = index;
        });
    }

    // 5. Action: Thêm ảnh mới (Optimistic Preview)
    function addImages(files: FileList) {
        isUploading = true;
        Array.from(files).forEach((file, index) => {
            const url = URL.createObjectURL(file);
            const newAsset: MediaAsset = {
                id: `tmp_${safeRandomUUID()}`,
                url,
                is_primary: assets.length === 0 && index === 0, // Nếu chưa có ảnh thì cái đầu tiên là primary
                order_index: assets.length,
                media_metadata: { size: file.size, type: file.type, name: file.name }
            };
            assets.push(newAsset);
        });
        isUploading = false;
    }

    function removeAsset(id: string) {
        const asset = assets.find(a => a.id === id);
        if (asset && asset.url.startsWith('blob:')) {
            URL.revokeObjectURL(asset.url); // R03: Dọn dẹp bộ nhớ
        }
        const wasPrimary = asset?.is_primary;
        assets = assets.filter(a => a.id !== id);

        // Phase 15.3: Auto-promote next asset if primary was deleted
        if (wasPrimary && assets.length > 0) {
            assets[0].is_primary = true;
            assets[0].order_index = -1;
        }
        recalculateOrder();
    }

    function addImagesFromUrl(url: string) {
        const newAsset: MediaAsset = {
            id: `img_${safeRandomUUID()}`,
            url,
            is_primary: assets.length === 0,
            order_index: assets.length
        };
        assets.push(newAsset);
    }

    function initAssets(initialAssets: MediaAsset[]) {
        // Dọn dẹp Blob cũ nếu có trước khi nạp mới
        assets.forEach(a => {
            if (a.url.startsWith('blob:')) URL.revokeObjectURL(a.url);
        });
        assets = [...initialAssets].sort((a, b) => a.order_index - b.order_index);
    }

    return {
        get assets() { return assets; },
        get primaryAsset() { return primaryAsset; },
        get secondaryAssets() { return secondaryAssets; },
        get isUploading() { return isUploading; },
        swapPrimary,
        reorderAssets,
        addImages,
        addImagesFromUrl,
        initAssets,
        removeAsset
    };
}

export const xohiImageStore = createXohiImageState();
