<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import type { WidgetType } from "$lib/state/types";
  import { fade, fly } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import Package from "lucide-svelte/icons/package";
  import Users from "lucide-svelte/icons/users";
  import Newspaper from "lucide-svelte/icons/newspaper";
  import ShoppingCart from "lucide-svelte/icons/shopping-cart";
  import Shield from "lucide-svelte/icons/shield";
  import Settings from "lucide-svelte/icons/settings";
  import Home from "lucide-svelte/icons/home";
  import Megaphone from "lucide-svelte/icons/megaphone";
  
  interface MenuItem {
    id: WidgetType;
    label: string;
    icon: Component;
    color: string;
  }

  const menuItems: MenuItem[] = [
    { id: "NONE", label: "XoHi Home", icon: Home, color: "#00FFFF" },
    { id: "ORDER_MANAGEMENT", label: "Đơn hàng", icon: ShoppingCart, color: "#FFAA00" },
    { id: "PRODUCT_MANAGEMENT", label: "Sản phẩm", icon: Package, color: "#00FFFF" },
    { id: "NEWS_MANAGEMENT", label: "Tin tức", icon: Newspaper, color: "#FF33FF" },
    { id: "CAMPAIGNS", label: "Campaigns", icon: Megaphone, color: "#39ff14" },
    { id: "USER_MANAGEMENT", label: "Nhân viên", icon: Users, color: "#39FF14" },
    { id: "PERMISSION_MANAGEMENT", label: "Phân quyền", icon: Shield, color: "#39FF14" },
    { id: "VOICE_SETTINGS", label: "Cài đặt giọng nói", icon: Settings, color: "#gray-400" },
  ];

  function handleSelect(id: WidgetType) {
    if (id === "NONE") {
      nanobot.closeUniversalModal(); // Back to home
    } else {
      nanobot.openWidget(id);
    }
    nanobot.toggleMobileDrawer(); // Close drawer
  }

  // Swipe gesture handling
  let touchStartX = 0;
  let touchEndX = 0;

  function handleTouchStart(e: TouchEvent) {
    touchStartX = e.changedTouches[0].screenX;
  }

  function handleTouchEnd(e: TouchEvent) {
    touchEndX = e.changedTouches[0].screenX;
    if (touchStartX - touchEndX > 100) {
      nanobot.toggleMobileDrawer();
    }
  }
</script>

{#if nanobot.showMobileDrawer}
  <!-- Backdrop -->
  <div
    role="presentation"
    onclick={() => nanobot.toggleMobileDrawer()}
    class="fixed inset-0 bg-black/80 z-[100]"
    transition:fade={{ duration: 200 }}
  ></div>

  <!-- Drawer -->
  <div
    role="navigation"
    class="fixed inset-y-0 left-0 w-[280px] bg-[#0a0a0a] border-r border-white/5 z-[110] flex flex-col shadow-2xl"
    transition:fly={{ x: -280, duration: 300, opacity: 1 }}
    ontouchstart={handleTouchStart}
    ontouchend={handleTouchEnd}
  >
    <!-- Header -->
    <div class="p-6 border-b border-white/5 flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <div class="w-12 h-12 rounded-full border border-neon-cyan/30 flex items-center justify-center bg-neon-cyan/5">
          <span class="text-neon-cyan font-bold font-mono tracking-widest text-[10px]">XOHI</span>
        </div>
        <button 
          onclick={() => nanobot.toggleMobileDrawer()}
          class="p-2 rounded-full border border-white/10 text-gray-400 hover:text-white bg-white/5"
        >
          <X size={18} />
        </button>
      </div>
      <div>
        <div class="text-[10px] font-mono text-neon-cyan uppercase tracking-widest mb-1">Trinity Core</div>
        <div class="text-sm font-bold text-white truncate">{nanobot.userEmail || 'ADMINISTRATOR'}</div>
      </div>
    </div>

    <!-- Navigation List -->
    <div class="flex-1 overflow-y-auto p-4 space-y-2 relative">
      <div class="absolute inset-x-0 h-4 bg-gradient-to-b from-[#0a0a0a] to-transparent top-0 z-10 pointer-events-none"></div>
      
      {#each menuItems as item}
        <button
          onclick={() => handleSelect(item.id)}
          class="w-full flex items-center gap-4 p-4 rounded-2xl border border-transparent transition-colors active:scale-[0.98] {nanobot.activeWidget === item.id || (nanobot.activeWidget === 'NONE' && item.id === 'NONE') ? 'bg-white/10 border-white/20' : 'bg-transparent hover:bg-white/5'}"
        >
          <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border border-white/5 bg-black" style:color={item.color}>
            <item.icon size={20} />
          </div>
          <span class="text-[15px] font-bold tracking-wide {nanobot.activeWidget === item.id || (nanobot.activeWidget === 'NONE' && item.id === 'NONE') ? 'text-white' : 'text-gray-300'}">{item.label}</span>
        </button>
      {/each}
    </div>

    <!-- Footer -->
    <div class="p-5 border-t border-white/5 bg-[#050505]">
      <div class="text-[9px] font-mono text-gray-600 uppercase tracking-[0.2em] text-center">Xohi OS • System Online</div>
      <div class="flex justify-center gap-1.5 mt-2">
        <div class="w-1.5 h-1.5 rounded-full bg-neon-cyan/40 animate-pulse"></div>
        <div class="w-1.5 h-1.5 rounded-full bg-neon-cyan/40 animate-pulse" style="animation-delay: 200ms"></div>
        <div class="w-1.5 h-1.5 rounded-full bg-neon-cyan/40 animate-pulse" style="animation-delay: 400ms"></div>
      </div>
    </div>
  </div>
{/if}
