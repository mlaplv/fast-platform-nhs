<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, slide, scale } from 'svelte/transition';
  import { apiClient, ApiError } from '$lib/utils/apiClient';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import UserPageWrapper from '$lib/components/storefront/user/UserPageWrapper.svelte';
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
  import ArrowUpRight from "@lucide/svelte/icons/arrow-up-right";
  import Landmark from "@lucide/svelte/icons/landmark";
  import Lock from "@lucide/svelte/icons/lock";

  interface CtvProfile {
    is_registered: boolean;
    ctv_code?: string;
    encrypted_code?: string;
    tier_name?: string;
    commission_rate?: number;
    balance?: number;
    total_revenue?: number;
    total_commission?: number;
    paid_commission?: number;
    total_orders?: number;
    status?: 'ACTIVE' | 'PENDING' | 'SUSPENDED' | 'BANNED' | 'CANCELLED';
    tiers?: Array<{
      name: string;
      commission_rate: number;
      min_revenue_threshold: number;
      bonus_rate: number;
    }>;
    bank_info?: {
      bank?: string;
      account_no?: string;
      account_name?: string;
    };
  }

  interface CommissionItem {
    order_id: string;
    order_amount: number;
    commission_rate: number;
    commission_amount: number;
    status: 'PENDING' | 'CONFIRMED' | 'PAID' | 'CANCELLED';
    created_at: string;
  }

  interface LeaderboardRow {
    ctv_code_masked: string;
    tier?: string;
    total_revenue: number;
    total_orders: number;
  }

  interface GlobalStats {
    summary?: {
      total_ctv?: number;
      active_ctv?: number;
    };
    leaderboard?: LeaderboardRow[];
  }

  const ui = getClientUi();

  // CTV profile state
  let profile = $state<CtvProfile | null>(null);
  let commissions = $state<CommissionItem[]>([]);
  let globalStats = $state<GlobalStats | null>(null);
  let isLoading = $state(true);
  let activeTab = $state('dashboard'); // dashboard | history | leaderboard

  // Form states
  let isRegistering = $state(false);
  let regCode = $state('');
  let regReferredBy = $state('');
  let regError = $state('');

  // Bank form state
  let showBankModal = $state(false);
  let bankName = $state('');
  let bankAccountNo = $state('');
  let bankAccountName = $state('');
  let isUpdatingBank = $state(false);

  // Withdraw form state
  let showWithdrawModal = $state(false);
  let withdrawAmount = $state<number>(200000);
  let isWithdrawing = $state(false);

  // QR display
  let showQrCode = $state(false);
  let isDeactivating = $state(false);
  let showDeactivateConfirm = $state(false);
  let showFullPolicy = $state(false);

  onMount(async () => {
    await loadCtvData();
  });

  async function loadCtvData() {
    isLoading = true;
    try {
      // 1. Fetch profile
      const rawProfile = await apiClient.get<CtvProfile>('/client/ctv/profile');
      // Guard: infer is_registered from ctv_code presence (backward compat)
      profile = {
        ...rawProfile,
        is_registered: rawProfile.is_registered ?? !!rawProfile.ctv_code,
      };
      if (profile && profile.bank_info) {
        bankName = profile.bank_info.bank || '';
        bankAccountNo = profile.bank_info.account_no || '';
        bankAccountName = profile.bank_info.account_name || '';
      }
      
      // 2. Fetch history and leaderboard if registered
      if (profile?.is_registered) {
        const commData = await apiClient.get<{ items: CommissionItem[] }>('/client/ctv/commissions?page=1&page_size=30');
        commissions = commData.items || [];
      }
      
      // 3. Global stats: client CTV không có quyền admin — bỏ qua silently
    } catch (e: any) {
      // Not registered yet
      if (e instanceof ApiError && e.status === 404) {
        profile = { is_registered: false };
      } else {
        console.error(e);
      }
    } finally {
      isLoading = false;
    }
  }

  // Handle Registration
  async function handleRegister(e: Event) {
    e.preventDefault();
    regError = '';
    isRegistering = true;
    
    try {
      const res = await apiClient.post<any>('/client/ctv/register', {
        ctv_code: regCode.trim().toUpperCase(),
        referred_by_code: regReferredBy.trim().toUpperCase() || undefined
      });
      ui.showToast(res.message || 'Đăng ký CTV thành công!', 'success');
      await loadCtvData();
    } catch (e: any) {
      regError = e.message || 'Đăng ký thất bại. Vui lòng kiểm tra lại.';
    } finally {
      isRegistering = false;
    }
  }

  // Handle Bank Update
  async function handleUpdateBank(e: Event) {
    e.preventDefault();
    if (!bankName || !bankAccountNo || !bankAccountName) {
      ui.showToast('Vui lòng điền đầy đủ thông tin ngân hàng', 'warning');
      return;
    }
    
    isUpdatingBank = true;
    try {
      await apiClient.patch('/client/ctv/bank-info', {
        bank: bankName.trim(),
        account_no: bankAccountNo.trim(),
        account_name: bankAccountName.trim().toUpperCase()
      });
      ui.showToast('Cập nhật tài khoản ngân hàng thành công!', 'success');
      showBankModal = false;
      await loadCtvData();
    } catch (e: any) {
      ui.showToast(e.message || 'Cập nhật thất bại', 'error');
    } finally {
      isUpdatingBank = false;
    }
  }

  // Handle Withdrawal request
  async function handleWithdraw(e: Event) {
    e.preventDefault();
    if (withdrawAmount < 200000) {
      ui.showToast('Số tiền rút tối thiểu là 200,000đ', 'warning');
      return;
    }
    if (withdrawAmount > (profile?.balance || 0)) {
      ui.showToast('Số dư khả dụng không đủ', 'warning');
      return;
    }
    if (!profile?.bank_info?.bank) {
      ui.showToast('Vui lòng liên kết tài khoản ngân hàng trước khi rút tiền', 'warning');
      showBankModal = true;
      showWithdrawModal = false;
      return;
    }

    isWithdrawing = true;
    try {
      await apiClient.post('/client/ctv/withdraw', {
        amount: withdrawAmount
      });
      ui.showToast('Đã gửi yêu cầu rút tiền. Vui lòng đợi Admin phê duyệt.', 'success');
      showWithdrawModal = false;
      await loadCtvData();
    } catch (e: any) {
      ui.showToast(e.message || 'Yêu cầu rút tiền thất bại', 'error');
    } finally {
      isWithdrawing = false;
    }
  }

  // Clipboard share helper
  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    ui.showToast('Đã sao chép liên kết giới thiệu độc quyền!', 'success');
  }

  // Format currency
  function formatVnd(val: number): string {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  }

  // Calculate remaining return days (7-day Osmo policy)
  function getPendingDaysLeft(createdAtStr: string): string {
    try {
      const created = new Date(createdAtStr);
      const now = new Date();
      const diffTime = now.getTime() - created.getTime();
      const diffDays = diffTime / (1000 * 60 * 60 * 24);
      const left = Math.ceil(7 - diffDays);
      if (left <= 0) return 'Đối soát';
      return `Chờ duyệt (${left} ngày)`;
    } catch (e) {
      return 'Chờ duyệt';
    }
  }

  // Handle CTV Deactivation — 2-step confirm flow
  async function handleDeactivate() {
    isDeactivating = true;
    try {
      await apiClient.delete('/client/ctv/profile');
      ui.showToast('Đã rời chương trình CTV thành công. Hẹn gặp lại!', 'success');
      showDeactivateConfirm = false;
      profile = { is_registered: false };
    } catch (e: any) {
      ui.showToast(e.message || 'Không thể hủy đăng ký lúc này. Vui lòng thử lại.', 'error');
    } finally {
      isDeactivating = false;
    }
  }

  const referralLink = $derived(
    profile?.encrypted_code 
      ? `${window.location.origin}?ctv=${profile.encrypted_code}` 
      : (profile?.ctv_code ? `${window.location.origin}?ctv=${profile.ctv_code}` : '')
  );
  const qrCodeUrl = $derived(referralLink ? `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(referralLink)}` : '');
</script>

<UserPageWrapper 
  title="Kênh Đại lý số & CTV" 
  description="Chia sẻ liên kết độc quyền của bạn để nhận hoa hồng trọn đời từ osmo."
>
  {#if isLoading}
    <div class="flex flex-col items-center justify-center py-20 gap-4" in:fade>
      <div class="w-10 h-10 border-2 border-stone-100 border-t-luxury-copper rounded-full animate-spin"></div>
      <p class="text-[10px] font-black tracking-widest text-stone-400">ĐANG TẢI DỮ LIỆU CTV...</p>
    </div>
  {:else if profile?.status === 'BANNED'}
    <!-- BANNED ACCOUNT VIEW -->
    <div class="max-w-xl mx-auto py-12 animate-fade-in" in:fade>
      <div class="bg-white border border-red-100 rounded-2xl p-8 shadow-xl text-center space-y-6">
        <div class="w-16 h-16 bg-red-50 border border-red-100 rounded-2xl flex items-center justify-center mx-auto text-red-500">
          <Lock class="w-8 h-8 animate-pulse" />
        </div>
        <div class="space-y-2">
          <span class="text-[10px] tracking-[4px] text-red-500 font-mono font-black uppercase">TÀI KHOẢN CTV BỊ KHÓA</span>
          <h2 class="text-xl font-bold text-stone-900 tracking-tight">Quyền truy cập đã bị đình chỉ</h2>
          <p class="text-xs text-stone-500 max-w-sm mx-auto leading-relaxed mt-2">
            Tài khoản cộng tác viên của bạn đã bị khóa do vi phạm chính sách của Osmo. Vui lòng liên hệ với bộ phận hỗ trợ khách hàng để được giải đáp.
          </p>
        </div>
        <div class="pt-4 border-t border-stone-100">
          <a href="/support" class="inline-block px-6 py-2.5 bg-stone-900 hover:bg-stone-850 text-white rounded-xl text-xs font-bold transition-all">
            Liên hệ hỗ trợ ngay
          </a>
        </div>
      </div>
    </div>
  {:else if profile?.status === 'SUSPENDED'}
    <!-- SUSPENDED ACCOUNT VIEW -->
    <div class="max-w-xl mx-auto py-12 animate-fade-in" in:fade>
      <div class="bg-white border border-orange-100 rounded-2xl p-8 shadow-xl text-center space-y-6">
        <div class="w-16 h-16 bg-orange-50 border border-orange-100 rounded-2xl flex items-center justify-center mx-auto text-orange-500">
          <Lock class="w-8 h-8" />
        </div>
        <div class="space-y-2">
          <span class="text-[10px] tracking-[4px] text-orange-500 font-mono font-black uppercase">TÀI KHOẢN TẠM ĐÌNH CHỈ</span>
          <h2 class="text-xl font-bold text-stone-900 tracking-tight">Tạm ngưng hoạt động kênh CTV</h2>
          <p class="text-xs text-stone-500 max-w-sm mx-auto leading-relaxed mt-2">
            Kênh cộng tác viên của bạn đang tạm thời bị đình chỉ để phục vụ đối soát định kỳ. Vui lòng quay lại sau hoặc liên hệ Admin.
          </p>
        </div>
        <div class="pt-4 border-t border-stone-100">
          <a href="/support" class="inline-block px-6 py-2.5 bg-stone-900 hover:bg-stone-850 text-white rounded-xl text-xs font-bold transition-all">
            Liên hệ hỗ trợ
          </a>
        </div>
      </div>
    </div>
  {:else if !profile?.is_registered}
    <!-- REGISTRATION FLOW -->
    <div class="max-w-xl mx-auto py-6" in:fade>
      <div class="bg-gradient-to-tr from-stone-900 to-neutral-950 text-white rounded-2xl p-8 shadow-xl border border-stone-800 relative overflow-hidden">
        <!-- Decoration background -->
        <div class="absolute -right-16 -top-16 w-48 h-48 bg-luxury-copper/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -left-16 -bottom-16 w-48 h-48 bg-amber-500/5 rounded-full blur-3xl pointer-events-none"></div>

        <div class="relative z-10 space-y-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-luxury-copper/20 rounded-xl flex items-center justify-center border border-luxury-copper/30">
              <Award class="w-5 h-5 text-luxury-copper" />
            </div>
            <div>
              <span class="text-[10px] tracking-[4px] text-luxury-copper font-black">CHƯƠNG TRÌNH ĐẠI LÝ SỐ</span>
              <h2 class="text-xl font-serif italic tracking-wide">Trở thành đối tác osmo</h2>
            </div>
          </div>

          <p class="text-xs text-stone-300 leading-relaxed font-light">
            Tham gia mạng lưới đại lý số & CTV thông minh của osmo. Nhận ngay chiết khấu hoa hồng hấp dẫn theo cấp bậc trên mỗi đơn hàng được giới thiệu thành công. Không cần ôm hàng, không cần vận chuyển.
          </p>

          <form onsubmit={handleRegister} class="space-y-4 pt-4 border-t border-stone-800">
            {#if regError}
              <div class="p-3 bg-red-950/50 border border-red-900/50 text-red-400 text-xs rounded-lg animate-pulse">
                {regError}
              </div>
            {/if}

            <div class="space-y-2">
              <label for="regCode" class="block text-[10px] tracking-[2px] font-bold text-stone-400 uppercase">Mã giới thiệu mong muốn</label>
              <input 
                id="regCode"
                type="text" 
                bind:value={regCode}
                placeholder="VD: MINHMINH99, LOUISTHANH" 
                class="w-full bg-stone-900/60 border border-stone-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-luxury-copper text-white uppercase font-bold tracking-wider placeholder:text-stone-600 transition-colors"
                required
                minlength="4"
                maxlength="20"
              />
              <p class="text-[9px] text-stone-500 tracking-wider">Viết liền không dấu, từ 4-20 ký tự (Chỉ gồm chữ và số).</p>
            </div>

            <div class="space-y-2">
              <label for="regReferredBy" class="block text-[10px] tracking-[2px] font-bold text-stone-400 uppercase">Mã giới thiệu người bảo trợ (Nếu có)</label>
              <input 
                id="regReferredBy"
                type="text" 
                bind:value={regReferredBy}
                placeholder="Nhập mã của người giới thiệu bạn" 
                class="w-full bg-stone-900/60 border border-stone-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-luxury-copper text-white uppercase tracking-wider placeholder:text-stone-600 transition-colors"
                maxlength="20"
              />
            </div>

            <button 
              type="submit" 
              disabled={isRegistering}
              class="w-full py-4 rounded-xl bg-luxury-copper hover:bg-amber-600 disabled:bg-stone-800 text-stone-950 font-black text-xs tracking-[4px] uppercase active:scale-[0.98] transition-all shadow-lg shadow-luxury-copper/10 mt-6"
            >
              {#if isRegistering}
                ĐANG KÍCH HOẠT...
              {:else}
                ĐĂNG KÝ NGAY
              {/if}
            </button>
          </form>
        </div>
      </div>
    </div>
  {:else}
    <!-- ACTIVE CTV DASHBOARD -->
    <div class="space-y-8" in:fade>
      
      <!-- Premium Glass Header Badge -->
      <div class="bg-gradient-to-tr from-stone-900 to-neutral-950 text-white rounded-2xl p-6 md:p-8 border border-stone-800 relative overflow-hidden shadow-xl">
        <div class="absolute -right-20 -top-20 w-52 h-52 bg-luxury-copper/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          
          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <span class="px-2.5 py-0.5 bg-luxury-copper/20 border border-luxury-copper/30 text-luxury-copper text-[9px] tracking-[2px] font-black uppercase rounded-full">
                Tier {profile.tier_name || 'Đồng'}
              </span>
              <span class="flex items-center gap-1 text-[10px] text-stone-400 font-mono tracking-widest">
                <ShieldCheck class="w-3.5 h-3.5 text-emerald-500" /> AES-GCM SEALED
              </span>
            </div>
            
            <h2 class="text-2xl md:text-3xl font-serif italic text-stone-100 font-light">
              Xin chào, <span class="font-bold text-white not-italic">{authStore.user?.name}</span>
            </h2>
            
            <p class="text-xs text-stone-400 tracking-wider">
              Mã giới thiệu độc quyền của bạn: <strong class="text-luxury-copper text-sm tracking-widest bg-stone-900/80 px-3 py-1 rounded border border-stone-800 font-mono uppercase ml-1">{profile.ctv_code}</strong>
            </p>
          </div>

          <!-- Link Share Hub -->
          <div class="bg-stone-900/60 border border-stone-800/80 rounded-xl p-4 space-y-3 lg:max-w-md w-full">
            <span class="block text-[9px] tracking-[3px] font-black text-stone-500 uppercase">Liên kết tiếp thị của bạn</span>
            <div class="flex items-center bg-stone-950 border border-stone-800 rounded-lg p-1.5 pl-3">
              <span class="text-[11px] text-stone-400 truncate flex-1 font-mono tracking-tight">{referralLink}</span>
              <div class="flex items-center gap-1.5 ml-2 shrink-0">
                <button 
                  onclick={() => copyToClipboard(referralLink)}
                  class="p-2 hover:bg-stone-900 text-stone-300 hover:text-luxury-copper rounded transition-colors"
                  title="Sao chép liên kết"
                >
                  <Copy class="w-4 h-4" />
                </button>
                <button 
                  onclick={() => showQrCode = !showQrCode}
                  class="p-2 hover:bg-stone-900 text-stone-300 hover:text-luxury-copper rounded transition-colors"
                  title="Mã QR"
                >
                  <QrCode class="w-4 h-4" />
                </button>
              </div>
            </div>

            {#if showQrCode}
              <div class="flex flex-col items-center justify-center p-4 bg-white rounded-lg mt-2 transition-all border border-stone-200" transition:slide>
                <img src={qrCodeUrl} alt="Mã QR Giới thiệu" class="w-36 h-36" />
                <p class="text-[9px] text-stone-500 mt-2 font-medium tracking-wider">Quét mã để mua hàng qua mã CTV của bạn</p>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- Financial Metrics Grid -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        
        <!-- Current Balance -->
        <div class="bg-white rounded-xl p-5 border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] hover:shadow-lg transition-all space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-[10px] tracking-[0.5px] font-bold text-stone-400">Số dư khả dụng</span>
            <div class="w-8 h-8 rounded-lg bg-luxury-copper/10 flex items-center justify-center text-luxury-copper">
              <Coins class="w-4 h-4" />
            </div>
          </div>
          <div>
            <p class="text-xl font-bold text-stone-800 font-mono tracking-tight">{formatVnd(profile.balance || 0)}</p>
            <p class="text-[9px] text-stone-400 mt-1">Rút tối thiểu 200k • Phê duyệt nhanh</p>
          </div>
          <button 
            onclick={() => showWithdrawModal = true}
            class="w-full py-2.5 rounded-lg bg-stone-900 hover:bg-luxury-copper hover:text-stone-950 text-white font-bold text-[10px] tracking-[1px] transition-all"
          >
            Yêu cầu rút tiền
          </button>
        </div>

        <!-- Total Revenue -->
        <div class="bg-white rounded-xl p-5 border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-[10px] tracking-[0.5px] font-bold text-stone-400">Tổng doanh số</span>
            <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-500">
              <TrendingUp class="w-4 h-4" />
            </div>
          </div>
          <div>
            <p class="text-xl font-bold text-stone-800 font-mono tracking-tight">{formatVnd(profile.total_revenue || 0)}</p>
            <p class="text-[9px] text-stone-400 mt-1">Tổng giá trị đơn hàng thành công</p>
          </div>
          <div class="text-[9px] font-medium text-stone-500 bg-stone-50 py-2.5 px-3 rounded-lg text-center tracking-wider border border-stone-100">
            Chiết khấu: {((profile.tier?.commission_rate ?? profile.commission_rate ?? 0.05) * 100).toFixed(1)}%
          </div>
        </div>

        <!-- Total Commission -->
        <div class="bg-white rounded-xl p-5 border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-[10px] tracking-[0.5px] font-bold text-stone-400">Tổng hoa hồng tích lũy</span>
            <div class="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-500">
              <Award class="w-4 h-4" />
            </div>
          </div>
          <div>
            <p class="text-xl font-bold text-stone-800 font-mono tracking-tight">{formatVnd(profile.total_commission || 0)}</p>
            <p class="text-[9px] text-stone-400 mt-1">Tổng hoa hồng thực nhận + khả dụng</p>
          </div>
          <div class="text-[9px] font-medium text-stone-500 bg-stone-50 py-2.5 px-3 rounded-lg text-center tracking-wider border border-stone-100">
            Đã thanh toán: {formatVnd(profile.paid_commission || 0)}
          </div>
        </div>

        <!-- Total Referral Orders -->
        <div class="bg-white rounded-xl p-5 border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-[10px] tracking-[0.5px] font-bold text-stone-400">Đơn giới thiệu</span>
            <div class="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center text-purple-500">
              <ShoppingBag class="w-4 h-4" />
            </div>
          </div>
          <div>
            <p class="text-xl font-bold text-stone-800 font-mono tracking-tight">{profile.total_orders || 0} đơn</p>
            <p class="text-[9px] text-stone-400 mt-1">Số đơn hàng phát sinh từ link của bạn</p>
          </div>
          <!-- Bank & Deactivate Buttons Row (Compact Icon-Only Layout) -->
          <div class="flex items-center justify-center gap-2 pt-3 border-t border-stone-100 mt-2">
            <!-- Bank Update Button -->
            <button 
              onclick={() => showBankModal = true}
              class="flex-1 py-2.5 rounded-xl border border-stone-200 hover:border-stone-400 hover:bg-stone-50 text-stone-600 hover:text-stone-800 transition-all flex items-center justify-center group relative"
              title="Cập nhật tài khoản ngân hàng"
            >
              <Landmark class="w-4 h-4 transition-transform group-hover:scale-110" />
              <span class="absolute -top-8 bg-stone-900 text-white text-[9px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity font-bold whitespace-nowrap shadow-md">Liên kết ngân hàng</span>
            </button>

            <!-- Deactivate Button -->
            <button 
              onclick={() => showDeactivateConfirm = true}
              class="flex-1 py-2.5 rounded-xl border border-red-100 hover:border-red-300 hover:bg-red-50/50 text-red-400 hover:text-red-500 transition-all flex items-center justify-center group relative"
              title="Hủy đăng ký chương trình CTV"
            >
              <svg class="w-4 h-4 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span class="absolute -top-8 bg-red-950 text-white text-[9px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity font-bold whitespace-nowrap shadow-md">Hủy tham gia CTV</span>
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
          </div>

        </div>
      {:else if activeTab === 'history'}
        <!-- Lịch sử hoa hồng Tab -->
        <div class="bg-white rounded-xl border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.01)] overflow-hidden" in:fade>
          
          <div class="px-6 py-4 border-b border-stone-100 flex items-center justify-between">
            <h3 class="text-xs tracking-[0.5px] font-bold text-stone-800 flex items-center gap-1.5">
              <History class="w-4 h-4 text-luxury-copper" /> Biến động số dư hoa hồng
            </h3>
          </div>

          <div class="overflow-x-auto">
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
                    <tr class="hover:bg-stone-50/50 transition-colors">
                      <td class="py-4 px-6 font-mono font-medium text-stone-700">#{item.order_id.split('-')[0].toUpperCase()}</td>
                      <td class="py-4 px-6 text-right font-mono font-medium text-stone-800">{formatVnd(item.order_amount)}</td>
                      <td class="py-4 px-6 text-right font-mono text-stone-500">{(item.rate_applied || 0.15) * 100}%</td>
                      <td class="py-4 px-6 text-right font-mono font-bold text-luxury-copper">+{formatVnd(item.commission_amount)}</td>
                      <td class="py-4 px-6 relative group">
                        <span class="px-2.5 py-1 rounded-full text-[9px] font-bold tracking-wide transition-all
                          {item.status === 'CONFIRMED' ? 'bg-amber-50 border border-amber-200 text-amber-600' : ''}
                          {item.status === 'PAID' ? 'bg-emerald-50 border border-emerald-200 text-emerald-600' : ''}
                          {item.status === 'PENDING' ? 'bg-orange-50/70 border border-orange-200 text-orange-600' : ''}
                          {item.status === 'CANCELLED' ? 'bg-red-50 border border-red-200 text-red-500' : ''}
                        ">
                          {item.status === 'CONFIRMED' ? 'Khả dụng' : ''}
                          {item.status === 'PAID' ? 'Đã chi trả' : ''}
                          {item.status === 'PENDING' ? getPendingDaysLeft(item.created_at) : ''}
                          {item.status === 'CANCELLED' ? 'Đã hủy bỏ' : ''}
                        </span>
                        
                        {#if item.status === 'PENDING'}
                          <!-- Premium Tooltip for 7-day Return Policy Validation -->
                          <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-52 bg-stone-950 border border-stone-800 text-[10px] text-stone-300 rounded-lg p-2.5 shadow-xl z-10 leading-relaxed">
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

            <div class="overflow-x-auto">
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
  {/if}
</UserPageWrapper>

<!-- LINKED BANK DIALOG -->
{#if showBankModal}
  <div class="fixed inset-0 bg-stone-900/60 backdrop-blur-sm z-[99999] flex items-center justify-center p-4" transition:fade>
    <div class="bg-white rounded-2xl w-full max-w-md border border-stone-100 overflow-hidden shadow-2xl" transition:scale={{ start: 0.95, duration: 200 }}>
      
      <div class="px-6 py-5 bg-stone-900 text-white flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Landmark class="w-5 h-5 text-luxury-copper" />
          <h3 class="text-sm font-bold tracking-widest uppercase">CẬP NHẬT TÀI KHOẢN BANK</h3>
        </div>
        <button onclick={() => showBankModal = false} class="text-stone-400 hover:text-white transition-colors text-xs font-black">ĐÓNG</button>
      </div>

      <form onsubmit={handleUpdateBank} class="p-6 space-y-4">
        <p class="text-[11px] text-stone-500 leading-relaxed">
          * Thông tin tài khoản ngân hàng của bạn sẽ được mã hóa bảo mật chuẩn quân sự bằng thuật toán <strong>AES-GCM-256</strong> trước khi lưu vào Cơ sở dữ liệu.
        </p>

        <div class="space-y-1">
          <label for="bankName" class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Tên Ngân hàng</label>
          <input 
            id="bankName"
            type="text" 
            bind:value={bankName}
            placeholder="VD: Vietcombank, Techcombank, VPBank" 
            class="w-full bg-white text-stone-900 border border-stone-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-luxury-copper placeholder:text-stone-300"
            required
          />
        </div>

        <div class="space-y-1">
          <label for="bankAccountNo" class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Số tài khoản</label>
          <input 
            id="bankAccountNo"
            type="text" 
            bind:value={bankAccountNo}
            placeholder="Nhập số tài khoản ngân hàng" 
            class="w-full bg-white text-stone-900 border border-stone-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-luxury-copper font-mono placeholder:text-stone-300"
            required
          />
        </div>

        <div class="space-y-1">
          <label for="bankAccountName" class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Tên chủ tài khoản</label>
          <input 
            id="bankAccountName"
            type="text" 
            bind:value={bankAccountName}
            placeholder="VD: NGUYEN VAN A" 
            class="w-full bg-white text-stone-900 border border-stone-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-luxury-copper uppercase font-bold placeholder:text-stone-300"
            required
          />
        </div>

        <button 
          type="submit" 
          disabled={isUpdatingBank}
          class="w-full py-3 bg-luxury-copper hover:bg-amber-600 disabled:bg-stone-300 text-stone-950 font-black text-xs tracking-[3px] uppercase rounded-lg active:scale-[0.98] transition-all shadow-md mt-4"
        >
          {#if isUpdatingBank}
            ĐANG MÃ HÓA & LƯU...
          {:else}
            XÁC NHẬN LIÊN KẾT
          {/if}
        </button>
      </form>

    </div>
  </div>
{/if}

<!-- WITHDRAWAL REQUEST DIALOG -->
{#if showWithdrawModal}
  <div class="fixed inset-0 bg-stone-900/60 backdrop-blur-sm z-[99999] flex items-center justify-center p-4" transition:fade>
    <div class="bg-white rounded-2xl w-full max-w-md border border-stone-100 overflow-hidden shadow-2xl" transition:scale={{ start: 0.95, duration: 200 }}>
      
      <div class="px-6 py-5 bg-stone-900 text-white flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Coins class="w-5 h-5 text-luxury-copper" />
          <h3 class="text-sm font-bold tracking-widest uppercase">YÊU CẦU RÚT HOA HỒNG</h3>
        </div>
        <button onclick={() => showWithdrawModal = false} class="text-stone-400 hover:text-white transition-colors text-xs font-black">ĐÓNG</button>
      </div>

      <form onsubmit={handleWithdraw} class="p-6 space-y-4">
        
        <div class="bg-stone-50 p-4 rounded-xl space-y-2 border border-stone-100">
          <div class="flex justify-between text-xs text-stone-500">
            <span>Số dư khả dụng:</span>
            <span class="font-bold font-mono text-stone-850">{formatVnd(profile.balance || 0)}</span>
          </div>
          <div class="flex justify-between text-xs text-stone-500">
            <span>Ngân hàng nhận:</span>
            {#if profile?.bank_info?.bank}
              <span class="font-bold text-stone-850">{profile.bank_info.bank} - {profile.bank_info.account_no}</span>
            {:else}
              <span class="text-rose-500 font-bold">Chưa liên kết Bank!</span>
            {/if}
          </div>
        </div>

        <div class="space-y-1">
          <label for="withdrawAmount" class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Số tiền muốn rút (VNĐ)</label>
          <input 
            id="withdrawAmount"
            type="number" 
            bind:value={withdrawAmount}
            min="200000"
            max={profile.balance || 0}
            step="10000"
            class="w-full bg-white text-stone-900 border border-stone-200 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:border-luxury-copper font-mono font-bold placeholder:text-stone-300"
            required
          />
          <p class="text-[9px] text-stone-500 mt-1">Hạn mức tối thiểu 200.000đ • Chỉ nhập số nguyên chia hết cho 10.000đ.</p>
        </div>

        <button 
          type="submit" 
          disabled={isWithdrawing || (profile?.balance || 0) < 200000}
          class="w-full py-3 bg-stone-900 hover:bg-luxury-copper hover:text-stone-950 disabled:bg-stone-200 disabled:text-stone-400 text-white font-black text-xs tracking-[3px] uppercase rounded-lg active:scale-[0.98] transition-all shadow-md mt-4"
        >
          {#if isWithdrawing}
            ĐANG GỬI LỆNH RÚT...
          {:else}
            XÁC NHẬN RÚT TIỀN
          {/if}
        </button>
      </form>

    </div>
  </div>
{/if}

{#if profile?.is_registered && showDeactivateConfirm}
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4" in:fade>
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" onclick={() => showDeactivateConfirm = false} role="presentation"></div>
    <div class="relative w-full max-w-sm bg-stone-950 border border-red-500/30 rounded-2xl shadow-2xl p-6 z-10" in:scale={{ duration: 200, start: 0.95 }}>
      <div class="flex flex-col items-center text-center gap-4">
        <div class="w-14 h-14 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center">
          <svg class="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <div>
          <h3 class="text-sm font-black text-white tracking-widest uppercase">XÁC NHẬN RỜI CHƯƠNG TRÌNH</h3>
          <p class="text-xs text-stone-400 mt-2 leading-relaxed">
            Bạn sắp rời khỏi chương trình CTV. Mã <span class="text-luxury-copper font-bold">{profile?.ctv_code}</span> sẽ bị vô hiệu hóa ngay lập tức.
          </p>
          <p class="text-[10px] text-stone-500 mt-1">Lịch sử hoa hồng vẫn được lưu giữ đầy đủ.</p>
        </div>
        <div class="w-full flex flex-col gap-2 mt-2">
          <button
            onclick={handleDeactivate}
            disabled={isDeactivating}
            class="w-full py-3 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-black text-xs tracking-[2px] uppercase rounded-xl transition-all active:scale-[0.98]"
          >
            {isDeactivating ? 'ĐANG XỬ LÝ...' : 'XÁC NHẬN RỜI CHƯƠNG TRÌNH'}
          </button>
          <button
            onclick={() => showDeactivateConfirm = false}
            class="w-full py-2.5 bg-transparent border border-stone-700 hover:border-stone-500 text-stone-400 hover:text-stone-200 font-bold text-xs tracking-widest uppercase rounded-xl transition-all"
          >
            QUAY LẠI
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Glass effect helper class */
  .bg-gradient-to-tr {
    background-size: 200% 200%;
    animation: gradientShift 10s ease infinite;
  }
  @keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
</style>
