<script lang="ts">
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { fallbackSha256 } from '$lib/utils/cryptoFallback';
  import { fade, slide } from 'svelte/transition';
  import { Eye, EyeOff } from 'lucide-svelte';

  const ui = getClientUi();

  let oldPassword = $state('');
  let newPassword = $state('');
  let confirmPassword = $state('');
  let isSaving = $state(false);

  let showOldPassword = $state(false);
  let showNewPassword = $state(false);
  let showConfirmPassword = $state(false);

  const hasPassword = $derived(authStore.user?.has_password ?? true);

  async function hashPassword(pw: string): Promise<string> {
    if (!crypto.subtle) {
      return fallbackSha256(pw);
    }
    const encoder = new TextEncoder();
    const data = encoder.encode(pw);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  async function handleUpdatePassword() {
    if ((hasPassword && !oldPassword) || !newPassword || !confirmPassword) {
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
      const [hashedOld, hashedNew] = await Promise.all([
        hasPassword ? hashPassword(oldPassword) : Promise.resolve(null),
        hashPassword(newPassword)
      ]);

      await apiClient.patch('/api/v1/client/user/password', {
        old_password: hashedOld,
        new_password: hashedNew
      });

      ui.showToast('Mật khẩu đã được cập nhật thành công! ✨', 'success');
      
      // Update local state if successful
      authStore.syncUser({ has_password: true });
      
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

    <form onsubmit={(e) => { e.preventDefault(); handleUpdatePassword(); }} class="max-w-md space-y-8 py-6">
      <!-- Hidden username for browser autofill isolation -->
      {#if authStore.user?.email}
        <input type="text" name="username" value={authStore.user.email} class="hidden" autocomplete="username" readonly />
      {/if}

      {#if hasPassword}
        <div class="space-y-2" transition:slide>
          <label for="old_pass" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Mật khẩu hiện tại</label>
          <div class="relative group">
            <input
              id="old_pass"
              name="password"
              type={showOldPassword ? 'text' : 'password'}
              autocomplete="current-password"
              bind:value={oldPassword}
              class="w-full h-11 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800 pr-10"
            />
            <button
              type="button"
              onclick={() => showOldPassword = !showOldPassword}
              class="absolute right-[10px] top-1/2 -translate-y-1/2 text-stone-300 hover:text-luxury-copper transition-colors"
            >
              {#if showOldPassword}
                <EyeOff class="w-4 h-4" />
              {:else}
                <Eye class="w-4 h-4" />
              {/if}
            </button>
          </div>
        </div>
      {:else}
        <div class="p-4 bg-amber-50 border border-amber-100 rounded-sm" transition:fade>
           <p class="text-[12px] text-amber-700 italic">
             Chào Quý khách! Vì tài khoản của Quý khách đang được tích hợp qua Mạng xã hội/OTP, hệ thống chưa thiết lập mật khẩu riêng. 
             Hãy tạo mật khẩu mới ngay dưới đây để có thêm phương thức đăng nhập và bảo mật tối đa nhé.
           </p>
        </div>
      {/if}

      <div class="space-y-2">
        <label for="new_pass" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Mật khẩu mới</label>
        <div class="relative group">
          <input
            id="new_pass"
            name="new-password"
            type={showNewPassword ? 'text' : 'password'}
            autocomplete="new-password"
            bind:value={newPassword}
            class="w-full h-11 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800 pr-10"
          />
          <button
            type="button"
            onclick={() => showNewPassword = !showNewPassword}
            class="absolute right-[10px] top-1/2 -translate-y-1/2 text-stone-300 hover:text-luxury-copper transition-colors"
          >
            {#if showNewPassword}
              <EyeOff class="w-4 h-4" />
            {:else}
              <Eye class="w-4 h-4" />
            {/if}
          </button>
        </div>
      </div>

      <div class="space-y-2">
        <label for="confirm_pass" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Xác nhận mật khẩu mới</label>
        <div class="relative group">
          <input
            id="confirm_pass"
            name="confirm-password"
            type={showConfirmPassword ? 'text' : 'password'}
            autocomplete="new-password"
            bind:value={confirmPassword}
            class="w-full h-11 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800 pr-10"
          />
          <button
            type="button"
            onclick={() => showConfirmPassword = !showConfirmPassword}
            class="absolute right-[10px] top-1/2 -translate-y-1/2 text-stone-300 hover:text-luxury-copper transition-colors"
          >
            {#if showConfirmPassword}
              <EyeOff class="w-4 h-4" />
            {:else}
              <Eye class="w-4 h-4" />
            {/if}
          </button>
        </div>
      </div>

      <div class="pt-6">
        <button
          type="submit"
          disabled={isSaving}
          class="group relative px-12 py-3 bg-stone-900 text-white overflow-hidden transition-all duration-500 hover:shadow-lg disabled:opacity-50"
        >
          <div class="absolute inset-0 bg-luxury-copper translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
          <span class="relative z-10 text-[12px] uppercase tracking-[4px] font-bold">
            {isSaving ? 'Đang cập nhật...' : 'Xác nhận đổi'}
          </span>
        </button>
      </div>
    </form>
  </div>
</UserLayout>

