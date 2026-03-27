<script lang="ts">
  import { resolveMediaUrl } from '$lib/state/utils';
  
  let { product }: { product: any } = $props();
</script>

<section class="science-section py-32 bg-canvas border-t border-subtle">
  <div class="container mx-auto px-6 max-w-7xl">
    <div class="grid grid-cols-1 gap-6 auto-rows-[minmax(300px,auto)] bento-grid">
      <!-- Main Card -->
      <div class="bento-card bento-card--featured group bg-surface border border-subtle p-12 transition-all duration-500 overflow-hidden relative">
        <div class="relative z-10 h-full flex flex-col justify-end card-content">
           <h4 class="text-4xl font-black mb-6 leading-none tracking-tighter uppercase card-title">CÔNG NGHỆ <br/> NANO BẠC TỰ THÂN</h4>
           <p class="text-lg mb-10 max-w-md italic card-text">Thẩm thấu tuyệt đối, khóa chặt vùng mùi chỉ sau 3 giây.</p>
           <div class="flex flex-wrap gap-3 tag-cloud">
             {#each ['Không mùi', 'Không màu', 'Xịt sương mịn'] as tag}
              <span class="tag px-5 py-2.5 border border-white/10 rounded-full text-[10px] font-black uppercase tracking-widest">{tag}</span>
             {/each}
           </div>
        </div>
        <div class="absolute right-[-5%] bottom-[-5%] w-1/2 h-1/2 opacity-20 grayscale group-hover:scale-110 group-hover:grayscale-0 transition-all duration-[2s] card-image"
             style="background-image: url('{resolveMediaUrl(product.images?.[1] || product.images?.[0])}');"></div>
      </div>

      <!-- Stats Card -->
      <div class="bento-card bento-card--stats bg-surface border border-subtle p-12 transition-all duration-500 overflow-hidden relative flex flex-col justify-center text-center">
        <div class="text-7xl font-black mb-2 stat-value">48H</div>
        <p class="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 stat-label">Protection</p>
      </div>

      <!-- Icon Card -->
      <div class="bento-card bento-card--icon group bg-surface border border-subtle p-12 transition-all duration-500 overflow-hidden relative flex flex-col items-center justify-center text-center">
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl mb-8 icon-wrapper">🛡️</div>
        <span class="text-lg font-bold uppercase tracking-tight icon-label">An Toàn <br/> Tuyệt Đối</span>
      </div>

      <!-- Secondary Featured -->
      <div class="bento-card bento-card--wide group bg-surface border border-subtle p-12 transition-all duration-500 overflow-hidden relative flex items-center justify-between gap-12">
          <div class="flex-1">
             <h4 class="text-3xl font-black mb-6 uppercase tracking-tighter card-title-small">KHÔNG ĐỂ LẠI DẤU VẾT</h4>
             <p class="text-lg card-text">Tuyệt đối không vệt vàng hay bết dính trên áo sơ mi trắng.</p>
          </div>
          <div class="w-56 h-56 bg-cover rounded-[3rem] grayscale group-hover:grayscale-0 transition-all duration-700 border border-subtle side-image"
               style="background-image: url('{resolveMediaUrl(product.images?.[2] || product.images?.[0])}')"></div>
      </div>
    </div>
  </div>
</section>

<style lang="postcss">
  .science-section {
    container-type: inline-size;
    --card-radius: 4rem;
    --accent-glow: color-mix(in srgb, #60a5fa, transparent 90%);
  }

  .bento-card {
    border-radius: var(--card-radius);
  }

  .bento-card--featured {
    background-color: var(--accent-glow);
    border-color: rgba(59, 130, 246, 0.2);
  }

  .bento-card--icon:hover {
    border-color: var(--color-primary);
  }

  .bento-card--wide {
    min-height: 400px;
  }

  .card-text {
    color: var(--color-secondary);
  }

  .tag {
    background-color: rgba(2, 6, 23, 0.5); /* Hardcoded bg-canvas/50 */
  }

  .stat-value {
    color: var(--color-primary);
  }

  .icon-wrapper {
    background-color: var(--accent-glow);
  }

  .side-image {
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  }

  .card-image {
    background-size: contain;
    background-repeat: no-repeat;
  }

  @container (min-width: 768px) {
    .bento-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .bento-card--featured {
      grid-column: span 2 / span 2;
      grid-row: span 2 / span 2;
    }
    .bento-card--wide {
      grid-column: span 3 / span 3;
    }
  }

  @container (max-width: 900px) {
    .bento-card--wide {
      flex-direction: column;
      padding: 2rem;
    }
    .side-image {
      width: 100%;
      height: 12rem;
    }
    .card-image {
      opacity: 0.1;
    }
  }
</style>
