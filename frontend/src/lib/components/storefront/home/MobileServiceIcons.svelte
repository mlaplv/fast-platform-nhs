<!-- MobileServiceIcons.svelte -->
<!-- Quick service icons: Voucher Xtra, Ưu đãi vận chuyển, Cơn sốt quà tặng, LIVE, Mall -->
<script lang="ts">
  interface Service {
    icon: string;
    label: string;
    badge?: string;
  }

  const services: Service[] = [
    { icon: '🏷️', label: 'Voucher Xtra' },
    { icon: '🚚', label: 'Ưu đãi vận chuyển' },
    { icon: '🎁', label: 'Cơn sốt quà tặng', badge: 'NEW' },
    { icon: '📺', label: 'Mua sắm qua LIVE' },
    { icon: '🛍️', label: 'TikTok Shop Mall' },
  ];
</script>

<div class="service-icons-wrap">
  <div class="service-icons-row">
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
  <!-- Slide dots indicator -->
  <div class="service-dots">
    <div class="service-dot service-dot--active"></div>
    <div class="service-dot"></div>
  </div>
</div>

<style>
  .service-icons-wrap {
    background: #ffffff;
    padding: 14px 12px 12px;
  }

  .service-icons-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
  }

  .service-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    width: 18%;
  }

  .service-icon-container {
    position: relative;
  }

  .service-icon-bg {
    width: 48px;
    height: 48px;
    background: #fff5f5;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .service-icon {
    font-size: 22px;
    line-height: 1;
  }

  .service-badge {
    position: absolute;
    top: -4px;
    right: -6px;
    background: #ee4d2d;
    color: #fff;
    font-size: 8px;
    font-weight: 900;
    padding: 1.5px 4px;
    border-radius: 3px;
    line-height: 1.2;
  }

  .service-label {
    font-size: 10px;
    color: #444;
    font-weight: 500;
    text-align: center;
    line-height: 1.3;
    width: 100%;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .service-dots {
    display: flex;
    justify-content: center;
    gap: 4px;
    margin-top: 10px;
  }

  .service-dot {
    width: 6px;
    height: 4px;
    border-radius: 9999px;
    background: #e0e0e0;
    transition: width 0.3s;
  }

  .service-dot--active {
    width: 16px;
    background: #ee4d2d;
  }
</style>
