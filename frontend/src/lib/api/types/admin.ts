import type { components as CoreComponents } from './core';

export interface paths {
    "/api/v1/admin/ai/models": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["AIModelStatusResponse"]; }; }; }; };
        post: {
            requestBody: { content: { "application/json": components["schemas"]["ModelConfig"]; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["AIModelStatusResponse"]; }; }; };
        };
    };
    "/api/v1/admin/ai/models/discover": {
        post: { responses: { 201: { content: { "application/json": components["schemas"]["ModelDiscoveryResponse"]; }; }; }; };
    };
    "/api/v1/admin/ai/keys": {
        get: { responses: { 200: { content: { "application/json": { status: string; keys: components["schemas"]["KeyStats"][]; }; }; }; }; };
    };
    "/api/v1/admin/ai/keys/reset": {
        post: { responses: { 201: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/admin/ai/keys/bulk": {
        post: {
            requestBody: { content: { "application/json": components["schemas"]["BulkKeyInput"]; }; };
            responses: { 201: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; };
        };
    };
    "/api/v1/admin/ai/test/{index}": {
        get: { responses: { 200: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/admin/anomalies": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["AnomalyResponse"]; }; }; }; };
    };
}

export interface components {
    schemas: {
        AIModelStatusResponse: { primary_model: string; ai_models: string[]; discovered_models: string[]; };
        AnomalyResponse: { status: string; count: number; anomalies: unknown[]; };
        KeyStats: { index: number; key_preview: string; fail_count: number; health_score: number; last_used: number; status: string; };
        BulkKeyInput: { keys: string; };
        ModelConfig: { primary_model: unknown; ai_models: string[]; };
        ModelDiscoveryResponse: { status: string; models: string[]; };
    };
}
