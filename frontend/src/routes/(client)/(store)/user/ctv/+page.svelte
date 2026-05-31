<script lang="ts">
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import { apiClient, ApiError } from '$lib/utils/apiClient';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import UserPageWrapper from '$lib/components/storefront/user/UserPageWrapper.svelte';
  import Award from "@lucide/svelte/icons/award";
  import Lock from "@lucide/svelte/icons/lock";

  import { exportLedgerToExcel } from './utils/excelExport';
  import CtvDashboard from './components/CtvDashboard.svelte';
  import CtvModals from './components/CtvModals.svelte';

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
    pending_commission?: number;
    total_orders?: number;
    status?: 'ACTIVE' | 'PENDING' | 'SUSPENDED' | 'BANNED' | 'CANCELLED';
    tier?: {
      name: string;
      commission_rate_bps: number;
      commission_rate_pct: string;
      commission_rate: number;
      min_revenue_threshold: number;
    };
    tiers?: Array<{
      name: string;
      commission_rate_bps: number;
      commission_rate_pct: string;
      commission_rate: number;
      min_revenue_threshold: number;
      bonus_rate: number;
      bonus_rate_bps: number;
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
    rate_applied?: number;
    commission_amount: number;
    status: 'PENDING' | 'CONFIRMED' | 'PAID' | 'CANCELLED' | 'VOIDED';
    created_at: string;
    admin_note?: string;
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
  let regEmail = $state('');
  let regReferredBy = $state('');
  let regError = $state('');
  let acceptedTerms = $state(false);

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
      const raw = await apiClient.get<any>('/client/ctv/profile');
      const stats = raw.stats || {};
      const tier = raw.tier || {};
      profile = {
        is_registered: raw.is_registered ?? !!raw.ctv_code,
        ctv_code: raw.ctv_code,
        encrypted_code: raw.encrypted_code,
        status: raw.status,
        bank_info: raw.bank_info,
        tier: {
          name: tier.name || 'Đồng',
          commission_rate_bps: tier.commission_rate_bps || 1500,
          commission_rate_pct: tier.commission_rate_pct || '15.0%',
          commission_rate: (tier.commission_rate_bps || 1500) / 10000,
          min_revenue_threshold: tier.min_revenue_threshold || 0,
        },
        tier_name: tier.name || 'Đồng',
        commission_rate: (tier.commission_rate_bps || 1500) / 10000,
        total_revenue: stats.total_revenue || 0,
        total_commission: stats.total_commission || 0,
        paid_commission: stats.paid_commission || 0,
        pending_commission: stats.pending_commission || 0,
        balance: stats.available_to_withdraw || 0,
        total_orders: stats.total_orders || 0,
        tiers: (raw.tiers || []).map((t: any) => ({
          name: t.name,
          commission_rate_bps: t.commission_rate_bps,
          commission_rate_pct: t.commission_rate_pct,
          commission_rate: (t.commission_rate_bps || 0) / 10000,
          min_revenue_threshold: t.min_revenue_threshold || 0,
          bonus_rate: (t.bonus_rate_bps || 0) / 10000,
          bonus_rate_bps: t.bonus_rate_bps || 0,
        })),
      };
      if (profile && profile.bank_info) {
        bankName = profile.bank_info.bank || '';
        bankAccountNo = profile.bank_info.account_no || '';
        bankAccountName = profile.bank_info.account_name || '';
      }
      
      // 2. Fetch commission history if registered
      if (profile?.is_registered) {
        const commData = await apiClient.get<{ items: any[] }>('/client/ctv/commissions?page=1&page_size=30');
        commissions = (commData.items || []).map((item: any) => ({
          ...item,
          rate_applied: (item.rate_applied_bps || 500) / 10000,
        }));
      }
    } catch (e: any) {
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
    if (!acceptedTerms) {
      regError = 'Vui lòng đọc và chấp nhận Điều khoản & Chính sách CTV trước khi đăng ký.';
      return;
    }
    if (!regEmail || !regEmail.trim()) {
      regError = 'Vui lòng nhập Email để nhận thông báo hoa hồng.';
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(regEmail.trim())) {
      regError = 'Địa chỉ email không hợp lệ. Vui lòng nhập đúng định dạng (VD: email@example.com).';
      return;
    }
    isRegistering = true;
    
    try {
      const res = await apiClient.post<any>('/client/ctv/register', {
        ctv_code: regCode.trim().toUpperCase(),
        email: regEmail.trim(),
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

  function handleExportExcel() {
    if (!commissions || commissions.length === 0) return;
    const itemsToExport = commissions.map(item => ({
      ...item,
      ctv_code: profile?.ctv_code || ''
    }));
    exportLedgerToExcel(itemsToExport, `DoiSoat_CTV_${profile?.ctv_code || 'User'}`, profile?.ctv_code || '');
    ui.showToast('Đã xuất file đối soát hoa hồng thành công!', 'success');
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

  // Handle CTV Deactivation
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

  function parseBreakdown(note: string | undefined) {
    if (!note) return null;
    try {
      return JSON.parse(note);
    } catch (e) {
      return null;
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
    <div class="max-w-xl mx-auto py-6 animate-fade-in" in:fade>
      <div class="bg-gradient-to-br from-sky-100/60 via-sky-50/40 to-white/70 text-sky-950 rounded-2xl p-8 shadow-xl border border-white/60 relative overflow-hidden backdrop-blur-xl">
        <!-- Decoration background -->
        <div class="absolute -right-16 -top-16 w-48 h-48 bg-sky-300/20 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -left-16 -bottom-16 w-48 h-48 bg-luxury-copper/5 rounded-full blur-3xl pointer-events-none"></div>

        <div class="relative z-10 space-y-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-luxury-copper/10 rounded-xl flex items-center justify-center border border-luxury-copper/20">
              <Award class="w-5 h-5 text-luxury-copper" />
            </div>
            <div>
              <span class="text-[10px] tracking-[2px] text-[#8C6239] font-bold">Chương trình Đại lý số</span>
              <h2 class="text-xl font-serif italic tracking-wide text-sky-900 font-light animate-pulse">Trở thành đối tác osmo</h2>
            </div>
          </div>

          <p class="text-xs text-sky-900/80 leading-relaxed font-normal">
            Tham gia mạng lưới đại lý số & CTV thông minh của osmo. Nhận ngay chiết khấu hoa hồng hấp dẫn theo cấp bậc trên mỗi đơn hàng được giới thiệu thành công. Không cần ôm hàng, không cần vận chuyển.
          </p>

          <form onsubmit={handleRegister} class="space-y-4 pt-4 border-t border-sky-100/80">
            {#if regError}
              <div class="p-3 bg-red-50 border border-red-200 text-red-600 text-xs rounded-lg animate-pulse">
                {regError}
              </div>
            {/if}

            <div class="space-y-2">
              <label for="regCode" class="block text-xs font-bold text-sky-900/70">Mã giới thiệu mong muốn</label>
              <input 
                id="regCode"
                type="text" 
                bind:value={regCode}
                placeholder="VD: MINHMINH99, LOUISTHANH" 
                class="w-full bg-white/75 border border-white/80 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-luxury-copper text-stone-900 uppercase font-bold tracking-wider placeholder:text-stone-400 transition-colors shadow-sm focus:bg-white"
                required
                minlength="4"
                maxlength="20"
              />
              <p class="text-[9px] text-sky-900/50 tracking-wider">Viết liền không dấu, từ 4-20 ký tự (Chỉ gồm chữ và số).</p>
            </div>

            <div class="space-y-2">
              <label for="regEmail" class="block text-xs font-bold text-sky-900/70">Email nhận thông báo <span class="text-red-500 font-bold">(Bắt buộc)</span></label>
              <input 
                id="regEmail"
                type="email" 
                bind:value={regEmail}
                placeholder="email@example.com"
                autocomplete="email"
                class="w-full bg-white/75 border border-white/80 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-luxury-copper text-stone-900 placeholder:text-stone-400 transition-colors shadow-sm focus:bg-white"
                required
              />
              <p class="text-[9px] text-sky-900/50 tracking-wider">Nhận thông báo hoa hồng và cập nhật chương trình qua email.</p>
            </div>

            <div class="space-y-2">
              <label for="regReferredBy" class="block text-xs font-bold text-sky-900/70">Mã giới thiệu người bảo trợ (Nếu có)</label>
              <input 
                id="regReferredBy"
                type="text" 
                bind:value={regReferredBy}
                placeholder="Nhập mã của người giới thiệu bạn" 
                class="w-full bg-white/75 border border-white/80 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-luxury-copper text-stone-900 uppercase tracking-wider placeholder:text-stone-400 transition-colors shadow-sm focus:bg-white"
                maxlength="20"
              />
            </div>

            <!-- Terms & Conditions Checkbox -->
            <label class="flex items-start gap-3 cursor-pointer group pt-1">
              <input
                type="checkbox"
                bind:checked={acceptedTerms}
                class="mt-0.5 w-4 h-4 rounded accent-luxury-copper shrink-0 cursor-pointer"
              />
              <span class="text-[11px] text-sky-900/70 leading-relaxed font-medium group-hover:text-sky-900 transition-colors">
                Tôi đã đọc và đồng ý với
                <a
                  href="/quy-dinh-chinh-sach-doi-tac-affiliate-cong-tac-vien-ban-hang-tren-website-osmovn.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-[#8C6239] hover:text-amber-600 underline underline-offset-2 font-semibold transition-colors"
                  onclick={(e) => e.stopPropagation()}
                >Điều khoản & Chính sách Đối tác CTV/Affiliate của osmo.vn</a>
              </span>
            </label>

            <button 
              type="submit" 
              disabled={isRegistering || !acceptedTerms}
              class="w-full py-3.5 rounded-xl bg-[#8C6239] hover:bg-[#704d2b] disabled:bg-stone-200 disabled:text-stone-400 disabled:opacity-80 disabled:cursor-not-allowed text-white font-bold text-sm tracking-wide active:scale-[0.98] transition-all shadow-lg shadow-luxury-copper/15 mt-2"
            >
              {#if isRegistering}
                Đang kích hoạt...
              {:else}
                Đăng ký ngay
              {/if}
            </button>
          </form>
        </div>
      </div>
    </div>
  {:else}
    <!-- ACTIVE CTV DASHBOARD -->
    <CtvDashboard
      {profile}
      {commissions}
      {globalStats}
      bind:activeTab
      {referralLink}
      {qrCodeUrl}
      bind:showQrCode
      bind:showFullPolicy
      bind:showBankModal
      bind:showWithdrawModal
      bind:showDeactivateConfirm
      {copyToClipboard}
      {formatVnd}
      {handleExportExcel}
      {getPendingDaysLeft}
      {parseBreakdown}
    />
  {/if}
</UserPageWrapper>

<!-- DIALOGS & MODALS -->
<CtvModals
  bind:showBankModal
  bind:showWithdrawModal
  bind:showDeactivateConfirm
  bind:bankName
  bind:bankAccountNo
  bind:bankAccountName
  bind:withdrawAmount
  {profile}
  {isUpdatingBank}
  {isWithdrawing}
  {isDeactivating}
  {handleUpdateBank}
  {handleWithdraw}
  {handleDeactivate}
  {formatVnd}
/>

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
