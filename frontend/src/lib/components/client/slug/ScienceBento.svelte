<script lang="ts">
  import { resolveMediaUrl } from '$lib/state/utils';
  import "./ScienceBento.css";
</script>

<section id="science-mechanism" class="snap-session-standard science-section relative w-full overflow-hidden">
    <!-- 150px Coordinate Grid Overlay -->
    <div class="tech-grid opacity-30"></div>

    <div class="container mx-auto px-6 max-w-6xl text-center relative z-surface">
        
        <!-- SECTION HEADER (Normalized spacing to fix "thừa trên thiếu dưới") -->
        <header class="mb-8 md:mb-12 animate-reveal">
            <h2 class="text-white font-black tracking-tight leading-none uppercase mb-6 text-3xl md:text-5xl lg:text-6xl mx-auto flex flex-col gap-1 md:gap-2">

                <span>ỨC CHẾ ACETYLCHOLINE &</span>
                <span>ĐÓNG BĂNG HẠI KHUẨN</span>
            </h2>



            <p class="section-description text-white/40 text-base md:text-lg max-w-none mx-auto leading-relaxed">
                "Tinh chất siêu vi hạt can thiệp tức thì vào chất dẫn truyền thần kinh, ngắt lệnh tiết mồ hôi. Đồng thời bao vây và vô hiệu hóa 99.9% ổ vi khuẩn sinh mùi chỉ sau 3 giây chạm da."
            </p>
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

                <img 
                    src={resolveMediaUrl('/uploads/img/co--che.png')} 
                    alt="Cơ chế khoa học" 
                    class="w-full h-full object-contain rounded-[5px] transition-transform duration-700 group-hover:scale-105"
                />
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

                    <h3 class="text-white text-lg lg:text-2xl font-black mb-3 tracking-tight uppercase transition-colors group-hover:text-blue-400">
                        BẺ GÃY CHUỖI AXIT BÉO
                    </h3>
                    <p class="text-slate-500 text-xs lg:text-base leading-relaxed font-medium">
                        "Chặn đứng quá trình vi khuẩn phân hủy protein trong mồ hôi. Trung hòa mùi chua nồng và đào thải cặn bã tích tụ do lạm dụng hóa chất."
                    </p>
                </div>

                <!-- Thẻ 2: TÁI TẠO & SE KHÍT NANG LÔNG -->
                <div class="flex-1 flex flex-col justify-center relative bg-slate-800/40 border border-slate-700/60 rounded-[5px] p-8 lg:p-10 backdrop-blur-md transition-all duration-500 hover:border-blue-500/40 group overflow-hidden">
                    <!-- Technical Wave Decoration: Digital Pulse Variant -->
                    <div class="absolute bottom-[-15px] right-[-15px] w-56 h-56 opacity-20 pointer-events-none group-hover:opacity-40 transition-opacity duration-1000">
                        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" class="w-full h-full -rotate-12">
                            <path fill="none" stroke="#22c55e" stroke-width="2" d="M0,100 L40,100 L50,60 L70,140 L80,100 L120,100 L130,40 L150,160 L160,100 L200,100" class="wave-path" />
                            <path fill="none" stroke="#4ade80" stroke-width="1" d="M0,110 L40,110 L55,70 L75,150 L85,110 L125,110 L135,50 L155,170 L165,110 L200,110" class="wave-path-delayed" />
                        </svg>
                    </div>

                    <h3 class="text-white text-lg lg:text-2xl font-black mb-3 tracking-tight uppercase transition-colors group-hover:text-blue-400">
                        TÁI TẠO & SE KHÍT NANG LÔNG
                    </h3>
                    <p class="text-slate-500 text-xs lg:text-base leading-relaxed font-medium">
                        "Sử dụng phức hợp Dược liệu sinh học để phục hồi tuyến bã nhờn tổn thương. Trả lại vùng da sáng khỏe, phẳng mịn và khô ron suốt 48H."
                    </p>
                </div>

            </div>

        </div>

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
</style>
