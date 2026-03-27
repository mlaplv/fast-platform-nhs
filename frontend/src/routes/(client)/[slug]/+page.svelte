<script lang="ts">
  import { onMount } from 'svelte';
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { resolveMediaUrl } from '$lib/state/utils';
  import StealthCheckout from '$lib/components/client/StealthCheckout.svelte';
  import ClinicalQuiz from '$lib/components/client/ClinicalQuiz.svelte';
  import HeroBanner from '$lib/components/client/HeroBanner.svelte';
  import type { PageData } from './$types';

  
  
  let { data }: { data: PageData } = $props();
  const { product } = data;

  let timeLeft = $state(1800);

  onMount(() => {
    shopStore.init(product);
    const timer = setInterval(() => timeLeft > 0 && timeLeft--, 1000);
    return () => clearInterval(timer);
  });

  const formatTime = (s: number) => `${Math.floor(s/60)}:${(s%60).toString().padStart(2, '0')}`;
  const scrollToQuiz = () => document.getElementById('diagnostics')?.scrollIntoView({ behavior: 'smooth' });
</script>

<svelte:head>
  <title>{product.name} | Elite Storefront</title>
</svelte:head>

<div class="antialiased selection:bg-accent-blue selection:text-white overflow-x-hidden min-h-screen bg-canvas text-primary font-inter">
  
  <HeroBanner {product} {scrollToQuiz} />

  <!-- SOCIAL PROOF -->
  <section class="py-12 border-b border-subtle bg-canvas">
    <div class="container mx-auto px-6 flex flex-wrap justify-between items-center gap-12 opacity-30 grayscale hover:grayscale-0 transition-all font-black text-2xl tracking-tighter">
      {#each ['VTV1', 'HTV7', 'THANH NIÊN', 'VNEXPRESS', 'DÂN TRÍ'] as brand}
        <span>{brand}</span>
      {/each}
    </div>
  </section>

  <!-- DIAGNOSTICS -->
  <section id="diagnostics" class="py-32 bg-canvas">
    <div class="container mx-auto px-6 max-w-4xl text-center">
      <span class="inline-block px-4 py-1.5 rounded-full bg-accent-blue-glow text-accent-blue font-bold text-[10px] uppercase tracking-[0.3em] mb-8">Personalized Care</span>
      <h3 class="text-5xl md:text-7xl font-black mb-10 tracking-tighter leading-none uppercase">CHẨN ĐOÁN <br/> CÁ NHÂN HÓA</h3>
      <p class="text-secondary text-xl max-w-2xl mx-auto leading-relaxed mb-24">Hệ thống AI phân tích tình trạng để đề xuất nồng độ Nano Silver phù hợp.</p>
      <ClinicalQuiz />
    </div>
  </section>

  <!-- BENTO SCIENCE -->
  <section class="py-32 bg-canvas border-t border-subtle">
    <div class="container mx-auto px-6 max-w-7xl">
      <div class="bento-grid">
        <div class="bento-card bento-card--large bg-accent-blue-glow border border-accent-blue/20 p-12 rounded-[4rem] group overflow-hidden relative">
          <div class="relative z-10 h-full flex flex-col justify-end">
             <h4 class="text-4xl font-black mb-6 leading-none tracking-tighter uppercase">CÔNG NGHỆ <br/> NANO BẠC TỰ THÂN</h4>
             <p class="text-secondary text-lg mb-10 max-w-md italic">Thẩm thấu tuyệt đối, khóa chặt vùng mùi chỉ sau 3 giây.</p>
             <div class="flex flex-wrap gap-3">
               {#each ['Không mùi', 'Không màu', 'Xịt sương mịn'] as tag}
                <span class="px-5 py-2.5 bg-canvas/50 border border-white/10 rounded-full text-[10px] font-black uppercase tracking-widest">{tag}</span>
               {/each}
             </div>
          </div>
          <div class="absolute right-[-5%] bottom-[-5%] w-1/2 h-1/2 opacity-20 grayscale group-hover:scale-110 group-hover:grayscale-0 transition-all duration-[2s]"
               style="background-image: url('{resolveMediaUrl(product.images?.[1] || product.images?.[0])}'); background-size: contain; background-repeat: no-repeat;"></div>
        </div>

        <div class="bento-card bento-card--medium bg-surface border border-subtle p-12 rounded-[4rem] flex flex-col justify-center text-center">
          <div class="text-7xl font-black text-accent-blue mb-2">48H</div>
          <p class="text-[10px] font-black uppercase tracking-[0.4em] opacity-30">Protection</p>
        </div>

        <div class="bento-card bento-card--medium bg-surface border border-subtle p-12 rounded-[4rem] flex flex-col items-center justify-center text-center hover:border-accent-blue transition-colors">
          <div class="w-16 h-16 bg-accent-blue-glow rounded-2xl flex items-center justify-center text-3xl mb-8">🛡️</div>
          <span class="text-lg font-bold uppercase tracking-tight">An Toàn <br/> Tuyệt Đối</span>
        </div>

        <div class="bento-card bento-card--large bg-surface border border-subtle p-12 rounded-[4rem] flex items-center justify-between gap-12 group">
            <div class="flex-1">
               <h4 class="text-3xl font-black mb-6 uppercase tracking-tighter">KHÔNG ĐỂ LẠI DẤU VẾT</h4>
               <p class="text-secondary text-lg">Tuyệt đối không vệt vàng hay bết dính trên áo sơ mi trắng.</p>
            </div>
            <div class="w-56 h-56 bg-cover rounded-[3rem] grayscale group-hover:grayscale-0 transition-all duration-700 border border-subtle shadow-2xl"
                 style="background-image: url('{resolveMediaUrl(product.images?.[2] || product.images?.[0])}')"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- OFFER -->
  <section class="py-32 bg-canvas border-t border-subtle">
    <div class="container mx-auto px-6 max-w-5xl text-center">
      <div class="mb-24 px-8 py-3 bg-red-600 text-white font-black text-xs uppercase tracking-[0.3em] rounded-full inline-block animate-pulse">
        Ưu đãi kết thúc sau: {formatTime(timeLeft)}
      </div>
      <h3 class="text-6xl md:text-8xl font-black leading-[0.85] tracking-tighter uppercase mb-24">
        CHỌN LIỆU TRÌNH <br/> <span class="text-accent-blue">THAY ĐỔI CUỘC SỐNG.</span>
      </h3>

      <div class="package-grid">
         <div class="bg-surface border border-subtle p-12 rounded-[4rem] text-left hover:border-accent-blue/50 transition-all group">
            <h4 class="text-xl font-bold opacity-30 mb-4 tracking-widest uppercase">Combo Cơ Bản</h4>
            <div class="text-5xl font-black mb-12">{(shopStore.currentPrice).toLocaleString()}Đ</div>
            <button onclick={() => shopStore.openCheckout()} class="w-full py-6 elite-glass rounded-3xl font-black hover:bg-accent-blue hover:text-white transition-all text-sm tracking-widest uppercase">CHỌN GÓI NÀY</button>
         </div>

         <div class="bg-surface border-2 border-accent-blue p-12 rounded-[4rem] text-left relative shadow-2xl shadow-accent-blue/20">
            <div class="absolute -top-5 left-1/2 -translate-x-1/2 px-8 py-2 bg-accent-blue text-white font-black text-[10px] uppercase tracking-widest rounded-full">Phổ biến nhất</div>
            <h4 class="text-xl font-bold text-accent-blue mb-4 tracking-widest uppercase">Combo Elite</h4>
            <div class="text-6xl font-black mb-12">{(shopStore.currentPrice * 2 * 0.9).toLocaleString()}Đ</div>
            <button onclick={() => shopStore.openCheckout()} class="w-full py-6 bg-accent-blue text-white rounded-3xl font-black shadow-xl hover:scale-[1.03] active:scale-95 transition-all text-sm tracking-widest uppercase">MUA NGAY</button>
         </div>
      </div>
    </div>
  </section>

  <StealthCheckout />
</div>
