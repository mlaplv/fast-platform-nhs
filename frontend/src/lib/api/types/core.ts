/**
 * Core / Shared API Types
 * Refactored from monolithic types.ts
 * Compliance: <500 lines
 */

export interface paths {
    "/api/v1/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * GetHealth
         * @description null
         */
        get: {
            parameters: {
                query?: never;
                header?: never;
                path?: never;
                cookie?: never;
            };
            requestBody?: never;
            responses: {
                /** @description Request fulfilled, document follows */
                200: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        /** @example null */
                        "application/json": components["schemas"]["HealthStatusResponse"];
                    };
                };
            };
        };
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}

export interface components {
    schemas: {
        /**
         * GenericResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        GenericResponse: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            status: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            message: Record<string, never>;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            data: Record<string, never>;
        };
        /**
         * HealthStatusResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        HealthStatusResponse: {
            /**
             * @description null
             * @default Fast-Platform Gateway
             * @example null
             * @constant
             */
            system: string;
            /**
             * @description null
             * @default online
             * @example null
             * @constant
             */
            status: string;
        };
        /**
         * SuccessResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        SuccessResponse: {
            /**
             * @description null
             * @default true
             * @example null
             * @constant
             */
            ok: boolean;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            message: Record<string, never>;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            id: Record<string, never>;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            data: Record<string, never>;
        };
        /**
         * BulkActionResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        BulkActionResponse: {
            /**
             * @description null
             * @default true
             * @example null
             * @constant
             */
            ok: boolean;
            /**
             * @description null
             * @default 0
             * @example null
             * @constant
             */
            count: number;
        };
        /**
         * BulkDeleteRequest
         * @description null
         * @default null
         * @example null
         * @constant
         */
        BulkDeleteRequest: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            ids: string[];
            /**
             * @description null
             * @default false
             * @example null
             * @constant
             */
            permanent: boolean;
        };
        /**
         * BulkDownloadRequest
         * @description null
         * @default null
         * @example null
         * @constant
         */
        BulkDownloadRequest: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            ids: string[];
        };
        /**
         * BulkDownloadResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        BulkDownloadResponse: {
            /**
             * @description null
             * @default success
             * @example null
             * @constant
             */
            status: string;
            /** @description null */
            data: unknown;
        };
        /**
         * BulkDownloadResponseData
         * @description null
         * @default null
         * @example null
         * @constant
         */
        BulkDownloadResponseData: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            zip_url: string;
        };
        /**
         * BulkIdsRequest
         * @description null
         * @default null
         * @example null
         * @constant
         */
        BulkIdsRequest: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            ids: string[];
        };
        /**
         * CapabilityMetadata
         * @description null
         * @default null
         * @example null
         * @constant
         */
        CapabilityMetadata: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            id: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            name: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            desc: string;
            /**
             * @description null
             * @default false
             * @example null
             * @constant
             */
            active: boolean;
            /**
             * @description null
             * @default text-gray-400
             * @example null
             * @constant
             */
            color: string;
            /**
             * @description null
             * @default Brain
             * @example null
             * @constant
             */
            icon: string;
        };
    };
}
