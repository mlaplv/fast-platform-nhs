<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { permissionState } from "$lib/state/permissions.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import PanelRight from "@lucide/svelte/icons/panel-right";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Eye from "@lucide/svelte/icons/eye";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import User from "@lucide/svelte/icons/user";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Play from "@lucide/svelte/icons/play";  import { fade, fly } from "svelte/transition";
  import ContentReviewCard from "./ui/ContentReviewCard.svelte";
  import XohiLogo from "./XohiLogo.svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import type { UserData, SystemLog } from "$lib/state/types";

  let { hideHeader = false } = $props();

  const TRUNCATE_LIMIT = 120;

  // GOD-MODE: User Selection State
  let availableUsers: UserData[] = $state([]);
  let isLoadingUsers = $state(false);
  let hasAttemptedFetchUsers = $state(false);
  let isSuperAdmin = $derived(permissionState.roles.includes("SUPER_ADMIN"));

  interface CampaignLogMetadata {
    campaign_id?: string;
    id?: string;
    role?: string;
    step?: number;
  }

  // CNS V86.7: Chat Preservation Protocol
  const UNIMPORTANT_COMMANDS = [
    "mở inbox",
    "mở brain",
    "manage skills",
    "mở index",
    "mở trang quản trị"
  ];

  const filteredLogs = $derived(nanobot.activityLogs.filter(log => {
     if (!log.message) return true;
     const msg = log.message.toLowerCase().trim();
     const src = log.source || "";
     
     // CNS V86.4: Remove redundant system/action logs entirely
     if (["ACTION", "[ACTION]", "ADMIN", "[ADMIN]", "System", "system"].includes(src)) return false;

     // Filter out ONLY specific tool-trigger commands from user source
     const isToolTrigger = UNIMPORTANT_COMMANDS.includes(msg);
     const isUserSource = (log.data?.role === "user" || src === "SẾP" || src === "Sếp");
     
     if (isUserSource && isToolTrigger) return false;

     // CNS V86.9: Filter out Bot navigation confirmations
     if (!isUserSource && msg.includes("em mở") && (msg.includes("trang quản trị") || msg.includes("brain") || msg.includes("index"))) {
        return false;
     }
     
     return true;
  }));

  function getDisplayName(log: SystemLog) {
    let src = log.source || "System";
    // CNS V86.6: Identity Resolution Protocol
    // Prioritize Data Role 'user' over Source string
    if (log.data?.role === "user" || src === "SẾP" || src === "Sếp") {
      let name = (permissionState.userName || "SẾP").toUpperCase();
      // CNS V86.6: Identity Resolution Protocol
      if (name === "XOHI") return "MASTER ⚡";
      return name;
    }

    src = src.replace(/[\[\]]/g, "");
    if (src.toUpperCase() === "XOHI" || src === "XÔ-HỈ") return "XOHI";
    return src.toUpperCase();
  }

  function isHumanSource(log: SystemLog) {
    const src = log.source || "";
    return log.data?.role === "user" || src === "SẾP" || src === "Sếp";
  }

  // Track the latest log ID for each campaign to only render one Modal per campaign
  const latestLogMap = $derived.by(() => {
    const map = new Map<string, string>();
    for (const log of filteredLogs) {
      if (log.data?.role === "assistant" || log.source === "XOHI" || log.source === "[XOHI]" || log.source === "XÔ-HỈ") {
        const metadata = log.data as CampaignLogMetadata;
        const cid = metadata?.campaign_id || metadata?.id;
        if (cid) map.set(cid, log.id);
      }
    }
    return map;
  });

  $effect(() => {
    if (isSuperAdmin && availableUsers.length === 0 && !isLoadingUsers && !hasAttemptedFetchUsers) {
      hasAttemptedFetchUsers = true;
      // Tối ưu P1: Trì hoãn việc tải danh sách user 3s để không tranh chấp connection với hydration
      setTimeout(() => fetchUsers(), 3000);
    }
  });

  async function fetchUsers() {
    if (isLoadingUsers) return;
    isLoadingUsers = true;
    try {
      const res = await apiClient.get<UserData[] | { data: UserData[] }>("/api/v1/users?limit=50");
      const list = (Array.isArray(res) ? res : res?.data || []) as UserData[];
      
      // CNS V86.8: Clean tactical list — exclude mere customers
      availableUsers = list
        .filter(u => !u.roles || u.roles.some(r => ["ADMIN", "SUPER_ADMIN", "OPERATIVE", "STAFF"].includes(r.code)))
        .map((u: UserData) => ({
          id: u.id,
          name: u.name,
          email: u.email,
        }));
    } catch (e) {
      console.error("Failed to fetch users for God-Mode", e);
    } finally {
      isLoadingUsers = false;
    }
  }

  function handleUserChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    const userId = target.value;
    nanobot.setGodModeUser(userId === "self" ? null : userId);
    nanobot.syncSessionFromDb();
  }

  function maskSensitiveData(message: string) {
    if (!message) return "";
    let masked = message;

    const LOG_DISPLAY_TRUNCATE_LIMIT = 150;
    if (masked.length > LOG_DISPLAY_TRUNCATE_LIMIT) {
      masked = masked.substring(0, LOG_DISPLAY_TRUNCATE_LIMIT) + "...";
    }

    masked = masked.replace(/(sk-[a-zA-Z0-9]{12,})/g, "sk-****[REDACTED]****");

    const sensitivePattern =
      /(password|secret|api_key|token|salt|credential|private_key|auth_key)["\s:=]+["']?([^"'\s,}] {4,})["']?/gi;
    masked = masked.replace(sensitivePattern, (match, key) => {
      return `${key}: "****[REDACTED]****"`;
    });

    return masked;
  }

  function processMessage(message: string) {
    const masked = maskSensitiveData(message);
    if (masked.length <= TRUNCATE_LIMIT) return masked;
    return masked.slice(0, TRUNCATE_LIMIT) + "...";
  }

  function isLongMessage(message: string) {
    return message.length > TRUNCATE_LIMIT;
  }

  function formatRelativeTime(date: Date | string | number) {
    let d: Date;
    if (date instanceof Date) {
      d = date;
    } else {
      d = new Date(date);
    }

    if (isNaN(d.getTime())) {
      return "---";
    }

    const now = new Date();
    const isToday =
      d.getDate() === now.getDate() &&
      d.getMonth() === now.getMonth() &&
      d.getFullYear() === now.getFullYear();

    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    const isYesterday =
      d.getDate() === yesterday.getDate() &&
      d.getMonth() === yesterday.getMonth() &&
      d.getFullYear() === yesterday.getFullYear();

    if (isToday) {
      return d.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      });
    } else if (isYesterday) {
      return "Hôm qua";
    } else {
      return d.toLocaleDateString("vi-VN", {
        day: "2-digit",
        month: "2-digit",
      });
    }
  }

  let scrollContainer: HTMLElement | undefined = $state();
  let userHasScrolledUp = $state(false);
  let isScrollAnchoring = false;
  let isProgrammaticScrolling = false;
  let lastScrollTop = 0;

  function scrollToBottom() {
    if (scrollContainer && !isScrollAnchoring) {
      isProgrammaticScrolling = true;
      scrollContainer.scrollTo({
        top: scrollContainer.scrollHeight,
        behavior: "smooth",
      });
      setTimeout(() => {
        isProgrammaticScrolling = false;
      }, 1000);
    }
  }

  async function handleScroll(e: Event) {
    if (isScrollAnchoring) return;
    const target = e.target as HTMLElement;
    const currentScrollTop = target.scrollTop;

    nanobot.setMobileScrollPosition(currentScrollTop);

    const isScrollingUp = currentScrollTop < lastScrollTop;
    lastScrollTop = currentScrollTop;

    if (isProgrammaticScrolling) return;

    const threshold = 100;

    const isAtBottom =
      target.scrollHeight - target.scrollTop - target.clientHeight < threshold;
    userHasScrolledUp = !isAtBottom;

    if (
      isScrollingUp &&
      currentScrollTop < 50 &&
      nanobot.chatPagination.hasMore &&
      !nanobot.chatPagination.isLoading
    ) {
      const prevScrollHeight = target.scrollHeight;
      const prevScrollTop = target.scrollTop;

      isScrollAnchoring = true;
      await nanobot.loadMoreMessages();

      setTimeout(() => {
        if (scrollContainer) {
          const newScrollHeight = scrollContainer.scrollHeight;
          const heightDiff = newScrollHeight - prevScrollHeight;
          scrollContainer.scrollTop = prevScrollTop + heightDiff;
        }
        isScrollAnchoring = false;
      }, 50);
    }
  }

  $effect(() => {
    if (
      filteredLogs.length > 0 &&
      !userHasScrolledUp &&
      !isScrollAnchoring &&
      !isProgrammaticScrolling
    ) {
      setTimeout(scrollToBottom, 100);
    }
  });

  async function handleClearLogs() {
    if (!isSuperAdmin) {
      nanobot.showToast(
        "CHỈ SUPER_ADMIN MỚI CÓ QUYỀN XÓA LOG HỆ THỐNG",
        "error",
      );
      return;
    }

    const hasActiveCampaign = nanobot.activityLogs.some(log => {
      const metadata = log.data as CampaignLogMetadata;
      const cid = metadata?.campaign_id || metadata?.id;
      return cid && (log.id === latestLogMap.get(cid));
    });

    let message = "Xác nhận xóa vĩnh viễn toàn bộ nhật ký chat và log hệ thống hiện tại? Hành động này không thể hoàn tác.";
    let title = "Security Purge";
    
    if (hasActiveCampaign) {
      title = "⚠️ CẢNH BÁO CHIẾN DỊCH";
      message = "Sếp đang có chiến dịch bài viết chưa hoàn tất trong log. Nếu xóa lúc này, nút 'RESUME' nhanh trên màn hình sẽ biến mất! Sếp vẫn muốn xóa chứ?";
    }

    const confirmed = await nanobot.showConfirm({
      title,
      message,
      confirmLabel: "EXECUTE_PURGE",
      cancelLabel: "ABORT_ACTION",
    });

    if (confirmed) {
      await nanobot.clearChatLogs();
    } else {
      nanobot.showToast("THAO TÁC ĐÃ ĐƯỢC Hủy bỏ AN TOÀN", "info", 3000);
    }
  }

  let isManualRefreshing = $state(false);

  async function handleManualSync() {
    isManualRefreshing = true;
    try {
      await nanobot.syncSessionFromDb();
    } finally {
      isManualRefreshing = false;
    }
  }
</script>

<style>
  .truncate-2-lines {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>

<div
  class="flex-1 h-full min-h-0 font-mono text-xs flex flex-col overflow-hidden bg-black/40 backdrop-blur-md"
>
  {#if !hideHeader}
    <div 
      class="h-12 shrink-0 border-b border-white/10 bg-black/60 backdrop-blur-xl" 
      style="z-index: {Z_INDEX_ADMIN.LAYOUT_HEADER}"
    >
      <div class="h-full flex items-center justify-between px-3">
        <div class="flex items-center gap-1.5">
          <div class="flex items-center gap-2">
            <XohiLogo size={14} class="text-neon-cyan opacity-80" />
            <span class="text-[10px] font-black tracking-widest text-white/40 ">Hearting Log</span>
          </div>

          <div class="w-[1px] h-4 bg-white/10 mx-2"></div>

          {#if isSuperAdmin}
            <div class="flex items-center gap-1.5 p-1 rounded-md hover:bg-white/5 transition-all group/usr">
              <User size={12} class="text-neon-cyan/40 group-hover/usr:text-neon-cyan/80 transition-colors" />
              <select
                onchange={handleUserChange}
                class="bg-transparent border-none text-[9px] font-mono text-white/40 group-hover/usr:text-white/80 focus:ring-0 outline-none cursor-pointer tracking-tighter max-w-[90px]"
                value={nanobot.godModeUser || "self"}
              >
                <option value="self" class="bg-black/95 text-neon-cyan font-bold ">
                  {permissionState.userName || "Identity"}
                </option>
                {#each availableUsers as user}
                  <option value={user.id} class="bg-black/95 text-white/80">
                    {user.name?.split(" ")[0] || user.email.split("@")[0].toUpperCase()}
                  </option>
                {/each}
              </select>
            </div>
          {/if}
        </div>

        <div class="flex items-center gap-1">
          <button
            onclick={handleManualSync}
            class="p-1.5 rounded-md hover:bg-white/5 transition-all group/sync active:scale-90"
            title="Force Sync"
            disabled={nanobot.chatPagination.isLoading || isManualRefreshing}
          >
            <RefreshCw
              size={14}
              strokeWidth={2.5}
              class="text-neon-cyan/40 group-hover/sync:text-neon-cyan transition-colors {isManualRefreshing ? 'animate-spin' : ''}"
            />
          </button>

          {#if isSuperAdmin}
            <button
              onclick={handleClearLogs}
              class="p-1.5 rounded-md hover:bg-red-500/10 group/trash transition-all active:scale-90"
              title="Purge Logs"
            >
              <Trash2 size={14} strokeWidth={2.5} class="text-red-500/40 group-hover/trash:text-red-500 transition-colors" />
            </button>
          {/if}
        </div>
      </div>
    </div>
  {/if}

  <div
    bind:this={scrollContainer}
    onscroll={handleScroll}
    class="flex-1 overflow-y-auto scrollbar-hide flex flex-col items-center py-4 px-3"
  >
    {#if nanobot.chatPagination.isLoading && filteredLogs.length === 0}
      <div class="flex flex-col items-center justify-center h-full gap-3 opacity-20">
         <RefreshCw size={24} class="animate-spin text-neon-cyan" />
         <span class="text-[10px] tracking-widest text-neon-cyan">SYNCING_NEURAL_LINK</span>
      </div>
    {:else if filteredLogs.length === 0}
      <div class="flex flex-col items-center justify-center h-full gap-4 text-center opacity-10">
        <Sparkles size={32} class="text-white" />
        <div class="space-y-1">
          <p class="text-[11px] font-bold tracking-[0.2em]">Neural Silence</p>
          <p class="text-[9px] tracking-tighter">Waiting for operative heartbeat...</p>
        </div>
      </div>
    {:else}
      <div class="w-full flex flex-col gap-1">
        {#each filteredLogs as log (log.id)}
          <div
            in:fade={{ duration: 150 }}
            class="group/log relative flex flex-col px-1 py-1.5 transition-all hover:bg-white/[0.03]"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-baseline gap-2">
                 <span class="text-[9px] font-black tracking-widest shrink-0 {isHumanSource(log) ? 'text-white/50' : 'text-neon-cyan/80'}">
                    [{getDisplayName(log)}]
                 </span>
                 <p class="text-[11px] leading-relaxed text-gray-400 group-hover/log:text-white/80 transition-colors break-words inline">
                    {processMessage(log.message)}
                 </p>
                 <span class="text-[7px] font-mono text-white/10 ml-auto tabular-nums">
                    {formatRelativeTime(log.timestamp)}
                 </span>
              </div>

              {#if (log.data?.role === "assistant" || log.source === "XOHI" || log.source === "[XOHI]" || log.source === "XÔ-HỈ")}
                {@const cid = log.data?.campaign_id || (log.data as any)?.id}
                {#if cid && log.id === latestLogMap.get(cid)}
                  <div class="mt-3 p-3 rounded border border-neon-cyan/20 bg-neon-cyan/5 flex items-center justify-between gap-3 animate-in fade-in slide-in-from-bottom-2">
                    <div class="flex items-center gap-2 min-w-0">
                      <div class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shrink-0"></div>
                      <span class="text-[10px] font-bold text-neon-cyan truncate ">Duyệt Bước: {log.data?.step || 1}</span>
                    </div>
                    <button
                      onclick={() => nanobot.resumeCampaign(log)}
                      class="px-4 py-1.5 bg-neon-cyan text-black font-black text-[10px] rounded hover:bg-white transition-all active:scale-95 shadow-[0_0_15px_rgba(0,255,255,0.3)] tracking-tighter"
                    >
                      Resume
                    </button>
                  </div>
                {/if}
              {/if}
            </div>
            
            <button
               onclick={() => nanobot.showFullLog(log)}
               class="absolute top-2 right-2 opacity-0 group-hover/log:opacity-100 p-1 rounded hover:bg-white/10 text-white/40 hover:text-white transition-all"
            >
               <Eye size={12} />
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  {#if userHasScrolledUp}
    <button
      onclick={scrollToBottom}
      transition:fade
      class="absolute bottom-6 right-6 p-2 rounded-full bg-neon-cyan text-black shadow-lg shadow-neon-cyan/20 hover:scale-110 transition-transform active:scale-90"
    >
      <PanelRight size={16} class="rotate-90" />
    </button>
  {/if}
</div>
