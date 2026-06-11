<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  const ui = getClientUi();
  let status = $derived(page.status ?? 404);
  let message = $derived(page.error?.message ?? "Trang bạn đang tìm hiện không khả dụng.");

  let siteName = $derived(
    ui.settings?.basic_info?.site_name || 
    ui.settings?.name || 
    page.data?.shopInfo?.basic_info?.site_name || 
    page.data?.shopInfo?.name || 
    "SmartShop"
  );

  let isBackendDown = $derived(status === 503 || message.includes("Backend Connection Failed"));
</script>

<svelte:head>
  <title>{status} - {siteName} Error</title>
  <meta name="description" content="{status} - {message}" />
  <meta property="og:title" content="{status} - {siteName} Error" />
  <meta property="og:description" content="{message}" />
</svelte:head>

<div class="error-container">
  <!-- Dynamic Ambient Background -->
  <div class="ambient-glow"></div>

  <div class="glass-card">
    <div class="content">
      <div class="status-code">
        {status}
        <div class="glow-ring"></div>
      </div>

      <h1 class="title">
        {#if isBackendDown}
          Hệ thống đang bảo trì
        {:else if status === 404}
          Không tìm thấy trang
        {:else}
          Đã xảy ra lỗi
        {/if}
      </h1>

      <p class="description">
        {#if isBackendDown}
          Chúng tôi đang nâng cấp hệ thống để mang lại trải nghiệm tốt hơn. Quý khách vui lòng quay lại sau ít phút nữa nhé!
        {:else}
          {message}
        {/if}
      </p>

      <div class="actions">
        <button 
          class="btn-primary" 
          onclick={() => goto("/")}
        >
          Quay lại CỬA HÀNG
        </button>
        
        <button 
          class="btn-secondary"
          onclick={() => window.location.reload()}
        >
          THỬ TẢI LẠI TRANG
        </button>
      </div>

      <!-- Technical Hash for Support (Low profile) -->
      <div class="footer-info">
        <span class="hash-label">ID GIAO DỊCH:</span>
        <span class="hash-value">{Math.random().toString(36).substring(7).toUpperCase()}</span>
      </div>
    </div>
  </div>
</div>

<style>
  /* Liquid Glass V2.2 - Client Edition (VPS-Safe) */
  .error-container {
    --bg-deep: #020408;
    --accent-blue: #3b82f6;
    --text-main: #ffffff;
    --text-dim: rgba(255, 255, 255, 0.6);
    
    position: fixed;
    inset: 0;
    background-color: var(--bg-deep);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    color: var(--text-main);
    z-index: var(--z-fab);
    overflow: hidden;
  }

  .ambient-glow {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
    pointer-events: none;
  }

  .glass-card {
    position: relative;
    width: 100%;
    max-width: 480px;
    background: rgba(255, 255, 255, 0.03);
    /* Note: client.css disables backdrop-filter globally, so we rely on gradients */
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 32px;
    padding: 48px 32px;
    text-align: center;
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.4);
    animation: fadeIn 0.8s ease-out;
  }

  .status-code {
    position: relative;
    font-size: 10rem;
    font-weight: 200;
    line-height: 1;
    letter-spacing: -0.05em;
    color: var(--text-main);
    margin-bottom: 32px;
    display: inline-block;
  }

  .glow-ring {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 120%;
    height: 120%;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 80%);
    z-index: -1;
  }

  .title {
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 16px;
    letter-spacing: -0.02em;
  }

  .description {
    font-size: 1rem;
    line-height: 1.6;
    color: var(--text-dim);
    margin-bottom: 40px;
    max-width: 320px;
    margin-left: auto;
    margin-right: auto;
  }

  .actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .btn-primary {
    background: var(--accent-blue);
    color: white;
    border: none;
    padding: 16px 24px;
    border-radius: 16px;
    font-size: 0.875rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
  }

  .btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(59, 130, 246, 0.4);
    background: #4f91ff;
  }

  .btn-primary:active { transform: translateY(0); }

  .btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-main);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 16px 24px;
    border-radius: 16px;
    font-size: 0.875rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.3s ease;
  }

  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  .footer-info {
    margin-top: 48px;
    font-size: 0.65rem;
    font-family: monospace;
    letter-spacing: 0.1em;
    color: rgba(255, 255, 255, 0.2);
  }

  .hash-value { color: var(--accent-blue); opacity: 0.6; }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* Responsive Refinements */
  @media (max-width: 480px) {
    .glass-card { padding: 40px 24px; border-radius: 24px; }
    .status-code { font-size: 7rem; }
    .title { font-size: 1.5rem; }
  }
</style>
