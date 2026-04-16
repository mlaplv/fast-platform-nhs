<script lang="ts">
  import { apiClient } from '$lib/utils/apiClient';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
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
    if (!crypto.subtle) return fallbackSha256(pw);
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
      authStore.syncUser({ has_password: true });
      oldPassword = ''; newPassword = ''; confirmPassword = '';
      ui.closeModal();
    } catch (e) {
      error = (e as Error).message || 'Không thể cập nhật mật khẩu';
    } finally {
      isSaving = false;
    }
  }
</script>

<div class="space-y-8" in:fade>
  <form onsubmit={(e) => { e.preventDefault(); handleUpdatePassword(); }} class="space-y-8 py-6">
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
            class="w-full h-12 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800 pr-10"
          />
          <button
            type="button"
            onclick={() => showOldPassword = !showOldPassword}
            class="absolute right-[10px] top-1/2 -translate-y-1/2 text-stone-300 hover:text-luxury-copper transition-colors"
          >
            {#if showOldPassword}<EyeOff class="w-4 h-4" />{:else}<Eye class="w-4 h-4" />{/if}
          </button>
        </div>
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
          class="w-full h-12 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800 pr-10"
        />
        <button
          type="button"
          onclick={() => showNewPassword = !showNewPassword}
          class="absolute right-[10px] top-1/2 -translate-y-1/2 text-stone-300 hover:text-luxury-copper transition-colors"
        >
          {#if showNewPassword}<EyeOff class="w-4 h-4" />{:else}<Eye class="w-4 h-4" />{/if}
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
          class="w-full h-12 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800 pr-10"
        />
        <button
          type="button"
          onclick={() => showConfirmPassword = !showConfirmPassword}
          class="absolute right-[10px] top-1/2 -translate-y-1/2 text-stone-300 hover:text-luxury-copper transition-colors"
        >
          {#if showConfirmPassword}<EyeOff class="w-4 h-4" />{:else}<Eye class="w-4 h-4" />{/if}
        </button>
      </div>
    </div>

    <div class="pt-6 flex justify-center">
      <button
        type="submit"
        disabled={isSaving}
        class="group relative px-16 py-4 bg-stone-900 text-white overflow-hidden transition-all duration-500 hover:shadow-[0_10px_30px_rgba(0,0,0,0.15)] disabled:opacity-50"
      >
        <div class="absolute inset-0 bg-luxury-copper translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
        <span class="relative z-10 text-[11px] uppercase tracking-[4px] font-black">
          {isSaving ? 'Đang cập nhật...' : 'Xác nhận đổi'}
        </span>
      </button>
    </div>
  </form>
</div>
