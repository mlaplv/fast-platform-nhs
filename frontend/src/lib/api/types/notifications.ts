import type { components as CoreComponents } from './core';

export interface paths {
    "/api/v1/notifications": {
        get: { responses: { 200: { content: { "application/json": components["schemas"]["NotificationListResponse"]; }; }; }; };
    };
}

export interface components {
    schemas: {
        NotificationResponse: { id: string; userId: unknown; type: string; message: string; isRead: boolean; createdAt: string; };
        NotificationListResponse: { data: components["schemas"]["NotificationResponse"][]; total: number; };
    };
}
