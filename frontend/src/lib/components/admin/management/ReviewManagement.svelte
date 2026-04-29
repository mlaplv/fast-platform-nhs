<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import { untrack } from "svelte";
  import Star from "lucide-svelte/icons/star";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import XCircle from "lucide-svelte/icons/x-circle";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import MessageSquare from "lucide-svelte/icons/message-square";
  import Edit2 from "lucide-svelte/icons/edit-2";
  import ThumbsUp from "lucide-svelte/icons/thumbs-up";
  import Layers from "lucide-svelte/icons/layers";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import LayoutGrid from "lucide-svelte/icons/layout-grid";
  import List from "lucide-svelte/icons/list";
  import X from "lucide-svelte/icons/x";
  import Play from "lucide-svelte/icons/play";
  import NeuralEditor from "$lib/components/admin/ui/tiptap/NeuralEditor.svelte";
  import type { BaseWidgetProps } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";

  let { data = {} } = $props<BaseWidgetProps>();

  interface Review {
    id: string;
    entity_type: string;
    entity_id: string;
    customer_name: string;
    customer_phone?: string;
    customer_location?: string;
    rating: number;
    content: string;
    status: string;
    created_at: string;
    likes_count?: number;
    attachments?: {url: string, type: string}[];
  }

  let reviews = $state<Review[]>([]);
  let totalReviews = $state(0);
  let isLoading = $state(true);

  let activeFilter = $state("all"); // PENDING, APPROVED, REJECTED
  let activeCategory = $state("all"); // PRODUCT, CATEGORY, NEWS
  let viewMode = $state<"grid" | "list">("grid");
  
  let currentPage = $state(1);
  let pageSize = $state(20);

  let selectedIds = $state<string[]>([]);

  let editingReviewId = $state<string | null>(null);
  let editContent = $state("");
  let editAttachments = $state<{url: string, type: string}[]>([]);

  function startEdit(review: Review) {
    editingReviewId = review.id;
    editContent = review.content;
    editAttachments = Array.isArray(review.attachments) ? JSON.parse(JSON.stringify(review.attachments)) : [];
  }

  function cancelEdit() {
    editingReviewId = null;
    editContent = "";
    editAttachments = [];
  }

  async function saveEdit(id: string) {
    isLoading = true;
    try {
      await apiClient.patch(`/api/v1/reviews/${id}/content`, { 
        content: editContent,
        attachments: editAttachments
      });
      nanobot.showToast("Đã cập nhật nội dung đánh giá", "success");
      cancelEdit();
      await loadReviews();
    } catch (e: unknown) {
      nanobot.showToast("Lỗi khi cập nhật đánh giá", "error");
    } finally {
      isLoading = false;
    }
  }

  async function loadReviews() {
    isLoading = true;
    try {
      const offset = (currentPage - 1) * pageSize;
      const params = new URLSearchParams({
        limit: pageSize.toString(),
        offset: offset.toString()
      });
      if (activeFilter !== "all") params.append("status", activeFilter.toUpperCase());
      if (activeCategory !== "all") params.append("entity_type", activeCategory.toUpperCase());

      const res = await apiClient.get<{ items: Review[]; total: number }>(`/api/v1/reviews?${params.toString()}`);
      reviews = res.items || [];
      totalReviews = res.total || 0;
    } catch (e: unknown) {
      const err = e as Error;
      nanobot.showToast("Lỗi tải đánh giá: " + err.message, "error");
    } finally {
      isLoading = false;
    }
  }

  $effect(() => {
    loadReviews();
  });

  $effect(() => {
    if (activeFilter || activeCategory) {
      untrack(() => { currentPage = 1; });
    }
  });

  async function handleUpdateStatus(id: string, newStatus: string) {
    isLoading = true;
    try {
      await apiClient.patch(`/api/v1/reviews/${id}/status`, { status: newStatus });
      nanobot.showToast(`Đã duyệt đánh giá thành ${newStatus}`, "success");
      await loadReviews();
    } catch (e: unknown) {
      const err = e as Error;
      nanobot.showToast("Lỗi cập nhật đánh giá", "error");
    } finally {
      isLoading = false;
    }
  }

  async function handleDelete(id: string) {
    const confirm = await nanobot.showConfirm({
      title: "XÁC NHẬN XOÁ",
      message: "Bạn có chắc chắn muốn xoá đánh giá này vĩnh viễn?",
      confirmLabel: "XOÁ NGAY",
      cancelLabel: "HUỶ"
    });
    if (!confirm) return;

    isLoading = true;
    try {
      await apiClient.delete(`/api/v1/reviews/${id}`);
      nanobot.showToast("Đã xoá đánh giá", "success");
      await loadReviews();
    } catch (e: unknown) {
      const err = e as Error;
      nanobot.showToast("Lỗi khi xoá: " + err.message, "error");
    } finally {
      isLoading = false;
    }
  }

  // Bulk Actions logic
  function toggleSelect(id: string) {
    if (selectedIds.includes(id)) {
      selectedIds = selectedIds.filter(i => i !== id);
    } else {
      selectedIds = [...selectedIds, id];
    }
  }

  function toggleSelectAll() {
    if (selectedIds.length === reviews.length && reviews.length > 0) {
      selectedIds = [];
    } else {
      selectedIds = reviews.map(r => r.id);
    }
  }

  async function handleBulkAction(action: "APPROVE" | "REJECT" | "DELETE") {
    const count = selectedIds.length;
    const confirm = await nanobot.showConfirm({
      title: "THAO TÁC HÀNG LOẠT",
      message: `Thực hiện tác vụ ${action} cho ${count} đánh giá đã chọn?`,
      confirmLabel: "XÁC NHẬN",
      cancelLabel: "HUỶ"
    });
    if (!confirm) return;

    isLoading = true;
    try {
      for (const id of selectedIds) {
        if (action === "DELETE") {
          await apiClient.delete(`/api/v1/reviews/${id}`);
        } else {
          await apiClient.patch(`/api/v1/reviews/${id}/status`, { status: action === "APPROVE" ? "APPROVED" : "REJECTED" });
        }
      }
      nanobot.showToast(`Đã xử lý ${count} mục thành công`, "success");
      selectedIds = [];
      await loadReviews();
    } catch (e: unknown) {
      const err = e as Error;
      nanobot.showToast("Lỗi thao tác hàng loạt", "error");
    } finally {
      isLoading = false;
    }
  }

  function formatDate(iso: string) {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("vi-VN", {
      hour: "2-digit", minute: "2-digit",
      day: "2-digit", month: "2-digit", year: "numeric"
    });
  }

  function getStatusStyle(status: string) {
    if (status === "APPROVED") return "bg-green-500/20 text-green-400 border-green-500/30";
    if (status === "REJECTED") return "bg-red-500/20 text-red-400 border-red-500/30";
    return "bg-amber-500/20 text-amber-400 border-amber-500/30";
  }

</script>

<div class="w-full h-full flex flex-col relative bg-[#050505]">
  <!-- Header / Filters -->
  <div class="p-4 sm:p-6 border-b border-white/5 flex flex-col gap-6">
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full border border-neon-cyan/20 bg-neon-cyan/5 flex items-center justify-center">
          <Star class="text-neon-cyan" size={20} />
        </div>
        <div>
          <h2 class="text-white font-bold tracking-widest uppercase text-sm">Quản Trị Đánh Giá</h2>
          <p class="text-[10px] text-gray-500 font-mono tracking-widest uppercase">{totalReviews} BLOCKS FOUND</p>
        </div>
      </div>
      
      <div class="flex items-center gap-4">
        <!-- View Mode Toggle -->
        <div class="flex items-center bg-white/[0.02] border border-white/5 p-1 rounded">
          <button 
            onclick={() => viewMode = 'grid'}
            class="p-1.5 transition-all {viewMode === 'grid' ? 'bg-neon-cyan/20 text-neon-cyan' : 'text-gray-500 hover:text-gray-300'}"
            title="Chế độ Ô"
          >
            <LayoutGrid size={14} />
          </button>
          <button 
            onclick={() => viewMode = 'list'}
            class="p-1.5 transition-all {viewMode === 'list' ? 'bg-neon-cyan/20 text-neon-cyan' : 'text-gray-500 hover:text-gray-300'}"
            title="Chế độ Danh sách"
          >
            <List size={14} />
          </button>
        </div>

        <button onclick={loadReviews} class="p-2 hover:bg-white/5 rounded-full transition-colors text-gray-500 hover:text-neon-cyan" title="Làm mới">
          <RefreshCw size={16} class={isLoading ? 'animate-spin' : ''} />
        </button>
      </div>
    </div>

    <div class="flex flex-wrap gap-6 items-center">
      <!-- Status Filter -->
      <div class="flex flex-col gap-2">
        <span class="text-[8px] font-mono text-gray-500 uppercase tracking-widest">Trạng thái</span>
        <div class="flex items-center bg-white/[0.02] border border-white/5 p-1 rounded">
          {#each ["all", "pending", "approved", "rejected"] as f}
            <button
              onclick={() => activeFilter = f}
              class="px-3 py-1 text-[9px] font-mono tracking-widest uppercase transition-all {activeFilter === f ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/20' : 'text-gray-500 hover:text-gray-300'}"
            >
              {f}
            </button>
          {/each}
        </div>
      </div>

      <!-- Entity Type Filter -->
      <div class="flex flex-col gap-2">
        <span class="text-[8px] font-mono text-gray-500 uppercase tracking-widest">Danh mục</span>
        <div class="flex items-center bg-white/[0.02] border border-white/5 p-1 rounded">
          {#each ["all", "product", "category", "news"] as c}
            <button
              onclick={() => activeCategory = c}
              class="px-3 py-1 text-[9px] font-mono tracking-widest uppercase transition-all {activeCategory === c ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' : 'text-gray-500 hover:text-gray-300'}"
            >
              {c}
            </button>
          {/each}
        </div>
      </div>

      <!-- Select All Toggle -->
      <div class="ml-auto mt-4 sm:mt-0">
        <button 
          onclick={toggleSelectAll}
          class="flex items-center gap-2 px-3 py-1.5 border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all text-[10px] font-mono uppercase tracking-widest text-gray-400"
        >
          <Layers size={14} class={selectedIds.length === reviews.length && reviews.length > 0 ? 'text-neon-cyan' : ''} />
          {selectedIds.length === reviews.length && reviews.length > 0 ? 'Bỏ chọn tất cả' : 'Chọn tất cả trên trang'}
        </button>
      </div>
    </div>
  </div>

  <!-- Content Area -->
  <div class="flex-1 overflow-y-auto p-4 sm:p-6 pb-32 custom-scrollbar">
    {#if isLoading && reviews.length === 0}
       <div class="h-full flex flex-col gap-3 items-center justify-center text-neon-cyan/50 font-mono text-[10px] tracking-[0.3em] uppercase animate-pulse">
         <div class="w-10 h-10 border-2 border-neon-cyan/20 border-t-neon-cyan rounded-full animate-spin"></div>
         SYNCING_DATABANKS...
       </div>
    {:else if reviews.length === 0}
       <div class="h-full flex flex-col items-center justify-center text-gray-500 gap-3">
         <div class="w-12 h-12 rounded-full border border-white/5 bg-white/[0.02] flex items-center justify-center">
           <MessageSquare size={20} class="opacity-30" />
         </div>
         <p class="font-mono text-[10px] tracking-[0.2em] uppercase">NO_REVIEWS_FOUND</p>
       </div>
    {:else}
      {#if viewMode === 'grid'}
        <!-- Grid View -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" in:fade>
          {#each reviews as review (review.id)}
            <label class="relative group cursor-pointer block">
              <input 
                type="checkbox" 
                class="hidden" 
                checked={selectedIds.includes(review.id)}
                onchange={() => toggleSelect(review.id)}
              />
              
              <div class="flex flex-col h-full bg-[#0a0a0a] border {selectedIds.includes(review.id) ? 'border-neon-cyan shadow-[0_0_15px_rgba(0,255,255,0.1)]' : 'border-white/5'} hover:border-neon-cyan/30 p-5 transition-all">
                
                {#if selectedIds.includes(review.id)}
                  <div class="absolute -top-1.5 -right-1.5 w-4 h-4 bg-neon-cyan flex items-center justify-center rounded-full text-black shadow-[0_0_10px_rgba(0,255,255,0.5)] z-20">
                    <CheckCircle size={10} />
                  </div>
                {/if}

                <div class="flex justify-between items-start mb-4">
                  <div>
                    <h3 class="text-gray-200 text-sm font-bold tracking-wide">{review.customer_name}</h3>
                    <div class="flex items-center gap-2 mt-1.5">
                      <span class="text-[9px] font-mono tracking-[0.2em] text-[#FFB800] bg-[#FFB800]/5 px-1.5 py-0.5 border border-[#FFB800]/20 uppercase">
                        {review.entity_type}
                      </span>
                      <span class="text-[9px] text-gray-600 font-mono tracking-wider">{formatDate(review.created_at)}</span>
                    </div>
                  </div>
                  <div class="flex items-center text-[#FFB800] gap-0.5">
                    {#each Array(5) as _, i}
                      <Star size={12} class={i < review.rating ? "fill-[#FFB800]" : "text-white/10"} />
                    {/each}
                  </div>
                </div>

                <div class="text-xs text-gray-400 leading-relaxed mb-5 italic border-l-2 border-white/10 pl-3 min-h-[40px] line-clamp-3 content-prose-admin">
                  {@html review.content}
                </div>
                
                <!-- Media Preview in Grid (Read-only) -->
                {#if review.attachments && review.attachments.length > 0}
                  <div class="flex gap-2 mb-4 overflow-hidden h-12">
                    {#each review.attachments as media}
                      <div class="w-12 h-12 relative bg-white/5 shrink-0 border border-white/10">
                        {#if media.type === 'video' || media.url.match(/\.(mp4|webm|mov)$/i) || media.url.includes('video')}
                          <video src={media.url} class="w-full h-full object-cover" muted playsinline></video>
                          <div class="absolute inset-0 bg-black/20 flex items-center justify-center">
                            <Play class="w-3 h-3 text-white fill-current opacity-80" />
                          </div>
                        {:else}
                          <img src={media.url} class="w-full h-full object-cover" alt="" />
                        {/if}
                      </div>
                    {/each}
                  </div>
                {/if}
                
                <div class="mt-auto flex justify-between items-center border-t border-white/5 pt-4">
                  <div class="flex items-center gap-3">
                    <div class="flex items-center gap-1 text-neon-cyan/60 font-mono text-[9px]">
                      <ThumbsUp size={10} class="fill-neon-cyan/20" />
                      <span>{review.likes_count || 0}</span>
                    </div>
                    <span class="text-[9px] font-mono tracking-[0.2em] uppercase px-2 py-0.5 border rounded-sm {getStatusStyle(review.status)}">
                      {review.status}
                    </span>
                  </div>
                  <div class="flex gap-2" onclick={(e) => e.stopPropagation()}>
                    <div class="flex flex-col items-end">
                      {#if review.customer_location}
                        <span class="text-[8px] text-gray-500 font-mono uppercase tracking-widest mb-1">{review.customer_location}</span>
                      {/if}
                      <div class="flex gap-2">
                        <button onclick={() => startEdit(review)} class="w-7 h-7 rounded bg-white/[0.02] border border-white/5 hover:bg-blue-500/20 hover:border-blue-500/30 flex items-center justify-center text-gray-500 hover:text-blue-400 transition-colors" title="Chỉnh sửa">
                          <Edit2 size={14} />
                        </button>
                        {#if review.status !== 'APPROVED'}
                          <button onclick={() => handleUpdateStatus(review.id, 'APPROVED')} class="w-7 h-7 rounded bg-white/[0.02] border border-white/5 hover:bg-green-500/20 hover:border-green-500/30 flex items-center justify-center text-gray-500 hover:text-green-400 transition-colors" title="Chấp thuận">
                            <CheckCircle size={14} />
                          </button>
                        {/if}
                        {#if review.status !== 'REJECTED'}
                          <button onclick={() => handleUpdateStatus(review.id, 'REJECTED')} class="w-7 h-7 rounded bg-white/[0.02] border border-white/5 hover:bg-red-500/20 hover:border-red-500/30 flex items-center justify-center text-gray-500 hover:text-red-400 transition-colors" title="Từ chối">
                            <XCircle size={14} />
                          </button>
                        {/if}
                        <button onclick={() => handleDelete(review.id)} class="w-7 h-7 rounded bg-white/[0.02] border border-white/5 hover:bg-red-600/20 hover:border-red-600/30 flex items-center justify-center text-gray-500 hover:text-red-500 transition-colors" title="Xoá vĩnh viễn">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </label>
          {/each}
        </div>
      {:else}
        <!-- List View (Table) -->
        <div class="w-full border border-white/5 bg-[#0a0a0a]/50" in:fade>
          <table class="w-full border-collapse">
            <thead>
              <tr class="border-b border-white/5 bg-white/[0.02]">
                <th class="w-10 p-4"></th>
                <th class="text-[10px] font-mono text-gray-500 uppercase tracking-widest text-left p-4">Khách hàng</th>
                <th class="text-[10px] font-mono text-gray-500 uppercase tracking-widest text-left p-4">Danh mục</th>
                <th class="text-[10px] font-mono text-gray-500 uppercase tracking-widest text-left p-4">Đánh giá</th>
                <th class="text-[10px] font-mono text-gray-500 uppercase tracking-widest text-left p-4">Nội dung</th>
                <th class="text-[10px] font-mono text-gray-500 uppercase tracking-widest text-left p-4">Trạng thái</th>
                <th class="text-[10px] font-mono text-gray-500 uppercase tracking-widest text-right p-4">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {#each reviews as review (review.id)}
                <tr class="border-b border-white/5 hover:bg-white/[0.02] transition-colors {selectedIds.includes(review.id) ? 'bg-neon-cyan/5' : ''}">
                  <td class="p-4">
                    <input 
                      type="checkbox" 
                      class="w-4 h-4 rounded border-white/10 bg-transparent text-neon-cyan focus:ring-0 cursor-pointer"
                      checked={selectedIds.includes(review.id)}
                      onchange={() => toggleSelect(review.id)}
                    />
                  </td>
                  <td class="p-4">
                    <div class="flex flex-col">
                      <span class="text-xs font-bold text-gray-200">{review.customer_name}</span>
                      <span class="text-[9px] text-gray-500 font-mono italic">{review.customer_location || 'Việt Nam'}</span>
                      <span class="text-[9px] text-gray-600 font-mono mt-1">{formatDate(review.created_at)}</span>
                    </div>
                  </td>
                  <td class="p-4">
                    <span class="text-[9px] font-mono tracking-[0.2em] text-[#FFB800] bg-[#FFB800]/5 px-1.5 py-0.5 border border-[#FFB800]/20 uppercase">
                      {review.entity_type}
                    </span>
                  </td>
                  <td class="p-4">
                    <div class="flex items-center text-[#FFB800] gap-0.5">
                      {#each Array(5) as _, i}
                        <Star size={10} class={i < review.rating ? "fill-[#FFB800]" : "text-white/10"} />
                      {/each}
                    </div>
                  </td>
                  <td class="p-4 max-w-[400px] flex-col gap-2">
                    <div class="text-[11px] text-gray-400 line-clamp-2 content-prose-admin" title="Nội dung">
                      {@html review.content}
                    </div>
                    {#if review.attachments && review.attachments.length > 0}
                      <div class="flex gap-1.5 overflow-hidden h-8 mt-2">
                        {#each review.attachments as media}
                          <div class="w-8 h-8 relative bg-white/5 shrink-0 border border-white/10">
                            {#if media.type === 'video' || media.url.match(/\.(mp4|webm|mov)$/i) || media.url.includes('video')}
                              <video src={media.url} class="w-full h-full object-cover" muted playsinline></video>
                              <div class="absolute inset-0 bg-black/20 flex items-center justify-center">
                                <Play class="w-2 h-2 text-white fill-current opacity-80" />
                              </div>
                            {:else}
                              <img src={media.url} class="w-full h-full object-cover" alt="" />
                            {/if}
                          </div>
                        {/each}
                      </div>
                    {/if}
                  </td>
                  <td class="p-4">
                    <div class="flex flex-col gap-1">
                      <span class="text-[9px] font-mono tracking-[0.2em] uppercase px-2 py-0.5 border rounded-sm {getStatusStyle(review.status)}">
                        {review.status}
                      </span>
                      <div class="flex items-center gap-1 text-neon-cyan/50 font-mono text-[8px] justify-center">
                        <ThumbsUp size={8} /> {review.likes_count || 0}
                      </div>
                    </div>
                  </td>
                  <td class="p-4 text-right align-top">
                    <div class="flex justify-end gap-1.5">
                      <button onclick={() => startEdit(review)} class="w-6 h-6 rounded bg-white/[0.02] border border-white/5 hover:bg-blue-500/20 text-gray-500 hover:text-blue-400 flex items-center justify-center transition-colors" title="Chỉnh sửa">
                        <Edit2 size={12} />
                      </button>
                      {#if review.status !== 'APPROVED'}
                        <button onclick={() => handleUpdateStatus(review.id, 'APPROVED')} class="w-6 h-6 rounded bg-white/[0.02] border border-white/5 hover:bg-green-500/20 text-gray-500 hover:text-green-400 flex items-center justify-center transition-colors">
                          <CheckCircle size={12} />
                        </button>
                      {/if}
                      {#if review.status !== 'REJECTED'}
                        <button onclick={() => handleUpdateStatus(review.id, 'REJECTED')} class="w-6 h-6 rounded bg-white/[0.02] border border-white/5 hover:bg-red-500/20 text-gray-500 hover:text-red-400 flex items-center justify-center transition-colors">
                          <XCircle size={12} />
                        </button>
                      {/if}
                      <button onclick={() => handleDelete(review.id)} class="w-6 h-6 rounded bg-white/[0.02] border border-white/5 hover:bg-red-600/20 text-gray-500 hover:text-red-500 flex items-center justify-center transition-colors">
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    {/if}
  </div>

  <!-- Bulk Action Bar -->
  {#if selectedIds.length > 0}
    <div 
      class="absolute bottom-6 left-1/2 -translate-x-1/2 z-50 bg-[#0a0a0a] border border-neon-cyan shadow-[0_0_30px_rgba(0,255,255,0.2)] px-6 py-4 flex items-center gap-6 rounded-none min-w-[400px]"
      transition:fade
    >
      <div class="flex flex-col shrink-0">
        <span class="text-[8px] font-mono text-gray-500 tracking-widest uppercase">Kích hoạt tác vụ</span>
        <span class="text-xs font-bold text-neon-cyan font-mono">{selectedIds.length} ITEMS SELECTED</span>
      </div>
      
      <div class="h-8 w-px bg-white/10 mx-2"></div>
      
      <div class="flex items-center gap-3">
        <button 
          onclick={() => handleBulkAction('APPROVE')} 
          class="flex items-center gap-2 px-4 py-2 bg-green-500/10 hover:bg-green-500 text-green-500 hover:text-black border border-green-500/30 transition-all text-[10px] font-mono tracking-widest uppercase"
        >
          <CheckCircle size={14} /> DUYỆT
        </button>
        <button 
          onclick={() => handleBulkAction('REJECT')} 
          class="flex items-center gap-2 px-4 py-2 bg-amber-500/10 hover:bg-amber-500 text-amber-500 hover:text-black border border-amber-500/30 transition-all text-[10px] font-mono tracking-widest uppercase"
        >
          <XCircle size={14} /> TỪ CHỐI
        </button>
        <button 
          onclick={() => handleBulkAction('DELETE')} 
          class="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white border border-red-500/30 transition-all text-[10px] font-mono tracking-widest uppercase"
        >
          <Trash2 size={14} /> XOÁ HÀNG LOẠT
        </button>
      </div>
      
      <div class="h-8 w-px bg-white/10 mx-2"></div>
      
      <button 
        onclick={() => selectedIds = []}
        class="text-[10px] font-mono text-gray-500 hover:text-white uppercase tracking-widest transition-colors"
      >
        HUỶ BỎ
      </button>
    </div>
  {/if}
  <!-- Edit Review Drawer (Right-aligned, AppointmentDrawer pattern) -->
  {#if editingReviewId}
    <div use:portal class="relative" style="z-index: {Z_INDEX_ADMIN.MODAL};">
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-black/90 backdrop-blur-sm"
        style="z-index: {Z_INDEX_ADMIN.OVERLAY};"
        transition:fade={{ duration: 300 }}
        onclick={cancelEdit}
        role="button"
        tabindex="0"
        onkeydown={(e) => e.key === 'Escape' && cancelEdit()}
        aria-label="Đóng panel"
      ></div>

      <!-- Drawer Panel -->
      <div
        class="fixed top-0 right-0 h-full w-[560px] max-w-full bg-[#050505] border-l border-white/10 shadow-[-30px_0_60px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden"
        transition:fly={{ x: 560, duration: 300, opacity: 1 }}
        style="z-index: {Z_INDEX_ADMIN.MODAL + 10};"
      >
        <!-- Header -->
        <div class="h-16 flex items-center justify-between px-6 border-b border-white/10 relative bg-black/40 shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-neon-cyan/10 border border-neon-cyan/20 flex items-center justify-center">
              <Edit2 size={14} class="text-neon-cyan" />
            </div>
            <div>
              <h2 class="text-sm font-bold text-white tracking-widest uppercase">Chỉnh Sửa Đánh Giá</h2>
              <div class="text-[9px] font-mono text-gray-500 uppercase">SYS_ID: {editingReviewId}</div>
            </div>
          </div>
          <button
            onclick={cancelEdit}
            class="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-white hover:bg-white/10 rounded-lg transition-colors border border-transparent hover:border-white/10"
          >
            <X size={16} />
          </button>
          <!-- Decorative bottom line -->
          <div class="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-neon-cyan/20 to-transparent"></div>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto custom-scrollbar p-6 flex flex-col gap-8">
          <!-- NeuralEditor -->
          <div class="flex flex-col gap-3">
            <div class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Nội dung đánh giá</div>
            <div class="border border-white/5 bg-white/[0.02] rounded-xl overflow-hidden">
              <NeuralEditor bind:content={editContent} />
            </div>
          </div>

          <!-- Attachments -->
          <div class="flex flex-col gap-3">
            <div class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1 flex items-center gap-2">
              Tài nguyên đính kèm
              <span class="px-1.5 py-0.5 bg-red-500/10 text-red-400 border border-red-500/20 text-[8px] rounded-sm font-mono normal-case tracking-normal">Xóa vật lý</span>
            </div>

            {#if editAttachments.length === 0}
              <div class="text-[10px] font-mono text-gray-600 italic py-4 text-center border border-white/5 rounded-xl bg-white/[0.02]">
                Không có hình ảnh / video nào.
              </div>
            {:else}
              <div class="flex flex-wrap gap-4">
                {#each editAttachments as media}
                  <div class="w-28 h-28 relative border border-white/10 rounded-lg bg-[#050505] group overflow-hidden">
                    {#if media.type === 'video' || media.url.match(/\.(mp4|webm|mov)$/i) || media.url.includes('video')}
                      <video src={media.url} class="w-full h-full object-cover" muted playsinline></video>
                      <div class="absolute inset-0 bg-black/30 flex items-center justify-center pointer-events-none">
                        <Play size={16} class="text-white fill-current opacity-80" />
                      </div>
                    {:else}
                      <img src={media.url} alt="" class="w-full h-full object-cover" />
                    {/if}

                    <button
                      onclick={() => editAttachments = editAttachments.filter(a => a.url !== media.url)}
                      class="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-red-500/90 text-white flex items-center justify-center shadow-lg hover:scale-110 transition-transform z-10"
                      title="Xóa tài nguyên này"
                    >
                      <X size={12} />
                    </button>

                    <div class="absolute bottom-1 left-1 bg-black/70 px-1 py-0.5 text-[8px] font-mono text-white uppercase backdrop-blur-sm rounded-sm">
                      {media.type}
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>

          <!-- Save Button (in-body, following AppointmentDrawer pattern) -->
          <div class="pt-2">
            <button
              onclick={() => saveEdit(editingReviewId!)}
              disabled={isLoading}
              class="w-full py-4 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-500 text-black text-[11px] font-black uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_10px_30px_-5px_rgba(0,200,200,0.4)] disabled:opacity-50 flex items-center justify-center gap-2 relative overflow-hidden group"
            >
              <!-- Sheen effect -->
              <div class="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
              {#if isLoading}
                <RefreshCw size={14} class="animate-spin" />
                Đang xử lý...
              {:else}
                Lưu đánh giá
              {/if}
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
    height: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 255, 0.2);
  }
  
  :global(.content-prose-admin p) {
    margin-bottom: 0.25rem;
    display: inline;
  }
  :global(.content-prose-admin p:last-child) {
    margin-bottom: 0;
  }
  :global(.content-prose-admin strong) {
    color: #e5e7eb;
    font-weight: 700;
  }
  :global(.content-prose-admin ul) {
    list-style-type: none;
    margin-top: 0.25rem;
    display: inline;
  }
  :global(.content-prose-admin li) {
    display: inline;
  }
  :global(.content-prose-admin li::before) {
    content: "• ";
    color: #0ff;
    margin-left: 4px;
  }
</style>
