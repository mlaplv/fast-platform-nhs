<script lang="ts">
  import { ChevronRight, MessageCircleMore } from 'lucide-svelte';
  import type { Product } from '$lib/types';

  interface Props {
    product: Product;
  }

  let { product }: Props = $props();
  const productReviews = $derived(Array.isArray((product.metadata as any)?.reviews) ? (product.metadata as any).reviews : []);
</script>

<section id="reviews" class="content-section">
  <div class="section-header">
    <h2 class="section-title">Đánh giá khách hàng</h2>
    <button class="view-all">Xem tất cả <ChevronRight size={14} /></button>
  </div>

  {#if productReviews.length === 0}
    <div class="empty-reviews-state">
      <div class="score-big">{(product.metadata as any)?.rating || '5.0'}<span>/5</span></div>
      <div class="flex flex-col items-center justify-center py-6 text-gray-400">
        <MessageCircleMore size={40} class="mb-2 opacity-20" />
        <p class="text-sm">Chưa có đánh giá cho sản phẩm này</p>
      </div>
    </div>
  {:else}
    <div class="reviews-summary">
      <div class="score-big">{(product.metadata as any)?.rating || '5.0'}<span>/5</span></div>
      <div class="review-tags">
        <span class="tag active">Tất cả ({productReviews.length})</span>
      </div>
    </div>
    {#each productReviews.slice(0, 3) as review}
      <div class="review-item">
        <div class="user-info">
          <div class="avatar">{(review.user || review.name || 'U').charAt(0)}</div>
          <div>
            <div class="username">{review.user || review.name || 'Ẩn danh'}</div>
            <div class="stars-tiny">{'⭐'.repeat(review.rating || 5)}</div>
          </div>
        </div>
        <p class="comment">{review.comment || review.content}</p>
        <div class="review-date">{review.date || 'Gần đây'}</div>
      </div>
    {/each}
  {/if}
</section>

<style>
  .content-section { background: white; padding: 16px; }
  .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .section-title { font-size: 14px; font-weight: 700; color: #333; margin: 0; }
  .view-all { background: none; border: none; font-size: 12px; color: #ff2556; display: flex; align-items: center; gap: 4px; }
  
  .score-big { font-size: 24px; font-weight: 900; color: #333; display: flex; align-items: baseline; gap: 2px; }
  .score-big span { font-size: 14px; color: #999; font-weight: 500; }
  
  .review-item { padding: 12px 0; border-bottom: 1px solid #f5f5f5; }
  .review-item:last-child { border-bottom: none; }
  .user-info { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .avatar { width: 32px; height: 32px; background: #eee; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; color: #666; }
  .username { font-size: 12px; font-weight: 600; color: #444; }
  .stars-tiny { font-size: 8px; }
  .comment { font-size: 13px; color: #333; line-height: 1.5; margin: 0 0 6px 0; }
  .review-date { font-size: 11px; color: #999; }
</style>
