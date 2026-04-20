import { browser } from '$app/environment';
import { getClientUi } from './commerce/ui.svelte';
import { permissionState } from './permissions.svelte';

export interface UserAddress {
  id: string;
  name: string;
  phone: string;
  city: string;
  ward: string;
  address: string;
  isDefault: boolean;
}

export interface User {
  id: string;
  email: string;
  name: string;
  username?: string;
  role: string;
  gender?: string;
  dob?: string;
  avatar_url?: string;
  phone?: string;
  has_password?: boolean;
  extra_metadata?: {
    tier?: 'STANDARD' | 'SILVER' | 'GOLD' | 'PLATINUM';
    points?: number;
    addresses?: UserAddress[];
    skin_profile?: {
      skinType: string;
      concerns: string[];
      sensitivity: number;
    };
    [key: string]: unknown;
  };
}

class AuthStore {
  user = $state<User | null>(null);
  token = $state<string | null>(null);
  isAuthenticated = $derived(!!this.token);

  constructor() {
    if (browser) {
      const savedToken = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user_info');
      if (savedToken) {
        this.token = savedToken;
      }
      if (savedUser) {
        try {
          this.user = JSON.parse(savedUser);
        } catch (e) {
          console.error("Failed to parse user info", e);
        }
      }
    }
  }

  setSession(token: string, user: User) {
    this.token = token;
    this.user = user;
    if (browser) {
      localStorage.setItem('access_token', token);
      localStorage.setItem('user_info', JSON.stringify(user));

      // Elite V2.2: Sync with permissionState immediately
      permissionState.syncFromToken();

      // Elite V3.0: Delayed sync message — wait for hydration to ensure Bell is ready
      setTimeout(() => {
          getClientUi().showToast(`Chào mừng ${user.name} đã quay trở lại!`, 'success');
      }, 800);
    }
  }

  logout() {
    const name = this.user?.name || 'Sếp';
    this.token = null;
    this.user = null;
    if (browser) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      localStorage.removeItem('admin_token');
      
      // Elite V3.0: Clear local notification state on logout to prevent mixed data
      import('./notification.svelte').then(({ getNotificationState }) => {
          getNotificationState().setNotifications([]);
      });

      getClientUi().showToast(`Hẹn gặp lại ${name}!`, 'info');
    }
  }

  /**
   * Elite V3.0: Sync partial user data to state and localStorage.
   * Ensures UI updates immediately and persistence across reloads.
   */
  syncUser(partial: Partial<User>) {
    if (!this.user) return;
    
    // Elite V3.1: Robust deep merge for extra_metadata
    if (partial.extra_metadata) {
      if (!this.user.extra_metadata) {
        this.user.extra_metadata = {};
      }

      const currentMeta = this.user.extra_metadata;
      const partialMeta = partial.extra_metadata;

      // Step 1: Merge top-level extra_metadata keys
      this.user.extra_metadata = {
        ...currentMeta,
        ...partialMeta
      };

      // Step 2: Special handling for nested skin_profile
      if (partialMeta.skin_profile) {
        this.user.extra_metadata.skin_profile = {
          ...(currentMeta.skin_profile || {}),
          ...partialMeta.skin_profile
        };
      }
      
      // Elite V2.2: Silent sync for better UX
      this.notifyProgress?.();
    }

    // Update other top-level fields
    const keys = Object.keys(partial) as Array<keyof User>;
    keys.forEach(key => {
      if (key !== 'extra_metadata' && partial[key] !== undefined) {
        // @ts-expect-error - Elite V3.1: Runtime sync for Svelte state
        this.user[key] = partial[key];
      }
    });

    if (browser) {
      localStorage.setItem('user_info', JSON.stringify(this.user));
    }
  }

  async fetchCurrentUser() {
    if (!this.token) return null;
    return this.user;
  }
}

export const authStore = new AuthStore();
