import { apiClient } from '$lib/utils/apiClient';
import type { MediaAsset } from '$lib/types';

class MediaStore {
    // States using Runes
    assets = $state<MediaAsset[]>([]);
    total = $state(0);
    isLoading = $state(false);
    currentCampaignId = $state<string | null>(null);

    // Analytics State (V9.0)
    stats = $state<{
        total_count: number;
        total_size: number;
        breakdown: Array<{ type: string; count: number; size: number }>;
        storage_provider: string;
    } | null>(null);

    // Selection State (V65.0 Bulk Ops)
    selectedIds = $state<Set<string>>(new Set());

    toggleSelection(id: string) {
        if (this.selectedIds.has(id)) {
            this.selectedIds.delete(id);
        } else {
            this.selectedIds.add(id);
        }
        // Force refresh for Svelte state (Sets are not deep tracked)
        this.selectedIds = new Set(this.selectedIds);
    }

    selectAll() {
        this.selectedIds = new Set(this.assets.map(a => a.id));
    }

    clearSelection() {
        this.selectedIds = new Set();
    }

    async bulkDelete(permanent = false) {
        if (this.selectedIds.size === 0) return;

        try {
            const ids = Array.from(this.selectedIds);
            const response = await apiClient.post<{ status: string }>('/api/v1/media/bulk-delete', {
                ids,
                permanent: permanent || this.isTrashMode // Auto permanent if already in trash
            });
            if (response.status === 'success') {
                this.assets = this.assets.filter(a => !this.selectedIds.has(a.id));
                this.total -= this.selectedIds.size;
                this.clearSelection();
            }
        } catch (error) {
            console.error('[MediaStore] Bulk delete failed:', error);
        }
    }

    async restoreAsset(assetId: string) {
        try {
            const response = await apiClient.post<{ status: string }>(`/api/v1/media/${assetId}/restore`);
            if (response.status === 'success') {
                this.assets = this.assets.filter(a => a.id !== assetId);
                this.total--;
            }
        } catch (error) {
            console.error('[MediaStore] Failed to restore asset:', error);
        }
    }

    async bulkDownload() {
        if (this.selectedIds.size === 0) return;

        try {
            const ids = Array.from(this.selectedIds);
            const response = await apiClient.post<{ status: string, data: { zip_url: string } }>('/api/v1/media/bulk-download', { ids });

            if (response.status === 'success' && response.data.zip_url) {
                // Tạo link ẩn để trigger download
                const link = document.createElement('a');
                link.href = response.data.zip_url;
                link.download = `xohi_assets_${new Date().getTime()}.zip`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                this.clearSelection();
            }
        } catch (error) {
            console.error('[MediaStore] Bulk download failed:', error);
        }
    }

    limit = $state(50);
    offset = $state(0);
    isTrashMode = $state(false);

    // SSE Management
    private eventSource: EventSource | null = null;

    async loadAssets(campaignId?: string, force = false, query?: string) {
        if (this.isLoading && !force) return;

        this.isLoading = true;
        this.currentCampaignId = campaignId || null;

        // Auto-subscribe to updates if campaignId is provided
        if (campaignId) {
            this.subscribeToUpdates(campaignId);
        }

        try {
            // Chuẩn hóa đường dẫn API v1
            let endpoint = '/api/v1/media/';
            const params: Record<string, string> = {
                limit: this.limit.toString(),
                offset: this.offset.toString()
            };

            if (campaignId) {
                params.campaign_id = campaignId;
            }

            if (query) {
                params.q = query;
            }

            if (this.isTrashMode) {
                params.trash = 'true';
            }

            const response = await apiClient.get<{ status: string, data: { items: MediaAsset[], total: number } }>(endpoint, { params });
            if (response.status === 'success') {
                this.assets = response.data.items;
                this.total = response.data.total;
            }
        } catch (error: unknown) {
            console.error('[MediaStore] Failed to load assets:', (error as Error).message);
        } finally {
            this.isLoading = false;
        }
    }

    async toggleTrashMode() {
        this.isTrashMode = !this.isTrashMode;
        this.offset = 0;
        this.clearSelection();
        await this.loadAssets(this.currentCampaignId || undefined, true);
    }

    async loadStats() {
        try {
            const response = await apiClient.get<{ status: string, data: {
                total_count: number;
                total_size: number;
                breakdown: Array<{ type: string; count: number; size: number }>;
                storage_provider: string;
            } }>('/api/v1/media/stats');
            if (response.status === 'success') {
                this.stats = response.data;
            }
        } catch (error: unknown) {
            console.error('[MediaStore] Failed to load stats:', (error as Error).message);
        }
    }

    subscribeToUpdates(campaignId: string) {
        if (this.eventSource) {
            this.eventSource.close();
        }

        console.log(`[MediaStore] Subscribing to AI updates for campaign: ${campaignId}`);
        this.eventSource = new EventSource(`/api/v1/content/stream/${campaignId}`);

        this.eventSource.onmessage = (event) => {
            try {
                // Handle both raw data and structured events
                const data = JSON.parse(event.data);

                // If the event is MEDIA_ANALYZED (from event_bus)
                if (data.type === 'MEDIA_ANALYZED' || (data.metadata && data.metadata.source === 'MediaAnalyst')) {
                    this.handleMediaAnalyzed(data as Record<string, unknown>);
                }
            } catch (e) {
                // Probably a ping or non-JSON data
            }
        };

        this.eventSource.onerror = () => {
            console.warn('[MediaStore] SSE connection lost. Reconnecting...');
            this.eventSource?.close();
            this.eventSource = null;
            // Retry logic could be added here if needed
        };
    }

    private handleMediaAnalyzed(payload: Record<string, unknown>) {
        const assetId = (payload.id || payload.asset_id) as string;
        if (!assetId) return;

        console.log(`[MediaStore] Asset analyzed real-time: ${assetId}`);

        // Update the asset in the list surgically
        const index = this.assets.findIndex(a => a.id === assetId);
        if (index !== -1) {
            // Trigger reactivity by replacing the object
            this.assets[index] = {
                ...this.assets[index],
                alt_text: (payload.alt_text as string) || this.assets[index].alt_text,
                metadata: {
                    ...this.assets[index].metadata,
                    ...((payload.media_metadata as Record<string, unknown>) || (payload.metadata as Record<string, unknown>) || {})
                }
            };
        }
    }

    cleanup() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    async fetchRemote(url: string) {
        if (!url) return;

        try {
            this.isLoading = true;
            const response = await apiClient.post<{ status: string, data: MediaAsset }>('/api/v1/media/fetch-remote', {
                url,
                campaign_id: this.currentCampaignId
            });

            if (response.status === 'success' && response.data) {
                // Thêm asset mới vào đầu danh sách để Sếp thấy ngay
                const newAsset: MediaAsset = {
                    ...response.data,
                    // Giả định các fields mặc định, AI sẽ cập nhật sau qua SSE
                    created_at: new Date().toISOString(),
                    metadata: response.data.metadata || {}
                };
                this.assets = [newAsset, ...this.assets];
                this.total++;
            }
        } catch (error: unknown) {
            console.error('[MediaStore] Remote fetch failed:', (error as Error).message);
        } finally {
            this.isLoading = false;
        }
    }

    async deleteAsset(assetId: string, permanent = false) {
        try {
            const response = await apiClient.delete<{ status: string }>(`/api/v1/media/${assetId}`, {
                params: { permanent: (permanent || this.isTrashMode).toString() }
            });
            if (response.status === 'success') {
                this.assets = this.assets.filter(a => a.id !== assetId);
                this.total--;
            }
        } catch (error: unknown) {
            console.error('[MediaStore] Failed to delete asset:', (error as Error).message);
        }
    }

    async updateMetadata(assetId: string, metadata: Record<string, unknown>) {
        try {
            const response = await apiClient.patch<{ status: string }>(`/api/v1/media/${assetId}`, metadata);
            if (response.status === 'success') {
                // R105: Surgical state update for ultra-fast UX (<200ms)
                const index = this.assets.findIndex(a => a.id === assetId);
                if (index !== -1) {
                    this.assets[index] = {
                        ...this.assets[index],
                        ...metadata,
                        // Ensure nested metadata is merged if provided
                        metadata: {
                            ...this.assets[index].metadata,
                            ...((metadata.metadata as Record<string, unknown>) || {})
                        }
                    } as MediaAsset;
                }
            }
        } catch (error: unknown) {
            console.error('[MediaStore] Failed to update metadata:', (error as Error).message);
        }
    }

    async quickEdit(assetId: string, action: string, params: Record<string, unknown> | null = null) {
        try {
            this.isLoading = true;
            const response = await apiClient.post<{ status: string, data: Partial<MediaAsset> }>(`/api/v1/media/${assetId}/edit`, { action, params });
            if (response.status === 'success' && response.data) {
                // R105: Surgical state update
                const index = this.assets.findIndex(a => a.id === assetId);
                if (index !== -1) {
                    const updatedAsset = response.data;
                    this.assets[index] = {
                        ...this.assets[index],
                        ...updatedAsset,
                        // Thêm timestamp để bypass browser cache của ảnh gốc/thumb
                        _updatedAt: Date.now()
                    } as MediaAsset;
                }
            }
        } catch (error: unknown) {
            console.error('[MediaStore] Quick edit failed:', (error as Error).message);
        } finally {
            this.isLoading = false;
        }
    }
}

export const mediaStore = new MediaStore();
