<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { apiClient, ApiError } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import XohiLogo from '$lib/components/admin/XohiLogo.svelte';
  import { 
    Users, 
    Award, 
    DollarSign, 
    Settings, 
    Check, 
    X, 
    Search, 
    Plus, 
    Edit, 
    CheckCircle2, 
    AlertTriangle,
    Coins,
    UserCheck,
    Lock
  } from '@lucide/svelte';

  const ui = getClientUi();

  // State Management
  let activeTab = $state<'withdrawals' | 'members' | 'tiers'>('withdrawals');
  let isLoading = $state(true);

  // Tiers State
  let tiers = $state<any[]>([]);
  let showTierModal = $state(false);
  let editingTier = $state<any>(null);
  let tierForm = $state({
    name: '',
    min_revenue_threshold: 0,
    commission_rate: 0.15,
    bonus_rate: 0.0,
    max_withdrawal_per_month: 50000000.0,
    is_default: false
  });

  // Members State
  let members = $state<any[]>([]);
  let totalMembers = $state(0);
  let membersPage = $state(1);
  let membersSearch = $state('');
  let membersStatus = $state('');
  let showTierAssignModal = $state(false);
  let showStatusModal = $state(false);
  let selectedMember = $state<any>(null);
  let selectedTierId = $state('');
  let newStatus = $state('');
  let adminNote = $state('');

  // Withdrawals State
  let withdrawals = $state<any[]>([]);
  let totalWithdrawals = $state(0);
  let withdrawalsPage = $state(1);
  let showPayoutModal = $state(false);
  let selectedWithdrawal = $state<any>(null);
  let payoutAmount = $state(0);
  let payoutNote = $state('');
  let isProcessingPayout = $state(false);

  // Lifecycle
  onMount(async () => {
    await loadInitialData();
  });

  async function loadInitialData() {
    isLoading = true;
    try {
      await Promise.all([
        loadTiers(),
        loadWithdrawals(),
        loadMembers()
      ]);
    } catch (e: any) {
      ui.showToast(e.message || 'Lỗi tải dữ liệu hệ thống', 'error');
    } finally {
      isLoading = false;
    }
  }

  // Tiers Functions
  async function loadTiers() {
    try {
      const res = await apiClient.get<any[]>('/admin/ctv/tiers');
      tiers = res || [];
    } catch (e: any) {
      console.error(e);
    }
  }

  function openCreateTier() {
    editingTier = null;
    tierForm = {
      name: '',
      min_revenue_threshold: 0,
      commission_rate: 0.15,
      bonus_rate: 0.0,
      max_withdrawal_per_month: 50000000.0,
      is_default: false
    };
    showTierModal = true;
  }

  function openEditTier(tier: any) {
    editingTier = tier;
    tierForm = {
      name: tier.name,
      min_revenue_threshold: tier.min_revenue_threshold,
      commission_rate: tier.commission_rate,
      bonus_rate: tier.bonus_rate,
      max_withdrawal_per_month: tier.max_withdrawal_per_month,
      is_default: tier.is_default
    };
    showTierModal = true;
  }

  async function handleSaveTier(e: Event) {
    e.preventDefault();
    try {
      if (editingTier) {
        await apiClient.patch(`/admin/ctv/tiers/${editingTier.id}`, tierForm);
        ui.showToast('Cập nhật cấp bậc thành công!', 'success');
      } else {
        await apiClient.post('/admin/ctv/tiers', tierForm);
        ui.showToast('Tạo cấp bậc mới thành công!', 'success');
      }
      showTierModal = false;
      await loadTiers();
    } catch (e: any) {
      ui.showToast(e.message || 'Lưu thất bại', 'error');
    }
  }

  // Members Functions
  async function loadMembers() {
    try {
      const query = `page=${membersPage}&page_size=20&search=${encodeURIComponent(membersSearch)}&status=${membersStatus}`;
      const res = await apiClient.get<any>(`/admin/ctv/members?${query}`);
      members = res.items || [];
      totalMembers = res.total || 0;
    } catch (e: any) {
      console.error(e);
    }
  }

  function openTierAssign(member: any) {
    selectedMember = member;
    selectedTierId = '';
    showTierAssignModal = true;
  }

  async function handleAssignTier() {
    if (!selectedTierId) return;
    try {
      await apiClient.patch(`/admin/ctv/members/${selectedMember.id}/tier`, {
        tier_id: selectedTierId
      });
      ui.showToast(`Đã đổi cấp bậc của ${selectedMember.ctv_code} thành công!`, 'success');
      showTierAssignModal = false;
      await loadMembers();
    } catch (e: any) {
      ui.showToast(e.message || 'Lỗi phân cấp', 'error');
    }
  }

  function openStatusModal(member: any) {
    selectedMember = member;
    newStatus = member.status;
    adminNote = '';
    showStatusModal = true;
  }

  async function handleUpdateStatus() {
    try {
      await apiClient.patch(`/admin/ctv/members/${selectedMember.id}/status`, {
        status: newStatus,
        note: adminNote.trim() || undefined
      });
      ui.showToast(`Cập nhật trạng thái CTV ${selectedMember.ctv_code} thành công!`, 'success');
      showStatusModal = false;
      await loadMembers();
    } catch (e: any) {
      ui.showToast(e.message || 'Lỗi cập nhật trạng thái', 'error');
    }
  }

  // Withdrawals Functions
  async function loadWithdrawals() {
    try {
      const res = await apiClient.get<any>(`/admin/ctv/withdrawals?page=${withdrawalsPage}&page_size=20`);
      withdrawals = res.items || [];
      totalWithdrawals = res.total || 0;
    } catch (e: any) {
      console.error(e);
    }
  }

  function openPayoutModal(withdrawal: any) {
    selectedWithdrawal = withdrawal;
    payoutAmount = withdrawal.amount_requested;
    payoutNote = '';
    showPayoutModal = true;
  }

  async function handleApprovePayout() {
    isProcessingPayout = true;
    try {
      await apiClient.post('/admin/ctv/withdrawals/payout', {
        withdrawal_id: selectedWithdrawal.id,
        amount_approved: payoutAmount,
        note: payoutNote.trim() || undefined
      });
      ui.showToast('Phê duyệt và giải ngân hoa hồng thành công!', 'success');
      showPayoutModal = false;
      await Promise.all([
        loadWithdrawals(),
        loadMembers()
      ]);
    } catch (e: any) {
      ui.showToast(e.message || 'Lỗi xử lý thanh toán', 'error');
    } finally {
      isProcessingPayout = false;
    }
  }

  // Format currency
  function formatVnd(val: number): string {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  }
</script>

<div class="min-h-screen bg-[#010101] text-white p-8 relative overflow-hidden font-sans">
  
  <!-- Subtle Neural Background -->
  <div class="absolute inset-0 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-stone-900/40 via-black to-black -z-10"></div>

  <!-- Header -->
  <header class="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/5 pb-8">
    <div>
      <div class="flex items-center gap-3">
        <div class="p-2.5 rounded-xl bg-luxury-copper/10 border border-luxury-copper/20 text-luxury-copper">
          <Coins class="w-6 h-6 animate-pulse" />
        </div>
        <h1 class="text-3xl font-extrabold tracking-tighter bg-gradient-to-r from-white via-stone-200 to-stone-500 bg-clip-text text-transparent uppercase">
          CTV AFFILIATE HUBS
        </h1>
      </div>
      <p class="text-xs text-stone-500 mt-2.5 tracking-wider uppercase font-mono">Hệ thống điều phối đại lý số & hoa hồng 3 lớp quân sự</p>
    </div>
    
    <!-- Tab Selectors -->
    <div class="flex items-center bg-stone-950/80 border border-stone-800/60 p-1.5 rounded-xl">
      <button 
        onclick={() => activeTab = 'withdrawals'}
        class="px-4 py-2 text-xs tracking-widest uppercase font-black rounded-lg transition-all flex items-center gap-2 {activeTab === 'withdrawals' ? 'bg-luxury-copper text-stone-950 shadow-lg' : 'text-stone-400 hover:text-white'}"
      >
        <DollarSign class="w-3.5 h-3.5" /> RÚT TIỀN ({totalWithdrawals})
      </button>
      <button 
        onclick={() => activeTab = 'members'}
        class="px-4 py-2 text-xs tracking-widest uppercase font-black rounded-lg transition-all flex items-center gap-2 {activeTab === 'members' ? 'bg-luxury-copper text-stone-950 shadow-lg' : 'text-stone-400 hover:text-white'}"
      >
        <Users class="w-3.5 h-3.5" /> ĐẠI LÝ ({totalMembers})
      </button>
      <button 
        onclick={() => activeTab = 'tiers'}
        class="px-4 py-2 text-xs tracking-widest uppercase font-black rounded-lg transition-all flex items-center gap-2 {activeTab === 'tiers' ? 'bg-luxury-copper text-stone-950 shadow-lg' : 'text-stone-400 hover:text-white'}"
      >
        <Award class="w-3.5 h-3.5" /> HẠNG MỨC ({tiers.length})
      </button>
    </div>
  </header>

  {#if isLoading}
    <div class="flex flex-col items-center justify-center py-32 gap-4">
      <XohiLogo variant="simple" size={80} />
      <p class="text-xs text-stone-500 animate-pulse font-mono uppercase tracking-[3px]">Đang giải mã dữ liệu...</p>
    </div>
  {:else}

    <!-- ── TAB 1: WITHDRAWALS ────────────────────────────────────────────────── -->
    {#if activeTab === 'withdrawals'}
      <div class="space-y-6" in:fade>
        <div class="bg-stone-950/80 border border-stone-800/40 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md">
          <div class="px-6 py-5 border-b border-stone-800/40 flex items-center justify-between">
            <h3 class="text-xs tracking-[2px] font-black text-stone-300 uppercase">YÊU CẦU THANH TOÁN HOA HỒNG</h3>
            <span class="text-[10px] bg-stone-900 border border-stone-800 px-3 py-1 rounded-full font-mono text-stone-400">Total requests: {totalWithdrawals}</span>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-stone-900/40 border-b border-stone-800/60 text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">
                  <th class="py-4 px-6">Mã CTV</th>
                  <th class="py-4 px-6">Tài khoản nhận</th>
                  <th class="py-4 px-6 text-right">Số tiền yêu cầu</th>
                  <th class="py-4 px-6 text-center">Trạng thái</th>
                  <th class="py-4 px-6">Ngày gửi</th>
                  <th class="py-4 px-6 text-center">Hành động</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-stone-900/60 text-xs font-mono">
                {#if withdrawals.length === 0}
                  <tr>
                    <td colspan="6" class="py-16 text-center text-stone-500 font-light italic uppercase tracking-wider text-[10px]">
                      Không tìm thấy yêu cầu rút tiền nào đang chờ duyệt
                    </td>
                  </tr>
                {:else}
                  {#each withdrawals as item}
                    <tr class="hover:bg-white/[0.01] transition-colors">
                      <td class="py-4 px-6 font-bold text-white tracking-wider">{item.ctv_code}</td>
                      <td class="py-4 px-6 font-sans text-stone-300">
                        {#if item.bank_info}
                          <div class="font-black text-xs text-white">{item.bank_info.account_name}</div>
                          <div class="text-[10px] text-stone-500 mt-0.5">{item.bank_info.bank} • {item.bank_info.account_no}</div>
                        {:else}
                          <span class="text-red-400 italic">Chưa liên kết</span>
                        {/if}
                      </td>
                      <td class="py-4 px-6 text-right font-black text-luxury-copper text-sm">{formatVnd(item.amount_requested)}</td>
                      <td class="py-4 px-6 text-center">
                        <span class="px-2 py-0.5 rounded-full text-[9px] font-bold tracking-wide uppercase 
                          {item.status === 'PENDING' ? 'bg-orange-500/10 border border-orange-500/20 text-orange-400' : ''}
                          {item.status === 'PAID' || item.status === 'APPROVED' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' : ''}
                          {item.status === 'REJECTED' ? 'bg-red-500/10 border border-red-500/20 text-red-400' : ''}
                        ">
                          {item.status === 'PENDING' ? 'Chờ duyệt' : ''}
                          {item.status === 'PAID' || item.status === 'APPROVED' ? 'Đã chi' : ''}
                          {item.status === 'REJECTED' ? 'Từ chối' : ''}
                        </span>
                      </td>
                      <td class="py-4 px-6 text-stone-500">{new Date(item.requested_at).toLocaleDateString('vi-VN')}</td>
                      <td class="py-4 px-6 text-center">
                        {#if item.status === 'PENDING'}
                          <button
                            onclick={() => openPayoutModal(item)}
                            class="px-3.5 py-1.5 bg-luxury-copper hover:bg-amber-600 active:scale-95 text-stone-950 font-black rounded-lg transition-all tracking-wider text-[9px] uppercase shadow-lg shadow-luxury-copper/5"
                          >
                            GIẢI NGÂN
                          </button>
                        {:else}
                          <span class="text-[10px] text-stone-600 font-sans italic">Hoàn tất</span>
                        {/if}
                      </td>
                    </tr>
                  {/each}
                {/if}
              </tbody>
            </table>
          </div>
        </div>
      </div>

    <!-- ── TAB 2: MEMBERS ───────────────────────────────────────────────────── -->
    {:else if activeTab === 'members'}
      <div class="space-y-6" in:fade>
        
        <!-- Filters Bar -->
        <div class="flex flex-col md:flex-row gap-4 bg-stone-950/80 border border-stone-800/40 p-4 rounded-xl backdrop-blur-md">
          <div class="flex-1 relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-500" />
            <input 
              type="text" 
              placeholder="Tìm kiếm theo mã CTV..." 
              bind:value={membersSearch}
              oninput={loadMembers}
              class="w-full bg-stone-900/60 border border-stone-800 rounded-lg pl-10 pr-4 py-2 text-xs focus:outline-none focus:border-luxury-copper text-white placeholder:text-stone-500 transition-colors uppercase font-bold"
            />
          </div>
          <div class="flex gap-4">
            <select
              bind:value={membersStatus}
              onchange={loadMembers}
              class="bg-stone-900/60 border border-stone-800 rounded-lg px-4 py-2 text-xs focus:outline-none focus:border-luxury-copper text-stone-300"
            >
              <option value="">Tất cả trạng thái</option>
              <option value="ACTIVE">Hoạt động</option>
              <option value="SUSPENDED">Tạm đình chỉ</option>
              <option value="BANNED">Đã cấm</option>
            </select>
          </div>
        </div>

        <!-- Members Table -->
        <div class="bg-stone-950/80 border border-stone-800/40 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md">
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-stone-900/40 border-b border-stone-800/60 text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">
                  <th class="py-4 px-6">Mã CTV</th>
                  <th class="py-4 px-6 text-center">Cấp bậc</th>
                  <th class="py-4 px-6 text-right">Chiết khấu</th>
                  <th class="py-4 px-6 text-right">Tổng Doanh số</th>
                  <th class="py-4 px-6 text-right">Hoa hồng tích lũy</th>
                  <th class="py-4 px-6 text-right">Đã chi trả</th>
                  <th class="py-4 px-6 text-center">Trạng thái</th>
                  <th class="py-4 px-6 text-center">Điều phối</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-stone-900/60 text-xs font-mono">
                {#if members.length === 0}
                  <tr>
                    <td colspan="8" class="py-16 text-center text-stone-500 font-light italic uppercase tracking-wider text-[10px]">
                      Không tìm thấy đại lý cộng tác viên nào
                    </td>
                  </tr>
                {:else}
                  {#each members as item}
                    <tr class="hover:bg-white/[0.01] transition-colors">
                      <td class="py-4 px-6 font-bold text-white tracking-wider">{item.ctv_code}</td>
                      <td class="py-4 px-6 text-center font-sans">
                        <span class="px-2 py-0.5 rounded border border-luxury-copper/20 text-luxury-copper text-[10px] font-bold">
                          {item.tier_name}
                        </span>
                      </td>
                      <td class="py-4 px-6 text-right text-stone-300 font-bold">{item.commission_rate_pct}</td>
                      <td class="py-4 px-6 text-right text-stone-400">{formatVnd(item.total_revenue)}</td>
                      <td class="py-4 px-6 text-right text-white font-bold">
                        <div>{formatVnd(item.total_commission)}</div>
                        <div class="text-[9px] text-stone-500 font-normal mt-0.5">Treo: {formatVnd(item.pending_commission || 0)}</div>
                      </td>
                      <td class="py-4 px-6 text-right text-emerald-400">
                        <div>{formatVnd(item.paid_commission)}</div>
                        <div class="text-[9px] text-stone-500 font-normal mt-0.5">Khả dụng: {formatVnd(item.available_commission || 0)}</div>
                      </td>
                      <td class="py-4 px-6 text-center">
                        <span class="px-2 py-0.5 rounded-full text-[9px] font-bold tracking-wide uppercase 
                          {item.status === 'ACTIVE' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' : ''}
                          {item.status === 'SUSPENDED' ? 'bg-orange-500/10 border border-orange-500/20 text-orange-400' : ''}
                          {item.status === 'BANNED' ? 'bg-red-500/10 border border-red-500/20 text-red-400' : ''}
                        ">
                          {item.status === 'ACTIVE' ? 'Hoạt động' : ''}
                          {item.status === 'SUSPENDED' ? 'Tạm đình chỉ' : ''}
                          {item.status === 'BANNED' ? 'Bị cấm' : ''}
                        </span>
                      </td>
                      <td class="py-4 px-6 text-center font-sans">
                        <div class="flex justify-center gap-1.5">
                          <button
                            onclick={() => openTierAssign(item)}
                            class="px-2 py-1 bg-stone-900 border border-stone-800 hover:border-luxury-copper hover:text-luxury-copper rounded text-[9px] font-bold tracking-widest uppercase transition-colors"
                          >
                            HẠNG
                          </button>
                          <button
                            onclick={() => openStatusModal(item)}
                            class="px-2 py-1 bg-stone-900 border border-stone-800 hover:border-red-500 hover:text-red-400 rounded text-[9px] font-bold tracking-widest uppercase transition-colors"
                          >
                            KHÓA
                          </button>
                        </div>
                      </td>
                    </tr>
                  {/each}
                {/if}
              </tbody>
            </table>
          </div>
        </div>
      </div>

    <!-- ── TAB 3: TIERS ─────────────────────────────────────────────────────── -->
    {:else if activeTab === 'tiers'}
      <div class="space-y-6" in:fade>
        
        <!-- Action bar -->
        <div class="flex justify-end">
          <button 
            onclick={openCreateTier}
            class="px-4 py-2 bg-luxury-copper hover:bg-amber-600 active:scale-95 text-stone-950 font-black rounded-lg transition-all text-xs tracking-widest uppercase shadow-lg shadow-luxury-copper/10 flex items-center gap-1.5"
          >
            <Plus class="w-4 h-4" /> Tạo hạng mới
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {#each tiers as tier}
            <div class="bg-stone-950/80 border border-stone-800/40 hover:border-luxury-copper/30 transition-all rounded-2xl p-6 shadow-xl backdrop-blur-md relative group flex flex-col justify-between min-h-[220px]">
              
              {#if tier.is_default}
                <span class="absolute top-4 right-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[8px] font-mono tracking-widest uppercase px-2 py-0.5 rounded-full font-black">
                  Mặc định
                </span>
              {/if}

              <div>
                <h4 class="text-base font-extrabold text-white tracking-wider flex items-center gap-2">
                  <Award class="w-5 h-5 text-luxury-copper" /> {tier.name}
                </h4>
                <p class="text-xs text-stone-500 mt-2 font-mono uppercase tracking-wider">Tỷ lệ hoa hồng:</p>
                <p class="text-3xl font-black text-luxury-copper tracking-tight mt-1">{(tier.commission_rate * 100).toFixed(1)}%</p>
              </div>

              <div class="mt-4 pt-4 border-t border-stone-900 space-y-2 text-[10px] font-mono text-stone-400">
                <div class="flex justify-between">
                  <span>Ngưỡng doanh số:</span>
                  <span class="font-bold text-white">{formatVnd(tier.min_revenue_threshold)}</span>
                </div>
                <div class="flex justify-between">
                  <span>Rút tối đa/tháng:</span>
                  <span class="font-bold text-stone-300">{formatVnd(tier.max_withdrawal_per_month)}</span>
                </div>
                <div class="flex justify-between">
                  <span>Bonus thêm:</span>
                  <span class="font-bold text-emerald-400">{(tier.bonus_rate * 100).toFixed(1)}%</span>
                </div>
              </div>

              <div class="mt-4 flex gap-2">
                <button
                  onclick={() => openEditTier(tier)}
                  class="w-full py-2 bg-stone-900 border border-stone-800 hover:border-stone-700 hover:text-white rounded-lg text-[9px] font-bold tracking-widest uppercase transition-all flex items-center justify-center gap-1"
                >
                  <Edit class="w-3 h-3" /> Chỉnh sửa
                </button>
              </div>

            </div>
          {/each}
        </div>
      </div>
    {/if}

  {/if}

  <!-- ── MODAL: SAVE TIER ──────────────────────────────────────────────────── -->
  {#if showTierModal}
    <div class="fixed inset-0 bg-stone-950/70 backdrop-blur-sm z-[99999] flex items-center justify-center p-4" transition:fade>
      <div class="bg-stone-900 border border-stone-850 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl" transition:scale={{ start: 0.95, duration: 200 }}>
        <div class="px-6 py-5 bg-stone-950 border-b border-stone-850 text-white flex items-center justify-between">
          <h3 class="text-xs tracking-[2px] font-bold uppercase">{editingTier ? 'Cập nhật cấp bậc' : 'Tạo cấp bậc mới'}</h3>
          <button onclick={() => showTierModal = false} class="text-stone-400 hover:text-white transition-colors text-xs font-black">ĐÓNG</button>
        </div>
        <form onsubmit={handleSaveTier} class="p-6 space-y-4 text-xs">
          <div class="space-y-1">
            <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Tên Cấp bậc</label>
            <input 
              type="text" 
              bind:value={tierForm.name}
              placeholder="VD: Bạc, Vàng, VIP" 
              class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-luxury-copper"
              required
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Tỷ lệ hoa hồng (0.0 - 1.0)</label>
              <input 
                type="number" 
                step="0.01"
                min="0"
                max="1"
                bind:value={tierForm.commission_rate}
                class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-luxury-copper font-mono"
                required
              />
            </div>
            <div class="space-y-1">
              <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Bonus thêm (0.0 - 1.0)</label>
              <input 
                type="number" 
                step="0.01"
                min="0"
                max="1"
                bind:value={tierForm.bonus_rate}
                class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-luxury-copper font-mono"
                required
              />
            </div>
          </div>
          <div class="space-y-1">
            <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Ngưỡng doanh số đạt tier (VNĐ)</label>
            <input 
              type="number" 
              bind:value={tierForm.min_revenue_threshold}
              class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-luxury-copper font-mono"
              required
            />
          </div>
          <div class="space-y-1">
            <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Hạn mức rút/tháng (VNĐ)</label>
            <input 
              type="number" 
              bind:value={tierForm.max_withdrawal_per_month}
              class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-luxury-copper font-mono"
              required
            />
          </div>
          <div class="flex items-center gap-2 pt-2">
            <input 
              id="is_default"
              type="checkbox" 
              bind:checked={tierForm.is_default}
              class="w-4 h-4 bg-stone-950 text-luxury-copper border-stone-800 rounded focus:ring-luxury-copper"
            />
            <label for="is_default" class="text-[10px] font-bold text-stone-300 uppercase tracking-wider">Cấp bậc mặc định khi CTV đăng ký</label>
          </div>
          <button 
            type="submit" 
            class="w-full py-3 bg-luxury-copper hover:bg-amber-600 text-stone-950 font-black text-xs tracking-[3px] uppercase rounded-lg transition-all shadow-md mt-6"
          >
            LƯU CẤP BẬC
          </button>
        </form>
      </div>
    </div>
  {/if}

  <!-- ── MODAL: ASSIGN TIER ────────────────────────────────────────────────── -->
  {#if showTierAssignModal}
    <div class="fixed inset-0 bg-stone-950/70 backdrop-blur-sm z-[99999] flex items-center justify-center p-4" transition:fade>
      <div class="bg-stone-900 border border-stone-850 rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl" transition:scale={{ start: 0.95, duration: 200 }}>
        <div class="px-6 py-5 bg-stone-950 border-b border-stone-850 text-white flex items-center justify-between">
          <h3 class="text-xs tracking-[2px] font-bold uppercase">Thay đổi cấp bậc</h3>
          <button onclick={() => showTierAssignModal = false} class="text-stone-400 hover:text-white transition-colors text-xs font-black">ĐÓNG</button>
        </div>
        <div class="p-6 space-y-4">
          <p class="text-xs text-stone-400">Điều chỉnh cấp bậc hoa hồng trực tiếp cho CTV <span class="font-bold text-luxury-copper">{selectedMember?.ctv_code}</span>:</p>
          <div class="space-y-1">
            <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Chọn Cấp bậc mới</label>
            <select
              bind:value={selectedTierId}
              class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2.5 text-xs focus:outline-none focus:border-luxury-copper"
            >
              <option value="">-- Chọn Cấp bậc --</option>
              {#each tiers as tier}
                <option value={tier.id}>{tier.name} ({(tier.commission_rate * 100).toFixed(0)}%)</option>
              {/each}
            </select>
          </div>
          <button 
            onclick={handleAssignTier}
            disabled={!selectedTierId}
            class="w-full py-3 bg-luxury-copper hover:bg-amber-600 disabled:bg-stone-800 disabled:text-stone-600 text-stone-950 font-black text-xs tracking-[3px] uppercase rounded-lg transition-all shadow-md mt-4"
          >
            ĐẶC CÁCH THĂNG HẠNG
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- ── MODAL: STATUS UPDATE ──────────────────────────────────────────────── -->
  {#if showStatusModal}
    <div class="fixed inset-0 bg-stone-950/70 backdrop-blur-sm z-[99999] flex items-center justify-center p-4" transition:fade>
      <div class="bg-stone-900 border border-stone-850 rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl" transition:scale={{ start: 0.95, duration: 200 }}>
        <div class="px-6 py-5 bg-stone-950 border-b border-stone-850 text-white flex items-center justify-between">
          <h3 class="text-xs tracking-[2px] font-bold uppercase">Trạng thái tài khoản</h3>
          <button onclick={() => showStatusModal = false} class="text-stone-400 hover:text-white transition-colors text-xs font-black">ĐÓNG</button>
        </div>
        <div class="p-6 space-y-4 text-xs">
          <p class="text-stone-400">Cập nhật trạng thái hoạt động của CTV <span class="font-bold text-white">{selectedMember?.ctv_code}</span>:</p>
          
          <div class="space-y-1">
            <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Trạng thái mới</label>
            <select
              bind:value={newStatus}
              class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2.5 text-xs focus:outline-none focus:border-luxury-copper"
            >
              <option value="ACTIVE">HOẠT ĐỘNG (ACTIVE)</option>
              <option value="SUSPENDED">TẠM ĐÌNH CHỈ (SUSPENDED)</option>
              <option value="BANNED">KHÓA VĨNH VIỄN (BANNED)</option>
            </select>
          </div>

          <div class="space-y-1">
            <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Lý do điều chỉnh (AuditLog)</label>
            <textarea
              bind:value={adminNote}
              placeholder="Nhập lý do thay đổi trạng thái..."
              rows="3"
              class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2 focus:outline-none focus:border-luxury-copper"
            ></textarea>
          </div>

          <button 
            onclick={handleUpdateStatus}
            class="w-full py-3 bg-red-600 hover:bg-red-500 text-white font-black text-xs tracking-[3px] uppercase rounded-lg transition-all shadow-md mt-4"
          >
            XÁC NHẬN CẬP NHẬT
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- ── MODAL: PAYOUT GIẢI NGÂN ────────────────────────────────────────────── -->
  {#if showPayoutModal}
    <div class="fixed inset-0 bg-stone-950/70 backdrop-blur-sm z-[99999] flex items-center justify-center p-4" transition:fade>
      <div class="bg-stone-900 border border-stone-850 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl" transition:scale={{ start: 0.95, duration: 200 }}>
        <div class="px-6 py-5 bg-stone-950 border-b border-stone-850 text-white flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Coins class="w-4 h-4 text-luxury-copper" />
            <h3 class="text-xs tracking-[2px] font-bold uppercase">XÁC NHẬN DUYỆT RÚT HOA HỒNG</h3>
          </div>
          <button onclick={() => showPayoutModal = false} class="text-stone-400 hover:text-white transition-colors text-xs font-black">ĐÓNG</button>
        </div>
        <div class="p-6 space-y-4 text-xs leading-relaxed">
          <div class="bg-stone-950 border border-stone-800 p-4 rounded-xl space-y-2">
            <div class="flex justify-between text-stone-400">
              <span>Đại lý nhận:</span>
              <span class="font-bold text-white tracking-wider">{selectedWithdrawal?.ctv_code}</span>
            </div>
            <div class="flex justify-between text-stone-400">
              <span>Tài khoản nhận:</span>
              <span class="font-bold text-stone-300">
                {selectedWithdrawal?.bank_info?.bank} • {selectedWithdrawal?.bank_info?.account_no}
              </span>
            </div>
            <div class="flex justify-between text-stone-400 border-t border-stone-900 pt-2 mt-2">
              <span>Số tiền yêu cầu:</span>
              <span class="font-black text-luxury-copper">{formatVnd(selectedWithdrawal?.amount_requested)}</span>
            </div>
          </div>

          <div class="space-y-1">
            <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Số tiền duyệt chi trả (VNĐ)</label>
            <input 
              type="number" 
              bind:value={payoutAmount}
              class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-luxury-copper font-mono font-bold text-luxury-copper"
              required
            />
          </div>

          <div class="space-y-1">
            <label class="block text-[9px] tracking-[2px] font-bold text-stone-400 uppercase">Ghi chú duyệt chi</label>
            <input 
              type="text" 
              bind:value={payoutNote}
              placeholder="VD: Đã chuyển khoản Vietcombank thành công" 
              class="w-full bg-stone-950 text-white border border-stone-800 rounded-lg px-3 py-2 focus:outline-none focus:border-luxury-copper"
            />
          </div>

          <button 
            onclick={handleApprovePayout}
            disabled={isProcessingPayout || payoutAmount <= 0}
            class="w-full py-3 bg-luxury-copper hover:bg-amber-600 disabled:bg-stone-800 disabled:text-stone-600 text-stone-950 font-black text-xs tracking-[3px] uppercase rounded-lg transition-all shadow-md mt-6 flex items-center justify-center gap-1.5"
          >
            {#if isProcessingPayout}
              ĐANG GHI NHẬN THANH TOÁN...
            {:else}
              <UserCheck class="w-4 h-4" /> DUYỆT & GIẢI NGÂN
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}

</div>
