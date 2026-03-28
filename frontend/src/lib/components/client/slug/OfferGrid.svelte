<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import "./OfferGrid.css";
  
  let { timeLeft = 1800 }: { timeLeft?: number } = $props();

  const formatTime = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };
</script>

<section id="offers" class="offer-section snap-session py-32 relative overflow-hidden">
  <!-- Dynamic Atmospheric Layers thưa Sếp! -->
  <div class="absolute inset-0 bg-radial-at-t from-blue-900/10 to-transparent pointer-events-none"></div>
  <div class="liquid-orb top-[10%] left-[-10%] w-[800px] h-[800px] bg-blue-600/10"></div>
  <div class="liquid-orb bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-cyan-400/5"></div>

  <div class="container mx-auto px-6 max-w-6xl text-center relative z-10">
    
    <!-- Minimalist Status Bar -->
    <div class="flex justify-center mb-16">
      <div class="timer-badge px-6 py-1.5 rounded-full text-[9px] uppercase tracking-[0.3em] flex items-center gap-3">
        <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_#22d3ee]"></span>
        Ưu đãi nội bộ kết thúc sau: <span class="font-bold tabular-nums">{formatTime(timeLeft)}</span>
      </div>
    </div>

    <!-- Professional Headline Hierarchy -->
    <div class="max-w-4xl mx-auto mb-20 text-center">
      <h3 class="headline-title">
        Chúng tôi không thể thay đổi <br/> cơ địa của bạn.
      </h3>
      <p class="headline-sub">
        Nhưng cam kết: <span class="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent font-bold">Khóa Mùi 48H.</span>
      </p>
      
      <!-- Integrated Trust Proof -->
      <div class="flex items-center justify-center gap-4 mt-12 opacity-40 grayscale hover:grayscale-0 transition-all duration-500">
         <span class="text-[8px] uppercase tracking-[0.4em] font-bold text-slate-400">Được kiểm định bởi</span>
         <div class="h-px w-8 bg-slate-800"></div>
         <span class="text-[9px] uppercase tracking-[0.2em] font-black text-slate-300">Clinical Labs VN</span>
         <div class="h-px w-8 bg-slate-800"></div>
         <span class="text-[8px] uppercase tracking-[0.4em] font-bold text-slate-400">Tiêu chuẩn Dược phẩm</span>
      </div>
    </div>

    <!-- Package Architecture -->
    <div class="package-grid grid grid-cols-1 gap-10 items-stretch">
      
      <!-- Card: Trial -->
      <div class="package-card p-10 md:p-12 text-left flex flex-col h-full border-white/5">
        <div class="mb-10">
          <p class="text-[8px] font-bold text-slate-500 uppercase tracking-[0.4em] mb-4">Giai đoạn kích hoạt</p>
          <h5 class="text-xl font-bold text-white mb-6">Combo Cơ Bản</h5>
          
          <div class="flex items-baseline gap-3 mb-2">
            <span class="text-xs text-slate-600 line-through">350.000đ</span>
            <span class="text-3xl font-black text-white">249.000đ</span>
          </div>
          <p class="text-[9px] text-blue-400 font-bold uppercase tracking-widest">+ Phí vận chuyển: 30.000đ</p>
        </div>

        <ul class="bullet-list mb-12 flex-grow space-y-4">
          <li class="flex items-center gap-3">
            <span class="icon-check text-cyan-400">✦</span>
            <span>01 Tinh chất khử mùi Elite</span>
          </li>
          <li class="flex items-center gap-3">
            <span class="icon-check text-cyan-400">✦</span>
            <span>Hiệu quả tức thì lần đầu dùng</span>
          </li>
          <li class="flex items-center gap-3 opacity-20">
            <span class="icon-minus text-slate-700">−</span>
            <span>Miễn phí giao hàng toàn quốc</span>
          </li>
        </ul>

        <button 
          onclick={() => { shopStore.setQuantity(1); shopStore.openCheckout(); }} 
          class="btn-buy ghost w-full text-[9px] uppercase tracking-[0.2em]"
        >
          Bắt đầu trải nghiệm
        </button>
      </div>

      <!-- Card: Professional (Hero) -->
      <div class="package-card popular p-10 md:p-12 text-left relative flex flex-col h-full md:scale-[1.03]">
        <div class="absolute -top-3 right-8 px-4 py-1.5 bg-blue-600/90 text-white font-black text-[8px] uppercase tracking-[0.3em] rounded-md shadow-xl backdrop-blur-md">
          Chuyên gia khuyên dùng
        </div>

        <div class="mb-10">
          <p class="text-[8px] font-bold text-cyan-400 uppercase tracking-[0.4em] mb-4">Phác đồ tối đa</p>
          <h5 class="text-xl font-bold text-white mb-6">Combo Elite Triple</h5>
          
          <div class="flex items-baseline gap-3 mb-2">
            <span class="text-xs text-slate-600 line-through">700.000đ</span>
            <span class="text-4xl font-black text-white">448.000đ</span>
          </div>
          <p class="text-[9px] text-emerald-400 font-bold uppercase tracking-widest">Tiết kiệm: 252.000đ</p>
        </div>

        <ul class="bullet-list mb-12 flex-grow space-y-4">
          <li class="flex items-center gap-3 font-bold text-slate-200">
            <span class="icon-check text-cyan-400">✦</span>
            <span>02 Tinh chất (Đủ liệu trình)</span>
          </li>
          <li class="flex items-center gap-3 font-bold text-emerald-400">
            <span class="icon-check text-emerald-400">✦</span>
            <span>Miễn phí vận chuyển (Freeship)</span>
          </li>
          <li class="flex items-center gap-3">
            <span class="icon-check text-cyan-400">✦</span>
            <span>Cam kết hoàn tiền ẩn danh</span>
          </li>
          <li class="flex items-center gap-3">
            <span class="icon-check text-cyan-400">✦</span>
            <span>Tặng kèm Voucher: 100k</span>
          </li>
        </ul>

        <button 
          onclick={() => { shopStore.setQuantity(2); shopStore.openCheckout(); }} 
          class="btn-buy primary w-full text-[9px] uppercase tracking-[0.2em]"
        >
          Chọn phác đồ tự tin
        </button>
      </div>

    </div>
  </div>

  <!-- Dynamic Line Wave Divider - High Impact Edition thưa Sếp! -->
  <div class="wave-container">
    <svg viewBox="0 0 1440 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
      <defs>
        <linearGradient id="wave-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#3b82f6" stop-opacity="0" />
          <stop offset="50%" stop-color="#22d3ee" stop-opacity="1" />
          <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
        </linearGradient>
      </defs>
      <!-- Multi-layered lines for 'strength' -->
      <path class="wave-line opacity-20" d="M0,160 C320,300 420,20 720,160 C1020,300 1120,20 1440,160" />
      <path class="wave-line" d="M0,200 C320,340 420,60 720,200 C1020,340 1120,60 1440,200" />
      <path class="wave-line secondary" d="M0,240 C320,100 420,380 720,240 C1020,100 1120,380 1440,240" />
      <path class="wave-line opacity-30" d="M0,100 C320,240 420,-40 720,100 C1020,240 1120,-40 1440,100" />
    </svg>
  </div>
</section>
