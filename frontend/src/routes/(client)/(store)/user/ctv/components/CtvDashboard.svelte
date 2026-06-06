<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import CreditCard from "@lucide/svelte/icons/credit-card";
  import Award from "@lucide/svelte/icons/award";
  import Coins from "@lucide/svelte/icons/coins";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import Copy from "@lucide/svelte/icons/copy";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import QrCode from "@lucide/svelte/icons/qr-code";
  import Users from "@lucide/svelte/icons/users";
  import History from "@lucide/svelte/icons/history";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import ChevronUp from "@lucide/svelte/icons/chevron-up";
  import Landmark from "@lucide/svelte/icons/landmark";

  import { authStore } from '$lib/state/authStore.svelte';
  import { logger } from '$lib/utils/logger';

  let {
    profile,
    commissions,
    globalStats,
    activeTab = $bindable(),
    referralLink,
    qrCodeUrl,

    // Modal triggers
    showQrCode = $bindable(),
    showFullPolicy = $bindable(),
    showBankModal = $bindable(),
    showWithdrawModal = $bindable(),
    showDeactivateConfirm = $bindable(),

    // Methods
    copyToClipboard,
    formatVnd,
    handleExportExcel,
    getPendingDaysLeft,
    parseBreakdown,
  } = $props<{
    profile: any;
    commissions: any[];
    globalStats: any;
    activeTab: string;
    referralLink: string;
    qrCodeUrl: string;

    showQrCode: boolean;
    showFullPolicy: boolean;
    showBankModal: boolean;
    showWithdrawModal: boolean;
    showDeactivateConfirm: boolean;

    copyToClipboard: (text: string) => void;
    formatVnd: (val: number) => string;
    handleExportExcel: () => void;
    getPendingDaysLeft: (createdAt: string) => string;
    parseBreakdown: (note: string | undefined) => any;
  }>();

  const canShare = $derived(typeof navigator !== 'undefined' && !!navigator.share);

  async function handleNativeShare() {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Trở thành Đại lý số Osmo',
          text: 'Tham gia mạng lưới Đại lý số & CTV thông minh của Osmo để nhận chiết khấu hoa hồng hấp dẫn!',
          url: referralLink,
        });
      } catch (err) {
        logger.warn('Native share failed', err);
      }
    }
  }
</script>

<div class="space-y-8" in:fade>
  
  <!-- Premium Glass Header Badge -->
  <div class="bg-gradient-to-br from-stone-100/90 via-white/70 to-stone-50/80 text-stone-900 rounded-2xl p-6 md:p-8 border border-white/80 relative overflow-hidden shadow-xl shadow-stone-900/5 backdrop-blur-xl">
    <div class="absolute -right-20 -top-20 w-52 h-52 bg-luxury-copper/5 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute -left-20 -bottom-20 w-44 h-44 bg-luxury-copper/5 rounded-full blur-3xl pointer-events-none"></div>
    <div class="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
      
      <div class="space-y-3">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="px-2.5 py-0.5 bg-luxury-copper/10 border border-luxury-copper/20 text-[#8C6239] text-[9px] tracking-[2px] font-black uppercase rounded-full">
            Tier {profile.tier_name || 'Đồng'}
          </span>
          <!-- Phase 1: Commission Rate Badge (TikTok/Shopee style) -->
          <span class="flex items-center gap-1 px-3 py-1 bg-[#8C6239] text-white text-[11px] font-black rounded-full shadow-sm shadow-[#8C6239]/30">
            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"/><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd"/></svg>
            Hoa hồng {((profile.tier?.commission_rate ?? profile.commission_rate ?? 0.15) * 100).toFixed(0)}%
          </span>
          <span class="flex items-center gap-1 text-[10px] text-[#8C6239] font-mono tracking-widest font-bold">
            <ShieldCheck class="w-3.5 h-3.5 text-[#8C6239]" /> AES-GCM SEALED
          </span>
        </div>
        
        <h2 class="text-2xl md:text-3xl font-serif italic text-stone-850 font-light">
          Xin chào, <span class="font-bold text-stone-900 not-italic">{authStore.user?.name}</span>
        </h2>

        <p class="text-xs text-stone-500 tracking-wider">
          Mã giới thiệu độc quyền của bạn: <strong class="text-[#8C6239] text-sm tracking-widest bg-white/80 px-3 py-1 rounded border border-white/95 font-mono uppercase ml-1 shadow-sm">{profile.ctv_code}</strong>
        </p>

        <!-- Phase 1: Tier Roadmap Progress (Shopee Affiliate style) -->
        {#if profile.tiers && profile.tiers.length > 1}
          <div class="pt-1 space-y-1.5">
            <p class="text-[9px] text-stone-400 font-bold tracking-widest uppercase">Lộ trình cấp bậc</p>
            <div class="flex items-center gap-1.5 flex-wrap">
              {#each profile.tiers as t}
                {@const isActive = t.name === (profile.tier?.name || profile.tier_name)}
                <div class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-black border transition-all
                  {isActive
                    ? 'bg-[#8C6239] border-[#8C6239] text-white shadow-sm'
                    : 'bg-white/60 border-white/80 text-stone-400 hover:text-stone-600'}
                ">
                  {t.name} · {(t.commission_rate * 100).toFixed(0)}%
                  {#if isActive}<span class="ml-0.5">✓</span>{/if}
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <!-- Link Share Hub -->
      <div class="bg-white/30 border border-white/60 rounded-xl p-4 space-y-3 lg:max-w-md w-full shadow-inner backdrop-blur-md">
        <span class="block text-[9px] tracking-[3px] font-black text-stone-400 uppercase">Liên kết tiếp thị của bạn</span>
        <div class="flex items-center bg-white/70 border border-white/85 rounded-lg p-1.5 pl-3 shadow-sm">
          <span class="text-[11px] text-stone-600 truncate flex-1 font-mono tracking-tight">{referralLink}</span>
          <div class="flex items-center gap-1.5 ml-2 shrink-0">
            {#if canShare}
              <button 
                onclick={handleNativeShare}
                class="p-2 hover:bg-white/85 text-[#8C6239] hover:text-luxury-copper rounded transition-colors"
                title="Chia sẻ liên kết"
              >
                <ExternalLink class="w-4 h-4" />
              </button>
            {/if}
            <button 
              onclick={() => copyToClipboard(referralLink)}
              class="p-2 hover:bg-white/85 text-[#8C6239] hover:text-luxury-copper rounded transition-colors"
              title="Sao chép liên kết"
            >
              <Copy class="w-4 h-4" />
            </button>
            <button 
              onclick={() => showQrCode = !showQrCode}
              class="p-2 hover:bg-white/85 text-[#8C6239] hover:text-luxury-copper rounded transition-colors"
              title="Mã QR"
            >
              <QrCode class="w-4 h-4" />
            </button>
          </div>
        </div>

        {#if showQrCode}
          <div class="flex flex-col items-center justify-center p-4 bg-white/90 rounded-lg mt-2 transition-all border border-white/80 shadow-md" transition:slide>
            <img src={qrCodeUrl} alt="Mã QR Giới thiệu" class="w-36 h-36" />
            <p class="text-[9px] text-stone-400 mt-2 font-medium tracking-wider">Quét mã để mua hàng qua mã CTV của bạn</p>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Financial Metrics Grid -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
    
    <!-- Current Balance -->
    <div class="bg-white rounded-xl p-3.5 sm:p-5 border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] hover:shadow-lg transition-all flex flex-col justify-between space-y-3 sm:space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-[9px] sm:text-[10px] tracking-[0.5px] font-bold text-stone-400 uppercase">Số dư khả dụng</span>
        <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-luxury-copper/10 flex items-center justify-center text-luxury-copper shrink-0">
          <Coins class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        </div>
      </div>
      <div>
        <p class="text-base sm:text-lg md:text-xl font-bold text-stone-800 font-mono tracking-tight break-all">{formatVnd(profile.balance || 0)}</p>
        <p class="text-[8px] sm:text-[9px] text-stone-400 mt-1">Rút tối thiểu 200k • Phê duyệt nhanh</p>
      </div>
      <button 
        onclick={() => showWithdrawModal = true}
        class="w-full py-2 sm:py-2.5 rounded-lg bg-stone-900 hover:bg-luxury-copper hover:text-stone-950 text-white font-bold text-[9px] sm:text-[10px] tracking-[0.5px] sm:tracking-[1px] transition-all mt-auto"
      >
        Rút tiền
      </button>
    </div>

    <!-- Total Revenue -->
    <div class="bg-white rounded-xl p-3.5 sm:p-5 border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] flex flex-col justify-between space-y-3 sm:space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-[9px] sm:text-[10px] tracking-[0.5px] font-bold text-stone-400 uppercase">Tổng doanh số</span>
        <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-500 shrink-0">
          <TrendingUp class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        </div>
      </div>
      <div>
        <p class="text-base sm:text-lg md:text-xl font-bold text-stone-800 font-mono tracking-tight break-all">{formatVnd(profile.total_revenue || 0)}</p>
        <p class="text-[8px] sm:text-[9px] text-stone-400 mt-1">Tổng đơn thành công</p>
      </div>
      <div class="text-[8px] sm:text-[9px] font-medium text-stone-500 bg-stone-50 py-2 sm:py-2.5 px-2 sm:px-3 rounded-lg text-center tracking-wider border border-stone-100 mt-auto">
        Chiết khấu: {((profile.tier?.commission_rate ?? profile.commission_rate ?? 0.05) * 100).toFixed(1)}%
      </div>
    </div>

    <!-- Total Commission -->
    <div class="bg-white rounded-xl p-3.5 sm:p-5 border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] flex flex-col justify-between space-y-3 sm:space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-[9px] sm:text-[10px] tracking-[0.5px] font-bold text-stone-400 uppercase">Tích lũy</span>
        <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-500 shrink-0">
          <Award class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        </div>
      </div>
      <div>
        <p class="text-base sm:text-lg md:text-xl font-bold text-stone-800 font-mono tracking-tight break-all">{formatVnd(profile.total_commission || 0)}</p>
        <p class="text-[8px] sm:text-[9px] text-stone-400 mt-1">Treo: {formatVnd(profile.pending_commission || 0)}</p>
      </div>
      <div class="text-[8px] sm:text-[9px] font-medium text-stone-500 bg-stone-50 py-2 sm:py-2.5 px-2 sm:px-3 rounded-lg text-center tracking-wider border border-stone-100 mt-auto truncate">
        Đã nhận: {formatVnd(profile.paid_commission || 0)}
      </div>
    </div>

    <!-- Total Referral Orders -->
    <div class="bg-white rounded-xl p-3.5 sm:p-5 border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] flex flex-col justify-between space-y-3 sm:space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-[9px] sm:text-[10px] tracking-[0.5px] font-bold text-stone-400 uppercase">Đơn hàng</span>
        <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-purple-50 flex items-center justify-center text-purple-500 shrink-0">
          <ShoppingBag class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        </div>
      </div>
      <div>
        <p class="text-base sm:text-lg md:text-xl font-bold text-stone-800 font-mono tracking-tight break-all">{profile.total_orders || 0} đơn</p>
        <p class="text-[8px] sm:text-[9px] text-stone-400 mt-1">Số đơn giới thiệu thành công</p>
      </div>
      <!-- Bank & Deactivate Buttons Row (Compact Icon-Only Layout) -->
      <div class="flex items-center justify-center gap-1.5 pt-2 sm:pt-3 border-t border-stone-100 mt-auto">
        <!-- Bank Update Button -->
        <button 
          onclick={() => showBankModal = true}
          class="flex-1 py-1.5 sm:py-2.5 rounded-lg border border-stone-200 hover:border-stone-400 hover:bg-stone-50 text-stone-600 hover:text-stone-800 transition-all flex items-center justify-center group relative"
          title="Cập nhật tài khoản ngân hàng"
        >
          <Landmark class="w-3.5 h-3.5 sm:w-4 sm:h-4 transition-transform group-hover:scale-110" />
        </button>

        <!-- Deactivate Button -->
        <button 
          onclick={() => showDeactivateConfirm = true}
          class="flex-1 py-1.5 sm:py-2.5 rounded-lg border border-red-100 hover:border-red-300 hover:bg-red-50/50 text-red-400 hover:text-red-500 transition-all flex items-center justify-center group relative"
          title="Hủy đăng ký chương trình CTV"
        >
          <svg class="w-3.5 h-3.5 sm:w-4 sm:h-4 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </div>

  </div>

  <!-- Navigation Tabs -->
  <div class="border-b border-stone-100 flex items-center gap-6">
    <button 
      onclick={() => activeTab = 'dashboard'}
      class="pb-3 text-xs tracking-[0.5px] font-bold relative transition-colors {activeTab === 'dashboard' ? 'text-stone-800 font-extrabold' : 'text-stone-400 hover:text-stone-600'}"
    >
      Tổng quan & cấp bậc
      {#if activeTab === 'dashboard'}
        <div class="absolute bottom-0 left-0 w-full h-0.5 bg-luxury-copper" transition:fade></div>
      {/if}
    </button>

    <button 
      onclick={() => activeTab = 'history'}
      class="pb-3 text-xs tracking-[0.5px] font-bold relative transition-colors {activeTab === 'history' ? 'text-stone-800 font-extrabold' : 'text-stone-400 hover:text-stone-600'}"
    >
      Lịch sử hoa hồng
      {#if activeTab === 'history'}
        <div class="absolute bottom-0 left-0 w-full h-0.5 bg-luxury-copper" transition:fade></div>
      {/if}
    </button>

    <button 
      onclick={() => activeTab = 'leaderboard'}
      class="pb-3 text-xs tracking-[0.5px] font-bold relative transition-colors {activeTab === 'leaderboard' ? 'text-stone-800 font-extrabold' : 'text-stone-400 hover:text-stone-600'}"
    >
      Bảng xếp hạng (Viral)
      {#if activeTab === 'leaderboard'}
        <div class="absolute bottom-0 left-0 w-full h-0.5 bg-luxury-copper" transition:fade></div>
      {/if}
    </button>
  </div>

  <!-- TAB CONTENTS -->
  {#if activeTab === 'dashboard'}
    <!-- Dashboard / Tiers Tab -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8" in:fade>
      
      <!-- Tier Progression -->
      <div class="lg:col-span-2 space-y-6 bg-white p-6 rounded-xl border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)]">
        <h3 class="text-sm font-serif italic text-stone-800 tracking-wide flex items-center gap-2">
          <Award class="w-4 h-4 text-luxury-copper" /> Tiến trình cấp bậc Đại lý số
        </h3>

        <!-- Progress Bar -->
        <div class="space-y-2 pt-2">
          <div class="flex items-center justify-between text-xs font-bold text-stone-600">
            <span>Cấp hiện tại: {profile.tier_name || 'Đồng'}</span>
            <span>Doanh số hiện tại: {formatVnd(profile.total_revenue || 0)}</span>
          </div>
          
          <!-- Simple visual tiers line -->
          <div class="w-full bg-stone-100 h-3 rounded-full overflow-hidden relative border border-stone-200/50">
            <div 
              class="bg-luxury-copper h-full transition-all duration-1000"
              style="width: {Math.min(100, ((profile.total_revenue || 0) / 100000000) * 100)}%"
            ></div>
          </div>
          
          <div class="flex items-center justify-between text-[10px] text-stone-400 font-mono">
            <span>0đ (Đồng)</span>
            <span>10M (Bạc)</span>
            <span>50M (Vàng)</span>
            <span>100M+ (Kim Cương)</span>
          </div>
        </div>

        <!-- Tiers details list (Dynamic from DB) -->
        <div class="space-y-3 pt-4 border-t border-stone-100">
          <span class="block text-[10px] tracking-[0.5px] font-bold text-stone-400">Quyền lợi chiết khấu theo cấp bậc</span>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
            {#if profile && profile.tiers && profile.tiers.length > 0}
              {#each profile.tiers as t}
                <div class="p-3.5 bg-stone-50 rounded-lg text-center border {profile.tier_name === t.name ? 'border-luxury-copper bg-amber-50/10' : 'border-stone-100'}">
                  <span class="block text-[9px] font-black text-stone-400 tracking-wider">{t.name}</span>
                  <span class="block text-sm font-bold text-stone-800 mt-1">{(t.commission_rate * 100).toFixed(1)}%</span>
                  {#if t.bonus_rate > 0}
                    <span class="block text-[8px] text-emerald-600 font-bold mt-0.5 font-mono">+{(t.bonus_rate * 100).toFixed(1)}% Thưởng</span>
                  {/if}
                  <span class="block text-[8px] text-stone-400 mt-1 font-mono">Từ {formatVnd(t.min_revenue_threshold)}</span>
                </div>
              {/each}
            {:else}
              <!-- Fallback backward compatibility static -->
              <div class="p-3.5 bg-stone-50 rounded-lg text-center border {profile?.tier_name === 'Đồng' ? 'border-luxury-copper bg-amber-50/10' : 'border-stone-100'}">
                <span class="block text-[9px] font-black text-stone-400 tracking-wider">Đồng</span>
                <span class="block text-sm font-bold text-stone-800 mt-1">5%</span>
                <span class="block text-[8px] text-stone-400 mt-1 font-mono">Từ 0đ</span>
              </div>
            {/if}
          </div>
        </div>

      </div>

      <!-- Referral Rules and Safety Guide (Collapsible with Dynamic Arrow Below Text) -->
      <div class="bg-stone-50 rounded-xl p-5 border border-stone-200/50 space-y-3 h-fit self-start">
        <div class="flex items-center justify-between text-left">
          <h3 class="text-xs tracking-[1px] font-bold text-stone-800 flex items-center gap-1.5">
            <ShieldCheck class="w-4 h-4 text-luxury-copper" /> Chính sách CTV & an toàn
          </h3>
        </div>
        
        <ul class="space-y-3.5 text-xs text-stone-600 leading-relaxed font-light transition-all duration-300">
          <li class="flex items-start gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-luxury-copper mt-1.5 shrink-0"></span>
            <span><strong>Bảo mật AES-GCM:</strong> Mọi biến động số dư và lịch sử giao dịch đều được đóng dấu mật mã bảo vệ.</span>
          </li>
          
          <li class="flex items-start gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-luxury-copper mt-1.5 shrink-0"></span>
            <span><strong>Phòng chống tự giới thiệu:</strong> Hệ thống tự động phát hiện và chặn các đơn hàng tự mua qua link CTV của chính mình.</span>
          </li>
          
          {#if showFullPolicy}
            <div class="space-y-3.5 pt-3.5 border-t border-stone-200/60" transition:slide>
              <li class="flex items-start gap-2">
                 <span class="w-1.5 h-1.5 rounded-full bg-luxury-copper mt-1.5 shrink-0"></span>
                <span><strong>Chiết khấu trực tiếp:</strong> osmo áp dụng mô hình liên kết trực tiếp (depth = 1), đảm bảo minh bạch, lành mạnh và tối ưu hóa lợi nhuận cao nhất cho CTV.</span>
              </li>
              <li class="flex items-start gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-luxury-copper mt-1.5 shrink-0"></span>
                <span><strong>Quy trình rút tiền:</strong> Lệnh rút tiền tối thiểu 200,000đ được Admin phê duyệt thủ công vào mỗi Thứ Sáu hàng tuần.</span>
              </li>
            </div>
          {/if}
        </ul>

        <!-- Expand / Collapse Arrow placed elegantly below the text -->
        <button 
          onclick={() => showFullPolicy = !showFullPolicy}
          class="w-full pt-2 mt-1 border-t border-stone-200/40 flex items-center justify-center gap-1 text-[9px] font-bold text-luxury-copper hover:text-amber-600 transition-colors tracking-[0.5px]"
        >
          {#if showFullPolicy}
            Thu gọn chính sách <ChevronUp class="w-3.5 h-3.5" />
          {:else}
            Xem thêm chính sách <ChevronDown class="w-3.5 h-3.5" />
          {/if}
        </button>

        <!-- Link to full affiliate policy article -->
        <a
          href="/quy-dinh-chinh-sach-doi-tac-affiliate-cong-tac-vien-ban-hang-tren-website-osmovn.html"
          target="_blank"
          rel="noopener noreferrer"
          class="w-full mt-1 flex items-center justify-center gap-1.5 text-[9px] font-bold text-sky-600 hover:text-sky-700 transition-colors tracking-[0.5px] py-1"
        >
          <ExternalLink class="w-3 h-3" /> Xem chi tiết Điều khoản & Chính sách CTV
        </a>
      </div>

    </div>
  {:else if activeTab === 'history'}
    <!-- Lịch sử hoa hồng Tab -->
    <div class="bg-white rounded-xl border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] lg:overflow-visible overflow-hidden" in:fade>
      
      <div class="px-6 py-4 border-b border-stone-100 flex items-center justify-between">
        <h3 class="text-xs tracking-[0.5px] font-bold text-stone-800 flex items-center gap-1.5">
          <History class="w-4 h-4 text-luxury-copper" /> Biến động số dư hoa hồng
        </h3>
        
        <button
          onclick={handleExportExcel}
          disabled={commissions.length === 0}
          class="px-3 py-1.5 bg-luxury-copper hover:bg-amber-600 disabled:bg-stone-100 disabled:text-stone-400 active:scale-95 text-stone-950 font-bold rounded-lg transition-all tracking-wider text-[9px] uppercase shadow-lg shadow-luxury-copper/5 flex items-center gap-1"
        >
          📊 Xuất Excel đối soát
        </button>
      </div>

      <!-- Desktop Table Layout -->
      <div class="hidden lg:block lg:overflow-visible overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-stone-50 border-b border-stone-100 text-[10px] tracking-[0.5px] font-bold text-stone-400">
              <th class="py-4 px-6">Mã đơn hàng</th>
              <th class="py-4 px-6 text-right">Doanh thu</th>
              <th class="py-4 px-6 text-right">Tỷ lệ</th>
              <th class="py-4 px-6 text-right">Hoa hồng nhận</th>
              <th class="py-4 px-6">Trạng thái</th>
              <th class="py-4 px-6">Thời gian</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-100 text-xs">
            {#if commissions.length === 0}
              <tr>
                <td colspan="6" class="py-12 text-center text-stone-400 font-light italic">
                  Bạn chưa phát sinh giao dịch hoa hồng nào. Hãy chia sẻ liên kết ngay!
                </td>
              </tr>
            {:else}
              {#each commissions as item}
                <tr class="hover:bg-stone-50/50 transition-colors hover:relative hover:z-40">
                  <td class="py-4 px-6 font-mono font-medium text-stone-700">#{item.order_id.split('-')[0].toUpperCase()}</td>
                  <td class="py-4 px-6 text-right font-mono font-medium text-stone-800">{formatVnd(item.order_amount)}</td>
                  <td class="py-4 px-6 text-right font-mono text-stone-500">{(item.rate_applied ?? profile.tier?.commission_rate ?? profile.commission_rate ?? 0.05) * 100}%</td>
                  <td class="py-4 px-6 text-right font-mono font-bold text-luxury-copper relative group cursor-help">
                    <span>+{formatVnd(item.commission_amount)}</span>
                    
                    <!-- Premium Glassmorphic Tooltip for breakdown details -->
                    {#if parseBreakdown(item.admin_note)}
                      {@const bd = parseBreakdown(item.admin_note)}
                      <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 hidden group-hover:block w-64 bg-stone-950/95 backdrop-blur-md border border-stone-850 text-[10px] text-stone-300 rounded-xl p-3.5 shadow-2xl z-[200] leading-relaxed text-left font-sans">
                        <!-- Arrow pointing down to the cell -->
                        <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-stone-950"></div>
                        
                        <h4 class="font-bold text-white mb-2 pb-1 border-b border-stone-850 flex items-center justify-between">
                          <span>📝 Chi tiết đối soát</span>
                          <span class="text-[8px] font-mono font-bold text-luxury-copper uppercase tracking-wider">Micsmo V2.2</span>
                        </h4>
                        
                        <div class="space-y-1.5 font-mono text-[9px]">
                          <div class="flex justify-between">
                            <span class="text-stone-500">Doanh thu gộp:</span>
                            <span class="text-white">{formatVnd(bd.order_total)}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-stone-500">Khấu trừ ship:</span>
                            <span class="text-red-400">-{formatVnd(bd.shipping_fee)}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-stone-500">Thuế thu nhập ({Math.round((bd.tax_rate || 0.03) * 100)}%):</span>
                            <span class="text-red-400">-{formatVnd(bd.tax_deduction)}</span>
                          </div>
                          <div class="h-[1px] bg-stone-850 my-1"></div>
                          <div class="flex justify-between">
                            <span class="text-stone-400 font-bold">Doanh thu thuần:</span>
                            <span class="text-emerald-400 font-bold">{formatVnd(bd.revenue_net)}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-stone-500">Tỷ lệ chiết khấu:</span>
                            <span class="text-luxury-copper font-bold">{(bd.rate_applied * 100).toFixed(1)}%</span>
                          </div>
                          
                          {#if bd.is_allocated && bd.allocation_details && bd.allocation_details.length > 0}
                            <div class="mt-2 pt-2 border-t border-stone-800 space-y-1.5">
                              <span class="block text-[8px] uppercase tracking-wider text-amber-500 font-black">Phân bổ doanh thu (Proportional Allocation):</span>
                              {#each bd.allocation_details as detail}
                                <div class="bg-stone-900/60 p-2 rounded border border-stone-850/80 space-y-1">
                                  <div class="flex justify-between text-[8px] font-bold text-white leading-tight">
                                    <span class="truncate max-w-[150px]">{detail.name} (x{detail.qty})</span>
                                    <span class="text-amber-400 font-mono">{(detail.rate * 100).toFixed(1)}%</span>
                                  </div>
                                  <div class="flex justify-between text-[8px] text-stone-400 font-mono">
                                    <span>pb {detail.fraction}%: {formatVnd(detail.allocated_revenue)}</span>
                                    <span class="text-luxury-copper">+{formatVnd(detail.gross_commission)}</span>
                                  </div>
                                </div>
                              {/each}
                            </div>
                          {/if}

                          <div class="h-[1px] bg-stone-850 my-1"></div>
                          <div class="flex justify-between text-xs pt-0.5">
                            <span class="text-white font-bold">Hoa hồng thực nhận:</span>
                            <span class="text-luxury-copper font-bold">+{formatVnd(bd.commission_amount)}</span>
                          </div>
                        </div>
                      </div>
                    {/if}

                    {#if !parseBreakdown(item.admin_note) && item.admin_note}
                      <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 hidden group-hover:block w-56 bg-stone-950/95 backdrop-blur-md border border-stone-850 text-[10px] text-stone-300 rounded-xl p-3.5 shadow-2xl z-[200] leading-relaxed text-left font-sans">
                        <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-stone-950"></div>
                        <h4 class="font-bold text-white mb-1.5 pb-1 border-b border-stone-800 flex items-center gap-1.5">
                          <span>⚠️ Ghi chú xử lý</span>
                        </h4>
                        <p class="font-mono text-[9px] leading-relaxed">{item.admin_note}</p>
                      </div>
                    {/if}
                  </td>
                  <td class="py-4 px-6 relative group">
                    <span class="px-2.5 py-1 rounded-full text-[9px] font-bold tracking-wide transition-all
                      {item.status === 'CONFIRMED' ? 'bg-amber-50 border border-amber-200 text-amber-600' : ''}
                      {item.status === 'PAID' ? 'bg-emerald-50 border border-emerald-200 text-emerald-600' : ''}
                      {item.status === 'PENDING' ? 'bg-orange-50/70 border border-orange-200 text-orange-600' : ''}
                      {item.status === 'CANCELLED' || item.status === 'VOIDED' ? 'bg-red-50 border border-red-200 text-red-500' : ''}
                    ">
                      {item.status === 'CONFIRMED' ? 'Khả dụng' : ''}
                      {item.status === 'PAID' ? 'Đã chi trả' : ''}
                      {item.status === 'PENDING' ? getPendingDaysLeft(item.created_at) : ''}
                      {item.status === 'CANCELLED' || item.status === 'VOIDED' ? 'Đã hủy bỏ' : ''}
                    </span>
                    
                    {#if item.status === 'PENDING'}
                      <!-- Premium Tooltip for 7-day Return Policy Validation -->
                      <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 hidden group-hover:block w-52 bg-stone-950 border border-stone-800 text-[10px] text-stone-300 rounded-lg p-2.5 shadow-xl z-[200] leading-relaxed text-left font-sans">
                        <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-stone-950"></div>
                        <p class="font-bold text-white mb-0.5">🔒 Đơn hàng đã ghi nhận</p>
                        <p>Đang đối soát theo chính sách 7 ngày đổi trả của Osmo. Hoa hồng sẽ tự động chuyển sang "Khả dụng" sau khi hết hạn đổi trả.</p>
                      </div>
                    {/if}
                  </td>
                  <td class="py-4 px-6 text-stone-400 font-mono">{new Date(item.created_at).toLocaleDateString('vi-VN')}</td>
                </tr>
              {/each}
            {/if}
          </tbody>
        </table>
      </div>

      <!-- Mobile Card List Layout -->
      <div class="block lg:hidden divide-y divide-stone-100">
        {#if commissions.length === 0}
          <div class="py-12 text-center text-stone-400 font-light italic text-xs">
            Bạn chưa phát sinh giao dịch hoa hồng nào. Hãy chia sẻ liên kết ngay!
          </div>
        {:else}
          {#each commissions as item}
            <div class="p-4 space-y-3 hover:bg-stone-50/50 transition-colors">
              <div class="flex items-center justify-between">
                <span class="font-mono font-bold text-stone-800 text-xs sm:text-sm">#{item.order_id.split('-')[0].toUpperCase()}</span>
                <span class="px-2.5 py-1 rounded-full text-[9px] font-bold tracking-wide
                  {item.status === 'CONFIRMED' ? 'bg-amber-50 border border-amber-200 text-amber-600' : ''}
                  {item.status === 'PAID' ? 'bg-emerald-50 border border-emerald-200 text-emerald-600' : ''}
                  {item.status === 'PENDING' ? 'bg-orange-50/70 border border-orange-200 text-orange-600' : ''}
                  {item.status === 'CANCELLED' || item.status === 'VOIDED' ? 'bg-red-50 border border-red-200 text-red-500' : ''}
                ">
                  {item.status === 'CONFIRMED' ? 'Khả dụng' : ''}
                  {item.status === 'PAID' ? 'Đã chi trả' : ''}
                  {item.status === 'PENDING' ? getPendingDaysLeft(item.created_at) : ''}
                  {item.status === 'CANCELLED' || item.status === 'VOIDED' ? 'Đã hủy bỏ' : ''}
                </span>
              </div>

              <div class="grid grid-cols-3 gap-2 text-[10px] sm:text-[11px] text-stone-500">
                <div>
                  <span class="block text-[8px] uppercase tracking-wider text-stone-400">Doanh thu</span>
                  <span class="font-mono font-semibold text-stone-700">{formatVnd(item.order_amount)}</span>
                </div>
                <div>
                  <span class="block text-[8px] uppercase tracking-wider text-stone-400">Tỷ lệ</span>
                  <span class="font-mono font-semibold text-stone-700">{(item.rate_applied ?? profile.tier?.commission_rate ?? profile.commission_rate ?? 0.05) * 100}%</span>
                </div>
                <div class="text-right">
                  <span class="block text-[8px] uppercase tracking-wider text-stone-400">Hoa hồng nhận</span>
                  <span class="font-mono font-extrabold text-luxury-copper text-xs sm:text-sm">+{formatVnd(item.commission_amount)}</span>
                </div>
              </div>

              <!-- Mobile Audit Breakdown Card -->
              {#if parseBreakdown(item.admin_note)}
                {@const bd = parseBreakdown(item.admin_note)}
                <div class="bg-stone-50 border border-stone-200/50 rounded-xl p-3 space-y-2.5 mt-2">
                  <div class="flex items-center justify-between text-[8px] text-stone-400 font-bold uppercase tracking-wider">
                    <span>📊 Chi tiết đối soát</span>
                    <span class="text-luxury-copper font-mono">Micsmo V2.2</span>
                  </div>
                  <div class="grid grid-cols-2 gap-x-4 gap-y-1.5 font-mono text-[9px] text-stone-600">
                    <div class="flex justify-between">
                      <span>Gộp:</span>
                      <span class="text-stone-850 font-medium">{formatVnd(bd.order_total)}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Thuần:</span>
                      <span class="text-emerald-600 font-bold">{formatVnd(bd.revenue_net)}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Phí ship:</span>
                      <span class="text-red-500 font-medium">-{formatVnd(bd.shipping_fee)}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Tỷ lệ tb:</span>
                      <span class="text-luxury-copper font-medium">{(bd.rate_applied * 100).toFixed(1)}%</span>
                    </div>
                    <div class="flex justify-between col-span-2 pt-1 border-t border-stone-200/50">
                      <span class="text-stone-500">Thuế TN ({Math.round((bd.tax_rate || 0.03) * 100)}%):</span>
                      <span class="text-red-500 font-bold">-{formatVnd(bd.tax_deduction)}</span>
                    </div>
                  </div>

                  {#if bd.is_allocated && bd.allocation_details && bd.allocation_details.length > 0}
                    <div class="pt-2 border-t border-stone-200 space-y-1.5">
                      <span class="block text-[8px] uppercase tracking-wider text-amber-600 font-black">Phân bổ doanh thu (Proportional):</span>
                      {#each bd.allocation_details as detail}
                        <div class="bg-stone-100/70 p-2 rounded border border-stone-200/60 space-y-0.5">
                          <div class="flex justify-between text-[8.5px] font-bold text-stone-800 leading-tight">
                            <span class="truncate max-w-[130px]">{detail.name} (x{detail.qty})</span>
                            <span class="text-amber-600 font-mono">{(detail.rate * 100).toFixed(1)}%</span>
                          </div>
                          <div class="flex justify-between text-[8px] text-stone-500 font-mono">
                            <span>pb {detail.fraction}%: {formatVnd(detail.allocated_revenue)}</span>
                            <span class="text-luxury-copper font-bold">+{formatVnd(detail.gross_commission)}</span>
                          </div>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              {:else if item.admin_note}
                <div class="bg-amber-50/40 border border-amber-200/40 rounded-xl p-3 text-[9px] text-stone-600 leading-relaxed">
                  <strong class="block text-[8px] uppercase tracking-wider text-stone-400 mb-1">⚠️ Ghi chú:</strong>
                  {item.admin_note}
                </div>
              {/if}

              <div class="text-[8px] text-stone-400 font-mono flex items-center justify-between pt-1 border-t border-stone-100/50">
                <span>Thời gian: {new Date(item.created_at).toLocaleDateString('vi-VN')} {new Date(item.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  {:else if activeTab === 'leaderboard'}
    <!-- Leaderboard (Bảng xếp hạng ẩn danh) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8" in:fade>
      
      <!-- Masked Leaderboard Table -->
      <div class="lg:col-span-2 bg-white rounded-xl border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] overflow-hidden">
        <div class="px-6 py-4 border-b border-stone-100">
          <h3 class="text-xs tracking-[0.5px] font-bold text-stone-800 flex items-center gap-1.5">
            <Users class="w-4 h-4 text-luxury-copper" /> Top đại lý số xuất sắc tháng
          </h3>
        </div>

        <!-- Desktop Leaderboard Table -->
        <div class="hidden lg:block lg:overflow-visible overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-stone-50 border-b border-stone-100 text-[10px] tracking-[0.5px] font-bold text-stone-400">
                <th class="py-4 px-6 text-center w-16">Hạng</th>
                <th class="py-4 px-6">Mã CTV</th>
                <th class="py-4 px-6">Cấp bậc</th>
                <th class="py-4 px-6 text-right">Tổng doanh số</th>
                <th class="py-4 px-6 text-center">Đơn giới thiệu</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-100 text-xs">
              {#if !globalStats?.leaderboard || globalStats.leaderboard.length === 0}
                <tr>
                  <td colspan="5" class="py-12 text-center text-stone-400 font-light italic">
                    Đang cập nhật bảng xếp hạng đại lý...
                  </td>
                </tr>
              {:else}
                {#each globalStats.leaderboard as row, idx}
                  <tr class="hover:bg-stone-50/50 transition-colors {idx < 3 ? 'bg-amber-50/5 font-semibold' : ''}">
                    <td class="py-4 px-6 text-center font-bold">
                      {#if idx === 0}
                        <span class="inline-flex w-6 h-6 items-center justify-center rounded-full bg-amber-400 text-stone-900 shadow">1</span>
                      {:else if idx === 1}
                        <span class="inline-flex w-6 h-6 items-center justify-center rounded-full bg-stone-300 text-stone-900 shadow">2</span>
                      {:else if idx === 2}
                        <span class="inline-flex w-6 h-6 items-center justify-center rounded-full bg-amber-600 text-white shadow">3</span>
                      {:else}
                        <span class="text-stone-400 font-mono">{idx + 1}</span>
                      {/if}
                    </td>
                    <td class="py-4 px-6 font-mono tracking-wider font-bold text-stone-700">{row.ctv_code_masked}</td>
                    <td class="py-4 px-6">
                      <span class="px-2 py-0.5 rounded-full text-[9px] font-bold tracking-wider border border-stone-200 text-stone-600 bg-stone-50">
                        {row.tier || 'Đồng'}
                      </span>
                    </td>
                    <td class="py-4 px-6 text-right font-mono font-bold text-stone-800">{formatVnd(row.total_revenue)}</td>
                    <td class="py-4 px-6 text-center font-mono font-medium text-stone-500">{row.total_orders} đơn</td>
                  </tr>
                {/each}
              {/if}
            </tbody>
          </table>
        </div>

        <!-- Mobile Leaderboard Layout -->
        <div class="block lg:hidden divide-y divide-stone-100">
          {#if !globalStats?.leaderboard || globalStats.leaderboard.length === 0}
            <div class="py-12 text-center text-stone-400 font-light italic text-xs">
              Đang cập nhật bảng xếp hạng đại lý...
            </div>
          {:else}
            {#each globalStats.leaderboard as row, idx}
              <div class="p-4 flex items-center justify-between hover:bg-stone-50/50 transition-colors {idx < 3 ? 'bg-amber-50/5' : ''}">
                <div class="flex items-center gap-3">
                  <!-- Rank Badge -->
                  <div class="w-8 h-8 flex items-center justify-center shrink-0">
                    {#if idx === 0}
                      <span class="inline-flex w-7 h-7 items-center justify-center rounded-full bg-amber-400 text-stone-900 shadow-md font-bold text-xs">1</span>
                    {:else if idx === 1}
                      <span class="inline-flex w-7 h-7 items-center justify-center rounded-full bg-stone-300 text-stone-900 shadow-md font-bold text-xs">2</span>
                    {:else if idx === 2}
                      <span class="inline-flex w-7 h-7 items-center justify-center rounded-full bg-amber-600 text-white shadow-md font-bold text-xs">3</span>
                    {:else}
                      <span class="text-stone-400 font-mono font-bold text-sm">{idx + 1}</span>
                    {/if}
                  </div>
                  
                  <div class="space-y-1">
                    <span class="font-mono tracking-wider font-bold text-stone-800 text-xs sm:text-sm block">{row.ctv_code_masked}</span>
                    <span class="inline-block px-2 py-0.5 rounded-full text-[9px] font-bold tracking-wider border border-stone-200 text-stone-600 bg-stone-50">
                      {row.tier || 'Đồng'}
                    </span>
                  </div>
                </div>

                <div class="text-right space-y-1">
                  <span class="font-mono font-extrabold text-stone-800 text-xs sm:text-sm block">{formatVnd(row.total_revenue)}</span>
                  <span class="text-[9px] text-stone-400 font-mono block">{row.total_orders} đơn</span>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>

      <!-- Banner Game Hóa / Viral Copy -->
      <div class="bg-gradient-to-tr from-stone-900 to-neutral-950 text-white p-6 rounded-xl border border-stone-800 space-y-6 relative overflow-hidden flex flex-col justify-between">
        <div class="absolute -right-20 -top-20 w-44 h-44 bg-luxury-copper/10 rounded-full blur-3xl pointer-events-none"></div>
        
        <div class="space-y-4">
          <span class="text-[9px] tracking-[2px] text-luxury-copper font-bold block">Bứt phá doanh số</span>
          <h3 class="text-lg font-serif italic text-stone-100 font-light">Thăng cấp Kim Cương - Nhận chiết khấu 25%</h3>
          <p class="text-xs text-stone-300 leading-relaxed font-light">
            osmo vinh danh các đại lý số có doanh số giới thiệu lớn hàng tháng bằng những phần thưởng bonus trực tiếp vào tài khoản ngân hàng liên kết. Càng chia sẻ nhiều, hoa hồng càng thụ động và bền vững!
          </p>
        </div>

        <div class="pt-6 border-t border-stone-800">
          <div class="flex items-center justify-between text-xs text-stone-400">
            <span>Tổng CTV toàn hệ thống</span>
            <span class="font-bold font-mono text-white text-sm">{globalStats?.summary?.total_ctv || 0}</span>
          </div>
          <div class="flex items-center justify-between text-xs text-stone-400 mt-2">
            <span>Đang hoạt động (Active)</span>
            <span class="font-bold font-mono text-emerald-400 text-sm">{globalStats?.summary?.active_ctv || 0}</span>
          </div>
        </div>
      </div>

    </div>
  {/if}

</div>
<style>
  /* Glass effect helper class */
  .bg-gradient-to-br {
    background-size: 200% 200%;
    animation: gradientShift 10s ease infinite;
  }
  @keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
</style>
