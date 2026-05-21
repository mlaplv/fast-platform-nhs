<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';

  interface Props {
    categories: Array<{ id: string; name: string; slug: string; image?: string; icon?: string }>;
  }
  let { categories }: Props = $props();
</script>

<div class="w-full pt-[15px] pb-6 overflow-hidden">
  <div class="flex flex-wrap justify-start items-start gap-x-8 md:gap-x-6 lg:gap-x-12 gap-y-8 px-2 md:px-0">
    {#each categories as category (category.id)}
      <button
        onclick={() => goto(`/${category.slug || slugify(category.name)}/`)}
        class="flex flex-col items-center justify-start w-[85px] md:w-[90px] lg:w-[100px] cursor-pointer group outline-none"
      >
        <!-- Elite Squircle Icon Container (Viral 2026) -->
        <div class="w-[50px] h-[50px] md:w-[60px] md:h-[60px] bg-white rounded-[20px] md:rounded-[24px] flex items-center justify-center border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.04)] transition-all duration-500 group-hover:-translate-y-2 group-hover:shadow-[0_12px_30px_rgba(193,143,126,0.15)] group-hover:border-[#C18F7E]/20 shrink-0 overflow-hidden relative">
          {#if category.image}
            <img 
              src={category.image} 
              alt={category.name} 
              class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
            />
          {:else}
            <div class="text-2xl md:text-3xl transition-transform duration-700 group-hover:scale-110 select-none opacity-80 group-hover:opacity-100">
              {category.icon || '✨'}
            </div>
          {/if}
          
          <!-- Liquid Glow Overlay -->
          <div class="absolute inset-0 bg-gradient-to-tr from-[#C18F7E]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
        </div>
        
        <!-- Premium Typography -->
        <span class="mt-4 text-[11px] md:text-[13px] font-bold text-gray-600 text-center leading-snug transition-colors duration-300 group-hover:text-[#C18F7E] w-full line-clamp-2 px-1 tracking-tight">
          {category.name}
        </span>
      </button>
    {/each}

    <!-- ── Viral Voucher Icon (Desktop Quick Menu) ── -->
    <a
      href="/khuyen-mai"
      id="desktop-quick-voucher"
      class="flex flex-col items-center justify-start w-[85px] md:w-[90px] lg:w-[100px] cursor-pointer group no-underline relative"
      aria-label="Mã Giảm Giá"
    >
      <div class="voucher-icon-wrap w-[50px] h-[50px] md:w-[60px] md:h-[60px] rounded-[20px] md:rounded-[24px] flex items-center justify-center shrink-0 relative">
        <!-- Animated background rings -->
        <span class="ring ring-1"></span>
        <span class="ring ring-2"></span>
        
        <!-- High-fidelity custom SVG Ticket from image design -->
        <svg class="w-[36px] h-[22px] md:w-[44px] md:h-[26px] select-none z-10 relative group-hover:scale-105 transition-transform duration-300" viewBox="0 0 46 26" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- White ticket scallop base -->
          <path d="M 6,0 C 6,3.3 3.3,6 0,6 L 0,20 C 3.3,20 6,22.7 6,26 L 40,26 C 40,22.7 42.7,20 46,20 L 46,6 C 42.7,6 40,3.3 40,0 Z" fill="#ffffff" />
          <!-- Dashed internal orange border -->
          <path d="M 8.5,2.5 C 8.5,5.8 5.8,8.5 2.5,8.5 L 2.5,17.5 C 5.8,17.5 8.5,20.2 8.5,23.5 L 37.5,23.5 C 37.5,20.2 40.2,17.5 43.5,17.5 L 43.5,8.5 C 40.2,8.5 37.5,5.8 37.5,2.5 Z" stroke="#EE4D2D" stroke-width="1.2" stroke-dasharray="2,2" fill="none" />
          <!-- VOUCHER bold orange text -->
          <text x="23" y="16.5" font-size="7.5" font-weight="900" fill="#EE4D2D" text-anchor="middle" letter-spacing="0.1" font-family="system-ui, -apple-system, sans-serif">VOUCHER</text>
        </svg>

        <!-- HOT badge -->
        <span class="hot-badge">HOT</span>
      </div>
      <span class="mt-4 text-[11px] md:text-[13px] font-bold text-[#EE4D2D] text-center leading-snug w-full line-clamp-2 px-1 tracking-tight">
        Mã Giảm Giá
      </span>
    </a>
  </div>
</div>

<style>
  /* Viral Voucher Icon — Desktop */
  .voucher-icon-wrap {
    background: #EE4D2D;
    border: 1.5px solid #EE4D2D;
    box-shadow: 0 4px 20px rgba(238, 77, 45, 0.15);
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
  }
  :global(#desktop-quick-voucher:hover) .voucher-icon-wrap {
    transform: translateY(-8px);
    box-shadow: 0 12px 32px rgba(238, 77, 45, 0.3);
    border-color: #ff6b35;
  }

  /* Pulse rings */
  .ring {
    position: absolute;
    border-radius: inherit;
    border: 1.5px solid #EE4D2D;
    opacity: 0;
    inset: 0;
    pointer-events: none;
    animation: ring-pulse 2.4s ease-out infinite;
  }
  .ring-2 { animation-delay: 0.8s; }

  @keyframes ring-pulse {
    0%   { opacity: 0.8; transform: scale(1); }
    100% { opacity: 0;   transform: scale(1.6); }
  }

  /* HOT badge */
  .hot-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: linear-gradient(135deg, #EE4D2D 0%, #FF6B35 100%);
    color: #fff;
    font-size: 8px;
    font-weight: 900;
    letter-spacing: 0.5px;
    padding: 2px 6px;
    border-radius: 6px;
    border: 1.5px solid #fff;
    box-shadow: 0 4px 10px rgba(238, 77, 45, 0.4);
    z-index: 100;
    animation: badge-bounce 1.5s ease-in-out infinite;
  }
  @keyframes badge-bounce {
    0%, 100% { transform: translateY(0) scale(1); }
    50%       { transform: translateY(-3px) scale(1.05); }
  }
</style>
