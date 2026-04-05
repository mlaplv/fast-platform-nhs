/**
 * API Types Monolith Replacement
 * Domain-specific types are now modularized in ./types/
 * Compliance: Elite V2.2 (< 500 lines)
 */

export * from './types/index';
export type { paths, components, webhooks, $defs, operations } from './types/index';
