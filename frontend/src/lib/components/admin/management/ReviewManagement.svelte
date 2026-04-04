<script lang="ts">
  import { fade } from "svelte/transition";
  import { untrack } from "svelte";
  import Star from "lucide-svelte/icons/star";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import XCircle from "lucide-svelte/icons/x-circle";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import MessageSquare from "lucide-svelte/icons/message-square";
  import Layers from "lucide-svelte/icons/layers";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import LayoutGrid from "lucide-svelte/icons/layout-grid";
  import List from "lucide-svelte/icons/list";
  import type { BaseWidgetProps } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
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
  }

  let reviews = $state<Review[]>([]);
  let totalReviews = $state(0);
  let isLoading = $state(true);

  let activeFilter = $state("all"); // PENDING, APPROVED, REJECTED
  let activeCategory = $state("all"); // PRODUCT, NEWS
  let viewMode = $state<"grid" | "list">("grid");
  
  let currentPage = $state(1);
  let pageSize = $state(20);

  let selectedIds = $state<string[]>([]);

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
          {#each ["all", "product", "news"] as c}
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

                <p class="text-xs text-gray-400 leading-relaxed mb-5 italic border-l-2 border-white/10 pl-3 min-h-[40px]">"{review.content}"</p>
                
                <div class="mt-auto flex justify-between items-center border-t border-white/5 pt-4">
                  <span class="text-[9px] font-mono tracking-[0.2em] uppercase px-2 py-0.5 border rounded-sm {getStatusStyle(review.status)}">
                    {review.status}
                  </span>
                  <div class="flex gap-2" onclick={(e) => e.stopPropagation()}>
                    <div class="flex flex-col items-end">
                      {#if review.customer_location}
                        <span class="text-[8px] text-gray-500 font-mono uppercase tracking-widest mb-1">{review.customer_location}</span>
                      {/if}
                      <div class="flex gap-2">
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
                  <td class="p-4 max-w-[300px]">
                    <p class="text-[11px] text-gray-400 truncate" title={review.content}>{review.content}</p>
                  </td>
                  <td class="p-4">
                    <span class="text-[9px] font-mono tracking-[0.2em] uppercase px-2 py-0.5 border rounded-sm {getStatusStyle(review.status)}">
                      {review.status}
                    </span>
                  </td>
                  <td class="p-4 text-right">
                    <div class="flex justify-end gap-1.5">
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
</style>
