<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import "./VerifiedReviews.css";

  const reviews = [
    {
      id: 1,
      name: "K.H.",
      phone: "098124",
      location: "Hà Nội*",
      rating: 5,
      content: "Ám ảnh 5 năm không dám mặc sơ mi trắng vì ố vàng và ướt sũng. Hôm qua thử xịt đúng 1 lần buổi sáng, lúc lắc nhẹ thấy sương rất mịn mát. Đi làm cả ngày trời 40 độ mà tối về nách áo vẫn khô ron, không một mùi lạ. Thực sự là chân ái!",
      initial: "H"
    },
    {
      id: 2,
      name: "T.M.",
      phone: "090882",
      location: "TP.HCM*",
      rating: 5,
      content: "Cơ địa nội tiết mình ra mồ hôi như tắm, dùng đủ loại lăn ngoại nhập đều bó tay. Bác sĩ da liễu khuyên dùng thử cái này vì cơ chế kép. Khó tin thật, 2 ngày chưa tắm lại mà vẫn không hề có mùi bục ra. Đáng từng xu.",
      initial: "T"
    },
    {
      id: 3,
      name: "P.T.",
      phone: "093441",
      location: "Đà Nẵng*",
      rating: 5,
      content: "Mình ngại nhất khoản đi nhận hàng. Nhưng shop đóng hộp trơn bọc kín bưng, che tên sản phẩm hoàn toàn. Bạn shipper giao đến chỉ bảo 'có gói mỹ phẩm'. 10 điểm cho sự tế nhị và bảo mật thông tin.",
      initial: "P"
    }
  ];

  let showFormModal = $state(false);
  let isLocationOpen = $state(false);
  let newReview = $state({
    name: '',
    location: '',
    rating: 5,
    content: '',
    phone: '',
    isSubmitting: false,
    showSuccess: false
  });

  const isValid = $derived(
    newReview.name.length >= 2 && 
    newReview.phone.length >= 10 && 
    newReview.content.length >= 10 &&
    newReview.location !== ''
  );

  const locations = [
    "Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", 
    "Bình Dương", "Đồng Nai", "Khánh Hòa", "Lâm Đồng", "Quảng Ninh"
  ];

  const setRating = (r: number) => {
    newReview.rating = r;
  };

  const submitReview = async (e: Event) => {
    e.preventDefault();
    if (!isValid || newReview.isSubmitting) return;
    
    newReview.isSubmitting = true;
    await new Promise(r => setTimeout(r, 2000));
    newReview.isSubmitting = false;
    newReview.showSuccess = true;
    
    setTimeout(() => {
      showFormModal = false;
      newReview.showSuccess = false;
      newReview.content = '';
      newReview.phone = '';
      newReview.name = '';
      newReview.location = '';
      newReview.rating = 5;
    }, 2000);
  };
</script>

<section id="reviews" class="reviews-viewport snap-session relative">
  <div class="reviews-container my-auto">
    <div class="mb-16 text-center">
      <h2 class="section-headline mb-8">
        "99.8% Tìm lại sự tự do. <br class="hidden md:block"/> Không còn những khoảng cách ngập ngừng."
      </h2>
      <div class="flex flex-col items-center gap-6">
        <div class="trust-indicator inline-flex items-center gap-6 px-6 py-3 bg-white/5 rounded-full border border-white/10 backdrop-blur-md">
          <div class="flex items-center gap-1.5">
            {#each Array(5) as _, i}
              <svg class="w-5 h-5 {i < 4.9 ? 'text-amber-400' : 'text-white/10'}" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            {/each}
          </div>
          <span class="text-white/60 text-[10px] font-black tracking-[0.2em] uppercase">
            4.9/5 <span class="mx-3 opacity-20">|</span> 2,140+ LƯỢT MUA
          </span>
        </div>
        <button onclick={() => showFormModal = true} class="px-8 py-3 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-[10px] font-black uppercase tracking-[0.2em] hover:bg-emerald-500/20 transition-all active:scale-95 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
          Viết đánh giá của bạn
        </button>
      </div>
    </div>

    <div class="bento-hub-frame relative group">
      <div class="reviews-layout relative" style:z-index="var(--z-surface)">
        <div class="flex items-center justify-between mb-10 px-2">
            <div class="hud-tag primary">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                CORE // VERIFIED_USER_FEEDBACK
            </div>
        </div>

        <div class="reviews-scroll-wrapper">
          {#each reviews as review}
            <div class="review-card">
              <div class="review-header flex items-center justify-between mb-8">
                <div class="flex items-center gap-4">
                  <div class="avatar-circle">{review.initial}</div>
                  <div class="user-meta">
                    <div class="user-name font-bold text-base text-white/90">{review.name} ({review.phone})</div>
                    <div class="user-location text-[9px] text-white/30 uppercase tracking-[0.15em] font-black">{review.location}</div>
                  </div>
                </div>
                <div class="verified-badge">
                  <span class="verified-dot w-1.5 h-1.5 bg-emerald-400 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
                  <span class="text-[8px] font-black text-emerald-400 uppercase tracking-widest">VERIFIED</span>
                </div>
              </div>

              <div class="rating-stars flex gap-1 mb-6">
                {#each Array(review.rating) as _}
                  <svg class="w-3.5 h-3.5 text-emerald-400/80" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                {/each}
              </div>

              <div class="review-content relative">
                <p class="text-slate-300 leading-relaxed text-sm italic font-medium">"{review.content}"</p>
              </div>

              <div class="clinical-verify mt-auto pt-8 flex items-center justify-between opacity-60">
                <div class="compliance-tag flex items-center gap-2">
                  <span class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] leading-none">ELITE_COMPLIANT</span>
                </div>
                <div class="buy-check flex items-center gap-1.5">
                  <svg class="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                  </svg>
                  <span class="text-[9px] font-black text-emerald-400/80 uppercase tracking-widest">Store_Verified</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>
</section>

{#if showFormModal}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="modal-overlay fixed inset-0 flex items-center justify-center p-4 backdrop-blur-3xl"
    style:z-index="var(--z-sticky-header)"
    transition:fade={{ duration: 300 }}
    onclick={(e) => { if(e.target === e.currentTarget) showFormModal = false }}
  >
    <div 
      class="modal-content-frame w-full max-w-[1200px] bg-slate-900/40 border border-white/10 rounded-[3rem] shadow-[0_0_100px_rgba(0,0,0,0.8)] relative"
      transition:fly={{ y: 30, duration: 600, easing: cubicOut }}
    >
      <button 
        onclick={() => showFormModal = false}
        class="absolute top-8 right-8 w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-all active:scale-90"
        style:z-index="var(--z-vui-caption)"
      >
        <svg class="w-5 h-5 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <div class="p-8 md:p-12">
        <div class="form-truth-layout relative">
          {#if newReview.showSuccess}
            <div class="success-overlay absolute inset-0 bg-[#020617]/95 backdrop-blur-2xl flex flex-col items-center justify-center text-center p-8 rounded-[3rem]" style:z-index="var(--z-vui-caption)" transition:fade>
              <div class="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mb-6 border border-emerald-500/30">
                <svg class="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
              </div>
              <h4 class="text-3xl font-black text-white uppercase tracking-tighter mb-4">Gửi thành công</h4>
              <p class="text-white/40 text-sm max-w-xs font-medium uppercase tracking-widest">Hệ thống đã ghi nhận phản hồi của bạn.</p>
            </div>
          {/if}

          <div class="flex items-center justify-between mb-10 pb-6 border-b border-white/5 pr-12 lg:pr-16">
            <div class="hud-tag primary">
              <span class="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse"></span>
              MODULE // REAL_VOICE_ANALYSIS_V2
            </div>
            <div class="text-[9px] font-bold uppercase tracking-[0.2em] text-white/20 font-mono hidden sm:block">SECURE_ENCRYPTION_ACTIVE [AES-256]</div>
          </div>

          <form onsubmit={submitReview} class="space-y-8">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <!-- Left Column: Identity & Context -->
              <div class="space-y-6">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <label class="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] ml-2">Danh tính</label>
                    <input type="text" bind:value={newReview.name} placeholder="Họ và Tên *" class="input-liquid" />
                  </div>
                  <div class="space-y-2">
                    <label class="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] ml-2">Liên hệ</label>
                    <input type="tel" bind:value={newReview.phone} placeholder="Số điện thoại *" class="input-liquid" />
                  </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div class="space-y-2 relative">
                    <label class="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] ml-2">Vị trí</label>
                    <button 
                      type="button"
                      onclick={() => isLocationOpen = !isLocationOpen}
                      class="input-liquid flex items-center justify-between h-[58px] text-left"
                    >
                      <span class={newReview.location ? 'text-white' : 'text-white/20 uppercase text-[11px] font-bold tracking-[0.1em]'}>
                        {newReview.location || 'Chọn Tỉnh/Thành'}
                      </span>
                      <svg class="w-4 h-4 text-white/30 transition-transform {isLocationOpen ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {#if isLocationOpen}
                      <div
                        class="absolute top-[calc(100%+8px)] left-0 w-full bg-[#0f172a]/95 backdrop-blur-2xl border border-white/10 rounded-2xl overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)]"
                        style:z-index="var(--z-vui-caption)"
                        transition:fly={{ y: -10, duration: 200 }}
                      >
                        <div class="max-h-[240px] overflow-y-auto scrollbar-mission">
                          {#each locations as loc}
                            <button 
                              type="button"
                              onclick={() => { newReview.location = loc; isLocationOpen = false; }}
                              class="w-full px-6 py-3.5 text-left text-sm text-white/70 hover:text-white hover:bg-white/5 transition-all border-b border-white/5 last:border-0"
                            >
                              {loc}
                            </button>
                          {/each}
                        </div>
                      </div>
                    {/if}
                  </div>
                  <div class="space-y-2">
                    <label class="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] ml-2">Đánh giá sao</label>
                    <div class="rating-picker flex items-center justify-center gap-3 h-[58px] rounded-2xl">
                      {#each Array(5) as _, i}
                        <button type="button" onclick={() => setRating(i + 1)} class="star-picker-btn transition-all">
                          <svg class="w-6 h-6 {i < newReview.rating ? 'text-amber-400' : 'text-white/5'}" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        </button>
                      {/each}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Right Column: Message -->
              <div class="space-y-2">
                <label class="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] ml-2">Trải nghiệm thực tế</label>
                <div class="relative h-full pb-6">
                  <textarea bind:value={newReview.content} placeholder="Hãy cho chúng tôi biết cảm nhận của bạn... *" class="input-liquid resize-none h-[140px] lg:h-full pr-12 scrollbar-mission"></textarea>
                  <div class="char-counter absolute bottom-10 right-4 opacity-40">{newReview.content.length}/500</div>
                </div>
              </div>
            </div>

            <!-- Bottom: Action Button -->
            <div class="pt-4">
              <button 
                type="submit" 
                disabled={newReview.isSubmitting || !isValid} 
                class="submit-glow-btn w-full py-6 flex items-center justify-center gap-4 group/btn"
              >
                {#if newReview.isSubmitting}
                  <div class="text-xs font-black animate-pulse uppercase tracking-[0.2em]">Đang xử lý dữ liệu...</div>
                {:else}
                  <span class="text-base font-black tracking-[0.3em] uppercase group-hover/btn:scale-105 transition-transform">XÁC NHẬN GỬI ĐÁNH GIÁ</span>
                  <div class="px-3 py-1 bg-white/10 rounded-md text-[8px] font-mono tracking-widest opacity-60">SECURE_GATE // V2.2</div>
                {/if}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
{/if}
