<script lang="ts">
  import type { Category } from '$lib/types';

  interface Palette {
    bg: string;
    text: string;
    shadow: string;
  }

  interface TabItem {
    label: string;
    slug?: string;
    isHot?: boolean;
    badgeText?: string;
    style: Palette;
  }

  interface Props {
    categories: Category[];
    activeTab: number;
    onTabChange: (index: number) => void;
  }

  let { categories, activeTab, onTabChange }: Props = $props();

  // High-authority "Viral 2026" palettes for standard items
  const palettes: Palette[] = [
    { bg: 'linear-gradient(135deg, #0cebeb, #20e3b2, #29ffc6)', text: '#004d40', shadow: '#20e3b2' }, // Neon Mint
    { bg: 'linear-gradient(135deg, #e0c3fc, #8ec5fc)', text: '#3c315b', shadow: '#8ec5fc' }, // Pastel Blue-Lilac
    { bg: 'linear-gradient(135deg, #ffd6a5, #ffadad)', text: '#800000', shadow: '#ffadad' }, // Soft Peach
    { bg: 'linear-gradient(135deg, #81ffef, #f067ff)', text: '#ffffff', shadow: '#81ffef' }, // Hyper Link
    { bg: 'linear-gradient(135deg, #bdb2ff, #7d2ae8)', text: '#ffffff', shadow: '#bdb2ff' }, // Violet
    { bg: 'linear-gradient(135deg, #60efff, #0061ff)', text: '#ffffff', shadow: '#0061ff' }, // Ocean
    { bg: 'linear-gradient(135deg, #ff2b54, #ff00c1)', text: '#ffffff', shadow: '#ff2b54' }  // Flashy Red
  ];

  // Strategic "Hot/Viral" palettes for 2026 conversion
  const hotPalettes: Palette[] = [
    { bg: 'linear-gradient(135deg, #fbda61, #ff5acd)', text: '#ffffff', shadow: '#fbda61' }, // Viral Pink-Gold
    { bg: 'linear-gradient(135deg, #81ffef, #f067ff)', text: '#ffffff', shadow: '#f067ff' }, // Electric Cyan-Magenta
    { bg: 'linear-gradient(135deg, #3a86ff, #4cc9f0)', text: '#ffffff', shadow: '#3a86ff' }, // Tech Blue
    { bg: 'linear-gradient(135deg, #ffbe0b, #fb5607)', text: '#ffffff', shadow: '#ffbe0b' }  // Mango Burst
  ];

  // Badge labels for variety to avoid "HOT" repetition
  const badgeLabels = ['HOT', 'TREND', 'NEW', 'TOP'];

  // Combine static Elite tabs with dynamic DB categories
  const tabs = $derived<TabItem[]>([
    { label: 'Tất cả', style: { bg: '#222', text: '#fff', shadow: '#222' } }, // Clean Black for "All"
    ...categories.map((cat, i) => {
      const nameLower = cat.name.toLowerCase();
      const isHot = nameLower.includes('kem dưỡng') || nameLower.includes('serum') || nameLower.includes('hot');
      
      let style: Palette;
      if (isHot) {
        // Rotate through hot palettes
        style = hotPalettes[i % hotPalettes.length];
      } else {
        style = palettes[i % palettes.length];
      }
        
      return { 
        label: cat.name, 
        slug: cat.slug,
        isHot,
        badgeText: isHot ? badgeLabels[i % badgeLabels.length] : undefined,
        style
      };
    })
  ]);
</script>

<div class="category-tabs-container">
  <div class="tabs-scroll">
    {#each tabs as tab, i}
      <button 
        class="tab-item {activeTab === i ? 'active' : ''}"
        onclick={() => onTabChange(i)}
      >
        <div class="tab-pill-wrap" style:background={tab.style.bg} style:box-shadow="0 4px 12px {tab.style.shadow}44">
          <span class="tab-pill" style:color={tab.style.text}>
            {tab.label}
          </span>
          {#if tab.isHot && tab.badgeText}
            <span class="hot-tag">{tab.badgeText}</span>
          {/if}
        </div>
        {#if activeTab === i}
          <div class="tab-indicator"></div>
        {/if}
      </button>
    {/each}
  </div>
</div>

<style>
  .category-tabs-container {
    background: #fff;
    padding: 2px 0 0; /* Minimized top padding */
    position: sticky;
    top: var(--mobile-header-total);
    z-index: 10;
    border-bottom: 1px solid #f0f0f0;
  }

  .tabs-scroll {
    display: flex;
    overflow-x: auto;
    overflow-y: visible; /* Ensure absolute children aren't clipped */
    scrollbar-width: none;
    -ms-overflow-style: none;
    gap: 8px;
    padding: 0 12px;
  }
  .tabs-scroll::-webkit-scrollbar { display: none; }

  .tab-item {
    position: relative;
    padding: 10px 2px 8px; /* Balanced padding */
    border: none;
    background: none;
    cursor: pointer;
    flex-shrink: 0;
    user-select: none;
  }

  .tab-pill-wrap {
    position: relative;
    padding: 6px 14px;
    border-radius: 12px;
    transition: transform 0.2s cubic-bezier(0.18, 0.89, 0.32, 1.28);
  }
  .tab-item.active .tab-pill-wrap {
    transform: scale(1.05);
  }

  .tab-pill {
    font-size: 13px;
    font-weight: 800;
    white-space: nowrap;
  }

  .hot-tag {
    position: absolute;
    top: -8px;
    right: -6px;
    background: #ff2b54;
    color: #fff;
    font-size: 8px;
    font-weight: 900;
    padding: 2px 5px;
    border-radius: 4px;
    box-shadow: 0 2px 6px rgba(255, 43, 84, 0.4);
    animation: hot-float 1s ease-in-out infinite alternate;
  }

  @keyframes hot-float {
    from { transform: translateY(0); }
    to { transform: translateY(-3px); }
  }

  .tab-indicator {
    position: absolute;
    bottom: 2px;
    left: 15%;
    right: 15%;
    height: 3px;
    background: #222;
    border-radius: 4px;
  }
</style>
