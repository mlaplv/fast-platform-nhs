import { browser } from '$app/environment';
import { getClientUi } from './commerce/ui.svelte';

export interface User {
  id: string;
  email: string;
  name: string;
  username?: string;
  role: string;
  gender?: string;
  dob?: string;
  avatar_url?: string;
  extra_metadata?: {
    tier?: 'MEMBER' | 'SILVER' | 'GOLD' | 'PLATINUM';
    points?: number;
    skinProfile?: {
      skinType: string;
      concerns: string[];
      sensitivity: number;
    };
    [key: string]: any;
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

      // Step 2: Special handling for nested skinProfile
      if (partialMeta.skinProfile) {
        this.user.extra_metadata.skinProfile = {
          ...(currentMeta.skinProfile || {}),
          ...partialMeta.skinProfile
        };
      }
      
      console.log('🔄 [AuthStore] Đã đồng bộ extra_metadata:', $state.snapshot(this.user.extra_metadata));
    }

    // Update other top-level fields
    Object.keys(partial).forEach(key => {
      if (key !== 'extra_metadata' && partial[key as keyof User] !== undefined) {
        (this.user as any)[key] = partial[key as keyof User];
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
