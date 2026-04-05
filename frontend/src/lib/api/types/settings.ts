import type { components as CoreComponents } from './core';

export interface paths {
    "/api/v1/settings/lexicon/overrides": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["LexiconOverridesResponse"]; }; }; }; };
        post: {
            requestBody: { content: { "application/json": { wrong_word: string; right_word: string; }; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["LexiconOverridesResponse"]; }; }; };
        };
    };
    "/api/v1/settings/lexicon/stopwords": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["LexiconStopwordsResponse"]; }; }; }; };
        post: {
            requestBody: { content: { "application/json": { word: string; }; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["LexiconStopwordsResponse"]; }; }; };
        };
    };
    "/api/v1/settings/campaign-mode": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["CampaignModeResponse"]; }; }; }; };
        post: {
            requestBody: { content: { "application/json": { is_campaign_mode: boolean; }; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["CampaignModeResponse"]; }; }; };
        };
    };
    "/api/v1/settings/voice": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["VoiceSettingsResponse"]; }; }; }; };
        post: {
            requestBody: { content: { "application/json": components["schemas"]["VoiceSettingsPayload"]; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["VoiceSettingsResponse"]; }; }; };
        };
    };
}

export interface components {
    schemas: {
        LexiconOverridesResponse: { overrides: Record<string, string>; };
        LexiconStopwordsResponse: { stopwords: string[]; };
        CampaignModeResponse: { is_campaign_mode: boolean; };
        VoiceSettingsResponse: {
            wake_words: string[];
            sleep_words: string[];
            greeting_template: string;
            farewell_template: string;
            is_campaign_mode: boolean;
            capabilities: string[];
            chat_settings: unknown;
            stt_anchors: string[];
            mic_sensitivity: number;
        };
        VoiceSettingsPayload: {
            wake_words: string[];
            sleep_words: string[];
            capabilities: unknown;
            greeting_template?: string;
            farewell_template?: string;
            is_campaign_mode?: unknown;
            chat_settings?: unknown;
            stt_anchors?: unknown;
            mic_sensitivity?: unknown;
        };
    };
}
