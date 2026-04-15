<!-- MobileServiceIcons.svelte -->
<!-- Quick service icons with horizontal slide and Elite 2.2 aesthetic -->
<script lang="ts">
  import { onMount } from 'svelte';

  interface Service {
    icon: string;
    label: string;
    badge?: string;
  }

  const services: Service[] = [
    { icon: '🤖', label: 'Chuyên gia hỗ trợ ai agentic', badge: 'NEW' },
    { icon: '🔥', label: 'Tham gia khuyến mãi sâu' },
    { icon: '🚛', label: 'Ưu đãi miễn phí vận chuyển' },
    { icon: '🎁', label: 'Cơn sốt quà tặng từ nhãn hàng' },
    { icon: '🛡️', label: 'Chính sách & quyền lợi bảo mật' },
  ];

  let scrollContainer: HTMLDivElement;
  let activeDot = $state(0);

  function handleScroll() {
    if (!scrollContainer) return;
    const { scrollLeft, scrollWidth, clientWidth } = scrollContainer;
    // Simple logic for 2 dots (standard mobile grid)
    activeDot = scrollLeft > (scrollWidth - clientWidth) / 3 ? 1 : 0;
  }

  onMount(() => {
    scrollContainer?.addEventListener('scroll', handleScroll, { passive: true });
    return () => scrollContainer?.removeEventListener('scroll', handleScroll);
  });
</script>

<div class="service-icons-wrap">
  <div 
    class="service-scroll-area" 
    bind:this={scrollContainer}
  >
    <div class="service-grid">
      {#each services as svc}
        <button class="service-item">
          <div class="service-icon-container">
            <div class="service-icon-bg">
              <span class="service-icon">{svc.icon}</span>
            </div>
            {#if svc.badge}
              <span class="service-badge">{svc.badge}</span>
            {/if}
          </div>
          <span class="service-label">{svc.label}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Slide dots indicator -->
  <div class="service-dots">
    <div class="service-dot {activeDot === 0 ? 'service-dot--active' : ''}"></div>
    <div class="service-dot {activeDot === 1 ? 'service-dot--active' : ''}"></div>
  </div>
</div>

<style>
  .service-icons-wrap {
    background: #ffffff;
    padding: 16px 0 12px;
    overflow: hidden;
  }

  .service-scroll-area {
    display: flex;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    scroll-snap-type: x mandatory;
    padding: 0 12px;
  }

  .service-scroll-area::-webkit-scrollbar {
    display: none;
  }

  .service-grid {
    display: grid;
    grid-auto-flow: column;
    /* Show roughly 4.5 items to hint at more */
    grid-template-columns: repeat(8, calc((100vw - 24px) / 4.8));
    gap: 8px;
  }

  .service-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px 0;
    scroll-snap-align: start;
  }

  .service-icon-container {
    position: relative;
    padding-top: 4px;
    padding-right: 4px;
  }

  .service-icon-bg {
    width: 44px;
    height: 44px;
    background: #FFF5F0;
    border-radius: 16px; /* Squircle style */
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s;
    box-shadow: 0 4px 12px rgba(238, 77, 45, 0.05);
  }

  .service-item:active .service-icon-bg {
    transform: scale(0.92);
  }

  .service-icon {
    font-size: 20px;
  }

  .service-badge {
    position: absolute;
    top: 0;
    right: 0;
    background: #C18F7E;
    color: #fff;
    font-size: 8px;
    font-weight: 950;
    padding: 2.5px 5px;
    border-radius: 5px;
    line-height: 1;
    border: 1.5px solid #fff;
    box-shadow: 0 4px 8px rgba(238, 77, 45, 0.2);
    z-index: 2;
  }

  .service-label {
    font-size: 10px;
    color: #333;
    font-weight: 550;
    text-align: center;
    line-height: 1.25;
    width: 100%;
    height: 2.5em; /* Fix height for 2 lines */
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .service-dots {
    display: flex;
    justify-content: center;
    gap: 5px;
    margin-top: 14px;
  }

  .service-dot {
    width: 5px;
    height: 3px;
    border-radius: 9999px;
    background: #efefef;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }

  .service-dot--active {
    width: 14px;
    background: #C18F7E;
  }
</style>
