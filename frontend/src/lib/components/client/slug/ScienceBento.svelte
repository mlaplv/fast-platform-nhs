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
    headline: metadata.science_headline || '<span>PHÁ VỠ HẮC SẮC TỐ &</span><span>TÁI SINH LÀN DA SÁNG HỒNG</span>',
    subheadline: metadata.science_subheadline || '"Tinh chất dạng serum-kem mỏng nhẹ thẩm thấu tàng hình chỉ sau 3 giây. Can thiệp trực tiếp vào quá trình hình thành Melanin, làm sáng rạng rỡ các vùng da mỏng manh nhạy cảm nhất mà tuyệt đối không hề bết dính."',
    image: metadata.science_image || '/uploads/img/co--che.png',
    card1_title: metadata.science_card1_title || 'ĐÁNH BẬT THÂM SẠM TẬN GỐC',
    card1_desc: metadata.science_card1_desc || '"Sức mạnh từ chiết xuất Hoa Anh Đào (Sakura) chuẩn Nhật giúp ức chế mạnh mẽ Melanin. Xóa mờ các đốm nâu và vùng da xỉn màu do ma sát với trang phục hoặc tổn thương sau khi cạo, nhổ."',
    card2_title: metadata.science_card2_title || 'PHỤC HỒI & DƯỠNG DA MỀM MƯỚT',
    card2_desc: metadata.science_card2_desc || '"Tổ hợp Vitamin C, E cùng chiết xuất Lô hội giúp bơm đầy độ ẩm, làm dịu tức thì tình trạng sần sùi, thô ráp. Nuôi dưỡng bề mặt da mềm mịn như lụa, cảm giác luôn khô ráo và thoải mái suốt ngày dài."'
  });
</script>

<section id="science-mechanism" class="snap-session-standard science-section relative w-full overflow-hidden">
    <!-- 150px Coordinate Grid Overlay -->
    <div class="tech-grid opacity-30"></div>

    <div class="container mx-auto px-6 max-w-6xl text-center relative z-surface">
        
        <!-- SECTION HEADER (Normalized spacing to fix "thừa trên thiếu dưới") -->
        <header class="mb-8 md:mb-12 animate-reveal">
            <EditableWrapper path="metadata.science_headline" value={labels.headline} type="html" label="SỬA TIÊU ĐỀ">
                <h2 class="text-white font-black tracking-tight leading-none uppercase mb-6 text-3xl md:text-5xl lg:text-6xl mx-auto bento-headline">
                    {@html labels.headline}
                </h2>
            </EditableWrapper>

            <EditableWrapper path="metadata.science_subheadline" value={labels.subheadline} type="html" label="SỬA MÔ TẢ">
                <p class="section-description text-white/40 text-base md:text-lg max-w-none mx-auto leading-relaxed">
                    {@html labels.subheadline}
                </p>
            </EditableWrapper>
        </header>

        <!-- BENTO GRID (50/50 Split with perfectly uniform gaps) -->
        <div class="grid grid-cols-1 md:grid-cols-12 gap-5 items-stretch text-left">
            
            <!-- KHỐI TRÁI (FULL IMAGE - NO BORDERS) -->
            <div class="md:col-span-6 flex items-center mechanism-image-wrapper relative group overflow-hidden">
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

            <!-- KHỐI PHẢI (SUB BLOCKS) -->
            <div class="md:col-span-6 flex flex-col gap-5 h-full">
                <!-- Thẻ 1: BẺ GÃY CHUỖI AXIT BÉO -->
                <div class="flex-1 flex flex-col justify-center relative bg-slate-800/40 border border-slate-700/60 rounded-[5px] p-8 lg:p-10 backdrop-blur-md transition-all duration-500 hover:border-blue-500/40 group overflow-hidden">
                    <!-- Technical Wave Decoration -->
                    <div class="absolute bottom-[-10px] right-[-10px] w-48 h-48 opacity-20 pointer-events-none group-hover:opacity-40 transition-opacity duration-1000">
                        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" class="w-full h-full rotate-12">
                            <path fill="none" stroke="#3b82f6" stroke-width="2" d="M0,100 C20,150 40,50 60,100 C80,150 100,50 120,100 C140,150 160,50 180,100 C200,150 220,50 240,100" class="wave-path" />
                            <path fill="none" stroke="#60a5fa" stroke-width="1" d="M0,110 C20,160 40,60 60,110 C80,160 100,60 120,110 C140,160 160,60 180,110 C200,160 220,60 240,110" class="wave-path-delayed" />
                        </svg>
                    </div>

                    <EditableWrapper path="metadata.science_card1_title" value={labels.card1_title} label="SỬA TIÊU ĐỀ THẺ 1">
                        <h3 class="text-white text-lg lg:text-2xl font-black mb-3 tracking-tight uppercase transition-colors group-hover:text-blue-400">
                            {labels.card1_title}
                        </h3>
                    </EditableWrapper>
                    
                    <EditableWrapper path="metadata.science_card1_desc" value={labels.card1_desc} type="html" label="SỬA MÔ TẢ THẺ 1">
                        <p class="text-slate-500 text-xs lg:text-base leading-relaxed font-medium">
                            {labels.card1_desc}
                        </p>
                    </EditableWrapper>
                </div>

                <!-- Thẻ 2: TÁI TẠO & SE KHÍT NANG LÔNG -->
                <div class="flex-1 flex flex-col justify-center relative bg-slate-800/40 border border-slate-700/60 rounded-[5px] p-8 lg:p-10 backdrop-blur-md transition-all duration-500 hover:border-blue-500/40 group overflow-visible">
                    <!-- Technical Wave Decoration: Digital Pulse Variant -->
                    <div class="absolute bottom-[-15px] right-[-15px] w-56 h-56 opacity-20 pointer-events-none group-hover:opacity-40 transition-opacity duration-1000">
                        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" class="w-full h-full -rotate-12">
                            <path fill="none" stroke="#22c55e" stroke-width="2" d="M0,100 L40,100 L50,60 L70,140 L80,100 L120,100 L130,40 L150,160 L160,100 L200,100" class="wave-path" />
                            <path fill="none" stroke="#4ade80" stroke-width="1" d="M0,110 L40,110 L55,70 L75,150 L85,110 L125,110 L135,50 L155,170 L165,110 L200,110" class="wave-path-delayed" />
                        </svg>
                    </div>

                    <EditableWrapper path="metadata.science_card2_title" value={labels.card2_title} label="SỬA TIÊU ĐỀ THẺ 2">
                        <h3 class="text-white text-lg lg:text-2xl font-black mb-3 tracking-tight uppercase transition-colors group-hover:text-blue-400">
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

    <!-- Dynamic Line Wave Divider - High Impact Edition! -->
    <div class="wave-container">
        <svg viewBox="0 0 1440 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
            <defs>
                <linearGradient id="wave-gradient-science" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#3b82f6" stop-opacity="0" />
                    <stop offset="50%" stop-color="#22d3ee" stop-opacity="1" />
                    <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
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
