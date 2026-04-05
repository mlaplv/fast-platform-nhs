import type { components as CoreComponents } from './core';

export interface paths {
    "/api/v1/categories": {
        get: {
            responses: {
                200: { content: { "application/json": components["schemas"]["CategoryListResponse"]; }; };
            };
        };
        post: {
            requestBody: { content: { "application/json": components["schemas"]["CreateCategoryRequest"]; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["CategoryResponse"]; }; }; };
        };
    };
    "/api/v1/categories/{category_id}": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["CategoryResponse"]; }; }; }; };
        patch: {
            requestBody: { content: { "application/json": components["schemas"]["UpdateCategoryRequest"]; }; };
            responses: { 200: { content: { "application/json": components["schemas"]["CategoryResponse"]; }; }; };
        };
        delete: { responses: { 200: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/products": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["ProductListResponse"]; }; }; }; };
        post: {
            requestBody: { content: { "application/json": components["schemas"]["CreateProductRequest"]; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["ProductResponse"]; }; }; };
        };
    };
    "/api/v1/products/{product_id}": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["ProductResponse"]; }; }; }; };
        patch: {
            requestBody: { content: { "application/json": components["schemas"]["UpdateProductRequest"]; }; };
            responses: { 200: { content: { "application/json": components["schemas"]["ProductResponse"]; }; }; };
        };
        delete: { responses: { 200: { content: { "application/json": CoreComponents["schemas"]["SuccessResponse"]; }; }; }; };
    };
    "/api/v1/orders": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["OrderListResponse"]; }; }; }; };
        post: {
            requestBody: { content: { "application/json": components["schemas"]["OrderCreateRequest"]; }; };
            responses: { 201: { content: { "application/json": components["schemas"]["OrderResponse"]; }; }; };
        };
    };
    "/api/v1/orders/{order_id}": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["OrderResponse"]; }; }; }; };
    };
    "/api/v1/orders/{order_id}/cancel": {
        patch: {
            requestBody: { content: { "application/json": components["schemas"]["CancelOrderRequest"]; }; };
            responses: { 200: { content: { "application/json": components["schemas"]["OrderResponse"]; }; }; };
        };
    };
    "/api/v1/orders/{order_id}/status": {
        patch: {
            requestBody: { content: { "application/json": components["schemas"]["OrderStatusUpdate"]; }; };
            responses: { 200: { content: { "application/json": components["schemas"]["OrderResponse"]; }; }; };
        };
    };
}

export interface components {
    schemas: {
        CategoryResponse: {
            id: string;
            name: string;
            slug: string;
            parentId: Record<string, never>;
            productCount: number;
            children: components["schemas"]["CategoryResponse"][];
            createdAt: string;
            has_children: boolean;
        };
        CategoryListResponse: { data: components["schemas"]["CategoryResponse"][]; total: number; };
        CreateCategoryRequest: { name: string; slug?: string; parentId?: string; };
        UpdateCategoryRequest: { name?: string; slug?: string; parentId?: string; };
        
        ProductResponse: {
            id: string;
            name: string;
            sku: string;
            price: number;
            stock: number;
            status: string;
            category: string;
            categoryId: string;
            description: string;
            type: string;
            createdAt: string;
            is_in_stock: boolean;
            display_status: string;
        };
        ProductListResponse: { data: components["schemas"]["ProductResponse"][]; total: number; };
        CreateProductRequest: { name: string; sku: string; price: number; stock: number; categoryId: string; description?: string; status?: string; };
        UpdateProductRequest: { name?: string; sku?: string; price?: number; stock?: number; categoryId?: string; description?: string; status?: string; };

        OrderResponse: {
            id: string;
            customerName: string;
            status: string;
            total: number;
            items: Record<string, unknown>[];
            createdAt: string;
            cancellationReason?: string;
            isSpam: boolean;
            spamScore: number;
            spamReason?: string;
            history: Record<string, unknown>[];
            display_status: string;
            items_count: number;
        };
        OrderListResponse: { data: components["schemas"]["OrderResponse"][]; total: number; };
        OrderCreateRequest: { items: Record<string, unknown>[]; total_amount: number; customer_name: string; customer_email: string; customer_phone: string; customer_address: string; };
        OrderStatusUpdate: { status: string; };
        CancelOrderRequest: { reason: string; };
    };
}
