<script lang="ts">
  import { useNanobot, type WidgetType } from "$lib/state/nanobot.svelte";
  import { onMount, type Component } from "svelte";
  import { goto } from "$app/navigation";
  
  const nanobot = useNanobot();
  import Package from "lucide-svelte/icons/package";
  import Users from "lucide-svelte/icons/users";
  import Newspaper from "lucide-svelte/icons/newspaper";
  import ShoppingCart from "lucide-svelte/icons/shopping-cart";
  import Gift from "lucide-svelte/icons/gift";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import ChevronRight from "lucide-svelte/icons/chevron-right";
  import Megaphone from "lucide-svelte/icons/megaphone";
  import FileText from "lucide-svelte/icons/file-text";
  import FolderTree from "lucide-svelte/icons/folder-tree";
  import BoxIcon from "lucide-svelte/icons/box";
  import UserCog from "lucide-svelte/icons/user-cog";
  import Shield from "lucide-svelte/icons/shield";
  import Image from "lucide-svelte/icons/image";
  import Globe from "lucide-svelte/icons/globe";
  import Calendar from "lucide-svelte/icons/calendar";
  import Layout from "lucide-svelte/icons/layout";
  import Star from "lucide-svelte/icons/star";
  import { fade, fly } from "svelte/transition";

  let { open = $bindable() } = $props();

  onMount(() => {
    if (open === undefined) open = false;
  });

  interface SubItem {
    label: string;
    widget: WidgetType;
  }

  interface CategoryItem {
    id: string;
    icon: Component;
    label: string;
    sublabel?: string;
    color: string;
    widget?: WidgetType;
    href?: string;
    children?: SubItem[];
  }

  const categories: CategoryItem[] = [
    {
      id: "orders",
      label: "Đơn hàng",
      sublabel: "Quản lý giao dịch",
      icon: ShoppingCart,
      color: "#FFB800", // Amber/Gold for orders
      widget: "ORDER_MANAGEMENT",
    },
    {
      id: "vouchers",
      label: "Vouchers",
      sublabel: "Viral Gift & Promotion",
      icon: Gift,
      color: "#FE2C55", // TikTok Red/Pink
      widget: "VOUCHER_MANAGEMENT",
    },
    {
      id: "appointments",
      label: "Lịch hẹn",
      sublabel: "Neural Scheduling",
      icon: Calendar,
      color: "#00F3FF", // matching neon-cyan
      widget: "APPOINTMENTS",
    },
    {
      id: "product",
      label: "Sản phẩm",
      sublabel: "Quản lý kho & Nhãn hàng",
      icon: Package,
      color: "#00F3FF", // neon-cyan
      children: [
        { label: "Sản phẩm", widget: "PRODUCT_MANAGEMENT" },
        { label: "Danh mục", widget: "CATEGORY_MANAGEMENT" },
        { label: "Quản trị Đánh giá", widget: "REVIEW_MANAGEMENT" }
      ]
    },
    {
      id: "campaigns",
      label: "Campaigns",
      sublabel: "Content Factory & Ads",
      icon: Megaphone,
      color: "#FF33FF", // vibrant-purple
      children: [
        { label: "Content Factory", widget: "CAMPAIGNS" }
      ]
    },
    {
      id: "users",
      label: "Người dùng",
      sublabel: "Phân quyền & Tài khoản",
      icon: Users,
      color: "#39FF14", // neon-green
      children: [
        { label: "Người dùng", widget: "USER_MANAGEMENT" },
        { label: "Phân quyền", widget: "PERMISSION_MANAGEMENT" },
      ]
    },
    {
      id: "news",
      icon: Newspaper,
      label: "Bài viết",
      sublabel: "Bài viết & Blog",
      widget: "NEWS_MANAGEMENT",
      color: "#FF33FF",
    },
    {
      id: "media",
      icon: Image,
      label: "Thư viện Ảnh",
      sublabel: "Toàn cục & Quản lý file",
      widget: "MEDIA_MANAGER",
      color: "#00F3FF", // matching neon-cyan for media
    },
    {
      id: "banners",
      label: "Quản lý Banner",
      sublabel: "Quảng cáo & Promo",
      icon: Layout,
      color: "#FFB800",
      widget: "BANNER_MANAGEMENT",
    },
    {
      id: "support-kb",
      label: "Hỗ trợ Helen",
      sublabel: "Đào tạo AI & Inbox",
      icon: Sparkles,
      color: "#FF33FF", // vibrant-purple
      children: [
        { label: "Tri thức (RAG)", widget: "SUPPORT_KNOWLEDGE" },
        { label: "Hộp thư AI", widget: "SUPPORT_INBOX" },
        { label: "Brain Manager", widget: "BRAIN_MANAGEMENT" },
      ]
    },
    {
      id: "system",
      label: "Cấu hình",
      sublabel: "Node Config & Control",
      icon: Globe,
      color: "#00F3FF",
      widget: "SYSTEM_SETTINGS",
    },
  ];

  let itemsRevealed = $state(0);
  let expandedIndex = $state(-1);
  let staggerTimer: ReturnType<typeof setInterval> | undefined;

  $effect(() => {
    if (open) {
      itemsRevealed = 0;
      expandedIndex = -1;
      let count = 0;
      staggerTimer = setInterval(() => {
        count++;
        itemsRevealed = count;
        if (count >= categories.length) {
          clearInterval(staggerTimer);
        }
      }, 60);
    } else {
      itemsRevealed = 0;
      expandedIndex = -1;
      if (staggerTimer) clearInterval(staggerTimer);
    }
  });

  function handleSelect(item: CategoryItem, index: number) {
    if (item.children && item.children.length > 0) {
      expandedIndex = expandedIndex === index ? -1 : index;
    } else if (item.href) {
      open = false;
      goto(item.href);
    } else if (item.widget) {
      open = false;
      nanobot.openWidget(item.widget);
    }
  }

  function handleSubSelect(sub: SubItem) {
    open = false;
    nanobot.openWidget(sub.widget);
  }
</script>

{#if open}
  <!-- Popover Container (Origin: Bottom Left of Omnibar) -->
  <div
    class="absolute bottom-full left-0 mb-4 z-[var(--z-admin-hud)] w-[320px] origin-bottom-left"
    transition:fly={{ y: 20, duration: 400, opacity: 0 }}
  >
    <!-- Holographic Popover Frame -->
    <div
      class="relative bg-[#0a0a0a]/95 md:bg-[#0a0a0a]/90 md:backdrop-blur-3xl border border-neon-cyan/20 overflow-hidden shadow-[0_0_50px_rgba(0,243,255,0.1)]"
    >
      <!-- Scanning Line -->
      <div
        class="absolute inset-x-0 h-[100px] bg-gradient-to-b from-transparent via-neon-cyan/5 to-transparent z-0 pointer-events-none cat-scan-line"
      ></div>

      <!-- Corner Brackets -->
      <div
        class="absolute top-0 left-0 w-4 h-4 border-t border-l border-neon-cyan/40"
      ></div>
      <div
        class="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-neon-cyan/40"
      ></div>

      <!-- Header -->
      <div
        class="px-5 py-4 border-b border-white/5 bg-white/[0.02] flex items-center gap-3"
      >
        <div class="p-1.5 bg-neon-cyan/10 rounded">
          <Sparkles size={12} class="text-neon-cyan" />
        </div>
        <span
          class="text-[9px] font-mono uppercase tracking-[0.3em] text-white/40"
          >Matrix Quick Access</span
        >
      </div>

      <!-- List -->
      <div
        class="p-3 relative z-10 space-y-1 max-h-[400px] overflow-y-auto scrollbar-mission"
      >
        {#each categories as item, i}
          <div class="flex flex-col">
            <button
              onclick={() => handleSelect(item, i)}
              class="w-full flex items-center gap-4 px-4 py-3 hover:bg-white/[0.04] transition-all group border border-transparent hover:border-white/5"
              style:opacity={i < itemsRevealed ? 1 : 0}
              style:transform="translateX({i < itemsRevealed ? 0 : -10}px)"
              style:transition-delay="{i * 40}ms"
            >
              <div
                class="w-10 h-10 shrink-0 flex items-center justify-center border transition-all duration-300 group-hover:scale-110"
                style:border-color="{item.color}30"
                style:background="{item.color}05"
                style:color={item.color}
              >
                <item.icon size={20} />
              </div>
              <div class="flex-1 text-left">
                <span
                  class="block text-[7px] font-mono text-white/20 uppercase tracking-widest leading-none mb-1"
                  >Node_0x{i + 1}</span
                >
                <div
                  class="text-[13px] font-bold text-gray-200 group-hover:text-white tracking-widest uppercase"
                >
                  {item.label}
                </div>
                <div class="text-[9px] text-gray-600 font-mono tracking-wider">
                  {item.sublabel}
                </div>
              </div>
              <div
                class="transition-transform duration-300 transform {expandedIndex ===
                i
                  ? 'rotate-90 text-neon-cyan'
                  : 'text-white/20 group-hover:text-white/40'}"
              >
                <ChevronRight size={14} />
              </div>
            </button>

            {#if item.children && expandedIndex === i}
              <div
                class="pl-14 pr-2 pb-2 space-y-1"
                transition:fly={{ y: -10, duration: 300 }}
              >
                {#each item.children as sub, si}
                  <button
                    onclick={() => handleSubSelect(sub)}
                    class="w-full py-2 px-3 text-[11px] font-mono text-gray-400 hover:text-neon-cyan hover:bg-neon-cyan/5 transition-all text-left flex items-center justify-between group/sub"
                  >
                    <span class="tracking-widest uppercase">{sub.label}</span>
                    <ChevronRight
                      size={10}
                      class="opacity-0 group-hover/sub:opacity-100 -translate-x-2 group-hover/sub:translate-x-0 transition-all"
                    />
                  </button>
                {/each}
              </div>
            {/if}
          </div>
        {/each}
      </div>

      <!-- Footer -->
      <div
        class="px-5 py-2 bg-white/[0.01] border-t border-white/5 flex justify-between items-center opacity-40"
      >
        <span
          class="text-[7px] font-mono uppercase tracking-widest text-white/30"
          >System Link Established</span
        >
        <div class="flex gap-1">
          <div class="w-1 h-1 bg-neon-cyan/40"></div>
          <div class="w-1 h-1 bg-neon-cyan/40"></div>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .cat-scan-line {
    animation: scanline 4s linear infinite;
  }

  @keyframes scanline {
    0% {
      transform: translateY(-100%);
    }
    100% {
      transform: translateY(300%);
    }
  }

  .scrollbar-mission::-webkit-scrollbar {
    width: 3px;
  }
  .scrollbar-mission::-webkit-scrollbar-track {
    background: transparent;
  }
  .scrollbar-mission::-webkit-scrollbar-thumb {
    background: rgba(0, 243, 255, 0.1);
  }
</style>
