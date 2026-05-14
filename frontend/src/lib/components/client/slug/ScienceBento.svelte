<script lang="ts">
  import { resolveMediaUrl } from '$lib/state/utils';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import { scale } from 'svelte/transition';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import HelpCircle from "@lucide/svelte/icons/help-circle";
import X from "@lucide/svelte/icons/x";
  import "./ScienceBento.css";

  const shopStore = getShopStore();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);
  const metadata = $derived(product?.metadata || {});

  const stripTags = (h: string) => h ? h.replace(/<[^>]*>?/gm, '').trim() : '';
  const legacyParts = $derived(metadata.science_headline?.split('</span><span>') || []);
  const h1 = $derived(metadata.science_headline_1 || stripTags(legacyParts[0]) || "CƠ CHẾ KHOA HỌC");
  const h2 = $derived(metadata.science_headline_2 || stripTags(legacyParts[1]) || "Miccosmo Beppin Body Virgin White Serum");

  const labels = $derived({
    subheadline: metadata.science_subheadline || '"Không chỉ đơn thuần là dưỡng da, Beppin Body thấu hiểu sự tinh tế của nàng. Tinh chất thẩm thấu sâu, giải quyết triệt để các đốm nâu cứng đầu nhất, trả lại sự mịn màng như lụa để bạn tự tin trong mọi khoảnh khắc."',
    image: metadata.science_image || '/uploads/img/co--che.webp',
    card1_title: metadata.science_card1_title || 'TÁC ĐỘNG SÂU - HIỆU QUẢ NHANH',
    card1_desc: metadata.science_card1_desc || '"Công nghệ dẫn truyền Nano vượt trội giúp tinh chất Placenta Nhật Bản thẩm thấu sâu hơn 3 lần. Giai đoạn 1: Phá vỡ chuỗi melanin tối màu ngay dưới bề mặt biểu bì."',
    card2_title: metadata.science_card2_title || 'PHỤC HỒI & TRẺ HÓA TỨC THÌ',
    card2_desc: metadata.science_card2_desc || '"Tổ hợp Collagen cao cấp cùng Vitamin C tinh khiết giúp kích thích sản sinh tế bào mới. Không chỉ dưỡng trắng, chúng tôi còn kiến tạo bề mặt da mịn mướt, săn chắc và luôn khô thoáng."',
    faq_title: metadata.science_faq_title || 'Câu hỏi thường gặp',
    faq_subtitle: metadata.science_faq_subtitle || 'Giải đáp các thắc mắc phổ biến về sản phẩm'
  });

  let selectedFaqIndex = $state(-1);
  let isModalOpen = $state(false);

  const faqs = $derived(metadata?.faqs || []);

  const selectedFaq = $derived(selectedFaqIndex >= 0 ? faqs[selectedFaqIndex] : null);

  function openFaq(index: number) {
    selectedFaqIndex = index;
    isModalOpen = true;
  }

  function closeFaq() {
    isModalOpen = false;
  }
</script>

<section id="science-mechanism" class="snap-session snap-session-standard science-section relative w-full overflow-hidden" style:padding-top="var(--standard-pt)">
    <!-- 150px Coordinate Grid Overlay -->
    <div class="tech-grid opacity-30"></div>

    <div class="container mx-auto px-6 max-w-6xl text-center relative z-surface">
        
        <h2 class="elite-session-headline mb-10 text-center bento-headline">
            <span>
                <EditableWrapper path="metadata.science_headline_1" type="text" label="SỬA TIÊU ĐỀ 1" class="inline" as="span">
                    {h1}
                </EditableWrapper>
            </span>
            <span>
                <EditableWrapper path="metadata.science_headline_2" type="text" label="SỬA TIÊU ĐỀ 2" class="inline" as="span">
                    {h2}
                </EditableWrapper>
            </span>
        </h2>

        <p class="section-description text-white/50 text-[11px] md:text-[12px] max-w-xl mx-auto leading-relaxed tracking-[0.1em] uppercase -mt-6 mb-12 text-center font-medium">
            <EditableWrapper path="metadata.science_subheadline" type="text" label="SỬA MÔ TẢ" as="span">
                {product?.metadata?.science_subheadline || labels.subheadline}
            </EditableWrapper>
        </p>

        <!-- BENTO GRID (KINETIC ASYMMETRIC - Viral 2026) -->
        <div class="bento-grid-kinetic grid grid-cols-1 md:grid-cols-12 gap-10 items-stretch text-left">
            
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
                        loading="lazy"
                        decoding="async"
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

                    <h3 class="text-white text-lg lg:text-2xl font-black mb-3 tracking-tight uppercase transition-colors group-hover:text-luxury-sakura">
                        <EditableWrapper path="metadata.science_card1_title" type="text" label="SỬA TIÊU ĐỀ THẺ 1" as="span">
                            {product?.metadata?.science_card1_title || labels.card1_title}
                        </EditableWrapper>
                    </h3>
                    
                    <p class="text-slate-500 text-xs lg:text-base leading-relaxed font-medium">
                        <EditableWrapper path="metadata.science_card1_desc" type="text" label="SỬA MÔ TẢ THẺ 1">
                            {product?.metadata?.science_card1_desc || labels.card1_desc}
                        </EditableWrapper>
                    </p>
                </div>

                <!-- Thẻ 2 -->
                <div class="flex-1 flex flex-col justify-center relative bg-white/[0.01] border border-white/5 rounded-[2rem] p-10 backdrop-blur-3xl transition-all duration-700 hover:border-luxury-gold/40 group overflow-visible shadow-2xl">
                    <div class="absolute bottom-[-15px] right-[-15px] w-56 h-56 opacity-20 pointer-events-none group-hover:opacity-40 transition-opacity duration-1000">
                        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" class="w-full h-full -rotate-12">
                            <path fill="none" stroke="#FFB7C5" stroke-width="2" d="M0,100 L40,100 L50,60 L70,140 L80,100 L120,100 L130,40 L150,160 L160,100 L200,100" class="wave-path" />
                            <path fill="none" stroke="#E3B5A4" stroke-width="1" d="M0,110 L40,110 L55,70 L75,150 L85,110 L125,110 L135,50 L155,170 L165,110 L200,110" class="wave-path-delayed" />
                        </svg>
                    </div>

                    <h3 class="text-white text-lg lg:text-2xl font-black mb-3 tracking-tight uppercase transition-colors group-hover:text-luxury-gold">
                        <EditableWrapper path="metadata.science_card2_title" type="text" label="SỬA TIÊU ĐỀ THẺ 2" as="span">
                            {product?.metadata?.science_card2_title || labels.card2_title}
                        </EditableWrapper>
                    </h3>

                    <p class="text-slate-500 text-xs lg:text-base leading-relaxed font-medium">
                        <EditableWrapper path="metadata.science_card2_desc" type="text" label="SỬA MÔ TẢ THẺ 2">
                            {product?.metadata?.science_card2_desc || labels.card2_desc}
                        </EditableWrapper>
                    </p>
                </div>
                </div> <!-- Close Khối phải kinetic stack -->
            </div> <!-- Close BENTO GRID -->

            <!-- FAQ SECTION (Super Compact Viral Modal Edition) -->
            {#if faqs.length > 0}
            <div class="faq-ultra-compact mt-12 border-t border-white/5 pt-10 pb-16">
                <div class="max-w-6xl mx-auto flex flex-col items-start">
                    
                    <!-- HEADER: SINGLE ROW -->
                    <div class="faq-header-row flex flex-row items-center gap-6 mb-10 w-full group cursor-pointer">
                        <div class="faq-icon-box w-14 h-14 rounded-2xl bg-luxury-sakura/10 border border-luxury-sakura/20 flex items-center justify-center text-luxury-sakura shadow-[0_0_30px_rgba(193,143,126,0.1)] transition-transform group-hover:scale-110">
                            <HelpCircle class="w-8 h-8" strokeWidth={2.5} />
                        </div>
                        
                        <div class="flex flex-col">
                            <h3 class="text-2xl lg:text-3xl font-black text-white tracking-tighter uppercase leading-none">
                                <EditableWrapper path="metadata.science_faq_title" type="text" label="SỬA TIÊU ĐỀ FAQ" as="span">
                                    {labels.faq_title}
                                </EditableWrapper>
                            </h3>
                            <p class="text-[10px] uppercase tracking-[0.3em] font-bold text-slate-500 mt-2 opacity-60">
                                Click để xem giải đáp chuyên sâu
                            </p>
                        </div>
                    </div>

                    <!-- FAQ GRID (LOCKED TO MAX 4 ITEMS UI) -->
                    <div class="faq-grid w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {#each faqs.slice(0, 4) as faq, i}
                            <button 
                                class="faq-item-card group relative bg-white/[0.02] border border-white/5 rounded-2xl p-6 text-left transition-all duration-500 hover:bg-white/[0.04] hover:border-luxury-sakura/30 hover:-translate-y-1 h-full"
                                onclick={() => openFaq(i)}
                            >
                                <div class="flex items-center justify-between gap-4 w-full h-full">
                                    <span class="question-text flex-1 text-[13px] font-bold text-white/90">
                                        {faq.question}
                                    </span>
                                    <div class="faq-arrow-indicator shrink-0">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 opacity-40 group-hover:text-luxury-sakura group-hover:opacity-100 transition-all" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M5 12h14m-7-7 7 7-7 7"/>
                                        </svg>
                                    </div>
                                </div>
                            </button>
                        {/each}
                    </div>
                </div>
            </div>
            {/if}
        </div> <!-- Close Container -->

        <!-- VIRAL FAQ MODAL -->
        {#if isModalOpen && selectedFaq}
        <div use:portal class="faq-viral-modal fixed inset-0 flex items-center justify-center p-6" style:z-index={Z_INDEX_CLIENT.MODAL}>
            <!-- Backdrop -->
            <button
                transition:fade={{ duration: 300 }}
                type="button"
                class="absolute inset-0 bg-black/80 backdrop-blur-xl border-none outline-none cursor-default"
                onclick={closeFaq}
                aria-label="Đóng"
            ></button>

            <!-- Modal Content -->
            <div
                transition:scale={{ duration: 400, start: 0.9, opacity: 0 }}
                class="relative w-full max-w-lg bg-[#0a0a0a] border border-white/10 rounded-[40px] shadow-[0_50px_100px_rgba(0,0,0,0.9)] overflow-hidden flex flex-col p-10 lg:p-14"
                role="dialog"
                aria-modal="true"
            >
                <button 
                    onclick={closeFaq} 
                    class="absolute right-8 top-8 w-12 h-12 flex items-center justify-center text-white/30 hover:text-white hover:bg-white/5 transition-all rounded-full border border-white/5"
                >
                    <X class="w-6 h-6" strokeWidth={2} />
                </button>

                <div class="flex flex-col text-center items-center">
                    <div class="w-20 h-20 rounded-[2rem] bg-luxury-sakura/10 border border-luxury-sakura/20 flex items-center justify-center text-luxury-sakura mb-10 shadow-[0_0_50px_rgba(193,143,126,0.2)]">
                        <HelpCircle class="w-10 h-10" strokeWidth={2.5} />
                    </div>

                    <h2 class="text-2xl lg:text-3xl font-black text-white tracking-tighter leading-tight mb-8">
                         {selectedFaq.question}
                    </h2>

                    <div class="w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-10"></div>

                    <p class="text-slate-400 text-lg lg:text-xl font-medium leading-relaxed opacity-90 italic">
                        "{selectedFaq.answer}"
                    </p>

                    <button 
                        onclick={closeFaq}
                        class="mt-14 w-full py-5 bg-white text-black text-xs font-black uppercase tracking-[0.3em] rounded-2xl hover:bg-luxury-sakura hover:text-white transition-all transform hover:scale-[1.02] active:scale-95 shadow-[0_20px_40px_rgba(255,255,255,0.1)]"
                    >
                        Tôi đã rõ
                    </button>
                </div>
            </div>
        </div>
        {/if}

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
    margin-bottom: 0.15rem;
  }
  
  .bento-headline :global(span:last-child) {
    font-size: 0.65em !important;
    opacity: 0.8;
    letter-spacing: 0.05em !important;
    font-weight: 500 !important;
    -webkit-text-fill-color: white !important; /* Force hiển thị rõ ràng */
  }
</style>
