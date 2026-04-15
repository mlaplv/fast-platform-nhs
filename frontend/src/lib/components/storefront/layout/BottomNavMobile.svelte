<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  let activeTab = $derived($page.url.pathname.startsWith('/bai-viet') ? 'news' : ($page.url.pathname === '/' ? 'home' : 'other'));

  const tabs = [
    { id: 'home', label: 'TRANG CHỦ', icon: '🏠', activeIcon: '🏠', href: '/' },
    { id: 'shop', label: 'CỬA HÀNG', icon: '🛍️', activeIcon: '🛍️', href: '/' },
    { id: 'news', label: 'BÀI VIẾT', icon: '📰', activeIcon: '📰', href: '/bai-viet' },
    { id: 'profile', label: 'TÔI', icon: '👤', activeIcon: '👤', href: '/user/profile' }
  ];
</script>

<nav class="fixed bottom-0 w-full z-[var(--z-mobile-tab-bar)] bg-[#363636] flex justify-around items-center pt-2.5 pb-[calc(10px+env(safe-area-inset-bottom))] px-1 shadow-[0_-20px_30px_rgba(255,255,255,0.7)]">
  {#each tabs as tab}
    <button
      onclick={() => goto(tab.href)}
      class="flex flex-col items-center gap-1 transition-all duration-200 relative w-1/4 {activeTab === tab.id ? 'opacity-100' : 'opacity-60'}"
    >
      <span class="text-[22px] leading-none {activeTab !== tab.id ? 'grayscale brightness-150' : ''}">
        {activeTab === tab.id ? tab.activeIcon : tab.icon}
      </span>
      <span class="text-[10px] font-bold tracking-widest text-[#B0B0B0] {activeTab === tab.id ? '!text-white' : ''}">
        {tab.label}
      </span>
    </button>
  {/each}
</nav>
