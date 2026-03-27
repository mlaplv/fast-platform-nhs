<script lang="ts">
  import { onMount } from 'svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { browser } from '$app/environment';
  
  let { product = {}, scrollToQuiz } = $props();
  let themeMode = $state('system');

  const productName = $derived(product?.name || 'Elite Formulation');
  const mainImage = $derived(resolveMediaUrl(product?.images?.[0] || ''));

  const updateDOM = (theme: string) => {
    if (!browser) return;
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
  };

  const applyTheme = (mode: string) => {
    themeMode = mode;
    if (!browser) return;
    localStorage.setItem('hero-theme-mode', mode);
    if (mode === 'system') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      updateDOM(isDark ? 'dark' : 'light');
    } else {
      updateDOM(mode);
    }
  };

  onMount(() => {
    if (browser) {
      applyTheme(localStorage.getItem('hero-theme-mode') || 'system');
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      const h = (e: MediaQueryListEvent) => themeMode === 'system' && updateDOM(e.matches ? 'dark' : 'light');
      mq.addEventListener('change', h);
      return () => mq.removeEventListener('change', h);
    }
  });
</script>

<section class="hero-center-layout">
  <!-- THEME SWITCHER -->
  <button class="fixed top-6 right-6 z-[100] w-12 h-12 rounded-full elite-glass flex items-center justify-center shadow-xl" onclick={() => {
    const modes = ['system', 'light', 'dark'] as const;
    applyTheme(modes[(modes.indexOf(themeMode as any) + 1) % modes.length]);
  }}>
    {#if themeMode === 'dark'}<svg class="w-5 h-5 text-yellow-400 fill-current" viewBox="0 0 24 24"><path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5z"/></svg>{:else}<svg class="w-5 h-5 text-blue-500 fill-current" viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c.44-.06.9-.1 1.36-.1H12z"/></svg>{/if}
  </button>

  <!-- TOP HUD -->
  <header class="absolute top-8 left-1/2 -translate-x-1/2 z-20 flex elite-glass rounded-full p-1 opacity-80 backdrop-blur-md">
      <div class="px-4 py-1.5 border-r border-white/5 flex items-center gap-2">
        <div class="w-1.5 h-1.5 bg-pink-500 rounded-full"></div>
        <span class="text-[9px] font-black uppercase tracking-widest opacity-60">Nano Silver 99.8%</span>
      </div>
      <div class="px-4 py-1.5 flex items-center">
        <span class="text-[9px] font-black uppercase tracking-widest text-blue-400">Clinical Mode</span>
      </div>
  </header>

  <!-- VIDEO BACKGROUND -->
  <div class="absolute inset-0 z-0 w-full h-full">
    <div class="absolute inset-0 bg-gradient-to-b from-canvas/60 to-canvas z-10 w-full h-full"></div>
    <video autoplay muted loop playsinline class="w-full h-full object-cover opacity-20 filter grayscale v-zoom">
      <source src="/video/video-hn.mp4" type="video/mp4" />
    </video>
  </div>

  <div class="container relative z-10 flex flex-col items-center">
    <div class="mb-4 inline-flex items-center px-4 py-1 bg-blue-600/10 border border-blue-500/20 rounded-md">
       <span class="text-[8px] font-black uppercase tracking-[0.4em] text-blue-500">Elite Formulation V2.2</span>
    </div>

    <h1 class="text-7xl md:text-9xl font-black mb-8">CHẤM DỨT <br/> MÙI CƠ THỂ.</h1>

    <div class="relative w-full max-w-5xl py-12 flex items-center justify-center">
       <div class="absolute inset-0 liquid-oval-bg scale-y-[0.8] md:scale-y-[0.7]"></div>
       <div class="relative z-10 flex flex-col md:flex-row items-center justify-center gap-16 md:gap-32 w-full px-12">
          <div class="relative float-anim">
             <div class="bg-white p-6 rounded-[2.5rem] shadow-2xl border-4 border-white/10">
                <img src="{mainImage}" alt="{productName}" class="w-48 md:w-64 object-contain" />
             </div>
          </div>
          <div class="flex flex-col gap-8 text-left">
             <div class="flex items-center gap-6"><div class="w-2 h-2 bg-blue-500 rounded-full shadow-lg"></div><div class="flex flex-col"><span class="text-[9px] font-black text-blue-500 uppercase">Absorption</span><span class="text-3xl font-black">XUẤT THẤU 3s</span></div></div>
             <div class="flex items-center gap-6"><div class="w-2 h-2 bg-indigo-500 rounded-full shadow-lg"></div><div class="flex flex-col"><span class="text-[9px] font-black text-indigo-500 uppercase">Persistence</span><span class="text-3xl font-black">48H KHÔ THOÁNG</span></div></div>
             <div class="flex items-center gap-6"><div class="w-2 h-2 bg-emerald-500 rounded-full shadow-lg"></div><div class="flex flex-col"><span class="text-[9px] font-black text-emerald-500 uppercase">Organic</span><span class="text-3xl font-black">THẢO DƯỢC 100%</span></div></div>
          </div>
       </div>
    </div>
  </div>
</section>

<style>
  .hero-center-layout {
    position: relative; width: 100%; min-height: 100vh; background-color: #020617; color: #fff; overflow: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center;
  }
  .elite-glass {
    background: rgba(0,0,0,0.3); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08);
  }
  .liquid-oval-bg {
    background: rgba(255,255,255,0.02); backdrop-filter: blur(40px); border: 1px solid rgba(255,255,255,0.08); border-radius: 1000px;
  }
  .v-zoom { animation: zoom-slow 40s linear infinite; }
  .float-anim { animation: float 8s ease-in-out infinite; }
  @keyframes zoom-slow { 0%, 100% { transform: scale(1.1); } 50% { transform: scale(1.25); } }
  @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-30px); } }
</style>
