<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import X from "@lucide/svelte/icons/x";
  import Star from "@lucide/svelte/icons/star";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import CheckCircle from "@lucide/svelte/icons/check-circle";
  import Clock from "@lucide/svelte/icons/clock";
  import XCircle from "@lucide/svelte/icons/x-circle";
  import Dices from "@lucide/svelte/icons/dices";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Save from "@lucide/svelte/icons/save";
  import Ban from "@lucide/svelte/icons/ban";

  const nanobot = useNanobot();

  let {
    productId,
    productName,
    isOpen,
    onClose,
  } = $props<{
    productId: string;
    productName: string;
    isOpen: boolean;
    onClose: () => void;
  }>();

  // --- TYPES ---
  interface Review {
    id: string;
    customer_name: string;
    customer_location: string | null;
    rating: number;
    content: string;
    status: string;
    created_at: string;
    attributes: Record<string, unknown> | null;
  }

  // --- STATE ---
  let activeTab = $state<"existing" | "lab">("existing");
  let reviews = $state<Review[]>([]);
  let totalReviews = $state(0);
  let isLoadingReviews = $state(false);
  let isGenerating = $state(false);
  let lastGenerated = $state<Review | null>(null);
  let currentPage = $state(1);
  const PAGE_SIZE = 15;

  // Edit state
  interface EditDraft {
    customer_name: string;
    customer_location: string;
    rating: number;
    content: string;
  }
  let editingId = $state<string | null>(null);
  let editDraft = $state<EditDraft>({ customer_name: "", customer_location: "", rating: 5, content: "" });
  let isSavingEdit = $state(false);

  function openEdit(review: Review) {
    editingId = review.id;
    editDraft = {
      customer_name: review.customer_name,
      customer_location: review.customer_location ?? "",
      rating: review.rating,
      content: review.content,
    };
  }

  function cancelEdit() {
    editingId = null;
  }

  async function saveEdit(id: string) {
    if (!editDraft.content.trim()) {
      nanobot.showToast("Nội dung không được để trống", "error"); return;
    }
    isSavingEdit = true;
    try {
      await apiClient.patch(`/api/v1/reviews/${id}`, {
        customer_name: editDraft.customer_name.trim() || undefined,
        customer_location: editDraft.customer_location.trim() || undefined,
        rating: editDraft.rating,
        content: editDraft.content.trim(),
      });
      nanobot.showToast("✅ Đã lưu thay đổi", "success");
      editingId = null;
      await loadReviews();
    } catch (err) {
      nanobot.showToast("Lưu thất bại: " + (err as Error).message, "error");
    } finally {
      isSavingEdit = false;
    }
  }

  const totalPages = $derived(Math.max(1, Math.ceil(totalReviews / PAGE_SIZE)));

  // Stats
  const avgRating = $derived(
    reviews.length > 0
      ? reviews.reduce((s, r) => s + r.rating, 0) / reviews.length
      : 0
  );
  const ratingBreakdown = $derived(() => {
    const bd: Record<number, number> = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
    for (const r of reviews) {
      if (r.rating >= 1 && r.rating <= 5) bd[r.rating]++;
    }
    return bd;
  });

  // --- LOAD ---
  async function loadReviews() {
    if (!productId) return;
    isLoadingReviews = true;
    try {
      const offset = (currentPage - 1) * PAGE_SIZE;
      const res = await apiClient.get<{ items: Review[]; total: number }>(
        `/api/v1/reviews?entity_type=PRODUCT&entity_id=${productId}&limit=${PAGE_SIZE}&offset=${offset}`
      );
      reviews = res.items ?? [];
      totalReviews = res.total ?? 0;
    } catch (err) {
      nanobot.showToast("Lỗi tải đánh giá: " + (err as Error).message, "error");
    } finally {
      isLoadingReviews = false;
    }
  }

  $effect(() => {
    if (isOpen && productId) {
      currentPage;
      loadReviews();
    }
  });

  $effect(() => {
    if (!isOpen) {
      activeTab = "existing";
      lastGenerated = null;
      editingId = null;
    }
  });

  // --- AI SEED ---
  async function generateOneReview() {
    if (isGenerating) return;
    isGenerating = true;
    lastGenerated = null;
    try {
      const review = await apiClient.post<Review>("/api/v1/reviews/ai-seed", {
        entity_type: "PRODUCT",
        entity_id: productId,
      });
      lastGenerated = review;
      nanobot.showToast("✨ Xohi đã tạo 1 đánh giá mới!", "success");
      // Reload list if on existing tab or update count
      totalReviews += 1;
      if (activeTab === "existing") await loadReviews();
    } catch (err) {
      nanobot.showToast("AI thất bại: " + (err as Error).message, "error");
    } finally {
      isGenerating = false;
    }
  }

  // --- ACTIONS ---
  async function approveReview(id: string) {
    try {
      await apiClient.patch(`/api/v1/reviews/${id}/status`, { status: "APPROVED" });
      nanobot.showToast("Đã duyệt đánh giá", "success");
      await loadReviews();
    } catch {
      nanobot.showToast("Duyệt thất bại", "error");
    }
  }

  async function deleteReview(id: string) {
    try {
      await apiClient.delete(`/api/v1/reviews/${id}`);
      nanobot.showToast("Đã xoá đánh giá", "success");
      totalReviews = Math.max(0, totalReviews - 1);
      await loadReviews();
    } catch {
      nanobot.showToast("Xoá thất bại", "error");
    }
  }

  function formatDate(iso: string) {
    try {
      return new Date(iso).toLocaleDateString("vi-VN", {
        day: "2-digit", month: "2-digit", year: "numeric"
      });
    } catch {
      return iso;
    }
  }

  function getStyleBadge(attrs: Record<string, unknown> | null): string {
    if (!attrs?.style) return "";
    const map: Record<string, string> = {
      tiktok: "TikTok",
      shopee: "Shopee",
      lazada: "Lazada",
      authentic: "Mix",
    };
    return map[attrs.style as string] ?? "";
  }

  const STATUS_MAP: Record<string, { label: string; color: string; icon: typeof CheckCircle }> = {
    APPROVED: { label: "Hiển thị", color: "#39FF14", icon: CheckCircle },
    PENDING:  { label: "Chờ duyệt", color: "#FFB800", icon: Clock },
    REJECTED: { label: "Từ chối",  color: "#FF4444", icon: XCircle },
  };
</script>

{#if isOpen}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-black/80 backdrop-blur-md"
    style="z-index: {Z_INDEX_ADMIN.MODAL_OVERLAY};"
    transition:fade={{ duration: 150 }}
    onclick={onClose}
    role="presentation"
  ></div>

  <!-- Modal -->
  <div
    class="fixed inset-0 flex items-center justify-center p-4 pointer-events-none"
    style="z-index: {Z_INDEX_ADMIN.MODAL};"
    transition:fly={{ y: 20, duration: 200 }}
  >
    <div
      class="review-modal pointer-events-auto w-full max-w-2xl max-h-[85vh] flex flex-col rounded-3xl overflow-hidden border border-white/[0.06] shadow-[0_40px_120px_rgba(0,0,0,0.7)]"
      onclick={(e) => e.stopPropagation()}
      role="dialog"
      aria-modal="true"
      aria-label="Review Lab"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-6 pt-6 pb-4 border-b border-white/[0.05] shrink-0">
        <div class="flex flex-col gap-1">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-xl bg-[#FFB800]/10 border border-[#FFB800]/20 flex items-center justify-center">
              <Star size={14} class="text-[#FFB800]" />
            </div>
            <h2 class="text-[15px] font-black text-white tracking-tight">Xohi Review Lab</h2>
            <span class="px-2 py-0.5 rounded-full bg-[#FFB800]/10 border border-[#FFB800]/20 text-[8px] font-black text-[#FFB800] tracking-widest">
              {totalReviews} REVIEWS
            </span>
          </div>
          <p class="text-[10px] text-white/30 font-mono ml-10 truncate max-w-[320px]">{productName}</p>
        </div>

        <button
          onclick={onClose}
          class="p-2 rounded-xl border border-white/5 text-white/30 hover:text-white hover:border-white/20 transition-all"
          id="review-modal-close"
        >
          <X size={14} />
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 px-6 pt-4 pb-0 shrink-0">
        <button
          onclick={() => activeTab = "existing"}
          id="review-tab-existing"
          class="tab-btn {activeTab === 'existing' ? 'active' : ''}"
        >
          📋 Đánh giá hiện có
          {#if totalReviews > 0}
            <span class="ml-1.5 px-1.5 py-0.5 rounded-full text-[8px] font-black
              {activeTab === 'existing' ? 'bg-[#FFB800]/30 text-[#FFB800]' : 'bg-white/10 text-white/40'}">
              {totalReviews}
            </span>
          {/if}
        </button>
        <button
          onclick={() => { activeTab = "lab"; }}
          id="review-tab-lab"
          class="tab-btn {activeTab === 'lab' ? 'active' : ''}"
        >
          <Sparkles size={11} class="inline-block mr-1" />
          AI Seeding Lab
        </button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-hidden flex flex-col min-h-0">

        {#if activeTab === "existing"}
          <!-- ===== TAB 1: Hiện có ===== -->
          <div class="flex-1 flex flex-col min-h-0">

            <!-- Stats bar -->
            {#if reviews.length > 0}
              <div class="px-6 py-3 flex items-center gap-6 border-b border-white/[0.03] shrink-0">
                <div class="flex items-center gap-1.5">
                  <span class="text-[22px] font-black text-[#FFD700]">{avgRating.toFixed(1)}</span>
                  <div class="flex flex-col gap-0.5">
                    <div class="flex items-center gap-0.5">
                      {#each [1,2,3,4,5] as s}
                        <Star size={9} class="{s <= Math.round(avgRating) ? 'text-[#FFD700]' : 'text-white/10'}" fill="{s <= Math.round(avgRating) ? '#FFD700' : 'transparent'}" />
                      {/each}
                    </div>
                    <span class="text-[8px] text-white/30 font-mono">{totalReviews} đánh giá</span>
                  </div>
                </div>
                <!-- Rating bars -->
                <div class="flex-1 flex flex-col gap-0.5">
                  {#each [5,4,3,2,1] as star}
                    {@const count = ratingBreakdown()[star] ?? 0}
                    {@const pct = totalReviews > 0 ? (count / reviews.length) * 100 : 0}
                    <div class="flex items-center gap-1.5">
                      <span class="text-[7px] font-mono text-white/30 w-2">{star}</span>
                      <div class="flex-1 h-1 rounded-full bg-white/5 overflow-hidden">
                        <div class="h-full rounded-full bg-[#FFD700]/60 transition-all duration-500" style="width: {pct}%"></div>
                      </div>
                      <span class="text-[7px] font-mono text-white/20 w-3 text-right">{count}</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            <!-- List -->
            <div class="flex-1 overflow-y-auto custom-scrollbar px-6 py-4 flex flex-col gap-2">
              {#if isLoadingReviews}
                <div class="flex items-center justify-center h-32">
                  <RefreshCw size={16} class="animate-spin text-[#FFB800]/50" />
                </div>
              {:else if reviews.length === 0}
                <div class="flex flex-col items-center justify-center h-40 gap-3">
                  <Star size={32} class="text-white/10" />
                  <p class="text-[11px] text-white/20 font-mono">Chưa có đánh giá nào</p>
                  <button
                    onclick={() => activeTab = "lab"}
                    class="px-4 py-2 rounded-xl bg-[#FFB800]/10 border border-[#FFB800]/20 text-[10px] font-black text-[#FFB800] hover:bg-[#FFB800]/20 transition-all"
                  >
                    → Đi đến AI Lab để tạo ngay
                  </button>
                </div>
              {:else}
                {#each reviews as review (review.id)}
                  {@const statusInfo = STATUS_MAP[review.status] ?? STATUS_MAP["PENDING"]}
                  {@const isEditing = editingId === review.id}
                  <div
                    class="review-card flex flex-col gap-2 p-3.5 rounded-2xl border transition-all duration-200
                      {isEditing
                        ? 'border-[#FFB800]/30 bg-[#FFB800]/[0.03]'
                        : 'border-white/[0.04] hover:border-white/[0.08] bg-white/[0.02]'}"
                    transition:fade={{ duration: 120 }}
                  >
                    {#if isEditing}
                      <!-- ===== INLINE EDIT FORM ===== -->
                      <div class="flex flex-col gap-3" transition:fly={{ y: -4, duration: 150 }}>
                        <!-- Edit header -->
                        <div class="flex items-center gap-2 text-[9px] font-black text-[#FFB800] tracking-widest">
                          <Pencil size={10} />
                          ĐANG CHỈNH SỬA
                        </div>

                        <!-- Name + Location row -->
                        <div class="grid grid-cols-2 gap-2">
                          <div class="flex flex-col gap-1">
                            <label class="text-[8px] font-black text-white/30 tracking-widest">TÊN KHÁCH</label>
                            <input
                              type="text"
                              bind:value={editDraft.customer_name}
                              class="edit-input text-[11px]"
                              placeholder="Tên khách hàng"
                            />
                          </div>
                          <div class="flex flex-col gap-1">
                            <label class="text-[8px] font-black text-white/30 tracking-widest">ĐỊA ĐIỂM</label>
                            <input
                              type="text"
                              bind:value={editDraft.customer_location}
                              class="edit-input text-[11px]"
                              placeholder="TP.HCM, Hà Nội..."
                            />
                          </div>
                        </div>

                        <!-- Rating stars clickable -->
                        <div class="flex flex-col gap-1">
                          <label class="text-[8px] font-black text-white/30 tracking-widest">SỐ SAO</label>
                          <div class="flex items-center gap-1">
                            {#each [1,2,3,4,5] as s}
                              <button
                                onclick={() => editDraft.rating = s}
                                class="transition-transform hover:scale-125 active:scale-95"
                                title="{s} sao"
                              >
                                <Star
                                  size={18}
                                  class="{s <= editDraft.rating ? 'text-[#FFD700]' : 'text-white/10'} transition-colors"
                                  fill="{s <= editDraft.rating ? '#FFD700' : 'transparent'}"
                                />
                              </button>
                            {/each}
                            <span class="text-[10px] font-mono text-white/30 ml-2">{editDraft.rating}/5</span>
                          </div>
                        </div>

                        <!-- Content textarea -->
                        <div class="flex flex-col gap-1">
                          <label class="text-[8px] font-black text-white/30 tracking-widest">NỘI DUNG ĐÁNH GIÁ</label>
                          <textarea
                            bind:value={editDraft.content}
                            rows={3}
                            class="edit-input text-[12px] resize-none leading-relaxed"
                            placeholder="Nhập nội dung đánh giá..."
                          ></textarea>
                          <span class="text-[8px] text-white/20 text-right font-mono">{editDraft.content.length}/200</span>
                        </div>

                        <!-- Action buttons -->
                        <div class="flex items-center gap-2 justify-end">
                          <button
                            onclick={cancelEdit}
                            class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-white/10 text-[10px] font-black text-white/40 hover:text-white hover:border-white/30 transition-all"
                          >
                            <Ban size={11} />
                            Huỷ
                          </button>
                          <button
                            onclick={() => saveEdit(review.id)}
                            disabled={isSavingEdit}
                            class="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-[#FFB800]/15 border border-[#FFB800]/30 text-[10px] font-black text-[#FFB800] hover:bg-[#FFB800]/25 disabled:opacity-50 transition-all"
                          >
                            {#if isSavingEdit}
                              <RefreshCw size={11} class="animate-spin" />
                              Đang lưu...
                            {:else}
                              <Save size={11} />
                              Lưu thay đổi
                            {/if}
                          </button>
                        </div>
                      </div>

                    {:else}
                      <!-- ===== VIEW MODE ===== -->
                      <div class="flex items-start justify-between gap-2">
                        <div class="flex flex-col gap-0.5 min-w-0">
                          <div class="flex items-center gap-2 flex-wrap">
                            <span class="text-[12px] font-bold text-white/90">{review.customer_name}</span>
                            {#if review.customer_location}
                              <span class="flex items-center gap-1 text-[9px] text-white/30">
                                <MapPin size={8} />
                                {review.customer_location}
                              </span>
                            {/if}
                            {#if review.attributes?.ai_seeded}
                              {@const style = getStyleBadge(review.attributes)}
                              <span class="px-1.5 py-0.5 rounded-md bg-[#FFB800]/10 border border-[#FFB800]/20 text-[7px] font-black text-[#FFB800]">
                                🤖 {style}
                              </span>
                            {/if}
                          </div>
                          <!-- Stars -->
                          <div class="flex items-center gap-0.5">
                            {#each [1,2,3,4,5] as s}
                              <Star size={9} class="{s <= review.rating ? 'text-[#FFD700]' : 'text-white/10'}" fill="{s <= review.rating ? '#FFD700' : 'transparent'}" />
                            {/each}
                            <span class="text-[8px] text-white/20 ml-1 font-mono">{formatDate(review.created_at)}</span>
                          </div>
                        </div>
                        <!-- Status + Actions -->
                        <div class="flex items-center gap-1.5 shrink-0">
                          <span
                            class="px-2 py-1 rounded-lg text-[8px] font-black font-mono tracking-wider flex items-center gap-1"
                            style:color={statusInfo.color}
                            style:border="1px solid {statusInfo.color}30"
                            style:background="{statusInfo.color}12"
                          >
                            {statusInfo.label}
                          </span>
                          {#if review.status === "PENDING"}
                            <button
                              onclick={() => approveReview(review.id)}
                              class="p-1.5 rounded-lg bg-[#39FF14]/5 border border-[#39FF14]/20 text-[#39FF14]/60 hover:text-[#39FF14] hover:border-[#39FF14]/50 transition-all"
                              title="Duyệt"
                            >
                              <CheckCircle size={12} />
                            </button>
                          {/if}
                          <button
                            onclick={() => openEdit(review)}
                            class="p-1.5 rounded-lg bg-[#FFB800]/5 border border-[#FFB800]/10 text-[#FFB800]/50 hover:text-[#FFB800] hover:border-[#FFB800]/40 transition-all"
                            title="Sửa nội dung"
                          >
                            <Pencil size={12} />
                          </button>
                          <button
                            onclick={() => deleteReview(review.id)}
                            class="p-1.5 rounded-lg bg-red-500/5 border border-red-500/10 text-red-500/40 hover:text-red-400 hover:border-red-500/30 transition-all"
                            title="Xoá"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                      <p class="text-[12px] text-white/60 leading-relaxed">{review.content}</p>
                    {/if}
                  </div>
                {/each}
              {/if}
            </div>

            <!-- Pagination -->
            {#if totalPages > 1}
              <div class="flex items-center justify-center gap-2 px-6 py-3 border-t border-white/[0.03] shrink-0">
                <button
                  onclick={() => { currentPage = Math.max(1, currentPage - 1); }}
                  disabled={currentPage <= 1}
                  class="px-3 py-1.5 rounded-lg border border-white/5 text-[10px] text-white/40 hover:text-white hover:border-white/20 disabled:opacity-30 transition-all"
                >←</button>
                <span class="text-[10px] font-mono text-white/30">{currentPage} / {totalPages}</span>
                <button
                  onclick={() => { currentPage = Math.min(totalPages, currentPage + 1); }}
                  disabled={currentPage >= totalPages}
                  class="px-3 py-1.5 rounded-lg border border-white/5 text-[10px] text-white/40 hover:text-white hover:border-white/20 disabled:opacity-30 transition-all"
                >→</button>
              </div>
            {/if}
          </div>

        {:else}
          <!-- ===== TAB 2: AI Lab ===== -->
          <div class="flex-1 flex flex-col items-center justify-start px-8 py-8 gap-6 overflow-y-auto custom-scrollbar">

            <!-- Lab panel -->
            <div class="w-full max-w-md flex flex-col items-center gap-6">
              <!-- Orb icon -->
              <div class="relative">
                <div class="w-20 h-20 rounded-3xl bg-gradient-to-br from-[#FFB800]/20 to-[#FF6B00]/10 border border-[#FFB800]/20 flex items-center justify-center shadow-[0_0_40px_rgba(255,184,0,0.15)]">
                  <Sparkles size={32} class="text-[#FFB800]" />
                </div>
                <div class="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#FFB800] flex items-center justify-center">
                  <Dices size={10} class="text-black" />
                </div>
              </div>

              <div class="text-center flex flex-col gap-1">
                <h3 class="text-[16px] font-black text-white">Xohi Review Lab</h3>
                <p class="text-[11px] text-white/40 leading-relaxed">
                  Mỗi lần bấm tạo <strong class="text-[#FFB800]">1 đánh giá</strong> chân thực<br/>
                  Phong cách được chọn ngẫu nhiên mỗi lần
                </p>
              </div>

              <!-- Style badges -->
              <div class="flex items-center gap-2 flex-wrap justify-center">
                {#each [["TikTok", "#FF0050"], ["Shopee", "#EE4D2D"], ["Lazada", "#0F146D"], ["Mix", "#39FF14"]] as [label, color]}
                  <span
                    class="px-2.5 py-1 rounded-full text-[9px] font-black tracking-wider border"
                    style:color={color}
                    style:border-color="{color}40"
                    style:background="{color}10"
                  >{label}</span>
                {/each}
                <span class="text-[9px] text-white/20">← ngẫu nhiên</span>
              </div>

              <!-- CTA Button -->
              <button
                onclick={generateOneReview}
                disabled={isGenerating}
                id="review-lab-generate-btn"
                class="generate-btn w-full py-4 rounded-2xl font-black text-[14px] tracking-wider flex items-center justify-center gap-3 transition-all duration-300
                  {isGenerating ? 'opacity-70 cursor-not-allowed' : 'hover:scale-[1.02] active:scale-95'}"
              >
                {#if isGenerating}
                  <RefreshCw size={18} class="animate-spin" />
                  Xohi đang viết đánh giá...
                {:else}
                  <Dices size={18} />
                  Tạo 1 Đánh Giá Ngẫu Nhiên
                {/if}
              </button>

              <!-- Last generated preview -->
              {#if lastGenerated}
                <div
                  class="w-full p-4 rounded-2xl bg-[#39FF14]/[0.03] border border-[#39FF14]/20 flex flex-col gap-2"
                  transition:fly={{ y: 10, duration: 250 }}
                >
                  <div class="flex items-center gap-2 text-[9px] font-black text-[#39FF14] tracking-widest">
                    <CheckCircle size={11} />
                    VỪA TẠO XONG
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-[11px] font-bold text-white/70">{lastGenerated.customer_name}</span>
                    {#if lastGenerated.customer_location}
                      <span class="text-[9px] text-white/30">{lastGenerated.customer_location}</span>
                    {/if}
                    <div class="flex items-center gap-0.5 ml-auto">
                      {#each [1,2,3,4,5] as s}
                        <Star size={9} class="{s <= lastGenerated.rating ? 'text-[#FFD700]' : 'text-white/10'}" fill="{s <= lastGenerated.rating ? '#FFD700' : 'transparent'}" />
                      {/each}
                    </div>
                  </div>
                  <p class="text-[12px] text-white/60 italic">"{lastGenerated.content}"</p>
                  {#if lastGenerated.attributes?.style}
                    <span class="text-[8px] text-[#FFB800]/50 font-mono">style: {lastGenerated.attributes.style}</span>
                  {/if}
                </div>
              {/if}

              <!-- Hint -->
              <p class="text-[9px] text-white/20 text-center leading-relaxed">
                Nhấn nhiều lần để tích lũy đánh giá đa dạng.<br/>
                Review được tạo với trạng thái <span class="text-[#39FF14]/60">APPROVED</span> ngay lập tức.
              </p>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .review-modal {
    background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
  }

  .tab-btn {
    padding: 8px 16px;
    border-radius: 12px 12px 0 0;
    font-size: 10px;
    font-weight: 900;
    font-family: monospace;
    letter-spacing: 0.05em;
    color: rgba(255,255,255,0.3);
    border: 1px solid transparent;
    border-bottom: none;
    transition: all 0.2s;
    cursor: pointer;
    background: transparent;
    display: flex;
    align-items: center;
  }

  .tab-btn:hover {
    color: rgba(255,255,255,0.6);
  }

  .tab-btn.active {
    color: #FFB800;
    background: rgba(255,184,0,0.05);
    border-color: rgba(255,184,0,0.15);
    border-bottom-color: #050505;
  }

  .generate-btn {
    background: linear-gradient(135deg, rgba(255,184,0,0.15) 0%, rgba(255,107,0,0.08) 100%);
    border: 1px solid rgba(255,184,0,0.3);
    color: #FFB800;
    box-shadow: 0 0 30px rgba(255,184,0,0.1), inset 0 1px 0 rgba(255,255,255,0.05);
  }

  .generate-btn:not(:disabled):hover {
    background: linear-gradient(135deg, rgba(255,184,0,0.22) 0%, rgba(255,107,0,0.12) 100%);
    border-color: rgba(255,184,0,0.5);
    box-shadow: 0 0 50px rgba(255,184,0,0.2), inset 0 1px 0 rgba(255,255,255,0.08);
  }

  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 20px; }

  .edit-input {
    width: 100%;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 184, 0, 0.2);
    border-radius: 10px;
    padding: 8px 10px;
    color: rgba(255, 255, 255, 0.85);
    font-family: inherit;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .edit-input:focus {
    border-color: rgba(255, 184, 0, 0.5);
    box-shadow: 0 0 0 3px rgba(255, 184, 0, 0.06);
  }

  .edit-input::placeholder {
    color: rgba(255, 255, 255, 0.15);
  }
</style>
