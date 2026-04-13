<script lang="ts">
  import { onMount } from 'svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { 
    Facebook, 
    Linkedin, 
    Instagram, 
    Youtube, 
    Phone, 
    Mail, 
    MapPin, 
    ShieldCheck, 
    Zap,
    Clock,
    ArrowRight,
    Lock,
    CreditCard,
    CheckCircle2,
    Users
  } from 'lucide-svelte';

  interface Props {
    shopInfo: {
      name: string;
      companyName: string;
      taxId: string;
      businessLicense: string;
      slogan: string;
      description: string;
      hotline: string;
      email: string;
      address: string;
    };
  }

  let { shopInfo }: Props = $props();

  const currentYear = new Date().getFullYear();

  // FOMO: Simulated Live Activity Pulse
  let activeViewers = $state(88);
  onMount(() => {
    const interval = setInterval(() => {
       const change = Math.floor(Math.random() * 5) - 2;
       activeViewers = Math.max(76, Math.min(124, activeViewers + change));
    }, 5000);
    return () => clearInterval(interval);
  });

  // Elite V2.2: Link Ecosystem Data
  const ecosystemLinks = [
    { name: 'Giới thiệu', href: '/gioi-thieu' },
    { name: 'Tuyển dụng', href: '/tuyen-dung' },
    { name: 'Chính sách Bảo mật', href: '/chinh-sach-bao-mat-thong-tin' },
    { name: 'Điều khoản Dịch vụ', href: '/dieu-khoan-dich-vu' }
  ];

  const customerLinks = [
    { name: 'Tra cứu đơn hàng', href: '/track' },
    { name: 'Vận chuyển & Giao nhận', href: '/chinh-sach-van-chuyen-giao-nhan' },
    { name: 'Đổi trả & Hoàn tiền', href: '/chinh-sach-doi-tra-hoan-tien' },
    { name: 'Chính sách Kiểm hàng', href: '/chinh-sach-kiem-hang' },
    { name: 'Chính sách Bảo hành', href: '/chinh-sach-bao-hanh' },
    { name: 'Phương thức Thanh toán', href: '/phuong-thuc-thanh-toan' }
  ];
</script>

<footer class="relative overflow-hidden bg-[#0c0a09] border-t border-white/5 text-slate-400 font-medium selection:bg-[#C18F7E]/30 selection:text-white">
  <!-- Dynamic Mesh Background (Viral 2026 Atmosphere) -->
  <div class="absolute inset-0 pointer-events-none opacity-40">
    <div class="absolute top-[0%] left-[-10%] w-[40%] h-[60%] bg-[#C18F7E]/10 blur-[120px] rounded-full animate-pulse"></div>
    <div class="absolute bottom-[-20%] right-[-5%] w-[50%] h-[70%] bg-[#C18F7E]/5 blur-[150px] rounded-full"></div>
  </div>

  <!-- Noise Texture Overlay -->
  <div class="absolute inset-0 pointer-events-none opacity-[0.02] bg-[url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')] brightness-100 contrast-150"></div>

  <div class="max-w-[1240px] mx-auto px-6 pt-10 pb-8 relative z-[var(--z-wave)]">
    <!-- Elite Header Section -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-8 mb-12 items-start">
      
      <!-- Brand & AI Trust Section -->
      <div class="lg:col-span-4 space-y-8">
        <div class="flex flex-col group cursor-default">
          <span class="text-4xl font-black tracking-[0.25em] uppercase leading-none bg-gradient-to-r from-[#C18F7E] via-[#E3B5A4] to-[#C18F7E] bg-clip-text text-transparent drop-shadow-[0_0_15px_rgba(193,143,126,0.2)]">
            {shopInfo.name}
          </span>
          <div class="flex items-center gap-2 mt-4">
             <div class="h-[1px] w-12 bg-gradient-to-r from-[#C18F7E] to-transparent"></div>
             <span class="text-[10px] font-black tracking-[0.4em] text-white/40 uppercase">
               {shopInfo.slogan}
             </span>
          </div>
        </div>

        <p class="text-[14px] leading-relaxed text-slate-400 max-w-[320px] font-normal italic">
          "{shopInfo.description}"
        </p>

        <!-- FOMO: Live Pulse -->
        <div class="flex items-center gap-3 py-3 px-4 bg-[#C18F7E]/5 border border-[#C18F7E]/20 rounded-2xl w-fit backdrop-blur-md group hover:bg-[#C18F7E]/10 transition-all">
          <div class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </div>
          <p class="text-[11px] font-black uppercase tracking-widest text-[#C18F7E]">
            <span class="tabular-nums">{activeViewers}</span> Elite Members Shopping Now
          </p>
        </div>

        <!-- AI Trust Badges (Viral 2026 Flair) -->
        <div class="flex flex-wrap gap-2">
          <div class="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full backdrop-blur-md hover:bg-white/10 transition-all cursor-default group">
            <ShieldCheck size={12} class="text-[#C18F7E] group-hover:scale-110 transition-transform" />
            <span class="text-[8px] font-black uppercase tracking-widest text-white/80">AI Guarded</span>
          </div>
          <div class="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full backdrop-blur-md hover:bg-white/10 transition-all cursor-default group">
            <Zap size={12} class="text-[#C18F7E] group-hover:scale-110 transition-transform" />
            <span class="text-[8px] font-black uppercase tracking-widest text-white/80">Instant Sync</span>
          </div>
          <div class="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full backdrop-blur-md hover:bg-white/10 transition-all cursor-default group">
            <Clock size={12} class="text-[#C18F7E] group-hover:scale-110 transition-transform" />
            <span class="text-[8px] font-black uppercase tracking-widest text-white/80">24/7 Agent</span>
          </div>
        </div>
      </div>

      <!-- Links Column 1: Ecosystem -->
      <div class="lg:col-span-2 space-y-6">
        <h4 class="text-white font-black uppercase text-[10px] tracking-[0.4em] pl-2">Hệ sinh thái</h4>
        <ul class="space-y-3">
          {#each ecosystemLinks as link}
            <li>
              <a href={link.href} class="group flex items-center gap-2 text-[13px] text-slate-500 hover:text-white transition-all duration-300">
                <span class="w-0 h-[1.5px] bg-[#C18F7E] group-hover:w-3 transition-all"></span>
                {link.name}
              </a>
            </li>
          {/each}
        </ul>
      </div>

      <!-- Links Column 2: Support -->
      <div class="lg:col-span-2 space-y-6">
        <h4 class="text-white font-black uppercase text-[10px] tracking-[0.4em] pl-2">Khách hàng</h4>
        <ul class="space-y-3">
          {#each customerLinks as link}
            <li>
              <a href={link.href} class="group flex items-center gap-2 text-[13px] text-slate-500 hover:text-white transition-all duration-300">
                <span class="w-0 h-[1.5px] bg-[#C18F7E] group-hover:w-3 transition-all"></span>
                {link.name}
              </a>
            </li>
          {/each}
        </ul>
      </div>

      <!-- Contact & Social Connect -->
      <div class="lg:col-span-4 space-y-6">
        <h4 class="text-white font-black uppercase text-[10px] tracking-[0.4em] pl-2">Kết nối Micsmo</h4>
        
        <div class="bg-white/[0.02] border border-white/5 p-5 rounded-xl backdrop-blur-3xl space-y-5 hover:border-[#C18F7E]/20 transition-all group">
          <div class="flex items-center gap-4">
            <div class="w-7 h-7 rounded-lg bg-[#C18F7E]/10 flex items-center justify-center shrink-0">
              <MapPin size={14} class="text-[#C18F7E]" />
            </div>
            <p class="text-[12px] leading-relaxed text-slate-300 font-normal italic">
              {shopInfo.address}
            </p>
          </div>

          <div class="flex items-center gap-4">
            <div class="w-7 h-7 rounded-lg bg-[#C18F7E]/10 flex items-center justify-center shrink-0">
              <Mail size={14} class="text-[#C18F7E]" />
            </div>
            <a href="mailto:{shopInfo.email}" class="text-[12px] text-slate-300 hover:text-[#C18F7E] transition-colors">{shopInfo.email}</a>
          </div>

          <div class="pt-4 border-t border-white/5 flex items-center justify-between">
            <div class="flex flex-col">
               <span class="text-[8px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-1">Elite Hotline 24/7</span>
               <a href="tel:{shopInfo.hotline.replace(/-/g, '')}" class="text-xl font-black tracking-tighter text-white hover:text-[#C18F7E] transition-colors tabular-nums">
                 {shopInfo.hotline}
               </a>
            </div>
            <button class="w-9 h-9 rounded-full bg-[#C18F7E] text-[#020617] flex items-center justify-center hover:scale-110 active:scale-95 transition-all shadow-[0_0_20px_rgba(193,143,126,0.3)]">
               <ArrowRight size={18} />
            </button>
          </div>
        </div>

        <!-- Trust Badges & Payments -->
        <div class="bg-zinc-950/40 border border-white/5 p-4 rounded-xl flex items-center justify-between gap-4">
          <div class="flex flex-col gap-2">
            <span class="text-[8px] font-black uppercase tracking-widest text-slate-500">Security & Payments</span>
            <div class="flex items-center gap-3 opacity-60">
              <CreditCard size={14} class="text-slate-300" />
              <Lock size={14} class="text-slate-300" />
              <ShieldCheck size={14} class="text-slate-300" />
            </div>
          </div>
          <div class="flex flex-col items-end">
            <button class="bg-blue-600/10 hover:bg-blue-600/20 border border-blue-600/20 p-2 rounded transition-all group/bct" title="Đã Thông Báo Bộ Công Thương">
               <div class="flex items-center gap-1.5 grayscale group-hover/bct:grayscale-0 transition-all opacity-70 group-hover/bct:opacity-100">
                 <div class="w-6 h-4 bg-red-600/80 rounded-[2px] flex items-center justify-center">
                    <CheckCircle2 size={10} class="text-white" />
                 </div>
                 <span class="text-[7px] font-black text-white leading-none">BCT NO.2026</span>
               </div>
            </button>
          </div>
        </div>
      </div>

    </div>

    <!-- Bottom Bar: Ownership & Legal -->
    <div class="pt-8 border-t border-white/5">
      <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
        <div class="space-y-3">
          <div class="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 italic">
            <p>© {currentYear} <span class="text-white font-bold">{shopInfo.name}</span></p>
            <span class="w-1 h-1 rounded-full bg-white/10"></span>
            {#if shopInfo.companyName}
              <p class="font-bold text-slate-300 uppercase tracking-widest text-[8px]">{shopInfo.companyName}</p>
            {/if}
          </div>
          
          <div class="flex flex-wrap items-center gap-4 text-[9px] font-mono text-slate-600 uppercase tracking-widest leading-relaxed">
            {#if shopInfo.taxId}
              <div class="flex items-center gap-1.5 border-r border-white/5 pr-4 last:border-0 last:pr-0">
                <span class="text-slate-800 font-black">MST:</span>
                <span class="text-slate-500 tabular-nums">{shopInfo.taxId}</span>
              </div>
            {/if}
            {#if shopInfo.businessLicense}
              <div class="flex items-center gap-1.5 border-r border-white/5 pr-4 last:border-0 last:pr-0">
                <span class="text-slate-800 font-black">GPKD:</span>
                <span class="text-slate-500">{shopInfo.businessLicense}</span>
              </div>
            {/if}
            <div class="flex items-center gap-1.5 border-r border-white/5 pr-4 last:border-0 last:pr-0">
               <span class="text-slate-800 font-black">SSL:</span>
               <span class="text-slate-500 font-bold text-emerald-600/80 tracking-tighter">ENCRYPTED 256B</span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-6">
          <div class="flex items-center gap-3">
             {#each [
               { icon: Facebook, label: 'Facebook' },
               { icon: Linkedin, label: 'LinkedIn' },
               { icon: Youtube, label: 'YouTube' }
             ] as social}
               <button aria-label={social.label} class="text-slate-600 hover:text-[#C18F7E] transition-all">
                  <social.icon size={16} />
               </button>
             {/each}
          </div>
          <div class="flex items-center gap-2 group cursor-default">
             <span class="text-[9px] font-black uppercase tracking-widest text-slate-700 group-hover:text-slate-500 transition-colors">Crafted with AI 2026 Tech</span>
             <div class="w-1 h-1 rounded-full bg-[#C18F7E] animate-ping"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</footer>

<style>
  :global(footer) {
    contain: paint;
  }
</style>
