<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import Star from "@lucide/svelte/icons/star";
  import ThumbsUp from "@lucide/svelte/icons/thumbs-up";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";
  import Play from "@lucide/svelte/icons/play";
  import Camera from "@lucide/svelte/icons/camera";
  import Send from "@lucide/svelte/icons/send";
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import X from "@lucide/svelte/icons/x";
  import SimpleTiptap from '../ui/SimpleTiptap.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { fade, fly, scale } from 'svelte/transition';
  import type { Review, ReviewStats } from '$lib/types';

  const ui = getClientUi();

  interface Props {
    articleId: string;
  }
  let { articleId }: Props = $props();

  let reviews = $state<Review[]>([]);
  let stats = $state<ReviewStats | null>(null);
  let isLoading = $state(true);
  let isSubmitting = $state(false);
  let showWriteForm = $state(false);
  let submitSuccess = $state(false);
  let activeTab = $state<'all' | number | 'content' | 'media'>('all');
  let isUploadingMedia = $state(false);
  let fileInput = $state<HTMLInputElement | null>(null);
  let viewingMedia = $state<{url: string, type: string} | null>(null);

  // Review Actions State
  let likedReviews = $state<Set<string>>(new Set());
  let activeDropdownId = $state<string | null>(null);

  // Form State
  let newRating = $state(5);
  let newContent = $state('');
  let newAttributes = $state<Record<string, string>>({
    'Độ hữu ích': '',
    'Dễ hiểu': '',
    'Tính ứng dụng': ''
  });
  let attachedPhotos = $state<string[]>([]);
  
  async function fetchStats() {
    try {
      stats = await apiClient.get<ReviewStats>(`/client/reviews/stats`, {
        params: {
          entity_type: 'NEWS',
          entity_id: articleId
        }
      });
    } catch (e) {
      console.error("Lỗi fetch stats:", e);
    }
  }

  async function fetchReviews() {
    isLoading = true;
    try {
      const params: Record<string, string> = {
        entity_type: 'NEWS',
        entity_id: articleId,
        status: 'APPROVED'
      };
      if (typeof activeTab === 'number') params.rating = activeTab.toString();
      else if (activeTab === 'media') params.has_media = 'true';

      const data = await apiClient.get<{ items: Review[] }>(`/client/reviews`, { params });
      reviews = data.items.map((r: Review) => ({
        ...r,
        initial: (r.customer_name || 'K').charAt(0).toUpperCase(),
        name: r.customer_name
      }));
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

  $effect(() => {
    if (activeTab) {
       fetchReviews();
    }
    
    if (!authStore.isAuthenticated && showWriteForm) {
      showWriteForm = false;
    }
  });

  const ratingTabs = [
    { label: 'Tất Cả', key: 'all' },
    { label: '5 Sao', key: 5 },
    { label: '4 Sao', key: 4 },
    { label: '3 Sao', key: 3 },
    { label: '2 Sao', key: 2 },
    { label: '1 Sao', key: 1 },
    { label: 'Có Hình Ảnh / Video', key: 'media' }
  ];

  function getTabCount(key: string | number) {
    if (!stats) return '';
    if (typeof key === 'number') return `(${stats.rating_breakdown[key] || 0})`;
    if (key === 'media') return `(${stats.has_media_count || 0})`;
    return '';
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
           
           const json = await apiClient.upload<{ data: { file_path: string } }>('/client/reviews/upload', formData);
           if (json.data && json.data.file_path) {
               attachedPhotos = [...attachedPhotos, json.data.file_path];
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
      await apiClient.post('/client/reviews', {
        entity_type: 'NEWS',
        entity_id: articleId,
        customer_name: authStore.user?.name || 'Khách osmo',
        rating: newRating,
        content: newContent,
        attributes: Object.fromEntries(Object.entries(newAttributes).filter(([k, v]) => v !== '')),
        attachments: attachedPhotos.map(url => ({ 
           url, 
           type: (url.match(/\.(mp4|webm|mov)$/i) || url.includes('video')) ? 'video' : 'image' 
        }))
      });
      submitSuccess = true;
        setTimeout(() => {
          showWriteForm = false;
          submitSuccess = false;
          newContent = '';
          attachedPhotos = [];
          fetchStats();
          fetchReviews();
        }, 2000);
    } catch (e) {
      console.error("Lỗi submit review:", e);
    } finally {
      isSubmitting = false;
    }
  }

  async function handleLikeReview(reviewId: string) {
    if (likedReviews.has(reviewId)) return;
    
    const idx = reviews.findIndex(r => r.id === reviewId);
    if (idx !== -1) {
      reviews[idx].likes_count = (reviews[idx].likes_count || 0) + 1;
      likedReviews.add(reviewId);
    }
    
    try {
      const res = await apiClient.post<{new_count: number}>(`/client/reviews/${reviewId}/like`);
      if (idx !== -1 && res.new_count !== undefined) {
        reviews[idx].likes_count = res.new_count;
      }
    } catch (e) {
      console.error("Lỗi like review:", e);
      if (idx !== -1) {
         reviews[idx].likes_count -= 1;
         likedReviews.delete(reviewId);
      }
    }
  }

  async function handleReportReview(reviewId: string) {
    activeDropdownId = null;
    ui.openReportReview(reviewId);
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('vi-VN');
  };
</script>

<div class="bg-gray-50/50 p-10 mt-10 rounded-none border-t border-gray-100">
  <div class="flex flex-col md:flex-row items-center justify-between gap-6 mb-10 pb-6 border-b border-gray-100">
    <div>
      <h2 class="text-2xl font-black text-[#0f172a] tracking-tighter">Phản hồi từ độc giả</h2>
      <p class="text-gray-400 text-[10px] font-black tracking-[0.3em]">Xác thực trải nghiệm người dùng</p>
    </div>
    <button 
      onclick={handleWriteReview}
      class="px-10 py-5 bg-[#C18F7E] text-white font-black text-[11px] tracking-[0.3em] hover:bg-[#0f172a] transition-all">
      Viết cảm nhận ngay
    </button>
  </div>

  {#if showWriteForm}
    <div class="mb-12 p-10 bg-white border border-gray-100 shadow-xl" transition:fly={{ y: -20, duration: 600 }}>
      {#if submitSuccess}
        <div class="flex flex-col items-center justify-center py-10 text-center" in:scale>
          <CheckCircle2 class="w-16 h-16 text-[#C18F7E] mb-4" />
          <h3 class="text-lg font-black text-[#0f172a]">Gửi đánh giá thành công!</h3>
          <p class="text-sm text-gray-500 mt-1">Cảm ơn bạn đã đóng góp ý kiến cho bài viết.</p>
        </div>
      {:else}
        <div class="space-y-6">
          <div class="flex items-center gap-4">
            <span class="text-[11px] font-black text-gray-400 tracking-widest">Đánh giá sao:</span>
            <div class="flex gap-1">
              {#each Array(5) as _, i}
                <button onclick={() => newRating = i + 1} class="transition-transform hover:scale-125">
                  <Star class="w-8 h-8 {i < newRating ? 'text-[#C18F7E] fill-current' : 'text-gray-200'}" />
                </button>
              {/each}
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            {#each Object.keys(newAttributes) as attr}
              <div class="space-y-3">
                <span class="text-[9px] font-black text-gray-400 tracking-widest">{attr}</span>
                <div class="flex flex-wrap gap-2">
                  {#each (attr === 'Độ hữu ích' ? ['Rất cao', 'Trung bình', 'Thấp'] : attr === 'Dễ hiểu' ? ['Dễ hiểu', 'Hơi khó', 'Rất khó'] : ['Áp dụng ngay', 'Cần thêm HD', 'Khó áp dụng']) as opt}
                    <button 
                      onclick={() => newAttributes[attr] = opt}
                      class="px-4 py-2 text-[9px] font-black border transition-all tracking-widest {newAttributes[attr] === opt ? 'bg-[#0f172a] text-white border-[#0f172a]' : 'bg-white text-gray-400 border-gray-100 hover:border-[#C18F7E]'}">
                      {opt}
                    </button>
                    {/each}
                </div>
              </div>
            {/each}
          </div>

          <div class="relative w-full">
            <SimpleTiptap 
              bind:content={newContent}
              placeholder="Chia sẻ cảm nhận của bạn về kiến thức trong bài viết này nhé..."
              limit={5000}
            />
          </div>

          <div class="flex flex-wrap gap-3">
            <input type="file" multiple accept="image/*,video/*" bind:this={fileInput} onchange={handleFileSelect} class="hidden" />
            {#each attachedPhotos as photo}
              <div class="w-24 h-24 border border-gray-100 relative group bg-gray-50 overflow-hidden">
                <img src={photo} alt="" class="w-full h-full object-cover" />
              </div>
            {/each}
            {#if attachedPhotos.length < 5}
              <button onclick={() => fileInput?.click()} disabled={isUploadingMedia} class="w-24 h-24 border-2 border-dashed border-gray-100 flex flex-col items-center justify-center gap-2 text-gray-300 hover:border-[#C18F7E] hover:text-[#C18F7E] transition-all">
                <Camera class="w-6 h-6" />
                <span class="text-[8px] font-black">THÊM ẢNH/VIDEO</span>
              </button>
            {/if}
          </div>

          <div class="flex justify-end gap-6 pt-10 border-t border-gray-100">
            <button onclick={() => showWriteForm = false} class="text-[10px] font-black text-gray-400 hover:text-black tracking-[0.3em]">Hủy bỏ</button>
            <button 
              onclick={submitReview}
              disabled={isSubmitting || newContent.length < 5}
              class="px-20 py-5 bg-[#C18F7E] text-white font-black text-[11px] tracking-[0.3em] flex items-center gap-3">
              {isSubmitting ? 'ĐANG GỬI...' : 'Xác nhận gửi'}
              <Send class="w-4 h-4" />
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  {#if stats}
   <div class="bg-white border border-gray-100 p-8 flex items-center gap-14 mb-10">
    <div class="flex flex-col items-center">
      <div class="flex items-baseline gap-1 text-[#0f172a]">
        <span class="text-5xl font-black">{stats.average_rating}</span>
        <span class="text-xs font-black text-gray-300">/ 5</span>
      </div>
      <div class="flex gap-1 mt-2">
        {#each Array(5) as _, i}
          <Star class="w-5 h-5 {i < Math.round(stats.average_rating) ? 'text-[#C18F7E] fill-current' : 'text-gray-100'} " />
        {/each}
      </div>
    </div>

    <div class="flex-1 flex flex-wrap gap-2">
      {#each ratingTabs as tab}
        <button 
          onclick={() => activeTab = tab.key as 'all' | number | 'media'}
          class="px-6 py-3 text-[10px] font-black border transition-all tracking-widest {activeTab === tab.key ? 'bg-[#0f172a] text-white border-[#0f172a]' : 'bg-white text-gray-400 border-gray-100 hover:border-[#C18F7E]'}">
          {tab.label} {getTabCount(tab.key)}
        </button>
      {/each}
    </div>
  </div>
  {/if}

  <div class="space-y-8">
    {#if isLoading}
      <div class="py-20 flex flex-col items-center justify-center gap-4">
        <Loader2 class="w-10 h-10 animate-spin text-[#C18F7E]" />
        <span class="text-[10px] font-black tracking-[0.4em] text-gray-300">Syncing_Reader_Voices...</span>
      </div>
    {:else if reviews.length === 0}
      <div class="py-20 text-center text-gray-300 space-y-4">
        <div class="text-6xl font-black opacity-10">404</div>
        <p class="text-xs tracking-widest font-black">Chưa có phản hồi nào cho bài viết này.</p>
      </div>
    {:else}
      {#each reviews as review}
        <div class="flex gap-6 pb-10 border-b border-gray-100 last:border-0" in:fade>
          <div class="w-12 h-12 bg-gray-100 flex items-center justify-center text-[#C18F7E] font-black text-xl shrink-0">
            {review.initial}
          </div>

          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <span class="text-sm font-black text-[#0f172a]">{review.name}</span>
              <div class="flex gap-0.5">
                {#each Array(5) as _, i}
                  <Star class="w-3 h-3 {i < review.rating ? 'text-[#C18F7E] fill-current' : 'text-gray-200'}" />
                {/each}
              </div>
              <span class="text-[10px] font-black text-gray-300 ml-auto">{formatDate(review.created_at)}</span>
            </div>

            {#if review.attributes}
              <div class="flex flex-wrap gap-4 mb-4">
                {#each Object.entries(review.attributes) as [key, val]}
                  <div class="text-[11px] font-bold">
                    <span class="text-gray-400 tracking-widest">{key}:</span>
                    <span class="text-[#C18F7E]">{val}</span>
                  </div>
                {/each}
              </div>
            {/if}

            <div class="text-[14px] text-gray-700 leading-relaxed mb-6">
              {@html review.content}
            </div>

            {#if review.attachments && review.attachments.length > 0}
              <div class="flex flex-wrap gap-3">
                {#each review.attachments as media}
                  <div class="w-24 h-24 bg-gray-50 border border-gray-100 overflow-hidden relative cursor-zoom-in" onclick={() => viewingMedia = {url: media.url, type: media.type}}>
                    <img src={media.url} alt="" class="w-full h-full object-cover" />
                    {#if media.type === 'video'}
                      <div class="absolute inset-0 flex items-center justify-center bg-black/20"><Play class="w-6 h-6 text-white fill-current" /></div>
                    {/if}
                  </div>
                {/each}
              </div>
            {/if}

            <!-- Actions -->
            <div class="flex items-center justify-between mt-4 border-t border-gray-100 pt-4">
              <button 
                onclick={() => handleLikeReview(review.id)}
                class="flex items-center gap-1.5 group {likedReviews.has(review.id) ? 'pointer-events-none' : ''}">
                <ThumbsUp class="w-4 h-4 {review.likes_count || likedReviews.has(review.id) ? 'text-[#C18F7E] fill-current' : 'text-gray-300'} transition-colors {likedReviews.has(review.id) ? '' : 'group-hover:text-[#C18F7E]'}" />
                <span class="text-[13px] {likedReviews.has(review.id) ? 'text-[#C18F7E]' : 'text-gray-400'} font-medium group-hover:text-[#C18F7E]">{review.likes_count || ''}</span>
              </button>
              <div class="relative">
                <button 
                  onclick={() => activeDropdownId = activeDropdownId === review.id ? null : review.id}
                  class="text-gray-300 hover:text-gray-600 transition-colors">
                  <MoreHorizontal class="w-5 h-5" />
                </button>
                {#if activeDropdownId === review.id}
                  <!-- svelte-ignore a11y_click_events_have_key_events -->
                  <!-- svelte-ignore a11y_no_static_element_interactions -->
                  <div class="fixed inset-0 z-40" onclick={() => activeDropdownId = null}></div>
                  <div class="absolute right-0 top-full mt-1 w-40 bg-white border border-gray-100 shadow-xl z-50 py-1" in:fade={{ duration: 150 }}>
                    <button 
                      onclick={() => handleReportReview(review.id)}
                      class="w-full px-4 py-2 text-left text-[12px] font-medium text-red-600 hover:bg-gray-50 flex items-center gap-2">
                      <span class="text-base">🚩</span> Báo cáo vi phạm
                    </button>
                  </div>
                {/if}
              </div>
            </div>

          </div>
        </div>
      {/each}
    {/if}
  </div>
</div>

{#if viewingMedia}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-[9999] bg-black/95 flex items-center justify-center p-10" transition:fade onclick={() => viewingMedia = null}>
    <button class="absolute top-10 right-10 text-white hover:rotate-90 transition-all"><X class="w-10 h-10" /></button>
    <div class="max-w-6xl max-h-full" onclick={e => e.stopPropagation()}>
      {#if viewingMedia.type === 'video'}
        <video src={viewingMedia.url} class="max-w-full max-h-[85vh]" controls autoplay></video>
      {:else}
        <img src={viewingMedia.url} class="max-w-full max-h-[85vh] object-contain" alt="" />
      {/if}
    </div>
  </div>
{/if}

<style>
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 4px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: #C18F7E; }
</style>
