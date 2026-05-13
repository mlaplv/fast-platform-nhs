<script lang="ts">
  import type { Category } from '$lib/types';
  import { fade } from 'svelte/transition';

  interface Props {
    categories: Category[];
    activeTab: number;
    onTabChange: (index: number) => void;
  }

  let { categories, activeTab, onTabChange }: Props = $props();

  // Elite V2.2: Combine "All" with real categories
  const tabs = $derived([
    { id: 'all', name: 'Tất cả', image: null },
    ...categories
  ]);

  // Broken image tracker for fallback
  let brokenImages = $state<Record<string, boolean>>({});
  function handleImgError(id: string) {
    brokenImages[id] = true;
  }
</script>

<div class="category-pills-wrapper">
  <div class="pills-scroll">
    {#each tabs as tab, i (tab.id)}
      <button 
        class="pill-item {activeTab === i ? 'active' : ''}"
        onclick={() => onTabChange(i)}
      >
        <div class="pill-content">
          <span class="pill-label">{tab.name}</span>
        </div>
        
        {#if activeTab === i}
          <div class="pill-indicator" in:fade={{ duration: 200 }}></div>
        {/if}
      </button>
    {/each}
  </div>
</div>

<style>
  .category-pills-wrapper {
    background: #FFFFFF;
    position: sticky;
    top: var(--mobile-header-total, 48px);
    z-index: var(--z-category-pills, 100);
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    width: 100%;
  }

  .pills-scroll {
    display: flex;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    padding: 4px 2px; /* Ép sát biên nhất có thể */
    gap: 4px; /* Thu hẹp khoảng cách giữa các nút */
    align-items: center;
  }
  .pills-scroll::-webkit-scrollbar { display: none; }

  .pill-item {
    position: relative;
    padding: 4px 12px; /* Giảm padding nội bộ nút */
    border: 1px solid rgba(0, 0, 0, 0.04);
    border-radius: 100px;
    background: #FFFFFF;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  }

  .pill-item.active {
    background: linear-gradient(135deg, #ee4d2d 0%, #ff6a00 100%);
    border-color: transparent;
    box-shadow: 0 4px 12px rgba(238, 77, 45, 0.2);
    transform: scale(1.02); /* Giảm độ scale để tránh đè các nút bên cạnh */
  }

  .pill-content {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .pill-label {
    font-size: 12px; /* Giảm font-size để gọn hơn */
    font-weight: 800;
    color: #444;
    white-space: nowrap;
    letter-spacing: -0.03em; /* Ép chữ khít hơn */
    transition: color 0.3s ease;
  }

  .pill-item.active .pill-label {
    color: #FFFFFF; /* Text trắng trên nền gradient */
    text-shadow: 0 1px 2px rgba(0,0,0,0.1);
  }

  /* Hiệu ứng tia sáng lướt qua (Viral Shimmer) */
  .pill-item.active::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 50%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: pill-shimmer 2s infinite;
  }

  @keyframes pill-shimmer {
    0% { left: -100%; }
    100% { left: 200%; }
  }

  .pill-indicator {
    display: none; /* Bỏ indicator cũ vì đã có background active nổi bật */
  }
</style>
