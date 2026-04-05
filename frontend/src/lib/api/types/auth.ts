import type { components as CoreComponents } from './core';

export interface paths {
    "/api/v1/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Login
         * @description null
         */
        post: {
            parameters: {
                query?: never;
                header?: never;
                path?: never;
                cookie?: never;
            };
            requestBody: {
                content: {
                    "application/json": components["schemas"]["LoginRequest"];
                };
            };
            responses: {
                /** @description Request fulfilled, document follows */
                200: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        /** @example null */
                        "application/json": components["schemas"]["TokenResponse"];
                    };
                };
                /** @description Bad request syntax or unsupported method */
                400: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        /** @example null */
                        "application/json": CoreComponents["schemas"]["GenericResponse"];
                    };
                };
            };
        };
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Register
         * @description null
         */
        post: {
            parameters: {
                query?: never;
                header?: never;
                path?: never;
                cookie?: never;
            };
            requestBody: {
                content: {
                    "application/json": components["schemas"]["RegisterRequest"];
                };
            };
            responses: {
                /** @description Document created, URL follows */
                201: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        /** @example null */
                        "application/json": components["schemas"]["TokenResponse"];
                    };
                };
                /** @description Bad request syntax or unsupported method */
                400: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        /** @example null */
                        "application/json": CoreComponents["schemas"]["GenericResponse"];
                    };
                };
            };
        };
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/otp/request": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * RequestOtp
         * @description null
         */
        post: {
            parameters: {
                query?: never;
                header?: never;
                path?: never;
                cookie?: never;
            };
            requestBody: {
                content: {
                    "application/json": {
                        /**
                         * @description null
                         * @default null
                         * @example null
                         * @constant
                         */
                        email: string;
                    };
                };
            };
            responses: {
                /** @description Document created, URL follows */
                201: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        /** @example null */
                        "application/json": components["schemas"]["OTPRequestResponse"];
                    };
                };
            };
        };
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/otp/verify": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * VerifyOtp
         * @description null
         */
        post: {
            parameters: {
                query?: never;
                header?: never;
                path?: never;
                cookie?: never;
            };
            requestBody: {
                content: {
                    "application/json": {
                        /**
                         * @description null
                         * @default null
                         * @example null
                         * @constant
                         */
                        otp_token: string;
                        /**
                         * @description null
                         * @default null
                         * @example null
                         * @constant
                         */
                        otp_code: string;
                    };
                };
            };
            responses: {
                /** @description Document created, URL follows */
                201: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        /** @example null */
                        "application/json": components["schemas"]["OTPVerifyResponse"];
                    };
                };
            };
        };
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * ListUsers
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
                        "application/json": components["schemas"]["UserListResponse"];
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
    "/api/v1/users/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * GetUser
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
                        "application/json": components["schemas"]["UserResponse"];
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
         * LoginRequest
         * @description null
         * @default null
         * @example null
         * @constant
         */
        LoginRequest: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            identifier: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            password: string;
        };
        /**
         * TokenResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        TokenResponse: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            access_token: string;
            /**
             * @description null
             * @default Bearer
             * @example null
             * @constant
             */
            token_type: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            role: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            name: Record<string, never>;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            email: Record<string, never>;
        };
        /**
         * RegisterRequest
         * @description null
         * @default null
         * @example null
         * @constant
         */
        RegisterRequest: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            email: string;
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
            password: string;
        };
        /**
         * OTPRequestResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        OTPRequestResponse: {
            /**
             * @description null
             * @default success
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
            message: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            otp_token: string;
        };
        /**
         * OTPVerifyResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        OTPVerifyResponse: {
            /**
             * @description null
             * @default success
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
            access_token: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            role: string;
        };
        /**
         * UserListResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        UserListResponse: {
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            data: components["schemas"]["UserResponse"][];
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            total: number;
        };
        /**
         * UserResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        UserResponse: {
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
            email: string;
            /**
             * @description null
             * @default Unknown
             * @example null
             * @constant
             */
            name: string;
            /**
             * @description null
             * @default ACTIVE
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
            roles: components["schemas"]["RoleResponse"][];
            /**
             * Format: date-time
             * @description null
             * @default null
             * @example null
             * @constant
             */
            createdAt: string;
        };
        /**
         * RoleResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        RoleResponse: {
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
            code: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            description: Record<string, never>;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            permissions: components["schemas"]["PermissionResponse"][];
        };
        /**
         * PermissionResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        PermissionResponse: {
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
            code: string;
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
            description: Record<string, never>;
        };
        /**
         * SocialLoginResponse
         * @description null
         * @default null
         * @example null
         * @constant
         */
        SocialLoginResponse: {
            /**
             * @description null
             * @default success
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
            message: string;
            /**
             * @description null
             * @default null
             * @example null
             * @constant
             */
            instructions: string;
        };
    };
}
