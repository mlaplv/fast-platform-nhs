<script lang="ts">

  import { page } from '$app/stores';
  import { fade, scale, fly } from 'svelte/transition';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import Image from "@lucide/svelte/icons/image";
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
  import Zap from "@lucide/svelte/icons/zap";
  import Fingerprint from "@lucide/svelte/icons/fingerprint";

  import type { Product, BarcodeVerificationResponse } from '$lib/types';
  import { formatCurrency } from '$lib/utils/format';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  let { product, verificationData }: { 
    verificationData?: BarcodeVerificationResponse 
  } = $props();
 
  const ui = getClientUi();
 
  $effect(() => {
    if (verificationData) {
      console.log("🧬 [VerificationCenter] Glass UI reactive trigger - Data:", $state.snapshot(verificationData));
    }
  });

  // Elite V2.2: Real Data Integration (Derived from API response or Fallback)
  let manufacturer = $derived.by((): BarcodeVerificationResponse => {
    const fallback: BarcodeVerificationResponse = {
      name: product.name,
      brand: product.metadata?.brand ?? '',
      origin: product.metadata?.origin ?? '',
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
      notification_date: product.metadata?.notification_date,
      reward_label: 'Tra cứu chính hãng thành công',
      reward_sub: 'Sản phẩm chính ngạch được kiểm định bởi Osmo.'
    };

    if (!verificationData) return fallback;

    return {
      ...fallback,
      ...verificationData,
      factory: { ...fallback.factory, ...(verificationData.factory || {}) },
      certificates: verificationData.certificates?.length ? verificationData.certificates : fallback.certificates,
      recent_scans: verificationData.recent_scans?.length ? verificationData.recent_scans : fallback.recent_scans,
      import_journey: verificationData.import_journey?.length ? verificationData.import_journey : fallback.import_journey,
      is_estimated: !verificationData?.batch_dna 
    };
  });

  let recentScans = $derived(manufacturer.recent_scans || []);
  let journey = $derived(manufacturer.import_journey || []);
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
        // Silently fail if user cancels
      }
    } else {
      try {
        await navigator.clipboard.writeText(window.location.href);
        ui.showToast('Đã sao chép liên kết hồ sơ vào khay nhớ tạm', 'success');
      } catch (err) {
        ui.showToast('Không thể sao chép liên kết', 'error');
      }
    }
  }

  // Dynamic FOMO: derived from real scans_24h (avoids hardcode)
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

<div class="verification-center">
  <!-- FOMO NOTIFICATION BAR -->
  <div class="mb-2 bg-red-500/10 border border-red-500/20 rounded-none p-4 flex flex-col sm:flex-row items-center justify-between overflow-hidden relative group gap-3">
    <div class="absolute inset-0 bg-gradient-to-r from-red-500/0 via-red-500/10 to-red-500/0 w-[200%] animate-[shimmer_2s_infinite]"></div>
    <div class="flex items-center gap-3 relative z-10 w-full sm:w-auto justify-center sm:justify-start">
      <div class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.8)]"></div>
      <span class="text-sm font-bold text-red-400">🔥 Đang có <span class="text-white text-base">{concurrentViewers}</span> người cùng xem mã này</span>
    </div>
    <div class="flex items-center gap-2 bg-red-500/20 px-3 py-1.5 rounded-none border border-red-500/30 relative z-10">
      <Activity size={12} class="text-red-400" />
      <span class="text-[10px] font-black text-red-100">{manufacturer.scans_24h} quét/24h</span>
    </div>
  </div>

  <!-- TRUTH LAYER: VERIFICATION STATUS -->
  <div class="truth-header flex flex-col md:flex-row items-start md:items-center justify-between glass-morphism mb-2 gap-2 relative overflow-hidden">
    <div class="absolute -right-32 -top-32 w-96 h-96 bg-blue-500/10 blur-[80px] rounded-full pointer-events-none"></div>
    <div class="absolute -left-32 -bottom-32 w-96 h-96 bg-emerald-500/10 blur-[80px] rounded-full pointer-events-none"></div>
    
    <div class="flex items-center gap-2 relative z-10">
      <div class="w-16 h-16 rounded-none flex items-center justify-center relative group">
        <img src="/01.Badge_52ad415e46.webp" alt="Verified Badge" class="w-full h-full object-contain group-hover:scale-110 transition-transform drop-shadow-[0_0_15px_rgba(59,130,246,0.3)]" />
      </div>
      <div>
        <h2 class="text-3xl sm:text-4xl font-black text-white leading-none mb-2 drop-shadow-lg flex items-center gap-3">
          Verified <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">Osmo</span>
        </h2>
        <p class="text-[11px] text-blue-300/80 font-bold flex items-center gap-2">
          <ShieldCheck size={12} /> Dữ liệu bảo mật & tuyệt đối minh bạch
        </p>
      </div>
    </div>
    <div class="md:text-right relative z-10 w-full md:w-auto bg-black/40 md:bg-transparent p-4 md:p-0 rounded-none border md:border-0 border-white/5">
      <p class="text-[10px] text-white/40 font-bold mb-1 flex items-center md:justify-end gap-2">
        <Fingerprint size={12} /> Batch DNA
      </p>
      <p class="text-2xl font-mono text-luxury-copper font-black drop-shadow-[0_0_10px_rgba(193,143,126,0.3)]">{manufacturer.batch_dna}</p>
    </div>
  </div>

  {#if recentScans.length > 0}
  <div class="mb-4 flex items-center gap-4 overflow-hidden glass-morphism !rounded-none p-4 !bg-blue-900/10 !border-blue-500/20">
    <div class="relative flex items-center justify-center w-10 h-10 shrink-0 rounded-none bg-blue-500/20 border border-blue-500/40">
      <History size={16} class="text-blue-400" />
      <div class="absolute top-0 right-0 w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping"></div>
      <div class="absolute top-0 right-0 w-2.5 h-2.5 rounded-full bg-blue-500"></div>
    </div>
    <div class="flex-1 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2 text-sm text-white/80">
      <div><span class="font-black text-white">{recentScans[0].user}</span> vừa tra cứu chính hãng thành công</div>
      <div class="flex items-center gap-2 mt-1 sm:mt-0">
        <span class="text-blue-400 font-bold flex items-center gap-1"><MapPin size={12} /> {recentScans[0].location}</span>
        <span class="text-xs opacity-50 ml-auto sm:ml-2 bg-black/40 px-2 py-1 rounded-none shrink-0">{recentScans[0].time}</span>
      </div>
    </div>
  </div>
  {/if}

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-2">
    <!-- ROW 1: CORE TRUTH -->
    <div class="lg:col-span-3 grid grid-cols-1 lg:grid-cols-3 gap-2">
      <!-- PRODUCT IDENTITY -->
      <div class="glass-morphism p-4 sm:p-5 flex flex-col justify-between relative overflow-hidden group">
        <div class="corner-accents"></div>
        <div class="absolute -right-10 -top-10 w-40 h-40 bg-white/5 rounded-full blur-[30px] group-hover:bg-white/10 transition-colors"></div>
        <div>
          <div class="flex items-center justify-between mb-2 relative z-10">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-luxury-copper/20 flex items-center justify-center border border-luxury-copper/30">
                <PackageCheck size={16} class="text-luxury-copper" />
              </div>
              <span class="text-[10px] font-black text-white/60">Sản phẩm</span>
            </div>
            <div class="px-2 py-1 rounded bg-red-500/20 border border-red-500/30 flex items-center gap-1">
              <Zap size={10} class="text-red-400" />
              <span class="text-[9px] font-black text-red-400">Trending</span>
            </div>
          </div>
          <h3 class="text-2xl sm:text-3xl font-black text-white mb-4 leading-[1.1] line-clamp-3 relative z-10">{manufacturer.name}</h3>
        </div>
        <div class="p-4 rounded-none bg-gradient-to-r from-red-500/10 to-transparent border-l-2 border-red-500 relative z-10">
          <p class="text-[9px] text-white/40 font-black mb-1">Hạn sử dụng (EXP)</p>
          <div class="flex items-center gap-3">
            <Calendar size={16} class="text-red-400" />
            <p class="text-xl font-bold text-red-400 font-mono">{manufacturer.expiry_date}</p>
          </div>
        </div>
      </div>

      <!-- FACTORY & ORIGIN -->
      <div class="glass-morphism p-4 sm:p-5 lg:col-span-2 relative overflow-hidden">
        <div class="corner-accents"></div>
        <div class="flex items-center justify-between mb-2 relative z-10">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-luxury-copper/20 flex items-center justify-center border border-luxury-copper/30">
              <MapPin size={16} class="text-luxury-copper" />
            </div>
            <span class="text-[10px] font-black text-white/60">Nhà máy sản xuất</span>
          </div>
          <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-luxury-copper/10 border border-luxury-copper/20">
            <div class="w-1.5 h-1.5 rounded-full bg-luxury-copper animate-pulse"></div>
            <span class="text-[10px] font-black text-luxury-copper">{manufacturer.origin} Official site</span>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2 items-center relative z-10">
          <div class="h-40 bg-black/40 rounded-none relative overflow-hidden border border-white/10 group">
            <div class="absolute inset-0 bg-[url('https://www.google.com/maps/vt/pb=!1m4!1m3!1i12!2i3638!3i1622!2m3!1e0!2sm!3i605151527!3m8!2svi!3sUS!5e1105!12m4!1e68!2m2!1sset!2sRoadmap!4e0!5m1!5f2')] opacity-20 grayscale invert group-hover:scale-110 transition-transform duration-1000"></div>
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></div>
            <div class="absolute -inset-[100%] bg-[conic-gradient(from_0deg_at_50%_50%,rgba(193,143,126,0)_0%,rgba(193,143,126,0.1)_25%,rgba(193,143,126,0)_50%)] animate-[spin_4s_linear_infinite]"></div>
            
            <div class="relative z-10 h-full flex flex-col items-center justify-center">
              <div class="relative">
                <div class="absolute -inset-4 bg-red-500/20 rounded-full blur-md animate-pulse"></div>
                <div class="w-4 h-4 bg-red-500 border-2 border-white rounded-full shadow-[0_0_15px_rgba(239,68,68,0.8)] relative z-10"></div>
              </div>
              <div class="mt-2 px-2 py-0.5 bg-black/60 backdrop-blur border border-white/10 rounded text-[8px] font-bold text-white tracking-wider">
                Verified location
              </div>
            </div>
          </div>
          <div class="space-y-4">
            <div class="p-4 rounded-none bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-colors">
              <p class="text-[9px] font-bold text-white/30 mb-1.5">Đơn vị sản xuất</p>
              <p class="text-white text-lg font-black leading-tight">{manufacturer.brand || 'MICCOSMO Japan'}</p>
            </div>
            <div class="p-4 rounded-none bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-colors">
              <p class="text-[9px] font-bold text-white/30 mb-1.5">Địa chỉ</p>
              <p class="text-white/70 text-xs font-medium leading-relaxed">{manufacturer.factory?.address}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ROW 2: LOGISTICS & LEGAL -->
    <div class="lg:col-span-3 grid grid-cols-1 lg:grid-cols-3 gap-2">
      <!-- JOURNEY -->
      <div class="glass-morphism p-4 sm:p-5 lg:col-span-1 relative overflow-hidden group">
        <div class="corner-accents"></div>
        <div class="absolute -right-20 -bottom-20 w-40 h-40 bg-emerald-500/10 blur-[40px] rounded-full pointer-events-none transition-opacity group-hover:opacity-100 opacity-50"></div>
        <div class="flex items-center gap-3 mb-4 relative z-10">
          <div class="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
            <Truck size={16} class="text-emerald-400" />
          </div>
          <span class="text-[10px] font-black text-white/60">Lộ trình lô hàng</span>
        </div>
        <div class="space-y-5 relative pl-7 z-10">
          {#each journey as step, index}
            <div class="relative flex flex-col justify-start group/step">
              {#if index < journey.length - 1}
                <div class="absolute -left-[18px] top-4 w-[2px] h-[calc(100%+8px)] bg-white/5"></div>
              {/if}
              {#if step.status === 'Completed' && index < journey.length - 1}
                <div class="absolute -left-[18px] top-4 w-[2px] h-[calc(100%+8px)] bg-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.3)]"></div>
              {/if}
              
              <div class="absolute -left-6 top-1 w-3.5 h-3.5 rounded-full border-2 z-10 transition-colors duration-300 {step.status === 'Completed' ? 'bg-emerald-500 border-emerald-300 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-black border-white/20'}">
                {#if step.status === 'Active'}
                  <div class="absolute inset-0 rounded-full bg-luxury-copper animate-ping opacity-50"></div>
                  <div class="absolute inset-0 rounded-full bg-luxury-copper scale-50"></div>
                {/if}
              </div>
              <div class="flex justify-between items-start mb-1">
                <h4 class="text-white text-xs font-bold {step.status === 'Active' ? 'text-luxury-copper' : ''}">{step.step}</h4>
                <p class="text-luxury-copper text-[9px] font-black bg-luxury-copper/10 px-2 py-0.5 rounded ml-2">{step.date}</p>
              </div>
              <p class="text-white/40 text-[10px] font-medium flex items-center gap-1">
                <MapPin size={10} /> {step.location}
              </p>
            </div>
          {/each}
        </div>
      </div>

      <!-- LEGAL -->
      <div class="glass-morphism p-4 sm:p-5 lg:col-span-2 relative overflow-hidden">
        <div class="corner-accents"></div>
        <div class="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 blur-[50px] pointer-events-none"></div>
        <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-4 relative z-10">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
              <Award size={16} class="text-blue-400" />
            </div>
            <span class="text-[10px] font-black text-white/60">Hồ sơ pháp lý</span>
          </div>
          {#if manufacturer.notification_no}
            <div class="px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 flex items-center gap-2">
              <ShieldCheck size={12} class="text-blue-400" />
              <span class="text-[9px] font-black text-blue-400">Official registration</span>
            </div>
          {/if}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-5 gap-2 relative z-10">
          {#if manufacturer.notification_no}
            <div class="md:col-span-3 p-6 rounded-none bg-gradient-to-br from-blue-900/20 to-black border border-blue-500/20 relative overflow-hidden group">
              <div class="absolute -right-10 -bottom-10 opacity-5 group-hover:scale-110 group-hover:rotate-12 transition-transform duration-700">
                <ShieldCheck size={160} class="text-blue-400" />
              </div>
              <div class="relative z-10">
                <div class="mb-5">
                  <p class="text-[9px] font-bold text-blue-400/80 mb-1.5">Số phiếu công bố</p>
                  <p class="text-white text-xl font-black font-mono">{manufacturer.notification_no}</p>
                </div>
                
                <div class="flex items-center gap-2 mb-2 p-3 rounded-none bg-white/[0.02] border border-white/5">
                  <div>
                    <p class="text-[8px] text-white/40 font-black mb-1">Ngày cấp</p>
                    <p class="text-[11px] text-white/90 font-bold">{manufacturer.notification_date}</p>
                  </div>
                  <div class="w-[1px] h-8 bg-white/10"></div>
                  <div>
                    <p class="text-[8px] text-white/40 font-black mb-1">Cơ quan</p>
                    <p class="text-[11px] text-white/90 font-bold">Cục Quản lý Dược</p>
                  </div>
                </div>

                {#if manufacturer.notification_doc}
                  <button 
                    onclick={() => showDocModal = true}
                    class="w-full sm:w-auto flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-6 py-3.5 rounded-none transition-all shadow-[0_5px_20px_rgba(59,130,246,0.3)] hover:shadow-[0_8px_25px_rgba(59,130,246,0.5)] group/btn border border-blue-400/50"
                  >
                    <Image size={16} class="group-hover/btn:scale-110 transition-transform" />
                    <span class="text-[10px] font-black">Xem bản gốc</span>
                  </button>
                {/if}
              </div>
            </div>
          {/if}

          <div class="md:col-span-2 space-y-4">
            <p class="text-[9px] font-black text-white/30 px-2">Chứng nhận quốc tế</p>
            <div class="flex flex-col gap-3">
              {#each manufacturer.certificates as cert}
                <div class="flex items-center gap-4 p-4 rounded-none bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-colors group">
                  <div class="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20 group-hover:scale-110 transition-transform">
                    <Award size={16} class="text-blue-400" />
                  </div>
                  <div class="flex-1">
                    <span class="block text-[11px] font-bold text-white/90 mb-0.5 leading-tight">{cert.name}</span>
                    <span class="text-[9px] text-emerald-400 font-bold tracking-widest flex items-center gap-1">
                      <CheckCircle size={10} /> {cert.status}
                    </span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- FOOTER CHUYÊN NGHIỆP (ELITE V2.2) -->
  <div class="w-full flex justify-end mt-4 px-0">
    <p class="text-right text-white/30 text-[9px] font-medium leading-none opacity-80">
      Thông tin tham khảo: {email} {#if hotline} <span class="mx-1 opacity-20">/</span> {hotline}{/if}
    </p>
  </div>
</div>

{#if showDocModal}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div use:portal transition:fade={{duration: 200}} class="fixed inset-0 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl" style:z-index={Z_INDEX_CLIENT.MODAL + 100} onclick={() => showDocModal = false}>
    <div transition:scale={{duration: 300, start: 0.95}} class="relative max-w-5xl w-full h-auto max-h-[90vh] flex flex-col md:flex-row items-stretch bg-[#0a0a0a] border border-white/10 shadow-[0_20px_100px_rgba(0,0,0,1)] overflow-hidden rounded-[5px]" onclick={(e) => e.stopPropagation()}>
      
      <!-- CLOSE BUTTON (ELITE V2.2 PORTAL SYNC) -->
      <button 
        onclick={() => showDocModal = false}
        class="absolute top-0 right-0 w-8 h-8 flex items-center justify-center text-white/40 hover:text-white hover:bg-white/10 transition-all z-[100002] border-l border-b border-white/10 rounded-bl-[5px]"
      >
        <X size={18} />
      </button>

      <!-- Image Container -->
      <div class="flex-1 bg-[#e5e7eb] relative flex items-center justify-center p-4 md:p-8 overflow-hidden group/img">
        <!-- Pattern Overlay -->
        <div class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03] pointer-events-none mix-blend-multiply"></div>

        <img src={manufacturer.notification_doc} alt="Phiếu công bố" class="w-auto h-full max-h-[75vh] object-contain drop-shadow-2xl relative z-10" />

        <!-- Watermark Center -->
        <div class="absolute inset-0 pointer-events-none flex items-center justify-center z-20 mix-blend-overlay opacity-5">
          <ShieldCheck size={300} class="text-blue-900" />
        </div>

      </div>

      <!-- Sidebar / Info Panel -->
      <div class="w-full md:w-[340px] bg-gradient-to-b from-[#111] to-black border-l border-white/5 p-8 flex flex-col relative overflow-hidden">
          <!-- Background Glow -->
          <div class="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 blur-[80px] pointer-events-none"></div>
          
          <div class="mb-6 relative z-10">
            <h3 class="text-white font-black text-2xl mb-2 tracking-tight">Phiếu công bố</h3>
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(34,197,94,0.8)] animate-pulse"></div>
              <p class="text-white/40 text-[10px] font-bold italic">Tra cứu chính hãng bởi bộ y tế</p>
            </div>
          </div>

          <div class="space-y-4 mb-auto relative z-10">
            <div class="flex flex-col gap-1 p-4 rounded-none bg-blue-500/10 border border-blue-500/20 backdrop-blur-md">
              <div class="flex items-center gap-2 mb-2">
                <CheckCircle size={14} class="text-blue-400" />
                <p class="text-[9px] text-blue-400/80 font-black">Số tiếp nhận</p>
              </div>
              <p class="text-white font-mono font-bold text-base tracking-wider">{manufacturer.notification_no}</p>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="flex flex-col gap-1 p-4 rounded-none bg-white/[0.03] border border-white/5">
                <Calendar size={14} class="text-white/40 mb-2" />
                <p class="text-[9px] text-white/40 font-black">Ngày cấp</p>
                <p class="text-white font-bold text-sm">{manufacturer.notification_date}</p>
              </div>
              <div class="flex flex-col gap-1 p-4 rounded-none bg-white/[0.03] border border-white/5">
                <Award size={14} class="text-white/40 mb-2" />
                <p class="text-[9px] text-white/40 font-black">Cơ quan</p>
                <p class="text-white font-bold text-sm leading-tight">Cục quản lý dược</p>
              </div>
            </div>
          </div>

          <div class="mt-8 pt-6 border-t border-white/10 flex flex-col gap-3 relative z-10">
            <button 
              onclick={handleDownload}
              class="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-4 rounded-none font-black text-[11px] transition-all shadow-lg hover:-translate-y-0.5"
            >
              <Download size={14} /> Tải bản sao y
            </button>
            <button 
              onclick={handleShare}
              class="w-full flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 text-white py-4 rounded-none font-black text-[11px] transition-all border border-white/10"
            >
              <Share2 size={14} /> Chia sẻ hồ sơ
            </button>
          </div>
        </div>
    </div>
  </div>
{/if}

<style>
  .verification-center {
    font-family: var(--font-sans, sans-serif);
    color: #fff;
    width: 100%;
  }

  .glass-morphism {
    background: rgba(10, 10, 10, 0.6);
    backdrop-filter: blur(50px) saturate(200%);
    border: none;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
    border-radius: 0px;
    position: relative;
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
    width: 20px;
    height: 20px;
    border-color: #C18F7E;
    border-style: solid;
    opacity: 0.8;
  }
  .corner-accents::before {
    top: 0; left: 0;
    border-width: 2px 0 0 2px;
  }
  .glass-morphism::before, .glass-morphism::after {
    content: '';
    position: absolute;
    width: 20px;
    height: 20px;
    border-color: #C18F7E;
    border-style: solid;
    opacity: 0.8;
    pointer-events: none;
    z-index: 20;
  }
  .glass-morphism::before {
    top: 0; right: 0;
    border-width: 2px 2px 0 0;
  }
  .glass-morphism::after {
    bottom: 0; left: 0;
    border-width: 0 0 2px 2px;
  }
  .corner-accents::after {
    bottom: 0; right: 0;
    border-width: 0 2px 2px 0;
  }

  .truth-header {
    padding: 28px 32px;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(10, 10, 10, 0.9) 100%);
    border-bottom: 1px solid rgba(59, 130, 246, 0.2);
  }

  :global(.text-luxury-copper) {
    color: #C18F7E;
  }

  :global(.bg-luxury-copper) {
    background-color: #C18F7E;
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateY(20px); filter: blur(10px); }
    to { opacity: 1; transform: translateY(0); filter: blur(0); }
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

  .animate-scan {
    animation: scan 3s ease-in-out infinite;
  }

  @media (max-width: 1024px) {
    .verification-center {
      padding: 16px;
    }
  }
</style>
