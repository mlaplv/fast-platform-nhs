<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import vnDivisions from '$lib/data/vn_divisions.json';
  import { fade, fly, scale } from 'svelte/transition';
  import { elasticOut } from 'svelte/easing';
  import Star from "@lucide/svelte/icons/star";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import MessageSquarePlus from "@lucide/svelte/icons/message-square-plus";
  import X from "@lucide/svelte/icons/x";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import Phone from "@lucide/svelte/icons/phone";
  import User from "@lucide/svelte/icons/user";
  import Send from "@lucide/svelte/icons/send";
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import { getShopStore } from '$lib/state/commerce/shop.svelte';

  import type { Review, Product } from '$lib/types';
  import { mapRawReview, type RawReview } from '$lib/utils/review';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  // Module-scoped static lists to prevent re-computation on every component mount
  const locations = (vnDivisions as Array<{ name: string }>).slice(1).map(d =>
    d.name.replace('Thành phố ', 'TP. ').replace('Tỉnh ', '').toUpperCase()
  );

  function normalize(str: string) {
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
  }

  interface Props {
    product: Product;
    initialReviews?: Review[];
  }
  let { product: propProduct, initialReviews = [] }: Props = $props();
  const shopStore = getShopStore();
  const ui = getClientUi();
  const product = $derived(propProduct || shopStore.product);
  const metadata = $derived(product?.metadata || {});

  const stripTags = (h: string) => h ? h.replace(/<[^>]*>?/gm, '').trim() : '';
  const legacyParts = $derived(metadata.reviews_headline?.split('//') || []);
  const h1 = $derived(metadata.reviews_headline_1 || stripTags(legacyParts[0]) || 'KHÁCH HÀNG');
  const h2 = $derived(metadata.reviews_headline_2 || stripTags(legacyParts[1]) || 'NÓI GÌ VỀ CHÚNG TÔI?');

  let realReviews = $state<Review[]>(initialReviews.length > 0 ? initialReviews.map(mapRawReview) : []);
  let isLoading = $state(initialReviews.length === 0);

  const labels = $derived({
    label_verified: metadata?.reviews_label_verified || 'Đã xác thực',
    label_store_verified: metadata?.reviews_label_store_verified || 'Xác thực bởi Cửa hàng',
    cta_write: metadata?.reviews_cta_write || 'Viết đánh giá',
    form_title: metadata?.reviews_form_title || 'Gửi đánh giá mới',
    success_title: metadata?.reviews_form_success_title || 'Thành công!',
    success_msg: metadata?.reviews_form_success_msg || 'Đánh giá của bạn đã được ghi nhận và đang chờ duyệt.'
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
  let locationSearch = $state('');

  // Toast System
  let toastMessage = $state('');
  let showToast = $state(false);
  
  const activeTimers = new Set<ReturnType<typeof setTimeout>>();

  $effect(() => {
    // Đóng form khi đăng xuất
    if (!authStore.isAuthenticated && showFormModal) {
      showFormModal = false;
    }
  });

  onDestroy(() => {
    activeTimers.forEach(clearTimeout);
    activeTimers.clear();
  });

  const filteredLocations = $derived.by(() => {
    let query = normalize(locationSearch);
    if (query === 'hcm') query = 'ho chi minh';
    if (query === 'hn') query = 'ha noi';
    
    return locations.filter(loc => {
      const normalizedLoc = normalize(loc);
      return normalizedLoc.includes(query) || (query === 'ho chi minh' && normalizedLoc.includes('hcm'));
    });
  });

  function triggerToast(msg: string) {
    toastMessage = msg;
    showToast = true;
    const timer = setTimeout(() => { showToast = false; }, 3000);
    activeTimers.add(timer);
  }

  // Slider State (Elite V2.2)
  let activeReviewIndex = $state(0);
  let reviewsScroller = $state<HTMLDivElement>();
  let scrollTickingReviews = false;

  function syncReviewOnScroll() {
    if (!reviewsScroller || scrollTickingReviews) return;
    scrollTickingReviews = true;
    requestAnimationFrame(() => {
      if (reviewsScroller) {
        activeReviewIndex = Math.round(reviewsScroller.scrollLeft / reviewsScroller.clientWidth);
      }
      scrollTickingReviews = false;
    });
  }

  import { apiClient } from '$lib/utils/apiClient';

  async function fetchReviews() {
    if (!product?.id) return;
    isLoading = true;
    try {
      const data = await apiClient.get<{ items: RawReview[] }>(`/client/reviews`, {
        params: {
          entity_type: 'PRODUCT',
          entity_id: product.id,
          status: 'APPROVED'
        }
      });
      realReviews = (data.items || []).map(mapRawReview);
    } catch (e) {
      console.error("Reviews Error:", e);
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    if (realReviews.length === 0) {
      fetchReviews();
    }
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
      await apiClient.post('/client/reviews', {
        entity_type: 'PRODUCT',
        entity_id: product?.id || '',
        customer_name: name,
        customer_phone: phone,
        customer_location: locationSelected,
        rating: ratingSelected,
        content: content
      });

      showSuccess = true;
      const timer = setTimeout(() => {
        showFormModal = false;
        showSuccess = false;
        name = ''; phone = ''; content = ''; locationSelected = '';
      }, 4000);
      activeTimers.add(timer);
    } catch (e) {
      triggerToast("Lỗi hệ thống hoặc mất kết nối.");
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="reviews-mobile-viewport h-full flex flex-col px-[3px] pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] bg-[#030303] relative overflow-hidden" id="reviews">
  <!-- HUD Header & Content (Aligned to 26px Standard: 3px base + 23px internal) -->
  <div class="mt-3 mb-8 px-[23px]">
    <div class="inline-flex items-center gap-2 px-3 py-1 bg-[#FFB7C5]/10 border border-[#FFB7C5]/20 rounded-full backdrop-blur-md mb-6">
      <div class="w-1.5 h-1.5 rounded-full bg-[#FFB7C5] animate-pulse shadow-[0_0_8px_rgba(255,183,197,0.6)]"></div>
      <span class="text-[10px] tracking-[0.1em] text-[#FFB7C5] font-black italic">
        {metadata.reviews_hud_feedback || 'Hệ thống // Phản hồi thực tế'}
      </span>
    </div>
    
    <div class="header-content text-center mb-8 relative">
        <h2 class="text-2xl font-black text-white tracking-tighter mb-4 italic">
          {h1}
          <br/>
          <span class="text-luxury-sakura">
            {h2}
          </span>
        </h2>
    </div>
  </div>

  <div 
    class="flex overflow-x-auto snap-x snap-mandatory gap-0 scrollbar-hide pb-2 reviews-scroll-container w-full" 
    bind:this={reviewsScroller}
    onscroll={syncReviewOnScroll}
  >
    {#if isLoading && realReviews.length === 0}
      <div class="py-20 text-center w-full">
        <div class="w-10 h-10 border-2 border-[#FFB7C5]/20 border-t-[#FFB7C5] rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-[9px] font-black text-white/20 tracking-[0.4em]">Syncing_Voices...</p>
      </div>
    {:else if realReviews.length === 0}
      <div class="py-20 text-center opacity-20 w-full">
        <p class="text-[10px] font-black tracking-widest">No Feedback Detected</p>
      </div>
    {:else}
      {#each realReviews.slice(0, 8) as review, i}
        <div class="w-full flex-none snap-center flex justify-center">
          <div class="review-card-mobile p-6 bg-white/[0.03] border border-white/10 rounded-[5px] backdrop-blur-3xl relative overflow-hidden" style="width: calc(100% - 14px); max-width: 360px;" in:fly={{ y: 20, delay: i * 100 }}>
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-[5px] bg-white/5 border border-white/10 flex items-center justify-center text-[#FFB7C5] font-black text-xl italic shadow-inner">
                  {review.initial || (review.name ? review.name.charAt(0).toUpperCase() : '?')}
                </div>
                <div class="flex flex-col min-w-0">
                  <h4 class="text-white font-black text-sm tracking-tight italic leading-tight mb-1">{review.name || 'Ẩn danh'}</h4>
                  <div class="flex flex-col gap-0.5">
                    <div class="flex items-center gap-1.5">
                      <span class="text-[9px] text-white/40 font-bold tracking-tight">{review.location || 'Việt Nam'}</span>
                      <div class="w-1 h-1 rounded-full bg-[#FFB7C5]/40 animate-pulse"></div>
                      <span class="text-[9px] text-[#FFB7C5] font-black tracking-widest uppercase">{labels.label_verified}</span>
                    </div>
                    <span class="text-[9px] text-white/20 font-mono tracking-wider">
                      {review.phone}
                    </span>
                  </div>
                </div>
              </div>
              <div class="p-2 bg-white/5 rounded-xl border border-white/5">
                 <ShieldCheck class="w-4 h-4 text-[#FFB7C5]/40" />
              </div>
            </div>
            
            <div class="rating-row flex gap-1 mb-4">
              {#each Array(5) as _, s}
                <Star 
                  class="w-3 h-3 {s < review.rating ? 'text-amber-400 fill-amber-400 star-shimmer' : 'text-white/5'}" 
                />
              {/each}
            </div>

            <div class="text-white/80 text-xs leading-relaxed italic font-medium tracking-tight review-content-text">
              {#if review.content.includes("<")}
                {@html review.content}
              {:else}
                “{review.content}”
              {/if}
            </div>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  {#if realReviews.length > 1}
    <div class="flex justify-center gap-1.5 mt-2 mb-8">
      {#each realReviews.slice(0, 8) as _, idx}
        <button 
          class="w-1.5 h-1.5 rounded-full transition-all duration-300 {activeReviewIndex === idx ? 'bg-[#FFB7C5] w-3' : 'bg-white/20'}"
          onclick={() => {
            if (reviewsScroller) {
              reviewsScroller.scrollTo({ left: idx * reviewsScroller.clientWidth, behavior: 'smooth' });
            }
          }}
          aria-label="Xem đánh giá {idx + 1}"
        ></button>
      {/each}
    </div>
  {/if}

  <div class="mt-4 pb-6 px-[23px]">
      <button 
        onclick={() => {
          if (!authStore.isAuthenticated) {
            ui.openLogin(() => showFormModal = true);
          } else {
            showFormModal = true;
          }
        }}
        class="w-full py-6 bg-[#FFB7C5]/10 border border-[#FFB7C5]/30 text-[#FFB7C5] rounded-[2.5rem] font-black text-[13px] tracking-[0.3em] flex items-center justify-center gap-3 active:scale-95 transition-all italic shadow-[0_0_30px_rgba(255,183,197,0.15)]"
      >
        <MessageSquarePlus class="w-5 h-5" /> {labels.cta_write}
      </button>
  </div>

  <div class="absolute -top-32 -right-32 w-80 h-80 bg-[#FFB7C5]/5 blur-[120px] rounded-full pointer-events-none"></div>
</div>

  <!-- Design Flourish -->
  <div class="absolute -top-32 -right-32 w-64 h-64 bg-[#FFB7C5]/10 blur-[100px] rounded-full pointer-events-none"></div>
  <div class="absolute -bottom-32 -left-32 w-64 h-64 bg-[#FFB7C5]/5 blur-[100px] rounded-full pointer-events-none"></div>

<!-- Mobile Form Modal -->
{#if showFormModal}
  <div 
    class="fixed inset-0 bg-black/98 flex flex-col pt-12 reviews-form-modal"
    transition:fade={{ duration: 300 }}
  >
    <!-- Tactical Header -->
    <div class="px-4 py-4 flex items-center justify-between border-b border-white/5 bg-white/[0.01] overflow-hidden relative">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-xl bg-[#FFB7C5]/10 border border-[#FFB7C5]/20 flex items-center justify-center">
          <ShieldCheck class="w-4 h-4 text-[#FFB7C5]" />
        </div>
        <div class="flex flex-col">
          <div class="text-[9px] font-black text-[#FFB7C5] tracking-[0.3em] font-mono leading-none mb-1">
            {labels.label_store_verified}
          </div>
          <div class="text-[7px] font-bold text-white/20 tracking-[0.5em] font-mono">
            SECURE_SYNC // VERIFIED_NODE
          </div>
        </div>
      </div>

      <button
        onclick={() => showFormModal = false}
        class="w-8 h-8 rounded-full bg-white/[0.03] flex items-center justify-center text-white/20 hover:text-white/60 active:scale-90 transition-all group"
      >
        <X class="w-4 h-4 group-hover:rotate-90 transition-transform duration-500" />
      </button>

      <!-- HUD Decoration Line -->
      <div class="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#FFB7C5]/20 to-transparent"></div>
    </div>

    <div class="flex-1 overflow-y-auto px-4 py-8">
      {#if showSuccess}
        <div class="h-full flex flex-col items-center justify-center text-center pb-20" in:scale={{ duration: 600, easing: elasticOut }}>
          <div class="w-24 h-24 bg-[#FFB7C5]/20 rounded-3xl flex items-center justify-center mb-8 border border-[#FFB7C5]/40">
            <CheckCircle2 class="w-12 h-12 text-[#FFB7C5]" />
          </div>
          <h3 class="text-4xl font-black text-white italic tracking-tighter mb-4">{labels.success_title}</h3>
          <p class="text-white/40 text-[11px] font-bold tracking-[0.2em] max-w-[240px] leading-relaxed">
            {labels.success_msg}
          </p>
        </div>
      {:else}
        <div in:fly={{ y: 20 }}>
          <h3 class="text-2xl font-black text-white italic tracking-tighter mb-8">{labels.form_title}</h3>

          <form onsubmit={handleSubmit} class="space-y-6 pb-12">
            <div class="space-y-4">
              <div class="relative">
                <User class="absolute left-4 top-5 w-4 h-4 text-white/20" />
                <input
                  type="text"
                  bind:value={name}
                  placeholder="Danh tính của bạn"
                  class="w-full bg-white/[0.03] border border-white/10 px-12 py-5 rounded-2xl text-white outline-none focus:border-[#FFB7C5]/50 transition-colors font-black text-xs tracking-widest placeholder:text-white/10"
                />
              </div>
              <div class="relative">
                <Phone class="absolute left-4 top-5 w-4 h-4 text-white/20" />
                <input
                  type="tel"
                  bind:value={phone}
                  placeholder="Số điện thoại bảo mật"
                  class="w-full bg-white/[0.03] border border-white/10 px-12 py-5 rounded-2xl text-white outline-none focus:border-[#FFB7C5]/50 transition-colors font-mono tracking-[0.2em] text-xs placeholder:text-white/10"
                />
              </div>
              <div class="relative">
                <MapPin class="absolute left-4 top-5 w-4 h-4 text-white/20 {isLocationOpen ? 'text-[#FFB7C5]/60' : ''} transition-colors" />
                <button
                  type="button"
                  onclick={() => isLocationOpen = !isLocationOpen}
                  class="w-full bg-white/[0.03] border border-white/10 px-12 py-5 rounded-2xl text-left outline-none transition-all font-black text-xs tracking-widest {locationSelected ? 'text-white' : 'text-white/20'} {isLocationOpen ? 'border-[#FFB7C5]/50 bg-[#FFB7C5]/5 shadow-[0_0_20px_rgba(255,183,197,0.05)]' : ''}"
                >
                  {locationSelected || 'Chọn Vị trí'}
                </button>

                {#if isLocationOpen}
                  <div 
                    class="absolute top-full left-0 right-0 mt-2 bg-[#050505] border border-white/20 rounded-2xl shadow-[0_40px_100px_rgba(0,0,0,1)] z-modal overflow-hidden flex flex-col"
                    in:fly={{ y: -10, duration: 200 }}
                    out:fade={{ duration: 150 }}
                    onmouseleave={() => isLocationOpen = false}
                  >
                    <!-- Search Header -->
                    <div class="px-4 py-3 border-b border-white/10 bg-white/[0.02] flex items-center gap-3">
                      <div class="flex-1 relative">
                        <input
                          type="text"
                          bind:value={locationSearch}
                          placeholder="TÌM KIẾM TỈNH THÀNH..."
                          class="w-full bg-transparent text-[10px] font-black tracking-widest text-white outline-none placeholder:text-white/20"
                          autofocus
                        />
                      </div>
                      <button
                        type="button"
                        onclick={() => { isLocationOpen = false; locationSearch = ''; }}
                        class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-white/40 hover:text-white transition-colors"
                      >
                        <X class="w-4 h-4" />
                      </button>
                    </div>

                    <div class="max-h-72 overflow-y-auto scrollbar-hide">
                      {#if filteredLocations.length > 0}
                        {#each filteredLocations as loc}
                          <button
                            type="button"
                            onclick={() => { locationSelected = loc; isLocationOpen = false; locationSearch = ''; }}
                            class="w-full px-5 py-4 text-left text-[11px] font-black tracking-[0.2em] transition-all border-b border-white/5 last:border-none flex items-center justify-between group {locationSelected === loc ? 'bg-[#FFB7C5]/10 text-[#FFB7C5]' : 'text-white/60 hover:bg-white/[0.05] hover:text-white'}"
                          >
                            {loc}
                            {#if locationSelected === loc}
                              <div class="w-1.5 h-1.5 rounded-full bg-[#FFB7C5] shadow-[0_0_12px_rgba(255,183,197,0.8)]"></div>
                            {/if}
                          </button>
                        {/each}
                      {:else}
                        <div class="py-10 text-center text-[9px] font-black text-white/20 tracking-widest italic">
                          Không tìm thấy kết quả
                        </div>
                      {/if}
                    </div>
                  </div>
                {/if}
              </div>
            </div>

            <div class="py-6 border-y border-white/5 space-y-4">
              <p class="text-center text-[10px] font-black text-white/20 tracking-[0.4em] mb-4">Đánh giá hệ thống</p>
              <div class="flex justify-center gap-4">
                {#each Array(5) as _, i}
                  <button
                    type="button"
                    onclick={() => ratingSelected = i + 1}
                    class="transition-transform active:scale-95"
                  >
                    <Star class="w-8 h-8 {i < ratingSelected ? 'text-amber-400 fill-amber-400 star-shimmer-large' : 'text-white/5'}" />
                  </button>
                {/each}
              </div>
            </div>

            <div class="space-y-4">
              <textarea
                bind:value={content}
                placeholder="Nhập trải nghiệm thực tế tại đây..."
                class="w-full h-40 bg-white/[0.03] border border-white/10 p-6 rounded-3xl text-white focus:border-[#FFB7C5]/50 transition-colors text-sm leading-relaxed placeholder:text-white/10 outline-none"
              ></textarea>
            </div>

            <!-- Honeypot -->
            <input type="text" bind:value={websiteUrl} class="hidden" tabindex="-1" />

            <button
              type="submit"
              disabled={isSubmitting}
              class="w-full py-6 bg-[#FFB7C5] rounded-3xl font-black text-slate-950 text-base tracking-[0.4em] flex items-center justify-center gap-3 disabled:opacity-50 active:scale-[0.98] transition-all"
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
    class="fixed top-8 left-6 right-6 reviews-toast"
    transition:fly={{ y: -50 }}
  >
    <div class="bg-red-500/20 border border-red-500/40 backdrop-blur-2xl px-4 py-4 rounded-2xl flex items-center gap-3">
      <div class="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse"></div>
      <span class="text-xs font-black text-red-100 tracking-widest">{toastMessage}</span>
    </div>
  </div>
{/if}

<style>
  .scrollbar-hide::-webkit-scrollbar { display: none; }
  .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
  
  .review-card-mobile {
    width: calc(100% - 14px);
    max-width: 360px;
    transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .star-shimmer {
    filter: drop-shadow(0 0 6px rgba(251,191,36,0.3));
  }

  .star-shimmer-large {
    filter: drop-shadow(0 0 10px rgba(251,191,36,0.6));
  }

  .reviews-form-modal {
    z-index: var(--z-modal);
    background-color: #030303; /* Hardcoded solid fallback for VPS Mode */
  }

  .reviews-toast {
    z-index: var(--z-toast);
  }

  :global(.review-content-text p) {
    display: inline !important;
    margin: 0 !important;
    padding: 0 !important;
  }
</style>
