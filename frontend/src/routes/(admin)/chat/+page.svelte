<script lang="ts">
  import { onMount, tick } from "svelte";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import OmniCommand from "$lib/components/admin/OmniCommand.svelte";
  import { fade } from "svelte/transition";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import LoaderCircle from "@lucide/svelte/icons/loader-circle";

  let scrollContainer = $state<HTMLDivElement>();
  let history = $derived(nanobot.chatHistory);
  let pagination = $derived(nanobot.chatPagination);

  // ── BƯỚC 3: SCROLL JUMP FIX (CHIẾN THUẬT ZALO) ──
  async function handleLoadMore() {
    if (!scrollContainer) return;
    const oldScrollHeight = scrollContainer.scrollHeight;

    await nanobot.loadMoreMessages();

    await tick();

    if (scrollContainer) {
      scrollContainer.scrollTop +=
        scrollContainer.scrollHeight - oldScrollHeight;
    }
  }

  // Svelte Action: Intersection Observer (Zero-library)
  function intersect(node: HTMLElement) {
    const observer = new IntersectionObserver(
      (entries) => {
        if (
          entries[0].isIntersecting &&
          pagination.hasMore &&
          !pagination.isLoading
        ) {
          handleLoadMore();
        }
      },
      { threshold: 0.1 },
    );

    observer.observe(node);
    return {
      destroy() {
        observer.disconnect(); // R4: Memory leak audit pass
      },
    };
  }

  // ── TEST CASE 3: NEW MESSAGE ANCHOR ──
  // Tự động cuộn xuống đáy khi có tin nhắn mới (Xohi trả lời hoặc User gửi)
  $effect.pre(() => {
    if (history.length > 0 && scrollContainer) {
      // Chỉ tự động cuộn nếu người dùng đang ở gần đáy (trong khoảng 300px)
      // Hoặc nếu đó là tin nhắn đầu tiên/vừa khởi tạo
      const isNearBottom =
        scrollContainer.scrollHeight -
          scrollContainer.scrollTop -
          scrollContainer.clientHeight <
        300;

      if (isNearBottom || pagination.isLoading === false) {
        tick().then(() => {
          if (scrollContainer) {
            scrollContainer.scrollTo({
              top: scrollContainer.scrollHeight,
              behavior: "smooth",
            });
          }
        });
      }
    }
  });

  onMount(() => {
    tick().then(() => {
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    });
  });
</script>

<svelte:head>
  <title>Chat Session | Xohi AI</title>
</svelte:head>

<div
  class="fixed inset-0 bg-[#050506] text-white flex flex-col items-center overflow-hidden"
>
  <div
    bind:this={scrollContainer}
    class="w-full max-w-2xl flex-1 overflow-y-auto px-8 pt-24 pb-32 scroll-smooth flex flex-col gap-6"
  >
    <h1
      class="text-2xl font-light tracking-widest text-cyan-400 uppercase mb-4 border-b border-cyan-400/20 pb-4"
    >
      Giao thức kết nối
    </h1>

    <!-- SENTINEL: Trigger load more (Zalo Standard) -->
    <div use:intersect class="h-4 w-full flex items-center justify-center">
      {#if pagination.isLoading}
        <div class="animate-spin text-cyan-400/50">
          <LoaderCircle size={20} />
        </div>
      {:else if !pagination.hasMore}
        <span class="text-[10px] uppercase tracking-widest opacity-20">
          Đầu lịch sử giao tiếp
        </span>
      {/if}
    </div>

    {#if history.length === 0 && !pagination.isLoading}
      <div
        class="flex-1 flex items-center justify-center opacity-30 italic font-light tracking-widest"
      >
        Khởi tạo luồng dữ liệu...
      </div>
    {:else}
      {#each history as msg (msg.id)}
        <div
          class="flex flex-col gap-2 {msg.role === 'user'
            ? 'items-end'
            : 'items-start'}"
          transition:fade
        >
          <div
            class="text-[10px] font-mono uppercase tracking-widest opacity-40"
          >
            {msg.role} • {msg.timestamp.toLocaleTimeString()}
          </div>
          <div
            class="max-w-[85%] p-4 rounded-2xl backdrop-blur-md border
                        {msg.role === 'user'
              ? 'bg-cyan-400/10 border-cyan-400/20 rounded-tr-none text-cyan-50'
              : 'bg-white/5 border-white/10 rounded-tl-none text-white/90'}"
          >
            {msg.content.text}
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <div 
    class="fixed bottom-8 left-0 right-0 pointer-events-none"
    style="z-index: {Z_INDEX.POPOVER};"
  >
    <div class="pointer-events-auto">
      <OmniCommand />
    </div>
  </div>
</div>

<style>
  :global(body) {
    background-color: #050506;
    overflow: hidden;
  }

  /* Custom Scrollbar for Sci-Fi look */
  div::-webkit-scrollbar {
    width: 4px;
  }
  div::-webkit-scrollbar-track {
    background: transparent;
  }
  div::-webkit-scrollbar-thumb {
    background: rgba(34, 211, 238, 0.1);
    border-radius: 10px;
  }
  div::-webkit-scrollbar-thumb:hover {
    background: rgba(34, 211, 238, 0.3);
  }
</style>
