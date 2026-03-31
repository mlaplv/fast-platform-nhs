<script lang="ts">
  // Force HMR Update for Widget Registry Integration
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { fade } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import SupremeCloseButton from "./SupremeCloseButton.svelte";
  import Terminal from "lucide-svelte/icons/terminal";
  import RevenueChart from "../widgets/RevenueChart.svelte";
  import ConfirmModal from "../widgets/ConfirmModal.svelte";
  import UserTable from "../widgets/UserTable.svelte";
  import UserManagement from "../management/UserManagement.svelte";
  import PermissionManagement from "../management/PermissionManagement.svelte";
  import CategoryManagement from "../management/CategoryManagement.svelte";
  import ProductManagement from "../management/ProductManagement.svelte";
  import OrderManagement from "../management/OrderManagement.svelte";
  import NewsManagement from "../management/NewsManagement.svelte";
  import NotificationList from "../widgets/NotificationList.svelte";
  import VoiceSettings from "../management/VoiceSettings.svelte";
  import ContentFactory from "../management/ContentFactory.svelte";
  import ContentReviewWidget from "../widgets/ContentReviewWidget.svelte";
  import MediaHubOverlay from "../../media/MediaHubOverlay.svelte";
  import SystemSettings from "../management/SystemSettings.svelte";
import BannerManagement from "../management/BannerManagement.svelte";
import AppointmentManagement from "../management/AppointmentManagement.svelte";

  import type { Component } from "svelte";
  import type { WidgetType } from "$lib/state/types";

  const WIDGET_REGISTRY: Record<string, Component<{ data: Record<string, unknown> }>> = {
    RevenueChart,
    REVENUE_CHART: RevenueChart,
    UserTable,
    USER_TABLE: UserTable,
    ConfirmModal,
    USER_MANAGEMENT: UserManagement,
    PERMISSION_MANAGEMENT: PermissionManagement,
    CATEGORY_MANAGEMENT: CategoryManagement,
    PRODUCT_MANAGEMENT: ProductManagement,
    ORDER_MANAGEMENT: OrderManagement,
    NEWS_MANAGEMENT: NewsManagement,
    NOTIFICATION_LIST: NotificationList,
    VOICE_SETTINGS: VoiceSettings,
    CAMPAIGNS: ContentFactory,
    CONTENT_REVIEW: ContentReviewWidget,
    MEDIA_MANAGER: MediaHubOverlay,
    SYSTEM_SETTINGS: SystemSettings,
    BANNER_MANAGEMENT: BannerManagement,
    APPOINTMENTS: AppointmentManagement,
  };

  const WIDGET_LABEL: Record<string, string> = {
    REVENUE_CHART: "REVENUE CHART",
    USER_TABLE: "USER TABLE",
    USER_MANAGEMENT: "USER MANAGEMENT",
    PERMISSION_MANAGEMENT: "PERMISSION MANAGEMENT",
    CATEGORY_MANAGEMENT: "CATEGORY MANAGEMENT",
    PRODUCT_MANAGEMENT: "PRODUCT MANAGEMENT",
    ORDER_MANAGEMENT: "ORDER MANAGEMENT",
    NEWS_MANAGEMENT: "NEWS MANAGEMENT",
    NOTIFICATION_LIST: "NOTIFICATIONS",
    VOICE_SETTINGS: "VOICE SETTINGS",
    CAMPAIGNS: "CONTENT FACTORY",
    CONTENT_REVIEW: "TRÌNH DUYỆT BÀI VIẾT",
    MEDIA_MANAGER: "THƯ VIỆN HÌNH ẢNH",
    SYSTEM_SETTINGS: "SYSTEM CONFIGURATION",
    BANNER_MANAGEMENT: "BANNER MANAGEMENT",
    APPOINTMENTS: "LỊCH HẸN NEURAL",
  };

  let open = $derived(nanobot.universalModalOpen);
  let ActiveWidget = $derived(
    nanobot.activeWidget !== "NONE"
      ? WIDGET_REGISTRY[nanobot.activeWidget]
      : null,
  );
  let WidgetData = $derived(nanobot.currentData || {});
  let title = $derived(WIDGET_LABEL[nanobot.activeWidget] || nanobot.activeWidget.replace(/_/g, " "));

  let currentTime = $state(new Date().toLocaleTimeString());
  $effect(() => {
    const timer = setInterval(() => {
      currentTime = new Date().toLocaleTimeString();
    }, 1000);
    return () => clearInterval(timer);
  });

  function close() {
    nanobot.closeUniversalModal();
  }
</script>

{#if open && ActiveWidget}
  {#if nanobot.activeWidget === 'MEDIA_MANAGER'}
    <ActiveWidget data={WidgetData} />
  {:else}
    <div
      class="xohi-widget-overlay"
      transition:fade={{ duration: 300 }}
      style="z-index: {Z_INDEX_ADMIN.MODAL};"
    >
    <!-- Backdrop (scoped to main content) -->
    <div
      class="absolute inset-0 bg-black/80 md:bg-black/60 md:backdrop-blur-sm"
      onclick={close}
      onkeydown={(e) => e.key === "Escape" && close()}
      role="presentation"
    ></div>

    <!-- Widget Container -->
    <div
      class="relative w-full h-full flex flex-col max-h-full overflow-hidden"
      style="z-index: {Z_INDEX_ADMIN.SURFACE};"
    >
      <!-- Header -->
      {#if nanobot.activeWidget !== 'CONTENT_REVIEW'}
      <div class="flex items-center justify-between px-5 py-3 border-b border-cyan-500/20 bg-black md:bg-black/80 md:backdrop-blur-md shrink-0">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-md bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <Terminal class="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <h2 class="text-xs font-mono tracking-[0.15em] uppercase text-cyan-400">
              {title}
            </h2>
            <p class="text-[9px] font-mono text-gray-500 uppercase tracking-wider">
              XOHI · TRINITY CORE
            </p>
          </div>
        </div>

        <div class="flex items-center gap-4">
          <SupremeCloseButton 
            campaign_id={nanobot.activeWidget === 'CONTENT_REVIEW' ? WidgetData.campaign_id : undefined} 
            onClose={close}
          />
        </div>
      </div>
      {/if}

      <!-- Widget Content (scrollable container managed by widget internally for CONTENT_REVIEW) -->
      <div class="flex-1 {nanobot.activeWidget === 'CONTENT_REVIEW' || nanobot.activeWidget === 'APPOINTMENTS' ? 'overflow-hidden p-0' : 'overflow-y-auto overflow-x-hidden p-4'}">
        <ActiveWidget data={WidgetData} isWidget={true} />
      </div>

      <!-- Bottom Border Accent -->
      <div class="h-px bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent shrink-0"></div>
    </div>
  </div>
  {/if}
{/if}

<style>
  .xohi-widget-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
  }
</style>
