import { apiClient } from '$lib/utils/apiClient';
import type { MediaAsset, MediaStats, MediaSseEvent, MediaMetadata } from '$lib/types';
import { sanitizeId } from './utils';
import { nanobot } from '$lib/state/nanobot.svelte';

class MediaStore {
    // States using Runes
    assets = $state<MediaAsset[]>([]);
    total = $state(0);
    isLoading = $state(false);
    currentCampaignId = $state<string | null>(null);

    // Analytics State (V9.0)
    stats = $state<MediaStats | null>(null);

    // Buffer for ultra-fast SSE events that arrive before upload API returns
    private pendingMetadataUpdates = new Map<string, MediaSseEvent>();

    // Post-tracking filter state
    linkedPostId = $state<string | null>(null);
    linkedPostType = $state<string | null>(null);

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
                this.assets = this.assets.filter(a => !ids.includes(a.id));
                this.total = Math.max(0, this.total - ids.length);
                this.selectedIds.clear();
                await this.loadStats(); // V10.0 Refresh counts
            }
        } catch (error) {
            console.error('[MediaStore] Bulk delete failed:', error);
        }
    }

    async bulkUpdateMetadata(updates: Array<{ id: string, metadata: Record<string, unknown> }>) {
        if (updates.length === 0) return;
        try {
            const response = await apiClient.patch<{ status: string }>('/api/v1/media/bulk-update', { updates });
            if (response.status === 'success') {
                updates.forEach(({ id, metadata }) => {
                    const index = this.assets.findIndex(a => a.id === id);
                    if (index !== -1) {
                        this.assets[index] = {
                            ...this.assets[index],
                            ...metadata,
                            media_metadata: {
                                ...this.assets[index].media_metadata,
                                ...((metadata.media_metadata as Record<string, unknown>) || (metadata.metadata as Record<string, unknown>) || {})
                            }
                        } as MediaAsset;
                    }
                });
            }
        } catch (error) {
            console.error('[MediaStore] Bulk update failed:', error);
        }
    }

    async aiAutoFillAltText(ids: string[]) {
        if (ids.length === 0) return;
        try {
            const response = await apiClient.post<{ status: string, data: Record<string, string> }>('/api/v1/media/ai-autofill-alt', { ids });
            if (response.status === 'success' && response.data) {
                // response.data is mapping of id -> generated alt text
                const updates = Object.entries(response.data).map(([id, alt_text]) => ({
                    id,
                    metadata: { alt_text }
                }));

                // Update local state immediately for snappy UX
                updates.forEach(({ id, metadata }) => {
                    const index = this.assets.findIndex(a => a.id === id);
                    if (index !== -1) {
                        this.assets[index] = { ...this.assets[index], alt_text: metadata.alt_text as string };
                    }
                });
            }
        } catch (error) {
            console.error('[MediaStore] AI Auto-fill failed:', error);
        }
    }

    async restoreAsset(assetId: string) {
        try {
            const response = await apiClient.post<{ status: string }>(`/api/v1/media/${assetId}/restore`);
            if (response.status === 'success') {
                this.assets = this.assets.filter(a => a.id !== assetId);
                this.total--;
                await this.loadStats();
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

        const cleanCid = sanitizeId(campaignId);
        this.isLoading = true;
        this.currentCampaignId = cleanCid;

        // Auto-subscribe to updates if campaignId is provided
        if (cleanCid) {
            this.subscribeToStoreUpdates(cleanCid);
        }

        try {
            // Chuẩn hóa đường dẫn API v1
            let endpoint = '/api/v1/media/';
            const params: Record<string, string> = {
                limit: this.limit.toString(),
                offset: this.offset.toString()
            };

            if (cleanCid) {
                params.campaign_id = cleanCid;
            }

            if (query) {
                params.q = query;
            }

            if (this.isTrashMode) {
                params.trash = 'true';
            }

            if (this.linkedPostId) {
                params.linked_post_id = this.linkedPostId;
            }

            if (this.linkedPostType) {
                params.linked_post_type = this.linkedPostType;
            }

            const response = await apiClient.get<{ status: string, data: { items: MediaAsset[], total: number } }>(endpoint, { params });
            if (response.status === 'success') {
                // Ensure field mapping consistency for R105
                this.assets = response.data.items;
                this.total = response.data.total;
            }
        } catch (error: unknown) {
            console.error('[MediaStore] Failed to load assets:', (error as Error).message);
        } finally {
            this.isLoading = false;
        }
    }

    async linkToPost(postId: string, postType: string) {
        if (this.selectedIds.size === 0) return;
        try {
            const asset_ids = Array.from(this.selectedIds);
            await apiClient.post('/api/v1/media/link-to-post', { asset_ids, post_id: postId, post_type: postType });
            // Update local state
            this.assets = this.assets.map(a => 
                this.selectedIds.has(a.id)
                    ? { ...a, linked_post_id: postId, linked_post_type: postType }
                    : a
            );
            this.clearSelection();
        } catch (error) {
            console.error('[MediaStore] Link to post failed:', error);
        }
    }

    setPostFilter(postId: string | null, postType: string | null) {
        this.linkedPostId = postId;
        this.linkedPostType = postType;
        this.offset = 0;
        this.loadAssets(this.currentCampaignId || undefined, true);
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
                total_trash_count: number;
                breakdown: Array<{ type: string; count: number; size: number }>;
                storage_provider: string;
            } }>('/api/v1/media/stats');
            if (response.status === 'success' && response.data) {
                this.stats = response.data;
            }
        } catch (error: unknown) {
            console.error('[MediaStore] Failed to load stats:', (error as Error).message);
        }
    }

   public subscribeToStoreUpdates(campaignId?: string | null) {
    if (this.currentCampaignId === campaignId && this.eventSource) {
      return;
    }

    if (this.eventSource) {
      this.eventSource.close();
    }

    if (campaignId && campaignId !== 'undefined' && campaignId !== 'null') {
        console.log(`[MediaStore] Subscribing to AI updates for campaign: ${campaignId}`);
        this.eventSource = new EventSource(`/api/v1/content/stream/${campaignId}`);
    } else {
        console.log(`[MediaStore] Subscribing to Global Pulse stream for media events`);
        this.eventSource = new EventSource(`/api/v1/pulse/stream`);
    }

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle standard SSE (MediaSseEvent payload structure)
        let payload = data;
        
        // Handle Pulse Stream wrapper structure
        if (data.event && data.payload) {
            if (data.event !== "MEDIA_ANALYZED") return;
            payload = data.payload;
        }

        if (payload.type === 'MEDIA_ANALYZED' || (payload.metadata && payload.metadata.source === 'MediaAnalyst')) {
          this.handleMediaAnalyzed(payload);
        }
      } catch (e) {
        // Probably a ping or non-JSON data
      }
    };
  }

  private handleMediaAnalyzed(payload: MediaSseEvent) {
    const assetId = payload.id || payload.asset_id;
    if (!assetId) return;

    console.log(`[MediaStore] Asset analyzed real-time: ${assetId}`);

    const index = this.assets.findIndex((a) => a.id === assetId);
    if (index !== -1) {
      const metadata = (payload.media_metadata || payload.metadata || {}) as Record<string, unknown>;

      this.assets[index] = {
        ...this.assets[index],
        alt_text: payload.alt_text || this.assets[index].alt_text,
        media_metadata: {
          ...this.assets[index].media_metadata,
          ...metadata,
        },
      };
    } else {
        // Asset not yet in state (race condition with ultra-fast heuristic analysis)
        console.log(`[MediaStore] Buffering fast SSE update for asset: ${assetId}`);
        this.pendingMetadataUpdates.set(assetId, payload);
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
            const cleanCid = sanitizeId(this.currentCampaignId);
            this.isLoading = true;
            const response = await apiClient.post<{ status: string, data: MediaAsset }>('/api/v1/media/fetch-remote', {
                url,
                campaign_id: cleanCid
            });

            if (response.status === 'success' && response.data) {
                // Thêm asset mới vào đầu danh sách để Sếp thấy ngay
                const newAsset: MediaAsset = {
                    ...response.data,
                    // Giả định các fields mặc định, AI sẽ cập nhật sau qua SSE
                    created_at: response.data.created_at || new Date().toISOString(),
                    media_metadata: response.data.media_metadata || {}
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

    async uploadAssets(files: FileList): Promise<{ successCount: number, failCount: number }> {
        if (!files || files.length === 0) return { successCount: 0, failCount: 0 };
        
        let successCount = 0;
        let failCount = 0;
        this.isLoading = true;
        
        const uploadPromises = Array.from(files).map(async (file, index) => {
            const tempId = `tmp_${Date.now()}_${index}`;
            const blobUrl = URL.createObjectURL(file);
            
            // Optimistic UI: Add immediately
            const tempAsset: MediaAsset = {
                id: tempId,
                filename: file.name,
                file_path: blobUrl,
                mime_type: file.type,
                size_bytes: file.size,
                created_at: new Date().toISOString(),
                is_public: true,
                media_metadata: { status: 'uploading' },
                is_primary: false,
                order_index: this.assets.length
            };
            this.assets = [tempAsset, ...this.assets];
            this.total++;

            try {
                const formData = new FormData();
                formData.append('data', file);
                const cleanCid = sanitizeId(this.currentCampaignId);
                if (cleanCid) formData.append('campaign_id', cleanCid);

                const response = await apiClient.upload<{ status: string, data: MediaAsset }>(
                    '/api/v1/media',
                    formData
                );

                // Defensive parsing
                let serverAsset = response?.data || response;
                if (response?.status === 'success' && response?.data) {
                    serverAsset = response.data;
                }

                if (serverAsset && serverAsset.id) {
                    // Check if there was a fast SSE event for this asset
                    let finalMetadata = { ...serverAsset.media_metadata, status: 'ready' };
                    let finalAltText = serverAsset.alt_text;
                    
                    const pendingUpdate = this.pendingMetadataUpdates.get(serverAsset.id);
                    if (pendingUpdate) {
                        console.log(`[MediaStore] Applying buffered SSE update for asset: ${serverAsset.id}`);
                        const pMeta = (pendingUpdate.media_metadata || pendingUpdate.metadata || {}) as Record<string, unknown>;
                        finalMetadata = { ...finalMetadata, ...pMeta };
                        finalAltText = pendingUpdate.alt_text || finalAltText;
                        this.pendingMetadataUpdates.delete(serverAsset.id);
                    }

                    // Update temp asset to real server asset with resolved metadata
                    this.assets = this.assets.map(a => 
                        a.id === tempId ? { ...serverAsset, alt_text: finalAltText, media_metadata: finalMetadata } : a
                    );
                    URL.revokeObjectURL(blobUrl);
                    successCount++;
                } else {
                    throw new Error("Invalid server response format");
                }
            } catch (error) {
                console.error('[MediaStore] Upload failed for', file.name, error);
                // Remove temp asset on failure
                this.assets = this.assets.filter(a => a.id !== tempId);
                if (this.total > 0) this.total -= 1;
                URL.revokeObjectURL(blobUrl);
                failCount++;
            }
        });

        await Promise.all(uploadPromises);
        this.isLoading = false;
        await this.loadStats(); // V10.0 Refresh counts
        return { successCount, failCount };
    }

    async deleteAsset(assetId: string, permanent = false) {
        try {
            const response = await apiClient.delete<{ status: string }>(`/api/v1/media/${assetId}`, {
                params: { permanent: (permanent || this.isTrashMode).toString() }
            });
            if (response.status === 'success') {
                this.assets = this.assets.filter(a => a.id !== assetId);
                this.total--;
                await this.loadStats();
            }
        } catch (error: unknown) {
            console.error('[MediaStore] Failed to delete asset:', (error as Error).message);
        }
    }

    async bulkRestore() {
        if (this.selectedIds.size === 0) return;
        this.isLoading = true;
        try {
            const ids = Array.from(this.selectedIds);
            const promises = ids.map(id => 
                apiClient.post<{ status: string, message: string }>(`/api/v1/media/${id}/restore`, {})
            );
            await Promise.allSettled(promises);
            this.assets = this.assets.filter(a => !this.selectedIds.has(a.id));
            this.total -= this.selectedIds.size;
            nanobot.showToast(`Đã khôi phục ${this.selectedIds.size} tài nguyên`, "success");
            this.clearSelection();
            await this.loadStats();
        } catch (error: unknown) {
            console.error('[MediaStore] Bulk restore failed:', (error as Error).message);
        } finally {
            this.isLoading = false;
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
                        media_metadata: {
                            ...this.assets[index].media_metadata,
                            ...((metadata.media_metadata as Record<string, unknown>) || (metadata.metadata as Record<string, unknown>) || {})
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
