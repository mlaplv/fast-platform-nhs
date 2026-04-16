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
      goto('/', { replaceState: true });

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
