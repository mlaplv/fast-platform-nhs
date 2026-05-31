import { authStore } from '../authStore.svelte';
import { apiClient } from '$lib/utils/apiClient';
import { loyaltyStore } from './loyalty.svelte';

export interface CheckinDay {
  day: number;
  reward: number;
  is_completed: boolean;
  is_today: boolean;
  is_bonus: boolean;
}

export interface CheckinStatus {
  current_streak: number;
  is_checked_in_today: boolean;
  cycle_length: number;
  today_reward: number;
  days: CheckinDay[];
  countdown_to_reset: string; // "HH:MM:SS"
  total_checkin_today: number; // social proof count
}

class CheckinStore {
  status = $state<CheckinStatus | null>(null);
  loading = $state(false);
  claiming = $state(false);
  error = $state<string | null>(null);
  // Controls popup visibility
  showPopup = $state(false);
  showHistory = $state(false);

  // Computed: whether user can still claim today
  canClaim = $derived(
    this.status !== null && !this.status.is_checked_in_today && !this.claiming
  );

  async fetchStatus() {
    if (!authStore.isAuthenticated) return;
    this.loading = true;
    this.error = null;
    try {
      const res = await apiClient.get<CheckinStatus>('/api/v1/client/user/loyalty/checkin');
      this.status = res;
    } catch (err: unknown) {
      console.error('[CheckinStore] fetchStatus error:', err);
      this.error = err instanceof Error ? err.message : 'Không tải được trạng thái điểm danh';
    } finally {
      this.loading = false;
    }
  }

  async claimReward(): Promise<boolean> {
    if (!this.canClaim || this.claiming) return false;
    this.claiming = true;
    this.error = null;
    try {
      const res = await apiClient.post<{ message: string; points_earned: number; new_balance: number; new_streak: number }>(
        '/api/v1/client/user/loyalty/checkin',
        {}
      );
      // Optimistic UI update — cập nhật trạng thái ngay lập tức
      if (this.status) {
        this.status = {
          ...this.status,
          is_checked_in_today: true,
          current_streak: res.new_streak,
        };
      }
      // Sync lại loyaltyStore để cập nhật số dư điểm ở toàn app
      await loyaltyStore.fetchLoyalty();
      return true;
    } catch (err: unknown) {
      console.error('[CheckinStore] claimReward error:', err);
      this.error = err instanceof Error ? err.message : 'Điểm danh thất bại, vui lòng thử lại';
      return false;
    } finally {
      this.claiming = false;
    }
  }

  openPopup() {
    this.showPopup = true;
    this.showHistory = false;
    // Auto-fetch fresh status khi mở popup
    this.fetchStatus();
  }

  closePopup() {
    this.showPopup = false;
    this.showHistory = false;
  }

  openHistory() {
    this.showHistory = true;
  }

  closeHistory() {
    this.showHistory = false;
  }
}

export const checkinStore = new CheckinStore();
