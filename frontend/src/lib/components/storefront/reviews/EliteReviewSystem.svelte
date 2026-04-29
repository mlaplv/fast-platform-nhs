<script lang="ts">
  import { onMount } from 'svelte';
  import { createReviewStore } from '$lib/state/commerce/reviewStore.svelte';
  import type { ReviewEntityType } from '$lib/types/commerce/review';
  import ReviewCard from './ReviewCard.svelte';
  import { Star, MessageSquare, Image, Loader2, ChevronDown } from 'lucide-svelte';
  import { fade, fly } from 'svelte/transition';

  interface Props {
    entityId: string;
    entityType: ReviewEntityType;
    mode?: 'full' | 'snippet';
    title?: string;
  }
  let { entityId, entityType, mode = 'full', title = 'Đánh giá từ khách hàng' }: Props = $props();

  const store = createReviewStore(entityId, entityType);
  let activeFilter = $state<'all' | number | 'media'>('all');

  onMount(() => {
    store.fetchStats();
    store.fetchReviews();
  });

  function setFilter(filter: 'all' | number | 'media') {
    activeFilter = filter;
    const rating = typeof filter === 'number' ? filter : undefined;
    const hasMedia = filter === 'media';
    store.fetchReviews(rating, hasMedia);
  }
</script>

<div class="elite-review-system {mode}">
  {#if mode === 'full'}
    <div class="review-header-section">
      <h2 class="section-title">{title}</h2>
      
      {#if store.stats}
        <div class="stats-overview" in:fade>
          <div class="avg-rating">
            <span class="score">{store.stats.average_rating}</span>
            <div class="stars">
               {#each Array(5) as _, i}
                <Star size={20} fill={i < Math.round(store.stats.average_rating) ? "#f59e0b" : "none"} color="#f59e0b" />
              {/each}
            </div>
            <span class="total">{store.stats.total_count} đánh giá</span>
          </div>

          <div class="filter-tabs">
            <button class="tab {activeFilter === 'all' ? 'active' : ''}" onclick={() => setFilter('all')}>
              Tất cả
            </button>
            <button class="tab {activeFilter === 5 ? 'active' : ''}" onclick={() => setFilter(5)}>
              5 Sao
            </button>
            <button class="tab {activeFilter === 'media' ? 'active' : ''}" onclick={() => setFilter('media')}>
              <Image size={14} /> Có ảnh/video
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <div class="review-list">
    {#if store.isLoading && store.reviews.length === 0}
      <div class="loading-state">
        <Loader2 class="animate-spin" />
        <span>Đang tải đánh giá...</span>
      </div>
    {:else if store.reviews.length > 0}
      {#each store.reviews as review (review.id)}
        <ReviewCard {review} compact={mode === 'snippet'} />
      {/each}

      {#if store.reviews.length < store.total}
        <button class="load-more-btn" onclick={() => store.loadMore()} disabled={store.isLoading}>
          {#if store.isLoading}
            <Loader2 size={16} class="animate-spin" />
          {:else}
            Xem thêm đánh giá <ChevronDown size={16} />
          {/if}
        </button>
      {/if}
    {:else}
      <div class="empty-state">
        <MessageSquare size={48} strokeWidth={1} />
        <p>Chưa có đánh giá nào cho nội dung này.</p>
        <p class="sub">Hãy là người đầu tiên chia sẻ cảm nhận của bạn!</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .elite-review-system {
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
  }

  .section-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 2rem;
    color: #111827;
    text-align: center;
  }

  .stats-overview {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 2.5rem;
    padding: 2.5rem;
    background: radial-gradient(circle at 100% 100%, rgba(255, 255, 255, 0.6) 0%, rgba(255, 255, 255, 0.3) 100%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.7);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.03);
  }

  .avg-rating {
    text-align: center;
  }

  .avg-rating .score {
    font-size: 3rem;
    font-weight: 800;
    color: #111827;
    line-height: 1;
    display: block;
  }

  .avg-rating .stars {
    display: flex;
    gap: 0.25rem;
    margin: 0.5rem 0;
  }

  .avg-rating .total {
    font-size: 0.875rem;
    color: #6b7280;
  }

  .filter-tabs {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .tab {
    padding: 0.5rem 1rem;
    border-radius: 100px;
    font-size: 0.875rem;
    font-weight: 500;
    background: white;
    border: 1px solid #e5e7eb;
    color: #4b5563;
    display: flex;
    align-items: center;
    gap: 0.375rem;
    transition: all 0.2s;
  }

  .tab:hover { border-color: #d1d5db; }
  .tab.active {
    background: #111827;
    border-color: #111827;
    color: white;
  }

  .loading-state, .empty-state {
    padding: 4rem 2rem;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    color: #6b7280;
  }

  .empty-state p { font-weight: 600; color: #374151; margin-bottom: 0.25rem; }
  .empty-state .sub { font-weight: 400; font-size: 0.875rem; }

  .load-more-btn {
    width: 100%;
    padding: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-weight: 600;
    font-size: 0.875rem;
    color: #4b5563;
    background: rgba(255, 255, 255, 0.5);
    border: 1px dashed #d1d5db;
    border-radius: 1rem;
    margin-top: 1rem;
    transition: all 0.2s;
  }

  .load-more-btn:hover { background: rgba(255, 255, 255, 0.8); border-color: #9ca3af; }

  /* Snippet mode */
  .snippet .section-title { font-size: 1.25rem; text-align: left; }
</style>
