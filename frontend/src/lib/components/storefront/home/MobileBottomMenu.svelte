<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import type { Product, Category } from '$lib/types';
  import { formatCurrency } from '$lib/utils/format';

  interface Props {
    isMenuOpen: boolean;
    toggleMenu: () => void;
    isLoadingCats: boolean;
    categoriesData: Category[];
    activeCategoryId: string | null;
    setActiveCategoryId: (id: string) => void;
    categoryProducts: Product[];
    getFallbackIcon: (name: string) => string;
    isImageUrl: (url: string | undefined) => boolean;
    brokenImages: Record<string, boolean>;
    handleImgError: (id: string) => void;
  }

  let { 
    isMenuOpen, toggleMenu, isLoadingCats, categoriesData, 
    activeCategoryId, setActiveCategoryId, categoryProducts, 
    getFallbackIcon, isImageUrl, brokenImages, handleImgError 
  }: Props = $props();

  const activeCategory = $derived(categoriesData.find(c => c.id === activeCategoryId));
</script>

{#if isMenuOpen}
  <button 
    class="tbn-bottom-sheet-overlay" 
    style="z-index: var(--z-mobile-bottom-sheet-overlay, 20000)"
    aria-label="Đóng menu"
    onclick={toggleMenu}
    in:fade={{ duration: 300 }} 
    out:fade={{ duration: 250 }}
  ></button>

  <div 
    class="tbn-bottom-sheet"
    style="z-index: var(--z-mobile-bottom-sheet, 20001)"
    in:fly={{ y: '100%', duration: 400, opacity: 1, easing: cubicOut }}
    out:fly={{ y: '100%', duration: 300, opacity: 1 }}
  >
     <div class="tbn-grab-handle-area" onclick={toggleMenu}>
        <div class="tbn-grab-handle"></div>
     </div>

     <div class="tbn-sheet-inner">
       <div class="tbn-sidebar">
          {#if isLoadingCats && categoriesData.length === 0}
             {#each Array(8) as _}
               <div class="tbn-skeleton-side"></div>
             {/each}
          {:else}
             {#each categoriesData as cat}
               <button 
                 class="tbn-cat-item {activeCategoryId === cat.id ? 'active' : ''}"
                 onclick={() => setActiveCategoryId(cat.id)}
               >
                 <div class="tbn-cat-icon-wrap">
                   {#if isImageUrl(cat.image || cat.thumbnail || cat.icon) && !brokenImages[cat.id]}
                     <img 
                       src={cat.image || cat.thumbnail || cat.icon} 
                       alt={cat.name} 
                       class="tbn-cat-img"
                       loading="lazy" 
                       onerror={() => handleImgError(cat.id)}
                     />
                   {:else if cat.icon && !isImageUrl(cat.icon)}
                      <div class="tbn-cat-placeholder">
                        <span class="tbn-cat-emoji">{cat.icon}</span>
                      </div>
                   {:else}
                     <div class="tbn-cat-placeholder">
                       <span class="tbn-cat-emoji">{getFallbackIcon(cat.name)}</span>
                     </div>
                   {/if}
                   {#if activeCategoryId === cat.id}<div class="tbn-cat-glow" in:fade></div>{/if}
                 </div>
                 <span class="tbn-cat-name">{cat.name}</span>
               </button>
             {/each}
          {/if}
       </div>

       <div class="tbn-content">
          <div class="tbn-content-header">
             <h3 class="tbn-content-title">{activeCategory?.name || 'Danh mục'}</h3>
             <a href={`/${activeCategory?.slug || ''}/`} onclick={toggleMenu} class="tbn-content-link group">
               <span>Xem tất cả</span>
               <ChevronRight class="w-3.5 h-3.5" />
             </a>
          </div>

          <div class="tbn-content-grid">
             {#if isLoadingCats && categoriesData.length === 0}
                {#each Array(9) as _}<div class="tbn-skeleton-card"></div>{/each}
             {:else}
                {#if activeCategory?.children && activeCategory.children.length > 0}
                  {#each activeCategory.children as child}
                    <a href={`/${child.slug}/`} onclick={toggleMenu} class="tbn-cat-card">
                      <div class="tbn-cat-img-wrapper">
                        {#if (child.image || child.thumbnail || child.icon) && !brokenImages[child.id]}
                          <img src={child.image || child.thumbnail || child.icon} alt={child.name} loading="lazy" onerror={() => handleImgError(child.id)} />
                        {:else}
                          <div class="tbn-cat-noimg text-xl">{getFallbackIcon(child.name)}</div>
                        {/if}
                      </div>
                      <span class="tbn-cat-title">{child.name}</span>
                    </a>
                  {/each}
                {:else if categoryProducts && categoryProducts.length > 0}
                  {#each categoryProducts as prod}
                    <a href={`/${prod.slug}`} onclick={toggleMenu} class="tbn-cat-card">
                      <div class="tbn-cat-img-wrapper">
                         {#if Array.isArray(prod.images) && prod.images.length > 0}
                           <img src={prod.images[0]} alt={prod.name} loading="lazy" />
                         {:else if prod.thumbnail || prod.image}
                           <img src={prod.thumbnail || prod.image} alt={prod.name} loading="lazy" />
                         {:else}
                           <div class="tbn-cat-noimg text-luxury-copper"><Sparkles class="w-5 h-5"/></div>
                         {/if}
                      </div>
                      <span class="tbn-cat-title text-left !font-bold pt-1">{prod.name}</span>
                      <span class="text-[10px] font-black text-luxury-copper mt-0.5">
                        {formatCurrency(prod.discountPrice || prod.discount_price || prod.price || 0)}
                      </span>
                    </a>
                  {/each}
                {:else}
                    <div class="tbn-cat-empty">
                       <Sparkles class="w-8 h-8 text-gray-200 mb-2" />
                       <p class="text-[10px] font-bold text-gray-400 tracking-widest">Đang cập nhật</p>
                    </div>
                {/if}
             {/if}
          </div>
       </div>
     </div>
  </div>
{/if}

<style>
  .tbn-bottom-sheet-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.6); border: none; cursor: default; }
  .tbn-bottom-sheet { position: fixed; bottom: 0; left: 0; right: 0; height: 88vh; background: #FFFFFF; border-radius: 32px 32px 0 0; box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.2); overflow: hidden; display: flex; flex-direction: column; }
  .tbn-grab-handle-area { width: 100%; height: 32px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; cursor: pointer; }
  .tbn-grab-handle { width: 36px; height: 4px; background: #E5E5E5; border-radius: 2px; }
  .tbn-sheet-inner { display: flex; flex: 1; width: 100%; overflow: hidden; }
  .tbn-sidebar { width: 90px; flex-shrink: 0; height: 100%; overflow-y: auto; background: #F9F9F9; padding-bottom: 40px; scrollbar-width: none; }
  .tbn-cat-item { display: flex; flex-direction: column; align-items: center; padding: 12px 6px; gap: 6px; width: 100%; border: none; background: transparent; }
  .tbn-cat-item.active { background: #FFFFFF; position: relative; }
  .tbn-cat-item.active::before { content: ''; position: absolute; left: 0; top: 20%; bottom: 20%; width: 3px; background: #C18F7E; border-radius: 0 4px 4px 0; }
  .tbn-cat-icon-wrap { position: relative; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; z-index: 1; }
  .tbn-cat-img { width: 100%; height: 100%; object-fit: cover; border-radius: 14px; border: 0.5px solid rgba(193, 143, 126, 0.1); }
  .tbn-cat-placeholder { width: 100%; height: 100%; background: linear-gradient(135deg, #FDFBFB 0%, #EBEDEE 100%); border-radius: 14px; display: flex; align-items: center; justify-content: center; }
  .tbn-cat-emoji { font-size: 20px; }
  .tbn-cat-glow { position: absolute; inset: -4px; background: radial-gradient(circle, rgba(193, 143, 126, 0.25) 0%, transparent 70%); border-radius: 20px; animation: cat-pulse 2s infinite; }
  @keyframes cat-pulse { 0%, 100% { opacity: 0.5; transform: scale(1); } 50% { opacity: 1; transform: scale(1.1); } }
  .tbn-cat-name { font-size: 10px; font-weight: 600; color: #666; text-align: center; line-height: 1.2; }
  .tbn-cat-item.active .tbn-cat-name { color: #C18F7E; }
  .tbn-content { flex: 1; overflow-y: auto; padding: 20px 16px 140px 16px; background: #FFFFFF; scrollbar-width: none; }
  .tbn-content-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
  .tbn-content-title { font-size: 14px; font-weight: 900; color: #111; }
  .tbn-content-link { font-size: 11px; font-weight: 800; color: #c18f7e; display: flex; align-items: center; gap: 4px; }
  .tbn-content-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px 12px; }
  .tbn-cat-card { display: flex; flex-direction: column; align-items: center; gap: 8px; text-decoration: none; }
  .tbn-cat-img-wrapper { width: 100%; aspect-ratio: 1; border-radius: 16px; overflow: hidden; background: #F5F5F5; border: 1px solid #F0F0F0; }
  .tbn-cat-img-wrapper img { width: 100%; height: 100%; object-fit: cover; }
  .tbn-cat-noimg { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
  .tbn-cat-title { font-size: 10px; font-weight: 700; color: #333; line-height: 1.3; text-align: center; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .tbn-skeleton-side { width: 60px; height: 60px; margin: 10px auto; border-radius: 12px; background: #F0F0F0; animation: pulse 1.5s infinite; }
  .tbn-skeleton-card { width: 100%; aspect-ratio: 1; border-radius: 16px; background: #F5F5F5; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%, 100% { opacity: 0.8; } 50% { opacity: 0.4; } }
  .tbn-cat-empty { width: 100%; grid-column: span 3; display: flex; flex-direction: column; align-items: center; padding: 40px 0; }
</style>
