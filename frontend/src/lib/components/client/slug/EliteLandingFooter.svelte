<script lang="ts">
  import { onMount } from "svelte";
  import { fade, scale } from "svelte/transition";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import FileText from "@lucide/svelte/icons/file-text";
  import Scan from "@lucide/svelte/icons/scan";
  import Phone from "@lucide/svelte/icons/phone";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import Mail from "@lucide/svelte/icons/mail";
  import CheckCircle from "@lucide/svelte/icons/check-circle";
  import X from "@lucide/svelte/icons/x";
  import type { Product } from "$lib/types";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";

  interface Props {
    product: Product;
    onTriggerScan?: () => void;
  }

  let { product, onTriggerScan }: Props = $props();
  const clientUi = getClientUi();

  // State
  let showLegalModal = $state(false);

  // Dynamic values
  const metadata = $derived(product?.metadata || {});
  const barcode = $derived(
    product?.sku || (metadata.barcode as string) || "4968123159004",
  );
  const notificationNo = $derived(
    (metadata.notification_no as string) || "210454/23/CBMP-QLD",
  );
  const notificationDate = $derived(
    (metadata.notification_date as string) || "2023-08-29",
  );
  const authority = $derived(
    (metadata.authority as string) || "Cục Quản lý Dược",
  );
  const notificationDoc = $derived(
    (metadata.notification_doc as string) || "/doc-placeholder.jpg",
  );

  // Contact Info from global settings with strict typing
  const companyName = $derived(
    clientUi.settings?.contact_info?.company_name ||
      clientUi.settings?.name ||
      "HKD Văn Lập",
  );
  const hotline = $derived(
    clientUi.settings?.contact_info?.hotline ||
      clientUi.settings?.hotline ||
      "094990112",
  );
  const email = $derived(
    clientUi.settings?.contact_info?.email ||
      clientUi.settings?.email ||
      "contact@osmo.vn",
  );
  const address = $derived(
    clientUi.settings?.contact_info?.address ||
      clientUi.settings?.address ||
      "336/28/19 Nguyễn Văn Luông, Phú Lâm, HCM",
  );
  const taxId = $derived(
    clientUi.settings?.contact_info?.tax_id || clientUi.settings?.tax_id || "",
  );
  const businessLicense = $derived(
    clientUi.settings?.contact_info?.business_license ||
      clientUi.settings?.business_license ||
      "",
  );
</script>

<footer class="elite-minimalist-footer w-full bg-[#010101] pt-20 pb-20 relative overflow-hidden">
  
  <!-- Dải sóng công nghệ lượn sóng mạnh mẽ & tinh tế (Neon Tech Wave Line) -->
  <div class="absolute top-0 left-0 w-full overflow-hidden leading-[0] select-none pointer-events-none z-20">
    <svg viewBox="0 0 1440 100" preserveAspectRatio="none" class="relative block w-full h-[50px]">
      <defs>
        <!-- Dải màu gradient Rose Gold rực cháy phối hợp Ngọc lam hiện đại -->
        <linearGradient id="tech-wave-glow-grad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#FF3366" stop-opacity="0" />
          <stop offset="15%" stop-color="#FF3366" stop-opacity="0.1" />
          <stop offset="35%" stop-color="#FF5E36" stop-opacity="0.4" />
          <stop offset="50%" stop-color="#E2B1A2" stop-opacity="0.9" />
          <stop offset="65%" stop-color="#00c4a7" stop-opacity="0.4" />
          <stop offset="85%" stop-color="#00c4a7" stop-opacity="0.1" />
          <stop offset="100%" stop-color="#00c4a7" stop-opacity="0" />
        </linearGradient>
        <filter id="wave-neon-glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <!-- Sóng chỉ dẫn công nghệ mảnh mai sắc nét với hiệu ứng phát sáng (Tập hợp 3 dòng sóng nghệ thuật) -->
      <path
        d="M0,50 C180,85 360,15 540,65 C720,115 900,10 1080,75 C1260,140 1380,55 1440,50"
        fill="none"
        stroke="url(#tech-wave-glow-grad)"
        stroke-width="1.8"
        class="animate-wave-pulse"
        filter="url(#wave-neon-glow)"
      />
      <path
        d="M0,60 C200,95 380,25 560,75 C740,125 920,20 1100,85 C1280,150 1400,65 1440,60"
        fill="none"
        stroke="url(#tech-wave-glow-grad)"
        stroke-width="1"
        opacity="0.3"
        class="animate-wave-pulse"
        style="animation-delay: -1.5s;"
      />
      <path
        d="M0,40 C160,75 340,5 520,55 C700,105 880,0 1060,65 C1240,130 1360,45 1440,40"
        fill="none"
        stroke="url(#tech-wave-glow-grad)"
        stroke-width="0.8"
        opacity="0.15"
        class="animate-wave-pulse"
        style="animation-delay: -3s;"
      />
    </svg>
  </div>

  <div class="container mx-auto px-6 max-w-6xl relative z-10">
    <!-- KHỐI HÌNH BẦU ĐỘC BẢN HỢP NHẤT TẤT CẢ (Unified Oval Capsule Card) -->
    <div class="elite-capsule-card">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-stretch">
        
        <!-- PHÂN HỆ 1: PHÁP LÝ & SỐ PHIẾU CÔNG BỐ (4 CỘT) -->
        <div class="lg:col-span-4 flex flex-col justify-between gap-6">
          <div>
            <div class="flex items-center gap-2 mb-4">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 indicator-glow-emerald"></span>
              <span class="text-[10px] font-bold text-emerald-400 tracking-wider">Phiếu công bố</span>
            </div>

            <div class="flex items-center gap-1.5 mb-1">
              <ShieldCheck size={12} class="text-emerald-400/80" />
              <span class="text-white/40 text-[10px] font-medium">Mã số hồ sơ</span>
            </div>
            <div class="text-white text-base md:text-lg font-black tracking-wide mb-3 font-mono">
              {notificationNo}
            </div>

            <div class="grid grid-cols-2 gap-4 border-t border-white/5 pt-4">
              <div>
                <span class="text-white/40 text-[9px] font-medium">Ngày cấp</span>
                <span class="block text-white/80 text-xs font-bold font-mono mt-0.5">{notificationDate}</span>
              </div>
              <div>
                <span class="text-white/40 text-[9px] font-medium">Cơ quan</span>
                <span class="block text-white/80 text-xs font-bold mt-0.5 truncate">{authority}</span>
              </div>
            </div>
          </div>

          <button
            onclick={() => (showLegalModal = true)}
            class="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-bold tracking-wider transition-all duration-300 flex items-center justify-center gap-2 border border-blue-500/10"
          >
            <FileText size={12} class="animate-bounce" />
            <span>Xem tài liệu gốc</span>
          </button>
        </div>

        <!-- PHÂN HỆ 2: MÃ VẠCH & XÁC MINH NGUỒN GỐC (4 CỘT) -->
        <div class="lg:col-span-4 flex flex-col justify-between gap-6 lg:px-10 lg:border-x lg:border-white/5">
          <div>
            <div class="flex items-center gap-2 mb-4">
              <span class="w-1.5 h-1.5 rounded-full bg-blue-400 indicator-glow-blue"></span>
              <span class="text-[10px] font-bold text-blue-400 tracking-wider">Xác thực DNA</span>
            </div>

            <span class="text-white/40 text-[10px] font-medium">Mã vạch EAN toàn cầu</span>
            <div class="text-white text-base md:text-lg font-black tracking-widest mt-1 mb-2 font-mono">
              {barcode}
            </div>
            <p class="text-white/40 text-[10px] leading-relaxed font-light">
              Sản phẩm được dán nhãn DNA chống hàng giả. Hỗ trợ truy xuất nguồn gốc nhà máy tại Tokyo, Nhật Bản.
            </p>
          </div>

          <button
            onclick={onTriggerScan}
            class="scan-laser-btn w-full py-3 rounded-xl bg-emerald-950/30 hover:bg-emerald-950/50 border border-emerald-500/20 hover:border-emerald-500/40 text-emerald-400 text-[11px] font-bold tracking-wider transition-all duration-300 flex items-center justify-center gap-2"
          >
            <Scan size={12} class="text-emerald-400 animate-pulse" />
            <span>Kích hoạt quét nguồn gốc</span>
          </button>
        </div>

        <!-- PHÂN HỆ 3: ĐẠI DIỆN THƯƠNG HIỆU & LIÊN HỆ (4 CỘT) -->
        <div class="lg:col-span-4 flex flex-col justify-between gap-6">
          <div>
            <div class="flex items-center gap-2 mb-4">
              <span class="w-1.5 h-1.5 rounded-full bg-white/30 indicator-glow-white"></span>
              <span class="text-[10px] font-bold text-white/50 tracking-wider">Liên hệ</span>
            </div>

            <div class="flex flex-col gap-2.5 text-white/60 text-[10px] font-light">
              <div class="flex items-start gap-2">
                <MapPin size={12} class="text-[#E8D5B0] shrink-0 mt-0.5" />
                <span class="leading-relaxed">{address}</span>
              </div>
              <div class="flex items-center gap-2">
                <Phone size={12} class="text-[#C18F7E] shrink-0" />
                <span>Hotline: <strong class="font-mono text-white">{hotline}</strong></span>
              </div>
              <div class="flex items-center gap-2">
                <Mail size={12} class="text-[#E3B5A4] shrink-0" />
                <span>Email: <strong class="font-mono">{email}</strong></span>
              </div>
            </div>
          </div>

          <div class="border-t border-white/5 pt-3 mt-1 flex flex-col gap-1 text-white/30 text-[8px] font-light font-mono leading-relaxed">
            {#if taxId}
              <div>
                MST: <strong class="font-mono text-white/50">{taxId}</strong>
              </div>
            {/if}
            <div class="flex items-start gap-1">
              <span class="text-white/40 shrink-0">HKD VALA:</span>
              <span class="text-white/50">{businessLicense || "066082007605, do UBND Phường Phú Lâm cấp ngày 28/4/2026"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bản quyền cuối trang -->
    <div class="mt-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-white/20 text-[9px] font-light">
      <p>
        © 2026 {product.metadata?.seo_site_name ||
          clientUi.settings?.basic_info?.site_name ||
          "OSMO"}. All rights reserved.
      </p>
      <div class="flex items-center gap-2 grayscale opacity-40 hover:opacity-100 hover:grayscale-0 transition-all">
        <img
          src="/bocongthuong.png"
          alt="Bộ Công Thương"
          class="h-6 object-contain"
          onerror={(e) => {
            (e.currentTarget as HTMLImageElement).style.display = "none";
          }}
        />
        <span class="border border-white/10 px-2 py-0.5 rounded text-[8px] font-mono tracking-wider opacity-60">Secure SSL Encrypted</span>
      </div>
    </div>
  </div>
</footer>

<!-- MODAL POP-UP XEM TÀI LIỆU GỐC -->
{#if showLegalModal}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    transition:fade={{ duration: 200 }}
    class="fixed inset-0 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md z-[9999]"
    onclick={() => (showLegalModal = false)}
  >
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      transition:scale={{ duration: 300, start: 0.95 }}
      class="bg-[#0f0f0f] w-full max-w-lg p-6 rounded-2xl border border-white/10 shadow-2xl relative overflow-hidden"
      onclick={(e) => e.stopPropagation()}
    >
      <button
        class="absolute top-4 right-4 text-white/40 hover:text-white transition-all w-8 h-8 flex items-center justify-center hover:bg-white/5 rounded-full z-30"
        onclick={() => (showLegalModal = false)}
      >
        <X size={16} />
      </button>

      <div class="flex flex-col gap-4">
        <div class="flex items-center gap-2 text-emerald-400">
          <CheckCircle size={18} />
          <h3 class="text-white text-sm font-bold tracking-tight">
            Hồ sơ pháp lý chính thức
          </h3>
        </div>

        <p class="text-white/60 text-xs font-light leading-relaxed">
          Phiếu công bố sản phẩm mỹ phẩm số <strong>{notificationNo}</strong> được
          cấp bởi Cục Quản lý Dược - Bộ Y Tế.
        </p>

        <!-- Bản scan gốc làm hình nền của card để xác minh trực quan EEAT tuyệt đối -->
        <div 
          class="aspect-[3/4] w-full rounded-xl border border-white/10 overflow-hidden flex flex-col items-end justify-end p-6 relative bg-cover bg-center bg-no-repeat shadow-inner"
          style="background-image: url('{notificationDoc}');"
        >
          <!-- Gradient che phủ tinh xảo bảo vệ độ hiển thị của text -->
          <div class="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-transparent z-10"></div>

          <div class="absolute inset-x-0 bottom-0 p-5 z-20 text-center flex flex-col gap-1.5 bg-black/70 backdrop-blur-md border-t border-white/5">
            <span class="text-emerald-400 text-[10px] font-bold tracking-wider uppercase">Trạng thái: Hoạt động</span>
            <span class="text-white text-xs font-bold font-mono">{notificationNo}</span>
            <span class="text-white/40 text-[8px] font-mono">Ngày cấp: {notificationDate} • {authority}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .elite-capsule-card {
    border-radius: 40px 0 40px 0;
    background: rgba(1, 1, 1, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 3rem 2.8rem !important;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(20px);
    transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  }
  
  @media (min-width: 768px) {
    .elite-capsule-card {
      border-radius: 64px 0 64px 0;
      padding: 4rem 4.5rem !important;
    }
  }

  @media (min-width: 1024px) {
    .elite-capsule-card {
      border-radius: 120px 0 120px 0;
      padding: 4.5rem 6.5rem !important;
    }
  }

  .elite-capsule-card:hover {
    border-color: rgba(255, 255, 255, 0.08);
  }

  /* Holographic scan laser sweep effect for EAN button */
  .scan-laser-btn {
    position: relative;
    overflow: hidden;
  }
  .scan-laser-btn::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 60%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(16, 185, 129, 0.3),
      transparent
    );
    transform: skewX(-20deg);
  }
  .scan-laser-btn:hover::after {
    animation: laser-sweep 1.6s ease-in-out infinite;
  }
  @keyframes laser-sweep {
    0% { left: -100%; }
    100% { left: 160%; }
  }

  /* Glowing electronic pulse for status dots */
  .indicator-glow-emerald {
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
    animation: indicator-pulse 2s infinite alternate;
  }
  .indicator-glow-blue {
    box-shadow: 0 0 8px rgba(59, 130, 246, 0.6);
    animation: indicator-pulse 2s infinite alternate-reverse;
  }
  .indicator-glow-white {
    box-shadow: 0 0 6px rgba(255, 255, 255, 0.3);
  }
  @keyframes indicator-pulse {
    0% { transform: scale(0.85); opacity: 0.7; }
    100% { transform: scale(1.15); opacity: 1; }
  }

  @keyframes wave-pulse {
    0%,
    100% {
      opacity: 0.8;
      stroke-width: 1.5px;
    }
    50% {
      opacity: 1;
      stroke-width: 2.2px;
      filter: drop-shadow(0 0 5px rgba(226, 177, 162, 0.7));
    }
  }

  .animate-wave-pulse {
    animation: wave-pulse 4s ease-in-out infinite;
  }
</style>
