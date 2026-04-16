<script lang="ts">
  import { resolveMediaUrl } from '$lib/state/utils';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import "./ScienceBento.css";

  const shopStore = getShopStore();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);
  const metadata = $derived(product?.metadata || {});

  const labels = $derived({
    headline: metadata.science_headline || '<span>BÍ QUYẾT TÁI SINH</span><span>VÙNG DA SÁNG HỒNG QUYẾN RŨ</span>',
    subheadline: metadata.science_subheadline || '"Không chỉ đơn thuần là dưỡng da, Beppin Body thấu hiểu sự tinh tế của nàng. Tinh chất thẩm thấu sâu, giải quyết triệt để các đốm nâu cứng đầu nhất, trả lại sự mịn màng như lụa để bạn tự tin trong mọi khoảnh khắc."',
    image: metadata.science_image || '/uploads/img/co--che.png',
    card1_title: metadata.science_card1_title || 'TÁC ĐỘNG SÂU - HIỆU QUẢ NHANH',
    card1_desc: metadata.science_card1_desc || '"Công nghệ dẫn truyền Nano vượt trội giúp tinh chất Placenta Nhật Bản thẩm thấu sâu hơn 3 lần. Giai đoạn 1: Phá vỡ chuỗi melanin tối màu ngay dưới bề mặt biểu bì."',
    card2_title: metadata.science_card2_title || 'PHỤC HỒI & TRẺ HÓA TỨC THÌ',
    card2_desc: metadata.science_card2_desc || '"Tổ hợp Collagen cao cấp cùng Vitamin C tinh khiết giúp kích thích sản sinh tế bào mới. Không chỉ dưỡng trắng, chúng tôi còn kiến tạo bề mặt da mịn mướt, săn chắc và luôn khô thoáng."'
  });
</script>

<section id="science-mechanism" class="snap-session snap-session-standard science-section relative w-full overflow-hidden" style:padding-top="var(--standard-pt)">
    <!-- 150px Coordinate Grid Overlay -->
    <div class="tech-grid opacity-30"></div>

    <div class="container mx-auto px-6 max-w-6xl text-center relative z-surface">
        
        <EditableWrapper path="metadata.science_headline" value={labels.headline} type="html" label="SỬA TIÊU ĐỀ" class="w-full flex justify-center">
            <h2 class="elite-session-headline mb-10">
                {@html labels.headline}
            </h2>
        </EditableWrapper>

        <EditableWrapper path="metadata.science_subheadline" value={labels.subheadline} type="html" label="SỬA MÔ TẢ" class="w-full flex justify-center">
            <p class="section-description text-white/40 text-base md:text-lg max-w-3xl mx-auto leading-relaxed -mt-4 mb-12">
                {@html labels.subheadline}
            </p>
        </EditableWrapper>

        <!-- BENTO GRID (KINETIC ASYMMETRIC - Viral 2026) -->
        <div class="grid grid-cols-1 md:grid-cols-12 gap-10 items-stretch text-left">
            
            <!-- KHỐI TRÁI (DYNAMIC IMAGE SCANNER) -->
            <div class="md:col-span-7 flex items-center mechanism-image-wrapper relative group overflow-hidden rounded-[2rem] border border-white/5 bg-slate-900/10">
                <!-- Modern Scan Effect -->
                <div class="absolute inset-0 pointer-events-none" style="z-index: var(--z-content);">
                    <div class="scanner-line"></div>
                    <div class="scanner-glow"></div>
                </div>

                <EditableWrapper path="metadata.science_image" type="image" label="SỬA ẢNH CƠ CHẾ SINH HỌC">
                    <img 
                        src={resolveMediaUrl(labels.image)} 
                        alt="Cơ chế khoa học" 
                        class="w-full h-full object-contain rounded-[5px] transition-transform duration-700 group-hover:scale-105"
                    />
                </EditableWrapper>
            </div>

            <!-- KHỐI PHẢI (SUB BLOCKS - KINETIC STACK) -->
            <div class="md:col-span-5 flex flex-col gap-6 h-full">
                <!-- Thẻ 1 -->
                <div class="flex-1 flex flex-col justify-center relative bg-white/[0.01] border border-white/5 rounded-[2rem] p-10 backdrop-blur-3xl transition-all duration-700 hover:border-luxury-sakura/40 group overflow-hidden shadow-2xl">
                    <div class="absolute bottom-[-10px] right-[-10px] w-48 h-48 opacity-20 pointer-events-none group-hover:opacity-40 transition-opacity duration-1000">
                        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" class="w-full h-full rotate-12">
                            <path fill="none" stroke="#FFB7C5" stroke-width="2" d="M0,100 C20,150 40,50 60,100 C80,150 100,50 120,100 C140,150 160,50 180,100 C200,150 220,50 240,100" class="wave-path" />
                            <path fill="none" stroke="#E8D5B0" stroke-width="1" d="M0,110 C20,160 40,60 60,110 C80,160 100,60 120,110 C140,160 160,60 180,110 C200,160 220,60 240,110" class="wave-path-delayed" />
                        </svg>
                    </div>

                    <EditableWrapper path="metadata.science_card1_title" value={labels.card1_title} label="SỬA TIÊU ĐỀ THẺ 1">
                        <h3 class="text-white text-lg lg:text-2xl font-black mb-3 tracking-tight uppercase transition-colors group-hover:text-luxury-sakura">
                            {labels.card1_title}
                        </h3>
                    </EditableWrapper>
                    
                    <EditableWrapper path="metadata.science_card1_desc" value={labels.card1_desc} type="html" label="SỬA MÔ TẢ THẺ 1">
                        <p class="text-slate-500 text-xs lg:text-base leading-relaxed font-medium">
                            {labels.card1_desc}
                        </p>
                    </EditableWrapper>
                </div>

                <!-- Thẻ 2 -->
                <div class="flex-1 flex flex-col justify-center relative bg-white/[0.01] border border-white/5 rounded-[2rem] p-10 backdrop-blur-3xl transition-all duration-700 hover:border-luxury-gold/40 group overflow-visible shadow-2xl">
                    <div class="absolute bottom-[-15px] right-[-15px] w-56 h-56 opacity-20 pointer-events-none group-hover:opacity-40 transition-opacity duration-1000">
                        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" class="w-full h-full -rotate-12">
                            <path fill="none" stroke="#FFB7C5" stroke-width="2" d="M0,100 L40,100 L50,60 L70,140 L80,100 L120,100 L130,40 L150,160 L160,100 L200,100" class="wave-path" />
                            <path fill="none" stroke="#E3B5A4" stroke-width="1" d="M0,110 L40,110 L55,70 L75,150 L85,110 L125,110 L135,50 L155,170 L165,110 L200,110" class="wave-path-delayed" />
                        </svg>
                    </div>

                    <EditableWrapper path="metadata.science_card2_title" value={labels.card2_title} label="SỬA TIÊU ĐỀ THẺ 2">
                        <h3 class="text-white text-lg lg:text-2xl font-black mb-3 tracking-tight uppercase transition-colors group-hover:text-luxury-gold">
                            {labels.card2_title}
                        </h3>
                    </EditableWrapper>

                    <EditableWrapper path="metadata.science_card2_desc" value={labels.card2_desc} type="html" label="SỬA MÔ TẢ THẺ 2">
                        <p class="text-slate-500 text-xs lg:text-base leading-relaxed font-medium">
                            {labels.card2_desc}
                        </p>
                    </EditableWrapper>
                </div>
            </div>
        </div>
    </div>

    <!-- Dynamic Line Wave Divider -->
    <div class="wave-container">
        <svg viewBox="0 0 1440 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
            <defs>
                <linearGradient id="wave-gradient-science" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#FFB7C5" stop-opacity="0" />
                    <stop offset="50%" stop-color="#E8D5B0" stop-opacity="1" />
                    <stop offset="100%" stop-color="#FFB7C5" stop-opacity="0" />
                </linearGradient>
            </defs>
            <path class="wave-line opacity-20" d="M0,160 C320,300 420,20 720,160 C1020,300 1120,20 1440,160" />
            <path class="wave-line" d="M0,200 C320,340 420,60 720,200 C1020,340 1120,60 1440,200" />
            <path class="wave-line secondary" d="M0,240 C320,100 420,380 720,240 C1020,100 1120,380 1440,240" />
            <path class="wave-line opacity-30" d="M0,100 C320,240 420,-40 720,100 C1020,240 1120,-40 1440,100" />
        </svg>
    </div>

</section>

<style>
  .animate-reveal {
    animation: reveal 1s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  }
  @keyframes reveal {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* Resilience Logic: Force spans to behave like block rows if present */
  .bento-headline :global(span) {
    display: block;
    margin-bottom: 0.25rem;
  }
</style>
