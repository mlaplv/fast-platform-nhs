<script lang="ts">
  import { onMount } from 'svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import MessageCircleMore from "@lucide/svelte/icons/message-circle-more";
  import Star from "@lucide/svelte/icons/star";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import Play from "@lucide/svelte/icons/play";
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import PenLine from "@lucide/svelte/icons/pen-line";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";
  import ThumbsUp from "@lucide/svelte/icons/thumbs-up";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import MinusCircle from "@lucide/svelte/icons/minus-circle";
  import type { Product, Category, Review, ReviewStats } from '$lib/types';
  import { apiClient } from '$lib/utils/apiClient';

  interface Props {
    product: Product | Category;
    entityType?: 'PRODUCT' | 'CATEGORY' | 'NEWS';
  }

  let { product, entityType = 'PRODUCT' }: Props = $props();

  let reviews = $state<Review[]>([]);
  let stats = $state<ReviewStats | null>(null);
  let isLoading = $state(true);
  let activeDropdownId = $state<string | null>(null);

  const ui = getClientUi();

  async function handleLike(review: Review & { _isLiked?: boolean }) {
    if (review._isLiked) return;
    review.likes_count = (review.likes_count || 0) + 1;
    review._isLiked = true;
    try {
      const res = await apiClient.post<{new_count: number}>(`/client/reviews/${review.id}/like`);
      if (res.new_count !== undefined) {
        review.likes_count = res.new_count;
      }
    } catch (e) {
      review.likes_count -= 1;
      review._isLiked = false;
      ui.showToast('Lỗi khi thích đánh giá', 'error');
    }
  }

  function handleReportReview(reviewId: string) {
    activeDropdownId = null;
    ui.openReportReview(reviewId);
  }

  async function fetchStats() {
    try {
      stats = await apiClient.get<ReviewStats>(`/client/reviews/stats`, {
        params: {
          entity_type: entityType,
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
          entity_type: entityType,
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

  const averageRating = $derived(stats?.average_rating || (product as any).metadata?.rating || '5.0');
  const reviewCount = $derived(stats?.total_count || 0);

  function isVideo(url: string) {
    return url.match(/\.(mp4|webm|mov)$/i) || url.includes('video');
  }

  // Elite 2026: AI Customer Sentiment Summary
  const meta = $derived((product as any)?.metadata || {});
  const aiSummary = $derived(meta.customer_sentiment_summary);
  const positiveNotes = $derived(meta.positive_notes || []);
  const negativeNotes = $derived(meta.negative_notes || []);
  const hasAiSentiment = $derived(aiSummary || positiveNotes.length > 0 || negativeNotes.length > 0);
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

  {#if hasAiSentiment}
    <div class="ai-sentiment-box mb-4 p-4 rounded-lg bg-gradient-to-br from-[#FFF9F6] to-white border border-[#ee4d2d]/10 shadow-sm relative overflow-hidden">
       <div class="flex items-center gap-2 mb-2 relative z-10">
         <Sparkles size={16} class="text-[#ee4d2d] fill-current" />
         <h3 class="text-[12px] font-black uppercase tracking-widest text-[#ee4d2d]">AI Tổng Hợp Đánh Giá</h3>
       </div>
       {#if aiSummary}
         <p class="text-[13px] text-gray-700 leading-relaxed mb-3 font-medium relative z-10">{aiSummary}</p>
       {/if}
       <div class="flex flex-col gap-3 relative z-10">
          {#if positiveNotes.length > 0}
            <div>
              <span class="text-[10px] font-black uppercase tracking-widest text-[#00bfa5] mb-1.5 block">Khách hàng ưng ý</span>
              <ul class="space-y-1.5">
                {#each positiveNotes as note}
                  <li class="text-[12px] text-gray-600 flex items-start gap-1.5"><CheckCircle2 size={14} class="text-[#00bfa5] mt-0.5 shrink-0" /> <span class="leading-tight">{note}</span></li>
                {/each}
              </ul>
            </div>
          {/if}
          {#if negativeNotes.length > 0}
            <div class="pt-2 border-t border-gray-100">
              <span class="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-1.5 block">Điểm cần lưu ý</span>
              <ul class="space-y-1.5">
                {#each negativeNotes as note}
                  <li class="text-[12px] text-gray-500 flex items-start gap-1.5"><MinusCircle size={14} class="text-gray-300 mt-0.5 shrink-0" /> <span class="leading-tight">{note}</span></li>
                {/each}
              </ul>
            </div>
          {/if}
       </div>
    </div>
  {/if}

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
        <div class="ml-auto flex items-center gap-3 relative">
          <button 
            onclick={() => activeDropdownId = activeDropdownId === review.id ? null : review.id}
            class="text-gray-300 hover:text-gray-600 transition-colors">
            <MoreHorizontal size={16} />
          </button>
          
          {#if activeDropdownId === review.id}
            <div class="absolute right-0 bottom-full mb-2 w-32 bg-white border border-gray-100 shadow-xl z-50 py-1 rounded-lg overflow-hidden">
              <button 
                onclick={() => handleReportReview(review.id)}
                class="w-full text-left px-4 py-2 text-[10px] font-bold text-red-500 hover:bg-red-50 transition-colors uppercase tracking-widest"
              >
                Báo cáo
              </button>
            </div>
          {/if}

          <button 
            onclick={() => handleLike(review)}
            class="flex items-center gap-1 {review._isLiked ? 'text-luxury-copper' : 'text-gray-300'} transition-all"
          >
            <ThumbsUp size={16} fill={review._isLiked ? "currentColor" : "none"} />
            <span class="text-xs font-bold">{review.likes_count || 0}</span>
          </button>
        </div>
      </div>

      <div class="review-content prose-osmo-mini">
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

  :global(.prose-osmo-mini p) { margin: 0 !important; }
</style>
