<script lang="ts">
  import { onMount } from "svelte";
  import { fade, slide } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import User from "lucide-svelte/icons/user";
  import Phone from "lucide-svelte/icons/phone";
  import Clock from "lucide-svelte/icons/clock";
  import MessageCircle from "lucide-svelte/icons/message-circle";
  import Search from "lucide-svelte/icons/search";
  import ChevronRight from "lucide-svelte/icons/chevron-right";
  import Tag from "lucide-svelte/icons/tag";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Lock from "lucide-svelte/icons/lock";
  import Unlock from "lucide-svelte/icons/unlock";
  import Send from "lucide-svelte/icons/send";
  import ShieldAlert from "lucide-svelte/icons/shield-alert";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import RotateCcw from "lucide-svelte/icons/rotate-ccw";
  import Copy from "lucide-svelte/icons/copy";
  import Quote from "lucide-svelte/icons/quote";
  import X from "lucide-svelte/icons/x";
  import MoreHorizontal from "lucide-svelte/icons/more-horizontal";

  interface SessionSummary {
    session_id: string;
    customer_name: string | null;
    customer_phone: string | null;
    product_slug: string | null;
    message_count: number;
    last_intent: string | null;
    last_message_at: string | null;
    is_takeover?: boolean;
    is_high_intent?: boolean;
    is_online?: boolean;
  }

  interface MessageView {
    id: string;
    role: "user" | "assistant";
    content: string;
    intent: string | null;
    created_at: string | null;
    is_revoked?: boolean;
  }

  interface SessionDetail {
    session_id: string;
    customer_name: string | null;
    customer_phone: string | null;
    product_slug: string | null;
    messages: MessageView[];
    is_takeover: boolean;
    is_online: boolean;
  }

  let { isWidget = false } = $props();

  let sessions = $state<SessionSummary[]>([]);
  let totalSessions = $state(0);
  let isLoading = $state(true);
  let selectedSessionId = $state<string | null>(null);
  let selectedSessionDetail = $state<SessionDetail | null>(null);
  let isDetailLoading = $state(false);
  let isTakeover = $state(false);
  let manualMessage = $state("");
  let isSending = $state(false);
  let searchInput = $state("");
  let searchTerm = $state("");
  let sidebarWidth = $state(320);
  let isResizing = $state(false);
  let chatScrollRef = $state<HTMLDivElement | null>(null);
  let quotedMessage = $state<MessageView | null>(null);

  // Auto-scroll logic
  $effect(() => {
    if (selectedSessionDetail && chatScrollRef) {
      // Small timeout to ensure DOM is rendered before scrolling
      setTimeout(() => {
        chatScrollRef?.scrollTo({
          top: chatScrollRef.scrollHeight,
          behavior: "smooth"
        });
      }, 50);
    }
  });

  // Sync Global Search & Refresh (Elite V2.2)
  $effect(() => {
    const term = nanobot.supportSearchTerm;
    if (term !== searchTerm) {
      searchTerm = term;
      loadSessions();
    }
  });

  $effect(() => {
    if (nanobot.supportRefreshToggle > 0) {
      loadSessions();
      // V86.2: Auto-refresh current chat messages if active
      if (selectedSessionId) {
        selectSession(selectedSessionId);
      }
    }
  });

  function startResizing() {
    isResizing = true;
  }

  function handleMouseMove(e: MouseEvent) {
    if (!isResizing) return;
    const newWidth = e.clientX - 60; // Offset for potential sidebar if any, but simplified
    if (newWidth > 200 && newWidth < 600) {
      sidebarWidth = newWidth;
    }
  }

  function stopResizing() {
    isResizing = false;
  }

  function isHighIntent(session: SessionSummary): boolean {
    return !!session.is_high_intent;
  }

  async function loadSessions() {
    isLoading = true;
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append("search", searchTerm);
      const res = await apiClient.get<{ data: SessionSummary[]; total: number }>(
        `/api/v1/admin/support/inbox/sessions?${params.toString()}`
      );
      sessions = res.data;
      totalSessions = res.total;
      nanobot.setActiveSupportSessionCount(res.total);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      nanobot.addLog(`[ADMIN] Load sessions failed: ${msg}`, "SYS", "error");
    } finally {
      isLoading = false;
    }
  }

  async function selectSession(id: string) {
    selectedSessionId = id;
    isDetailLoading = true;
    try {
      const res = await apiClient.get<SessionDetail & { is_takeover: boolean }>(`/api/v1/admin/support/inbox/sessions/${id}`);
      selectedSessionDetail = res;
      isTakeover = res.is_takeover;
      // V2.2: Sync is_online for UI
      const sessionIdx = sessions.findIndex(s => s.session_id === id);
      if (sessionIdx !== -1) sessions[sessionIdx].is_online = res.is_online;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      nanobot.addLog(`[ADMIN] Load session detail failed: ${msg}`, "SYS", "error");
      selectedSessionDetail = null;
    } finally {
      isDetailLoading = false;
    }
  }

  function formatDate(dateStr: string | null) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "2-digit",
    });
  }

  let searchTimer: ReturnType<typeof setTimeout> | undefined;
  async function toggleTakeover() {
    if (!selectedSessionId) return;
    try {
      const res = await apiClient.post<{ is_takeover: boolean }>(`/api/v1/admin/support/inbox/sessions/${selectedSessionId}/takeover`);
      isTakeover = res.is_takeover;
      nanobot.showToast(isTakeover ? "Đã chặn mồm Helen. Sếp toàn quyền điều khiển!" : "Đã trả quyền cho Helen AI.", "success");
    } catch (err: unknown) {
      nanobot.showToast("Không thể thay đổi trạng thái AI", "error");
    }
  }

  async function sendManualMessage() {
    if (!selectedSessionId || !manualMessage.trim() || isSending) return;
    
    isSending = true;
    try {
      await apiClient.post(`/api/v1/admin/support/inbox/sessions/${selectedSessionId}/message`, {
        message: quotedMessage 
          ? `> ${quotedMessage.role === 'assistant' ? 'Helen AI' : 'Khách'}: ${quotedMessage.content}\n\n${manualMessage}`
          : manualMessage
      });
      manualMessage = "";
      quotedMessage = null;
      // Refresh will be triggered by Pulse, but we fetch immediately for speed
      await selectSession(selectedSessionId);
    } catch (err: unknown) {
      nanobot.showToast("Gửi tin nhắn thất bại", "error");
    } finally {
      isSending = false;
    }
  }

  async function revokeMessage(msgId: string) {
    if (!selectedSessionId || !msgId) return;
    try {
      const res = await apiClient.post<{ is_revoked: boolean }>(
        `/api/v1/admin/support/inbox/sessions/${selectedSessionId}/messages/${msgId}/revoke`
      );
      nanobot.showToast(res.is_revoked ? "Đã thu hồi tin nhắn" : "Đã hoàn tác thu hồi", "success");
      // Refresh to sync state
      await selectSession(selectedSessionId);
    } catch (err: unknown) {
      nanobot.showToast("Không thể thực hiện thu hồi", "error");
    }
  }
  
  function copyMessage(content: string) {
    navigator.clipboard.writeText(content);
    nanobot.showToast("Đã copy vào bộ nhớ tạm", "success");
  }

  function quoteMessage(msg: MessageView) {
    quotedMessage = msg;
    // Focus the textarea
    const textarea = document.querySelector('textarea');
    textarea?.focus();
  }

  function clearQuote() {
    quotedMessage = null;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendManualMessage();
    }
  }

  function handleSearch(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    searchInput = val;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchTerm = val;
      loadSessions();
    }, 500);
  }

  onMount(() => {
    loadSessions();
  });
</script>

<div class="support-inbox h-full flex flex-col {!isWidget ? 'bg-obsidian-900/40 backdrop-blur-xl border border-white/5 rounded-2xl' : 'bg-transparent'} overflow-hidden">
  {#if !isWidget}
    <!-- Header -->
    <header class="p-6 border-b border-white/10 flex items-center justify-between bg-white/5 shrink-0">
      <div>
        <h2 class="text-xl font-bold flex items-center gap-3">
          <MessageCircle class="w-6 h-6 text-cyan-400" />
          Helen AI Inbox
          <span class="text-xs px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded-full border border-cyan-500/30">
            {totalSessions} Phiên
          </span>
        </h2>
        <p class="text-white/40 text-sm mt-1">Lịch sử hội thoại Agentic đã được giải mã</p>
      </div>
      
      <div class="flex items-center gap-4">
        <div class="relative w-64">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input 
            type="text" 
            placeholder="Tìm khách hàng, SĐT..." 
            class="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-cyan-500/50 transition-colors"
            oninput={handleSearch}
            bind:value={searchInput}
          />
        </div>
        <button 
          onclick={loadSessions}
          class="p-2 hover:bg-white/10 rounded-lg transition-colors"
          title="Làm mới"
        >
          <RefreshCw class="w-5 h-5 text-white/60 {isLoading ? 'animate-spin' : ''}" />
        </button>
      </div>
    </header>
  {/if}

  <div 
    class="flex-1 flex overflow-hidden {isResizing ? 'select-none cursor-col-resize' : ''}"
    onmousemove={handleMouseMove}
    onmouseup={stopResizing}
    onmouseleave={stopResizing}
    role="presentation"
  >
    <!-- Sessions List -->
    <aside 
      class="border-r border-white/10 overflow-y-auto custom-scrollbar flex flex-col shrink-0" 
      style:width="{sidebarWidth}px"
    >
      {#if isLoading && sessions.length === 0}
        <div class="p-8 text-center text-white/20">Đang tải phiên...</div>
      {:else if sessions.length === 0}
        <div class="p-8 text-center text-white/20">Không tìm thấy hội thoại nào</div>
      {:else}
        {#each sessions as session (session.session_id)}
          <button 
            onclick={() => selectSession(session.session_id)}
            class="w-full text-left p-4 border-b border-white/5 hover:bg-white/5 transition-all relative {selectedSessionId === session.session_id ? 'bg-cyan-500/10 border-l-2 border-l-cyan-500' : ''} {isHighIntent(session) ? 'high-intent-glow' : ''}"
          >
            {#if isHighIntent(session)}
              <div class="absolute top-2 right-2 flex items-center gap-1.5 p-1 rounded-md bg-cyan-500/10 border border-cyan-500/20 anim-pulse-cyan">
                {#if session.is_takeover}
                  <span class="text-[7px] font-bold px-1 py-0.5 bg-yellow-500/20 text-yellow-500 rounded border border-yellow-500/30 uppercase tracking-tighter mr-1 anim-pulse">AI SILENCED</span>
                {/if}
                <span class="flex h-2 w-2">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
                <span class="text-[8px] font-black text-cyan-400 uppercase tracking-widest leading-none">High Intent</span>
              </div>
            {:else if session.is_takeover}
              <div class="absolute top-2 right-2">
                <span class="text-[7px] font-bold px-1 py-0.5 bg-yellow-500/20 text-yellow-500 rounded border border-yellow-500/30 uppercase tracking-tighter">AI SILENCED</span>
              </div>
            {/if}
            <div class="flex justify-between items-start mb-1">
              <span class="font-bold truncate mr-2 transition-all duration-300 {isHighIntent(session) ? 'text-cyan-400 drop-shadow-[0_0_10px_rgba(6,182,212,0.4)]' : 'text-white/90'}">
                <span class="inline-block w-2 h-2 rounded-full mr-1.5 {session.is_online ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.6)]' : 'bg-white/20'}" title={session.is_online ? 'Online' : 'Offline'}></span>
                {session.customer_name || "Khách ẩn danh"}
              </span>
              <span class="text-[10px] text-white/30 whitespace-nowrap">
                {formatDate(session.last_message_at)}
              </span>
            </div>
            
            <div class="flex items-center gap-3 text-xs text-white/50">
              {#if session.customer_phone}
                <span class="flex items-center gap-1">
                  <Phone class="w-3 h-3" /> {session.customer_phone}
                </span>
              {/if}
              <span class="flex items-center gap-1">
                <MessageCircle class="w-3 h-3" /> {session.message_count}
              </span>
            </div>
            
            {#if session.last_intent}
              <div class="mt-2 flex gap-1">
                <span class="text-[9px] px-1.5 py-0.5 bg-white/5 rounded border border-white/10 uppercase tracking-tighter text-white/60">
                  {session.last_intent}
                </span>
              </div>
            {/if}
          </button>
        {/each}
      {/if}
    </aside>

    <!-- Resizable Divider -->
    <div 
      class="w-1 hover:w-1.5 transition-all bg-white/5 hover:bg-cyan-500/50 cursor-col-resize shrink-0 active:bg-cyan-500" 
      onmousedown={startResizing}
      role="separator"
      aria-orientation="vertical"
    ></div>

    <!-- Chat View -->
    <main class="flex-1 flex flex-col bg-black/20 overflow-hidden select-text">
      {#if selectedSessionDetail}
        <!-- Session Meta -->
        <div class="p-4 bg-white/5 border-b border-white/10 flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center font-bold text-white">
              {(selectedSessionDetail.customer_name || "K")[0]}
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="font-bold text-white/90">{selectedSessionDetail.customer_name || "Khách ẩn danh"}</h3>
                {#if selectedSessionDetail.is_online}
                  <span class="text-[9px] px-1.5 py-0.5 bg-green-500/20 text-green-400 rounded-full border border-green-500/30 font-bold animate-pulse">ONLINE</span>
                {:else}
                  <span class="text-[9px] px-1.5 py-0.5 bg-white/5 text-white/40 rounded-full border border-white/10 font-bold">OFFLINE</span>
                {/if}
              </div>
              <div class="text-xs text-white/40 flex gap-3">
                {#if selectedSessionDetail.customer_phone}
                  <span class="flex items-center gap-1"><Phone class="w-3 h-3" /> {selectedSessionDetail.customer_phone}</span>
                {/if}
                {#if selectedSessionDetail.product_slug}
                  <span class="flex items-center gap-1"><Tag class="w-3 h-3" /> SP: {selectedSessionDetail.product_slug}</span>
                {/if}
              </div>
            </div>
            
            <div class="flex items-center gap-4">
              <button 
                onclick={toggleTakeover}
                class="flex items-center gap-2 px-3 py-1.5 {isTakeover ? 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30' : 'bg-white/5 text-white/40 border-white/10'} border rounded-lg text-xs font-bold transition-all hover:scale-105 active:scale-95"
              >
                {#if isTakeover}
                  <Lock class="w-3.5 h-3.5" /> Chặn mồm Helen
                {:else}
                  <Unlock class="w-3.5 h-3.5" /> Thả xích Helen
                {/if}
              </button>
              <div class="text-[10px] text-white/20 font-mono">ID: {selectedSessionDetail.session_id.slice(0,8)}</div>
            </div>
          </div>
        </div>

        <!-- Messages Area -->
        <div 
          class="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar"
          bind:this={chatScrollRef}
        >
          {#each selectedSessionDetail.messages as msg}
            <div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'} group/msg">
              <div class="max-w-[80%] relative group">
                <div class="transition-all {msg.role === 'user' ? 'bg-cyan-600/20 border border-cyan-500/30 text-white/90 rounded-2xl rounded-tr-none' : 'bg-white/10 border border-white/10 text-white/80 rounded-2xl rounded-tl-none'} p-4 shadow-xl {msg.is_revoked ? 'opacity-40 grayscale' : ''}">
                  <div class="text-[9px] uppercase tracking-widest text-white/30 mb-1 flex justify-between gap-10">
                    <span>{msg.role === 'user' ? 'KHÁCH HÀNG' : 'HELEN AI'}</span>
                    <div class="flex items-center gap-2">
                      {#if msg.is_revoked}
                        <span class="text-red-400 font-bold">[ĐÃ THU HỒI]</span>
                      {/if}
                      <span>{formatDate(msg.created_at)}</span>
                    </div>
                  </div>
                  
                  {#if msg.is_revoked}
                    <p class="text-sm italic text-white/40 line-through select-none">{msg.content}</p>
                  {:else}
                    <p class="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  {/if}

                  {#if msg.intent}
                    <div class="mt-2 text-[8px] text-cyan-400/50 uppercase font-mono">INTENT: {msg.intent}</div>
                  {/if}
                </div>

                <!-- Professional Zalo-style Message Actions (Positioned @ Bottom Corner) -->
                <div class="absolute {msg.role === 'user' ? 'right-full mr-2' : 'left-full ml-2'} bottom-0 opacity-0 group-hover:opacity-100 transition-all duration-300 z-20 hover:scale-105 active:scale-95">
                  <div class="flex items-center gap-0.5 bg-obsidian-800/95 backdrop-blur-xl border border-white/10 rounded-full p-0.5 shadow-[0_8px_32px_rgba(0,0,0,0.5)] overflow-hidden">
                    <button 
                      onclick={() => quoteMessage(msg)}
                      class="p-2 hover:bg-white/10 text-white/40 hover:text-cyan-400 transition-colors rounded-full"
                      title="Trích dẫn"
                    >
                      <Quote class="w-3 h-3" />
                    </button>
                    <button 
                      onclick={() => copyMessage(msg.content)}
                      class="p-2 hover:bg-white/10 text-white/40 hover:text-white transition-colors rounded-full"
                      title="Copy tin nhắn"
                    >
                      <Copy class="w-3 h-3" />
                    </button>
                    <div class="w-px h-3 bg-white/10 mx-0.5"></div>
                    <button 
                      onclick={() => revokeMessage(msg.id)}
                      class="p-2 hover:bg-red-500/20 text-white/40 hover:text-red-400 transition-colors rounded-full"
                      title={msg.is_revoked ? "Hoàn tác thu hồi" : "Thu hồi tin nhắn"}
                    >
                      {#if msg.is_revoked}
                        <RotateCcw class="w-3 h-3" />
                      {:else}
                        <Trash2 class="w-3 h-3" />
                      {/if}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>

        <!-- Chat Input with Quote Preview (Elite V2.2) -->
        <div class="p-4 bg-black/40 border-t border-white/10 backdrop-blur-xl shrink-0 relative">
          {#if quotedMessage}
            <div 
              transition:slide={{ axis: 'y' }}
              class="absolute bottom-full left-0 right-0 bg-white/5 backdrop-blur-2xl border-t border-white/10 p-3 flex items-center justify-between z-10"
            >
              <div class="flex items-center gap-3 overflow-hidden">
                <div class="w-1 h-8 bg-cyan-500 rounded-full shrink-0"></div>
                <div class="flex flex-col min-w-0">
                  <span class="text-[10px] font-bold text-cyan-400 uppercase tracking-tighter">Đang trả lời {quotedMessage.role === 'assistant' ? 'Helen AI' : 'Khách hàng'}</span>
                  <p class="text-xs text-white/50 truncate max-w-md">{quotedMessage.content}</p>
                </div>
              </div>
              <button 
                onclick={clearQuote}
                class="p-2 hover:bg-white/10 rounded-full text-white/40 hover:text-white transition-colors"
              >
                <X class="w-4 h-4" />
              </button>
            </div>
          {/if}

          {#if isTakeover}
            <div class="mb-2 flex items-center gap-2 text-[10px] text-yellow-500 font-bold uppercase tracking-widest animate-pulse">
              <ShieldAlert class="w-3 h-3" /> Chế độ chỉ huy: Toàn quyền điều khiển thủ công
            </div>
          {/if}
          <div class="relative group">
            <textarea
              bind:value={manualMessage}
              onkeydown={handleKeydown}
              placeholder={isTakeover ? "Nhấn Enter để gửi tin nhắn trực tiếp cho khách..." : "Bật 'Chặn mồm' để chát trực tiếp với khách..."}
              disabled={!isTakeover}
              class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40 transition-all resize-none min-h-[50px] max-h-[150px] {isTakeover ? 'opacity-100' : 'opacity-40 cursor-not-allowed'}"
            ></textarea>
            <button 
              onclick={sendManualMessage}
              disabled={!isTakeover || !manualMessage.trim() || isSending}
              class="absolute right-4 bottom-4 p-2 bg-cyan-500/20 text-cyan-400 rounded-lg border border-cyan-500/30 hover:bg-cyan-500/40 transition-all disabled:opacity-0 active:scale-95"
            >
              <Send class="w-4 h-4" />
            </button>
          </div>
          <div class="mt-2 text-[9px] text-white/20 flex justify-between">
            <span>Shift + Enter để xuống dòng</span>
            {#if isSending}
              <span class="text-cyan-400 animate-pulse">Đang gửi...</span>
            {/if}
          </div>
        </div>
      {:else if isDetailLoading}
        <div class="flex-1 flex flex-col items-center justify-center text-white/20">
          <RefreshCw class="w-10 h-10 animate-spin mb-4" />
          <p>Đang giải mã nội dung...</p>
        </div>
      {:else}
        <div class="flex-1 flex flex-col items-center justify-center text-white/10 p-12 text-center">
          <MessageCircle class="w-20 h-20 mb-6 opacity-20" />
          <h3 class="text-lg font-bold text-white/20">Chọn một hội thoại để xem chi tiết</h3>
          <p class="max-w-xs mt-2">Dữ liệu được giải mã bảo mật 100% tại phía server Elite.</p>
        </div>
      {/if}
    </main>
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  .high-intent-glow {
    background: linear-gradient(90deg, rgba(6, 182, 212, 0.15) 0%, transparent 100%);
    box-shadow: inset 0 0 20px rgba(6, 182, 212, 0.2), 0 0 15px rgba(6, 182, 212, 0.15);
    border-right: 3px solid rgba(6, 182, 212, 0.6);
    z-index: 1;
    position: relative;
  }

  .high-intent-glow:hover {
    background: linear-gradient(90deg, rgba(6, 182, 212, 0.15) 0%, transparent 100%);
    box-shadow: inset 0 0 20px rgba(6, 182, 212, 0.2);
  }

  @keyframes pulse-cyan {
    0% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0.4); }
    70% { box-shadow: 0 0 0 6px rgba(6, 182, 212, 0); }
    100% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0); }
  }

  .anim-pulse-cyan {
    animation: pulse-cyan 2s infinite;
  }
</style>
