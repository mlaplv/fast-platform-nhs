<script lang="ts">
  import { resolveMediaUrl } from '$lib/state/utils';
  import type { Product } from '$lib/types';
  import "./ScienceBento.css";
  
  let { product }: { product: Product } = $props();
  let isViewerOpen = $state(false);

  const openViewer = (e: MouseEvent) => {
    e.stopPropagation();
    isViewerOpen = true;
  };
</script>

  <section id="science" class="science-viewport snap-session relative">

    <div class="science-container my-auto">
      <div class="mb-20 text-center">
        <h2 class="section-title text-center text-5xl font-black uppercase md:text-7xl">
          Cơ chế khoa học
        </h2>
        <p class="mt-4 text-sm tracking-[0.5em] text-white/30 uppercase">
          Công nghệ Nano Bạc Tự Thân độc bản từ Hồng Sơn.
        </p>
      </div>

      <div class="science-layout">
        
        <!-- LEFT: THE INNOVATION CORE -->
        <div class="column-left">
          
          <!-- 1. NANO CORE (Chamfered Glass) -->
          <div class="bento-tile glass-chamfer group">
            <div class="tile-content relative h-full" style:z-index="var(--z-surface)">
              <div class="hud-mono-label">HỆ THỐNG // LÕI NANO-BẠC</div>
              <div class="text-shield">
                <div class="shield-blob blob-1"></div>
                <div class="shield-blob blob-2"></div>
                <p class="text-xs leading-relaxed tracking-widest uppercase text-highlight-science">
                  Phá vỡ cấu trúc vi khuẩn gây mùi ngay lập tức bằng mạng lưới ion bạc tự kích hoạt.
                </p>
              </div>
            </div>
            <div class="capsule-visual" 
                 style="background-image: url('https://nhathuochongson.com/uploads/images/1-thanh-phan-nach-dy.jpg');">
            </div>
            <div class="laser-line"></div>
          </div>

          <!-- 2. MECHANISM (Horizon Sharp Glass) -->
          <div class="bento-tile glass-horizon group cursor-pointer relative" onclick={openViewer}>
            <div class="horizon-scroll-container absolute inset-0 overflow-hidden">
              <div class="horizon-slide-wrapper">
                <img src="https://nhathuochongson.com/uploads/images/co-che-n20_1587359851.jpg" alt="Mechanism" class="w-full h-auto" />
                <img src="https://nhathuochongson.com/uploads/images/co-che-n20_1587359851.jpg" alt="Mechanism" class="w-full h-auto" />
              </div>
            </div>
            
            <!-- MINIMALIST SCAN BUTTON -->
            <div class="absolute inset-x-0 bottom-12 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-700 translate-y-4 group-hover:translate-y-0" style:z-index="var(--z-layout-header)">
               <div class="hud-view-dot flex flex-col items-center gap-2">
                  <div class="w-12 h-12 rounded-full border border-white/20 backdrop-blur-xl flex items-center justify-center group/btn active:scale-95 transition-transform">
                     <svg class="w-5 h-5 text-emerald-400 group-hover/btn:scale-125 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                     </svg>
                  </div>
                  <div class="text-[8px] font-black tracking-[0.6em] text-emerald-400/50 uppercase">QUÉT_CHUYÊN_SÂU</div>
               </div>
            </div>

            <div class="tile-content absolute bottom-12 left-12" style:z-index="var(--z-surface)">
              <div class="hud-mono-label mb-0 opacity-50">QUY TRÌNH // PHÒNG NGỰ PHÂN TỬ</div>
            </div>
          </div>
        </div>

        <!-- RIGHT: THE TRUST SYSTEM -->
        <div class="column-right">
          
          <!-- 3. ADMISSION (Organic Blob) -->
          <div class="bento-tile glass-organic">
            <div class="tile-content">
              <div class="hud-mono-label opacity-20">KIỂM ĐỊNH // CHỨNG THỰC</div>
              <blockquote class="quote-master">
                "Chúng tôi không thể thay đổi gen hay cơ địa đặc trưng của bạn. <br/> Nhưng chúng tôi cam kết: Khóa mùi tuyệt đối, giữ bạn khô thoáng và tự tin suốt 48H."
              </blockquote>
            </div>
          </div>

          <!-- 4. STATS (Pill Island) -->
          <div class="bento-tile glass-island">
            <div class="stats-content text-center">
              <div class="flex items-baseline justify-center">
                <span class="stats-value-giant">48</span>
                <span class="stats-unit-cyan">H</span>
              </div>
              <div class="hud-mono-label mt-4 mb-0">PHÒNG NGỰ CHỦ ĐỘNG</div>
              <p class="mt-6 text-[10px] leading-relaxed tracking-widest text-white/30 uppercase">
                3s khô thoáng – Chạm đúng chân ái.<br/>
                Khóa mùi tuyệt đối, tự tin suốt ngày dài.
              </p>
            </div>
          </div>

          <!-- 5. GUARANTEE (Gem Cut Diamond) -->
          <div class="bento-tile glass-gem">
            <div class="guarantee-content">
              <div class="flex items-center gap-4 mb-4">
                <span class="text-3xl grayscale brightness-200">💎</span>
                <span class="hud-mono-label mb-0 text-white opacity-80 text-lg">BẢO CHỨNG</span>
              </div>
              <p class="text-sm leading-relaxed text-slate-400">
                Hoàn 100% trong 3 ngày. <br/> 
                <span class="text-cyan-400 font-bold tracking-widest">KHÔNG CẦN TRẢ VỎ</span>.
              </p>
            </div>
          </div>

        </div>

      </div>
    </div>

    <!-- FULL SCREEN IMAGE VIEWER (Ultra Premium) -->
    {#if isViewerOpen}
      <div
        class="fixed inset-0 flex items-center justify-center p-8 bg-[#020617]/90 backdrop-blur-3xl animate-in fade-in duration-700"
        style:z-index="var(--z-sticky-header)"
        onclick={() => isViewerOpen = false}
      >
        <button
          class="absolute top-12 right-12 text-white/40 hover:text-white transition-colors"
          style:z-index="var(--z-hud-service)"
          onclick={() => isViewerOpen = false}
        >
          <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div class="relative w-full max-w-5xl h-[85vh] rounded-[2rem] overflow-hidden border border-white/10 shadow-[0_50px_100px_rgba(0,0,0,0.8)] bg-[#020617] flex items-center justify-center">
           <div class="w-full h-full overflow-y-auto custom-scrollbar">
              <img src="https://nhathuochongson.com/uploads/images/co-che-n20_1587359851.jpg" alt="Mechanism Analysis" class="w-full h-auto block" />
           </div>
           <!-- OVERLAYS FOR VIEWER -->
           <div class="absolute inset-0 pointer-events-none ring-1 ring-inset ring-white/10 rounded-[2rem]"></div>
           <div class="absolute bottom-12 left-12 hud-mono-label opacity-100 text-emerald-400">PHÂN TÍCH // CHẾ ĐỘ: QUÉT TĨNH chuyên sâu // CHẤT LƯỢNG CAO</div>
        </div>
      </div>
    {/if}
  </section>
