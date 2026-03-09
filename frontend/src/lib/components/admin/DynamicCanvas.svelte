<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
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

  const WIDGET_REGISTRY: Record<string, any> = {
    RevenueChart,
    REVENUE_CHART: RevenueChart,
    SHOW_REVENUE: RevenueChart,
    SHOW_PRODUCT_EDIT: ProductManagement,
    UserTable,
    USER_TABLE: UserTable,
    ConfirmModal,
    USER_MANAGEMENT: UserManagement,
    PERMISSION_MANAGEMENT: PermissionManagement,
    CATEGORY_MANAGEMENT: CategoryManagement,
    PRODUCT_MANAGEMENT: ProductManagement,
    ORDER_MANAGEMENT: OrderManagement,
    NEWS_MANAGEMENT: NewsManagement,
    VOICE_SETTINGS: VoiceSettings,
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
