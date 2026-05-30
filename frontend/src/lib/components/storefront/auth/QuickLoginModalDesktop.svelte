<script lang="ts">
  import AuthForm from '$lib/components/storefront/auth/AuthForm.svelte';
  import X from "@lucide/svelte/icons/x";
  import Users from "@lucide/svelte/icons/users";
  import Gift from "@lucide/svelte/icons/gift";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { fade, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';

  const ui = getClientUi();
  let mode = $derived(ui.authModal.mode);
</script>

<div 
  use:portal 
  class="fixed inset-0 flex items-center justify-center bg-slate-950/70 backdrop-blur-md p-4 z-50" 
  style:z-index={Z_INDEX_CLIENT.OVERLAY}
  in:fade={{ duration: 400 }}
  onclick={(e) => e.target === e.currentTarget && ui.closeModal()}
>
  <div 
    class="bg-white w-full max-w-[850px] rounded-xl shadow-[0_25px_70px_rgba(0,0,0,0.3)] overflow-hidden relative flex flex-row min-h-[580px] max-h-[90vh] transition-all border border-slate-200"
    style:z-index={Z_INDEX_CLIENT.MODAL}
    in:scale={{ start: 0.98, duration: 250, easing: cubicOut }}
  >
    <!-- Left Column: Frosted Liquid Glass Panel (Hình 2 Style - Elegant & Sharp) -->
    <div class="hidden md:flex flex-col justify-between w-1/2 p-8 relative overflow-hidden border-r border-white/10 shrink-0 select-none bg-slate-950/20 backdrop-blur-xl">
      <!-- Dark Indigo & Violet Backing Gradients (Gives the gorgeous deep glass colorful tint of Image 2) -->
      <div class="absolute inset-0 bg-gradient-to-br from-[#0c1a30]/90 via-[#070e1b]/95 to-[#1c183a]/80 -z-20"></div>
      <div class="absolute inset-0 bg-gradient-to-tr from-cyan-500/5 via-transparent to-indigo-500/10 -z-10"></div>
      <!-- Subtle diagonal dynamic glass reflection -->
      <div class="absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.02] to-transparent -z-10 rotate-12 scale-150"></div>

      <!-- Top Header Branding -->
      <div class="relative z-10 flex items-center gap-2">
        <div class="w-7 h-7 rounded bg-white/5 flex items-center justify-center border border-white/10 backdrop-blur-md">
          <Sparkles class="w-4 h-4 text-cyan-400" />
        </div>
        <span class="text-xs font-bold tracking-[0.15em] text-white/90 uppercase italic">Osmo.vn Perks</span>
      </div>

      <!-- Core Perks List (Translucent Frosted Glass Cards) -->
      <div class="relative z-10 space-y-6 my-auto pt-6">
        <div>
          <h3 class="text-xl font-bold text-white tracking-tight">Quyền lợi thành viên</h3>
          <p class="text-[11px] text-slate-300 font-medium tracking-wide mt-1 leading-relaxed">Đăng nhập tài khoản để nhận đặc quyền mua sắm & chiết khấu độc quyền.</p>
        </div>

        <div class="space-y-3.5">
          <!-- Perk 1: CTV -->
          <div class="group flex items-start gap-3.5 p-3.5 rounded-lg bg-white/[0.02] backdrop-blur-md border border-white/[0.08] hover:bg-white/[0.06] hover:border-white/20 transition-all duration-200">
            <div class="w-9 h-9 rounded bg-white/5 flex items-center justify-center border border-white/10 text-cyan-400 shrink-0">
              <Users class="w-4.5 h-4.5" />
            </div>
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <h4 class="text-xs font-bold text-white">Cộng tác viên (Affiliate)</h4>
                <span class="text-[9px] font-bold text-yellow-400 bg-yellow-400/10 px-1.5 py-0.5 rounded border border-yellow-400/20">+15% Hoa hồng</span>
              </div>
              <p class="text-[11px] text-slate-300 leading-relaxed font-normal">Hưởng hoa hồng trọn đời lên đến 15% khi giới thiệu sản phẩm. Rút tiền nhanh chóng.</p>
            </div>
          </div>

          <!-- Perk 2: Tích điểm -->
          <div class="group flex items-start gap-3.5 p-3.5 rounded-lg bg-white/[0.02] backdrop-blur-md border border-white/[0.08] hover:bg-white/[0.06] hover:border-white/20 transition-all duration-200">
            <div class="w-9 h-9 rounded bg-white/5 flex items-center justify-center border border-white/10 text-emerald-400 shrink-0">
              <Gift class="w-4.5 h-4.5" />
            </div>
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <h4 class="text-xs font-bold text-white">Tích điểm đổi quà</h4>
                <span class="text-[9px] font-bold text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded border border-emerald-400/20">Hoàn 5% Điểm</span>
              </div>
              <p class="text-[11px] text-slate-300 leading-relaxed font-normal">Hoàn tiền tích lũy 5% cho mọi đơn hàng. Điểm tích lũy quy đổi quà tặng VIP.</p>
            </div>
          </div>

          <!-- Perk 3: Quản lý voucher & đơn hàng -->
          <div class="group flex items-start gap-3.5 p-3.5 rounded-lg bg-white/[0.02] backdrop-blur-md border border-white/[0.08] hover:bg-white/[0.06] hover:border-white/20 transition-all duration-200">
            <div class="w-9 h-9 rounded bg-white/5 flex items-center justify-center border border-white/10 text-[#e6b1a0] shrink-0">
              <ShoppingBag class="w-4.5 h-4.5" />
            </div>
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <h4 class="text-xs font-bold text-white">Ví Voucher & Đơn hàng</h4>
                <span class="text-[9px] font-bold text-[#e6b1a0] bg-[#c18f7e]/15 px-1.5 py-0.5 rounded border border-[#c18f7e]/30">Ví VIP</span>
              </div>
              <p class="text-[11px] text-slate-300 leading-relaxed font-normal">Ví thông minh tự động áp mã hời nhất và theo dõi lộ trình đơn hàng 24/7.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Branding Footer -->
      <div class="relative z-10 text-[10px] text-slate-500 font-normal leading-relaxed">
        Bằng cách tiếp tục, bạn đồng ý với <a href="/dieu-khoan-dich-vu.html" target="_blank" rel="noopener noreferrer" class="text-slate-400 hover:text-white underline transition-colors">Điều khoản dịch vụ</a> và <a href="/chinh-sach-bao-mat-thong-tin.html" target="_blank" rel="noopener noreferrer" class="text-slate-400 hover:text-white underline transition-colors">Chính sách bảo mật</a> của chúng tôi.
      </div>
    </div>

    <!-- Right Column: Interactive Auth Form (Sentence-case premium style) -->
    <div class="flex-1 p-8 md:p-10 flex flex-col justify-center bg-white relative max-h-[90vh] overflow-y-auto custom-scrollbar">
      <!-- Close Button: Premium floating square glass style -->
      <button 
        onclick={() => ui.closeModal()} 
        class="absolute right-6 top-6 w-9 h-9 flex items-center justify-center rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-400 hover:text-slate-800 transition-all border border-slate-200/60 shadow-sm z-50 hover:scale-105 active:scale-95"
        aria-label="Đóng cửa sổ"
      >
        <X class="w-5 h-5" strokeWidth={2.5} />
      </button>

      <!-- Sentence-case Elegant Header Area -->
      <div class="mb-6 mt-2 shrink-0">
        <h2 class="text-lg font-bold text-slate-900 tracking-tight leading-tight">
          {mode === 'login' ? 'Đăng nhập tài khoản' : (mode === 'register' ? 'Đăng ký thành viên' : 'Hồ sơ tài khoản')}
        </h2>
        <p class="text-xs text-slate-400 mt-1.5 leading-relaxed font-medium">
          {mode === 'login' ? 'Nhập thông tin để truy cập giỏ hàng và tích điểm thành viên' : (mode === 'register' ? 'Đăng ký tài khoản hội viên nhanh chóng chỉ với vài thao tác' : 'Quản lý thông tin tài khoản cá nhân')}
        </p>
      </div>

      <!-- Form Content -->
      <div class="flex-1 pb-2">
        <AuthForm onClose={() => ui.closeModal()} rounded={true} />
      </div>
    </div>
  </div>
</div>
