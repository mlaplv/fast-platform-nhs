<script lang="ts">
  import HeartbeatStream from "../../HeartbeatStream.svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { spring } from "svelte/motion";
  import ShoppingCart from "lucide-svelte/icons/shopping-cart";
  import Package from "lucide-svelte/icons/package";
  import Newspaper from "lucide-svelte/icons/newspaper";
  import Users from "lucide-svelte/icons/users";
  import Sparkles from "lucide-svelte/icons/sparkles";

  const quickActions = [
    { label: "Đơn hàng", icon: ShoppingCart, widget: "ORDER_MANAGEMENT", color: "text-amber-400", bg: "bg-amber-400/10", border: "border-amber-400/20" },
    { label: "Sản phẩm", icon: Package, widget: "PRODUCT_MANAGEMENT", color: "text-neon-cyan", bg: "bg-neon-cyan/10", border: "border-neon-cyan/20" },
    { label: "Tin tức", icon: Newspaper, widget: "NEWS_MANAGEMENT", color: "text-fuchsia-400", bg: "bg-fuchsia-400/10", border: "border-fuchsia-400/20" },
    { label: "Nhân viên", icon: Users, widget: "USER_MANAGEMENT", color: "text-[#39FF14]", bg: "bg-[#39FF14]/10", border: "border-[#39FF14]/20" }
  ];

  function openWidget(widgetId: string) {
    nanobot.openWidget(widgetId as any);
  }

  // Greeting logic
  let hour = new Date().getHours();
  function getGreeting() {
    if (hour < 12) return "kỳ nghỉ sáng tốt lành";
    if (hour < 18) return "chiều năng động";
    if (hour < 22) return "tối thư giãn";
    return "đêm muộn yên bình";
  }

  // Phase 11: Progressive Multi-stage Scroll Factor
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
  <!-- Absolute Adaptive Header (Phase 13.3: Hyper-Aggressive x3) -->
  <div 
    class="absolute top-0 left-0 right-0 z-30 px-6 pt-12 pb-6 transition-opacity duration-300 pointer-events-none"
    style:opacity={$scrollSpring}
    style:transform="translateY({(1 - $scrollSpring) * -120}px)"
  >
    <!-- Background Material -->
    <div 
      class="absolute inset-x-0 top-0 h-full bg-black/80 backdrop-blur-[40px] -z-10"
      style:opacity={1 - $scrollSpring}
    ></div>

    <div 
      class="flex items-start gap-4 mb-8 pointer-events-auto"
      style:transform="scale({0.6 + ($scrollSpring * 0.4)})"
      style:transform-origin="left top"
    >
      <div class="w-12 h-12 rounded-full border border-neon-cyan/20 flex items-center justify-center bg-black/40 shadow-[0_0_25px_rgba(0,255,255,0.15)] shrink-0">
        <Sparkles size={22} class="text-neon-cyan animate-pulse" />
      </div>
      <div>
        <h1 class="text-2xl font-bold text-white tracking-tight leading-tight">
          Chào Sếp,<br/>
          <span class="text-gray-400 font-medium text-[15px]">Chúc Sếp một {getGreeting()}.</span>
        </h1>
      </div>
    </div>
    
    <!-- Quick Actions Scroll Row -->
    <div 
      class="flex overflow-x-auto custom-scrollbar -mx-6 px-6 gap-3 snap-x pointer-events-auto transition-all"
    >
      {#each quickActions as action}
        <button
          onclick={() => openWidget(action.widget)}
          class="flex items-center gap-2.5 py-2.5 px-4 rounded-xl border {action.border} {action.bg} backdrop-blur-md active:scale-95 transition-all shrink-0 snap-start shadow-xl"
        >
          <div class="{action.color} opacity-90">
            <action.icon size={16} />
          </div>
          <span class="font-bold text-white text-[12px] whitespace-nowrap tracking-wide">{action.label}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Conversation Area -->
  <div class="flex-1 min-h-0 relative z-10">
    <!-- Reactive Spacer: Follows the header height to avoid gaps -->
    <div 
      class="w-full transition-all duration-300" 
      style:height="{$scrollSpring * 200}px"
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
