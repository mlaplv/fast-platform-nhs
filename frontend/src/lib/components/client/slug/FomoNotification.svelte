<script lang="ts">
  import { onMount } from 'svelte';
  import { fly, scale, fade } from 'svelte/transition';
  import { ShieldCheck, Zap, Radio } from 'lucide-svelte';

  const names = ["Chị Lan", "An T.", "Vân Anh", "Thanh H.", "Ngọc M.", "Chị Phượng", "Minh K.", "Thảo N.", "Hồng Q.", "Chị Mai"];
  const locations = ["Quận 1, HCM", "Hà Đông, Hà Nội", "Hải Châu, Đà Nẵng", "TP. Cần Thơ", "TP. Vinh", "TP. Thủ Đức", "Long Xuyên", "Buôn Ma Thuột", "TP. Huế", "Nam Định"];
  const products = ["Combo 3 Tái Sinh 💎", "Liệu Trình 14 Ngày 🔥", "Gói Kích Hoạt Elite ✨"];

  let currentFomo = $state<{ name: string; loc: string; action: string; time: string } | null>(null);
  let show = $state(false);

  function triggerFomo() {
    const name = names[Math.floor(Math.random() * names.length)];
    const loc = locations[Math.floor(Math.random() * locations.length)];
    const action = products[Math.floor(Math.random() * products.length)];
    const time = Math.floor(Math.random() * 3) + 1;

    currentFomo = { name, loc, action, time: `Cách đây ${time} phút` };
    show = true;

    // Viral 2026: Auto-hide after 7s
    setTimeout(() => {
      show = false;
    }, 7000);

    // Dynamic Interval for Low-Frequency Authenticity (45s - 120s)
    const nextDelay = 45000 + Math.random() * 75000;
    setTimeout(triggerFomo, nextDelay);
  }

  onMount(() => {
    // Neural Link Warmup
    setTimeout(triggerFomo, 15000);
  });
</script>

{#if show && currentFomo}
  <div 
    class="neural-pulse-notification fixed top-24 right-6 md:top-auto md:bottom-32 md:left-6 z-[1000] pointer-events-none"
    in:fly={{ y: 20, duration: 1000 }}
    out:fade={{ duration: 500 }}
  >
    <div class="pulse-container relative">
       <!-- Viral 2026: Neural Ripple Background -->
       <div class="neural-ripple absolute inset-0 bg-luxury-gold/20 blur-[30px] rounded-3xl animate-pulse"></div>
       
       <div class="neural-card p-5 rounded-[2rem] bg-black/60 backdrop-blur-[50px] border border-white/5 border-t-white/20 shadow-[0_40px_100px_rgba(0,0,0,0.9)] flex items-center gap-5">
          <div class="neural-status relative">
             <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-luxury-sakura to-black flex items-center justify-center text-white border border-white/5">
                <Radio class="w-5 h-5 animate-pulse" />
             </div>
             <div class="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-black animate-pulse"></div>
          </div>

          <div class="neural-info">
             <div class="flex items-center gap-3 mb-1">
                <span class="text-[8px] font-black text-white/30 uppercase tracking-[0.4em]">Neural_Sync_Active</span>
                <span class="text-[7px] font-mono text-luxury-gold uppercase">{currentFomo.time}</span>
             </div>
             <p class="text-xs text-white font-medium leading-tight">
                <span class="text-luxury-gold font-black italic">{currentFomo.name}</span> vừa sở hữu {currentFomo.action}
             </p>
             <div class="flex items-center gap-2 mt-2">
                <ShieldCheck class="w-2.5 h-2.5 text-luxury-sakura/50" />
                <span class="text-[8px] font-black text-white/40 uppercase tracking-widest">{currentFomo.loc}</span>
             </div>
          </div>
       </div>
    </div>
  </div>
{/if}

<style>
  .neural-pulse-notification {
     filter: drop-shadow(0 0 30px rgba(193, 143, 126, 0.15));
  }

  .neural-card {
     min-width: 280px;
     transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .neural-ripple {
     z-index: -1;
     animation: ripple-bloom 4s infinite;
  }

  @keyframes ripple-bloom {
     0% { transform: scale(0.95); opacity: 0.1; }
     50% { transform: scale(1.1); opacity: 0.3; }
     100% { transform: scale(0.95); opacity: 0.1; }
  }

  @media (max-width: 768px) {
     .neural-pulse-notification {
        right: 1.5rem;
        left: 1.5rem;
        top: 5rem;
        max-width: none;
     }
     .neural-card {
        min-width: auto;
     }
  }
</style>
