import { untrack } from "svelte";
import type { MediaAsset } from "./types";
import { safeRandomUUID, extractIdFromUrl, sanitizeId, resolveMediaUrl } from "./utils";
import { apiClient } from "$lib/utils/apiClient";

export class XohiImageStore {
    // CNS V85.0: Class-based store for stable singleton reactivity in Svelte 5
    assets = $state<MediaAsset[]>([]);
    isUploading = $state(false);
    campaignId = $state<string | null>(null);

    get primaryAsset() { 
        return this.assets.find(a => a.is_primary); 
    }
    
    get secondaryAssets() {
        return this.assets
            .filter(a => !a.is_primary)
            .sort((a, b) => a.order_index - b.order_index);
    }

    constructor() {}

    swapPrimary(assetId: string) {
        const oldPrimary = this.assets.find(a => a.is_primary);
        const newPrimary = this.assets.find(a => a.id === assetId);

        if (!newPrimary) return;

        this.assets.forEach(a => {
            if (a.id === assetId) {
                a.is_primary = true;
                a.order_index = -1;
            } else if (a.is_primary) {
                a.is_primary = false;
                a.order_index = oldPrimary ? oldPrimary.order_index : 0;
            }
        });

        this.recalculateOrder();
    }

    reorderAssets(orderedIds: string[]) {
        this.assets.forEach(a => {
            const newIndex = orderedIds.indexOf(a.id);
            if (newIndex !== -1) {
                a.order_index = newIndex;
            }
        });
    }

    recalculateOrder() {
        const secondary = this.assets
            .filter(a => !a.is_primary)
            .sort((a, b) => a.order_index - b.order_index);
            
        secondary.forEach((a, index) => {
            if (a.order_index !== index) {
                a.order_index = index;
            }
        });
    }

    async addImages(files: FileList) {
        this.isUploading = true;
        const uploadPromises = Array.from(files).map(async (file, index) => {
            const tempId = `tmp_${safeRandomUUID()}`;
            const blobUrl = URL.createObjectURL(file);

            const newAsset: MediaAsset = {
                id: tempId,
                file_path: blobUrl,
                is_primary: this.assets.length === 0 && index === 0,
                order_index: this.assets.length,
                media_metadata: { status: 'uploading', name: file.name },
            };
            this.assets.push(newAsset);

            try {
                const formData = new FormData();
                formData.append('data', file);
                const cleanCid = sanitizeId(this.campaignId);
                if (cleanCid) formData.append('campaign_id', cleanCid);

                const response = await apiClient.upload<{ data: MediaAsset }>(
                    '/api/v1/media',
                    formData
                );

                const idx = this.assets.findIndex(a => a.id === tempId);
                if (idx !== -1) {
                    const serverAsset = response.data;
                    this.assets[idx] = {
                        ...this.assets[idx],
                        id: serverAsset.id,
                        file_path: serverAsset.file_path,
                        media_metadata: { ...serverAsset.media_metadata, status: 'ready' }
                    };
                    URL.revokeObjectURL(blobUrl);
                }
            } catch (error) {
                console.error("Upload failed", error);
                const idx = this.assets.findIndex(a => a.id === tempId);
                if (idx !== -1) {
                    this.assets[idx].media_metadata = { status: 'error', error: String(error) };
                }
            }
        });

        await Promise.all(uploadPromises);
        this.isUploading = false;
    }

    async removeAsset(id: string, permanent: boolean = false) {
        const asset = this.assets.find(a => a.id === id);
        if (!asset) return;

        const wasPrimary = asset.is_primary;
        const path = asset.file_path || asset.url;

        if (path?.startsWith('blob:')) URL.revokeObjectURL(path);

        this.assets = this.assets.filter(a => a.id !== id);

        if (wasPrimary && this.assets.length > 0) {
            this.assets[0].is_primary = true;
            this.assets[0].order_index = -1;
        }
        this.recalculateOrder();

        const isPersisted = !asset.id.startsWith('tmp_') && !asset.id.startsWith('stable_');
        if (isPersisted) {
            try {
                const url = permanent ? `/api/v1/media/${id}?permanent=true` : `/api/v1/media/${id}`;
                await apiClient.delete(url);
            } catch (error) {
                console.warn("[XohiImageStore] Server deletion failed", error);
            }
        }
    }

    async addImagesFromUrl(url: string) {
        this.isUploading = true;
        try {
            const cleanCid = sanitizeId(this.campaignId);
            const response = await apiClient.post<{ data: MediaAsset }>(
                '/api/v1/media/fetch-remote',
                { url, campaign_id: cleanCid }
            );

            const serverAsset = response.data;
            if (serverAsset) {
                const hasPrimary = this.assets.some(a => a.is_primary);
                const newAsset: MediaAsset = {
                    ...serverAsset,
                    file_path: resolveMediaUrl(serverAsset.file_path || serverAsset.url || ''),
                    is_primary: !hasPrimary,
                    order_index: this.assets.length
                };
                this.assets = [...this.assets, newAsset].sort((a, b) => a.order_index - b.order_index);
            }
        } catch (error) {
            console.error("Fetch remote image failed", error);
        } finally {
            this.isUploading = false;
        }
    }

    async smartCrop(assetId: string, preset: 'square' | 'banner' | 'story' | 'feed', mode: 'ai' | 'normal' = 'ai') {
        const asset = this.assets.find(a => a.id === assetId);
        if (!asset) return;

        try {
            const response = await apiClient.post<{ data: MediaAsset }>(
                `/api/v1/media/${assetId}/edit`,
                {
                    action: mode === 'ai' ? 'smart_crop' : 'crop',
                    params: { preset },
                    source_url: asset.file_path || asset.url,
                    campaign_id: this.campaignId
                }
            );

            const serverAsset = response.data;
            const idx = this.assets.findIndex(a => a.id === assetId);
            if (idx !== -1 && serverAsset) {
                this.assets[idx] = {
                    ...this.assets[idx],
                    file_path: resolveMediaUrl(serverAsset.file_path),
                    dimensions: serverAsset.dimensions,
                    media_metadata: serverAsset.media_metadata
                };
            }
        } catch (error) {
            console.error("Crop failed", error);
        }
    }

    initAssets(initialAssets: (MediaAsset | string)[], id?: string) {
        if (id) this.campaignId = sanitizeId(id);

        const formatted = initialAssets.map((a, i) => {
            const isStr = typeof a === 'string';
            const url = isStr ? a : (a.file_path || a.url || '');
            const resolvedUrl = resolveMediaUrl(url);

            const obj: MediaAsset = isStr
                ? { id: '', file_path: resolvedUrl, is_primary: i === 0, order_index: i }
                : { ...a, file_path: resolvedUrl };

            const recoveredId = extractIdFromUrl(url);
            if (!obj.id || obj.id.startsWith('img_') || obj.id.startsWith('stable_')) {
                if (recoveredId) obj.id = recoveredId;
                else obj.id = `stable_${Math.abs(url.split('').reduce((acc,b)=>{acc=((acc<<5)-acc)+b.charCodeAt(0);return acc&acc},0)).toString(36)}_${i}`;
            }
            return obj;
        });

        const isDifferent = untrack(() => (
            formatted.length !== this.assets.length ||
            formatted.some((a, i) => 
                a.id !== this.assets[i]?.id || 
                a.is_primary !== this.assets[i]?.is_primary ||
                a.file_path !== this.assets[i]?.file_path
            )
        ));

        if (isDifferent) {
            const newPaths = new Set(formatted.map(a => a.file_path));
            this.assets.forEach(a => {
                if (a.file_path?.startsWith('blob:') && !newPaths.has(a.file_path)) URL.revokeObjectURL(a.file_path);
            });

            if (formatted.length > 0 && !formatted.some(a => a.is_primary)) {
                formatted[0].is_primary = true;
            }

            this.assets = formatted.sort((a, b) => a.order_index - b.order_index);
        }
    }

    clearAll() {
        this.assets.forEach(a => {
            if (a.file_path?.startsWith('blob:')) URL.revokeObjectURL(a.file_path);
        });
        this.assets = [];
        this.campaignId = null;
        this.isUploading = false;
    }
}

export const xohiImageStore = new XohiImageStore();
