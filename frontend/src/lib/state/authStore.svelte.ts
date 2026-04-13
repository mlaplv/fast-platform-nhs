import { browser } from '$app/environment';
import { getClientUi } from './commerce/ui.svelte';

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
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

  async fetchCurrentUser() {
    if (!this.token) return null;
    return this.user;
  }
}

export const authStore = new AuthStore();
