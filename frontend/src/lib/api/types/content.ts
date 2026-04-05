import type { components as CoreComponents } from './core';

export interface paths {
    "/api/v1/articles": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["ArticleListResponse"]; }; }; }; };
        post: {
            requestBody: { content: { "application/json": components["schemas"]["CreateArticleRequest"]; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["ArticleResponse"]; }; }; };
        };
    };
    "/api/v1/articles/{article_id}": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["ArticleResponse"]; }; }; }; };
        patch: {
            requestBody: { content: { "application/json": components["schemas"]["UpdateArticleRequest"]; }; };
            responses: { 200: { content: { "application/json": components["schemas"]["ArticleResponse"]; }; }; };
        };
        delete: { responses: { 200: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/content/clean": {
        post: { responses: { 201: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
}

export interface components {
    schemas: {
        ArticleResponse: {
            id: string;
            title: string;
            slug: string;
            excerpt: string;
            content: string;
            seoTitle?: string;
            seoDescription?: string;
            status: string;
            category: string;
            views: number;
            author: string;
            createdAt: string;
            display_status: string;
            reading_time: number;
        };
        ArticleListResponse: { data: components["schemas"]["ArticleResponse"][]; total: number; };
        CreateArticleRequest: { title: string; slug?: string; excerpt?: string; content: string; category?: string; status?: string; };
        UpdateArticleRequest: { title?: string; slug?: string; excerpt?: string; content?: string; category?: string; status?: string; };
    };
}
