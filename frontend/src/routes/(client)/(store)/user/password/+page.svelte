<script lang="ts">
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade } from 'svelte/transition';

  const ui = getClientUi();

  let oldPassword = $state('');
  let newPassword = $state('');
  let confirmPassword = $state('');
  let isSaving = $state(false);

  async function handleUpdatePassword() {
    if (!oldPassword || !newPassword || !confirmPassword) {
      ui.showToast('Vui lòng điền đầy đủ thông tin.', 'warning');
      return;
    }
    if (newPassword !== confirmPassword) {
      ui.showToast('Mật khẩu mới không khớp.', 'error');
      return;
    }
    if (newPassword.length < 6) {
      ui.showToast('Mật khẩu phải có ít nhất 6 ký tự.', 'warning');
      return;
    }

    isSaving = true;
    try {
      await apiClient.patch('/api/v1/client/user/password', {
        old_password: oldPassword,
        new_password: newPassword
      });
      ui.showToast('Đổi mật khẩu thành công! ✨', 'success');
      oldPassword = '';
      newPassword = '';
      confirmPassword = '';
    } catch (e: any) {
      ui.showToast(e.message || 'Lỗi khi đổi mật khẩu.', 'error');
    } finally {
      isSaving = false;
    }
  }
</script>

<UserLayout>
  <div class="space-y-8" in:fade>
    <div class="border-b border-stone-100 pb-5">
      <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Đổi Mật Khẩu</h1>
      <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Để bảo mật tài khoản, vui lòng không chia sẻ mật khẩu cho người khác</p>
    </div>

    <div class="max-w-md space-y-8 py-6">
      <div class="space-y-2">
        <label for="old_pass" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Mật khẩu hiện tại</label>
        <input
          id="old_pass"
          type="password"
          bind:value={oldPassword}
          class="w-full h-11 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800"
        />
      </div>

      <div class="space-y-2">
        <label for="new_pass" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Mật khẩu mới</label>
        <input
          id="new_pass"
          type="password"
          bind:value={newPassword}
          class="w-full h-11 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800"
        />
      </div>

      <div class="space-y-2">
        <label for="confirm_pass" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Xác nhận mật khẩu mới</label>
        <input
          id="confirm_pass"
          type="password"
          bind:value={confirmPassword}
          class="w-full h-11 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800"
        />
      </div>

      <div class="pt-6">
        <button
          onclick={handleUpdatePassword}
          disabled={isSaving}
          class="group relative px-12 py-3 bg-stone-900 text-white overflow-hidden transition-all duration-500 hover:shadow-lg disabled:opacity-50"
        >
          <div class="absolute inset-0 bg-luxury-copper translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
          <span class="relative z-10 text-[12px] uppercase tracking-[4px] font-bold">
            {isSaving ? 'Đang cập nhật...' : 'Xác nhận đổi'}
          </span>
        </button>
      </div>
    </div>
  </div>
</UserLayout>
