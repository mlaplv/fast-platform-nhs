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
          {#if tab.image && !brokenImages[tab.id]}
            <img 
              src={tab.image} 
              alt={tab.name} 
              class="pill-icon"
              onerror={() => handleImgError(tab.id)}
            />
          {:else if tab.id !== 'all'}
            <div class="pill-icon-placeholder">
              <span>✨</span>
            </div>
          {/if}
          
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
    padding: 8px 12px;
    gap: 8px;
    align-items: center;
  }
  .pills-scroll::-webkit-scrollbar { display: none; }

  .pill-item {
    position: relative;
    padding: 6px 16px;
    border: 1px solid #F0F0F0;
    border-radius: 12px;
    background: #FAFAFA;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .pill-item.active {
    background: #FFFFFF;
    border-color: #C18F7E;
    box-shadow: 0 4px 12px rgba(193, 143, 126, 0.12);
    transform: scale(1.02);
  }

  .pill-content {
    display: flex;
    items-center: center;
    gap: 8px;
  }

  .pill-icon {
    width: 20px;
    height: 20px;
    object-fit: contain;
    border-radius: 4px;
  }

  .pill-icon-placeholder {
    width: 20px;
    height: 20px;
    background: #F5F5F5;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
  }

  .pill-label {
    font-size: 13px;
    font-weight: 700;
    color: #666;
    white-space: nowrap;
    letter-spacing: -0.01em;
  }

  .pill-item.active .pill-label {
    color: #C18F7E;
  }

  .pill-indicator {
    position: absolute;
    bottom: -8px;
    left: 20%;
    right: 20%;
    height: 3px;
    background: #C18F7E;
    border-radius: 10px 10px 0 0;
  }
</style>
