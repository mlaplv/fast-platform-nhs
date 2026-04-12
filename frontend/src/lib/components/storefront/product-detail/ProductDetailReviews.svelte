<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { Star, ThumbsUp, MoreHorizontal, Play, Camera, Send, CheckCircle2, Loader2 } from 'lucide-svelte';
  
  const ui = getClientUi();
  import { fade, fly } from 'svelte/transition';

  interface Props {
    product: Product;
  }
  let { product }: Props = $props();

  let reviews = $state<Review[]>([]);
  let stats = $state<ReviewStats | null>(null);
  let isLoading = $state(true);
  let isSubmitting = $state(false);
  let showLoginModal = $state(false);
  let showWriteForm = $state(false);
  let submitSuccess = $state(false);
  let activeTab = $state<'all' | number | 'content' | 'media'>('all');

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
      const res = await fetch(`/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`);
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
      let url = `/api/v1/client/reviews?entity_type=PRODUCT&entity_id=${product.id}&status=APPROVED`;
      if (typeof activeTab === 'number') {
        url += `&rating=${activeTab}`;
      } else if (activeTab === 'media') {
        url += `&has_media=true`;
      }
      
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        reviews = data.items.map((r: any) => ({
          ...r,
          initial: r.customer_name.charAt(0).toUpperCase()
        }));
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

  $effect(() => {
    // Re-fetch reviews when tab changes
    if (activeTab) {
       fetchReviews();
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

  const handlePhotoUpload = () => {
    // Simulated upload
    const mockPhotos = [
      'https://pub-8a62f1c8491842ec9a5789fcfc01b979.r2.dev/review_1.png',
      'https://pub-8a62f1c8491842ec9a5789fcfc01b979.r2.dev/review_2.png',
      'https://pub-8a62f1c8491842ec9a5789fcfc01b979.r2.dev/review_3.png'
    ];
    if (attachedPhotos.length < 5) {
      attachedPhotos = [...attachedPhotos, mockPhotos[attachedPhotos.length % 3]];
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
          entity_type: 'PRODUCT',
          entity_id: product.id,
          customer_name: authStore.user?.name || 'Guest',
          rating: newRating,
          content: newContent,
          attributes: Object.fromEntries(Object.entries(newAttributes).filter(([k, v]) => v !== '')),
          attachments: attachedPhotos.map(url => ({ url, type: 'image' }))
        })
      });
      if (res.ok) {
        submitSuccess = true;
        setTimeout(() => {
          showWriteForm = false;
          submitSuccess = false;
          newContent = '';
          attachedPhotos = [];
        }, 2000);
      }
    } catch (e) {
      console.error("Lỗi submit review:", e);
    } finally {
      isSubmitting = false;
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toISOString().slice(0, 16).replace('T', ' ');
  };
</script>

<div class="bg-white p-10 mt-10 rounded-none relative overflow-hidden mb-24">
  <div class="flex flex-col md:flex-row items-center justify-between gap-6 mb-10 pb-6 border-b border-gray-50">
    <div>
      <h2 class="text-2xl font-black text-[#1a1a1a] tracking-tight leading-none mb-2">Đánh Giá Sản Phẩm</h2>
      <p class="text-gray-400 text-xs font-medium uppercase tracking-[0.2em]">Authentic Reviews from Customers</p>
    </div>
    <button 
      onclick={handleWriteReview}
      class="px-10 py-5 bg-gradient-to-r from-luxury-copper to-luxury-peach text-white font-black rounded-none text-[11px] tracking-[0.3em] hover:opacity-90 hover:shadow-lg hover:shadow-luxury-copper/20 hover:-translate-y-1 transition-all border border-white/20">
      VIẾT ĐÁNH GIÁ NGAY
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
          <p class="text-sm text-gray-500 mt-1">Cảm ơn Sếp đã đóng góp ý kiến cho sản phẩm.</p>
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
            <span class="text-xs font-bold text-[#ee4d2d] uppercase tracking-widest">{['Rất tệ', 'Tệ', 'Bình thường', 'Hài lòng', 'Tuyệt vời'][newRating - 1]}</span>
          </div>

          <!-- Quick Attributes -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            {#each Object.keys(newAttributes) as attr}
              <div class="space-y-2">
                <span class="text-[11px] font-black text-gray-400 uppercase tracking-widest">{attr}</span>
                <div class="flex flex-wrap gap-2">
                  {#each (attr === 'Thấm thấu' ? ['Tham nhanh', 'Hơi dính', 'Bết'] : attr === 'Mùi thơm' ? ['Thơm dịu', 'Nồng', 'Không mùi'] : ['Săn chắc', 'Mịn màng', 'Dưỡng ẩm']) as opt}
                    <button 
                      onclick={() => newAttributes[attr] = opt}
                      class="px-4 py-2 text-[10px] font-black border-2 transition-all uppercase tracking-widest {newAttributes[attr] === opt ? 'bg-black text-white border-black' : 'bg-white text-gray-400 border-gray-100 hover:border-black'}">
                      {opt}
                    </button>
                    {/each}
                </div>
              </div>
            {/each}
          </div>

          <div class="relative">
            <textarea 
              bind:value={newContent}
              placeholder="Chia sẻ cảm nhận của bạn về sản phẩm này nhé..."
              class="w-full h-40 bg-white border-2 border-gray-100 p-6 rounded-none text-sm font-medium focus:border-black outline-none transition-all resize-none"
            ></textarea>
            <div class="absolute bottom-4 right-6 text-[10px] text-gray-300 font-black">
              {newContent.length} / 5000
            </div>
          </div>

          <!-- Photo Upload Simulation -->
          <div class="flex flex-wrap gap-3">
            {#each attachedPhotos as photo}
              <div class="w-24 h-24 rounded-none overflow-hidden border-2 border-black relative group">
                <img src={photo} alt="Preview" class="w-full h-full object-cover" />
              </div>
            {/each}
            
            {#if attachedPhotos.length < 5}
              <button 
                onclick={handlePhotoUpload}
                class="w-24 h-24 rounded-none border-2 border-dashed border-gray-200 flex flex-col items-center justify-center gap-2 text-gray-300 hover:border-black hover:text-black transition-all"
              >
                <Camera class="w-6 h-6" />
                <span class="text-[9px] font-black uppercase tracking-[0.2em]">Add Photo</span>
              </button>
            {/if}
          </div>

          <div class="flex justify-end gap-6 pt-10 border-t border-gray-50">
            <button onclick={() => showWriteForm = false} class="px-8 py-5 text-[10px] font-black text-gray-400 hover:text-black tracking-[0.3em] uppercase transition-colors">HỦY BỎ</button>
            <button 
              onclick={submitReview}
              disabled={isSubmitting || newContent.length < 5}
              class="px-20 py-5 bg-gradient-to-r from-luxury-copper to-luxury-peach text-white font-black rounded-none text-[11px] tracking-[0.3em] flex items-center gap-3 hover:opacity-90 shadow-lg shadow-luxury-copper/20 hover:-translate-y-1 transition-all disabled:opacity-20 disabled:pointer-events-none"
            >
              {#if isSubmitting}
                <Loader2 class="w-5 h-5 animate-spin" />
              {:else}
                GỬI ĐÁNH GIÁ <Send class="w-4 h-4" />
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
        <span class="text-sm font-black uppercase tracking-widest text-gray-400">/ 5</span>
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
          onclick={() => activeTab = tab.key as any}
          class="px-6 py-3 text-[11px] font-black border-2 transition-all uppercase tracking-widest {activeTab === tab.key ? 'border-black bg-black text-white' : 'border-gray-100 bg-white text-gray-400 hover:border-black hover:text-black'}">
          {tab.label} {getTabCount(tab.key)}
        </button>
      {/each}
    </div>
  </div>
  {/if}

  <!-- Review List -->
  <div class="space-y-6">
    {#if isLoading}
      <div class="py-20 flex flex-col items-center justify-center gap-4">
        <div class="w-8 h-8 border-2 border-[#ee4d2d] border-t-transparent rounded-full animate-spin"></div>
        <span class="text-xs font-bold text-gray-400 uppercase tracking-widest">Đang tải đánh giá...</span>
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

            <!-- Content -->
            <p class="text-[13px] text-gray-800 leading-relaxed mb-4 whitespace-pre-line">
              {review.content}
            </p>

            <!-- Attachments (Images/Videos) -->
            {#if review.attachments && review.attachments.length > 0}
              <div class="flex flex-wrap gap-2.5 mb-4">
                {#each review.attachments as media}
                  <div class="w-[72px] h-[72px] bg-gray-100 border border-gray-100 relative group cursor-zoom-in overflow-hidden">
                    <img src={media.url} alt="Review media" class="w-full h-full object-cover transition-transform group-hover:scale-110" />
                    {#if media.type === 'video' || media.duration}
                      <div class="absolute inset-0 bg-black/20 flex items-center justify-center">
                        <Play class="w-4 h-4 text-white fill-current" />
                      </div>
                      {#if media.duration}
                        <div class="absolute bottom-1 right-1 bg-black/50 text-white text-[9px] px-1 rounded-sm flex items-center gap-0.5">
                          <Play class="w-2 h-2 fill-current" />
                          {media.duration}
                        </div>
                      {/if}
                    {/if}
                  </div>
                {/each}
              </div>
            {/if}

            <!-- Actions -->
            <div class="flex items-center justify-between">
              <button class="flex items-center gap-1.5 group">
                <ThumbsUp class="w-4 h-4 {review.likes_count ? 'text-[#ee4d2d] fill-current' : 'text-gray-300'} transition-colors group-hover:text-[#ee4d2d]" />
                <span class="text-[13px] text-gray-400 font-medium group-hover:text-[#ee4d2d]">{review.likes_count || ''}</span>
              </button>
              <button class="text-gray-300 hover:text-gray-600 transition-colors">
                <MoreHorizontal class="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      {/each}
    {/if}
  </div>
</div>

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
