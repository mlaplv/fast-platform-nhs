<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import { untrack } from "svelte";
  import Star from "@lucide/svelte/icons/star";
  import CheckCircle from "@lucide/svelte/icons/check-circle";
  import XCircle from "@lucide/svelte/icons/x-circle";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import Edit2 from "@lucide/svelte/icons/edit-2";
  import ThumbsUp from "@lucide/svelte/icons/thumbs-up";
  import Layers from "@lucide/svelte/icons/layers";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import LayoutGrid from "@lucide/svelte/icons/layout-grid";
  import List from "@lucide/svelte/icons/list";
  import X from "@lucide/svelte/icons/x";
  import Play from "@lucide/svelte/icons/play";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import User from "@lucide/svelte/icons/user";
  import Phone from "@lucide/svelte/icons/phone";
  import Box from "@lucide/svelte/icons/box";
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
  let isRewriting = $state(false);
  
  // Elite V2.2: Extended Edit States
  let editEntityType = $state<"PRODUCT" | "CATEGORY" | "NEWS">("PRODUCT");
  let editEntityId = $state("");
  let editCustomerName = $state("");
  let editCustomerPhone = $state("");
  let editCustomerLocation = $state("");
  let editRating = $state(5);
  
  // Entity Lists for Selection
  let targetEntities = $state<{id: string, name: string}[]>([]);
  let isTargetLoading = $state(false);
  let isEntitiesExpanded = $state(false);
  let isMoreEntitiesShown = $state(false);

  async function startEdit(review: Review) {
    editingReviewId = review.id;
    editContent = review.content;
    editAttachments = Array.isArray(review.attachments) ? JSON.parse(JSON.stringify(review.attachments)) : [];
    
    // Bind Extended Data
    editEntityType = review.entity_type as any;
    editEntityId = review.entity_id;
    editCustomerName = review.customer_name;
    editCustomerPhone = review.customer_phone || "";
    editCustomerLocation = review.customer_location || "";
    editRating = review.rating;
    
    await loadTargetEntities(editEntityType);
  }

  async function loadTargetEntities(type: string) {
    isTargetLoading = true;
    try {
      let endpoint = "";
      if (type === "PRODUCT") endpoint = "/api/v1/products?limit=200&status=PUBLISHED";
      else if (type === "NEWS") endpoint = "/api/v1/articles?limit=200&status=PUBLISHED";
      else if (type === "CATEGORY") endpoint = "/api/v1/categories?limit=200";
      
      if (!endpoint) {
        targetEntities = [];
        return;
      }

      const res = await apiClient.get<any>(endpoint);
      console.log(`🧬 [Xohi AI] Dữ liệu tải về từ ${endpoint}:`, res);
      
      // Elite V2.2: Litestar returns { data: [...], total: ... }
      const items = Array.isArray(res.data?.data) ? res.data.data : (Array.isArray(res.data) ? res.data : []);
      
      const seenIds = new Set();
      const rawList = items.map((i: any) => ({
        id: i.id,
        name: (type === "NEWS" ? i.title : i.name) || "Không tên"
      }));

      targetEntities = rawList.filter(item => {
        if (!item.id || seenIds.has(item.id)) return false;
        const nameLower = item.name.toLowerCase();
        // Loại bỏ mục test, rác
        if (nameLower.includes("test ") || nameLower.includes("faq save") || nameLower.includes("dummy")) return false;
        seenIds.add(item.id);
        return true;
      });
    } catch (e) {
      console.error("Lỗi tải danh sách thực thể:", e);
      targetEntities = [];
    } finally {
      isTargetLoading = false;
    }
  }

  function cancelEdit() {
    editingReviewId = null;
    editContent = "";
    editAttachments = [];
  }

  async function saveEdit(id: string) {
    isLoading = true;
    try {
      await apiClient.patch(`/api/v1/reviews/${id}`, { 
        content: editContent,
        attachments: editAttachments,
        entity_type: editEntityType,
        entity_id: editEntityId,
        customer_name: editCustomerName,
        customer_phone: editCustomerPhone,
        customer_location: editCustomerLocation,
        rating: editRating
      });
      nanobot.showToast("Đã cập nhật đánh giá hệ thống", "success");
      cancelEdit();
      await loadReviews();
    } catch (e: unknown) {
      nanobot.showToast("Lỗi khi cập nhật đánh giá", "error");
    } finally {
      isLoading = false;
    }
  }

  async function handleXohiRewrite() {
    if (!editContent || isRewriting) return;
    
    isRewriting = true;
    try {
      // Tìm tên thực thể đang được chọn để cung cấp ngữ cảnh cho AI
      const entityName = targetEntities.find(e => e.id === editEntityId)?.name || "sản phẩm/dịch vụ";
      
      console.log(`🧬 [Xohi AI] Gửi nội dung cho [${entityName}]:`, editContent);
      // Gọi AI Rewrite chuyên dụng cho Review
      const res = await apiClient.post<{new_content: string}>("/api/v1/content/analyze/neural-rewrite", {
        content: editContent,
        content_type: "review",
        topic: entityName,
        feedback: "Viết lại thật chân thật, bám sát trải nghiệm thực tế về đúng loại sản phẩm này. Tuyệt đối không dùng các từ mỹ miều sáo rỗng."
      });
      
      console.log("🧬 [Xohi AI] Kết quả từ API:", res);
      
      if (res.data && res.data.new_content) {
        editContent = res.data.new_content;
        console.log("🧬 [Xohi AI] Đã cập nhật editContent thành:", editContent);
        nanobot.showToast("Đã tối ưu đánh giá bằng Xohi Neural", "success");
      } else {
        console.warn("🧬 [Xohi AI] API không trả về new_content trong data:", res);
      }
    } catch (e: unknown) {
      const err = e as Error;
      nanobot.showToast("Lỗi Neural Engine: " + err.message, "error");
    } finally {
      isRewriting = false;
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
          <h2 class="text-white font-bold tracking-widest text-sm">Quản Trị Đánh Giá</h2>
          <p class="text-[10px] text-gray-500 font-mono tracking-widest ">{totalReviews} BLOCKS FOUND</p>
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

    <div class="flex flex-wrap gap-4 sm:gap-8 items-center bg-white/[0.03] border-y border-white/5 p-4 sm:p-6">
      <!-- Status Filter -->
      <div class="flex flex-col gap-3">
        <span class="text-[9px] font-mono text-neon-cyan tracking-[0.3em] font-bold">Lọc Trạng thái</span>
        <div class="flex items-center gap-1 bg-[#050505] border border-white/10 p-1 rounded-sm shadow-inner">
          {#each ["all", "pending", "approved", "rejected"] as f}
            <button
              onclick={() => activeFilter = f}
              class="px-4 py-1.5 text-[10px] font-mono tracking-widest transition-all {activeFilter === f ? 'bg-neon-cyan text-black shadow-[0_0_10px_rgba(0,255,255,0.4)] font-bold' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}"
            >
              {f}
            </button>
          {/each}
        </div>
      </div>

      <div class="hidden sm:block h-10 w-px bg-white/5"></div>

      <!-- Entity Type Filter -->
      <div class="flex flex-col gap-3">
        <span class="text-[9px] font-mono text-purple-400 tracking-[0.3em] font-bold">Lọc Danh mục</span>
        <div class="flex items-center gap-1 bg-[#050505] border border-white/10 p-1 rounded-sm shadow-inner">
          {#each ["all", "product", "category", "news"] as c}
            <button
              onclick={() => activeCategory = c}
              class="px-4 py-1.5 text-[10px] font-mono tracking-widest transition-all {activeCategory === c ? 'bg-purple-500 text-white shadow-[0_0_10px_rgba(168,85,247,0.4)] font-bold' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}"
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
          class="flex items-center gap-2 px-3 py-1.5 border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all text-[10px] font-mono tracking-widest text-gray-400"
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
       <div class="h-full flex flex-col gap-3 items-center justify-center text-neon-cyan/50 font-mono text-[10px] tracking-[0.3em] animate-pulse">
         <div class="w-10 h-10 border-2 border-neon-cyan/20 border-t-neon-cyan rounded-full animate-spin"></div>
         SYNCING_DATABANKS...
       </div>
    {:else if reviews.length === 0}
       <div class="h-full flex flex-col items-center justify-center text-gray-500 gap-3">
         <div class="w-12 h-12 rounded-full border border-white/5 bg-white/[0.02] flex items-center justify-center">
           <MessageSquare size={20} class="opacity-30" />
         </div>
         <p class="font-mono text-[10px] tracking-[0.2em] ">NO_REVIEWS_FOUND</p>
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
                      <span class="text-[9px] font-mono tracking-[0.2em] text-[#FFB800] bg-[#FFB800]/5 px-1.5 py-0.5 border border-[#FFB800]/20 ">
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
                    <span class="text-[9px] font-mono tracking-[0.2em] px-2 py-0.5 border rounded-sm {getStatusStyle(review.status)}">
                      {review.status}
                    </span>
                  </div>
                  <div class="flex gap-2" onclick={(e) => e.stopPropagation()}>
                    <div class="flex flex-col items-end">
                      {#if review.customer_location}
                        <span class="text-[8px] text-gray-500 font-mono tracking-widest mb-1">{review.customer_location}</span>
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
                <th class="text-[10px] font-mono text-gray-500 tracking-widest text-left p-4">Khách hàng</th>
                <th class="text-[10px] font-mono text-gray-500 tracking-widest text-left p-4">Danh mục</th>
                <th class="text-[10px] font-mono text-gray-500 tracking-widest text-left p-4">Đánh giá</th>
                <th class="text-[10px] font-mono text-gray-500 tracking-widest text-left p-4">Nội dung</th>
                <th class="text-[10px] font-mono text-gray-500 tracking-widest text-left p-4">Trạng thái</th>
                <th class="text-[10px] font-mono text-gray-500 tracking-widest text-right p-4">Thao tác</th>
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
                    <span class="text-[9px] font-mono tracking-[0.2em] text-[#FFB800] bg-[#FFB800]/5 px-1.5 py-0.5 border border-[#FFB800]/20 ">
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
                      <span class="text-[9px] font-mono tracking-[0.2em] px-2 py-0.5 border rounded-sm {getStatusStyle(review.status)}">
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

      <!-- Pagination -->
      {#if totalReviews > pageSize}
        <div class="mt-12 flex items-center justify-between border-t border-white/5 pt-8 pb-12">
          <div class="text-[10px] font-mono text-gray-600 tracking-widest">
            Hiển thị <span class="text-neon-cyan">{(currentPage - 1) * pageSize + 1}</span> - <span class="text-neon-cyan">{Math.min(currentPage * pageSize, totalReviews)}</span> của <span class="text-white">{totalReviews}</span> đánh giá
          </div>
          
          <div class="flex items-center gap-2">
            <button 
              onclick={() => currentPage = Math.max(1, currentPage - 1)}
              disabled={currentPage === 1 || isLoading}
              class="px-4 py-2 border border-white/5 bg-white/[0.02] hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all text-[10px] font-mono tracking-widest "
            >
              Trang trước
            </button>
            
            <div class="flex items-center gap-1">
              {#each Array(Math.ceil(totalReviews / pageSize)) as _, i}
                {#if Math.abs(i + 1 - currentPage) < 3 || i === 0 || i === Math.ceil(totalReviews / pageSize) - 1}
                  <button 
                    onclick={() => currentPage = i + 1}
                    class="w-8 h-8 flex items-center justify-center border {currentPage === i + 1 ? 'border-neon-cyan text-neon-cyan bg-neon-cyan/10' : 'border-white/5 text-gray-500 hover:border-white/20'} text-[10px] font-mono transition-all"
                  >
                    {i + 1}
                  </button>
                {:else if Math.abs(i + 1 - currentPage) === 3}
                  <span class="text-gray-700 mx-1">...</span>
                {/if}
              {/each}
            </div>

            <button 
              onclick={() => currentPage = Math.min(Math.ceil(totalReviews / pageSize), currentPage + 1)}
              disabled={currentPage === Math.ceil(totalReviews / pageSize) || isLoading}
              class="px-4 py-2 border border-white/5 bg-white/[0.02] hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all text-[10px] font-mono tracking-widest "
            >
              Trang sau
            </button>
          </div>
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
        <span class="text-[8px] font-mono text-gray-500 tracking-widest ">Kích hoạt tác vụ</span>
        <span class="text-xs font-bold text-neon-cyan font-mono">{selectedIds.length} ITEMS SELECTED</span>
      </div>
      
      <div class="h-8 w-px bg-white/10 mx-2"></div>
      
      <div class="flex items-center gap-3">
        <button 
          onclick={() => handleBulkAction('APPROVE')} 
          class="flex items-center gap-2 px-4 py-2 bg-green-500/10 hover:bg-green-500 text-green-500 hover:text-black border border-green-500/30 transition-all text-[10px] font-mono tracking-widest "
        >
          <CheckCircle size={14} /> DUYỆT
        </button>
        <button 
          onclick={() => handleBulkAction('REJECT')} 
          class="flex items-center gap-2 px-4 py-2 bg-amber-500/10 hover:bg-amber-500 text-amber-500 hover:text-black border border-amber-500/30 transition-all text-[10px] font-mono tracking-widest "
        >
          <XCircle size={14} /> TỪ CHỐI
        </button>
        <button 
          onclick={() => handleBulkAction('DELETE')} 
          class="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white border border-red-500/30 transition-all text-[10px] font-mono tracking-widest "
        >
          <Trash2 size={14} /> XOÁ HÀNG LOẠT
        </button>
      </div>
      
      <div class="h-8 w-px bg-white/10 mx-2"></div>
      
      <button 
        onclick={() => selectedIds = []}
        class="text-[10px] font-mono text-gray-500 hover:text-white tracking-widest transition-colors"
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
              <h2 class="text-sm font-bold text-white tracking-widest ">Chỉnh Sửa Đánh Giá</h2>
              <div class="text-[9px] font-mono text-gray-500 ">SYS_ID: {editingReviewId}</div>
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
        <div class="flex-1 overflow-y-auto custom-scrollbar p-6 flex flex-col gap-10">
          
          <!-- Section 1: Context (Nguồn đánh giá) -->
          <div class="flex flex-col gap-4">
            <div class="flex items-center gap-2">
              <Box size={14} class="text-neon-cyan" />
              <h3 class="text-[10px] font-black text-white/40 tracking-[0.2em]">Cấu hình nguồn đánh giá</h3>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="flex flex-col gap-2">
                <label class="text-[8px] font-bold text-gray-500 ml-1">Loại thực thể</label>
                <select 
                  bind:value={editEntityType}
                  onchange={() => loadTargetEntities(editEntityType)}
                  class="w-full bg-[#0a0a0b] border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50 transition-colors custom-select"
                >
                  <option value="PRODUCT" class="bg-[#0a0a0b]">SẢN PHẨM</option>
                  <option value="NEWS" class="bg-[#0a0a0b]">TIN TỨC / BÀI VIẾT</option>
                  <option value="CATEGORY" class="bg-[#0a0a0b]">DANH MỤC</option>
                </select>
              </div>
              <div class="flex flex-col gap-2">
                <label class="text-[8px] font-bold text-gray-500 ml-1">Đối tượng cụ thể</label>
                <div class="relative">
                  <button 
                    onclick={() => isEntitiesExpanded = !isEntitiesExpanded}
                    class="w-full bg-[#0a0a0b] border border-white/10 rounded-lg px-3 py-2 text-xs text-left text-white flex justify-between items-center focus:border-neon-cyan/50 transition-all {isTargetLoading ? 'opacity-50 cursor-wait' : ''}"
                  >
                    <span class="truncate">{targetEntities.find(e => e.id === editEntityId)?.name || "-- Chọn đối tượng --"}</span>
                    <Layers size={10} class="text-white/30" />
                  </button>

                  {#if isEntitiesExpanded}
                    <div class="absolute z-[100] left-0 right-0 mt-1 bg-[#0d0d0f] border border-white/10 shadow-2xl overflow-hidden max-h-[300px] flex flex-col">
                      <div class="overflow-y-auto custom-scrollbar flex-1">
                        {#each (isMoreEntitiesShown ? targetEntities : targetEntities.slice(0, 5)) as entity}
                          <button 
                            onclick={() => { editEntityId = entity.id; isEntitiesExpanded = false; isMoreEntitiesShown = false; }}
                            class="w-full text-left px-3 py-2 text-[11px] hover:bg-neon-cyan/10 hover:text-neon-cyan transition-colors {editEntityId === entity.id ? 'bg-neon-cyan/5 text-neon-cyan font-bold' : 'text-gray-400'}"
                          >
                            {entity.name}
                          </button>
                        {/each}
                        {#if targetEntities.length > 5 && !isMoreEntitiesShown}
                          <button onclick={(e) => { e.stopPropagation(); isMoreEntitiesShown = true; }} class="w-full px-3 py-1.5 text-[9px] font-mono text-neon-cyan/60 hover:text-neon-cyan hover:bg-white/5 text-center border-t border-white/5">+ XEM THÊM {targetEntities.length - 5} MỤC KHÁC</button>
                        {/if}
                        {#if isMoreEntitiesShown}
                          <button onclick={(e) => { e.stopPropagation(); isMoreEntitiesShown = false; }} class="w-full px-3 py-1.5 text-[9px] font-mono text-gray-600 hover:text-white hover:bg-white/5 text-center border-t border-white/5">THU GỌN</button>
                        {/if}
                      </div>
                    </div>
                    <div class="fixed inset-0 z-[90]" onclick={() => { isEntitiesExpanded = false; isMoreEntitiesShown = false; }}></div>
                  {/if}
                  {#if isTargetLoading}
                    <div class="absolute right-8 top-2.5"><div class="w-3 h-3 border-2 border-neon-cyan/20 border-t-neon-cyan rounded-full animate-spin"></div></div>
                  {/if}
                </div>
              </div>
            </div>
          </div>

          <!-- Section 2: Customer (Thông tin khách hàng) -->
          <div class="flex flex-col gap-4">
            <div class="flex items-center gap-2">
              <User size={14} class="text-neon-cyan" />
              <h3 class="text-[10px] font-black text-white/40 tracking-[0.2em]">Thông tin định danh</h3>
            </div>
            <div class="grid grid-cols-3 gap-4">
              <div class="flex flex-col gap-2">
                <label class="text-[8px] font-bold text-gray-500 ml-1">Tên hiển thị</label>
                <div class="relative group">
                  <User size={10} class="absolute left-3 top-3 text-white/20 group-focus-within:text-neon-cyan transition-colors" />
                  <input 
                    type="text" 
                    bind:value={editCustomerName}
                    placeholder="Nguyễn Văn A"
                    class="w-full bg-white/[0.03] border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50 transition-colors"
                  />
                </div>
              </div>
              <div class="flex flex-col gap-2">
                <label class="text-[8px] font-bold text-gray-500 ml-1">Số điện thoại</label>
                <div class="relative group">
                  <Phone size={10} class="absolute left-3 top-3 text-white/20 group-focus-within:text-neon-cyan transition-colors" />
                  <input 
                    type="text" 
                    bind:value={editCustomerPhone}
                    placeholder="09xxx..."
                    class="w-full bg-white/[0.03] border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50 transition-colors"
                  />
                </div>
              </div>
              <div class="flex flex-col gap-2">
                <label class="text-[8px] font-bold text-gray-500 ml-1">Địa điểm</label>
                <div class="relative group">
                  <MapPin size={10} class="absolute left-3 top-3 text-white/20 group-focus-within:text-neon-cyan transition-colors" />
                  <input 
                    type="text" 
                    bind:value={editCustomerLocation}
                    placeholder="Hà Nội, VN"
                    class="w-full bg-white/[0.03] border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50 transition-colors"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Section 3: Rating -->
          <div class="flex flex-col gap-4">
             <div class="flex items-center gap-2">
              <Star size={14} class="text-neon-cyan" />
              <h3 class="text-[10px] font-black text-white/40 tracking-[0.2em]">Đánh giá & Xếp hạng</h3>
            </div>
            <div class="flex items-center gap-4 bg-white/[0.02] border border-white/5 p-4 rounded-xl">
               <div class="flex gap-1">
                {#each Array(5) as _, i}
                  <button 
                    onclick={() => editRating = i + 1}
                    class="transition-all duration-300 {i < editRating ? 'text-yellow-400 scale-110 drop-shadow-[0_0_8px_rgba(250,204,21,0.4)]' : 'text-white/10 hover:text-white/30'}"
                  >
                    <Star size={20} fill={i < editRating ? 'currentColor' : 'none'} />
                  </button>
                {/each}
              </div>
              <div class="h-4 w-[1px] bg-white/10"></div>
              <span class="text-[10px] font-mono text-neon-cyan tracking-widest">{editRating} / 5 SAO</span>
            </div>
          </div>

          <!-- Section 4: Content (NeuralEditor) -->
          <div class="flex flex-col gap-3">
            <div class="flex justify-between items-end">
              <div class="flex items-center gap-2 ml-1">
                <Sparkles size={12} class="text-neon-cyan" />
                <div class="text-[8px] font-black text-white/30 tracking-[0.2em]">Nội dung & Trí tuệ AI</div>
              </div>
              <button 
                onclick={handleXohiRewrite}
                disabled={isRewriting}
                class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-neon-cyan/10 border border-neon-cyan/20 text-neon-cyan hover:bg-neon-cyan/20 transition-all group disabled:opacity-50 disabled:grayscale"
              >
                <Sparkles size={10} class={isRewriting ? 'animate-pulse' : 'group-hover:scale-125 transition-transform'} />
                <span class="text-[9px] font-bold tracking-wider">{isRewriting ? 'NEURAL_PROCESSING...' : 'XOHI_REWRITE'}</span>
              </button>
            </div>
            <div class="border border-white/5 bg-white/[0.02] rounded-xl overflow-hidden relative min-h-[300px]">
              {#if isRewriting}
                <div class="absolute inset-0 z-10 bg-black/40 backdrop-blur-[2px] flex items-center justify-center pointer-events-none">
                  <div class="flex flex-col items-center gap-2">
                    <div class="w-8 h-8 border-2 border-neon-cyan/20 border-t-neon-cyan rounded-full animate-spin"></div>
                    <span class="text-[8px] font-mono text-neon-cyan tracking-[0.3em] animate-pulse">REWRITING...</span>
                  </div>
                </div>
              {/if}
              <NeuralEditor bind:content={editContent} {isRewriting} />
            </div>
          </div>

          <!-- Attachments -->
          <div class="flex flex-col gap-3">
            <div class="text-[8px] font-black text-white/30 tracking-[0.2em] ml-1 flex items-center gap-2">
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

                    <div class="absolute bottom-1 left-1 bg-black/70 px-1 py-0.5 text-[8px] font-mono text-white backdrop-blur-sm rounded-sm">
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
              class="w-full py-4 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-500 text-black text-[11px] font-black tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_10px_30px_-5px_rgba(0,200,200,0.4)] disabled:opacity-50 flex items-center justify-center gap-2 relative overflow-hidden group"
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
