<script lang="ts">
  import BottomSheet from '$lib/components/mobile/BottomSheet.svelte';
  import AuthForm from '$lib/components/storefront/auth/AuthForm.svelte';
  import UserProfileForm from '$lib/components/storefront/user/UserProfileForm.svelte';
  import PasswordForm from '$lib/components/storefront/user/PasswordForm.svelte';
  import PurchaseList from '$lib/components/storefront/user/PurchaseList.svelte';
  import NotificationList from '$lib/components/storefront/user/NotificationList.svelte';
  import AddressWrapper from '$lib/components/storefront/user/AddressWrapper.svelte';
  import DashboardMobile from '$lib/components/storefront/user/DashboardMobile.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  const ui = getClientUi();
  let active = $derived(ui.authModal.isOpen);
  let mode = $derived(ui.authModal.mode);

  $effect(() => {
    console.log('[DEBUG] MobileAccountModal mode:', mode);
  });

  function onClose() {
    ui.closeModal();
  }

  const TITLE_MAP: Record<string, string> = {
    dashboard: 'TÀI KHOẢN',
    profile: 'HỒ SƠ CÁ NHÂN',
    login: 'ĐĂNG NHẬP',
    register: 'GIA NHẬP',
    address: 'ĐỊA CHỈ',
    password: 'ĐỔI MẬT KHẨU',
    purchase: 'ĐƠN MUA',
    notifications: 'THÔNG BÁO'
  };
</script>

<BottomSheet
  bind:active
  title={TITLE_MAP[mode] || 'TÀI KHOẢN'}
  {onClose}
>
  <div class="pt-4">
    {#if mode === 'dashboard'}
      <DashboardMobile />
    {:else if mode === 'profile'}
      <UserProfileForm />
    {:else if mode === 'password'}
      <PasswordForm />
    {:else if mode === 'purchase'}
      <PurchaseList />
    {:else if mode === 'notifications'}
      <NotificationList />
    {:else if mode === 'address'}
      <AddressWrapper />
    {:else if mode === 'login' || mode === 'register'}
      <AuthForm onClose={() => ui.closeModal()} />
    {:else}
      <!-- Fallback to dashboard if mode is unknown -->
      <DashboardMobile />
    {/if}
  </div>
</BottomSheet>

<style>
  :global(.user-content-wrapper :global(div[class*="max-w"])) {
    max-width: none !important;
  }
  :global(.user-content-wrapper :global(div[class*="p-"])) {
    padding: 0 !important;
  }
  :global(.user-content-wrapper :global(aside)) {
    display: none !important;
  }
</style>
