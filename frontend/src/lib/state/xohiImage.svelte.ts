import type { MediaAsset } from "./types";
import { safeRandomUUID, extractIdFromUrl, sanitizeId, resolveMediaUrl } from "./utils";
import { apiClient } from "$lib/utils/apiClient";

export function createXohiImageState() {
    // 1. State: Danh sách toàn bộ ảnh
    let assets = $state<MediaAsset[]>([]);
    let isUploading = $state(false);
    let campaignId = $state<string | null>(null);

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

    // 5. Action: Thêm ảnh mới (Direct Server Upload V65.0)
    async function addImages(files: FileList) {
        isUploading = true;

        const uploadPromises = Array.from(files).map(async (file, index) => {
            const tempId = `tmp_${safeRandomUUID()}`;
            const blobUrl = URL.createObjectURL(file);

            // Optimistic UI: Add preview immediately
            const newAsset: MediaAsset = {
                id: tempId,
                file_path: blobUrl,
                is_primary: assets.length === 0 && index === 0,
                order_index: assets.length,
                media_metadata: { status: 'uploading', name: file.name },
            };
            assets.push(newAsset);

            try {
                const formData = new FormData();
                formData.append('data', file);
                const cleanCid = sanitizeId(campaignId);
                if (cleanCid) formData.append('campaign_id', cleanCid);

                const response = await apiClient.upload<{ data: MediaAsset }>(
                    '/api/v1/media',
                    formData
                );

                // Replace temp asset with real one
                const idx = assets.findIndex(a => a.id === tempId);
                if (idx !== -1) {
                    const serverAsset = response.data;
                    assets[idx] = {
                        ...assets[idx],
                        id: serverAsset.id,
                        file_path: serverAsset.file_path,
                        media_metadata: { ...serverAsset.media_metadata, status: 'ready' }
                    };
                    URL.revokeObjectURL(blobUrl);
                }
            } catch (error) {
                console.error("Upload failed for", file.name, error);
                const idx = assets.findIndex(a => a.id === tempId);
                if (idx !== -1) {
                    assets[idx].media_metadata = { status: 'error', error: String(error) };
                }
            }
        });

        await Promise.all(uploadPromises);
        isUploading = false;
    }

    async function removeAsset(id: string, permanent: boolean = false) {
        const asset = assets.find(a => a.id === id);
        const path = asset?.file_path || asset?.url;
        if (path && path.startsWith('blob:')) {
            URL.revokeObjectURL(path);
        }

        // Phase 15.4: Resilient Server Synchro (Only delete if persisted real ID)
        const isPersisted = asset && !asset.id.startsWith('tmp_') && !asset.id.startsWith('stable_');

        if (isPersisted) {
            try {
                const url = permanent ? `/api/v1/media/${id}?permanent=true` : `/api/v1/media/${id}`;
                await apiClient.delete(url);
            } catch (error) {
                // R03: Log error but proceed to update local state to avoid UI hang
                console.warn("[xohiImage] Server deletion failed or not found, continuing with local removal", error);
            }
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

    async function addImagesFromUrl(url: string) {
        try {
            const cleanCid = sanitizeId(campaignId);
            const response = await apiClient.post<{ data: MediaAsset }>(
                '/api/v1/media/fetch-remote',
                { url, campaign_id: cleanCid }
            );

            const serverAsset = response.data;
            if (!serverAsset) {
                console.error("Fetch remote failed:", response);
                return;
            }
            const newAsset: MediaAsset = {
                ...serverAsset,
                file_path: resolveMediaUrl(serverAsset.file_path || serverAsset.url || ''), // CNS V80: Force resolve
                is_primary: assets.length === 0,
                order_index: assets.length
            };
            assets.push(newAsset);
        } catch (error) {
            console.error("Failed to fetch remote image", error);
            throw error;
        }
    }

    async function smartCrop(assetId: string, preset: 'square' | 'banner' | 'story' | 'feed', mode: 'ai' | 'normal' = 'ai') {
        const asset = assets.find(a => a.id === assetId);
        if (!asset) return;

        try {
            const response = await apiClient.post<{ data: MediaAsset }>(
                `/api/v1/media/${assetId}/edit`,
                {
                    action: mode === 'ai' ? 'smart_crop' : 'crop',
                    params: { preset },
                    source_url: asset.file_path || asset.url,
                    campaign_id: campaignId
                }
            );

            // Update local asset with new version (WebP path and dimensions might change)
            const serverAsset = response.data;
            if (!serverAsset) {
                console.error("Smart crop returned no data");
                return;
            }
            const idx = assets.findIndex(a => a.id === assetId);
            if (idx !== -1) {
                assets[idx] = {
                    ...assets[idx],
                    file_path: resolveMediaUrl(serverAsset.file_path), // CNS V80: Force resolve
                    dimensions: serverAsset.dimensions,
                    media_metadata: serverAsset.media_metadata
                };
            }
        } catch (error) {
            console.error("Smart crop failed", error);
        }
    }

    function initAssets(initialAssets: (MediaAsset | string)[], id?: string) {
        if (id) campaignId = sanitizeId(id);

        // CNS V80: Polymorphic Normalization (Handle both objects and raw URLs)
        const formatted = initialAssets.map((a, i) => {
            const isStr = typeof a === 'string';
            const url = isStr ? a : (a.file_path || a.url || '');
            const resolvedUrl = resolveMediaUrl(url);

            // Create base object
            const obj: MediaAsset = isStr
                ? { id: '', file_path: resolvedUrl, is_primary: i === 0, order_index: i }
                : { ...a, file_path: resolvedUrl };

            const recoveredId = extractIdFromUrl(url);

            // CNS V75: Priority to real DB ID from URL if current ID is client-side or missing
            if (!obj.id || obj.id.startsWith('img_') || obj.id.startsWith('stable_')) {
                if (recoveredId) {
                    obj.id = recoveredId;
                } else {
                    // Fallback to stable hash if absolutely no ID available (Critical for Google links)
                    const seed = url || `seed_${i}`;
                    let hash = 0;
                    for (let j = 0; j < seed.length; j++) {
                        hash = ((hash << 5) - hash) + seed.charCodeAt(j);
                        hash |= 0;
                    }
                    obj.id = `stable_${Math.abs(hash).toString(36)}_${i}`;
                }
            }

            return obj;
        });

        // CNS V76: Efficient shallow comparison before replacement to avoid reactivity storms
        const isDifferent = formatted.length !== assets.length ||
                           formatted.some((a, i) => a.id !== assets[i]?.id || a.file_path !== assets[i]?.file_path);

        if (isDifferent) {
            // Revoke blobs for removed assets
            const newPaths = new Set(formatted.map(a => a.file_path));
            assets.forEach(a => {
                const p = a.file_path || a.url;
                if (p?.startsWith('blob:') && !newPaths.has(p)) {
                    URL.revokeObjectURL(p);
                }
            });
            assets = [...formatted].sort((a, b) => a.order_index - b.order_index);
        }
    }

    function clearAll() {
        assets.forEach(a => {
            if (a.file_path?.startsWith('blob:')) URL.revokeObjectURL(a.file_path);
        });
        assets = [];
        campaignId = null;
        isUploading = false;
    }

    return {
        get assets() { return assets; },
        get primaryAsset() { return primaryAsset; },
        get secondaryAssets() { return secondaryAssets; },
        get isUploading() { return isUploading; },
        get campaignId() { return campaignId; },
        setCampaignId: (id: string) => { campaignId = id; },
        swapPrimary,
        reorderAssets,
        addImages,
        addImagesFromUrl,
        initAssets,
        removeAsset,
        smartCrop,
        clearAll
    };
}

export const xohiImageStore = createXohiImageState();
