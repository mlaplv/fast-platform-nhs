<script lang="ts">
  import { onMount } from "svelte";
  import { fade, fly } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import type { BaseWidgetProps } from "$lib/types";

  // Lucide Icons
  import Award from "@lucide/svelte/icons/award";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import DollarSign from "@lucide/svelte/icons/dollar-sign";
  import Users from "@lucide/svelte/icons/users";
  import CreditCard from "@lucide/svelte/icons/credit-card";
  import Settings from "@lucide/svelte/icons/settings";
  import Search from "@lucide/svelte/icons/search";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import Plus from "@lucide/svelte/icons/plus";
  import Calendar from "@lucide/svelte/icons/calendar";
  import AlertTriangle from "@lucide/svelte/icons/alert-triangle";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Edit3 from "@lucide/svelte/icons/edit-3";

  let { isWidget = false, data = {} } = $props<BaseWidgetProps>();
  const nanobot = useNanobot();

  // Navigation Tabs
  let activeTab = $state<"stats" | "withdrawals" | "members" | "tiers">("stats");

  // Core States
  let isLoading = $state(true);

  // ── 1. Statistics Tab States ──
  interface StatsSummary {
    total_ctv: number;
    active_ctv: number;
    total_gmv: number;
    total_commission: number;
    pending_withdrawals: number;
  }
  interface LeaderboardItem {
    rank: number;
    ctv_code_masked: string;
    total_revenue: number;
    total_orders: number;
    tier: string;
  }
  let statsSummary = $state<StatsSummary>({
    total_ctv: 0,
    active_ctv: 0,
    total_gmv: 0.0,
    total_commission: 0.0,
    pending_withdrawals: 0,
  });
  let leaderboard = $state<LeaderboardItem[]>([]);

  // ── 2. Withdrawals Tab States ──
  interface BankInfo {
    bank?: string;
    account_no?: string;
    account_name?: string;
  }
  interface WithdrawalRequest {
    id: string;
    affiliate_id: string;
    ctv_code: string | null;
    amount_requested: number;
    amount_approved: number;
    bank_info: BankInfo;
    status: "PENDING" | "APPROVED" | "PAID" | "REJECTED";
    requested_at: string;
    processed_at: string | null;
    admin_note: string | null;
  }
  let withdrawals = $state<WithdrawalRequest[]>([]);
  let withdrawalTotal = $state(0);
  let withdrawalPage = $state(1);
  let withdrawalStatusFilter = $state<string>("PENDING");

  // ── 3. Members Tab States ──
  interface AffiliateProfile {
    id: string;
    ctv_code: string;
    user_id: string;
    status: "ACTIVE" | "SUSPENDED" | "BANNED";
    tier_name: string;
    commission_rate_pct: string;
    total_revenue: number;
    total_commission: number;
    paid_commission: number;
    total_orders: number;
    registered_at: string;
  }
  let members = $state<AffiliateProfile[]>([]);
  let memberTotal = $state(0);
  let memberPage = $state(1);
  let memberSearch = $state("");
  let memberStatusFilter = $state<string>("");

  // ── 4. Tiers Tab States ──
  interface CommissionTier {
    id: string;
    name: string;
    min_revenue_threshold: number;
    commission_rate: number;
    commission_rate_pct: string;
    bonus_rate: number;
    max_withdrawal_per_month: number;
    is_default: boolean;
  }
  let tiers = $state<CommissionTier[]>([]);
  let showTierModal = $state(false);
  let editingTier = $state<Partial<CommissionTier> | null>(null);

  // Tab Load triggers
  $effect(() => {
    const _tab = activeTab;
    loadTabData();
  });

  async function loadTabData() {
    isLoading = true;
    try {
      if (activeTab === "stats") {
        const res = await apiClient.get<{ summary: StatsSummary; leaderboard: LeaderboardItem[] }>(
          "/api/v1/admin/ctv/stats"
        );
        statsSummary = res.summary;
        leaderboard = res.leaderboard;
      } else if (activeTab === "withdrawals") {
        const params = new URLSearchParams({
          page: withdrawalPage.toString(),
          page_size: "15",
        });
        if (withdrawalStatusFilter) params.append("status", withdrawalStatusFilter);
        const res = await apiClient.get<{ items: WithdrawalRequest[]; total: number }>(
          `/api/v1/admin/ctv/withdrawals?${params.toString()}`
        );
        withdrawals = res.items;
        withdrawalTotal = res.total;
      } else if (activeTab === "members") {
        const params = new URLSearchParams({
          page: memberPage.toString(),
          page_size: "15",
        });
        if (memberSearch) params.append("search", memberSearch);
        if (memberStatusFilter) params.append("status", memberStatusFilter);
        const res = await apiClient.get<{ items: AffiliateProfile[]; total: number }>(
          `/api/v1/admin/ctv/members?${params.toString()}`
        );
        members = res.items;
        memberTotal = res.total;
      } else if (activeTab === "tiers") {
        const res = await apiClient.get<CommissionTier[]>("/api/v1/admin/ctv/tiers");
        tiers = res;
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      nanobot.showToast(`Lỗi tải dữ liệu: ${msg}`, "error");
    } finally {
      isLoading = false;
    }
  }

  // ── Payout approval flow ──
  async function handleApprovePayout(item: WithdrawalRequest) {
    const note = await nanobot.showConfirm({
      title: "DUYỆT CHI HOA HỒNG CTV",
      message: `Xác nhận thanh toán số tiền ${item.amount_requested.toLocaleString()}đ cho CTV ${item.ctv_code}?\nTài khoản nhận: ${item.bank_info.bank} - ${item.bank_info.account_no} (${item.bank_info.account_name})`,
      confirmLabel: "XÁC NHẬN ĐÃ CHUYỂN KHOẢN",
      cancelLabel: "Hủy bỏ",
      isPrompt: true,
      promptPlaceholder: "Nhập mã giao dịch ngân hàng hoặc ghi chú..."
    });

    if (note !== undefined) {
      try {
        await apiClient.post("/api/v1/admin/ctv/withdrawals/payout", {
          withdrawal_id: item.id,
          amount_approved: item.amount_requested,
          note: typeof note === "string" ? note : ""
        });
        nanobot.showToast("Đã duyệt chi hoa hồng thành công!", "success");
        loadTabData();
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        nanobot.showToast(`Lỗi thanh toán: ${msg}`, "error");
      }
    }
  }

  // ── Update Member Status ──
  async function handleUpdateMemberStatus(affiliateId: string, currentCode: string, newStatus: "ACTIVE" | "SUSPENDED" | "BANNED") {
    const note = await nanobot.showConfirm({
      title: "CẬP NHẬT TRẠNG THÁI CTV",
      message: `Bạn có chắc muốn chuyển CTV ${currentCode} sang trạng thái ${newStatus === 'ACTIVE' ? 'HOẠT ĐỘNG' : newStatus === 'SUSPENDED' ? 'TẠM KHÓA' : 'CẤM HOẠT ĐỘNG'}?`,
      confirmLabel: "CẬP NHẬT",
      cancelLabel: "Hủy",
      isPrompt: true,
      promptPlaceholder: "Lý do cập nhật trạng thái..."
    });

    if (note !== undefined) {
      try {
        await apiClient.patch(`/api/v1/admin/ctv/members/${affiliateId}/status`, {
          status: newStatus,
          note: typeof note === "string" ? note : ""
        });
        nanobot.showToast(`Đã chuyển trạng thái CTV ${currentCode} thành công!`, "success");
        loadTabData();
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        nanobot.showToast(`Lỗi: ${msg}`, "error");
      }
    }
  }

  // ── Manual Tier Change ──
  async function handleAssignTier(affiliateId: string, currentCode: string, tierId: string) {
    try {
      await apiClient.patch(`/api/v1/admin/ctv/members/${affiliateId}/tier`, {
        tier_id: tierId
      });
      nanobot.showToast(`Đã gán hạng mới cho CTV ${currentCode}!`, "success");
      loadTabData();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      nanobot.showToast(`Lỗi gán hạng: ${msg}`, "error");
    }
  }

  // ── Tier Create/Update ──
  function openTierModal(tier: CommissionTier | null = null) {
    if (tier) {
      editingTier = { ...tier };
    } else {
      editingTier = {
        name: "",
        min_revenue_threshold: 0,
        commission_rate: 0.15,
        bonus_rate: 0.0,
        max_withdrawal_per_month: 50000000,
        is_default: false
      };
    }
    showTierModal = true;
  }

  async function saveTier() {
    if (!editingTier || !editingTier.name) return;
    try {
      if (editingTier.id) {
        await apiClient.patch(`/api/v1/admin/ctv/tiers/${editingTier.id}`, editingTier);
        nanobot.showToast(`Đã cập nhật cấu hình hạng ${editingTier.name}`, "success");
      } else {
        await apiClient.post("/api/v1/admin/ctv/tiers", editingTier);
        nanobot.showToast(`Đã tạo cấu hình hạng ${editingTier.name} mới!`, "success");
      }
      showTierModal = false;
      loadTabData();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      nanobot.showToast(`Lỗi lưu cấu hình: ${msg}`, "error");
    }
  }

  onMount(() => {
    loadTabData();
  });
</script>

<div class="ctv-management w-full h-full flex flex-col bg-[#050505] text-gray-100 font-sans relative overflow-hidden">
  <!-- Dynamic Scanline decorative -->
  <div class="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-[#00FFFF]/30 to-transparent top-0 animate-pulse pointer-events-none"></div>

  <!-- Header Section -->
  <header class="px-6 py-4 border-b border-white/5 bg-[#0a0a0a]/90 shrink-0 flex flex-col md:flex-row md:items-center justify-between gap-4">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-lg bg-[#00FFFF]/10 border border-[#00FFFF]/30 flex items-center justify-center">
        <Award class="w-5 h-5 text-[#00FFFF]" />
      </div>
      <div>
        <h2 class="text-md font-bold tracking-widest text-[#00FFFF]">HỆ THỐNG LIÊN KẾT (CTV)</h2>
        <p class="text-[10px] font-mono text-gray-500 tracking-wider">VIRAL 2026 // COMMISSION PLATFORM</p>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex bg-black/60 border border-white/5 rounded-full p-1 self-start md:self-auto shrink-0">
      <button 
        onclick={() => activeTab = "stats"}
        class="px-4 py-1.5 text-xs font-bold tracking-widest rounded-full transition-all {activeTab === 'stats' ? 'bg-[#00FFFF]/10 text-[#00FFFF] border border-[#00FFFF]/20' : 'text-gray-400 hover:text-white border border-transparent'}"
      >
        TỔNG QUAN
      </button>
      <button 
        onclick={() => activeTab = "withdrawals"}
        class="px-4 py-1.5 text-xs font-bold tracking-widest rounded-full transition-all relative {activeTab === 'withdrawals' ? 'bg-[#00FFFF]/10 text-[#00FFFF] border border-[#00FFFF]/20' : 'text-gray-400 hover:text-white border border-transparent'}"
      >
        RÚT TIỀN
        {#if statsSummary.pending_withdrawals > 0}
          <span class="absolute -top-1 -right-1 px-1.5 py-0.5 text-[8px] font-bold bg-[#FE2C55] text-white rounded-full animate-bounce">
            {statsSummary.pending_withdrawals}
          </span>
        {/if}
      </button>
      <button 
        onclick={() => activeTab = "members"}
        class="px-4 py-1.5 text-xs font-bold tracking-widest rounded-full transition-all {activeTab === 'members' ? 'bg-[#00FFFF]/10 text-[#00FFFF] border border-[#00FFFF]/20' : 'text-gray-400 hover:text-white border border-transparent'}"
      >
        THÀNH VIÊN
      </button>
      <button 
        onclick={() => activeTab = "tiers"}
        class="px-4 py-1.5 text-xs font-bold tracking-widest rounded-full transition-all {activeTab === 'tiers' ? 'bg-[#00FFFF]/10 text-[#00FFFF] border border-[#00FFFF]/20' : 'text-gray-400 hover:text-white border border-transparent'}"
      >
        CẤP HOA HỒNG
      </button>
    </div>
  </header>

  <!-- Content Body -->
  <div class="flex-1 overflow-y-auto custom-scrollbar p-6">
    {#if isLoading}
      <div class="w-full h-64 flex flex-col items-center justify-center gap-4">
        <div class="w-10 h-10 border-2 border-[#00FFFF]/10 border-t-[#00FFFF] rounded-full animate-spin"></div>
        <span class="text-[9px] font-mono text-[#00FFFF]/50 tracking-[0.4em]">SYNCHRONIZING_CORE_STATE...</span>
      </div>
    {:else}
      <!-- ── TAB 1: STATISTICS ── -->
      {#if activeTab === "stats"}
        <div class="space-y-6" in:fade={{ duration: 300 }}>
          <!-- Stats Summary Grid -->
          <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <div class="bg-gray-900/40 border border-white/5 rounded-2xl p-4 flex flex-col justify-between h-24 hover:border-[#00FFFF]/20 transition-all duration-300">
              <span class="text-[9px] font-mono text-gray-500 tracking-wider">TỔNG THÀNH VIÊN</span>
              <div class="flex items-baseline justify-between mt-2">
                <span class="text-2xl font-black text-gray-100">{statsSummary.total_ctv}</span>
                <Users class="w-4 h-4 text-gray-600" />
              </div>
            </div>
            <div class="bg-gray-900/40 border border-white/5 rounded-2xl p-4 flex flex-col justify-between h-24 hover:border-[#00FFFF]/20 transition-all duration-300">
              <span class="text-[9px] font-mono text-[#39FF14] tracking-wider">ĐANG HOẠT ĐỘNG</span>
              <div class="flex items-baseline justify-between mt-2">
                <span class="text-2xl font-black text-[#39FF14]">{statsSummary.active_ctv}</span>
                <ShieldCheck class="w-4 h-4 text-[#39FF14]/40" />
              </div>
            </div>
            <div class="bg-gray-900/40 border border-white/5 rounded-2xl p-4 flex flex-col justify-between h-24 hover:border-[#00FFFF]/20 transition-all duration-300">
              <span class="text-[9px] font-mono text-gray-500 tracking-wider">TỔNG GMV (ĐƠN LIÊN KẾT)</span>
              <div class="flex items-baseline justify-between mt-2">
                <span class="text-xl font-black text-[#00FFFF]">{statsSummary.total_gmv.toLocaleString()}đ</span>
                <TrendingUp class="w-4 h-4 text-[#00FFFF]/40" />
              </div>
            </div>
            <div class="bg-gray-900/40 border border-white/5 rounded-2xl p-4 flex flex-col justify-between h-24 hover:border-[#00FFFF]/20 transition-all duration-300">
              <span class="text-[9px] font-mono text-gray-500 tracking-wider">TỔNG HOA HỒNG PHÁT SINH</span>
              <div class="flex items-baseline justify-between mt-2">
                <span class="text-xl font-black text-amber-500">{statsSummary.total_commission.toLocaleString()}đ</span>
                <DollarSign class="w-4 h-4 text-amber-500/40" />
              </div>
            </div>
            <div class="bg-gray-900/40 border border-[#FE2C55]/20 rounded-2xl p-4 flex flex-col justify-between h-24 hover:border-[#FE2C55]/40 transition-all duration-300 col-span-2 lg:col-span-1">
              <span class="text-[9px] font-mono text-[#FE2C55] tracking-wider">CHỜ DUYỆT RÚT TIỀN</span>
              <div class="flex items-baseline justify-between mt-2">
                <span class="text-2xl font-black text-[#FE2C55]">{statsSummary.pending_withdrawals}</span>
                <CreditCard class="w-4 h-4 text-[#FE2C55]/40" />
              </div>
            </div>
          </div>

          <!-- Leaderboard Grid -->
          <div class="bg-gray-900/20 border border-white/5 rounded-2xl p-6">
            <h3 class="text-sm font-bold tracking-widest text-[#00FFFF] mb-4 flex items-center gap-2">
              <Award class="w-4 h-4" /> BẢNG XẾP HẠNG DOANH SỐ CTV (TOP 10)
            </h3>
            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse text-xs">
                <thead>
                  <tr class="border-b border-white/5 text-gray-500 font-mono">
                    <th class="py-3 px-4">XẾP HẠNG</th>
                    <th class="py-3 px-4">MÃ CTV</th>
                    <th class="py-3 px-4 text-right">TỔNG DOANH SỐ (GMV)</th>
                    <th class="py-3 px-4 text-right">TỔNG ĐƠN HÀNG</th>
                    <th class="py-3 px-4">CẤP HẠNG</th>
                  </tr>
                </thead>
                <tbody>
                  {#each leaderboard as item (item.rank)}
                    <tr class="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                      <td class="py-3 px-4 font-mono font-bold">
                        {#if item.rank === 1}
                          <span class="text-amber-500">🏆 #1</span>
                        {:else if item.rank === 2}
                          <span class="text-gray-300">🥈 #2</span>
                        {:else if item.rank === 3}
                          <span class="text-amber-700">🥉 #3</span>
                        {:else}
                          #{item.rank}
                        {/if}
                      </td>
                      <td class="py-3 px-4 font-mono font-bold text-gray-200">{item.ctv_code_masked}</td>
                      <td class="py-3 px-4 text-right font-mono font-bold text-[#00FFFF]">{item.total_revenue.toLocaleString()}đ</td>
                      <td class="py-3 px-4 text-right font-mono text-gray-400">{item.total_orders} đơn</td>
                      <td class="py-3 px-4">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-white/5 border border-white/10 text-gray-300">
                          {item.tier}
                        </span>
                      </td>
                    </tr>
                  {:else}
                    <tr>
                      <td colspan="5" class="py-8 text-center text-gray-600 font-mono">CHƯA CÓ DỮ LIỆU BẢNG XẾP HẠNG</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      <!-- ── TAB 2: WITHDRAWAL REQUESTS ── -->
      {:else if activeTab === "withdrawals"}
        <div class="space-y-4" in:fade={{ duration: 300 }}>
          <!-- Filter Toolbar -->
          <div class="flex flex-col md:flex-row justify-between items-center gap-4 bg-[#0a0a0a]/50 p-4 border border-white/5 rounded-2xl">
            <div class="flex gap-2">
              <button 
                onclick={() => { withdrawalStatusFilter = "PENDING"; withdrawalPage = 1; loadTabData(); }}
                class="px-4 py-1.5 rounded-lg text-xs font-bold tracking-wider transition-colors {withdrawalStatusFilter === 'PENDING' ? 'bg-[#FE2C55]/10 text-[#FE2C55] border border-[#FE2C55]/20' : 'text-gray-400 hover:text-white bg-white/5'}"
              >
                ĐANG CHỜ ({statsSummary.pending_withdrawals})
              </button>
              <button 
                onclick={() => { withdrawalStatusFilter = "PAID"; withdrawalPage = 1; loadTabData(); }}
                class="px-4 py-1.5 rounded-lg text-xs font-bold tracking-wider transition-colors {withdrawalStatusFilter === 'PAID' ? 'bg-[#39FF14]/10 text-[#39FF14] border border-[#39FF14]/20' : 'text-gray-400 hover:text-white bg-white/5'}"
              >
                ĐÃ CHI TRẢ
              </button>
              <button 
                onclick={() => { withdrawalStatusFilter = ""; withdrawalPage = 1; loadTabData(); }}
                class="px-4 py-1.5 rounded-lg text-xs font-bold tracking-wider transition-colors {withdrawalStatusFilter === '' ? 'bg-[#00FFFF]/10 text-[#00FFFF] border border-[#00FFFF]/20' : 'text-gray-400 hover:text-white bg-white/5'}"
              >
                TẤT CẢ
              </button>
            </div>
            <button onclick={loadTabData} class="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
              <RefreshCw class="w-4 h-4" />
            </button>
          </div>

          <!-- Withdrawal Table -->
          <div class="bg-gray-900/20 border border-white/5 rounded-2xl overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse text-xs">
                <thead>
                  <tr class="border-b border-white/5 text-gray-500 font-mono bg-white/[0.01]">
                    <th class="py-3 px-4">CTV</th>
                    <th class="py-3 px-4">NGÀY YÊU CẦU</th>
                    <th class="py-3 px-4 text-right">SỐ TIỀN</th>
                    <th class="py-3 px-4">TÀI KHOẢN NGÂN HÀNG</th>
                    <th class="py-3 px-4">TRẠNG THÁI</th>
                    <th class="py-3 px-4">HÀNH ĐỘNG</th>
                  </tr>
                </thead>
                <tbody>
                  {#each withdrawals as item (item.id)}
                    <tr class="border-b border-white/5 hover:bg-white/[0.01] transition-colors">
                      <td class="py-3 px-4">
                        <div class="font-bold text-gray-200 font-mono">{item.ctv_code}</div>
                        <div class="text-[9px] text-gray-600 font-mono">{item.affiliate_id.slice(0, 8)}...</div>
                      </td>
                      <td class="py-3 px-4 font-mono text-gray-400">
                        {new Date(item.requested_at).toLocaleString("vi-VN")}
                      </td>
                      <td class="py-3 px-4 text-right font-mono font-bold text-amber-500">
                        {item.amount_requested.toLocaleString()}đ
                      </td>
                      <td class="py-3 px-4 font-mono text-gray-300">
                        <div class="font-bold">{item.bank_info.account_name}</div>
                        <div class="text-[10px] text-[#00FFFF]/80">{item.bank_info.bank} - {item.bank_info.account_no}</div>
                      </td>
                      <td class="py-3 px-4">
                        {#if item.status === "PENDING"}
                          <span class="px-2 py-0.5 rounded text-[9px] font-black bg-[#FE2C55]/10 border border-[#FE2C55]/20 text-[#FE2C55] tracking-widest animate-pulse">PENDING</span>
                        {:else if item.status === "PAID"}
                          <span class="px-2 py-0.5 rounded text-[9px] font-black bg-[#39FF14]/10 border border-[#39FF14]/20 text-[#39FF14] tracking-widest">PAID</span>
                        {:else}
                          <span class="px-2 py-0.5 rounded text-[9px] font-black bg-white/5 border border-white/10 text-gray-400 tracking-widest">{item.status}</span>
                        {/if}
                        {#if item.admin_note}
                          <div class="text-[9px] text-gray-500 italic mt-1 max-w-xs truncate" title={item.admin_note}>
                            "{item.admin_note}"
                          </div>
                        {/if}
                      </td>
                      <td class="py-3 px-4">
                        {#if item.status === "PENDING"}
                          <button 
                            onclick={() => handleApprovePayout(item)}
                            class="px-3 py-1 bg-[#39FF14]/10 border border-[#39FF14]/30 hover:bg-[#39FF14]/20 rounded-md text-[10px] font-bold text-[#39FF14] transition-all flex items-center gap-1 shrink-0"
                          >
                            <Check class="w-3.5 h-3.5" /> DUYỆT CHI
                          </button>
                        {:else}
                          <span class="text-[10px] text-gray-600 font-mono">-</span>
                        {/if}
                      </td>
                    </tr>
                  {:else}
                    <tr>
                      <td colspan="6" class="py-12 text-center text-gray-600 font-mono">CHƯA CÓ YÊU CẦU RÚT TIỀN NÀO TRONG BỘ LỌC</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      <!-- ── TAB 3: MEMBER LIST ── -->
      {:else if activeTab === "members"}
        <div class="space-y-4" in:fade={{ duration: 300 }}>
          <!-- Filter / Search Header -->
          <div class="flex flex-col md:flex-row justify-between items-center gap-4 bg-[#0a0a0a]/50 p-4 border border-white/5 rounded-2xl">
            <div class="relative w-full md:w-80 group">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30 group-focus-within:text-[#00FFFF] transition-colors" />
              <input 
                type="text" 
                placeholder="Tìm mã CTV..." 
                class="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-xs font-mono text-gray-100 placeholder:text-gray-600 focus:outline-none focus:border-[#00FFFF]/40 focus:bg-white/[0.08] transition-all"
                bind:value={memberSearch}
                oninput={() => { memberPage = 1; loadTabData(); }}
              />
            </div>

            <div class="flex gap-2 w-full md:w-auto self-end md:self-auto shrink-0 justify-end">
              <select 
                bind:value={memberStatusFilter}
                onchange={() => { memberPage = 1; loadTabData(); }}
                class="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none font-mono focus:border-[#00FFFF]/30"
              >
                <option value="" class="bg-[#050505] text-gray-300">TẤT CẢ TRẠNG THÁI</option>
                <option value="ACTIVE" class="bg-[#050505] text-gray-300">ACTIVE</option>
                <option value="SUSPENDED" class="bg-[#050505] text-gray-300">SUSPENDED</option>
                <option value="BANNED" class="bg-[#050505] text-gray-300">BANNED</option>
              </select>
              <button onclick={loadTabData} class="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
                <RefreshCw class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Members Table -->
          <div class="bg-gray-900/20 border border-white/5 rounded-2xl overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse text-xs">
                <thead>
                  <tr class="border-b border-white/5 text-gray-500 font-mono bg-white/[0.01]">
                    <th class="py-3 px-4">MÃ CTV</th>
                    <th class="py-3 px-4 text-right">DOANH THU (GMV)</th>
                    <th class="py-3 px-4 text-right">HOA HỒNG PHÁT SINH</th>
                    <th class="py-3 px-4 text-right">ĐÃ CHI TRẢ</th>
                    <th class="py-3 px-4">CẤP HẠNG</th>
                    <th class="py-3 px-4">TRẠNG THÁI</th>
                    <th class="py-3 px-4">HÀNH ĐỘNG</th>
                  </tr>
                </thead>
                <tbody>
                  {#each members as item (item.id)}
                    <tr class="border-b border-white/5 hover:bg-white/[0.01] transition-colors">
                      <td class="py-3 px-4">
                        <div class="font-bold text-gray-200 font-mono">{item.ctv_code}</div>
                        <div class="text-[9px] text-gray-500 font-mono">Đăng ký: {new Date(item.registered_at).toLocaleDateString("vi-VN")}</div>
                      </td>
                      <td class="py-3 px-4 text-right font-mono font-bold text-[#00FFFF]">
                        {item.total_revenue.toLocaleString()}đ
                      </td>
                      <td class="py-3 px-4 text-right font-mono font-bold text-amber-500">
                        {item.total_commission.toLocaleString()}đ
                      </td>
                      <td class="py-3 px-4 text-right font-mono font-bold text-[#39FF14]">
                        {item.paid_commission.toLocaleString()}đ
                      </td>
                      <td class="py-3 px-4">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-white/5 border border-white/10 text-gray-300">
                          {item.tier_name} ({item.commission_rate_pct})
                        </span>
                      </td>
                      <td class="py-3 px-4">
                        {#if item.status === "ACTIVE"}
                          <span class="px-2 py-0.5 rounded text-[9px] font-black bg-[#39FF14]/10 border border-[#39FF14]/20 text-[#39FF14] tracking-widest">ACTIVE</span>
                        {:else if item.status === "SUSPENDED"}
                          <span class="px-2 py-0.5 rounded text-[9px] font-black bg-amber-500/10 border border-amber-500/20 text-amber-500 tracking-widest">SUSPENDED</span>
                        {:else}
                          <span class="px-2 py-0.5 rounded text-[9px] font-black bg-[#FE2C55]/10 border border-[#FE2C55]/20 text-[#FE2C55] tracking-widest">BANNED</span>
                        {/if}
                      </td>
                      <td class="py-3 px-4 flex items-center gap-2">
                        <!-- Fast status switch -->
                        {#if item.status !== "ACTIVE"}
                          <button 
                            onclick={() => handleUpdateMemberStatus(item.id, item.ctv_code, "ACTIVE")}
                            class="p-1 hover:bg-[#39FF14]/20 border border-[#39FF14]/30 rounded text-[#39FF14] transition-colors"
                            title="Kích hoạt"
                          >
                            <Check class="w-3.5 h-3.5" />
                          </button>
                        {/if}
                        {#if item.status === "ACTIVE"}
                          <button 
                            onclick={() => handleUpdateMemberStatus(item.id, item.ctv_code, "SUSPENDED")}
                            class="p-1 hover:bg-amber-500/20 border border-amber-500/30 rounded text-amber-500 transition-colors"
                            title="Tạm khóa"
                          >
                            <AlertTriangle class="w-3.5 h-3.5" />
                          </button>
                        {/if}
                        {#if item.status !== "BANNED"}
                          <button 
                            onclick={() => handleUpdateMemberStatus(item.id, item.ctv_code, "BANNED")}
                            class="p-1 hover:bg-[#FE2C55]/20 border border-[#FE2C55]/30 rounded text-[#FE2C55] transition-colors"
                            title="Khóa vĩnh viễn"
                          >
                            <X class="w-3.5 h-3.5" />
                          </button>
                        {/if}
                      </td>
                    </tr>
                  {:else}
                    <tr>
                      <td colspan="7" class="py-12 text-center text-gray-600 font-mono">CHƯA CÓ THÀNH VIÊN CTV NÀO</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      <!-- ── TAB 4: COMMISSION TIERS ── -->
      {:else if activeTab === "tiers"}
        <div class="space-y-4" in:fade={{ duration: 300 }}>
          <!-- Toolbar -->
          <div class="flex justify-between items-center bg-[#0a0a0a]/50 p-4 border border-white/5 rounded-2xl">
            <span class="text-xs font-mono text-gray-500 tracking-wider">CẤU HÌNH CÁC TẦNG DOANH SỐ & % HOA HỒNG CHI TRẢ CHO CTV</span>
            <button 
              onclick={() => openTierModal(null)}
              class="px-4 py-1.5 bg-[#00FFFF] hover:bg-[#00FFFF]/80 text-black text-xs font-bold tracking-widest rounded-lg flex items-center gap-1.5 transition-all shadow-lg"
            >
              <Plus class="w-3.5 h-3.5" /> TẠO CẤP HẠNG MỚI
            </button>
          </div>

          <!-- Tiers Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {#each tiers as tier (tier.id)}
              <div class="bg-gray-900/40 border {tier.is_default ? 'border-[#00FFFF]/30 shadow-[0_0_20px_rgba(0,255,255,0.05)]' : 'border-white/5'} rounded-2xl p-5 relative hover:border-[#00FFFF]/30 transition-all duration-300 group">
                {#if tier.is_default}
                  <span class="absolute top-4 right-4 px-2 py-0.5 text-[8px] font-black bg-[#00FFFF]/10 border border-[#00FFFF]/20 text-[#00FFFF] rounded tracking-widest">DEFAULT TIER</span>
                {/if}

                <div class="flex flex-col justify-between h-full">
                  <div>
                    <h4 class="text-md font-black text-gray-200 tracking-widest uppercase mb-1">{tier.name}</h4>
                    <span class="text-[9px] font-mono text-gray-500 block mb-4">ID: {tier.id.slice(0, 8)}...</span>

                    <div class="space-y-2 border-t border-white/5 pt-4">
                      <div class="flex justify-between text-xs font-mono">
                        <span class="text-gray-500">Mốc Doanh thu:</span>
                        <span class="text-gray-200 font-bold">{tier.min_revenue_threshold.toLocaleString()}đ</span>
                      </div>
                      <div class="flex justify-between text-xs font-mono">
                        <span class="text-gray-500">Tỷ lệ hoa hồng:</span>
                        <span class="text-[#00FFFF] font-bold">{tier.commission_rate_pct}</span>
                      </div>
                      <div class="flex justify-between text-xs font-mono">
                        <span class="text-gray-500">Tỷ lệ thưởng:</span>
                        <span class="text-[#39FF14] font-bold">{tier.bonus_rate * 100}%</span>
                      </div>
                      <div class="flex justify-between text-xs font-mono">
                        <span class="text-gray-500">Hạn mức rút / tháng:</span>
                        <span class="text-amber-500 font-bold">{tier.max_withdrawal_per_month.toLocaleString()}đ</span>
                      </div>
                    </div>
                  </div>

                  <div class="mt-6 border-t border-white/5 pt-4 flex justify-end">
                    <button 
                      onclick={() => openTierModal(tier)}
                      class="px-3 py-1 bg-white/5 border border-white/10 hover:bg-[#00FFFF]/10 hover:border-[#00FFFF]/30 hover:text-[#00FFFF] rounded-md text-[10px] font-mono tracking-widest text-gray-400 transition-all flex items-center gap-1"
                    >
                      <Edit3 class="w-3 h-3" /> CẬP NHẬT
                    </button>
                  </div>
                </div>
              </div>
            {:else}
              <div class="col-span-full py-12 text-center text-gray-600 font-mono">CHƯA CÓ CẤU HÌNH TẦNG HOA HỒNG NÀO</div>
            {/each}
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

<!-- ── TIER DETAILS/FORM MODAL ── -->
{#if showTierModal && editingTier}
  <div class="fixed inset-0 z-[var(--z-admin-hud)] flex items-center justify-center p-4" transition:fade={{ duration: 200 }}>
    <div class="absolute inset-0 bg-black/80 backdrop-blur-md" onclick={() => showTierModal = false} role="presentation"></div>

    <div class="relative w-full max-w-md bg-[#0a0a0a] border border-[#00FFFF]/30 rounded-2xl shadow-2xl overflow-hidden p-6 z-10" transition:fly={{ y: 20, duration: 300 }}>
      <!-- Header -->
      <header class="mb-6 flex justify-between items-center">
        <h3 class="text-sm font-black tracking-widest text-[#00FFFF] uppercase">
          {editingTier.id ? 'CẬP NHẬT CẤP HẠNG CTV' : 'TẠO CẤP HẠNG CTV MỚI'}
        </h3>
        <button onclick={() => showTierModal = false} class="p-1 text-gray-500 hover:text-white transition-colors">
          <X class="w-4 h-4" />
        </button>
      </header>

      <!-- Form -->
      <div class="space-y-4 text-xs">
        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-gray-500">TÊN CẤP HẠNG</label>
          <input 
            type="text" 
            class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-[#00FFFF]/30 transition-all"
            placeholder="Ví dụ: Đồng, Bạc, Vàng..."
            bind:value={editingTier.name}
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-gray-500">MỐC DOANH THU TỐI THIỂU (GMV)</label>
          <input 
            type="number" 
            class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-[#00FFFF]/30 transition-all font-mono"
            placeholder="0"
            bind:value={editingTier.min_revenue_threshold}
          />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="font-mono text-gray-500">TỶ LỆ HOA HỒNG (0.0 -> 1.0)</label>
            <input 
              type="number" 
              step="0.01"
              class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-[#00FFFF]/30 transition-all font-mono"
              placeholder="0.15"
              bind:value={editingTier.commission_rate}
            />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="font-mono text-gray-500">TỶ LỆ THƯỞNG BONUS</label>
            <input 
              type="number" 
              step="0.01"
              class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-[#00FFFF]/30 transition-all font-mono"
              placeholder="0.0"
              bind:value={editingTier.bonus_rate}
            />
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-gray-500">HẠN MỨC RÚT TIỀN TỐI ĐA / THÁNG</label>
          <input 
            type="number" 
            class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-[#00FFFF]/30 transition-all font-mono"
            placeholder="50,000,000"
            bind:value={editingTier.max_withdrawal_per_month}
          />
        </div>

        <div class="flex items-center gap-2 mt-2">
          <input 
            type="checkbox" 
            id="tier-default"
            class="accent-[#00FFFF]"
            bind:checked={editingTier.is_default}
          />
          <label for="tier-default" class="font-mono text-gray-400 select-none cursor-pointer">Đặt làm cấp hạng mặc định khi đăng ký</label>
        </div>
      </div>

      <!-- Action Footer -->
      <footer class="mt-8 flex justify-end gap-3">
        <button 
          onclick={() => showTierModal = false}
          class="px-4 py-2 border border-white/10 bg-transparent text-xs font-bold text-gray-400 hover:text-white rounded-lg transition-colors"
        >
          HỦY BỎ
        </button>
        <button 
          onclick={saveTier}
          class="px-4 py-2 bg-[#00FFFF] text-black text-xs font-bold rounded-lg transition-colors hover:bg-[#00FFFF]/80"
        >
          LƯU CẤU HÌNH
        </button>
      </footer>
    </div>
  </div>
{/if}

<style>
  .scrollbar-mission::-webkit-scrollbar {
    width: 3px;
  }
  .scrollbar-mission::-webkit-scrollbar-track {
    background: transparent;
  }
  .scrollbar-mission::-webkit-scrollbar-thumb {
    background: rgba(0, 243, 255, 0.1);
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
    height: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
</style>
