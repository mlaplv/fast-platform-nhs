<script lang="ts">
  import { fade } from 'svelte/transition';

  interface Props {
    active: boolean;
    onClose: () => void;
  }
  let { active = $bindable(), onClose }: Props = $props();

  const links = [
    { label: 'Hồ sơ', href: '/user/profile' },
    { label: 'Đơn mua', href: '/user/purchase' },
    { label: 'Địa chỉ', href: '/user/address' },
    { label: 'Mật khẩu', href: '/user/password' },
    { label: 'Thông báo', href: '/user/notifications' },
  ];
</script>

{#if active}
  <div class="fixed inset-0 z-[var(--z-modal)] bg-white p-6 pt-20" transition:fade>
    <button onclick={onClose} class="absolute top-6 right-6 text-gray-900">
      <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
    </button>
    <nav class="space-y-6">
      {#each links as link}
        <a href={link.href} onclick={onClose} class="block text-lg font-black uppercase tracking-widest text-stone-900">{link.label}</a>
      {/each}
    </nav>
  </div>
{/if}
