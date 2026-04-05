import type { components as CoreComponents } from './core';

export interface paths {
    "/api/v1/content/campaigns": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["CampaignListResponse"]; }; }; }; };
    };
    "/api/v1/content/campaigns/{campaign_id}": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["ContentCampaign"]; }; }; }; };
        patch: {
            requestBody: { content: { "application/json": Record<string, unknown>; }; };
            responses: { 200: { content: { "application/json": components["schemas"]["ContentCampaign"]; }; }; };
        };
        delete: { responses: { 200: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/content/campaigns/{campaign_id}/analyze/seo": {
        post: { responses: { 201: { content: { "application/json": components["schemas"]["AuditorAnalysisResponse"]; }; }; }; };
    };
    "/api/v1/content/campaigns/{campaign_id}/analyze/copyright": {
        post: { responses: { 201: { content: { "application/json": components["schemas"]["AuditorAnalysisResponse"]; }; }; }; };
    };
    "/api/v1/content/campaigns/{campaign_id}/analyze/ai-inspect": {
        post: { responses: { 201: { content: { "application/json": components["schemas"]["AuditorAnalysisResponse"]; }; }; }; };
    };
    "/api/v1/content/campaigns/{campaign_id}/approve": {
        post: { responses: { 201: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/content/campaigns/{campaign_id}/publish": {
        post: { responses: { 201: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/content/campaigns/{campaign_id}/retry": {
        post: { responses: { 201: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/content/campaigns/{campaign_id}/metadata": {
        put: { responses: { 200: { content: { "application/json": components["schemas"]["ContentCampaign"]; }; }; }; };
    };
    "/api/v1/content/stream/{campaign_id}": {
        get: { responses: { 200: { content: { "application/json": Record<string, any>; }; }; }; };
    };
}

export interface components {
    schemas: {
        ContentCampaign: {
            id: string;
            user_id: string;
            source_input: Record<string, unknown>;
            reviewer_type: string;
            current_step: number;
            status: string;
            gold_metadata: Record<string, unknown>;
            topic_data: Record<string, unknown>;
            assets_data: Record<string, unknown>;
            outline_data: Record<string, unknown>;
            draft_content: Record<string, unknown>;
            final_html: Record<string, unknown>;
            search_count: number;
            created_at: string;
        };
        CampaignListItem: {
            id: string;
            topic_data: Record<string, unknown>;
            status: string;
            current_step: number;
            created_at: string;
            user_id: string;
            category: string;
        };
        CampaignListResponse: { items: components["schemas"]["CampaignListItem"][]; total: number; has_more: boolean; limit: number; offset: number; };
        AuditorAnalysisResponse: {
            draft_id: string;
            overall_risk_score: number;
            risk_metrics: components["schemas"]["RiskMetric"][];
            impact_forecasts: components["schemas"]["ImpactForecast"][];
            recommendation: string;
            timestamp: string;
        };
        ImpactForecast: { category: string; impact_level: string; description: string; };
        RiskMetric: { label: string; score: number; reason: string; };
    };
}
