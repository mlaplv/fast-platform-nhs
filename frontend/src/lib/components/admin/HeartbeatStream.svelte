<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { permissionState } from "$lib/state/permissions.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import PanelRight from "lucide-svelte/icons/panel-right";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Eye from "lucide-svelte/icons/eye";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import User from "lucide-svelte/icons/user";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Play from "lucide-svelte/icons/play";
  import { fade, fly } from "svelte/transition";
  import ContentReviewCard from "./ui/ContentReviewCard.svelte";

  let { hideHeader = false } = $props();

  const TRUNCATE_LIMIT = 120;

  // GOD-MODE: User Selection State
  let availableUsers: { id: string; name: string; email: string }[] = $state(
    [],
  );
  let isLoadingUsers = $state(false);
  let hasAttemptedFetchUsers = $state(false);
  let isSuperAdmin = $derived(permissionState.roles.includes("SUPER_ADMIN"));

    // Track the latest log ID for each campaign to only render one Modal per campaign
    let latestLogIdsPerCampaign = $derived(() => {
      const map = new Map<string, string>();
      for (const log of nanobot.activityLogs) {
         if (log.data?.role === "assistant" || log.source === "XOHI" || log.source === "[XOHI]" || log.source === "XÔ-HỈ") {
            if (log.data?.campaign_id) {
               map.set(log.data.campaign_id, log.id);
            }
         }
      }
      return map;
    });

  $effect(() => {
    if (isSuperAdmin && availableUsers.length === 0 && !isLoadingUsers && !hasAttemptedFetchUsers) {
      hasAttemptedFetchUsers = true;
      fetchUsers();
    }
  });

  async function fetchUsers() {
    if (isLoadingUsers) return;
    isLoadingUsers = true;
    try {
      const res = await apiClient.get<any>("/api/v1/users?limit=50");
      const list = Array.isArray(res) ? res : res.data || [];
      availableUsers = list.map((u: any) => ({
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

    // Truncate ultra-long messages (e.g., full article drafts) for the sidebar UI
    const LOG_DISPLAY_TRUNCATE_LIMIT = 150;
    if (masked.length > LOG_DISPLAY_TRUNCATE_LIMIT) {
      masked = masked.substring(0, LOG_DISPLAY_TRUNCATE_LIMIT) + "...";
    }

    // API Keys (sk-...)
    masked = masked.replace(/(sk-[a-zA-Z0-9]{12,})/g, "sk-****[REDACTED]****");

    // Generic Sensitive Keys in JSON/KV (password, secret, token, etc)
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

  function formatRelativeTime(date: Date) {
    const now = new Date();
    const isToday =
      date.getDate() === now.getDate() &&
      date.getMonth() === now.getMonth() &&
      date.getFullYear() === now.getFullYear();

    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    const isYesterday =
      date.getDate() === yesterday.getDate() &&
      date.getMonth() === yesterday.getMonth() &&
      date.getFullYear() === yesterday.getFullYear();

    if (isToday) {
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      });
    } else if (isYesterday) {
      return "Hôm qua";
    } else {
      return date.toLocaleDateString("vi-VN", {
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
      // Reset programmatic flag after smooth scroll duration
      setTimeout(() => {
        isProgrammaticScrolling = false;
      }, 1000);
    }
  }

  async function handleScroll(e: Event) {
    if (isScrollAnchoring) return;
    const target = e.target as HTMLElement;
    const currentScrollTop = target.scrollTop;

    // Update global scroll position for adaptive UI (V60.2)
    nanobot.setMobileScrollPosition(currentScrollTop);

    const isScrollingUp = currentScrollTop < lastScrollTop;
    lastScrollTop = currentScrollTop;

    if (isProgrammaticScrolling) return;

    const threshold = 100;

    // Bottom detection
    const isAtBottom =
      target.scrollHeight - target.scrollTop - target.clientHeight < threshold;
    userHasScrolledUp = !isAtBottom;

    // Top detection for Infinite Scroll (Zalo style)
    // CRITICAL: Only trigger if scrolling UP and not programmatic
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

      // Post-load Anchoring: Adjust scroll position to account for new content
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
    // Auto-scroll to bottom on new logs if not currently scrolled up OR anchoring
    if (
      nanobot.activityLogs.length > 0 &&
      !userHasScrolledUp &&
      !isScrollAnchoring &&
      !isProgrammaticScrolling
    ) {
      // Small timeout to ensure DOM has updated
      setTimeout(scrollToBottom, 100);
    }
  });

  // Force scroll down on mount to ensure logs are visible
  $effect(() => {
    // Scroll intentionally on mount or updates appropriately
  });

  async function handleClearLogs() {
    if (!isSuperAdmin) {
      nanobot.showToast(
        "CHỈ SUPER_ADMIN MỚI CÓ QUYỀN XÓA LOG HỆ THỐNG",
        "error",
      );
      return;
    }

    const confirmed = await nanobot.showConfirm({
      title: "Security Purge",
      message:
        "Xác nhận xóa vĩnh viễn toàn bộ nhật ký chat và log hệ thống hiện tại? Hành động này không thể hoàn tác.",
      confirmLabel: "EXECUTE_PURGE",
      cancelLabel: "ABORT_ACTION",
    });

    if (confirmed) {
      await nanobot.clearChatLogs();
    } else {
      nanobot.showToast("THAO TÁC ĐÃ ĐƯỢC HỦY BỎ AN TOÀN", "info", 3000);
    }
  }
</script>

<div
  class="flex-1 h-full min-h-0 font-mono text-xs flex flex-col overflow-hidden"
>
  {#if !hideHeader}
    <div class="h-12 shrink-0 border-b border-white/5 bg-black/20 backdrop-blur-sm">
      <!-- Neural Control Bar (Minimalist Icon Row) -->
      <div class="h-full flex items-center justify-between px-5">
        <!-- Left Group: Branding & View Controls -->
        <div class="flex items-center gap-1">
          <!-- Logo Restored (Static) -->
          <div class="flex items-center gap-1.5 px-0.5 mr-1">
            <div
              class="w-5 h-5 flex items-center justify-center rounded-sm bg-neon-cyan/5"
            >
              <Sparkles size={12} class="text-neon-cyan/40" />
            </div>
            <span
              class="text-[9px] font-black tracking-tighter text-white/30 uppercase"
              >Xohi Hearting</span
            >
          </div>

          <div class="w-[1px] h-4 bg-white/5 mx-1"></div>

          {#if isSuperAdmin}
            <div
              class="flex items-center gap-1.5 p-1 rounded-md hover:bg-white/5 transition-all group/usr"
            >
              <User
                size={12}
                class="text-neon-cyan/30 group-hover/usr:text-neon-cyan/60 transition-colors"
              />
              <select
                onchange={handleUserChange}
                class="bg-transparent border-none text-[9px] font-mono text-white/30 group-hover/usr:text-white/60 focus:ring-0 outline-none cursor-pointer uppercase tracking-tighter max-w-[80px]"
                value={nanobot.godModeUser || "self"}
              >
                <option
                  value="self"
                  class="bg-black/95 text-neon-cyan font-bold">SELF</option
                >
                {#each availableUsers as user}
                  <option value={user.id} class="bg-black/95 text-white/80">
                    {user.name?.split(" ")[0] ||
                      user.email.split("@")[0].toUpperCase()}
                  </option>
                {/each}
              </select>
            </div>
          {/if}
        </div>

        <!-- Right Group: Action Controls -->
        <div class="flex items-center gap-0.5">
          <button
            onclick={() => nanobot.syncSessionFromDb()}
            class="p-1.5 rounded-md hover:bg-white/5 transition-all group/sync active:scale-95"
            title="Đồng bộ Heartbeat"
            disabled={nanobot.chatPagination.isLoading}
          >
            <RefreshCw
              size={14}
              strokeWidth={2.5}
              class="text-neon-cyan/40 group-hover/sync:text-neon-cyan transition-colors {nanobot
                .chatPagination.isLoading
                ? 'animate-spin opacity-100'
                : ''}"
            />
          </button>

          {#if isSuperAdmin}
            <button
              onclick={handleClearLogs}
              class="p-1.5 rounded-md hover:bg-alert-red/10 group/trash transition-all active:scale-95"
              title="Xóa log hệ thống"
            >
              <Trash2
                size={14}
                strokeWidth={2.5}
                class="text-alert-red/30 group-hover/trash:text-alert-red transition-colors"
              />
            </button>
          {/if}

          <div class="w-[1px] h-4 bg-white/5 mx-1"></div>

          <button
            onclick={() => nanobot.toggleHeartbeat()}
            class="flex items-center justify-center w-9 h-9 rounded-md hover:bg-white/5 text-neon-cyan/60 hover:text-neon-cyan transition-colors"
            title="Đóng sidebar"
          >
            <PanelRight size={18} strokeWidth={2.5} />
          </button>
        </div>
      </div>
    </div>
  {/if}
  <div
    bind:this={scrollContainer}
    onscroll={handleScroll}
    class="flex-1 overflow-y-auto overflow-x-hidden space-y-4 flex flex-col items-start px-4 {hideHeader
      ? 'pt-6 pb-24'
      : 'scrollbar-none pb-16'}"
  >
    <!-- Infinite Scroll Loading Indicator -->
    {#if nanobot.chatPagination.isLoading && userHasScrolledUp}
      <div
        in:fade
        class="w-full py-4 flex flex-col items-center justify-center gap-2 border-b border-white/5 bg-white/[0.02]"
      >
        <div
          class="flex items-center gap-2 text-[10px] font-bold text-neon-cyan/40 tracking-[0.2em] uppercase"
        >
          <RefreshCw size={10} class="animate-spin" />
          <span>Synchronizing History</span>
        </div>
        <div
          class="h-[1px] w-24 bg-gradient-to-r from-transparent via-neon-cyan/20 to-transparent"
        ></div>
      </div>
    {/if}

    {#each nanobot.activityLogs as log (log.id)}
      {#if hideHeader}
        <!-- CHAT BUBBLE LAYOUT (MOBILE MINIMALIST) -->
        <div
          in:fly={{ y: 20, duration: 400, opacity: 0 }}
          out:fade={{ duration: 150 }}
          class="w-full flex flex-col {log.data?.role === 'assistant' || log.source === 'XOHI' ||
          log.source === '[XOHI]' || log.source === 'XÔ-HỈ'
            ? 'items-start'
            : log.source === '[ADMIN]'
              ? 'items-end'
              : 'items-center'}"
        >
          {#if log.data?.role === "assistant" || log.source === "XOHI" || log.source === "[XOHI]" || log.source === "XÔ-HỈ"}
            <div
              class="max-w-[88%] bg-white/[0.03] rounded-2xl rounded-tl-none px-4 py-3.5 shadow-sm border border-white/[0.05]"
            >
              <div class="flex items-center gap-2 mb-2 opacity-40">
                <Sparkles size={10} class="text-neon-cyan" />
                <span class="text-[9px] font-medium text-white uppercase tracking-widest">XoHi</span>
                <span class="text-[8px] font-mono text-gray-500">{formatRelativeTime(log.timestamp)}</span>
              </div>
              <div class="text-[14px] text-white/90 leading-[1.6] font-normal tracking-wide break-words">
                {processMessage(log.message)}
              </div>
              
              {#if log.data?.campaign_id && log.id === latestLogIdsPerCampaign().get(log.data.campaign_id)}
                <div class="mt-4 pt-3 border-t border-white/10 flex items-center justify-between gap-4">
                  <div class="flex items-center gap-2 min-w-0">
                    <div class="w-1.5 h-1.5 rounded-full bg-neon-cyan shadow-[0_0_8px_rgba(0,255,255,0.5)] animate-pulse"></div>
                    <span class="text-[11px] font-medium text-neon-cyan/80 truncate">
                      Giai đoạn {log.data.step || 1}
                    </span>
                  </div>
                  <button
                    onclick={(e) => {
                      e.stopPropagation();
                      nanobot.resumeCampaign(log);
                    }}
                    class="shrink-0 text-[11px] font-bold tracking-tight px-4 py-1.5 bg-white text-black rounded-full hover:bg-neon-cyan transition-all active:scale-95 shadow-lg"
                  >
                    MỞ DUYỆT
                  </button>
                </div>
              {/if}
            </div>
          {:else if log.source === "[ADMIN]"}
            <div
              class="max-w-[85%] bg-neon-cyan/10 border border-neon-cyan/10 rounded-2xl rounded-tr-none px-4 py-3"
            >
              <div class="flex items-center justify-end gap-2 mb-1.5 opacity-40">
                <span class="text-[8px] font-mono text-gray-500">{formatRelativeTime(log.timestamp)}</span>
                <span class="text-[9px] font-medium text-neon-cyan uppercase tracking-widest">Admin</span>
              </div>
              <div class="text-[14px] text-white/90 leading-[1.6] font-normal tracking-wide break-words">
                {processMessage(log.message)}
              </div>
            </div>
          {:else}
            <!-- System / Security Logs -->
            <div
              class="max-w-[90%] bg-transparent border border-white/5 rounded-full px-4 py-1.5 flex flex-col items-center text-center opacity-40 mt-1 mb-1"
            >
              <span
                class="text-[8px] font-mono {log.source.includes('Sec')
                  ? 'text-red-400'
                  : 'text-gray-500'} uppercase tracking-widest"
                >{log.source} • {formatRelativeTime(log.timestamp)}</span
              >
              <!-- <span class="text-[9px] font-mono text-gray-400 truncate w-full">{processMessage(log.message)}</span> -->
            </div>
          {/if}
        </div>
      {:else}
        <!-- STANDARD DESKTOP LOG LAYOUT -->
        <div
          in:fly={{ y: 20, duration: 400, opacity: 0 }}
          out:fade={{ duration: 150 }}
          class="flex items-start justify-between group/log py-[5px] w-full max-w-full gap-2 border-b border-white/[0.02] last:border-0"
        >
          <div class="flex items-start flex-1 min-w-0">
            <div
              class="flex items-center justify-end gap-1.5 shrink-0 w-11 mr-2 mt-[3px] opacity-60 group-hover/log:opacity-100 transition-opacity"
            >
              {#if log.data?.role === "assistant" || log.source === "XOHI" || log.source === "[XOHI]" || log.source === "XÔ-HỈ"}
                <span
                  class="text-[#FF33FF] font-bold tracking-wider text-[8px] uppercase"
                  >XOHI{#if log.routerTier}<span
                      class="text-[#c0e8ff]/60 ml-0.5 tracking-normal uppercase"
                      >[t{log.routerTier}]</span
                    >{/if}</span
                >
                <div class="w-1 h-1 rounded-full bg-[#FF33FF] shrink-0"></div>
              {:else if log.source === "[ADMIN]"}
                <span
                  class="text-neon-cyan font-bold tracking-wider text-[8px] uppercase"
                  >ADM</span
                >
                <div class="w-1 h-1 rounded-full bg-neon-cyan shrink-0"></div>
              {:else if log.source === "Nanobot-Sec" || log.source === "Nanobot-Vault"}
                <span
                  class="text-alert-red font-bold tracking-wider text-[8px] uppercase"
                  >SEC</span
                >
                <div class="w-1 h-1 rounded-full bg-alert-red shrink-0"></div>
              {:else if log.source.includes("Admin") || log.source === "Omni-Command"}
                <span
                  class="text-white font-bold tracking-wider text-[8px] uppercase"
                  >CMD</span
                >
                <div class="w-1 h-1 rounded-full bg-white shrink-0"></div>
              {:else}
                <span
                  class="text-gray-500 font-bold tracking-wider text-[8px] uppercase"
                  >SYS</span
                >
                <div class="w-1 h-1 rounded-full bg-gray-500 shrink-0"></div>
              {/if}
            </div>

            <div
              class="text-gray-400 group-hover/log:text-[#c0e8ff]/90 transition-colors text-[11px] font-mono leading-[1.6] flex-1 min-w-0"
            >
              <span class="truncate-2-lines pr-2">
                {processMessage(log.message)}
              </span>

              {#if (log.data?.role === "assistant" || log.source === "XOHI" || log.source === "[XOHI]" || log.source === "XÔ-HỈ") && log.data?.campaign_id}
                <!-- R81: Single Point of Resume -> Open Full VUI Modal -->
                {#if log.id === latestLogIdsPerCampaign().get(log.data.campaign_id)}
                  <div class="mt-2.5 flex items-center justify-between gap-2 p-2 rounded border border-[#c0e8ff]/20 bg-[#c0e8ff]/5">
                    <div class="flex items-center gap-1.5 min-w-0">
                      <div class="w-1.5 h-1.5 rounded-full bg-[#00FF00] animate-pulse"></div>
                      <span class="text-[10px] text-[#c0e8ff] truncate">
                        Sẵn sàng duyệt: Bước {log.data.step || 1}
                      </span>
                    </div>
                    <button
                      onclick={() => nanobot.resumeCampaign(log)}
                      class="shrink-0 text-[10px] font-bold tracking-wider px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors shadow-lg shadow-blue-500/20"
                    >
                      RESUME
                    </button>
                  </div>
                {/if}
              {/if}
            </div>
          </div>

          <div
            class="relative flex flex-col items-end shrink-0 mt-0.5 w-[38px]"
          >
            {#if isLongMessage(log.message) || log.data?.role === "assistant" || log.source === "XOHI" || log.source === "[XOHI]" || log.source === "XÔ-HỈ"}
              <span
                class="text-[9px] font-mono text-gray-500 opacity-50 group-hover/log:opacity-0 transition-opacity whitespace-nowrap"
              >
                {formatRelativeTime(log.timestamp)}
              </span>
              <div class="absolute top-0 right-0 flex items-center gap-1.5 opacity-0 group-hover/log:opacity-100 transition-opacity whitespace-nowrap">
                <button
                  onclick={() => nanobot.showFullLog(log)}
                  class="bg-white/5 hover:bg-white/10 text-white/40 hover:text-white transition-all cursor-pointer flex items-center justify-center p-1 rounded-md"
                  title="Xem chi tiết"
                >
                  <Eye size={12} />
                </button>
              </div>
            {:else}
              <span
                class="text-[9px] font-mono text-gray-500 opacity-50 group-hover/log:opacity-100 transition-opacity whitespace-nowrap"
              >
                {formatRelativeTime(log.timestamp)}
              </span>
            {/if}
          </div>
        </div>
      {/if}
    {/each}

  </div>


</div>

<style>
  .scrollbar-none::-webkit-scrollbar {
    display: none;
  }
  .scrollbar-none {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  .truncate-2-lines {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
