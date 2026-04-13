<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { Loader2, ShieldCheck, CheckCircle2 } from 'lucide-svelte';
  import { fly } from 'svelte/transition';

  const ui = getClientUi();
  let status = $state<'processing' | 'success' | 'error'>('processing');
  let errorMessage = $state('');

  onMount(() => {
    // Wait for SvelteKit page store to initialize
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const error = params.get('error');

    if (error) {
      status = 'error';
      errorMessage = error;
      setTimeout(() => {
        goto('/');
      }, 3000);
      return;
    }

    if (!token) {
      status = 'error';
      errorMessage = 'Không hợp lệ (Missing Token)';
      setTimeout(() => {
        goto('/');
      }, 3000);
      return;
    }

    try {
      // Decode JWT Payload to feed AuthStore
      const payloadBase64 = token.split('.')[1];
      const payloadDecoded = JSON.parse(atob(payloadBase64));
      
      authStore.setSession(token, {
        id: payloadDecoded.id || 'unknown',
        email: payloadDecoded.sub || '',
        name: payloadDecoded.name || payloadDecoded.sub?.split('@')[0] || 'User',
        role: (payloadDecoded.roles && payloadDecoded.roles[0]) || 'CUSTOMER'
      });

      status = 'success';
      
      // Cleanup UI
      ui.closeModal();
      ui.showToast(`Chào mừng ${payloadDecoded.name || 'Sếp'} đã quay trở lại!`, 'success');

      // Redirect home and clean URL immediately
      window.location.replace('/');

    } catch (err) {
      status = 'error';
      errorMessage = 'Token bị hỏng hoặc hết hạn';
      ui.showToast(errorMessage, 'error');
      setTimeout(() => {
        goto('/');
      }, 2000);
    }
  });

</script>

<div class="fixed inset-0 bg-[#f5f5f5] z-[var(--z-modal-overlay)]"></div>
