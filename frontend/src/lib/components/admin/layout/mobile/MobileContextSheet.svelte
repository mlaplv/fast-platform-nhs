<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { fly } from "svelte/transition";
  import type { Component } from "svelte";
  import type { WidgetType } from "$lib/state/types";
  import type { BaseWidgetProps } from "$lib/types";
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
  import ContentFactory from "../../management/ContentFactory.svelte";
  import ContentReviewWidget from "../../widgets/ContentReviewWidget.svelte";
  import SystemSettings from "../../management/SystemSettings.svelte";

  const WIDGET_REGISTRY: Partial<Record<WidgetType, Component<BaseWidgetProps>>> = {
    REVENUE_CHART: RevenueChart as Component<BaseWidgetProps>,
    USER_TABLE: UserTable as Component<BaseWidgetProps>,
    USER_MANAGEMENT: UserManagement as Component<BaseWidgetProps>,
    PERMISSION_MANAGEMENT: PermissionManagement as Component<BaseWidgetProps>,
    CATEGORY_MANAGEMENT: CategoryManagement as Component<BaseWidgetProps>,
    PRODUCT_MANAGEMENT: ProductManagement as Component<BaseWidgetProps>,
    ORDER_MANAGEMENT: OrderManagement as Component<BaseWidgetProps>,
    NEWS_MANAGEMENT: NewsManagement as Component<BaseWidgetProps>,
    NOTIFICATION_LIST: NotificationList as Component<BaseWidgetProps>,
    VOICE_SETTINGS: VoiceSettings as Component<BaseWidgetProps>,
    CAMPAIGNS: ContentFactory as unknown as Component<BaseWidgetProps>,
    CONTENT_REVIEW: ContentReviewWidget as unknown as Component<BaseWidgetProps>,
    SYSTEM_SETTINGS: SystemSettings as Component<BaseWidgetProps>,
  };

  const WIDGET_LABEL: Partial<Record<WidgetType, string>> = {
    REVENUE_CHART: "Doanh thu",
    USER_MANAGEMENT: "Nhân viên",
    PERMISSION_MANAGEMENT: "Phân quyền",
    CATEGORY_MANAGEMENT: "Danh mục",
    PRODUCT_MANAGEMENT: "Sản phẩm",
    ORDER_MANAGEMENT: "Đơn hàng",
    NEWS_MANAGEMENT: "Tin tức",
    VOICE_SETTINGS: "Voice Settings",
    CAMPAIGNS: "Chiến dịch",
    CONTENT_REVIEW: "Duyệt bài",
    SYSTEM_SETTINGS: "Cấu hình hệ thống",
  };

  let ActiveWidget = $derived(
    nanobot.activeWidget !== "NONE"
      ? WIDGET_REGISTRY[nanobot.activeWidget as WidgetType]
      : null,
  );
  let WidgetData = $derived(nanobot.currentData || {});
  let title = $derived(
    WIDGET_LABEL[nanobot.activeWidget as WidgetType] ||
    nanobot.activeWidget.replace(/_/g, " ")
  );

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
