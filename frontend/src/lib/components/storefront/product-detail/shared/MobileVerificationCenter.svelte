<script lang="ts">
  import { fade, scale, fly } from 'svelte/transition';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import History from "@lucide/svelte/icons/history";
  import Award from "@lucide/svelte/icons/award";
  import Truck from "@lucide/svelte/icons/truck";
  import Calendar from "@lucide/svelte/icons/calendar";
  import PackageCheck from "@lucide/svelte/icons/package-check";
  import X from "@lucide/svelte/icons/x";
  import Download from "@lucide/svelte/icons/download";
  import Share2 from "@lucide/svelte/icons/share-2";
  import CheckCircle from "@lucide/svelte/icons/check-circle";
  import Activity from "@lucide/svelte/icons/activity";

  import Fingerprint from "@lucide/svelte/icons/fingerprint";
  import Image from "@lucide/svelte/icons/image";
  import type { Product, BarcodeVerificationResponse } from '$lib/types';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { portal } from '$lib/core/actions/portal';
  import { page } from '$app/stores';
  import { logger } from '$lib/utils/logger';

  let { product, verificationData }: { 
    product: Product, 
    verificationData?: BarcodeVerificationResponse 
  } = $props();
 
  const ui = getClientUi();

  // Elite V2.2: Ultra-Lean Mobile Data Sync (1:1 with Desktop Logic)
  let manufacturer = $derived.by((): BarcodeVerificationResponse => {
    const fallback: BarcodeVerificationResponse = {
      name: product.name,
      brand: product.metadata?.brand || '',
      origin: product.metadata?.origin || '',
      factory: {
        lat: product.metadata?.factory_lat ?? 34.6937,
        lng: product.metadata?.factory_lng ?? 135.5023,
        address: product.metadata?.factory_address ?? `${product.metadata?.brand ?? ''}, ${product.metadata?.origin ?? 'Japan'}`.trim()
      },
      batch_dna: product.metadata?.batch_dna ?? '',
      mfg_date: product.metadata?.mfg_date ?? null,
      expiry_date: product.metadata?.expiry_date ?? null,
      scans_24h: product.metadata?.scans_24h ?? 0,
      certificates: [],
      recent_scans: [],
      import_journey: [],
      notification_doc: product.metadata?.notification_doc,
      notification_no: product.metadata?.notification_no,
      notification_date: product.metadata?.notification_date
    };

    if (!verificationData) return fallback;
    return {
      ...fallback,
      ...verificationData,
      factory: { ...fallback.factory, ...(verificationData.factory || {}) },
      certificates: verificationData.certificates?.length ? verificationData.certificates : fallback.certificates,
      recent_scans: verificationData.recent_scans?.length ? verificationData.recent_scans : fallback.recent_scans,
      import_journey: verificationData.import_journey?.length ? verificationData.import_journey : fallback.import_journey
    };
  });

  let showDocModal = $state(false);

  function handleDownload() {
    if (!manufacturer.notification_doc) return;
    window.open(manufacturer.notification_doc, '_blank');
  }

  async function handleShare() {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Phiếu công bố - ${product.name}`,
          text: `Số tiếp nhận: ${manufacturer.notification_no}`,
          url: window.location.href
        });
      } catch (err) {
        logger.warn('Mobile share verification profile failed', err);
      }
    } else {
      try {
        await navigator.clipboard.writeText(window.location.href);
        ui.showToast('Đã sao chép liên kết!', 'success');
      } catch (err) {
        ui.showToast('Lỗi sao chép', 'error');
      }
    }
  }
  // Dynamic FOMO: derived from real scans_24h
  let concurrentViewers = $derived(Math.max(3, Math.min(50, Math.floor((manufacturer.scans_24h || 300) / 80))));
  let hotline = $derived(
    $page.data.shopInfo?.contact_info?.hotline ||
    $page.data.shopInfo?.contact?.hotline ||
    ''
  );
  let email = $derived(
    $page.data.shopInfo?.contact_info?.email ||
    $page.data.shopInfo?.contact?.email ||
    'info@osmo.vn'
  );
</script>

<div class="mobile-verification-center flex flex-col gap-3 p-0 select-none">
  
  <!-- 1. COMPACT FOMO BAR -->
  <div class="bg-red-500/10 border border-red-500/20 p-3 flex items-center justify-between relative overflow-hidden rounded-[5px]">
    <div class="absolute inset-0 bg-gradient-to-r from-red-500/0 via-red-500/5 to-red-500/0 w-[200%] animate-[shimmer_2s_infinite]"></div>
    <div class="flex items-center gap-2 relative z-10">
      <div class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.5)]"></div>
      <span class="text-[11px] font-bold text-red-400">🔥 <span class="text-white">{concurrentViewers}</span> người đang xem mã này</span>
    </div>
    <div class="flex items-center gap-1.5 bg-red-500/20 px-2 py-1 rounded-none border border-red-500/30 relative z-10">
      <Activity size={10} class="text-red-400" />
      <span class="text-[9px] font-black text-red-100">{manufacturer.scans_24h} quét/24h</span>
    </div>
  </div>

  <!-- 2. TRUTH HEADER (SLIM LUXURY) -->
  <div class="bg-blue-500/5 border border-white/5 p-4 flex items-center justify-between rounded-[5px] relative overflow-hidden">
    <div class="absolute -right-20 -top-20 w-40 h-40 bg-blue-500/10 blur-[40px] rounded-full pointer-events-none"></div>
    <div class="flex items-center gap-3 relative z-10">
      <div class="w-12 h-12 flex items-center justify-center relative">
        <img src="/01.Badge_52ad415e46.webp" alt="Verified Badge" width="48" height="48" class="w-full h-full object-contain drop-shadow-[0_0_10px_rgba(59,130,246,0.3)]" />
      </div>
      <div>
        <h2 class="text-xl font-black text-white tracking-tighter leading-none italic">Verified Osmo</h2>
        <p class="text-[9px] text-blue-300/60 font-bold mt-1.5 flex items-center gap-1">
          <Fingerprint size={10} /> Dữ liệu bảo mật tuyệt đối
        </p>
      </div>
    </div>
    <div class="text-right relative z-10">
      <p class="text-[8px] text-white/30 font-bold mb-1">Batch DNA</p>
      <p class="text-sm font-mono text-luxury-copper font-black tracking-tight">{manufacturer.batch_dna}</p>
    </div>
  </div>

  <!-- 3. RECENT SCAN (AUTO-UPDATE FEEL) -->
  {#if manufacturer.recent_scans?.length > 0}
    <div class="bg-blue-900/10 border border-blue-500/20 p-3 flex items-center gap-3 rounded-[5px] relative overflow-hidden">
      <div class="absolute inset-0 bg-blue-400/5 animate-pulse"></div>
      <div class="w-8 h-8 rounded-none bg-blue-500/20 border border-blue-500/40 flex items-center justify-center shrink-0 relative">
        <History size={14} class="text-blue-400" />
        <div class="absolute top-0 right-0 w-2 h-2 rounded-full bg-blue-400 animate-ping"></div>
      </div>
      <p class="text-[11px] text-white/80 leading-tight relative z-10">
        <span class="font-black text-white">{manufacturer.recent_scans[0].user}</span> vừa tra cứu chính hãng tại <span class="text-blue-400 font-bold">{manufacturer.recent_scans[0].location}</span>
        <span class="block text-[9px] text-white/40 mt-0.5">{manufacturer.recent_scans[0].time}</span>
      </p>
    </div>
  {/if}

  <!-- 4. LEGAL DOCS (TOP PRIORITY) -->
  <div class="glass-morphism-mobile p-4 overflow-hidden relative">
    <div class="corner-accents"></div>
    <div class="absolute -right-10 -bottom-10 opacity-5">
      <ShieldCheck size={120} class="text-blue-400" />
    </div>
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-[10px] font-black text-white/40 flex items-center gap-2">
        <Award size={12} class="text-blue-400" /> Hồ sơ pháp lý
      </h3>
      {#if manufacturer.notification_no}
        <div class="px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20">
          <span class="text-[7px] font-black text-blue-400">Official registration</span>
        </div>
      {/if}
    </div>

    <div class="flex flex-col gap-3">
      <div class="p-4 bg-gradient-to-br from-blue-900/20 to-black border border-blue-500/20 relative">
        <div class="mb-4">
          <p class="text-[8px] font-bold text-blue-400/80 mb-1">Số phiếu công bố</p>
          <p class="text-white text-lg font-black font-mono tracking-wider">{manufacturer.notification_no}</p>
        </div>
        
        <div class="grid grid-cols-2 gap-2 mb-4">
          <div class="p-2 bg-white/[0.02] border border-white/5">
            <p class="text-[7px] text-white/40 font-black mb-0.5">Ngày cấp</p>
            <p class="text-[10px] text-white font-bold">{manufacturer.notification_date}</p>
          </div>
          <div class="p-2 bg-white/[0.02] border border-white/5">
            <p class="text-[7px] text-white/40 font-black mb-0.5">Cơ quan</p>
            <p class="text-[10px] text-white font-bold">Cục QL Dược</p>
          </div>
        </div>

        {#if manufacturer.notification_doc}
          <button 
            onclick={() => showDocModal = true}
            class="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-3 font-black text-[9px] shadow-[0_5px_15px_rgba(59,130,246,0.3)] transition-all"
          >
            <Image size={14} /> Xem bản gốc
          </button>
        {/if}
      </div>
    </div>
  </div>

  <!-- 5. MANUFACTURING & FACTORY -->
  <div class="glass-morphism-mobile p-4 flex flex-col gap-4 relative">
    <div class="corner-accents"></div>
    <div class="flex items-center justify-between">
      <h3 class="text-[10px] font-black text-white/40 flex items-center gap-2">
        <MapPin size={12} class="text-luxury-copper" /> Nhà máy sản xuất
      </h3>
        <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-luxury-copper/10 border border-luxury-copper/20">
        <div class="w-1 h-1 rounded-full bg-luxury-copper animate-pulse"></div>
        <span class="text-[8px] font-black text-luxury-copper">{manufacturer.origin} Official site</span>
      </div>
    </div>

    <div class="h-40 bg-black/40 rounded-none relative overflow-hidden border border-white/10 group">
      <div class="absolute inset-0 bg-[url('https://www.google.com/maps/vt/pb=!1m4!1m3!1i12!2i3638!3i1622!2m3!1e0!2sm!3i605151527!3m8!2svi!3sUS!5e1105!12m4!1e68!2m2!1sset!2sRoadmap!4e0!5m1!5f2')] opacity-20 grayscale invert group-hover:scale-110 transition-transform duration-1000"></div>
      <div class="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent"></div>
      <div class="absolute -inset-[100%] bg-[conic-gradient(from_0deg_at_50%_50%,rgba(193,143,126,0)_0%,rgba(193,143,126,0.1)_25%,rgba(193,143,126,0)_50%)] animate-[spin_4s_linear_infinite]"></div>
      <div class="absolute top-0 left-0 w-full h-0.5 bg-luxury-copper/50 shadow-[0_0_15px_rgba(193,143,126,0.8)] z-20 animate-scan-map"></div>
      <div class="relative z-10 h-full flex flex-col items-center justify-center">
        <div class="relative">
          <div class="absolute -inset-4 bg-red-500/20 rounded-full blur-md animate-pulse"></div>
          <div class="w-4 h-4 bg-red-500 border-2 border-white rounded-full shadow-[0_0_20px_rgba(239,68,68,0.8)] relative z-10"></div>
        </div>
        <div class="mt-3 px-3 py-1 bg-black/80 backdrop-blur border border-white/10 rounded text-[8px] font-black text-white tracking-[0.2em] shadow-2xl">
          Verified location
        </div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-2">
      <div class="p-3 bg-white/[0.02] border border-white/5 col-span-2">
        <p class="text-[8px] font-bold text-white/30 mb-1">Đơn vị sản xuất</p>
        <p class="text-white text-xs font-black tracking-tight">{manufacturer.brand}</p>
      </div>
      <div class="p-3 bg-white/[0.02] border border-white/5">
        <p class="text-[8px] font-bold text-white/30 mb-1">Địa chỉ</p>
        <p class="text-white/60 text-[10px] leading-relaxed line-clamp-1">{manufacturer.factory?.address}</p>
      </div>
      {#if manufacturer.mfg_date}
      <div class="p-3 bg-white/[0.02] border border-white/5">
        <p class="text-[8px] font-bold text-white/30 mb-1">Ngày SX (MFG)</p>
        <p class="text-white/80 text-[10px] font-bold font-mono">{manufacturer.mfg_date}</p>
      </div>
      {/if}
      {#if manufacturer.expiry_date}
      <div class="p-3 bg-red-500/5 border border-red-500/10">
        <p class="text-[8px] font-bold text-white/30 mb-1">Hạn SD (EXP)</p>
        <p class="text-red-400 text-[10px] font-bold font-mono">{manufacturer.expiry_date}</p>
      </div>
      {/if}
    </div>
  </div>

  <!-- 6. LOGISTICS JOURNEY -->
  <div class="bg-white/[0.02] border border-white/5 p-4 rounded-[5px]">
    <h3 class="text-[10px] font-black text-white/40 mb-5 flex items-center gap-2">
      <Truck size={12} class="text-emerald-500" /> Lộ trình hàng hóa
    </h3>
    <div class="flex flex-col gap-0 pl-1">
      {#each manufacturer.import_journey as step, i}
        <div class="flex gap-4 group/step">
          <div class="flex flex-col items-center">
            <div class="w-2.5 h-2.5 rounded-full border-2 transition-colors duration-300 {step.status === 'Completed' ? 'bg-emerald-500 border-emerald-300 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-black border-white/20'}">
              {#if step.status === 'Active'}
                <div class="absolute w-2.5 h-2.5 rounded-full bg-luxury-copper animate-ping opacity-50"></div>
              {/if}
            </div>
            {#if i < manufacturer.import_journey.length - 1}
              <div class="w-px h-10 bg-white/10 transition-colors {step.status === 'Completed' ? 'bg-emerald-500/30' : ''}"></div>
            {/if}
          </div>
          <div class="flex-1 pb-5">
            <div class="flex justify-between items-start mb-0.5">
              <span class="text-[11px] font-bold text-white tracking-tight {step.status === 'Active' ? 'text-luxury-copper' : ''}">{step.step}</span>
              <span class="text-[9px] text-luxury-copper font-black bg-luxury-copper/10 px-1.5 py-0.5 rounded">{step.date}</span>
            </div>
            <p class="text-[10px] text-white/40 flex items-center gap-1">
              <MapPin size={8} /> {step.location}
            </p>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- 7. CERTIFICATES GRID -->
  <div class="grid grid-cols-2 gap-2">
    {#each manufacturer.certificates as cert}
      <div class="bg-white/[0.03] border border-white/5 p-3 flex items-center gap-3">
        <div class="w-7 h-7 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20 shrink-0">
          <Award size={12} class="text-blue-400" />
        </div>
        <div>
          <p class="text-[9px] font-bold text-white leading-tight line-clamp-1">{cert.name}</p>
          <p class="text-[7px] text-emerald-400 font-bold tracking-widest flex items-center gap-1">
            <CheckCircle size={8} /> {cert.status}
          </p>
        </div>
      </div>
    {/each}
  </div>

  <!-- FOOTER CHUYÊN NGHIỆP (ELITE V2.2) -->
  <div class="flex items-center justify-end mt-0 px-1 pb-1">
    <p class="text-right text-white/30 text-[8px] font-medium leading-none opacity-80">
      Tham khảo: <a href="mailto:{email}" class="hover:text-white/60">{email}</a>
      {#if hotline} <span class="mx-0.5 opacity-20">/</span> <a href="tel:{hotline.replace(/\D/g, '')}" class="hover:text-white/60">{hotline}</a>{/if}
    </p>
  </div>
</div>

<!-- LEGAL MODAL (ULTRA-LEAN EDITION) -->
{#if showDocModal}
  <div use:portal transition:fade={{duration: 200}} class="fixed inset-0 flex items-center justify-center p-0.5 bg-black/95 backdrop-blur-3xl" style:z-index={Z_INDEX_CLIENT.MODAL + 100} onclick={() => showDocModal = false}>
    <div transition:scale={{duration: 300, start: 0.95}} class="relative w-full h-full bg-[#0a0a0a] rounded-[5px] border border-white/10 overflow-hidden flex flex-col shadow-2xl" onclick={(e) => e.stopPropagation()}>
      
      <!-- Minimalist Pro Close Button (Extreme Corner) -->
      <button 
        class="absolute top-0 right-0 z-[50000] w-10 h-10 flex items-center justify-center text-black/30 active:text-black/80 active:bg-black/5 rounded-full transition-all duration-300"
        onclick={() => showDocModal = false}
        aria-label="Đóng modal"
      >
        <X size={20} strokeWidth={2} />
      </button>

      <div class="flex-1 overflow-y-auto custom-scrollbar bg-black">
        <div class="bg-[#e5e7eb] relative flex items-center justify-center p-0 overflow-hidden group min-h-[300px]">
          <div class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03] pointer-events-none mix-blend-multiply"></div>
          <img src={manufacturer.notification_doc} alt="Legal Doc" class="w-full h-auto drop-shadow-2xl relative z-10" />
          <div class="absolute inset-0 pointer-events-none flex items-center justify-center z-20 mix-blend-overlay opacity-5">
            <ShieldCheck size={200} class="text-blue-900" />
          </div>
        </div>

        <div class="bg-gradient-to-b from-[#111] to-black p-6 border-t border-white/5">
          <div class="mb-6">
            <h3 class="text-white font-black text-xl mb-1 tracking-tight">Thông tin pháp lý</h3>
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]"></div>
              <p class="text-white/40 text-[10px] font-medium italic">Tra cứu chính hãng bởi bộ y tế</p>
            </div>
          </div>

          <div class="space-y-3">
            <div class="p-4 bg-blue-500/5 border border-blue-500/10">
              <p class="text-[8px] text-blue-400/80 tracking-widest font-black mb-1">Số tiếp nhận</p>
              <p class="text-white font-mono font-bold text-base tracking-wider">{manufacturer.notification_no}</p>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div class="p-4 bg-white/[0.02] border border-white/5">
                <p class="text-[8px] text-white/40 font-black mb-1">Ngày cấp</p>
                <p class="text-white font-bold text-xs">{manufacturer.notification_date}</p>
              </div>
              <div class="p-4 bg-white/[0.02] border border-white/5">
                <p class="text-[8px] text-white/40 font-black mb-1">Cơ quan</p>
                <p class="text-white font-bold text-xs">Cục quản lý dược</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="p-4 bg-black border-t border-white/10 flex gap-2">
        <button 
          onclick={handleDownload}
          class="flex-1 bg-white/5 text-white py-3.5 text-[9px] font-black flex items-center justify-center gap-2"
        >
          <Download size={14} /> Tải xuống
        </button>
        <button 
          onclick={handleShare}
          class="flex-1 bg-blue-600 text-white py-3.5 text-[9px] font-black flex items-center justify-center gap-2 shadow-[0_5px_15px_rgba(59,130,246,0.3)]"
        >
          <Share2 size={14} /> Chia sẻ
        </button>
      </div>

    </div>
  </div>
{/if}

<style>
  .mobile-verification-center {
    font-family: var(--font-sans, sans-serif);
  }

  .glass-morphism-mobile {
    background: rgba(10, 10, 10, 0.4);
    backdrop-filter: blur(20px);
    border: none;
    border-radius: 0;
  }

  /* Industrial Reticle Accents */
  .corner-accents {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 20;
  }
  .corner-accents::before, .corner-accents::after {
    content: '';
    position: absolute;
    width: 15px;
    height: 15px;
    border-color: #C18F7E;
    border-style: solid;
    opacity: 0.8;
  }
  /* Top Left & Top Right */
  .corner-accents::before {
    top: 0; left: 0;
    border-width: 2px 0 0 2px;
  }
  /* Bottom Right & Bottom Left via container */
  .glass-morphism-mobile::before, .glass-morphism-mobile::after {
    content: '';
    position: absolute;
    width: 15px;
    height: 15px;
    border-color: #C18F7E;
    border-style: solid;
    opacity: 0.8;
    pointer-events: none;
    z-index: 20;
  }
  .glass-morphism-mobile::before {
    top: 0; right: 0;
    border-width: 2px 2px 0 0;
  }
  .glass-morphism-mobile::after {
    bottom: 0; left: 0;
    border-width: 0 0 2px 2px;
  }
  .corner-accents::after {
    bottom: 0; right: 0;
    border-width: 0 2px 2px 0;
  }

  @keyframes scan-map {
    0% { top: 0; opacity: 0; }
    20% { opacity: 1; }
    80% { opacity: 1; }
    100% { top: 100%; opacity: 0; }
  }

  .laser-scan-line-legal {
    position: absolute;
    left: 0;
    right: 0;
    height: 1px;
    background: #3b82f6;
    box-shadow: 0 0 10px #3b82f6, 0 0 20px #3b82f6;
    z-index: 100;
    animation: laser-scan-move 3s linear infinite;
  }

  @keyframes laser-scan-move {
    0% { top: 0; opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { top: 100%; opacity: 0; }
  }

  @keyframes shimmer {
    100% { transform: translateX(100%); }
  }

  .animate-scan-map {
    animation: scan-map 4s ease-in-out infinite;
  }

  .animate-scan {
    animation: scan 3s linear infinite;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 2px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
  }

  :global(.text-luxury-copper) {
    color: #C18F7E;
  }

  :global(.bg-luxury-copper) {
    background-color: #C18F7E;
  }
</style>
