<!-- MobileBottomNav.svelte -->
<!-- Safari iOS Liquid Glass Floating Nav (Elite V2.2) -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';

  let isShrunk = $state(false);
  let lastScrollY = 0;

  onMount(() => {
    // Tìm trực tiếp scroller gốc của app (Dựa theo +page/layout config của mình)
    const scroller = document.querySelector('.page-container');
    if (!scroller) return;

    const handleScroll = () => {
      const currentScrollY = scroller.scrollTop;
      
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
    <button class="tbn-item" aria-label="Menu nhanh">
      <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <!-- Asymmetric Viral 2026 lines (Staggered effect) -->
        <path d="M4 7h16M9 12h11M4 17h16" />
      </svg>
      <span class="tbn-label">Menu</span>
    </button>

    <!-- 1. Hotline -->
    <button class="tbn-item" aria-label="Hotline">
      <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
      </svg>
      <span class="tbn-label">Hotline</span>
    </button>

    <!-- 2. AI Chat (Viral Magic Core) -->
    <button class="tbn-item tbn-item--ai" aria-label="AI Chat">
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

    <!-- 3. Tài khoản -->
    <button class="tbn-item" aria-label="Tài khoản">
      <svg class="tbn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
      <span class="tbn-label">Tài khoản</span>
    </button>

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
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: saturate(250%) blur(40px);
    -webkit-backdrop-filter: saturate(250%) blur(40px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 20px;
    box-shadow: 
      inset 0 1px 1px rgba(255, 255, 255, 0.7), /* Viền sáng bên trong (Inner highlight) */
      0 8px 32px rgba(0, 0, 0, 0.08); /* Bóng nhạt tạo độ nổi */
    
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
