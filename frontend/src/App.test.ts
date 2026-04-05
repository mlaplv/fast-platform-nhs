import { describe, it, expect } from 'vitest';
import { ADMIN_PROTECTED_PATHS } from '$lib/constants/routes';

describe('System Integrity: Routes', () => {
    it('should have required admin protected paths defined', () => {
        expect(ADMIN_PROTECTED_PATHS as readonly string[]).toContain('/chat');
        expect(ADMIN_PROTECTED_PATHS as readonly string[]).toContain('/settings');
    });

    it('should enforce read-only constants for routes', () => {
        expect(Object.isFrozen(ADMIN_PROTECTED_PATHS)).toBe(true);
    });
});

