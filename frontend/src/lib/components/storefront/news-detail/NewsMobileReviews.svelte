<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { ChevronRight, MessageCircleMore, Star, Loader2, Play, CheckCircle2, Camera, Send, X } from 'lucide-svelte';
  import type { Review, ReviewStats } from '$lib/types';
  import { fade, fly, scale } from 'svelte/transition';

  const ui = getClientUi();

  interface Props {
    articleId: string;
    slug: string;
  }

  let { articleId, slug }: Props = $props();

  let reviews = $state<Review[]>([]);
  let stats = $state<ReviewStats | null>(null);
  let isLoading = $state(true);

  // Write Form State
  let showWriteForm = $state(false);
  let isSubmitting = $state(false);
  let submitSuccess = $state(false);
  let newRating = $state(5);
  let newContent = $state('');
  let attachedPhotos = $state<string[]>([]);
  let isUploadingMedia = $state(false);
  let fileInput = $state<HTMLInputElement | null>(null);

  async function fetchStats() {
    try {
      const res = await fetch(`/api/v1/client/reviews/stats?entity_type=NEWS&entity_id=${articleId}`);
      if (res.ok) {
        stats = await res.json();
      }
    } catch (e) {
      console.error("Lỗi fetch stats:", e);
    }
  }

  async function fetchReviews() {
    isLoading = true;
    try {
      const res = await fetch(`/api/v1/client/reviews?entity_type=NEWS&entity_id=${articleId}&status=APPROVED&limit=1`);
      if (res.ok) {
        const data = await res.json();
        reviews = data.items;
      }
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

  const averageRating = $derived(stats?.average_rating || '5.0');
  const reviewCount = $derived(stats?.total_count || 0);

  function isVideo(url: string) {
    return url.match(/\.(mp4|webm|mov)$/i) || url.includes('video');
  }

  const handleWriteReview = () => {
    if (!authStore.isAuthenticated) {
      ui.openLogin(() => {
        showWriteForm = true;
      });
    } else {
      showWriteForm = !showWriteForm;
    }
  };

  const handleFileSelect = async (e: Event) => {
    const target = e.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;
    
    isUploadingMedia = true;
    try {
       for (let i = 0; i < target.files.length; i++) {
           const file = target.files[i];
           const formData = new FormData();
           formData.append('data', file);
           
           const res = await fetch('/api/v1/client/reviews/upload', {
               method: 'POST',
               headers: {
                   'Authorization': `Bearer ${authStore.token}`
               },
               body: formData
           });
           
           if (res.ok) {
               const json = await res.json();
               if (json.data && json.data.file_path) {
                   attachedPhotos = [...attachedPhotos, json.data.file_path];
               }
           }
       }
    } catch (err) {
       console.error("Upload error:", err);
    } finally {
       isUploadingMedia = false;
    }
  };

  async function submitReview() {
    if (!newContent || newContent.length < 5) return;
    isSubmitting = true;
    try {
      const res = await fetch('/api/v1/client/reviews', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authStore.token}`
        },
        body: JSON.stringify({
          entity_type: 'NEWS',
          entity_id: articleId,
          customer_name: authStore.user?.name || 'Khách Micsmo',
          rating: newRating,
          content: newContent,
          attributes: {}, // Optional for mobile
          attachments: attachedPhotos.map(url => ({ 
             url, 
             type: isVideo(url) ? 'video' : 'image' 
          }))
        })
      });
      if (res.ok) {
        submitSuccess = true;
        setTimeout(() => {
          showWriteForm = false;
          submitSuccess = false;
          newContent = '';
          attachedPhotos = [];
          fetchStats();
          fetchReviews();
        }, 2000);
      }
    } catch (e) {
      console.error("Lỗi submit review:", e);
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="px-6 py-10 bg-white border-t border-gray-100">
  <!-- Professional Header -->
  <div class="flex items-center justify-between mb-8 pb-6 border-b border-gray-50">
    <div class="space-y-1.5">
      <h2 class="text-[13px] font-black text-[#0f172a] uppercase tracking-[0.2em] italic leading-none">Phản hồi từ độc giả</h2>
      <div class="flex items-center gap-2.5">
        <div class="flex gap-0.5">
          {#each Array(5) as _, i}
            <Star size={14} class="{i < Math.round(Number(averageRating)) ? 'text-[#C18F7E] fill-current' : 'text-gray-200'}" />
          {/each}
        </div>
        <div class="flex items-baseline gap-1">
          <span class="text-sm font-black text-[#C18F7E]">{averageRating}</span>
          <span class="text-[9px] font-bold text-gray-300 uppercase">({reviewCount} lượt)</span>
        </div>
      </div>
    </div>
    <button onclick={handleWriteReview} class="px-6 py-3 bg-[#C18F7E] text-white text-[10px] font-black uppercase tracking-widest active:scale-95 transition-all shadow-xl shadow-[#C18F7E]/20">
        Viết ngay
    </button>
  </div>

  {#if showWriteForm}
    <div class="mb-10 p-6 bg-gray-50 border border-gray-100" in:fly={{ y: 20 }}>
        {#if submitSuccess}
            <div class="py-6 flex flex-col items-center justify-center text-center" in:scale>
                <CheckCircle2 class="w-12 h-12 text-[#C18F7E] mb-3" />
                <p class="text-sm font-black text-[#0f172a] uppercase tracking-tight">Gửi thành công!</p>
            </div>
        {:else}
            <div class="space-y-6">
                <!-- Rating -->
                <div class="flex items-center justify-between">
                    <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest">Đánh giá của bạn</span>
                    <div class="flex gap-2">
                        {#each Array(5) as _, i}
                            <button onclick={() => newRating = i + 1}>
                                <Star class="w-7 h-7 {i < newRating ? 'text-[#C18F7E] fill-current' : 'text-gray-200'}" />
                            </button>
                        {/each}
                    </div>
                </div>

                <!-- Textarea -->
                <div class="relative">
                    <textarea 
                        bind:value={newContent}
                        placeholder="Hãy chia sẻ cảm nhận của bạn về bài viết này..." 
                        class="w-full h-32 p-4 text-sm bg-white border-none focus:ring-1 focus:ring-[#C18F7E] outline-none rounded-none"
                    ></textarea>
                </div>

                <!-- Media -->
                <div class="flex flex-wrap gap-2">
                    <input type="file" multiple accept="image/*,video/*" bind:this={fileInput} onchange={handleFileSelect} class="hidden" />
                    {#each attachedPhotos as photo}
                        <div class="w-16 h-16 border border-gray-200 overflow-hidden bg-white">
                            <img src={photo} alt="" class="w-full h-full object-cover" />
                        </div>
                    {/each}
                    {#if attachedPhotos.length < 5}
                        <button onclick={() => fileInput?.click()} disabled={isUploadingMedia} class="w-16 h-16 border-2 border-dashed border-gray-200 flex flex-col items-center justify-center text-gray-300">
                            {#if isUploadingMedia}<Loader2 class="w-4 h-4 animate-spin"/>{:else}<Camera class="w-5 h-5"/>{/if}
                        </button>
                    {/if}
                </div>

                <!-- Footer -->
                <div class="flex items-center justify-end gap-6 pt-4 border-t border-gray-200">
                    <button onclick={() => showWriteForm = false} class="text-[10px] font-black text-gray-400 uppercase">Hủy</button>
                    <button 
                        onclick={submitReview}
                        disabled={isSubmitting || newContent.length < 5} 
                        class="px-8 py-3 bg-[#0f172a] text-white text-[10px] font-black uppercase flex items-center gap-2 active:scale-95 transition-all disabled:opacity-30">
                        {isSubmitting ? 'ĐANG GỬI' : 'XÁC NHẬN'} <Send size={12} />
                    </button>
                </div>
            </div>
        {/if}
    </div>
  {/if}

  {#if isLoading}
    <div class="py-10 flex flex-col items-center justify-center gap-3">
      <Loader2 size={24} class="animate-spin text-[#C18F7E]" />
    </div>
  {:else if reviews.length === 0 && !showWriteForm}
    <div class="flex flex-col items-center py-10 text-center opacity-30">
      <MessageCircleMore size={40} class="mb-4" />
      <p class="text-[10px] font-black uppercase tracking-widest">Đang chờ ý kiến từ độc giả...</p>
    </div>
  {:else if reviews.length > 0}
    {@const review = reviews[0]}
    <div class="bg-gray-50/50 p-5 border border-gray-100 rounded-none" in:fade>
      <div class="flex items-center gap-3 mb-4">
        <div class="w-10 h-10 bg-[#C18F7E]/10 rounded-full flex items-center justify-center text-[#C18F7E] font-black text-sm">
          {(review.customer_name || 'U').charAt(0).toUpperCase()}
        </div>
        <div class="flex-1">
          <div class="flex items-center gap-1">
            <span class="text-xs font-black text-[#0f172a] uppercase">{review.customer_name || 'Khách hàng'}</span>
            <CheckCircle2 size={12} fill="currentColor" class="text-green-500" />
          </div>
          <div class="flex gap-0.5">
            {#each Array(5) as _, i}
              <Star size={10} class="{i < review.rating ? 'text-[#C18F7E] fill-current' : 'text-gray-200'}" />
            {/each}
          </div>
        </div>
        <span class="text-[9px] font-black text-gray-300 uppercase shrink-0">BÀI VIẾT HÀNG ĐẦU</span>
      </div>

      <div class="text-sm text-gray-700 leading-relaxed italic line-clamp-3 mb-4 font-medium">
        "{review.content}"
      </div>

      {#if review.attachments && review.attachments.length > 0}
        <div class="flex gap-2">
          {#each review.attachments.slice(0, 3) as media}
            <div class="w-20 h-20 bg-white border border-gray-100 overflow-hidden relative">
              <img src={media.url} alt="Review" class="w-full h-full object-cover" />
              {#if isVideo(media.url)}
                <div class="absolute inset-0 flex items-center justify-center bg-black/10"><Play size={16} fill="white" /></div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}

      <div class="mt-6 flex items-center justify-between">
        <div class="text-[9px] font-black uppercase tracking-widest text-gray-300">
           {reviewCount * 14 + 120}+ Độc giả tin dùng
        </div>
        <div class="px-6 py-3 bg-[#C18F7E] text-white text-[9px] font-black uppercase tracking-widest active:scale-95 transition-all">
          TẤT CẢ CẢM NHẬN
        </div>
      </div>
    </div>
  {/if}
</div>
