<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import { fly } from 'svelte/transition';

  const ui = getClientUi();
  let status = $state<'processing' | 'success' | 'error'>('processing');
  let errorMessage = $state('');
  let returnUrl = $state('/');

  onMount(async () => {
    // Wait for SvelteKit page store to initialize
    returnUrl = sessionStorage.getItem('returnTo') || '/';
    sessionStorage.removeItem('returnTo');

    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const error = params.get('error');

    if (error) {
      status = 'error';
      errorMessage = error;
      setTimeout(() => {
        goto(returnUrl);
      }, 3000);
      return;
    }

    if (!token) {
      status = 'error';
      errorMessage = 'Không hợp lệ (Missing Token)';
      setTimeout(() => {
        goto(returnUrl);
      }, 3000);
      return;
    }

    try {
      // Elite V2.2: Robust JWT Decoding (Handles Base64URL + Unicode)
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payloadDecoded = JSON.parse(jsonPayload);

      authStore.setSession(token, {
        id: payloadDecoded.id || 'unknown',
        email: payloadDecoded.sub || '',
        name: payloadDecoded.name || payloadDecoded.sub?.split('@')[0] || 'User',
        role: (payloadDecoded.roles && payloadDecoded.roles[0]) || 'CUSTOMER',
        has_password: !!payloadDecoded.hpw
      });

      status = 'success';
      
      // Cleanup UI
      ui.closeModal();
      
      // Elite V3.0 SPA Navigation: maintain state (Toasts, Pulse notifications)
      const returnScroll = sessionStorage.getItem('returnScroll');
      await goto(returnUrl, { replaceState: true });
      
      if (returnScroll) {
        setTimeout(() => {
          window.scrollTo({ top: parseInt(returnScroll), behavior: 'instant' });
          sessionStorage.removeItem('returnScroll');
        }, 50); // Đợi 50ms để DOM render xong component
      }

    } catch (err) {
      status = 'error';
      errorMessage = 'Token bị hỏng hoặc hết hạn';
      ui.showToast(errorMessage, 'error');
      setTimeout(() => {
        goto(returnUrl);
      }, 2000);
    }
  });

</script>

<SeoHead title="Đang xác thực | {ui.settings?.basic_info?.site_name || 'osmo Elite'}" robots="noindex, nofollow" />

<div class="fixed inset-0 bg-white z-[var(--z-modal-overlay)] flex items-center justify-center p-6">

    <div class="max-w-md w-full text-center space-y-6">
        {#if status === 'processing'}
            <div class="flex flex-col items-center gap-4">
                <div class="relative w-16 h-16">
                    <Loader2 class="w-16 h-16 text-luxury-copper animate-spin" />
                    <div class="absolute inset-0 flex items-center justify-center">
                        <ShieldCheck class="w-6 h-6 text-luxury-copper/50" />
                    </div>
                </div>
                <div class="space-y-1">
                    <h2 class="text-xl font-bold text-gray-900 tracking-tight">Đang xác thực...</h2>
                    <p class="text-sm text-gray-500">Hệ thống đang thiết lập phiên làm việc an toàn.</p>
                </div>
            </div>
        {:else if status === 'success'}
            <div class="flex flex-col items-center gap-4 animate-in fade-in zoom-in duration-500">
                <div class="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center">
                    <CheckCircle2 class="w-10 h-10 text-green-500" />
                </div>
                <div class="space-y-1">
                    <h2 class="text-xl font-bold text-gray-900 tracking-tight">Đăng nhập thành công!</h2>
                    <p class="text-sm text-gray-500">Đang chuyển hướng...</p>
                </div>
            </div>
        {:else}
            <div class="flex flex-col items-center gap-4 animate-in fade-in zoom-in duration-500">
                <div class="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center text-2xl">
                    ⚠️
                </div>
                <div class="space-y-1">
                    <h2 class="text-xl font-bold text-gray-900 tracking-tight">Xác thực thất bại</h2>
                    <p class="text-sm text-red-500">{errorMessage || 'Đã có lỗi xảy ra trong quá trình xác thực.'}</p>
                </div>
                <button
                    onclick={() => goto(returnUrl)}
                    class="mt-4 px-6 py-2 bg-gray-900 text-white rounded-full text-sm font-bold hover:bg-gray-800 transition-colors"
                >
                    {returnUrl === '/' ? 'Quay lại trang chủ' : 'Quay lại trang trước'}
                </button>
            </div>
        {/if}
    </div>
</div>
