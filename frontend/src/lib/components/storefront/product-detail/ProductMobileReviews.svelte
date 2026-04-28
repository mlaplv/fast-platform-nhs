<script lang="ts">
  import { onMount } from 'svelte';
  import { ChevronRight, MessageCircleMore, Star, Loader2, Play, CheckCircle2, PenLine } from 'lucide-svelte';
  import type { Product, Review, ReviewStats } from '$lib/types';
  import { apiClient } from '$lib/utils/apiClient';

  interface Props {
    product: Product;
  }

  let { product }: Props = $props();

  let reviews = $state<Review[]>([]);
  let stats = $state<ReviewStats | null>(null);
  let isLoading = $state(true);

  async function fetchStats() {
    try {
      stats = await apiClient.get<ReviewStats>(`/client/reviews/stats`, {
        params: {
          entity_type: 'PRODUCT',
          entity_id: product.id
        }
      });
    } catch (e) {
      console.error("Lỗi fetch stats:", e);
    }
  }

  async function fetchReviews() {
    isLoading = true;
    try {
      const data = await apiClient.get<{ items: Review[] }>(`/client/reviews`, {
        params: {
          entity_type: 'PRODUCT',
          entity_id: product.id,
          status: 'APPROVED',
          limit: '1'
        }
      });
      reviews = data.items;
    } catch (e) {
      console.error("Lỗi fetch reviews:", e);
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    fetchStats();
    fetchReviews();
  });

  const averageRating = $derived(stats?.average_rating || product.metadata?.rating || '5.0');
  const reviewCount = $derived(stats?.total_count || 0);

  function isVideo(url: string) {
    return url.match(/\.(mp4|webm|mov)$/i) || url.includes('video');
  }
</script>

<section id="reviews" class="content-section">
  <div class="section-header">
    <div class="flex items-center gap-2">
      <h2 class="section-title">Đánh giá khách hàng</h2>
      {#if reviewCount > 0}
        <span class="text-[10px] bg-gray-100 px-1.5 py-0.5 rounded-full text-gray-500 font-bold">{reviewCount}</span>
      {/if}
    </div>
    {#if reviewCount > 0}
      <a href="/{product.slug}/reviews" class="view-all text-luxury-copper">Xem tất cả <ChevronRight size={14} /></a>
    {:else}
      <a href="/{product.slug}/reviews?write=true" class="view-all text-luxury-copper">
        <PenLine size={14} class="mr-1" /> Viết <ChevronRight size={14} />
      </a>
    {/if}
  </div>

  {#if isLoading}
    <div class="flex flex-col items-center justify-center py-10 text-gray-400">
      <Loader2 size={24} class="animate-spin mb-2" />
      <p class="text-xs uppercase tracking-widest font-bold">Đang tải đánh giá...</p>
    </div>
  {:else if reviews.length === 0}
    <div class="empty-reviews-state">
      <div class="score-big">{averageRating}<span>/5</span></div>
      <div class="flex flex-col items-center justify-center py-6 text-gray-400">
        <MessageCircleMore size={40} class="mb-2 opacity-20" />
        <p class="text-sm">Chưa có đánh giá cho sản phẩm này</p>
      </div>
    </div>
  {:else}
    {@const review = reviews[0]}
    <div class="viral-review-card">
      <div class="user-row">
        <div class="avatar">{(review.customer_name || 'U').charAt(0).toUpperCase()}</div>
        <div class="user-meta">
          <div class="flex items-center gap-1.5">
            <span class="username">{review.customer_name || 'Khách hàng'}</span>
            <span class="verified-badge"><CheckCircle2 size={10} fill="currentColor" class="text-luxury-copper" /></span>
          </div>
          <div class="stars-row flex gap-0.5">
            {#each Array(5) as _, i}
              <Star size={10} class="{i < review.rating ? 'text-luxury-copper fill-current' : 'text-gray-200'}" />
            {/each}
          </div>
        </div>
        <div class="review-date-mini">{new Date(review.created_at).toLocaleDateString('vi-VN')}</div>
      </div>

      <div class="review-content prose-micsmo-mini">
        {@html review.content}
      </div>

      {#if review.attachments && review.attachments.length > 0}
        <div class="media-grid">
          {#each review.attachments.slice(0, 3) as media}
            <div class="media-item">
              {#if isVideo(media.url)}
                <video src={media.url} muted playsinline class="media-preview"></video>
                <div class="play-overlay"><Play size={16} fill="white" class="text-white" /></div>
              {:else}
                <img src={media.url} alt="Review" class="media-preview" />
              {/if}
            </div>
          {/each}
          {#if review.attachments.length > 3}
            <div class="media-more">+{review.attachments.length - 3}</div>
          {/if}
        </div>
      {/if}

      <div class="fomo-footer mt-4 p-3 bg-luxury-peach/10 rounded-lg flex items-center justify-between border border-luxury-peach/20">
        <div class="flex flex-col">
          <span class="text-[11px] font-black text-luxury-copper uppercase tracking-tighter italic">Cảm nhận thực tế</span>
          <span class="text-[9px] text-gray-400 font-bold uppercase tracking-widest mt-0.5">Đã có {reviewCount * 12 + 89} người tin dùng</span>
        </div>
        <a href="/{product.slug}/reviews" class="btn-discover bg-luxury-copper">Khám phá ngay</a>
      </div>
    </div>
  {/if}
</section>

<style>
  .content-section { background: white; padding: 16px; }
  .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .section-title { font-size: 14px; font-weight: 800; color: #222; margin: 0; text-transform: uppercase; letter-spacing: -0.01em; }
  .view-all { font-size: 12px; display: flex; align-items: center; gap: 4px; font-weight: 600; text-decoration: none; }

  .score-big { font-size: 24px; font-weight: 900; color: #333; display: flex; align-items: baseline; gap: 2px; }
  .score-big span { font-size: 14px; color: #999; font-weight: 500; }

  .viral-review-card { position: relative; }
  .user-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
  .avatar { width: 40px; height: 40px; background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 900; color: #666; border: 1px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
  .user-meta { flex: 1; }
  .username { font-size: 13px; font-weight: 700; color: #222; }
  .review-date-mini { font-size: 10px; color: #bbb; font-weight: 500; }

  .review-content { margin-bottom: 12px; font-size: 14px; color: #444; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

  .media-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 4px; }
  .media-item { aspect-ratio: 1; border-radius: 8px; overflow: hidden; position: relative; background: #f9f9f9; border: 1px solid #f0f0f0; }
  .media-preview { width: 100%; height: 100%; object-fit: cover; }
  .play-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.2); }
  .media-more { position: absolute; bottom: 10px; right: 10px; width: 32px; height: 32px; border-radius: 50%; background: rgba(0,0,0,0.6); color: white; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 900; }

  .btn-discover { color: white; font-size: 10px; font-weight: 900; padding: 6px 12px; border-radius: 4px; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 4px 10px rgba(193, 143, 126, 0.2); }

  :global(.prose-micsmo-mini p) { margin: 0 !important; }
</style>
