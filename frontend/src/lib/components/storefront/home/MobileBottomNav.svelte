<!-- MobileBottomNav.svelte -->
<!-- Safari iOS Liquid Glass Floating Nav (Elite V2.2) -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  import type { Product } from '$lib/types';

  interface Props {
    isProductMode?: boolean;
    product?: Product | null;
    onAddToCart?: () => void;
    onBuyNow?: () => void;
    onChatOpen?: () => void;
  }
  let { 
    isProductMode = false, 
    product = null,
    onAddToCart,
    onBuyNow,
    onChatOpen
  }: Props = $props();

  let isShrunk = $state(false);
  let lastScrollY = 0;

  onMount(() => {
    // Tìm trực tiếp scroller gốc của app (Dựa theo +page/layout config của mình) hoặc fallback về window
    const scroller = document.querySelector('.page-container') || window;

    const handleScroll = () => {
      // Đoán đúng vị trí cuộn trên cả Window hoặc Element
      const currentScrollY = scroller === window ? window.scrollY : (scroller as Element).scrollTop;
      
      // Chống nhạy (Debounce/Threshold logic) để trải nghiệm mượt mà không bị giật liên tục
      if (currentScrollY > lastScrollY + 10 && currentScrollY > 80) {
        if (!isShrunk) isShrunk = true;
        lastScrollY = currentScrollY;
      } else if (currentScrollY < lastScrollY - 10 || currentScrollY <= 80) {
        if (isShrunk) isShrunk = false;
        lastScrollY = currentScrollY;
      }
    };

    scroller.addEventListener('scroll', handleScroll, { passive: true });
    return () => scroller.removeEventListener('scroll', handleScroll);
  });
</script>

<nav class="tbn-nav {isShrunk ? 'tbn-nav--shrunk' : ''}" style="z-index: {Z_INDEX_CLIENT.MOBILE_TAB_BAR};">
  <div class="tbn-nav-inner">
    
    <!-- 0. Menu nhanh -->
    {#if !isProductMode}
      <button class="tbn-item" aria-label="Menu nhanh">
        <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <!-- Asymmetric Viral 2026 lines (Staggered effect) -->
          <path d="M4 7h16M9 12h11M4 17h16" />
        </svg>
        <span class="tbn-label">Menu</span>
      </button>
    {/if}

    <!-- 1. Hotline -->
    <button 
      class="tbn-item" 
      aria-label="Hotline"
      onclick={() => window.location.href = 'tel:0968123159'}
    >
      <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
      </svg>
      <span class="tbn-label">Hotline</span>
    </button>

    <!-- 2. AI Chat (Viral Magic Core) -->
    <button 
      class="tbn-item tbn-item--ai" 
      aria-label="AI Chat"
      onclick={() => onChatOpen?.()}
    >
      <div class="tbn-ai-tooltip">
        <span class="tbn-ai-tooltip-text">AI agentic hỗ trợ tư vấn chuyên sâu</span>
      </div>
      <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <defs>
          <linearGradient id="ai-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#25f4ee" />
            <stop offset="100%" stop-color="#fe2c55" />
          </linearGradient>
        </defs>
        <!-- Sparkle/Star shape with gradient stroke -->
        <path d="M12 2l2.4 5.6 5.6 2.4-5.6 2.4L12 18l-2.4-5.6-5.6-2.4 5.6-2.4L12 2z" stroke="url(#ai-grad)" fill="url(#ai-grad)" fill-opacity="0.2"/>
        <path d="M19 19l1.2 2.8 2.8 1.2-2.8 1.2L19 27l-1.2-2.8-2.8-1.2 2.8-1.2z" transform="scale(0.5) translate(22, 12)" stroke="url(#ai-grad)"/>
        <path d="M5 19l1.2 2.8 2.8 1.2-2.8 1.2L5 27l-1.2-2.8-2.8-1.2 2.8-1.2z" transform="scale(0.3) translate(0, 40)" stroke="url(#ai-grad)"/>
      </svg>
      <span class="tbn-label tbn-label--ai">AI Chat</span>
    </button>

    <!-- 3. Hành động mua (Vị trí cuối cùng) -->
    {#if isProductMode && product}
      <!-- Cụm Fused Capsule (Viral 2026 - Tối ưu vòng tròn lồng nhau) -->
      <div class="tbn-action-group">
        <!-- Nút Thêm vào giỏ (Nắp trái) -->
        <button 
          class="tbn-action-split tbn-action-split--cart" 
          aria-label="Thêm vào giỏ hàng"
          onclick={() => onAddToCart?.()}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
            <path d="M12 9h4M14 7v4" />
          </svg>
        </button>
 
        <!-- Nút Mua ngay (Thân chính) -->
        <button 
          class="tbn-action-split tbn-action-split--buy" 
          aria-label="Mua ngay"
          onclick={() => onBuyNow?.()}
        >
          <span class="buy-text">Mua ngay</span>
          <span class="buy-sub">
            {(product.discount_price || product.price).toLocaleString('vi-VN')}₫ | Freeship
          </span>
        </button>
      </div>
    {/if}

    {#if !isProductMode}
      <button class="tbn-item" aria-label="Tài khoản">
        <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        <span class="tbn-label">Tài khoản</span>
      </button>
    {/if}

  </div>
</nav>

<style>
  *, *::before, *::after {
    box-sizing: border-box;
  }

  /* Cấu trúc nổi (Floating Bar) kiểu Safari iOS */
  .tbn-nav {
    position: fixed;
    /* Căn giữa tuyệt đối với width ôm sát nội dung (hug contents) */
    bottom: max(env(safe-area-inset-bottom), 12px);
    left: 50%;
    translate: -50% 0;
    width: max-content;
    max-width: calc(100vw - 16px);
    height: 64px;
    
    /* Thiết kế Liquid Glass Premium chuẩn iOS Control Center */
    background: rgba(255, 255, 255, 0.98); /* Gần như đặc để không bị lẫn chữ nền */
    backdrop-filter: saturate(180%) blur(20px);
    -webkit-backdrop-filter: saturate(180%) blur(20px);
    border: 1px solid rgba(0, 0, 0, 0.05); /* Viền mảnh sẫm màu để tách khối */
    border-radius: 20px;
    box-shadow: 
      0 12px 40px rgba(0, 0, 0, 0.15), /* Bóng đậm hơn để nổi bật trên nền rác */
      0 2px 4px rgba(0,0,0,0.05);
    
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: visible; /* Cho phép tooltip bay ra ngoài */
    
    transform-origin: center bottom;
    transition: all 0.35s cubic-bezier(0.25, 1, 0.5, 1);
  }


  .tbn-nav-inner {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 0 6px;
  }

  /* State: Cuộn xuống (Shrunk) */
  .tbn-nav--shrunk {
    height: 48px;
    border-radius: 24px;
    /* translate để giữ căn giữa và add thêm offset Y */
    translate: -50% 4px;
    background: rgba(255, 255, 255, 0.6); /* Tăng độ đục để rõ hơn khi nhỏ */
  }

  /* Cấu hình các Nút con */
  .tbn-item {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    background: none;
    border: none;
    cursor: pointer;
    color: #444; 
    transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
    height: 100%;
    flex: 0 0 auto;
    padding: 0 14px;
    min-width: 64px;
  }

  .tbn-item:active {
    opacity: 0.6;
    transform: scale(0.95);
  }

  .tbn-icon {
    width: 22px;
    height: 22px;
    transition: transform 0.3s ease;
  }

  .tbn-label {
    font-size: 10px;
    font-weight: 700; /* Dày dặn tạo quyền lực */
    line-height: 1;
    white-space: nowrap;
    opacity: 1;
    transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
    transform-origin: top center;
  }

  /* Hiệu ứng khi thanh nav bị Shrink */
  .tbn-nav--shrunk .tbn-label {
    opacity: 0;
    height: 0;
    transform: scaleY(0);
    margin-top: 0;
  }
  
  .tbn-nav--shrunk .tbn-item {
    gap: 0;
    padding: 0 8px; /* Ép khoảng cách ngang nhỏ lại */
    min-width: 44px; /* Thu hẹp chiều ngang để bóp chật lại */
  }

  .tbn-nav--shrunk .tbn-nav-inner {
    gap: 0px; 
    padding: 0 6px;
  }

  .tbn-nav--shrunk .tbn-icon {
    transform: scale(1.1); /* Phóng lớn icon 1 chút bù lại phần text mất đi */
    color: #111; /* Đổi màu mượt mà */
  }

  /* ==================================================
     HỒNG TÂM AI CHAT - (THE NUCLEUS)
     ================================================== */
  .tbn-label--ai {
    /* Đổ chữ theo Gradient */
    background: linear-gradient(90deg, #25f4ee, #fe2c55);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800; /* Bớt nặng nề */
  }

  /* ==================================================
     HÀNH ĐỘNG MUA (FUSED CAPSULE - VIRAL 2026)
     Khắc phục lỗi thiết kế hình học (vòng tròn lồng nhau)
     ================================================== */
  .tbn-action-group {
    display: flex;
    flex: 1;
    height: 100%; /* Bám full mí trên và dưới của thanh Nav */
    margin-left: 8px; /* Tách khỏi AI Chat */
    margin-right: -6px; /* Bơm qua lớp đệm padding 6px để bám sát sạt mép phải */
    border-radius: 0 20px 20px 0; /* Bo cong khít với vỏ 20px bên phải, THẲNG TẮP (0px) bên trái */
    overflow: hidden; /* Cắt ghép nguyên khối */
    box-shadow: none; /* Bỏ bóng để chìm mượt vào viền Glass */
    border: none;
    background: transparent;
    transform: translateZ(0); /* Anti-aliasing cut corners */
  }

  /* Khớp viền hoàn hảo khi bị Shrink (Vỏ ngoài thu lại biến thành 24px) */
  .tbn-nav--shrunk .tbn-action-group {
    border-radius: 0 24px 24px 0;
  }

  .tbn-action-split {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: none;
    cursor: pointer;
    overflow: hidden;
  }

  /* Ink ripple effect */
  .tbn-action-split::after {
    content: '';
    position: absolute;
    inset: 0;
    background: currentColor;
    opacity: 0;
    transition: opacity 0.2s ease;
  }
  .tbn-action-split:active::after { opacity: 0.15; }

  /* Nắp trái (Add to cart) */
  .tbn-action-split--cart {
    width: 60px;
    background: transparent; /* Xóa bỏ nền theo yêu cầu Sếp */
    color: #ff1e4d;
    border-right: 1px dashed rgba(254, 44, 85, 0.15); /* Ranh giới xé vé (Ticket vibe) */
  }

  /* Thân chính (Buy Now) */
  .tbn-action-split--buy {
    flex: 1;
    background: linear-gradient(110deg, #ff1e4d 0%, #fe2c55 50%, #ff4b72 100%);
    color: white;
    padding: 0 16px;
  }

  .buy-text {
    font-size: 15px;
    font-weight: 800;
    line-height: 1.1;
    text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    letter-spacing: -0.2px;
  }

  .buy-sub {
    font-size: 10px;
    font-weight: 500;
    opacity: 0.95;
    letter-spacing: -0.1px;
  }

  /* TOOLTIP DYNAMIC GLASS (iOS 26 bright mode style) */
  .tbn-ai-tooltip {
    position: absolute;
    top: -46px;
    right: -8px; 
    /* Kính Sáng (Light Glass) chuẩn iOS */
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: saturate(200%) blur(30px);
    -webkit-backdrop-filter: saturate(200%) blur(30px);
    border: none;
    
    height: 28px;
    padding: 0 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    border-radius: 16px;
    white-space: nowrap;
    /* Drop-shadow ôm quanh toàn bộ body + mũi tên tạo thành 1 khối hợp nhất */
    filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.12));
    pointer-events: none;
    transition: all 0.35s cubic-bezier(0.25, 1, 0.5, 1);
    animation: floatTooltip 2.5s infinite ease-in-out;
  }

  /* Gradient Text phát sáng bên trong lớp kính */
  .tbn-ai-tooltip-text {
    background: linear-gradient(90deg, #25f4ee, #fe2c55);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 11px;
    font-weight: 800;
    line-height: 1; /* Khóa chiều cao chữ để Flex căn chuẩn */
    margin-top: 1px; /* Optical tuning bù phần râu chữ */
  }

  /* Mũi tên trỏ xuống liền khối bằng tam giác CSS (không đè lên nền trong) */
  .tbn-ai-tooltip::after {
    content: '';
    position: absolute;
    bottom: -6px; /* Tràn xuống đúng bằng chiều cao tam giác, không bị lẹm vào trong */
    right: 33px; /* Bù trừ một nửa độ rộng mũi tên (7px) để tâm mũi tên nằm đúng trọng tâm nút (40px) */
    border-width: 6px 7px 0;
    border-style: solid;
    /* Dùng đúng màu nền của Tooltip để nối liền 100% không chắp vá */
    border-color: rgba(255, 255, 255, 0.95) transparent transparent transparent;
  }

  @keyframes floatTooltip {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
  }

  /* Giấu tooltip cực mượt khi thu nhỏ Nav */
  .tbn-nav--shrunk .tbn-ai-tooltip {
    opacity: 0;
    transform: translateY(12px) scale(0.6);
  }
</style>
