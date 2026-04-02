<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, fly, scale, blur } from 'svelte/transition';
  import { cubicOut, elasticOut } from 'svelte/easing';
  import { Star, ShieldCheck, MessageSquarePlus, X, MapPin, Phone, User, Send, CheckCircle2 } from 'lucide-svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';

  let { product } = $props();
  const shopStore = getShopStore();
  const metadata = $derived(product?.metadata || {});
  
  interface ReviewApiResponse {
    id: string | number;
    customer_name: string;
    customer_phone?: string;
    customer_location?: string;
    rating: number;
    content: string;
    created_at: string;
  }
  let realReviews = $state<Review[]>([]);
  let isLoading = $state(true);

  const labels = $derived({
    headline: metadata.reviews_headline || 'KHÁCH HÀNG NÓI GÌ?',
    trust_score: metadata.reviews_trust_score || '4.9/5',
    count_text: product?.orderCountText || metadata.reviews_count_text || '2,140+ LƯỢT MUA',
    hud_feedback: metadata.reviews_hud_feedback || 'HỆ THỐNG // PHẢN HỒI THỰC TẾ',
    label_verified: metadata.reviews_label_verified || 'ĐÃ XÁC THỰC',
    label_store_verified: metadata.reviews_label_store_verified || 'Xác thực bởi Cửa hàng',
    cta_write: metadata.reviews_cta_write || 'Viết đánh giá',
    form_title: metadata.reviews_form_title || 'GỬI ĐÁNH GIÁ MỚI',
    success_title: metadata.reviews_form_success_title || 'THÀNH CÔNG!',
    success_msg: metadata.reviews_form_success_msg || 'Đánh giá của bạn đã được ghi nhận và đang chờ duyệt.'
  });

  let showFormModal = $state(false);
  let isSubmitting = $state(false);
  let showSuccess = $state(false);
  
  // Form State
  let name = $state('');
  let phone = $state('');
  let content = $state('');
  let locationSelected = $state('');
  let ratingSelected = $state(5);
  let isLocationOpen = $state(false);
  let websiteUrl = $state(''); // Honeypot

  // Toast System
  let toastMessage = $state('');
  let showToast = $state(false);

  const locations = [
    "Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", 
    "Bình Dương", "Đồng Nai", "Khánh Hòa", "Lâm Đồng", "Quảng Ninh"
  ];

  function triggerToast(msg: string) {
    toastMessage = msg;
    showToast = true;
    setTimeout(() => { showToast = false; }, 3000);
  }

  async function fetchReviews() {
    if (!product?.id) return;
    isLoading = true;
    try {
      const res = await fetch(`/api/v1/client/reviews?entity_type=PRODUCT&entity_id=${product.id}&status=APPROVED`);
      if (res.ok) {
        const data = await res.json();
        realReviews = (data.items as ReviewApiResponse[] || []).map((r: ReviewApiResponse) => ({
          id: r.id,
          name: r.customer_name,
          phone: r.customer_phone ? r.customer_phone.slice(0, 3) + '****' + r.customer_phone.slice(-3) : 'Ẩn danh',
          location: r.customer_location || 'Việt Nam',
          rating: r.rating,
          content: r.content,
          initial: r.customer_name ? r.customer_name.charAt(0).toUpperCase() : '?'
        }));
      }
    } catch (e) {
      console.error("Reviews Error:", e);
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    fetchReviews();
  });

  async function handleSubmit(e: Event) {
    e.preventDefault();
    if (isSubmitting) return;

    if (!name || name.length < 2 || phone.length < 10 || content.length < 10 || !locationSelected) {
      triggerToast("Hệ thống: Vui lòng nhập đầy đủ thông tin.");
      return;
    }

    if (websiteUrl) return; // Silent reject bot

    isSubmitting = true;
    try {
      const res = await fetch('/api/v1/client/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_type: 'PRODUCT',
          entity_id: product?.id || '',
          customer_name: name,
          customer_phone: phone,
          customer_location: locationSelected,
          rating: ratingSelected,
          content: content
        })
      });

      if (res.ok) {
        showSuccess = true;
        setTimeout(() => {
          showFormModal = false;
          showSuccess = false;
          name = ''; phone = ''; content = ''; locationSelected = '';
        }, 4000);
      } else {
        triggerToast("Lỗi hệ thống. Thử lại sau.");
      }
    } catch (e) {
      triggerToast("Mất kết nối máy chủ.");
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="reviews-mobile-viewport h-full flex flex-col px-6 pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] bg-[#030303] relative overflow-hidden" id="reviews">
  <!-- HUD Header -->
  <div class="mt-8 mb-8">
    <div class="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full mb-6 backdrop-blur-md">
      <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
      <span class="text-[9px] uppercase tracking-[0.2em] text-emerald-400 font-black italic">{labels.hud_feedback}</span>
    </div>
    
    <h2 class="text-[28px] xs:text-3xl sm:text-4xl font-black text-white leading-[1.1] break-words uppercase tracking-tighter italic mb-6">
      {@html labels.headline}
    </h2>

    <div class="flex items-center gap-4 bg-white/[0.03] w-full px-5 py-4 rounded-3xl border border-white/10 backdrop-blur-xl">
      <div class="flex items-center gap-1">
        {#each Array(5) as _, i}
          <Star class="w-3.5 h-3.5 {i < 5 ? 'text-amber-400 fill-amber-400' : 'text-white/10'} drop-shadow-[0_0_8px_rgba(251,191,36,0.4)]" />
        {/each}
      </div>
      <div class="h-4 w-px bg-white/10"></div>
      <div class="flex flex-col">
        <div class="flex items-center gap-2">
          <span class="text-xs font-black text-white italic">{labels.trust_score}</span>
          <span class="text-[9px] text-emerald-400 font-black uppercase tracking-widest">{labels.count_text}</span>
        </div>
      </div>
    </div>
  </div>

  <div class="flex overflow-x-auto snap-x snap-mandatory gap-4 -mx-6 px-6 scrollbar-hide pb-10">
    {#if isLoading && realReviews.length === 0}
      <div class="py-20 text-center">
        <div class="w-10 h-10 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-[9px] font-black text-white/20 uppercase tracking-[0.4em]">Syncing_Voices...</p>
      </div>
    {:else if realReviews.length === 0}
      <div class="py-20 text-center opacity-20">
        <p class="text-[10px] font-black uppercase tracking-widest">No Feedback Detected</p>
      </div>
    {:else}
      {#each realReviews.slice(0, 8) as review, i}
        <div class="review-card-mobile flex-none snap-center p-6 bg-white/[0.03] border border-white/10 rounded-[2.5rem] backdrop-blur-3xl relative overflow-hidden" in:fly={{ y: 20, delay: i * 100 }}>
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-emerald-400 font-black text-xl italic shadow-inner">
                {review.initial}
              </div>
              <div>
                <h4 class="text-white font-black text-sm tracking-tight uppercase italic">{review.name}</h4>
                <div class="flex items-center gap-2">
                  <span class="text-[8px] text-white/30 font-black uppercase tracking-[0.2em]">{review.location}</span>
                  <div class="w-1 h-1 rounded-full bg-emerald-500/40"></div>
                  <span class="text-[8px] text-emerald-400 font-black uppercase tracking-widest">{labels.label_verified}</span>
                </div>
              </div>
            </div>
            <div class="p-2 bg-white/5 rounded-xl border border-white/5">
               <ShieldCheck class="w-4 h-4 text-emerald-500/40" />
            </div>
          </div>
          
          <div class="rating-row flex gap-1 mb-4">
            {#each Array(5) as _, s}
              <Star 
                class="w-3 h-3 {s < review.rating ? 'text-amber-400 fill-amber-400' : 'text-white/5'}" 
                style={s < review.rating ? 'filter: drop-shadow(0 0 6px rgba(251,191,36,0.3))' : ''}
              />
            {/each}
          </div>

          <p class="text-white/80 text-xs leading-relaxed italic font-medium tracking-tight">
            "{review.content}"
          </p>
        </div>
      {/each}
    {/if}
  </div>

  <div class="mt-4 pb-6">
    <button 
      onclick={() => showFormModal = true}
      class="w-full py-6 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-[2.5rem] font-black text-[13px] tracking-[0.3em] flex items-center justify-center gap-3 active:scale-95 transition-all uppercase italic shadow-[0_0_30px_rgba(16,185,129,0.15)]"
    >
      <MessageSquarePlus class="w-5 h-5" /> {labels.cta_write}
    </button>
  </div>

  <div class="absolute -top-32 -right-32 w-80 h-80 bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none"></div>
</div>

  <!-- Design Flourish -->
  <div class="absolute -top-32 -right-32 w-64 h-64 bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none"></div>
  <div class="absolute -bottom-32 -left-32 w-64 h-64 bg-blue-500/5 blur-[100px] rounded-full pointer-events-none"></div>

<!-- Mobile Form Modal -->
{#if showFormModal}
  <div 
    class="fixed inset-0 bg-black/90 backdrop-blur-2xl flex flex-col pt-12"
    style:z-index={Z_INDEX_CLIENT.MOBILE_REVIEW_OVERLAY}
    transition:fade={{ duration: 300 }}
  >
    <div class="p-6 flex items-center justify-between border-b border-white/10">
      <div class="text-xs font-black text-white/40 uppercase tracking-[0.3em] font-mono">
        {labels.label_store_verified}
      </div>
      <button
        onclick={() => showFormModal = false}
        class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-white/60 active:scale-90"
      >
        <X class="w-6 h-6" />
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-8">
      {#if showSuccess}
        <div class="h-full flex flex-col items-center justify-center text-center pb-20" in:scale={{ duration: 600, easing: elasticOut }}>
          <div class="w-24 h-24 bg-emerald-500/20 rounded-3xl flex items-center justify-center mb-8 border border-emerald-500/40">
            <CheckCircle2 class="w-12 h-12 text-emerald-400" />
          </div>
          <h3 class="text-4xl font-black text-white italic uppercase tracking-tighter mb-4">{labels.success_title}</h3>
          <p class="text-white/40 text-[11px] font-bold uppercase tracking-[0.2em] max-w-[240px] leading-relaxed">
            {labels.success_msg}
          </p>
        </div>
      {:else}
        <div in:fly={{ y: 20 }}>
          <h3 class="text-2xl font-black text-white uppercase italic tracking-tighter mb-8">{labels.form_title}</h3>

          <form onsubmit={handleSubmit} class="space-y-6 pb-12">
            <div class="space-y-4">
              <div class="relative">
                <User class="absolute left-4 top-5 w-4 h-4 text-white/20" />
                <input
                  type="text"
                  bind:value={name}
                  placeholder="Danh tính của bạn"
                  class="w-full bg-white/[0.03] border border-white/10 px-12 py-5 rounded-2xl text-white outline-none focus:border-emerald-500/50 transition-colors uppercase font-black text-xs tracking-widest placeholder:text-white/10"
                />
              </div>
              <div class="relative">
                <Phone class="absolute left-4 top-5 w-4 h-4 text-white/20" />
                <input
                  type="tel"
                  bind:value={phone}
                  placeholder="Số điện thoại bảo mật"
                  class="w-full bg-white/[0.03] border border-white/10 px-12 py-5 rounded-2xl text-white outline-none focus:border-emerald-500/50 transition-colors font-mono tracking-[0.2em] text-xs placeholder:text-white/10"
                />
              </div>
              <div class="relative">
                <MapPin class="absolute left-4 top-5 w-4 h-4 text-white/20" />
                <select
                  bind:value={locationSelected}
                  class="w-full bg-white/[0.03] border border-white/10 px-12 py-5 rounded-2xl text-white outline-none focus:border-emerald-500/50 transition-colors appearance-none uppercase font-black text-xs tracking-widest {locationSelected ? 'text-white' : 'text-white/20'}"
                >
                  <option value="" disabled>Chọn Vị trí</option>
                  {#each locations as loc}
                    <option value={loc}>{loc}</option>
                  {/each}
                </select>
              </div>
            </div>

            <div class="py-6 border-y border-white/5 space-y-4">
              <p class="text-center text-[10px] font-black text-white/20 uppercase tracking-[0.4em] mb-4">Đánh giá hệ thống</p>
              <div class="flex justify-center gap-4">
                {#each Array(5) as _, i}
                  <button
                    type="button"
                    onclick={() => ratingSelected = i + 1}
                    class="transition-transform active:scale-95"
                  >
                    <Star class="w-8 h-8 {i < ratingSelected ? 'text-amber-400 fill-amber-400' : 'text-white/5'}" style={i < ratingSelected ? 'filter: drop-shadow(0 0 10px rgba(251,191,36,0.6))' : ''} />
                  </button>
                {/each}
              </div>
            </div>

            <div class="space-y-4">
              <textarea
                bind:value={content}
                placeholder="Nhập trải nghiệm thực tế tại đây..."
                class="w-full h-40 bg-white/[0.03] border border-white/10 p-6 rounded-3xl text-white focus:border-emerald-500/50 transition-colors text-sm leading-relaxed placeholder:text-white/10 outline-none"
              ></textarea>
            </div>

            <!-- Honeypot -->
            <input type="text" bind:value={websiteUrl} class="hidden" tabindex="-1" />

            <button
              type="submit"
              disabled={isSubmitting}
              class="w-full py-6 bg-emerald-500 rounded-3xl font-black text-slate-950 text-base tracking-[0.4em] uppercase flex items-center justify-center gap-3 disabled:opacity-50 active:scale-[0.98] transition-all"
            >
              {#if isSubmitting}
                <div class="w-5 h-5 border-2 border-slate-950/20 border-t-slate-950 rounded-full animate-spin"></div>
              {:else}
                GỬI PHẢN HỒI <Send class="w-4 h-4" />
              {/if}
            </button>
          </form>
        </div>
      {/if}
    </div>
  </div>
{/if}

<!-- Toast -->
{#if showToast}
  <div
    class="fixed top-8 left-6 right-6"
    style:z-index={Z_INDEX_CLIENT.MOBILE_REVIEW_HEADER}
    transition:fly={{ y: -50 }}
  >
    <div class="bg-red-500/20 border border-red-500/40 backdrop-blur-2xl px-6 py-4 rounded-2xl flex items-center gap-3">
      <div class="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse"></div>
      <span class="text-xs font-black text-red-100 uppercase tracking-widest">{toastMessage}</span>
    </div>
  </div>
{/if}

<style>
  .scrollbar-hide::-webkit-scrollbar { display: none; }
  .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
  
  .review-card-mobile {
    width: 92vw;
    max-width: 440px;
    transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  }
</style>
