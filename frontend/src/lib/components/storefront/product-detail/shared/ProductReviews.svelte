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
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import MinusCircle from "@lucide/svelte/icons/minus-circle";
  import SimpleTiptap from '../../ui/SimpleTiptap.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import type { Product, Review, ReviewStats } from '$lib/types';
  
  const ui = getClientUi();
  import { fade, fly, scale } from 'svelte/transition';

  interface Props {
    product: Product;
    entityType?: 'PRODUCT' | 'CATEGORY' | 'SHOP';
  }
  let { product, entityType = 'PRODUCT' }: Props = $props();


  let reviews = $state<Review[]>([]);
  let stats = $state<ReviewStats | null>(null);
  let isLoading = $state(true);
  let isSubmitting = $state(false);
  let showLoginModal = $state(false);
  let showWriteForm = $state(false);
  let submitSuccess = $state(false);
  let activeTab = $state<'all' | number | 'content' | 'media'>('all');
  let isUploadingMedia = $state(false);
  let fileInput = $state<HTMLInputElement | null>(null);
  let viewingMedia = $state<{url: string, type: string} | null>(null);

  // Review Actions State
  let likedReviews = $state<Set<string>>(new Set());
  let activeDropdownId = $state<string | null>(null);

  // AI Sentiment State
  const meta = $derived(product?.metadata || {});
  const aiSummary = $derived(meta.customer_sentiment_summary);
  const positiveNotes = $derived(meta.positive_notes || []);
  const negativeNotes = $derived(meta.negative_notes || []);

  const hasAiSentiment = $derived(aiSummary || positiveNotes.length > 0 || negativeNotes.length > 0);

  // Form State
  let newRating = $state(5);
  let newContent = $state('');
  let newAttributes = $state<Record<string, string>>({
    'Thấm thấu': '',
    'Da săn chắc': '',
    'Mùi thơm': ''
  });
  let attachedPhotos = $state<string[]>([]);
  
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
      const params: Record<string, string> = {
        entity_type: entityType,
        entity_id: product.id,
        status: 'APPROVED'
      };
      if (typeof activeTab === 'number') params.rating = activeTab.toString();
      else if (activeTab === 'media') params.has_media = 'true';
      
      const data = await apiClient.get<{ items: Review[] }>(`/client/reviews`, { params });
      reviews = data.items.map((r: Review) => ({
        ...r,
        initial: r.customer_name.charAt(0).toUpperCase()
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

  // Elite Performance Fix P1.3: Chỉ re-fetch khi tab THỰC SỰ thay đổi, không chạy lúc mount
  // Tách biệt với auth logic để tránh $effect dependency pollution
  let _prevTab = $state<typeof activeTab>('all');
  $effect(() => {
    const currentTab = activeTab;
    if (currentTab !== _prevTab) {
      _prevTab = currentTab;
      fetchReviews();
    }
  });

  // Auth guard: Đóng form khi đăng xuất (tách riêng để không trigger fetchReviews)
  $effect(() => {
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
    { label: 'Có Bình Luận', key: 'content' },
    { label: 'Có Hình Ảnh / Video', key: 'media' }
  ];

  function getTabCount(key: string | number) {
    if (!stats) return '';
    if (typeof key === 'number') return `(${stats.rating_breakdown[key] || 0})`;
    if (key === 'content') return `(${stats.has_content_count || 0})`;
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
    if (!authStore.isAuthenticated) {
       ui.showToast('Vui lòng đăng nhập để tải ảnh', 'error');
       return;
    }
    const target = e.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;
    
    if (attachedPhotos.length + target.files.length > 5) {
       ui.showToast('Chỉ được tải lên tối đa 5 file đính kèm.', 'error');
       return;
    }

    isUploadingMedia = true;
    try {
       for (let i = 0; i < target.files.length; i++) {
           const file = target.files[i];
           if (file.type.startsWith('image/') && file.size > 5 * 1024 * 1024) {
               ui.showToast(`Ảnh ${file.name} vượt quá 5MB.`, 'error');
               continue;
           }
           if (file.type.startsWith('video/') && file.size > 20 * 1024 * 1024) {
               ui.showToast(`Video ${file.name} vượt quá 20MB.`, 'error');
               continue;
           }

           const formData = new FormData();
           // Litestar UploadFile uses "data" explicitly based on Body(...) binding
           formData.append('data', file);
           
           const json = await apiClient.upload<{ data: { file_path: string } }>('/client/reviews/upload', formData);
           if (json.data && json.data.file_path) {
               attachedPhotos = [...attachedPhotos, json.data.file_path];
           }
       }
    } catch (err) {
       console.error("Upload error:", err);
       ui.showToast('Lỗi gián đoạn khi kết nối máy chủ.', 'error');
    } finally {
       isUploadingMedia = false;
       if (fileInput) fileInput.value = '';
    }
  };

  async function submitReview() {
    if (!newContent || newContent.length < 5) return;
    isSubmitting = true;
    try {
      await apiClient.post('/client/reviews', {
        entity_type: entityType,
        entity_id: product.id,
        customer_name: authStore.user?.name || 'Khách',
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
    const date = new Date(dateStr);
    return date.toISOString().slice(0, 16).replace('T', ' ');
  };
</script>

<div class="bg-white p-6 md:p-10 mt-0 rounded-none relative overflow-hidden mb-0">
  <div class="flex flex-col md:flex-row items-center justify-between gap-6 mb-10 pb-6 border-b border-gray-50">
    <div>
      <h2 class="text-2xl font-black text-[#1a1a1a] tracking-tight leading-none mb-2">Đánh giá {product.name}</h2>
      <p class="text-gray-400 text-xs font-medium tracking-[0.2em]">Trải nghiệm thực tế từ người dùng</p>
    </div>
    <button 
      id="btn-write-review"
      onclick={handleWriteReview}
      class="px-10 py-5 bg-gradient-to-r from-luxury-copper to-luxury-peach text-white font-black rounded-none text-[11px] tracking-[0.3em] hover:opacity-90 hover:shadow-lg hover:shadow-luxury-copper/20 hover:-translate-y-1 transition-all border border-white/20">
      Viết đánh giá ngay
    </button>
  </div>

  <!-- Auth Modal removed (now global) -->

  <!-- Write Review Form (Clean Minimalist) -->
  {#if showWriteForm}
    <div class="mb-12 p-10 bg-white border border-gray-100 rounded-none" transition:fly={{ y: -20, duration: 600 }}>
      {#if submitSuccess}
        <div class="flex flex-col items-center justify-center py-10 text-center" in:scale>
          <CheckCircle2 class="w-16 h-16 text-green-500 mb-4" />
          <h3 class="text-lg font-black text-gray-900">Gửi đánh giá thành công!</h3>
          <p class="text-sm text-gray-500 mt-1">Cảm ơn Sếp đã đóng góp ý kiến cho {entityType === 'CATEGORY' ? 'danh mục' : 'sản phẩm'}.</p>
        </div>
      {:else}
        <div class="space-y-6">
          <div class="flex items-center gap-4">
            <span class="text-sm font-bold text-gray-700">Mức độ hài lòng:</span>
            <div class="flex gap-1">
              {#each Array(5) as _, i}
                <button onclick={() => newRating = i + 1} class="transition-transform hover:scale-125">
                  <Star class="w-8 h-8 {i < newRating ? 'text-[#ee4d2d] fill-current' : 'text-gray-200'}" />
                </button>
              {/each}
            </div>
            <span class="text-xs font-bold text-[#ee4d2d] tracking-widest">{['Rất tệ', 'Tệ', 'Bình thường', 'Hài lòng', 'Tuyệt vời'][newRating - 1]}</span>
          </div>

          <!-- Quick Attributes -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            {#each Object.keys(newAttributes) as attr}
              <div class="space-y-2">
                <span class="text-[11px] font-black text-gray-400 tracking-widest">{attr}</span>
                <div class="flex flex-wrap gap-2">
                  {#each (attr === 'Thấm thấu' ? ['Tham nhanh', 'Hơi dính', 'Bết'] : attr === 'Mùi thơm' ? ['Thơm dịu', 'Nồng', 'Không mùi'] : ['Săn chắc', 'Mịn màng', 'Dưỡng ẩm']) as opt}
                    <button 
                      onclick={() => newAttributes[attr] = opt}
                      class="px-4 py-2 text-[10px] font-black border-2 transition-all tracking-widest {newAttributes[attr] === opt ? 'bg-black text-white border-black' : 'bg-white text-gray-400 border-gray-100 hover:border-black'}">
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
              placeholder="Chia sẻ cảm nhận của bạn về {entityType === 'CATEGORY' ? 'danh mục' : 'sản phẩm'} này nhé..."
              limit={5000}
            />
          </div>

          <!-- Photo Upload & Processing -->
          <div class="flex flex-wrap gap-3">
            <input 
                type="file" 
                multiple 
                accept="image/png, image/jpeg, image/webp, video/mp4, video/webm" 
                bind:this={fileInput} 
                onchange={handleFileSelect}
                class="hidden" 
            />

            {#each attachedPhotos as photo}
              <div class="w-24 h-24 rounded-none overflow-hidden border-2 border-black relative group bg-gray-50 flex items-center justify-center">
                {#if photo.endsWith('.mp4') || photo.endsWith('.webm') || photo.includes('video')}
                   <video src={photo} class="w-full h-full object-cover" muted loop playsinline></video>
                   <div class="absolute inset-0 bg-black/10 flex items-center justify-center">
                     <Play class="w-6 h-6 text-white fill-current opacity-80" />
                   </div>
                {:else}
                   <img src={photo} alt="Xem trước ảnh đánh giá sản phẩm {product.name}" class="w-full h-full object-cover" />
                {/if}
              </div>
            {/each}
            
            {#if attachedPhotos.length < 5}
              <button 
                onclick={() => fileInput?.click()}
                disabled={isUploadingMedia}
                class="w-24 h-24 rounded-none border-2 border-dashed border-gray-200 flex flex-col items-center justify-center gap-2 text-gray-300 hover:border-black hover:text-black transition-all disabled:opacity-50 disabled:pointer-events-none"
              >
                {#if isUploadingMedia}
                    <Loader2 class="w-6 h-6 animate-spin" />
                    <span class="text-[9px] font-black tracking-[0.2em]">Đang tải lên</span>
                {:else}
                    <Camera class="w-6 h-6" />
                    <span class="text-[9px] font-black tracking-[0.2em]">Thêm ảnh/video</span>
                {/if}
              </button>
            {/if}
          </div>

          <div class="flex justify-end gap-6 pt-10 border-t border-gray-50">
            <button onclick={() => showWriteForm = false} class="px-6 py-4 text-[11px] font-black text-gray-400 tracking-widest transition-colors">Hủy bỏ</button>
            <button 
              onclick={submitReview}
              disabled={isSubmitting || newContent.length < 5}
              class="px-20 py-5 bg-gradient-to-r from-luxury-copper to-luxury-peach text-white font-black rounded-none text-[11px] tracking-[0.3em] flex items-center gap-3 hover:opacity-90 shadow-lg shadow-luxury-copper/20 hover:-translate-y-1 transition-all disabled:opacity-20 disabled:pointer-events-none"
            >
              {#if isSubmitting}
                <Loader2 class="w-5 h-5 animate-spin" />
              {:else}
                Gửi đánh giá <Send class="w-4 h-4" />
              {/if}
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Summary Box (Premium Standard) -->
  {#if stats}
   <div class="bg-white border border-gray-100 p-10 flex items-center gap-14 mb-10 rounded-none">
    <div class="flex flex-col items-center">
      <div class="flex items-baseline gap-1 text-black">
        <span class="text-5xl font-black tracking-tighter">{stats.average_rating}</span>
        <span class="text-sm font-black tracking-widest text-gray-400">/ 5</span>
      </div>
      <div class="flex gap-1.5 mt-2">
        {#each Array(5) as _, i}
          <Star class="w-6 h-6 {i < Math.round(stats.average_rating) ? 'text-[#ee4d2d] fill-current' : 'text-gray-200'} " />
        {/each}
      </div>
    </div>

    <div class="flex-1 flex flex-wrap gap-3">
      {#each ratingTabs as tab}
        <button 
          onclick={() => activeTab = tab.key as typeof activeTab}
          class="px-6 py-3 text-[11px] font-black border-2 transition-all tracking-widest {activeTab === tab.key ? 'border-black bg-black text-white' : 'border-gray-100 bg-white text-gray-400 hover:border-black hover:text-black'}">
          {tab.label} {getTabCount(tab.key)}
        </button>
      {/each}
    </div>
  </div>
  {/if}

  <!-- AI Sentiment Box (Desktop) -->
  {#if hasAiSentiment}
    <div class="mb-10 bg-gradient-to-r from-[#FFF9F6] to-white border border-[#ee4d2d]/10 p-8 flex flex-col md:flex-row gap-8 relative overflow-hidden">
       <!-- Decorative background -->
       <div class="absolute -top-10 -right-10 w-40 h-40 bg-[#ee4d2d]/5 rounded-full blur-3xl pointer-events-none"></div>

       <div class="w-full md:w-1/3 shrink-0 relative z-10">
         <div class="flex items-center gap-2 mb-3">
           <Sparkles class="w-5 h-5 text-[#ee4d2d] fill-current" />
           <h3 class="text-[13px] font-black tracking-[0.2em] text-[#ee4d2d]">AI Tổng hợp đánh giá</h3>
         </div>
         {#if aiSummary}
           <p class="text-[14px] text-gray-700 leading-relaxed font-medium">{aiSummary}</p>
         {/if}
       </div>

       <div class="flex-1 flex flex-col sm:flex-row gap-6 relative z-10">
          {#if positiveNotes.length > 0}
            <div class="flex-1 bg-white/60 backdrop-blur-sm p-4 border border-green-500/10">
              <span class="text-[11px] font-black tracking-widest text-[#00bfa5] mb-3 block border-b border-green-500/10 pb-2">Khách hàng ưng ý</span>
              <ul class="space-y-2.5">
                {#each positiveNotes as note}
                  <li class="text-[13px] text-gray-600 flex items-start gap-2"><CheckCircle2 class="w-4 h-4 text-[#00bfa5] mt-0.5 shrink-0" /> <span class="leading-tight">{note}</span></li>
                {/each}
              </ul>
            </div>
          {/if}
          {#if negativeNotes.length > 0}
            <div class="flex-1 bg-white/60 backdrop-blur-sm p-4 border border-gray-200/50">
              <span class="text-[11px] font-black tracking-widest text-gray-400 mb-3 block border-b border-gray-100 pb-2">Điểm cần lưu ý</span>
              <ul class="space-y-2.5">
                {#each negativeNotes as note}
                  <li class="text-[13px] text-gray-500 flex items-start gap-2"><MinusCircle class="w-4 h-4 text-gray-300 mt-0.5 shrink-0" /> <span class="leading-tight">{note}</span></li>
                {/each}
              </ul>
            </div>
          {/if}
       </div>
    </div>
  {/if}

  <!-- Review List -->
  <div class="space-y-6">
    {#if isLoading}
      <div class="py-20 flex flex-col items-center justify-center gap-4">
        <div class="w-8 h-8 border-2 border-[#ee4d2d] border-t-transparent rounded-full animate-spin"></div>
        <span class="text-xs font-bold text-gray-400 tracking-widest">Đang tải đánh giá...</span>
      </div>
    {:else if reviews.length === 0}
      <div class="py-20 flex flex-col items-center justify-center text-gray-400">
        <svg class="w-16 h-16 opacity-20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
        <span class="text-sm">Chưa có đánh giá nào cho tiêu chí này.</span>
      </div>
    {:else}
      {#each reviews as review}
        <div class="flex gap-4 pb-6 border-b border-gray-50 last:border-0" in:fade>
          <!-- Avatar -->
          <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center overflow-hidden shrink-0 border border-gray-50">
            {#if review.avatar}
              <img src={review.avatar} alt={review.name} class="w-full h-full object-cover" />
            {:else}
              <span class="text-[14px] font-bold text-gray-400">{review.initial}</span>
            {/if}
          </div>

          <div class="flex-1 flex flex-col">
            <div class="flex items-center justify-between mb-0.5">
              <span class="text-[12px] font-medium text-gray-900">{review.name}</span>
            </div>
            
            <div class="flex gap-0.5 mb-1.5">
              {#each Array(5) as _, i}
                <Star class="w-2.5 h-2.5 {i < review.rating ? 'text-[#ee4d2d] fill-current' : 'text-gray-200'}" />
              {/each}
            </div>

            <span class="text-[12px] text-gray-400 mb-4">{formatDate(review.created_at)}</span>

            <!-- Attributes -->
            {#if review.attributes}
              <div class="space-y-1.5 mb-4">
                {#each Object.entries(review.attributes) as [key, val]}
                  <div class="flex items-baseline gap-2 text-[13px]">
                    <span class="text-gray-400 capitalize">{key}:</span>
                    <span class="text-gray-800 font-medium">{val}</span>
                  </div>
                {/each}
              </div>
            {/if}

            <div class="text-[13px] text-gray-800 leading-relaxed mb-4 prose-osmo">
              {@html review.content}
            </div>

            <!-- Attachments (Images/Videos) -->
            {#if review.attachments && review.attachments.length > 0}
              <div class="flex flex-wrap gap-2.5 mb-4">
                {#each review.attachments as media}
                  <!-- svelte-ignore a11y_click_events_have_key_events -->
                  <!-- svelte-ignore a11y_no_static_element_interactions -->
                  <div 
                    class="w-[72px] h-[72px] bg-gray-100 border border-gray-100 relative group cursor-zoom-in overflow-hidden"
                    onclick={() => viewingMedia = { url: media.url, type: media.type === 'video' || media.url.match(/\.(mp4|webm|mov)$/i) ? 'video' : 'image' }}
                  >
                    {#if media.type === 'video' || media.url.match(/\.(mp4|webm|mov)$/i)}
                      <video src={media.url} class="w-full h-full object-cover transition-transform group-hover:scale-110" muted playsinline></video>
                      <div class="absolute inset-0 bg-black/20 flex items-center justify-center pointer-events-none">
                        <Play class="w-4 h-4 text-white fill-current opacity-90" />
                      </div>
                    {:else}
                      <img src={media.url} alt="Hình ảnh đánh giá thực tế {product.name}" class="w-full h-full object-cover transition-transform group-hover:scale-110" />
                    {/if}
                  </div>
                {/each}
              </div>
            {/if}

            <!-- Actions -->
            <div class="flex items-center justify-between">
              <button 
                onclick={() => handleLikeReview(review.id)}
                class="flex items-center gap-1.5 group {likedReviews.has(review.id) ? 'pointer-events-none' : ''}">
                <ThumbsUp class="w-4 h-4 {review.likes_count || likedReviews.has(review.id) ? 'text-[#ee4d2d] fill-current' : 'text-gray-300'} transition-colors {likedReviews.has(review.id) ? '' : 'group-hover:text-[#ee4d2d]'}" />
                <span class="text-[13px] {likedReviews.has(review.id) ? 'text-[#ee4d2d]' : 'text-gray-400'} font-medium group-hover:text-[#ee4d2d]">{review.likes_count || ''}</span>
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

<!-- Elite Theater Mode (Lightbox) -->
{#if viewingMedia}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-[var(--z-modal-overlay)] bg-black/95 flex items-center justify-center" transition:fade onclick={() => viewingMedia = null}>
    <button onclick={() => viewingMedia = null} class="absolute top-6 right-6 p-2 text-white/50 hover:text-white transition-colors bg-white/5 rounded-full hover:bg-white/10">
      <X class="w-6 h-6" />
    </button>
    <div class="max-w-5xl max-h-[90vh] p-4 flex outline-none" in:scale={{ duration: 300, start: 0.9 }}>
      {#if viewingMedia.type === 'video'}
        <!-- svelte-ignore a11y_media_has_caption -->
        <video src={viewingMedia.url} class="max-w-full max-h-[85vh] object-contain rounded-none shadow-2xl ring-1 ring-white/10" controls autoplay onclick={(e) => e.stopPropagation()}></video>
      {:else}
        <img src={viewingMedia.url} class="max-w-full max-h-[85vh] object-contain rounded-none shadow-2xl ring-1 ring-white/10" alt="Full review media" onclick={(e) => e.stopPropagation()} />
      {/if}
    </div>
  </div>
{/if}

<style>
  /* Standard Mall Scrollbar (Silent) */
  :global(.custom-scrollbar::-webkit-scrollbar) {
    width: 6px;
  }
  :global(.custom-scrollbar::-webkit-scrollbar-track) {
    background: transparent;
  }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) {
    background: #e5e5e5;
    border-radius: 10px;
  }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) {
    background: #ccc;
  }
</style>
