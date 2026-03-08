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
  import { fade, fly } from "svelte/transition";
  import ContentReviewCard from "./ui/ContentReviewCard.svelte";

  let { hideHeader = false } = $props();

  const TRUNCATE_LIMIT = 120;

  // GOD-MODE: User Selection State
  let availableUsers: { id: string; name: string; email: string }[] = $state(
    [],
  );
  let isSuperAdmin = $derived(permissionState.roles.includes("SUPER_ADMIN"));

  $effect(() => {
    if (isSuperAdmin && availableUsers.length === 0) {
      fetchUsers();
    }
  });

  async function fetchUsers() {
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
    if (nanobot.activityLogs.length > 0) {
      setTimeout(scrollToBottom, 300);
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
    <div class="shrink-0 border-b border-white/5 bg-black/20 backdrop-blur-sm">
      <!-- Neural Control Bar (Minimalist Icon Row) -->
      <div class="h-10 flex items-center justify-between px-3">
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

          <button
            onclick={() => nanobot.toggleHeartbeat()}
            class="p-1.5 rounded-md hover:bg-white/5 transition-all text-neon-cyan/40 hover:text-neon-cyan active:scale-95"
            title="Đóng sidebar"
          >
            <PanelRight size={14} strokeWidth={2.5} />
          </button>

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
        </div>
      </div>
    </div>
  {/if}

  <div
    bind:this={scrollContainer}
    onscroll={handleScroll}
    class="flex-1 overflow-y-auto overflow-x-hidden space-y-1.5 flex flex-col items-start px-3 {hideHeader
      ? 'pt-4 pb-24'
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
        <!-- CHAT BUBBLE LAYOUT (MOBILE) -->
        <div
          in:fly={{ y: 20, duration: 400, opacity: 0 }}
          out:fade={{ duration: 150 }}
          class="w-full flex flex-col mb-1 {log.source === 'XOHI' ||
          log.source === '[XOHI]'
            ? 'items-start pl-2'
            : log.source === '[ADMIN]'
              ? 'items-end pr-2'
              : 'items-center'}"
        >
          {#if log.source === "XOHI" || log.source === "[XOHI]"}
            <div
              class="max-w-[85%] bg-neon-cyan/5 border border-neon-cyan/20 rounded-2xl rounded-tl-sm px-4 py-3 shadow-[0_4px_15px_rgba(0,255,255,0.05)]"
            >
              <div class="flex items-center gap-2 mb-1.5 opacity-60">
                <Sparkles size={10} class="text-neon-cyan" />
                <span
                  class="text-[9px] font-mono text-neon-cyan uppercase tracking-widest"
                  >XoHi</span
                >
                <span class="text-[8px] font-mono text-gray-500"
                  >{formatRelativeTime(log.timestamp)}</span
                >
              </div>
              <div
                class="text-[13px] text-gray-200 leading-relaxed font-sans break-words"
              >
                {processMessage(log.message)}
              </div>
            </div>
          {:else if log.source === "[ADMIN]"}
            <div
              class="max-w-[85%] bg-white/5 border border-white/10 rounded-2xl rounded-tr-sm px-4 py-3"
            >
              <div
                class="flex items-center justify-end gap-2 mb-1.5 opacity-60"
              >
                <span class="text-[8px] font-mono text-gray-500"
                  >{formatRelativeTime(log.timestamp)}</span
                >
                <span
                  class="text-[9px] font-mono text-gray-400 uppercase tracking-widest"
                  >{log.source.replace(/[\[\]]/g, "")}</span
                >
              </div>
              <div
                class="text-[13px] text-gray-300 leading-relaxed font-sans break-words"
              >
                {processMessage(log.message)}
              </div>
            </div>
          {:else}
            <!-- System / Security Logs -->
            <div
              class="max-w-[90%] bg-transparent border border-white/5 rounded-xl px-3 py-2 flex flex-col items-center text-center opacity-60 mt-1 mb-1"
            >
              <span
                class="text-[8px] font-mono {log.source.includes('Sec')
                  ? 'text-red-400'
                  : 'text-gray-500'} uppercase tracking-widest mb-0.5"
                >{log.source} • {formatRelativeTime(log.timestamp)}</span
              >
              <span class="text-[10px] font-mono text-gray-400 truncate w-full"
                >{processMessage(log.message)}</span
              >
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
              {#if log.source === "XOHI" || log.source === "[XOHI]"}
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

              {#if (log.source === "XOHI" || log.source === "[XOHI]") && log.data?.category === "CONTENT_CREATE"}
                <ContentReviewCard
                  campaign_id={log.data.campaign_id}
                  keywords={log.data.keywords}
                  assets={log.data.assets}
                  outline={log.data.outline}
                  step={log.data.step || 1}
                  status={log.data.status || "WAITING_FOR_REVIEW"}
                />
              {/if}
            </div>
          </div>

          <div
            class="relative flex flex-col items-end shrink-0 mt-0.5 w-[38px]"
          >
            {#if isLongMessage(log.message) || log.source === "XOHI" || log.source === "[XOHI]"}
              <span
                class="text-[9px] font-mono text-gray-500 opacity-50 group-hover/log:opacity-0 transition-opacity whitespace-nowrap"
              >
                {formatRelativeTime(log.timestamp)}
              </span>
              <button
                onclick={() => nanobot.showFullLog(log)}
                class="absolute top-0 right-0 opacity-0 group-hover/log:opacity-100 text-neon-cyan hover:text-white transition-all z-10 cursor-pointer flex items-center justify-center p-0.5"
                title="Phóng to"
              >
                <Eye size={12} />
              </button>
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
