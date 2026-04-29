import { $state } from 'svelte/runes';
import type { Review, ReviewStats, ReviewEntityType, ReviewListResponse } from '$lib/types/commerce/review';
import { apiClient } from '$lib/utils/apiClient';

/**
 * Elite Review Store (V2.2 Standard)
 * Centralized logic for fetching, filtering, and interacting with reviews.
 */
export function createReviewStore(entityId: string, entityType: ReviewEntityType) {
  let reviews = $state<Review[]>([]);
  let stats = $state<ReviewStats | null>(null);
  let isLoading = $state(false);
  let total = $state(0);
  let offset = $state(0);
  const limit = 10;

  async function fetchStats() {
    try {
      const data = await apiClient.get<ReviewStats>(`/client/reviews/stats`, {
        params: { entity_type: entityType, entity_id: entityId }
      });
      stats = data;
    } catch (e) {
      console.error("[ReviewStore] Failed to fetch stats:", e);
    }
  }

  async function fetchReviews(rating?: number, hasMedia?: boolean, reset = true) {
    if (reset) {
      offset = 0;
      reviews = [];
    }
    
    isLoading = true;
    try {
      const params: Record<string, string> = {
        entity_type: entityType,
        entity_id: entityId,
        status: 'APPROVED',
        limit: limit.toString(),
        offset: offset.toString()
      };
      
      if (rating) params.rating = rating.toString();
      if (hasMedia) params.has_media = 'true';

      const data = await apiClient.get<ReviewListResponse>(`/client/reviews`, { params });
      
      const mapped = data.items.map(r => ({
        ...r,
        name: r.customer_name,
        initial: r.customer_name?.charAt(0).toUpperCase() || '?'
      }));

      if (reset) reviews = mapped;
      else reviews = [...reviews, ...mapped];
      
      total = data.total;
    } catch (e) {
      console.error("[ReviewStore] Failed to fetch reviews:", e);
    } finally {
      isLoading = false;
    }
  }

  async function loadMore() {
    if (isLoading || reviews.length >= total) return;
    offset += limit;
    await fetchReviews(undefined, undefined, false);
  }

  return {
    get reviews() { return reviews; },
    get stats() { return stats; },
    get isLoading() { return isLoading; },
    get total() { return total; },
    fetchStats,
    fetchReviews,
    loadMore
  };
}
