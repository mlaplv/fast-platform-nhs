<script>
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import UserProfileForm from '$lib/components/storefront/user/UserProfileForm.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';

  const ui = getClientUi();

  $effect(() => {
    if (browser && !authStore.isAuthenticated) {
      ui.openLogin(() => {
        // Success callback if needed
      });
      goto('/');
    }
  });
</script>

<UserLayout>
  <UserProfileForm />
</UserLayout>
