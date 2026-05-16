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
  token = $state<string | null>(null); // CNS V2.2: Phụ thuộc vào Cookie, token state chỉ để tương thích ngược
  isAuthenticated = $derived(!!this.user); // R00: Elite - Xác thực dựa trên Profile thực

  constructor() {
    if (browser) {
      const savedUser = localStorage.getItem('user_info');
      if (savedUser) {
        try {
          this.user = JSON.parse(savedUser);
        } catch (e) {
          localStorage.removeItem('user_info');
          console.error("[AuthStore] Corrupted user_info purged.", e);
        }
        // Chỉ re-verify khi đã có user cache — tránh API call vô ích
        // cho khách vãng lai và tránh cross-territory session pickup.
        this.fetchCurrentUser();
      }
    }
  }

  setSession(token: string, user: User) {
    this.token = token;
    this.user = user;
    if (browser) {
      // R00: Chỉ lưu User Info để hiển thị nhanh, Token nằm trong HttpOnly Cookie
      localStorage.setItem('user_info', JSON.stringify(user));

      // Elite V2.2: Sync with permissionState immediately
      permissionState.syncFromToken();

      // Elite V3.0: Delayed sync message
      setTimeout(() => {
          getClientUi().showToast(`Chào mừng ${user.name} đã quay trở lại!`, 'success');
      }, 800);
    }
  }

  logout() {
    const name = this.user?.name || 'Quý khách';
    this.token = null;
    this.user = null;
    if (browser) {
      // Purge legacy localStorage tokens
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      localStorage.removeItem('admin_token');
      
      // Privacy Protocol: Purge order tracking persistence
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('order_verify_')) localStorage.removeItem(key);
      });

      // Clear local notification state
      import('./notification.svelte').then(({ getNotificationState }) => {
          getNotificationState().setNotifications([]);
      });

      getClientUi().showToast(`Hẹn gặp lại ${name}!`, 'info');

      // R00: Emit logout event — components listen and handle navigation.
      // Store chỉ quản lý state, KHÔNG tự navigate (Zero-Hydration principle).
      window.dispatchEvent(new CustomEvent('auth:logout'));
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
    }

    // Update other top-level fields (type-safe via Object.assign)
    const { extra_metadata: _, ...rest } = partial;
    Object.assign(this.user, rest);

    if (browser) {
      localStorage.setItem('user_info', JSON.stringify(this.user));
    }
  }

  async fetchCurrentUser() {
    try {
      const user = await import('../utils/apiClient').then(m => 
        m.apiClient.get<User>('/client/user/profile')
      );
      this.user = user;
      if (browser) {
        localStorage.setItem('user_info', JSON.stringify(user));
      }
      return user;
    } catch (e) {
      // CNS V2.2: Nếu fetch profile lỗi (401), clear local user state
      if (this.user) {
        this.user = null;
        if (browser) localStorage.removeItem('user_info');
      }
      return null;
    }
  }
}

export const authStore = new AuthStore();
