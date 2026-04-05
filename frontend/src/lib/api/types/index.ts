/**
 * Unified API Types Entry Point
 * Merges domain-specific types into a single interface for backward compatibility.
 * Compliance: Elite V2.2 (< 500 lines)
 */

import type { paths as CorePaths, components as CoreComponents } from './core';
import type { paths as AuthPaths, components as AuthComponents } from './auth';
import type { paths as CommercePaths, components as CommerceComponents } from './commerce';
import type { paths as ContentPaths, components as ContentComponents } from './content';
import type { paths as CampaignPaths, components as CampaignComponents } from './campaigns';
import type { paths as ChatPaths, components as ChatComponents } from './chat';
import type { paths as MediaPaths, components as MediaComponents } from './media';
import type { paths as AdminPaths, components as AdminComponents } from './admin';
import type { paths as NotificationPaths, components as NotificationComponents } from './notifications';
import type { paths as SettingsPaths, components as SettingsComponents } from './settings';

// Merge all paths
export type paths = CorePaths & 
    AuthPaths & 
    CommercePaths & 
    ContentPaths & 
    CampaignPaths & 
    ChatPaths & 
    MediaPaths & 
    AdminPaths & 
    NotificationPaths & 
    SettingsPaths;

// Webhooks (Reserved)
export type webhooks = Record<string, never>;

// Merge all components
export interface components {
    schemas: CoreComponents['schemas'] & 
        AuthComponents['schemas'] & 
        CommerceComponents['schemas'] & 
        ContentComponents['schemas'] & 
        CampaignComponents['schemas'] & 
        ChatComponents['schemas'] & 
        MediaComponents['schemas'] & 
        AdminComponents['schemas'] & 
        NotificationComponents['schemas'] & 
        SettingsComponents['schemas'];
}

// Global Definitions
export type $defs = Record<string, never>;
export type operations = Record<string, never>;
