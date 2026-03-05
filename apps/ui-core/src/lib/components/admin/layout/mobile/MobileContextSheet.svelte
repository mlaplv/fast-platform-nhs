<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fly } from "svelte/transition";
  import ChevronLeft from "lucide-svelte/icons/chevron-left";
  import Terminal from "lucide-svelte/icons/terminal";

  // Import all management components
  import RevenueChart from "../../widgets/RevenueChart.svelte";
  import UserTable from "../../widgets/UserTable.svelte";
  import UserManagement from "../../management/UserManagement.svelte";
  import PermissionManagement from "../../management/PermissionManagement.svelte";
  import CategoryManagement from "../../management/CategoryManagement.svelte";
  import ProductManagement from "../../management/ProductManagement.svelte";
  import OrderManagement from "../../management/OrderManagement.svelte";
  import NewsManagement from "../../management/NewsManagement.svelte";
  import NotificationList from "../../widgets/NotificationList.svelte";
  import VoiceSettings from "../../management/VoiceSettings.svelte";

  const WIDGET_REGISTRY: Record<string, any> = {
    REVENUE_CHART: RevenueChart,
    USER_TABLE: UserTable,
    USER_MANAGEMENT: UserManagement,
    PERMISSION_MANAGEMENT: PermissionManagement,
    CATEGORY_MANAGEMENT: CategoryManagement,
    PRODUCT_MANAGEMENT: ProductManagement,
    ORDER_MANAGEMENT: OrderManagement,
    NEWS_MANAGEMENT: NewsManagement,
    NOTIFICATION_LIST: NotificationList,
    VOICE_SETTINGS: VoiceSettings,
  };

  const WIDGET_LABEL: Record<string, string> = {
    REVENUE_CHART: "Doanh thu",
    USER_MANAGEMENT: "Nhân viên",
    PERMISSION_MANAGEMENT: "Phân quyền",
    CATEGORY_MANAGEMENT: "Danh mục",
    PRODUCT_MANAGEMENT: "Sản phẩm",
    ORDER_MANAGEMENT: "Đơn hàng",
    NEWS_MANAGEMENT: "Tin tức",
    VOICE_SETTINGS: "Voice Settings",
  };

  let ActiveWidget = $derived(
    nanobot.activeWidget !== "NONE"
      ? WIDGET_REGISTRY[nanobot.activeWidget]
      : null,
  );
  let WidgetData = $derived(nanobot.currentData || {});
  let title = $derived(WIDGET_LABEL[nanobot.activeWidget] || nanobot.activeWidget.replace(/_/g, " "));

  function handleBack() {
    nanobot.closeUniversalModal();
  }

  // Swipe gesture handling
  let touchStartX = 0;
  let touchEndX = 0;

  function handleTouchStart(e: TouchEvent) {
    touchStartX = e.changedTouches[0].screenX;
  }

  function handleTouchEnd(e: TouchEvent) {
    if (!ActiveWidget) return;
    touchEndX = e.changedTouches[0].screenX;
    if (touchEndX - touchStartX > 120) {
      handleBack();
    }
  }
</script>

{#if ActiveWidget}
  <div 
    class="fixed inset-0 z-[40] bg-[#050505] flex flex-col pb-[env(safe-area-inset-bottom)] pb-[70px]"
    role="dialog"
    aria-modal="true"
    aria-label="Contextual Management View"
    tabindex="-1"
    transition:fly={{ x: window.innerWidth, duration: 300, opacity: 1 }}
    ontouchstart={handleTouchStart}
    ontouchend={handleTouchEnd}
  >
    <!-- Header -->
    <div class="h-14 border-b border-white/5 bg-[#0a0a0a] flex items-center justify-between px-2 shrink-0">
      <div class="flex items-center gap-1">
        <button 
          onclick={handleBack}
          class="w-10 h-10 flex items-center justify-center text-neon-cyan hover:bg-neon-cyan/10 rounded-full transition-colors active:scale-95"
          aria-label="Back to XoHi"
        >
          <ChevronLeft size={24} strokeWidth={2.5} />
        </button>
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded bg-neon-cyan/10 border border-neon-cyan/20 flex items-center justify-center">
            <Terminal size={12} class="text-neon-cyan" />
          </div>
          <span class="font-bold text-white text-[15px] tracking-wide">{title}</span>
        </div>
      </div>
    </div>

    <!-- Content Area (Scrollable by the child component or here) -->
    <div class="flex-1 w-full relative overflow-hidden flex flex-col bg-[#050505]">
      <ActiveWidget data={WidgetData} />
    </div>
  </div>
{/if}
