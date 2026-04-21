<script lang="ts">
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import MessageCircle from "lucide-svelte/icons/message-circle";
  import Search from "lucide-svelte/icons/search";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";

  // Sub-components (Elite V2.2 Refactored < 500 lines)
  import SupportChatList from "./SupportChatList.svelte";
  import SupportChatView from "./SupportChatView.svelte";
  import type { SessionSummary } from "./SupportChatList.svelte";

  interface MessageView {
    id: string; role: "user" | "assistant"; content: string; intent: string | null; created_at: string | null; is_revoked?: boolean;
  }
  interface SessionDetail {
    session_id: string; customer_name: string | null; customer_phone: string | null; product_slug: string | null; messages: MessageView[]; is_takeover: boolean; is_online: boolean;
  }

  let { isWidget = false } = $props();
  const nanobot = useNanobot();

  let sessions = $state<SessionSummary[]>([]);
  let totalSessions = $state(0);
  let isLoading = $state(true);
  let selectedSessionId = $state<string | null>(null);
  let selectedSessionDetail = $state<SessionDetail | null>(null);
  let isTakeover = $state(false);
  let manualMessage = $state("");
  let isSending = $state(false);
  let searchInput = $state("");
  let searchTerm = $state("");
  let quotedMessage = $state<MessageView | null>(null);
  let sidebarWidth = $state(320);
  let isResizing = $state(false);

  // Sync Global Search & Refresh
  $effect(() => {
    if (nanobot.supportSearchTerm !== searchTerm) {
      searchTerm = nanobot.supportSearchTerm;
      loadSessions();
    }
  });

  $effect(() => {
    if (nanobot.supportRefreshToggle > 0) {
      loadSessions();
      if (selectedSessionId) selectSession(selectedSessionId);
    }
  });

  async function loadSessions() {
    isLoading = true;
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append("search", searchTerm);
      const res = await apiClient.get<{ data: SessionSummary[]; total: number }>(`/api/v1/admin/support/inbox/sessions?${params.toString()}`);
      sessions = res.data;
      totalSessions = res.total;
      nanobot.setActiveSupportSessionCount(res.total);
    } finally { isLoading = false; }
  }

  async function selectSession(id: string) {
    selectedSessionId = id;
    try {
      const res = await apiClient.get<SessionDetail>(`/api/v1/admin/support/inbox/sessions/${id}`);
      selectedSessionDetail = res;
      isTakeover = res.is_takeover;
    } catch { selectedSessionDetail = null; }
  }

  async function toggleTakeover() {
    if (!selectedSessionId) return;
    try {
      const res = await apiClient.post<{ is_takeover: boolean }>(`/api/v1/admin/support/inbox/sessions/${selectedSessionId}/takeover`);
      isTakeover = res.is_takeover;
      nanobot.showToast(isTakeover ? "Đã chặn mồm Helen." : "Đã thả xích Helen.", "success");
    } catch { nanobot.showToast("Lỗi hệ thống", "error"); }
  }

  async function sendManualMessage() {
    if (!selectedSessionId || !manualMessage.trim() || isSending) return;
    isSending = true;
    try {
      await apiClient.post(`/api/v1/admin/support/inbox/sessions/${selectedSessionId}/message`, {
        message: quotedMessage ? `> ${quotedMessage.role === 'assistant' ? 'Helen AI' : 'Khách'}: ${quotedMessage.content}\n\n${manualMessage}` : manualMessage
      });
      manualMessage = ""; quotedMessage = null;
      await selectSession(selectedSessionId);
    } finally { isSending = false; }
  }

  async function revokeMessage(msgId: string) {
    if (!selectedSessionId) return;
    try {
      await apiClient.post(`/api/v1/admin/support/inbox/sessions/${selectedSessionId}/messages/${msgId}/revoke`);
      await selectSession(selectedSessionId);
    } catch { nanobot.showToast("Lỗi thu hồi", "error"); }
  }

  function handleSearch(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    searchInput = val;
    setTimeout(() => { searchTerm = val; loadSessions(); }, 500);
  }

  onMount(() => { loadSessions(); });
</script>

<div class="support-inbox h-full flex flex-col {!isWidget ? 'bg-obsidian-900/40 backdrop-blur-xl border border-white/5 rounded-2xl' : 'bg-transparent'} overflow-hidden">
  {#if !isWidget}
    <header class="p-6 border-b border-white/10 flex items-center justify-between bg-white/5 shrink-0">
      <div>
        <h2 class="text-xl font-bold flex items-center gap-3"><MessageCircle class="w-6 h-6 text-cyan-400" /> Helen AI Inbox <span class="text-xs px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded-full border border-cyan-500/30">{totalSessions} Phiên</span></h2>
      </div>
      <div class="flex items-center gap-4">
        <div class="relative w-64"><Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" /><input type="text" placeholder="Tìm kiếm..." class="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-cyan-500/50" bind:value={searchInput} oninput={handleSearch} /></div>
        <button onclick={loadSessions} class="p-2 hover:bg-white/10 rounded-lg"><RefreshCw class="w-5 h-5 text-white/60 {isLoading ? 'animate-spin' : ''}" /></button>
      </div>
    </header>
  {/if}

  <div class="flex-1 flex overflow-hidden min-h-0 min-w-0 {isResizing ? 'select-none cursor-col-resize' : ''}" 
    onmousemove={(e) => { if (isResizing) sidebarWidth = Math.max(200, Math.min(600, e.clientX - 60)); }} 
    onmouseup={() => isResizing = false} onmouseleave={() => isResizing = false} role="presentation">
    
    <div style:width="{sidebarWidth}px" class="shrink-0 flex">
      <SupportChatList {sessions} {selectedSessionId} {isLoading} onSelect={selectSession} />
    </div>

    <!-- Divider -->
    <div class="w-px shrink-0 relative bg-white/10 hover:bg-cyan-500/50 cursor-col-resize z-10 transition-colors" onmousedown={() => isResizing = true} role="separator">
      <!-- Mở rộng vùng grab để dễ kéo thả -->
      <div class="absolute inset-y-0 -inset-x-2"></div>
    </div>

    <SupportChatView 
      session={selectedSessionDetail} 
      isLoading={isLoading} 
      {isTakeover} {isSending} {manualMessage} {quotedMessage}
      onToggleTakeover={toggleTakeover}
      onSendMessage={sendManualMessage}
      onRevokeMessage={revokeMessage}
      onCopyMessage={(c) => { navigator.clipboard.writeText(c); nanobot.showToast("Đã copy", "success"); }}
      onQuoteMessage={(m) => { quotedMessage = m; }}
      onClearQuote={() => quotedMessage = null}
      onUpdateMessage={(v) => manualMessage = v}
    />
  </div>
</div>
