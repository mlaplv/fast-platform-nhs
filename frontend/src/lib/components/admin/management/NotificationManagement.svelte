<script lang="ts">
  import { getNotificationState } from "$lib/state/notification.svelte";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import { fade, slide } from "svelte/transition";
  import XohiLogo from "../XohiLogo.svelte";
  import { onMount } from "svelte";
  
  const notificationState = getNotificationState();
  const nanobot = useNanobot();

  onMount(() => {
    notificationState.fetchNotifications();
  });

  let activeFilter = $state<"ALL" | "ORDER" | "CHAT" | "SECURITY" | "URGENT">("ALL");
  let searchQuery = $state("");
  let selectedNotification = $state<any | null>(null);
  let selectedIds = $state<string[]>([]);

  function toggleSelectAll() {
    if (selectedIds.length === filteredNotifications.length) {
      selectedIds = [];
    } else {
      selectedIds = filteredNotifications.map(n => n.id);
    }
  }

  function toggleSelect(id: string, event: Event) {
    event.stopPropagation();
    if (selectedIds.includes(id)) {
      selectedIds = selectedIds.filter(x => x !== id);
    } else {
      selectedIds = [...selectedIds, id];
    }
  }

  async function handleBulkDelete() {
    if (selectedIds.length === 0) return;
    if (confirm(`Xoá mềm ${selectedIds.length} thông báo đã chọn?`)) {
      await (notificationState as any).bulkDeleteNotifications(selectedIds);
      selectedIds = [];
    }
  }

  async function handleClearCurrentTab() {
    const filterLabel = activeFilter === "ALL" ? "tất cả" : `tab ${activeFilter}`;
    if (confirm(`Dọn sạch ${filterLabel} thông báo trong database?`)) {
      await (notificationState as any).clearNotifications(activeFilter);
      selectedIds = [];
    }
  }

  async function handleClearAllTabs() {
    if (confirm("Dọn sạch TẤT CẢ thông báo ở mọi tab trong database?")) {
      await (notificationState as any).clearNotifications("ALL");
      selectedIds = [];
    }
  }

  // Elite V2.2 Runes-based reactivity
  const filteredNotifications = $derived.by(() => {
    let list = notificationState.notifications;

    // Apply severity/type filters
    if (activeFilter !== "ALL") {
      list = list.filter(n => {
        const type = (n.type || "").toUpperCase();
        if (activeFilter === "ORDER") {
          return type.includes("ORDER") || type.includes("COMMERCE");
        }
        if (activeFilter === "CHAT") {
          return type === "CHAT" || type.includes("SUPPORT");
        }
        if (activeFilter === "SECURITY") {
          return type.includes("SECURITY") || type.includes("SYSTEM") || type.includes("ANOMALY");
        }
        if (activeFilter === "URGENT") {
          return type.includes("URGENT") || type === "CRITICAL";
        }
        return true;
      });
    }

    // Apply text search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(n => 
        (n.message || "").toLowerCase().includes(q) || 
        (n.type || "").toLowerCase().includes(q)
      );
    }

    return list;
  });

  const stats = $derived.by(() => {
    const list = notificationState.notifications;
    return {
      total: list.length,
      unread: list.filter(n => !n.isRead).length,
      orders: list.filter(n => (n.type || "").toUpperCase().includes("ORDER")).length,
      chats: list.filter(n => (n.type || "").toUpperCase() === "CHAT").length,
      critical: list.filter(n => (n.type || "").toUpperCase() === "CRITICAL" || (n.type || "").toUpperCase().includes("URGENT")).length
    };
  });

  async function handleMarkAllAsRead() {
    const unread = notificationState.notifications.filter(n => !n.isRead);
    for (const n of unread) {
      await notificationState.markNotificationAsRead(n.id);
    }
  }

  function getSeverityClass(type: string) {
    const t = (type || "").toUpperCase();
    if (t.includes("CRITICAL") || t.includes("URGENT") || t.includes("SECURITY")) {
      return "bg-red-500/10 border-red-500/30 text-red-400";
    }
    if (t.includes("ORDER") || t.includes("ACTION")) {
      return "bg-amber-500/10 border-amber-500/30 text-amber-400";
    }
    if (t.includes("CHAT")) {
      return "bg-blue-500/10 border-blue-500/30 text-blue-400";
    }
    return "bg-cyan-500/10 border-cyan-500/30 text-cyan-400";
  }

  function formatTime(isoStr: string) {
    if (!isoStr) return "";
    try {
      const date = new Date(isoStr);
      return date.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) + " - " + date.toLocaleDateString("vi-VN", { day: "numeric", month: "short" });
    } catch {
      return isoStr;
    }
  }
</script>

<div class="notification-management h-full w-full bg-[#030303]/90 text-gray-200 flex flex-col relative overflow-hidden backdrop-blur-2xl">
  <!-- Liquid Glass Header -->
  <header class="p-6 border-b border-white/5 flex items-center justify-between bg-black/40">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9m1.72 13a3 3 0 0 0 5.43 0"/></svg>
      </div>
      <div>
        <h2 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          NOTIFICATION HUB
          {#if stats.unread > 0}
            <span class="px-2 py-0.5 text-[10px] font-bold bg-cyan-500 text-black rounded-full animate-pulse">{stats.unread} NEW</span>
          {/if}
        </h2>
        <p class="text-xs text-gray-500">Giám sát và kiểm vết lịch sử tín hiệu hệ thống thời gian thực</p>
      </div>
    </div>

    <div class="flex items-center gap-2">
      {#if stats.unread > 0}
        <button 
          onclick={handleMarkAllAsRead} 
          class="px-4 py-2 text-xs font-semibold bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all duration-300 flex items-center gap-1.5"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>
          Đọc tất cả
        </button>
      {/if}
      
      <button 
        onclick={() => nanobot.closeUniversalModal()}
        class="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center border border-white/10 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
  </header>

  <!-- Overview Stats Widgets -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 p-6 bg-black/20">
    <div class="bg-white/[0.02] border border-white/5 rounded-2xl p-4 flex flex-col justify-between">
      <span class="text-xs text-gray-500 font-mono">TỔNG TÍN HIỆU</span>
      <span class="text-2xl font-bold tracking-tight text-white mt-1">{stats.total}</span>
    </div>
    <div class="bg-cyan-500/[0.02] border border-cyan-500/10 rounded-2xl p-4 flex flex-col justify-between">
      <span class="text-xs text-cyan-500/70 font-mono">CHƯA ĐỌC</span>
      <span class="text-2xl font-bold tracking-tight text-cyan-400 mt-1">{stats.unread}</span>
    </div>
    <div class="bg-amber-500/[0.02] border border-amber-500/10 rounded-2xl p-4 flex flex-col justify-between">
      <span class="text-xs text-amber-500/70 font-mono">ĐƠN HÀNG MỚI</span>
      <span class="text-2xl font-bold tracking-tight text-amber-400 mt-1">{stats.orders}</span>
    </div>
    <div class="bg-red-500/[0.02] border border-red-500/10 rounded-2xl p-4 flex flex-col justify-between">
      <span class="text-xs text-red-500/70 font-mono">KHẨN CẤP / CẢNH BÁO</span>
      <span class="text-2xl font-bold tracking-tight text-red-400 mt-1">{stats.critical}</span>
    </div>
  </div>

  <!-- Filters & Search Toolbar -->
  <div class="px-6 py-4 border-b border-white/5 bg-black/10 flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
    <div class="flex flex-wrap gap-1.5">
      <button 
        onclick={() => activeFilter = "ALL"}
        class="px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all duration-300 {activeFilter === 'ALL' ? 'bg-cyan-400/10 border-cyan-400/30 text-cyan-400' : 'bg-transparent border-white/5 hover:bg-white/5 text-gray-400'}"
      >
        Tất cả
      </button>
      <button 
        onclick={() => activeFilter = "ORDER"}
        class="px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all duration-300 {activeFilter === 'ORDER' ? 'bg-amber-400/10 border-amber-400/30 text-amber-400' : 'bg-transparent border-white/5 hover:bg-white/5 text-gray-400'}"
      >
        Đơn hàng
      </button>
      <button 
        onclick={() => activeFilter = "CHAT"}
        class="px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all duration-300 {activeFilter === 'CHAT' ? 'bg-blue-400/10 border-blue-400/30 text-blue-400' : 'bg-transparent border-white/5 hover:bg-white/5 text-gray-400'}"
      >
        Hội thoại
      </button>
      <button 
        onclick={() => activeFilter = "SECURITY"}
        class="px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all duration-300 {activeFilter === 'SECURITY' ? 'bg-red-400/10 border-red-400/30 text-red-400' : 'bg-transparent border-white/5 hover:bg-white/5 text-gray-400'}"
      >
        Hệ thống & An ninh
      </button>
      <button 
        onclick={() => activeFilter = "URGENT"}
        class="px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all duration-300 {activeFilter === 'URGENT' ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' : 'bg-transparent border-white/5 hover:bg-white/5 text-gray-400'}"
      >
        Khẩn cấp
      </button>
    </div>

    <!-- Search Input -->
    <div class="relative flex-1 max-w-md">
      <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-500">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      </span>
      <input 
        type="text" 
        bind:value={searchQuery}
        placeholder="Tìm kiếm thông báo..." 
        class="w-full pl-10 pr-4 py-2 text-xs bg-white/[0.03] hover:bg-white/[0.05] focus:bg-white/[0.08] border border-white/10 rounded-xl focus:border-cyan-500/30 focus:outline-none transition-all placeholder:text-gray-600 text-white font-medium"
      />
    </div>
  </div>

  <!-- Multi-select & Clears Action Toolbar -->
  <div class="px-6 py-3 bg-white/[0.02] border-b border-white/5 flex flex-wrap items-center justify-between gap-4">
    <div class="flex items-center gap-3">
      <button 
        onclick={toggleSelectAll}
        class="px-3 py-1.5 text-xs font-semibold rounded-xl border border-white/10 hover:bg-white/5 transition-all text-gray-300 flex items-center gap-2"
      >
        <div class="w-3.5 h-3.5 rounded border flex items-center justify-center transition-all {selectedIds.length === filteredNotifications.length && filteredNotifications.length > 0 ? 'bg-cyan-500 border-cyan-500 text-black' : 'border-white/20 bg-transparent'}">
          {#if selectedIds.length === filteredNotifications.length && filteredNotifications.length > 0}
            <svg xmlns="http://www.w3.org/2000/svg" class="w-2.5 h-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
          {/if}
        </div>
        {selectedIds.length === filteredNotifications.length && filteredNotifications.length > 0 ? 'Hủy chọn' : 'Chọn tất cả'}
      </button>

      {#if selectedIds.length > 0}
        <span class="text-xs text-cyan-400 font-mono">Đã chọn {selectedIds.length}</span>
        
        <button 
          onclick={handleBulkDelete}
          class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 transition-all flex items-center gap-1.5"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2M10 11v6M14 11v6"/></svg>
          Xóa đã chọn
        </button>
      {/if}
    </div>

    <div class="flex items-center gap-2">
      <button 
        onclick={handleClearCurrentTab}
        class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 transition-all flex items-center gap-1.5"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
        Dọn sạch Tab này
      </button>
      
      <button 
        onclick={handleClearAllTabs}
        class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-300 transition-all flex items-center gap-1.5"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
        Dọn sạch Tất cả
      </button>
    </div>
  </div>

  <!-- Notification List -->
  <div class="flex-1 overflow-y-auto p-6 space-y-3 custom-scrollbar">
    {#each filteredNotifications as item (item.id)}
      <div 
        onclick={() => {
          selectedNotification = item;
          if (!item.isRead) notificationState.markNotificationAsRead(item.id);
        }}
        class="group/item flex items-center justify-between p-4 bg-white/[0.01] hover:bg-white/[0.03] border {item.isRead ? 'border-white/5' : 'border-cyan-500/20 bg-cyan-500/[0.01]'} rounded-2xl transition-all duration-300 cursor-pointer"
        in:fade={{ duration: 200 }}
      >
        <div class="flex items-center gap-4 flex-1 min-w-0">
          <!-- Premium Checkbox -->
          <button 
            onclick={(e) => toggleSelect(item.id, e)}
            class="w-5 h-5 rounded-lg border flex items-center justify-center transition-all duration-300 flex-shrink-0 {selectedIds.includes(item.id) ? 'bg-cyan-500 border-cyan-500 text-black shadow-[0_0_8px_#00FFFF]' : 'border-white/10 hover:border-white/30 text-transparent bg-transparent'}"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
          </button>

          <!-- Severity Indicator -->
          <div class="px-2.5 py-1 text-[9px] font-bold font-mono tracking-widest rounded-lg border uppercase {getSeverityClass(item.type)}">
            {item.type || 'INFO'}
          </div>

          <!-- Message details -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-200 leading-relaxed group-hover/item:text-white transition-colors truncate">
              {item.message}
            </p>
            <span class="text-[10px] text-gray-500 font-mono mt-1 block">
              {formatTime(item.created_at)}
            </span>
          </div>
        </div>

        <div class="flex items-center gap-3 pl-4">
          {#if !item.isRead}
            <div class="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#00FFFF] animate-pulse"></div>
          {/if}

          <!-- Chevron link icon -->
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-600 group-hover/item:text-cyan-400 transform group-hover/item:translate-x-0.5 transition-all" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
        </div>
      </div>
    {:else}
      <div class="flex flex-col items-center justify-center py-20 text-center">
        <div class="w-16 h-16 rounded-2xl bg-white/[0.02] border border-white/5 flex items-center justify-center mb-4 text-gray-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>
        </div>
        <p class="text-gray-500 text-sm font-medium">Hộp thư trống.</p>
        <p class="text-gray-600 text-xs mt-1">Không tìm thấy thông báo hoặc tín hiệu nào phù hợp với bộ lọc.</p>
      </div>
    {/each}
  </div>

  <!-- Detail Dialog / Modal Drawer -->
  {#if selectedNotification}
    <div 
      class="absolute inset-0 bg-black/80 flex items-center justify-center p-6 z-50 backdrop-blur-md"
      onclick={() => selectedNotification = null}
      in:fade={{ duration: 150 }}
    >
      <div 
        class="bg-[#0c0c0c] border border-white/10 rounded-3xl max-w-md w-full p-6 shadow-2xl relative"
        onclick={e => e.stopPropagation()}
        in:slide={{ duration: 200 }}
      >
        <button 
          onclick={() => selectedNotification = null}
          class="absolute top-5 right-5 w-8 h-8 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center border border-white/5 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-400 hover:text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>

        <header class="mb-6">
          <span class="px-2.5 py-1 text-[9px] font-bold font-mono tracking-widest rounded-lg border uppercase {getSeverityClass(selectedNotification.type)}">
            {selectedNotification.type || 'INFO'}
          </span>
          <h3 class="text-lg font-bold text-white mt-4">CHI TIẾT TÍN HIỆU</h3>
          <span class="text-xs text-gray-500 font-mono mt-1 block">{formatTime(selectedNotification.created_at)}</span>
        </header>

        <div class="bg-white/[0.02] border border-white/5 rounded-2xl p-4 mb-6">
          <p class="text-sm text-gray-200 leading-relaxed font-medium">
            {selectedNotification.message}
          </p>
        </div>

        {#if selectedNotification.payload && Object.keys(selectedNotification.payload).length > 0}
          <div class="mb-6">
            <h4 class="text-xs font-bold text-gray-400 font-mono tracking-wider mb-2">METADATA</h4>
            <pre class="bg-black/40 border border-white/5 rounded-xl p-3 text-[10px] font-mono text-cyan-400 overflow-x-auto max-h-36 custom-scrollbar">{JSON.stringify(selectedNotification.payload, null, 2)}</pre>
          </div>
        {/if}

        <div class="flex gap-2">
          {#if selectedNotification.type === "CHAT" && selectedNotification.payload?.session_id}
            <button 
              onclick={() => {
                nanobot.openWidget("SUPPORT_INBOX", { session_id: selectedNotification.payload.session_id } as any);
                selectedNotification = null;
              }}
              class="flex-1 py-3 text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-black rounded-xl transition-all duration-300 flex items-center justify-center gap-1.5"
            >
              Mở hộp thư tư vấn
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </button>
          {:else}
            <button 
              onclick={() => selectedNotification = null}
              class="flex-1 py-3 text-xs font-bold bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-xl transition-all duration-300"
            >
              Đóng cửa sổ
            </button>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Premium Scrollbar */
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 9999px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 255, 0.2);
  }
</style>
