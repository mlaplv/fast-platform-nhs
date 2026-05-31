<script lang="ts">
  import { fade, scale } from 'svelte/transition';
  import Landmark from "@lucide/svelte/icons/landmark";
  import Coins from "@lucide/svelte/icons/coins";

  let {
    // Modal visibilities
    showBankModal = $bindable(),
    showWithdrawModal = $bindable(),
    showDeactivateConfirm = $bindable(),

    // Form inputs
    bankName = $bindable(),
    bankAccountNo = $bindable(),
    bankAccountName = $bindable(),
    withdrawAmount = $bindable(),

    // Profile & Action states
    profile,
    isUpdatingBank,
    isWithdrawing,
    isDeactivating,

    // Methods
    handleUpdateBank,
    handleWithdraw,
    handleDeactivate,
    formatVnd,
  } = $props<{
    showBankModal: boolean;
    showWithdrawModal: boolean;
    showDeactivateConfirm: boolean;
    bankName: string;
    bankAccountNo: string;
    bankAccountName: string;
    withdrawAmount: number;
    profile: any;
    isUpdatingBank: boolean;
    isWithdrawing: boolean;
    isDeactivating: boolean;

    handleUpdateBank: (e: Event) => void;
    handleWithdraw: (e: Event) => void;
    handleDeactivate: () => void;
    formatVnd: (val: number) => string;
  }>();
</script>

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
            <span class="font-bold font-mono text-stone-850">{formatVnd(profile?.balance || 0)}</span>
          </div>
          <div class="flex justify-between text-xs text-stone-500">
            <span>Ngân hàng nhận:</span>
            {#if profile?.bank_info?.bank}
              <span class="font-bold text-stone-850">{profile?.bank_info?.bank} - {profile?.bank_info?.account_no}</span>
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
            max={profile?.balance || 0}
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
