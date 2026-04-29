<script lang="ts">
  import type { Review } from '$lib/types/commerce/review';
  import { Star, ThumbsUp, CheckCircle2, Play } from 'lucide-svelte';
  import { fade } from 'svelte/transition';

  interface Props {
    review: Review;
    compact?: boolean;
  }
  let { review, compact = false }: Props = $props();

  const formattedDate = new Date(review.created_at).toLocaleDateString('vi-VN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  let isLiked = $state(false);
  let likes = $state(review.likes_count || 0);

  function toggleLike() {
    isLiked = !isLiked;
    likes += isLiked ? 1 : -1;
  }
</script>

<div class="elite-review-card {compact ? 'compact' : ''}" in:fade>
  <div class="review-header">
    <div class="customer-info">
      <div class="avatar">{review.initial || review.customer_name[0]}</div>
      <div class="meta">
        <div class="name">
          {review.customer_name}
          <CheckCircle2 size={14} class="verified-icon" />
        </div>
        <div class="date">{formattedDate}</div>
      </div>
    </div>
    <div class="rating">
      {#each Array(5) as _, i}
        <Star 
          size={compact ? 12 : 14} 
          fill={i < review.rating ? "currentColor" : "none"} 
          class={i < review.rating ? "star-active" : "star-inactive"} 
        />
      {/each}
    </div>
  </div>

  <div class="review-body">
    {#if review.attributes && Object.keys(review.attributes).length > 0}
      <div class="attributes">
        {#each Object.entries(review.attributes) as [key, value]}
          {#if value}
            <span class="attr-tag">{key}: <strong>{value}</strong></span>
          {/if}
        {/each}
      </div>
    {/if}
    
    <p class="content">{review.content}</p>

    {#if review.attachments && review.attachments.length > 0}
      <div class="attachments">
        {#each review.attachments as media}
          <button class="media-thumb">
            <img src={media.url} alt="Review attachment" />
            {#if media.type === 'video'}
              <div class="video-overlay"><Play size={16} fill="white" /></div>
            {/if}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <div class="review-footer">
    <button class="like-btn {isLiked ? 'active' : ''}" onclick={toggleLike}>
      <ThumbsUp size={14} />
      <span>Hữu ích ({likes})</span>
    </button>
  </div>
</div>

<style>
  .elite-review-card {
    background: radial-gradient(circle at 0% 0%, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0.4) 100%);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 1.5rem;
    padding: 2rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .elite-review-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.08);
  }

  .review-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .customer-info {
    display: flex;
    gap: 0.75rem;
    align-items: center;
  }

  .avatar {
    width: 2.5rem;
    height: 2.5rem;
    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    color: #4b5563;
    font-size: 1rem;
    border: 1px solid rgba(0, 0, 0, 0.05);
  }

  .name {
    font-weight: 600;
    color: #111827;
    font-size: 0.9375rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .verified-icon {
    color: #10b981;
  }

  .date {
    font-size: 0.75rem;
    color: #6b7280;
  }

  .rating {
    display: flex;
    gap: 0.125rem;
  }

  .star-active { color: #f59e0b; }
  .star-inactive { color: #d1d5db; }

  .review-body .content {
    font-size: 0.9375rem;
    line-height: 1.6;
    color: #374151;
    margin: 0.75rem 0;
    white-space: pre-wrap;
  }

  .attributes {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
  }

  .attr-tag {
    font-size: 0.75rem;
    padding: 0.25rem 0.625rem;
    background: rgba(0, 0, 0, 0.03);
    border-radius: 100px;
    color: #4b5563;
  }

  .attachments {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }

  .media-thumb {
    width: 5rem;
    height: 5rem;
    border-radius: 0.75rem;
    overflow: hidden;
    position: relative;
    flex-shrink: 0;
    border: 1px solid rgba(0, 0, 0, 0.05);
  }

  .media-thumb img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .video-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .review-footer {
    margin-top: 1.25rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(0, 0, 0, 0.05);
  }

  .like-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    color: #6b7280;
    transition: all 0.2s;
  }

  .like-btn:hover { color: #111827; }
  .like-btn.active { color: #2563eb; font-weight: 500; }

  /* Compact Mode for lists/previews */
  .elite-review-card.compact {
    padding: 1rem;
    margin-bottom: 0.75rem;
  }
  
  .elite-review-card.compact .avatar { width: 2rem; height: 2rem; font-size: 0.875rem; }
</style>
