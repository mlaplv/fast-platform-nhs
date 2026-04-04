<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import type { Component } from "svelte";
  import type { BaseWidgetProps } from "$lib/types";
  import RevenueChart from "./widgets/RevenueChart.svelte";
  import ConfirmModal from "./widgets/ConfirmModal.svelte";
  import UserTable from "./widgets/UserTable.svelte";
  import UserManagement from "./management/UserManagement.svelte";
  import PermissionManagement from "./management/PermissionManagement.svelte";
  import CategoryManagement from "./management/CategoryManagement.svelte";
  import ProductManagement from "./management/ProductManagement.svelte";
  import OrderManagement from "./management/OrderManagement.svelte";
  import NewsManagement from "./management/NewsManagement.svelte";
  import VoiceSettings from "./management/VoiceSettings.svelte";
  import SystemSettings from "./management/SystemSettings.svelte";
  import ReviewManagement from "./management/ReviewManagement.svelte";
  import SupportKnowledgeManagement from "./management/SupportKnowledgeManagement.svelte";
  import SupportInbox from "./management/SupportInbox.svelte";

  const WIDGET_REGISTRY: Record<string, Component<BaseWidgetProps>> = {
    RevenueChart: RevenueChart as Component<BaseWidgetProps>,
    REVENUE_CHART: RevenueChart as Component<BaseWidgetProps>,
    SHOW_REVENUE: RevenueChart as Component<BaseWidgetProps>,
    SHOW_PRODUCT_EDIT: ProductManagement as Component<BaseWidgetProps>,
    UserTable: UserTable as Component<BaseWidgetProps>,
    USER_TABLE: UserTable as Component<BaseWidgetProps>,
    ConfirmModal: ConfirmModal as Component<BaseWidgetProps>,
    USER_MANAGEMENT: UserManagement as Component<BaseWidgetProps>,
    PERMISSION_MANAGEMENT: PermissionManagement as Component<BaseWidgetProps>,
    CATEGORY_MANAGEMENT: CategoryManagement as Component<BaseWidgetProps>,
    PRODUCT_MANAGEMENT: ProductManagement as Component<BaseWidgetProps>,
    ORDER_MANAGEMENT: OrderManagement as Component<BaseWidgetProps>,
    NEWS_MANAGEMENT: NewsManagement as Component<BaseWidgetProps>,
    VOICE_SETTINGS: VoiceSettings as Component<BaseWidgetProps>,
    SYSTEM_SETTINGS: SystemSettings as Component<BaseWidgetProps>,
    REVIEW_MANAGEMENT: ReviewManagement as Component<BaseWidgetProps>,
    SUPPORT_KNOWLEDGE: SupportKnowledgeManagement as Component<BaseWidgetProps>,
    SUPPORT_INBOX: SupportInbox as Component<BaseWidgetProps>,
  };

  let ActiveWidget = $derived(
    nanobot.activeWidget !== "NONE"
      ? WIDGET_REGISTRY[nanobot.activeWidget]
      : null,
  );
  let WidgetData = $derived(nanobot.currentData || {});

  // Bridge to Universal Modal
  $effect(() => {
    if (nanobot.activeWidget && nanobot.activeWidget !== "NONE") {
      nanobot.showUniversalModal();
    }
  });
</script>

<div class="dynamic-canvas-bridge pointer-events-none">
  <!-- This component now acts as a bridge to trigger the Universal Modal -->
  {#if nanobot.activeWidget && nanobot.activeWidget !== "NONE"}
    <div class="hidden">
      <!-- Logic is handled by $effect -->
    </div>
  {/if}
</div>
