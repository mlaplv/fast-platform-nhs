<script lang="ts">
  import { onMount } from 'svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  const ui = getClientUi();
  import Facebook from "@lucide/svelte/icons/facebook";
  import Linkedin from "@lucide/svelte/icons/linkedin";
  import Youtube from "@lucide/svelte/icons/youtube";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import Mail from "@lucide/svelte/icons/mail";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Zap from "@lucide/svelte/icons/zap";
  import Clock from "@lucide/svelte/icons/clock";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import Lock from "@lucide/svelte/icons/lock";
  import CreditCard from "@lucide/svelte/icons/credit-card";
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";

  interface Props {
    shopInfo: {
      name: string;
      companyName: string;
      taxId: string;
      businessLicense: string;
      slogan: string;
      subslogan: string;
      description: string;
      hotline: string;
      email: string;
      address: string;
      social_links?: {
        facebook?: string;
        tiktok?: string;
        zalo?: string;
        youtube?: string;
        linkedin?: string;
      };
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

  // Accordion state (tablet md only)
  let openSections = $state<Record<string, boolean>>({
    ecosystem: false,
    customer: false,
    connect: false
  });
  function toggleSection(key: string): void {
    openSections[key] = !openSections[key];
  }

  const ecosystemLinks = [
    { name: 'Giới thiệu', href: '/gioi-thieu.html' },
    { name: 'Tuyển dụng', href: '/tuyen-dung.html' },
    { name: 'Chính sách Bảo mật', href: '/chinh-sach-bao-mat-thong-tin.html' },
    { name: 'Điều khoản Dịch vụ', href: '/dieu-khoan-dich-vu.html' }
  ];

  const customerLinks = [
    { name: 'Tra cứu đơn hàng', href: '/track' },
    { name: 'Vận chuyển & Giao nhận', href: '/chinh-sach-van-chuyen-giao-nhan.html' },
    { name: 'Đổi trả & Hoàn tiền', href: '/chinh-sach-doi-tra-hoan-tien.html' },
    { name: 'Chính sách Kiểm hàng', href: '/chinh-sach-kiem-hang.html' },
    { name: 'Chính sách Bảo hành', href: '/chinh-sach-bao-hanh.html' },
    { name: 'Phương thức Thanh toán', href: '/phuong-thuc-thanh-toan.html' }
  ];

  const socialLinks = [
    { icon: Facebook, label: 'Facebook', href: shopInfo.social_links?.facebook || '#' },
    { icon: Linkedin, label: 'LinkedIn', href: shopInfo.social_links?.linkedin || '#' },
    { icon: Youtube, label: 'YouTube', href: shopInfo.social_links?.youtube || '#' }
  ];
</script>

<footer class="relative overflow-hidden bg-[#0c0a09] border-t border-white/5 text-slate-400 font-medium selection:bg-[#C18F7E]/30 selection:text-white">
  <!-- Dynamic Mesh Background -->
  <div class="absolute inset-0 pointer-events-none opacity-40">
    <div class="absolute top-[0%] left-[-10%] w-[40%] h-[60%] bg-[#C18F7E]/10 blur-[120px] rounded-full animate-pulse"></div>
    <div class="absolute bottom-[-20%] right-[-5%] w-[50%] h-[70%] bg-[#C18F7E]/5 blur-[150px] rounded-full"></div>
  </div>
  <!-- Noise Texture -->
  <div class="absolute inset-0 pointer-events-none opacity-[0.02] bg-[url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')] brightness-100 contrast-150"></div>

  <div class="max-w-[1240px] mx-auto px-6 pt-10 pb-8 relative z-[var(--z-wave)]">

    {#if ui.isMobile}
      <!-- ══════════════════════════════════════════════
           TABLET/MOBILE (≤1023px): Viral FOMO Redesign
           ══════════════════════════════════════════════ -->
      <div class="block mb-6">

        <!-- [1] FOMO Strip – Subtle inline -->
        <div class="fomo-strip">
        <div class="fomo-pulse-dot">
          <span class="fomo-ping"></span>
          <span class="fomo-dot"></span>
        </div>
        <span class="fomo-count tabular-nums">{activeViewers}</span>
        <span class="fomo-label">đang online</span>
        <span class="fomo-sep">·</span>
        <ShieldCheck size={10} class="fomo-icon" />
        <span class="fomo-tag">AI Guard</span>
        <span class="fomo-sep">·</span>
        <Zap size={10} class="fomo-icon" />
        <span class="fomo-tag">Instant</span>
        <span class="fomo-sep">·</span>
        <Clock size={10} class="fomo-icon" />
        <span class="fomo-tag">24/7</span>
      </div>

      <!-- [2] Brand Block – Centered, full width -->
      <div class="brand-block">
        <span class="brand-name">{shopInfo.name}</span>
        <div class="brand-sub">
          <div class="brand-line"></div>
          <span class="brand-slogan">{shopInfo.slogan}</span>
          <div class="brand-line brand-line-rev"></div>
        </div>
        {#if shopInfo.subslogan}
          <p class="brand-desc">"{shopInfo.subslogan}"</p>
        {/if}
      </div>

      <!-- [3] Accordion Links -->
      <div class="accordion-item">
        <button
          class="accordion-trigger"
          onclick={() => toggleSection('ecosystem')}
          aria-expanded={openSections.ecosystem}
          id="acc-trigger-ecosystem"
        >
          <span class="acc-label">Thông tin chung</span>
          <ChevronDown size={14} class="acc-chevron {openSections.ecosystem ? 'rotated' : ''}" />
        </button>
        <div class="accordion-body {openSections.ecosystem ? 'open' : ''}" id="acc-body-ecosystem">
          <ul class="acc-list">
            {#each ecosystemLinks as link}
              <li><a href={link.href} class="acc-link">{link.name}</a></li>
            {/each}
          </ul>
        </div>
      </div>

      <div class="accordion-item">
        <button
          class="accordion-trigger"
          onclick={() => toggleSection('customer')}
          aria-expanded={openSections.customer}
          id="acc-trigger-customer"
        >
          <span class="acc-label">Khách hàng</span>
          <ChevronDown size={14} class="acc-chevron {openSections.customer ? 'rotated' : ''}" />
        </button>
        <div class="accordion-body {openSections.customer ? 'open' : ''}" id="acc-body-customer">
          <ul class="acc-list grid-cols-2-list">
            {#each customerLinks as link}
              <li><a href={link.href} class="acc-link">{link.name}</a></li>
            {/each}
          </ul>
        </div>
      </div>

      <div class="accordion-item">
        <button
          class="accordion-trigger"
          onclick={() => toggleSection('connect')}
          aria-expanded={openSections.connect}
          id="acc-trigger-connect"
        >
          <span class="acc-label">Thông tin liên hệ</span>
          <ChevronDown size={14} class="acc-chevron {openSections.connect ? 'rotated' : ''}" />
        </button>
        <div class="accordion-body {openSections.connect ? 'open' : ''}" id="acc-body-connect">
          <div class="acc-contact-body">
            <div class="acc-contact-row">
              <MapPin size={12} class="text-[#C18F7E] shrink-0 mt-0.5" />
              <p class="acc-contact-text italic">{shopInfo.address}</p>
            </div>
            <div class="acc-contact-row">
              <Mail size={12} class="text-[#C18F7E] shrink-0" />
              <a href="mailto:{shopInfo.email}" class="acc-contact-text hover:text-[#C18F7E] transition-colors">{shopInfo.email}</a>
            </div>
          </div>
        </div>
      </div>

      <!-- [4] Contact Bar – Always visible at bottom of tablet block -->
      <div class="contact-bar">
        <div class="contact-bar-hotline">
          <span class="contact-bar-hotline-label">Hotline 24/7</span>
          <a href="tel:{shopInfo.hotline.replace(/-/g, '')}" class="contact-bar-hotline-number tabular-nums">
            {shopInfo.hotline}
          </a>
        </div>
        <div class="contact-bar-right">
          {#each socialLinks as s}
            <a href={s.href} target="_blank" rel="noopener noreferrer" aria-label={s.label}
               class="contact-bar-social">
              <s.icon size={16} />
            </a>
          {/each}
        </div>
      </div>

    </div>
    {:else}
      <!-- ══════════════════════════════════════════════
           DESKTOP (lg 1024px+): Original 12-col grid
           ══════════════════════════════════════════════ -->
      <div class="grid grid-cols-12 gap-8 mb-12 items-start">

      <!-- Brand & AI Trust -->
      <div class="col-span-4 space-y-8">
        <div class="space-y-4">
          <div class="flex flex-col group cursor-default">
            <span class="text-4xl font-black tracking-[0.25em] leading-none bg-gradient-to-r from-[#C18F7E] via-[#E3B5A4] to-[#C18F7E] bg-clip-text text-transparent drop-shadow-[0_0_15px_rgba(193,143,126,0.2)] uppercase">
              {shopInfo.name}
            </span>
            <div class="flex items-center gap-2 mt-4">
               <div class="h-[1px] w-12 bg-gradient-to-r from-[#C18F7E] to-transparent"></div>
               <span class="text-[10px] font-black tracking-[0.4em] text-white/40 uppercase">{shopInfo.slogan}</span>
            </div>
          </div>
          {#if shopInfo.subslogan}
            <p class="text-[14px] leading-relaxed text-slate-400 max-w-[320px] font-normal italic">"{shopInfo.subslogan}"</p>
          {/if}
        </div>

        <!-- FOMO -->
        <div class="flex items-center gap-3 py-3 px-4 bg-[#C18F7E]/5 border border-[#C18F7E]/20 rounded-2xl w-fit backdrop-blur-md group hover:bg-[#C18F7E]/10 transition-all">
          <div class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </div>
          <p class="text-[11px] font-black tracking-widest text-[#C18F7E]">
            <span class="tabular-nums">{activeViewers}</span> thành viên
          </p>
        </div>

        <!-- AI Badges -->
        <div class="flex flex-wrap gap-2">
          <div class="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full backdrop-blur-md hover:bg-white/10 transition-all cursor-default group">
            <ShieldCheck size={12} class="text-[#C18F7E] group-hover:scale-110 transition-transform" />
            <span class="text-[8px] font-black tracking-widest text-white/80">AI Guarded</span>
          </div>
          <div class="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full backdrop-blur-md hover:bg-white/10 transition-all cursor-default group">
            <Zap size={12} class="text-[#C18F7E] group-hover:scale-110 transition-transform" />
            <span class="text-[8px] font-black tracking-widest text-white/80">Instant Sync</span>
          </div>
          <div class="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full backdrop-blur-md hover:bg-white/10 transition-all cursor-default group">
            <Clock size={12} class="text-[#C18F7E] group-hover:scale-110 transition-transform" />
            <span class="text-[8px] font-black tracking-widest text-white/80">24/7 Agent</span>
          </div>
        </div>
      </div>

      <!-- Links: Ecosystem -->
      <div class="col-span-2 space-y-6">
        <h4 class="text-white font-black text-[10px] tracking-[0.4em] pl-2">Thông tin chung
</h4>
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

      <!-- Links: Customer -->
      <div class="col-span-2 space-y-6">
        <h4 class="text-white font-black text-[10px] tracking-[0.4em] pl-2">Khách hàng</h4>
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

      <!-- Contact & Social -->
      <div class="col-span-4 space-y-6">
        <h4 class="text-white font-black text-[10px] tracking-[0.4em] pl-2">Thông tin liên hệ</h4>
        <div class="bg-white/[0.02] border border-white/5 p-5 rounded-xl backdrop-blur-3xl space-y-5 hover:border-[#C18F7E]/20 transition-all group">
          <div class="flex items-center gap-4">
            <div class="w-7 h-7 rounded-lg bg-[#C18F7E]/10 flex items-center justify-center shrink-0">
              <MapPin size={14} class="text-[#C18F7E]" />
            </div>
            <p class="text-[12px] leading-relaxed text-slate-300 font-normal italic">{shopInfo.address}</p>
          </div>
          <div class="flex items-center gap-4">
            <div class="w-7 h-7 rounded-lg bg-[#C18F7E]/10 flex items-center justify-center shrink-0">
              <Mail size={14} class="text-[#C18F7E]" />
            </div>
            <a href="mailto:{shopInfo.email}" class="text-[12px] text-slate-300 hover:text-[#C18F7E] transition-colors">{shopInfo.email}</a>
          </div>
          <div class="pt-4 border-t border-white/5 flex items-center justify-between">
            <div class="flex flex-col">
               <span class="text-[8px] tracking-[0.2em] text-slate-500 font-bold mb-1">Hotline 24/7</span>
               <a href="tel:{shopInfo.hotline.replace(/-/g, '')}" class="text-xl font-black tracking-tighter text-white hover:text-[#C18F7E] transition-colors tabular-nums">
                 {shopInfo.hotline}
               </a>
            </div>
            <button class="w-9 h-9 rounded-full bg-[#C18F7E] text-[#020617] flex items-center justify-center hover:scale-110 active:scale-95 transition-all shadow-[0_0_20px_rgba(193,143,126,0.3)]">
               <ArrowRight size={18} />
            </button>
          </div>
        </div>

        <!-- Trust Badges -->
        <div class="bg-zinc-950/40 border border-white/5 p-4 rounded-xl flex items-center justify-between gap-4">
          <div class="flex flex-col gap-2">
            <span class="text-[8px] font-black tracking-widest text-slate-500">Security & Payments</span>
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
    {/if}

    <!-- ══════════════════════════════════════════════
         Bottom Bar (shared – responsive)
         ══════════════════════════════════════════════ -->
    <div class="pt-6 border-t border-white/5">
      <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 lg:gap-6">
        <div class="space-y-2 lg:space-y-3">
          <div class="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 italic">
            <p>© {currentYear} <span class="text-white font-bold uppercase">{shopInfo.name}</span></p>
            <span class="w-1 h-1 rounded-full bg-white/10"></span>
            {#if shopInfo.companyName}
              <p class="font-bold text-slate-300 tracking-widest text-[8px]">{shopInfo.companyName}</p>
            {/if}
          </div>
          <div class="flex flex-wrap items-center gap-3 lg:gap-4 text-[9px] font-mono text-slate-600 tracking-widest leading-relaxed">
            {#if shopInfo.taxId}
              <div class="flex items-center gap-1.5">
                <span class="text-slate-800 font-black">MST:</span>
                <span class="text-slate-500 tabular-nums">{shopInfo.taxId}</span>
              </div>
            {/if}
            {#if shopInfo.businessLicense}
              <div class="flex items-center gap-1.5">
                <span class="text-slate-800 font-black">GPKD:</span>
                <span class="text-slate-500">{shopInfo.businessLicense}</span>
              </div>
            {/if}
            <div class="flex items-center gap-1.5">
               <span class="text-slate-800 font-black">SSL:</span>
               <span class="text-emerald-600/80 font-bold tracking-tighter">ENCRYPTED 256B</span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-4 lg:gap-6">
          <div class="flex items-center gap-3">
            {#each socialLinks as s}
              <a href={s.href} target="_blank" rel="noopener noreferrer" aria-label={s.label}
                 class="text-slate-600 hover:text-[#C18F7E] transition-all">
                <s.icon size={16} />
              </a>
            {/each}
          </div>
          <div class="flex items-center gap-2 group cursor-default">
             <span class="text-[9px] font-black tracking-widest text-slate-700 group-hover:text-slate-500 transition-colors">by lapiweb</span>
             <div class="w-1 h-1 rounded-full bg-[#C18F7E] animate-ping"></div>
          </div>
        </div>
      </div>
    </div>

  </div>
</footer>

<style>
  :global(footer) { contain: paint; }

  /* ── FOMO Strip (subtle inline) ── */
  .fomo-strip {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px 0;
    margin-bottom: 16px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
  }
  .fomo-pulse-dot {
    position: relative;
    display: flex;
    width: 6px;
    height: 6px;
    flex-shrink: 0;
  }
  .fomo-ping {
    position: absolute;
    inset: 0;
    border-radius: 9999px;
    background: #4ade80;
    opacity: 0.75;
    animation: ping 1.2s cubic-bezier(0,0,0.2,1) infinite;
  }
  .fomo-dot {
    position: relative;
    display: inline-flex;
    width: 6px;
    height: 6px;
    border-radius: 9999px;
    background: #22c55e;
  }
  @keyframes ping {
    75%, 100% { transform: scale(2); opacity: 0; }
  }
  .fomo-count {
    font-size: 12px;
    font-weight: 900;
    color: #C18F7E;
    letter-spacing: -0.01em;
  }
  .fomo-label {
    font-size: 10px;
    font-weight: 600;
    color: rgba(255,255,255,0.35);
    letter-spacing: 0.05em;
  }
  .fomo-sep {
    color: rgba(255,255,255,0.1);
    font-size: 10px;
    margin: 0 1px;
  }
  :global(.fomo-icon) {
    color: rgba(193,143,126,0.5);
    flex-shrink: 0;
  }
  .fomo-tag {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
  }

  /* ── Brand Block ── */
  .brand-block {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 4px;
  }
  .brand-name {
    font-size: clamp(22px, 5vw, 30px);
    font-weight: 900;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    background: linear-gradient(90deg, #C18F7E, #E3B5A4, #C18F7E);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
    display: block;
  }
  .brand-sub {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 10px;
  }
  .brand-line {
    height: 1px;
    width: 28px;
    background: linear-gradient(90deg, transparent, #C18F7E);
  }
  .brand-line-rev {
    background: linear-gradient(90deg, #C18F7E, transparent);
  }
  .brand-slogan {
    font-size: 8px;
    font-weight: 900;
    letter-spacing: 0.38em;
    color: rgba(255,255,255,0.35);
    text-transform: uppercase;
    white-space: nowrap;
  }
  .brand-desc {
    margin-top: 8px;
    font-size: 11px;
    line-height: 1.6;
    color: rgb(148 163 184);
    font-style: italic;
    font-weight: 400;
    max-width: 300px;
  }

  /* ── Accordion Core ── */
  .accordion-item {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
  .accordion-trigger {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 0;
    background: none;
    border: none;
    cursor: pointer;
    outline: none;
    -webkit-tap-highlight-color: transparent;
  }
  .accordion-trigger:focus-visible {
    outline: 1.5px solid rgba(193, 143, 126, 0.5);
    border-radius: 4px;
  }
  .acc-label {
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.35em;
    color: #fff;
    text-transform: uppercase;
  }
  :global(.acc-chevron) {
    color: rgba(193, 143, 126, 0.7);
    transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0;
  }
  :global(.acc-chevron.rotated) {
    transform: rotate(180deg);
    color: #C18F7E;
  }
  .accordion-body {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.38s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
    opacity: 0;
  }
  .accordion-body.open {
    max-height: 400px;
    opacity: 1;
  }
  .acc-list {
    list-style: none;
    padding: 0 0 12px 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .grid-cols-2-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px 16px;
  }
  .acc-link {
    font-size: 13px;
    color: rgb(100 116 139);
    text-decoration: none;
    transition: color 0.25s ease;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .acc-link::before {
    content: '';
    display: inline-block;
    width: 0;
    height: 1.5px;
    background: #C18F7E;
    transition: width 0.25s ease;
    flex-shrink: 0;
  }
  .acc-link:hover { color: #fff; }
  .acc-link:hover::before { width: 10px; }

  /* ── Accordion Contact Body ── */
  .acc-contact-body {
    padding: 10px 0 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .acc-contact-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }
  .acc-contact-text {
    font-size: 12px;
    color: rgb(203 213 225);
    font-weight: 400;
    line-height: 1.5;
    text-decoration: none;
  }

  /* ── Contact Bar ── */
  .contact-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 16px;
    padding: 14px 16px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    box-sizing: border-box;
    width: 100%;
  }
  .contact-bar-hotline {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .contact-bar-hotline-label {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.22em;
    color: rgb(100 116 139);
    text-transform: uppercase;
  }
  .contact-bar-hotline-number {
    font-size: 20px;
    font-weight: 900;
    letter-spacing: -0.03em;
    color: #fff;
    text-decoration: none;
    transition: color 0.2s ease;
  }
  .contact-bar-hotline-number:hover { color: #C18F7E; }
  .contact-bar-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .contact-bar-social {
    color: rgb(100 116 139);
    transition: color 0.2s ease;
    display: flex;
    align-items: center;
  }
  .contact-bar-social:hover { color: #C18F7E; }
</style>
