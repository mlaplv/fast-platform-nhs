<script lang="ts">
  // Force HMR Update for Widget Registry Integration
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { fade } from "svelte/transition";
  import X from "@lucide/svelte/icons/x";
  import SupremeCloseButton from "./SupremeCloseButton.svelte";
  import Terminal from "@lucide/svelte/icons/terminal";
  import Search from "@lucide/svelte/icons/search";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Activity from "@lucide/svelte/icons/activity";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import RevenueChart from "../widgets/RevenueChart.svelte";
  import ConfirmModal from "./ConfirmationModal.svelte";
  import UserTable from "../widgets/UserTable.svelte";
  import UserManagement from "../management/UserManagement.svelte";
  import PermissionManagement from "../management/PermissionManagement.svelte";
  import CategoryManagement from "../management/CategoryManagement.svelte";
  import ProductManagement from "../management/ProductManagement.svelte";
  import OrderManagement from "../management/OrderManagement.svelte";
  import NewsManagement from "../management/NewsManagement.svelte";
  import NotificationList from "../widgets/NotificationList.svelte";
  import NotificationManagement from "../management/NotificationManagement.svelte";
  import VoiceSettings from "../management/VoiceSettings.svelte";
  import ContentFactory from "../management/ContentFactory.svelte";
  import ContentReviewWidget from "../widgets/ContentReviewWidget.svelte";
  import MediaHubOverlay from "../../media/MediaHubOverlay.svelte";
  import SystemSettings from "../management/SystemSettings.svelte";
import BannerManagement from "../management/BannerManagement.svelte";
import AppointmentManagement from "../management/AppointmentManagement.svelte";
import ReviewManagement from "../management/ReviewManagement.svelte";
import SupportKnowledgeManagement from "../management/SupportKnowledgeManagement.svelte";
import SupportInbox from "../management/SupportInbox.svelte";
import BrainManagerWidget from "../management/BrainManagerWidget.svelte";
import VideoFullView from "../../widgets/VideoFullView.svelte";
import VoucherManagement from "../management/VoucherManagement.svelte";
import AdsFraudDashboard from "../AdsFraudDashboard.svelte";
import SecuritySOC from "../management/SecuritySOC.svelte";
import CtvManagement from "../management/CtvManagement.svelte";
import SeoGraphManagement from "../management/SeoGraphManagement.svelte";

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
    NOTIFICATION_MANAGEMENT: NotificationManagement,
    VOICE_SETTINGS: VoiceSettings,
    CAMPAIGNS: ContentFactory,
    CONTENT_REVIEW: ContentReviewWidget,
    MEDIA_MANAGER: MediaHubOverlay,
    SYSTEM_SETTINGS: SystemSettings,
    BANNER_MANAGEMENT: BannerManagement,
    APPOINTMENTS: AppointmentManagement,
    REVIEW_MANAGEMENT: ReviewManagement,
    SUPPORT_KNOWLEDGE: SupportKnowledgeManagement,
    SUPPORT_INBOX: SupportInbox,
    BRAIN_MANAGEMENT: BrainManagerWidget,
    VIDEO_FULLVIEW: VideoFullView,
    VOUCHER_MANAGEMENT: VoucherManagement,
    ADS_PROTECTION: AdsFraudDashboard,
    SECURITY_SOC: SecuritySOC,
    CTV_MANAGEMENT: CtvManagement,
    SEO_GRAPH: SeoGraphManagement,
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
    NOTIFICATION_MANAGEMENT: "SIGNAL MANAGEMENT HUB",
    VOICE_SETTINGS: "VOICE SETTINGS",
    CAMPAIGNS: "CONTENT FACTORY",
    CONTENT_REVIEW: "TRÌNH DUYỆT BÀI VIẾT",
    MEDIA_MANAGER: "THƯ VIỆN HÌNH ẢNH",
    SYSTEM_SETTINGS: "SYSTEM CONFIGURATION",
    BANNER_MANAGEMENT: "BANNER MANAGEMENT",
    APPOINTMENTS: "LỊCH HẸN NEURAL",
    REVIEW_MANAGEMENT: "QUẢN TRỊ ĐÁNH GIÁ",
    SUPPORT_KNOWLEDGE: "HELEN BRAIN — TRI THỨC AI",
    SUPPORT_INBOX: "HELEN INBOX — GIÁM SÁT HỘI THOẠI",
    BRAIN_MANAGEMENT: "HELEN BRAIN — QUẢN TRỊ TRI THỨC",
    VIDEO_FULLVIEW: "XEM VIDEO",
    VOUCHER_MANAGEMENT: "QUẢN LÝ VOUCHER & KHUYẾN MÃI",
    ADS_PROTECTION: "ADS FRAUD PROTECTION & CLICK SHIELD",
    SECURITY_SOC: "SECURITY OPERATIONS CENTER (SOC)",
    CTV_MANAGEMENT: "QUẢN LÝ HỆ THỐNG LIÊN KẾT (CTV)",
    SEO_GRAPH: "SEO PILLAR & CLUSTER GRAPH NETWORK",
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
      {#if !['CONTENT_REVIEW', 'ADS_PROTECTION', 'NOTIFICATION_MANAGEMENT'].includes(nanobot.activeWidget)}
      <div class="flex items-center justify-between px-5 py-3 border-b border-cyan-500/20 bg-black md:bg-black/80 md:backdrop-blur-md shrink-0">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-md bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <Terminal class="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <h2 class="text-xs font-mono tracking-[0.15em] text-cyan-400">
              {title}
            </h2>
            <p class="text-[9px] font-mono text-gray-500 tracking-wider">
              XOHI · TRINITY CORE
            </p>
          </div>
        </div>

        <div class="flex items-center gap-4">
          {#if nanobot.activeWidget === 'SUPPORT_INBOX'}
            <div class="flex items-center gap-3 mr-4 h-8 animate-in fade-in slide-in-from-right-4 duration-500">
              <div class="relative w-48 md:w-64 group">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-cyan-400/40 group-focus-within:text-cyan-400 transition-colors" />
                <input 
                  type="text" 
                  placeholder="Tìm khách, SĐT..." 
                  class="w-full bg-white/5 border border-white/10 rounded-md pl-8 pr-4 py-1 text-[10px] font-mono text-cyan-100 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/40 focus:bg-white/[0.08] transition-all"
                  value={nanobot.supportSearchTerm}
                  oninput={(e) => nanobot.setSupportSearchTerm(e.currentTarget.value)}
                />
              </div>
              
              <div class="flex items-center gap-2 px-2 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-md">
                <span class="text-[9px] font-mono text-cyan-400 tracking-tighter">
                  {nanobot.activeSupportSessionCount} Sessions
                </span>
              </div>

              <button 
                onclick={() => nanobot.triggerSupportRefresh()}
                class="p-1.5 hover:bg-white/10 rounded-md transition-colors group/refresh"
                title="Refresh Inbox"
              >
                <RefreshCw class="w-3 h-3 text-cyan-400/60 group-hover/refresh:text-cyan-400 transition-colors " />
              </button>
            </div>
          {:else if nanobot.activeWidget === 'BRAIN_MANAGEMENT'}
            <div class="flex items-center gap-2 mr-4 animate-in fade-in slide-in-from-right-4 duration-500">
               <!-- Health Pillar -->
               <div class="hidden md:flex items-center gap-3 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg mr-2">
                 <div class="flex items-center gap-1.5">
                   <Activity class="w-3 h-3 text-emerald-400" />
                   <span class="text-[9px] font-mono text-gray-400 ">Health</span>
                   <span class="text-[10px] font-mono font-bold text-emerald-400">{nanobot.brainVectorHealth}%</span>
                 </div>
                 <div class="w-px h-3 bg-white/10"></div>
                 <div class="flex items-center gap-1.5">
                   <span class="text-[9px] font-mono text-gray-400 ">Nodes</span>
                   <span class="text-[10px] font-mono font-bold text-white">{nanobot.brainTotalNodes}</span>
                 </div>
               </div>

               <button 
                onclick={() => { nanobot.brainActionTrigger = 'SYNC'; }}
                disabled={nanobot.isBrainSyncing}
                class="flex items-center gap-2 px-3 py-1.5 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-[9px] font-black tracking-widest text-indigo-400 hover:bg-indigo-500/20 transition-all disabled:opacity-50"
              >
                <RefreshCw class="w-3 h-3 {nanobot.isBrainSyncing ? 'animate-spin' : ''}" />
                {nanobot.isBrainSyncing ? 'Sync' : 'Sync'}
              </button>
               <button 
                onclick={() => { nanobot.brainActionTrigger = 'PURGE'; }}
                class="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-lg text-[9px] font-black tracking-widest text-red-500 hover:bg-red-500/20 transition-all"
              >
                <Trash2 class="w-3 h-3" />
                Purge
              </button>

              <button 
                onclick={() => { nanobot.setBrainManualOpen(true); }}
                class="flex items-center gap-2 px-3 py-1.5 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-[9px] font-black tracking-widest text-cyan-400 hover:bg-cyan-500/20 transition-all"
              >
                <BookOpen class="w-3 h-3" />
                Manual
              </button>
            </div>
          {/if}

          <SupremeCloseButton 
            campaign_id={nanobot.activeWidget === 'CONTENT_REVIEW' ? WidgetData.campaign_id : undefined} 
            onClose={close}
          />
        </div>
      </div>
      {/if}

      <!-- Widget Content (scrollable container managed by widget internally for CONTENT_REVIEW) -->
      <div class="flex-1 {['CONTENT_REVIEW', 'ADS_PROTECTION', 'SECURITY_SOC', 'CTV_MANAGEMENT', 'APPOINTMENTS', 'SUPPORT_INBOX', 'BRAIN_MANAGEMENT', 'ORDER_MANAGEMENT', 'PRODUCT_MANAGEMENT', 'VOUCHER_MANAGEMENT', 'NEWS_MANAGEMENT', 'CATEGORY_MANAGEMENT', 'USER_MANAGEMENT', 'NOTIFICATION_MANAGEMENT', 'SEO_GRAPH'].includes(nanobot.activeWidget) ? 'overflow-hidden p-0' : 'overflow-y-auto overflow-x-hidden p-4'}">
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
