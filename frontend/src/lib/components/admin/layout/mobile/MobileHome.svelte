<script lang="ts">
  import HeartbeatStream from "../../HeartbeatStream.svelte";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { permissionState } from "$lib/state/permissions.svelte";
  import type { WidgetType } from "$lib/state/types";
  import { spring } from "svelte/motion";
  import ShoppingCart from "lucide-svelte/icons/shopping-cart";
  import Package from "lucide-svelte/icons/package";
  import Newspaper from "lucide-svelte/icons/newspaper";
  import Users from "lucide-svelte/icons/users";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Megaphone from "lucide-svelte/icons/megaphone";
  import XohiLogo from "$lib/components/admin/XohiLogo.svelte";

  interface QuickAction {
    label: string;
    icon: Component;
    widget: WidgetType;
    color: string;
    bg: string;
    border: string;
  }

  const quickActions: QuickAction[] = [
    { label: "Đơn hàng", icon: ShoppingCart, widget: "ORDER_MANAGEMENT", color: "text-vibrant-purple", bg: "bg-vibrant-purple/10", border: "border-vibrant-purple/20" },
    { label: "Campaigns", icon: Megaphone, widget: "CAMPAIGNS", color: "text-hacker-green", bg: "bg-hacker-green/10", border: "border-hacker-green/20" },
    { label: "Sản phẩm", icon: Package, widget: "PRODUCT_MANAGEMENT", color: "text-neon-cyan", bg: "bg-neon-cyan/10", border: "border-neon-cyan/20" },
    { label: "Tin tức", icon: Newspaper, widget: "NEWS_MANAGEMENT", color: "text-fuchsia-400", bg: "bg-fuchsia-400/10", border: "border-fuchsia-400/20" },
    { label: "Nhân viên", icon: Users, widget: "USER_MANAGEMENT", color: "text-[#39FF14]", bg: "bg-[#39FF14]/10", border: "border-[#39FF14]/20" }
  ];

  function openWidget(widgetId: WidgetType) {
    nanobot.openWidget(widgetId);
  }

  // Greeting logic
  let hour = new Date().getHours();
  function getGreeting() {
    if (hour < 12) return "kỳ nghỉ sáng tốt lành";
    if (hour < 18) return "chiều năng động";
    if (hour < 22) return "tối thư giãn";
    return "đêm muộn yên bình";
  }

  // Adaptive Scroll Logic
  let lastPos = 0;
  let isScrollingUp = $state(false);
  
  const scrollSpring = spring(1, {
    stiffness: 0.08,
    damping: 0.75
  });

  $effect(() => {
    const pos = nanobot.mobileScrollPosition;
    isScrollingUp = pos < lastPos && pos > 10;
    lastPos = pos;

    let targetFactor = 1;
    if (isScrollingUp || pos < 20) {
      targetFactor = 1;
    } else if (pos > 280) {
      targetFactor = 0; // Stage 3: Fully hidden
    } else if (pos > 150) {
      targetFactor = 0.15; // Stage 2: Ghosting
    } else if (pos > 60) {
      targetFactor = 0.4; // Stage 1: Aggressive Shrink
    }

    scrollSpring.set(targetFactor);
  });
</script>

<div class="flex-1 flex flex-col relative w-full h-full overflow-hidden bg-[#020202]">
  <!-- Adaptive Header -->
  <div 
    class="absolute top-0 left-0 right-0 z-30 px-6 pt-14 pb-2 transition-all duration-500 ease-out pointer-events-none"
    style:opacity={$scrollSpring}
    style:transform="translateY({(1 - $scrollSpring) * -100}px)"
  >
    <!-- Background Material: Subtle Blur -->
    <div 
      class="absolute inset-x-0 top-0 h-full bg-black/60 backdrop-blur-[25px] -z-10"
      style:opacity={1 - $scrollSpring}
    ></div>

    <div 
      class="flex flex-col gap-1 mb-4 transition-transform duration-500 pointer-events-auto"
      style:transform="scale({0.85 + ($scrollSpring * 0.15)})"
      style:transform-origin="left top"
    >
      <div class="flex items-center gap-2 mb-2">
        <XohiLogo variant="simple" size={40} interactive={true} />
      </div>
      <div>
        <h1 class="text-2xl font-light text-white tracking-tight leading-tight">
          Chào {permissionState.userName || 'Sếp'},
        </h1>
        <p class="text-gray-400 font-normal text-[12px] mt-1 tracking-wide opacity-80">
          Chúc {permissionState.userName || 'Sếp'} một {getGreeting()}.
        </p>
      </div>
    </div>
    
    <!-- Quick Actions: Glass Pills Redesign -->
    <div 
      class="flex gap-2 overflow-x-auto custom-scrollbar -mx-6 px-6 pointer-events-auto transition-all duration-700"
      style:opacity={0.4 + ($scrollSpring * 0.6)}
    >
      {#each quickActions as action}
        <button
          onclick={() => openWidget(action.widget)}
          class="group flex items-center gap-2 py-1.5 px-3.5 rounded-full border border-white/5 bg-white/5 backdrop-blur-xl active:scale-95 active:bg-white/10 transition-all shrink-0 shadow-sm"
        >
          <div class="{action.color} opacity-70 group-active:opacity-100">
            <action.icon size={13} />
          </div>
          <span class="font-medium text-white/90 text-[12px] whitespace-nowrap tracking-wide">{action.label}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Conversation Area -->
  <div class="flex-1 min-h-0 relative z-10">
    <!-- Content Spacer -->
    <div 
      class="w-full transition-all duration-300" 
      style:height="{$scrollSpring * 240}px"
    ></div>
    <HeartbeatStream hideHeader={true} />
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .custom-scrollbar {
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
  }
</style>
