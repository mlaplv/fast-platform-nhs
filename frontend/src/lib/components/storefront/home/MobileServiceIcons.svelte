<!-- MobileServiceIcons.svelte -->
<!-- Ultra-Lean Quick service icons with enhanced Viral FOMO -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { goto } from '$app/navigation';

  const ui = getClientUi();

  interface Service {
    icon: string;
    label: string;
    href: string;
    badge?: string;
    badgeColor?: string;
  }

  const services: Service[] = [
    { 
      icon: '🔥', 
      label: 'Kiếm tiền', 
      href: '/user/ctv',
      badge: '25%',
      badgeColor: '#c5a059'
    },
    { 
      icon: '💰', 
      label: 'Tích điểm', 
      href: '/user/loyalty',
      badge: 'X2',
      badgeColor: '#FF4D4F'
    },
    { 
      icon: '🎟️', 
      label: 'Kho voucher', 
      href: '/khuyen-mai',
      badge: 'HOT',
      badgeColor: '#EE4D2D'
    },
    { 
      icon: '👑', 
      label: 'Tài khoản', 
      href: '/user/profile' 
    },
    { 
      icon: '🛍️', 
      label: 'Đơn hàng', 
      href: '/user/purchase' 
    },
    { 
      icon: '🛡️', 
      label: '7 ngày đổi trả', 
      href: '/chinh-sach-doi-tra-hoan-tien.html',
      badge: 'PRO'
    },
    { 
      icon: '🚚', 
      label: 'Tra cứu đơn', 
      href: '/track' 
    },
    { 
      icon: '💡', 
      label: 'Hướng dẫn', 
      href: '/bai-viet' 
    },
  ];


  let scrollContainer: HTMLDivElement;

  onMount(() => {
    // Logic removed as dots are gone
  });
</script>

<div class="service-icons-wrap">
  <div 
    class="service-scroll-area" 
    bind:this={scrollContainer}
  >
    <div class="service-grid">
      {#each services as svc}
        <a 
          href={svc.href} 
          onclick={(e) => {
            if (svc.href === '/user/ctv' && !authStore.isAuthenticated) {
              e.preventDefault();
              ui.openLogin(() => {
                goto('/user/ctv');
              }, '/user/ctv');
            }
          }}
          class="service-item"
        >
          <div class="service-icon-container">
            <div class="service-icon-bg">
              <span class="service-icon">{svc.icon}</span>
            </div>
            {#if svc.badge}
              <span class="service-badge" style="background: {svc.badgeColor || '#C18F7E'}">{svc.badge}</span>
            {/if}
          </div>
          <span class="service-label">{svc.label}</span>
        </a>
      {/each}
    </div>
  </div>
</div>

<style>
  .service-icons-wrap {
    background: #ffffff;
    /* Ultra-Lean: Reduced bottom padding by another 50% */
    padding: 4px 0 2px;
    overflow: hidden;
  }

  .service-scroll-area {
    display: flex;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    scroll-snap-type: x mandatory;
    /* Ultra-Lean: Minimal 5px side padding */
    padding: 0 5px;
  }

  .service-scroll-area::-webkit-scrollbar {
    display: none;
  }

  .service-grid {
    display: flex;
    /* Reduced gap to 2px for ultra-tight spacing */
    gap: 2px;
    padding: 0 5px;
  }

  .service-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    /* Reduced gap to tighten vertical space */
    gap: 3px;
    text-decoration: none;
    cursor: pointer;
    /* Ultra-Lean: No bottom padding */
    padding: 6px 0 0;
    scroll-snap-align: start;
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .service-item:active {
    transform: scale(0.92);
  }

  .service-icon-container {
    position: relative;
    padding-top: 4px;
    padding-right: 4px;
  }

  .service-icon-bg {
    width: 38px;
    height: 38px;
    background: #FFF5F0;
    border-radius: 14px; /* Slightly smaller squircle */
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(238, 77, 45, 0.03);
    border: 1px solid rgba(238, 77, 45, 0.03);
  }

  .service-item:hover .service-icon-bg {
    background: #FFEBE0;
    transform: translateY(-2px);
  }

  .service-icon {
    font-size: 18px;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
  }

  .service-badge {
    position: absolute;
    top: 0;
    right: 0;
    color: #fff;
    font-size: 8px;
    font-weight: 950;
    padding: 2.5px 5px;
    border-radius: 5px;
    line-height: 1;
    border: 1.5px solid #fff;
    box-shadow: 0 4px 8px rgba(238, 77, 45, 0.2);
    z-index: 2;
    letter-spacing: 0.02em;
  }

  .service-label {
    font-size: 10px;
    color: #444;
    /* Not bold, lowercase only as requested */
    font-weight: 500;
    text-align: center;
    line-height: 1.1;
    width: 100%;
    height: 2.2em; 
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    /* Force 0 padding bottom as requested */
    padding-bottom: 0;
  }
</style>






