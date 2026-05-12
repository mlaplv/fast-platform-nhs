<script lang="ts">
  import { onMount } from 'svelte';
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import Star from "@lucide/svelte/icons/star";
  import ThumbsUp from "@lucide/svelte/icons/thumbs-up";
  import MessageCircle from "@lucide/svelte/icons/message-circle";
  import Share2 from "@lucide/svelte/icons/share-2";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import Play from "@lucide/svelte/icons/play";
  import Camera from "@lucide/svelte/icons/camera";
  import Clock from "@lucide/svelte/icons/clock";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import Send from "@lucide/svelte/icons/send";
  import X from "@lucide/svelte/icons/x";
  import PenLine from "@lucide/svelte/icons/pen-line";
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { apiClient } from '$lib/utils/apiClient';

  let { data } = $props();
  const entity = $derived(data.entity);
  const entityType = $derived(data.entityType);
  const product = $derived(entityType === 'PRODUCT' ? entity : null);
  const category = $derived(entityType === 'CATEGORY' ? entity : null);
  const news = $derived(entityType === 'NEWS' ? entity : null);
  const ui = getClientUi();
  const cartStore = getCartStore();

  // --- State ---
  let reviews = $state<any[]>([]);
  let stats = $state<any>(null);
  let isLoading = $state(true);
  let activeFilter = $state<string>('all');
  let sortMode = $state<'newest' | 'highest'>('newest');
  let lightboxSrc = $state<string | null>(null);
  let activeDropdownId = $state<string | null>(null);

  // --- Write Review State ---
  let showWriteSheet = $state(false);
  let writeRating = $state(5);
  let writeContent = $state('');
  let writePhotos = $state<string[]>([]);
  let writePhone = $state('');
  let isUploadingPhoto = $state(false);
  let isSubmitting = $state(false);
  let submitSuccess = $state(false);
  let fileInputEl = $state<HTMLInputElement | null>(null);

  // --- Filter definition (built from stats) ---
  // API trả về: rating_breakdown, has_media_count (xem review_service.py)
  const filters = $derived<Array<{ key: string; label: string; count: number; icon?: string }>>([
    { key: 'all', label: 'Tất cả', count: stats?.total_count || 0 },
    { key: 'media', label: 'Có ảnh/video', count: stats?.has_media_count || 0, icon: 'camera' },
    { key: '5', label: '5', count: stats?.rating_breakdown?.[5] || 0, icon: 'star' },
    { key: '4', label: '4', count: stats?.rating_breakdown?.[4] || 0, icon: 'star' },
    { key: '3', label: '3', count: stats?.rating_breakdown?.[3] || 0, icon: 'star' },
    { key: '2', label: '2', count: stats?.rating_breakdown?.[2] || 0, icon: 'star' },
    { key: '1', label: '1', count: stats?.rating_breakdown?.[1] || 0, icon: 'star' },
  ].filter(f => f.key === 'all' || f.count > 0));

  // --- Filtered + Sorted list ---
  const displayReviews = $derived(
    reviews
      .filter(r => {
        if (activeFilter === 'all') return true;
        if (activeFilter === 'media') return r.attachments?.length > 0;
        if (activeFilter === 'extra') return r.is_followup === true;
        const star = parseInt(activeFilter);
        if (!isNaN(star)) return r.rating === star;
        return true;
      })
      .sort((a, b) => {
        if (sortMode === 'newest') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        return b.rating - a.rating;
      })
  );

  // --- Data fetching ---
  async function fetchData() {
    isLoading = true;
    try {
      const [revRes, statRes] = await Promise.all([
        fetch(`/api/v1/client/reviews?entity_type=${entityType}&entity_id=${entity.id}&status=APPROVED`),
        fetch(`/api/v1/client/reviews/stats?entity_type=${entityType}&entity_id=${entity.id}`)
      ]);
      if (revRes.ok) reviews = (await revRes.json()).items;
      if (statRes.ok) stats = await statRes.json();
    } catch (e) {
      console.error('Error loading reviews:', e);
    } finally {
      isLoading = false;
    }
  }

  $effect(() => {
    if (entity?.id) {
      fetchData();
    }
  });

  onMount(() => {
    ui.isHeaderHidden = true;
    ui.isFooterHidden = true;

    // Elite V2.2: Deep-linking for Write Review Flow
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('write') === 'true') {
      openWriteSheet();
    }

    return () => {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  // --- Helpers ---
  function goBack() { window.history.back(); }

  function isVideo(url: string): boolean {
    return !!(url.match(/\.(mp4|webm|mov)$/i) || url.includes('video'));
  }

  function buyNow() {
    if (product) {
      cartStore.addItem(product);
      window.location.href = '/checkout';
    } else {
      window.location.href = `/${entity.slug}`;
    }
  }

  function openLightbox(src: string) { lightboxSrc = src; }
  function closeLightbox() { lightboxSrc = null; }

  function formatDate(iso: string): string {
    const d = new Date(iso);
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  }

  async function handleLike(review: any) {
    if (review._isLiked) return;
    
    // Optimistic UI
    review.likes_count = (review.likes_count || 0) + 1;
    review._isLiked = true;

    try {
      const res = await apiClient.post<{new_count: number}>(`/client/reviews/${review.id}/like`);
      if (res.new_count !== undefined) {
        review.likes_count = res.new_count;
      }
    } catch (e) {
      // Revert if error
      review.likes_count -= 1;
      review._isLiked = false;
      ui.showToast('Có lỗi xảy ra khi thích đánh giá', 'error');
    }
  }

  function handleReportReview(reviewId: string) {
    activeDropdownId = null;
    ui.openReportReview(reviewId);
  }

  function renderStars(html: string): string {
    return html.replace(/<[^>]*>?/gm, '');
  }

  const avgRating = $derived(stats?.average_rating ?? (entity as any).metadata?.rating ?? 5);
  const totalCount = $derived(stats?.total_count ?? 0);

  // --- Write Review Logic ---
  function openWriteSheet() {
    if (!authStore.isAuthenticated) {
      // Yêu cầu xác thực: nếu chua login, mở login modal
      ui.openLogin(() => { showWriteSheet = true; });
      return;
    }
    writeRating = 5;
    writeContent = '';
    writePhotos = [];
    submitSuccess = false;
    showWriteSheet = true;
  }

  function closeWriteSheet() { showWriteSheet = false; }

  async function handlePhotoUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;
    if (writePhotos.length + target.files.length > 5) {
      ui.showToast('Chỉ được tải lên tối đa 5 ảnh.', 'error');
      return;
    }
    isUploadingPhoto = true;
    try {
      for (let i = 0; i < target.files.length; i++) {
        const file = target.files[i];
        if (file.size > (file.type.startsWith('video/') ? 20 : 5) * 1024 * 1024) {
          ui.showToast(`File ${file.name} quá lớn.`, 'error'); continue;
        }
        const fd = new FormData();
        fd.append('data', file);
        const res = await fetch('/api/v1/client/reviews/upload', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${authStore.token}` },
          body: fd
        });
        if (res.ok) {
          const json = await res.json();
          if (json?.data?.file_path) writePhotos = [...writePhotos, json.data.file_path];
        } else {
          const err = await res.json();
          ui.showToast(err.detail || 'Lỗi upload ảnh.', 'error');
        }
      }
    } catch { ui.showToast('Lỗi kết nối máy chủ.', 'error'); }
    finally {
      isUploadingPhoto = false;
      if (fileInputEl) fileInputEl.value = '';
    }
  }

  async function submitWriteReview() {
    if (writeContent.trim().length < 5) {
      ui.showToast('Nội dung phải ít nhất 5 ký tự.', 'error'); return;
    }
    isSubmitting = true;
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (authStore.token) headers['Authorization'] = `Bearer ${authStore.token}`;
      const res = await fetch('/api/v1/client/reviews', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          entity_type: entityType,
          entity_id: entity.id,
          customer_name: authStore.user?.name || 'Khách hàng',
          customer_phone: writePhone || undefined,
          rating: writeRating,
          content: writeContent.trim(),
          attachments: writePhotos.map(url => ({ url, type: isVideo(url) ? 'video' : 'image' }))
        })
      });
      if (res.ok) {
        submitSuccess = true;
        setTimeout(() => { showWriteSheet = false; submitSuccess = false; fetchData(); }, 2200);
      } else {
        const err = await res.json();
        ui.showToast(err.detail || 'Gửi đánh giá thất bại.', 'error');
      }
    } catch { ui.showToast('Lỗi kết nối. Thử lại sau.', 'error'); }
    finally { isSubmitting = false; }
  }
</script>

<!-- ===== ROOT ===== -->
<div class="rv-root">

  <!-- ── HEADER ── -->
  <header class="rv-header">
    <button class="rv-back" onclick={goBack} aria-label="Quay lại">
      <ChevronLeft size={22} />
    </button>
    <h1 class="rv-header-title">Đánh giá khác ({totalCount})</h1>
    <div class="rv-header-actions">
      <button class="rv-icon-btn" aria-label="Chia sẻ"><Share2 size={18} /></button>
      <button class="rv-icon-btn rv-cart-btn" onclick={buyNow} aria-label="Giỏ hàng">
        <ShoppingCart size={18} />
        {#if cartStore.totalItems > 0}
          <span class="rv-cart-badge">{cartStore.totalItems > 9 ? '9+' : cartStore.totalItems}</span>
        {/if}
      </button>
      <button class="rv-write-btn" onclick={openWriteSheet} aria-label="Viết đánh giá">
        <PenLine size={14} />
        <span>Viết</span>
      </button>
    </div>
  </header>

  <!-- ── RATING SUMMARY ── -->
  {#if !isLoading && stats}
    <div class="rv-summary">
      <div class="rv-score-block">
        <span class="rv-score-num">{Number(avgRating).toFixed(1)}</span>
        <span class="rv-score-suffix">/5</span>
      </div>
      <div class="rv-score-right">
        <div class="rv-stars-row">
          {#each Array(5) as _, i}
            <Star size={14} class="{i < Math.round(avgRating) ? 'rv-star--filled' : 'rv-star--empty'}" fill="{i < Math.round(avgRating) ? '#C18F7E' : 'transparent'}" color="{i < Math.round(avgRating) ? '#C18F7E' : '#ddd'}" />
          {/each}
        </div>
        <p class="rv-total-label">{totalCount.toLocaleString('vi-VN')} đánh giá thực tế</p>
        {#if stats.rating_breakdown}
          <div class="rv-dist">
            {#each [5,4,3,2,1] as star}
              {@const cnt = stats.rating_breakdown[star] || 0}
              {@const pct = totalCount > 0 ? Math.round(cnt/totalCount*100) : 0}
              <div class="rv-dist-row">
                <span class="rv-dist-star">{star}★</span>
                <div class="rv-dist-bar">
                  <div class="rv-dist-fill" style="width:{pct}%"></div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- ── FILTER CHIPS ── -->
  <div class="rv-filter-wrap">
    <div class="rv-filter-scroll">
      {#each filters as f}
        <button
          class="rv-chip {activeFilter === f.key ? 'rv-chip--active' : ''}"
          onclick={() => activeFilter = f.key}
        >
          {#if f.icon === 'camera'}
            <Camera size={11} />
          {:else if f.icon === 'star'}
            <Star size={11} fill={activeFilter === f.key ? 'white' : '#C18F7E'} color={activeFilter === f.key ? 'white' : '#C18F7E'} />
          {/if}
          {f.label}
          {#if f.count > 0}
            <span class="rv-chip-count">({f.count})</span>
          {/if}
        </button>
      {/each}
    </div>
  </div>

  <!-- ── SORT ROW ── -->
  <div class="rv-sort-row">
    <span class="rv-sort-label">
      Xem những khách hàng khác nhận xét gì
    </span>
    <button
      class="rv-sort-btn"
      onclick={() => sortMode = sortMode === 'newest' ? 'highest' : 'newest'}
    >
      {sortMode === 'newest' ? 'Mới nhất' : 'Tốt nhất'}
      <Clock size={12} />
    </button>
  </div>

  <!-- ── REVIEW LIST ── -->
  <div class="rv-list">
    {#if isLoading}
      <div class="rv-loading">
        <Loader2 size={28} class="rv-spinner" />
        <span>Đang tải đánh giá...</span>
      </div>
    {:else if displayReviews.length === 0}
      <div class="rv-empty">
        <MessageCircle size={48} class="rv-empty-icon" />
        <p>Chưa có đánh giá cho bộ lọc này</p>
      </div>
    {:else}
      {#each displayReviews as rev (rev.id)}
        <div class="rv-card">
          <!-- User row -->
          <div class="rv-card-user">
            <div class="rv-avatar">
              {#if rev.avatar_url}
                <img src={rev.avatar_url} alt={rev.customer_name} class="rv-avatar-img" />
              {:else}
                <span class="rv-avatar-initial">{(rev.customer_name || 'K').charAt(0).toUpperCase()}</span>
              {/if}
            </div>
            <div class="rv-user-meta">
              <div class="rv-username-row">
                <span class="rv-username">{rev.customer_name || 'Khách hàng'}</span>
                {#if rev.is_verified_buyer}
                  <span class="rv-verified">● ĐÃ MUA</span>
                {/if}
              </div>
              <div class="rv-stars-mini">
                {#each Array(5) as _, si}
                  <Star size={11} fill="{si < rev.rating ? '#C18F7E' : 'transparent'}" color="{si < rev.rating ? '#C18F7E' : '#ddd'}" />
                {/each}
                {#if rev.variant_name}
                  <span class="rv-variant-tag">· {rev.variant_name}</span>
                {/if}
              </div>
            </div>
          </div>

          <!-- Review text -->
          {#if rev.content}
            <p class="rv-text">{@html renderStars(rev.content)}</p>
          {/if}

          <!-- Product snippet card -->
          {#if entity}
            <div class="rv-product-ref">
              <div class="rv-product-thumb">
                {#if entity.images?.[0] || entity.image}
                  <img src={entity.images?.[0] || entity.image} alt={entity.name} />
                {:else}
                  <div class="rv-product-thumb-placeholder"></div>
                {/if}
              </div>
              <div class="rv-product-ref-info">
                <span class="rv-product-ref-name">{entity.name}</span>
                {#if entityType === 'PRODUCT' && entity.discountPrice && entity.discountPrice < entity.price}
                  <span class="rv-product-ref-avail rv-product-ref-avail--sale">Đang giảm giá</span>
                {:else}
                  <span class="rv-product-ref-avail">{entityType === 'PRODUCT' ? 'Còn hàng' : 'Khám phá ngay'}</span>
                {/if}
              </div>
            </div>
          {/if}

          <!-- Media grid -->
          {#if rev.attachments?.length > 0}
            <div class="rv-media-grid">
              {#each rev.attachments.slice(0, 4) as att, mi}
                <button
                  class="rv-media-item {mi === 3 && rev.attachments.length > 4 ? 'rv-media-more-wrap' : ''}"
                  onclick={() => openLightbox(att.url)}
                  aria-label="Xem ảnh"
                >
                  {#if isVideo(att.url)}
                    <!-- svelte-ignore a11y_media_has_caption -->
                    <video src={att.url} muted playsinline class="rv-media-thumb"></video>
                    <div class="rv-play-badge"><Play size={14} fill="white" color="white" /></div>
                  {:else}
                    <img src={att.url} alt="Ảnh đánh giá" class="rv-media-thumb" loading="lazy" />
                  {/if}
                  {#if mi === 3 && rev.attachments.length > 4}
                    <div class="rv-media-count">+{rev.attachments.length - 4}</div>
                  {/if}
                </button>
              {/each}
            </div>
          {/if}

          <!-- Card footer -->
          <div class="rv-card-footer">
            <span class="rv-date">{formatDate(rev.created_at)}</span>
            {#if rev.category_name}
              <span class="rv-cat-dot">· {rev.category_name}</span>
            {:else}
              <span class="rv-cat-dot">· Mỹ phẩm</span>
            {/if}
            <div class="rv-footer-actions relative">
              <button 
                class="rv-more-btn p-1 text-gray-300 hover:text-gray-600 transition-colors"
                onclick={() => activeDropdownId = activeDropdownId === rev.id ? null : rev.id}
              >
                <MoreHorizontal size={18} />
              </button>

              {#if activeDropdownId === rev.id}
                <div class="absolute right-0 bottom-full mb-2 w-32 bg-white border border-gray-100 shadow-xl z-50 py-1 rounded-lg overflow-hidden">
                  <button 
                    onclick={() => handleReportReview(rev.id)}
                    class="w-full text-left px-4 py-2 text-[11px] font-bold text-red-500 hover:bg-red-50 transition-colors uppercase tracking-widest"
                  >
                    Báo cáo
                  </button>
                </div>
              {/if}

              <button 
                class="rv-like-btn {rev._isLiked ? 'text-luxury-copper scale-110' : 'text-gray-400'} transition-all flex items-center gap-1.5" 
                aria-label="Thích"
                onclick={() => handleLike(rev)}
              >
                <ThumbsUp size={16} fill={rev._isLiked ? "currentColor" : "none"} />
                <span class="text-xs font-bold">{rev.likes_count || 0}</span>
              </button>
            </div>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- ── BOTTOM CTA ── -->
  <div class="rv-bottom-cta">
    <div class="rv-cta-product">
      {#if entity.images?.[0] || entity.image}
        <img src={entity.images?.[0] || entity.image} alt={entity.name} class="rv-cta-thumb" />
      {/if}
      <div class="rv-cta-info">
        <span class="rv-cta-name">{entity.name}</span>
        <span class="rv-cta-price">
          {#if entityType === 'PRODUCT'}
            ₫{(entity.discountPrice || entity.price)?.toLocaleString('vi-VN')}
          {:else}
            Xem ngay
          {/if}
        </span>
      </div>
    </div>
    <button class="rv-cta-buy" onclick={buyNow}>
      {#if entityType === 'PRODUCT'}
        MUA<br />NGAY
      {:else}
        XEM<br />NGAY
      {/if}
    </button>
  </div>
</div>

<!-- ── WRITE REVIEW BOTTOM SHEET ── -->
{#if showWriteSheet}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="rv-sheet-overlay" onclick={(e) => { if (e.target === e.currentTarget) closeWriteSheet(); }}>
    <div class="rv-sheet">
      <!-- Handle -->
      <div class="rv-sheet-handle"><div class="rv-sheet-handle-bar"></div></div>

      <!-- Header -->
      <div class="rv-sheet-header">
        <h2 class="rv-sheet-title">Viết đánh giá</h2>
        <button class="rv-sheet-close" onclick={closeWriteSheet} aria-label="Đóng">
          <X size={20} />
        </button>
      </div>

      <!-- Body -->
      <div class="rv-sheet-body">
        {#if submitSuccess}
          <div class="rv-success-state">
            <div class="rv-success-icon">✓</div>
            <p class="rv-success-title">Gửi đánh giá thành công!</p>
            <p class="rv-success-sub">Cảm ơn bạn! Đánh giá đang chờ duyệt.</p>
          </div>
        {:else}
          <!-- Product info -->
          <div class="rv-product-ref">
            {#if entity.images?.[0] || entity.image}
              <div class="rv-product-thumb"><img src={entity.images?.[0] || entity.image} alt={entity.name} /></div>
            {/if}
            <div class="rv-product-ref-info">
              <span class="rv-product-ref-name">{entity.name}</span>
              <span class="rv-product-ref-avail">Mỹ phẩm osmo</span>
            </div>
          </div>

          <!-- Star picker -->
          <div class="rv-star-picker">
            <span class="rv-star-picker-label">Mức độ hài lòng của bạn</span>
            <div class="rv-star-row">
              {#each Array(5) as _, si}
                <button
                  class="rv-star-pick-btn"
                  onclick={() => writeRating = si + 1}
                  aria-label="{si+1} sao"
                >
                  <Star
                    size={34}
                    fill="{si < writeRating ? '#C18F7E' : 'transparent'}"
                    color="{si < writeRating ? '#C18F7E' : '#ddd'}"
                  />
                </button>
              {/each}
            </div>
            <span class="rv-star-hint">
              {(['Rất tệ 😞', 'Tệ 😕', 'Bình thường 😐', 'Hài lòng 😊', 'Tuyệt vời 🤩'])[writeRating - 1]}
            </span>
          </div>

          <!-- Content -->
          <div>
            <label class="rv-content-label" for="rv-textarea">Cảm nhận của bạn *</label>
            <textarea
              id="rv-textarea"
              class="rv-textarea"
              bind:value={writeContent}
              placeholder="Chia sẻ cảm nhận về sản phẩm, chất lượng, mùi hương, hiệu quả dưỡng da..."
              maxlength="2000"
              rows="4"
            ></textarea>
            <p class="rv-char-count">{writeContent.length}/2000</p>
          </div>

          <!-- Photo upload -->
          <div>
            <label class="rv-content-label">Thêm ảnh / video (tối đa 5)</label>
            <div class="rv-photo-strip">
              {#each writePhotos as photo, pi}
                <div class="rv-photo-thumb">
                  {#if isVideo(photo)}
                    <!-- svelte-ignore a11y_media_has_caption -->
                    <video src={photo} muted playsinline></video>
                  {:else}
                    <img src={photo} alt="Ảnh đánh giá {pi+1}" />
                  {/if}
                  <button
                    class="rv-photo-remove"
                    onclick={() => writePhotos = writePhotos.filter((_, i) => i !== pi)}
                    aria-label="Xoá ảnh"
                  >×</button>
                </div>
              {/each}

              {#if writePhotos.length < 5}
                <!-- hidden native input -->
                <input
                  bind:this={fileInputEl}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,video/mp4,video/webm"
                  multiple
                  onchange={handlePhotoUpload}
                  style="display:none"
                />
                <button
                  class="rv-add-photo"
                  onclick={() => fileInputEl?.click()}
                  disabled={isUploadingPhoto}
                  aria-label="Thêm ảnh"
                >
                  {#if isUploadingPhoto}
                    <Loader2 size={20} class="rv-spin" />
                    <span>Đang tải...</span>
                  {:else}
                    <Camera size={20} />
                    <span>Thêm ảnh</span>
                  {/if}
                </button>
              {/if}
            </div>
          </div>
        {/if}
      </div>

      <!-- Footer / Submit -->
      {#if !submitSuccess}
        <div class="rv-sheet-footer">
          <button
            class="rv-submit-btn"
            onclick={submitWriteReview}
            disabled={isSubmitting || writeContent.trim().length < 5}
          >
            {#if isSubmitting}
              <Loader2 size={18} class="rv-spin" />
              Đang gửi...
            {:else}
              <Send size={16} /> Gửi đánh giá
            {/if}
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<!-- ── LIGHTBOX ── -->
{#if lightboxSrc}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="rv-lightbox" onclick={closeLightbox}>
    {#if isVideo(lightboxSrc)}
      <!-- svelte-ignore a11y_media_has_caption -->
      <video src={lightboxSrc} controls autoplay class="rv-lightbox-media"></video>
    {:else}
      <img src={lightboxSrc} alt="Ảnh đánh giá" class="rv-lightbox-media" />
    {/if}
  </div>
{/if}

<style>
  *, *::before, *::after { box-sizing: border-box; }

  /* ── ROOT ── */
  .rv-root {
    position: fixed;
    inset: 0;
    background: #f5f5f5;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    font-family: 'Be Vietnam Pro', 'Be Vietnam Pro', system-ui, sans-serif;
    z-index: 1200;
  }

  /* ── HEADER ── */
  .rv-header {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 16px;
    height: 52px;
    background: #fff;
    border-bottom: 1px solid #f0f0f0;
    flex-shrink: 0;
  }
  .rv-back {
    background: none;
    border: none;
    padding: 6px;
    cursor: pointer;
    color: #333;
    display: flex;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .rv-header-title {
    flex: 1;
    font-size: 15px;
    font-weight: 800;
    color: #111;
    margin: 0;
    text-align: center;
  }
  .rv-header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }
  .rv-icon-btn {
    background: none;
    border: none;
    padding: 6px;
    cursor: pointer;
    color: #333;
    display: flex;
    border-radius: 50%;
    position: relative;
  }
  .rv-cart-btn { color: #333; }
  .rv-cart-badge {
    position: absolute;
    top: 0; right: 0;
    background: #C18F7E;
    color: #fff;
    font-size: 9px;
    font-weight: 900;
    min-width: 14px;
    height: 14px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 3px;
    border: 1.5px solid #fff;
  }

  /* ── SCROLLABLE AREA ── */
  :global(.rv-root > .rv-summary),
  :global(.rv-root > .rv-filter-wrap),
  :global(.rv-root > .rv-sort-row),
  :global(.rv-root > .rv-list) {
    overflow-y: auto;
  }

  /* wrapper for all scrollable content */
  .rv-summary,
  .rv-filter-wrap,
  .rv-sort-row,
  .rv-list {
    overflow: visible;
  }

  /* Make the whole thing scroll */
  .rv-root {
    overflow-y: auto;
  }
  .rv-root > .rv-header {
    position: sticky;
    top: 0;
  }

  /* ── RATING SUMMARY ── */
  .rv-summary {
    background: #fff;
    padding: 16px;
    display: flex;
    gap: 16px;
    align-items: flex-start;
    border-bottom: 8px solid #f5f5f5;
    flex-shrink: 0;
  }
  .rv-score-block {
    display: flex;
    align-items: baseline;
    gap: 2px;
    flex-shrink: 0;
  }
  .rv-score-num {
    font-size: 42px;
    font-weight: 900;
    color: #C18F7E;
    line-height: 1;
  }
  .rv-score-suffix {
    font-size: 16px;
    color: #bbb;
    font-weight: 500;
  }
  .rv-score-right {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .rv-stars-row {
    display: flex;
    gap: 3px;
  }
  .rv-star--filled { }
  .rv-star--empty { }
  .rv-total-label {
    font-size: 11px;
    color: #888;
    font-weight: 600;
    margin: 0;
  }
  .rv-dist {
    display: flex;
    flex-direction: column;
    gap: 3px;
    margin-top: 4px;
  }
  .rv-dist-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .rv-dist-star {
    font-size: 10px;
    color: #C18F7E;
    font-weight: 700;
    width: 22px;
    flex-shrink: 0;
  }
  .rv-dist-bar {
    flex: 1;
    height: 4px;
    background: #f0ebe8;
    border-radius: 4px;
    overflow: hidden;
  }
  .rv-dist-fill {
    height: 100%;
    background: linear-gradient(90deg, #C18F7E, #E3B5A4);
    border-radius: 4px;
    transition: width 0.5s ease;
  }

  /* ── FILTER CHIPS ── */
  .rv-filter-wrap {
    background: #fff;
    padding: 12px 0 10px;
    flex-shrink: 0;
    border-bottom: 1px solid #f0f0f0;
    overflow: hidden;
  }
  .rv-filter-scroll {
    display: flex;
    overflow-x: auto;
    scrollbar-width: none;
    gap: 8px;
    padding: 0 16px;
    flex-wrap: wrap;
  }
  .rv-filter-scroll::-webkit-scrollbar { display: none; }
  .rv-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    border: 1.5px solid #e8e8e8;
    background: #fff;
    color: #444;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }
  .rv-chip--active {
    background: linear-gradient(135deg, #C18F7E, #E3B5A4);
    border-color: #C18F7E;
    color: #fff;
  }
  .rv-chip-count {
    font-size: 11px;
    font-weight: 600;
    opacity: 0.8;
  }

  /* ── SORT ROW ── */
  .rv-sort-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #fff;
    padding: 10px 16px;
    margin-top: 8px;
    border-bottom: 1px solid #f0f0f0;
    flex-shrink: 0;
  }
  .rv-sort-label {
    font-size: 11px;
    color: #888;
    font-weight: 500;
  }
  .rv-sort-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: none;
    border: none;
    font-size: 12px;
    font-weight: 700;
    color: #C18F7E;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 6px;
  }

  /* ── REVIEW LIST ── */
  .rv-list {
    flex: 1;
    padding-bottom: 80px;
  }

  .rv-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 60px 0;
    color: #C18F7E;
    font-size: 13px;
    font-weight: 600;
  }
  :global(.rv-spinner) {
    animation: rv-spin 1s linear infinite;
    color: #C18F7E;
  }
  @keyframes rv-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

  .rv-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    gap: 12px;
    color: #ccc;
    font-size: 13px;
  }
  :global(.rv-empty-icon) { color: #ddd; }

  /* ── REVIEW CARD ── */
  .rv-card {
    background: #fff;
    margin-bottom: 8px;
    padding: 16px;
    border-bottom: 1px solid #f5f5f5;
  }

  .rv-card-user {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }
  .rv-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    overflow: hidden;
    background: linear-gradient(135deg, #f5ede9, #e8d5cc);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .rv-avatar-img { width: 100%; height: 100%; object-fit: cover; }
  .rv-avatar-initial {
    font-size: 16px;
    font-weight: 900;
    color: #C18F7E;
  }
  .rv-user-meta { flex: 1; }
  .rv-username-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
  }
  .rv-username {
    font-size: 13px;
    font-weight: 800;
    color: #222;
  }
  .rv-verified {
    font-size: 10px;
    font-weight: 900;
    color: #C18F7E;
    background: rgba(193,143,126,0.1);
    padding: 2px 6px;
    border-radius: 4px;
  }
  .rv-stars-mini {
    display: flex;
    align-items: center;
    gap: 2px;
  }
  .rv-variant-tag {
    font-size: 10px;
    color: #999;
    font-weight: 600;
    margin-left: 2px;
  }

  /* Review text */
  .rv-text {
    font-size: 14px;
    color: #333;
    line-height: 1.65;
    margin: 0 0 12px;
  }

  /* Product reference card */
  .rv-product-ref {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 12px;
  }
  .rv-product-thumb {
    width: 40px;
    height: 40px;
    border-radius: 6px;
    overflow: hidden;
    background: #f0f0f0;
    flex-shrink: 0;
  }
  .rv-product-thumb img { width: 100%; height: 100%; object-fit: cover; }
  .rv-product-thumb-placeholder { width: 100%; height: 100%; background: #eee; }
  .rv-product-ref-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .rv-product-ref-name {
    font-size: 12px;
    font-weight: 700;
    color: #333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .rv-product-ref-avail {
    font-size: 11px;
    color: #aaa;
    font-weight: 500;
  }
  .rv-product-ref-avail--sale {
    color: #C18F7E;
    font-weight: 700;
  }

  /* Media grid */
  .rv-media-grid {
    display: flex;
    gap: 6px;
    margin-bottom: 12px;
    flex-wrap: wrap;
  }
  .rv-media-item {
    width: 90px;
    height: 90px;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    border: none;
    padding: 0;
    cursor: pointer;
    background: #f0f0f0;
    flex-shrink: 0;
  }
  .rv-media-thumb { width: 100%; height: 100%; object-fit: cover; display: block; }
  .rv-play-badge {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0,0,0,0.25);
  }
  .rv-media-more-wrap { position: relative; }
  .rv-media-count {
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 900;
    color: #fff;
  }

  /* Card footer */
  .rv-card-footer {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .rv-date {
    font-size: 11px;
    color: #bbb;
    font-weight: 500;
  }
  .rv-cat-dot {
    font-size: 11px;
    color: #bbb;
    font-weight: 500;
  }
  .rv-footer-actions {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .rv-more-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    cursor: pointer;
  }
  .rv-like-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    background: none;
    border: none;
    color: #aaa;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    padding: 4px;
    border-radius: 6px;
    transition: color 0.2s;
  }
  .rv-like-btn:active { color: #C18F7E; }

  /* ── BOTTOM CTA ── */
  .rv-bottom-cta {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: rgba(255,255,255,0.97);
    border-top: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    padding-bottom: max(10px, env(safe-area-inset-bottom));
    z-index: 20;
    box-shadow: 0 -4px 16px rgba(0,0,0,0.06);
  }
  .rv-cta-product {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-width: 0;
  }
  .rv-cta-thumb {
    width: 42px;
    height: 42px;
    border-radius: 6px;
    object-fit: cover;
    border: 1px solid #f0f0f0;
    flex-shrink: 0;
  }
  .rv-cta-info {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .rv-cta-name {
    font-size: 11px;
    font-weight: 700;
    color: #333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .rv-cta-price {
    font-size: 15px;
    font-weight: 900;
    color: #C18F7E;
  }
  .rv-cta-buy {
    background: linear-gradient(135deg, #C18F7E, #E3B5A4);
    color: #fff;
    font-size: 11px;
    font-weight: 900;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    text-align: center;
    line-height: 1.3;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 12px rgba(193,143,126,0.3);
    flex-shrink: 0;
    white-space: nowrap;
  }
  .rv-cta-buy:active { opacity: 0.85; }

  /* ── LIGHTBOX ── */
  .rv-lightbox {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.92);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    cursor: zoom-out;
  }
  .rv-lightbox-media {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  /* ── WRITE BUTTON (header) ── */
  .rv-write-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: linear-gradient(135deg, #C18F7E, #E3B5A4);
    color: #fff;
    border: none;
    border-radius: 20px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 800;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(193,143,126,0.3);
    letter-spacing: 0.2px;
    transition: opacity 0.2s;
  }
  .rv-write-btn:active { opacity: 0.8; }

  /* ── WRITE BOTTOM SHEET OVERLAY ── */
  .rv-sheet-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.45);
    z-index: 1400;
    display: flex;
    align-items: flex-end;
    justify-content: center;
  }
  .rv-sheet {
    background: #fff;
    border-radius: 20px 20px 0 0;
    width: 100%;
    max-height: 92dvh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: rv-sheet-up 0.32s cubic-bezier(0.25, 1, 0.5, 1);
  }
  @keyframes rv-sheet-up {
    from { transform: translateY(100%); }
    to   { transform: translateY(0); }
  }
  .rv-sheet-handle {
    display: flex;
    justify-content: center;
    padding: 12px 0 4px;
    flex-shrink: 0;
  }
  .rv-sheet-handle-bar {
    width: 36px; height: 4px;
    background: #e0e0e0;
    border-radius: 4px;
  }
  .rv-sheet-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px 12px;
    border-bottom: 1px solid #f5f5f5;
    flex-shrink: 0;
  }
  .rv-sheet-title {
    font-size: 15px;
    font-weight: 900;
    color: #111;
    margin: 0;
  }
  .rv-sheet-close {
    background: none; border: none;
    padding: 6px; cursor: pointer;
    color: #888;
    display: flex; border-radius: 50%;
  }
  .rv-sheet-body {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* Star picker */
  .rv-star-picker {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
  .rv-star-picker-label {
    font-size: 12px; color: #888; font-weight: 600;
  }
  .rv-star-row {
    display: flex; gap: 8px;
  }
  .rv-star-pick-btn {
    background: none; border: none;
    padding: 4px; cursor: pointer;
    transition: transform 0.15s;
  }
  .rv-star-pick-btn:active { transform: scale(1.3); }
  .rv-star-hint {
    font-size: 13px; font-weight: 700;
    color: #C18F7E;
  }

  /* Textarea */
  .rv-content-label {
    font-size: 12px; font-weight: 700; color: #555; margin-bottom: 6px;
    display: block;
  }
  .rv-textarea {
    width: 100%;
    min-height: 100px;
    border: 1.5px solid #e8e8e8;
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
    font-family: inherit;
    color: #333;
    resize: none;
    outline: none;
    transition: border-color 0.2s;
    box-sizing: border-box;
  }
  .rv-textarea:focus { border-color: #C18F7E; }
  .rv-char-count {
    text-align: right; font-size: 10px; color: #bbb; margin-top: 4px;
  }

  /* Photo strip */
  .rv-photo-strip {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .rv-photo-thumb {
    width: 72px; height: 72px;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    border: 1.5px solid #f0ebe8;
    flex-shrink: 0;
  }
  .rv-photo-thumb img, .rv-photo-thumb video {
    width: 100%; height: 100%; object-fit: cover;
  }
  .rv-photo-remove {
    position: absolute; top: 2px; right: 2px;
    background: rgba(0,0,0,0.55); color: #fff;
    border: none; border-radius: 50%; width: 18px; height: 18px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; font-size: 11px; font-weight: 900; padding: 0;
  }
  .rv-add-photo {
    width: 72px; height: 72px;
    border-radius: 8px;
    border: 1.5px dashed #C18F7E;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 4px; background: #FFF8F5;
    color: #C18F7E; cursor: pointer;
    font-size: 10px; font-weight: 700;
    flex-shrink: 0;
  }
  .rv-add-photo:active { opacity: 0.7; }

  /* Submit bar */
  .rv-sheet-footer {
    padding: 12px 16px;
    padding-bottom: max(12px, env(safe-area-inset-bottom));
    border-top: 1px solid #f5f5f5;
    flex-shrink: 0;
  }
  .rv-submit-btn {
    width: 100%;
    background: linear-gradient(135deg, #C18F7E, #E3B5A4);
    color: #fff;
    border: none; border-radius: 10px;
    padding: 14px;
    font-size: 14px; font-weight: 900;
    cursor: pointer; display: flex;
    align-items: center; justify-content: center;
    gap: 8px; letter-spacing: 0.3px;
    box-shadow: 0 4px 14px rgba(193,143,126,0.35);
    transition: opacity 0.2s;
  }
  .rv-submit-btn:disabled { opacity: 0.4; pointer-events: none; }
  .rv-submit-btn:active { opacity: 0.85; }

  /* Success state */
  .rv-success-state {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 12px; padding: 40px 0;
    text-align: center;
  }
  .rv-success-icon {
    width: 60px; height: 60px;
    background: linear-gradient(135deg, #C18F7E, #E3B5A4);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 28px;
  }
  .rv-success-title {
    font-size: 16px; font-weight: 900; color: #222;
    margin: 0;
  }
  .rv-success-sub {
    font-size: 13px; color: #888; margin: 0;
  }

  /* Spinner */
  :global(.rv-spin) { animation: rv-spin-anim 1s linear infinite; }
  @keyframes rv-spin-anim { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>