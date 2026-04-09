<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  // Bottom Navigation Viral Immersive 2026 cho Mobile
  // Tuân thủ Elite V2.2: Hiệu ứng Glassmorphism, Safe Area
  let activeTab = $derived($page.url.pathname.startsWith('/tin-tuc') ? 'news' : ($page.url.pathname === '/' ? 'home' : 'other'));

  const tabs = [
    { id: 'home', label: 'Trang chủ', icon: '🏠', activeIcon: '🏠', href: '/' },
    { id: 'shop', label: 'Cửa hàng', icon: '🛍️', activeIcon: '🛍️', href: '/' },
    { id: 'news', label: 'Tin tức', icon: '📰', activeIcon: '📰', href: '/tin-tuc/' },
    { id: 'profile', label: 'Tôi', icon: '👤', activeIcon: '👤', href: '/' }
  ];
</script>

<nav class="fixed bottom-0 w-full z-[var(--z-mobile-tab-bar)] bg-black/80 backdrop-blur-xl border-t border-white/5 text-white flex justify-around items-center pt-3 pb-[calc(12px+env(safe-area-inset-bottom))] px-2 shadow-[0_-10px_30px_rgba(0,0,0,0.5)]">
  {#each tabs as tab}
    <button
      onclick={() => goto(tab.href)}
      class="flex flex-col items-center gap-1.5 transition-all duration-300 relative group {activeTab === tab.id ? 'scale-110' : 'opacity-60 grayscale-[0.5]'}"
    >
      <div class="relative">
        <span class="text-2xl drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
          {activeTab === tab.id ? tab.activeIcon : tab.icon}
        </span>
      </div>
      <span class="text-[10px] font-black tracking-widest uppercase transition-colors {activeTab === tab.id ? 'text-red-500' : 'text-slate-400'}">
        {tab.label}
      </span>

      {#if activeTab === tab.id}
        <div class="absolute -bottom-2 w-1 h-1 bg-red-600 rounded-full shadow-[0_0_10px_#ef4444]"></div>
      {/if}
    </button>
  {/each}
</nav>
