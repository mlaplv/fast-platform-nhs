import type { components as CoreComponents } from './core';

export interface paths {
    "/api/v1/media": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["MediaListResponse"]; }; }; }; };
        post: { responses: { 201: { content: { "multipart/form-data": unknown; }; }; }; };
    };
    "/api/v1/media/{asset_id}": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["MediaDetailResponse"]; }; }; }; };
        patch: {
            requestBody: { content: { "application/json": components["schemas"]["MediaUpdateMetadata"]; }; };
            responses: { 200: { content: { "application/json": components["schemas"]["MediaAssetResponse"]; }; }; };
        };
        delete: { responses: { 200: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/media/{asset_id}/edit": {
        post: { 
            requestBody: { content: { "application/json": components["schemas"]["QuickEditRequest"]; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["QuickEditResponse"]; }; }; }; 
        };
    };
    "/api/v1/media/{asset_id}/restore": {
        post: { responses: { 201: { content: { "application/json": unknown; }; }; }; };
    };
    "/api/v1/media/{asset_id}/thumb": {
        get: { responses: { 200: { content: { "image/*": unknown; }; }; }; };
    };
    "/api/v1/media/bulk-delete": {
        post: {
            requestBody: { content: { "application/json": CoreComponents["schemas"]["BulkDeleteRequest"]; }; };
            responses: { 200: { content: { "application/json": CoreComponents["schemas"]["BulkActionResponse"]; }; }; };
        };
    };
    "/api/v1/media/bulk-download": {
        post: {
            requestBody: { content: { "application/json": CoreComponents["schemas"]["BulkDownloadRequest"]; }; };
            responses: { 200: { content: { "application/json": CoreComponents["schemas"]["BulkDownloadResponse"]; }; }; };
        };
    };
    "/api/v1/media/fetch-remote": {
        post: {
            requestBody: { content: { "application/json": { url: string; campaign_id?: string; }; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["MediaAssetResponse"]; }; }; };
        };
    };
    "/api/v1/media/stats": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["MediaStatsResponse"]; }; }; }; };
    };
}

export interface components {
    schemas: {
        MediaAssetResponse: {
            id: string;
            filename: string;
            file_path: string;
            file_size: number;
            mime_type: string;
            dimensions?: Record<string, number>;
            blurhash?: string;
            alt_text?: string;
            is_public: boolean;
            campaign_id?: string;
            owner_id?: string;
            created_at: string;
            media_metadata?: components["schemas"]["MediaMetadata"];
        };
        MediaDetailResponse: { status: string; data: components["schemas"]["MediaAssetResponse"]; };
        MediaListResponse: { status: string; data: { items: components["schemas"]["MediaAssetResponse"][]; total: number; limit: number; offset: number; }; };
        MediaMetadata: {
            embedding?: number[];
            ai_tags: string[];
            ai_description?: string;
            focal_point?: components["schemas"]["FocalPoint"];
            original_source?: string;
            sentiment?: string;
            analyzed_at?: string;
        };
        MediaStatsResponse: {
            status: string;
            data: {
                total_count: number;
                total_size: number;
                breakdown: components["schemas"]["MimeTypeBreakdown"][];
                storage_provider: string;
            };
        };
        MediaUpdateMetadata: { alt_text?: string; is_public?: boolean; media_metadata?: unknown; };
        MimeTypeBreakdown: { type: string; count: number; size: number; };
        FocalPoint: { x: number; y: number; };
        QuickEditRequest: { action: string; params: components["schemas"]["QuickEditParams"]; source_url?: string; };
        QuickEditResponse: { status: string; data: unknown; };
        QuickEditParams: { x?: number; y?: number; w?: number; h?: number; preset?: string; };
    };
}
