<script lang="ts">
  import { onMount } from 'svelte';
  import './ResultTimeline.css';
  import { fade, fly, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';

  const shopStore = getShopStore();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);

  interface TimelinePoint {
    day: number;
    title: string;
    description: string;
    icon: string;
  }

  const timeline: TimelinePoint[] = [
    { day: 1, title: 'KÍCH HOẠT', description: 'Tinh chất len lỏi vào tầng biểu bì, đánh thức cơ chế tự phục hồi.', icon: '✨' },
    { day: 7, title: 'HỒI SINH', description: 'Hắc tố mờ dần, làn da bắt đầu lấy lại độ đàn hồi và mịn màng.', icon: '🕊️' },
    { day: 14, title: 'RẠNG RỠ', description: 'Lột xác hoàn toàn. Bạn tự tin rạng ngời trong mọi khung hình.', icon: '💎' }
  ];

  const scenarios = [
    {
      title: "LUX_GALA",
      result: "Tự tin diện váy hở lưng quyến rũ",
      desc: "Xóa tan mọi mặc cảm thâm sạm vùng lưng.",
      id: "scene_1",
      parallax: 10
    },
    {
      title: "BEACH_READY",
      result: "Rạng rỡ cùng Bikini yêu thích",
      desc: "Làn da trắng mịn không tì vết dưới nắng.",
      id: "scene_2",
      parallax: -15
    },
    {
      title: "TOUCH_SENSATION",
      result: "Cảm giác chạm đầy mê hoặc",
      desc: "Mướt mịn đánh thức mọi giác quan.",
      id: "scene_3",
      parallax: 5
    }
  ];

  let visibleLevels = $state(0);
  let scrollY = $state(0);
  let displaySlots = $state(12);

  onMount(() => {
    // Neural Counter Logic
    const counterInterval = setInterval(() => {
      if (displaySlots > 7) displaySlots--;
      else clearInterval(counterInterval);
    }, 2000);
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        let i = 0;
        const interval = setInterval(() => {
          visibleLevels++;
          i++;
          if (i >= timeline.length + scenarios.length) clearInterval(interval);
        }, 400);
        observer.disconnect();
      }
    }, { threshold: 0.2 });

    const el = document.getElementById('result-timeline');
    if (el) observer.observe(el);

    const handleScroll = () => {
      scrollY = window.scrollY;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  });
</script>

<section id="result-timeline" class="cinematic-results-section snap-session">
  <div class="cinematic-grain"></div>
  <div class="background-silk-path">
     <svg viewBox="0 0 1000 1000" preserveAspectRatio="none">
        <path d="M-100,500 C200,300 400,700 700,400 C900,200 1100,500 1100,500" class="silk-line" />
     </svg>
  </div>

  <div class="container mx-auto px-6 max-w-7xl relative z-10">
    <!-- NARRATIVE HEADER -->
    <header class="mb-32 md:mb-48 text-left md:flex items-end justify-between border-b border-white/5 pb-10">
      <div class="max-w-2xl">
        <div class="hud-mini-tag mb-6">
          <span class="text-luxury-sakura font-black tracking-[0.5em] text-[8px] uppercase">Path_To_Transformation</span>
        </div>
        <h3 class="text-6xl md:text-8xl font-black text-white tracking-tighter leading-[0.9] uppercase italic mb-8">
          <EditableWrapper path="metadata.timeline_headline_1" type="text" label="TIÊU ĐỀ ĐẠI BIỂU 1">
            {product?.metadata?.timeline_headline_1 || 'KHOẢNH KHẮC'}
          </EditableWrapper>
          <br/> 
          <span class="text-luxury-gold">
             <EditableWrapper path="metadata.timeline_headline_2" type="text" label="TIÊU ĐỀ ĐẠI BIỂU 2">
               {product?.metadata?.timeline_headline_2 || 'CHIẾN THẮNG'}
             </EditableWrapper>
          </span>
        </h3>
      </div>
      <div class="hidden md:block text-right mb-2">
         <p class="text-slate-500 text-xs font-semibold tracking-widest uppercase">Elite Registry // 2026</p>
         <div class="text-luxury-sakura text-3xl font-black italic">98.6%</div>
         <p class="text-[9px] text-white/20 font-black uppercase tracking-widest leading-none">Global_Success_Rate</p>
      </div>
    </header>

    <!-- THE STORYLINE (Linear but Flowing) -->
    <div class="storyline-flow mb-40 md:mb-64">
       <div class="grid grid-cols-1 md:grid-cols-3 gap-24 md:gap-32">
          {#each timeline as item, i}
             <div class="story-node" class:active={visibleLevels > i}>
                 <div class="node-indicator">
                    <div class="pulse-ring"></div>
                    <EditableWrapper path={`metadata.timeline_${i}_day`} type="text" label="NGÀY">
                       <span class="node-day">{product?.metadata?.[`timeline_${i}_day`] || '0' + item.day}</span>
                    </EditableWrapper>
                 </div>
                 <div class="node-content mt-12">
                    <EditableWrapper path={`metadata.timeline_${i}_title`} type="text" label="BƯỚC">
                       <h4 class="text-2xl font-black text-white italic mb-4 tracking-tighter">{product?.metadata?.[`timeline_${i}_title`] || item.title}</h4>
                    </EditableWrapper>
                    <EditableWrapper path={`metadata.timeline_${i}_desc`} type="text" label="MÔ TẢ">
                       <p class="text-sm text-slate-400 font-medium leading-relaxed">{product?.metadata?.[`timeline_${i}_desc`] || item.description}</p>
                    </EditableWrapper>
                 </div>
             </div>
          {/each}
       </div>
    </div>

    <!-- ASYMMETRIC BENTO SCENARIOS -->
    <div class="cinematic-bento pt-20 border-t border-white/5">
        <div class="section-title-hud mb-20 text-center md:text-left">
           <EditableWrapper path="metadata.timeline_bento_tag" type="text" label="THẺ BENTO">
              <span class="text-[10px] font-black text-luxury-gold uppercase tracking-[0.6em] block mb-2">{product?.metadata?.timeline_bento_tag || 'The_Winning_Output'}</span>
           </EditableWrapper>
           <h4 class="text-4xl md:text-5xl font-black text-white italic uppercase tracking-tighter">
              <EditableWrapper path="metadata.timeline_bento_h1" type="text" label="TIÊU ĐỀ 1" class="inline">
                 {product?.metadata?.timeline_bento_h1 || 'SỐNG TRỌN'}
              </EditableWrapper>
              <span class="text-luxury-sakura">
                 <EditableWrapper path="metadata.timeline_bento_h2" type="text" label="TIÊU ĐỀ 2" class="inline">
                    {product?.metadata?.timeline_bento_h2 || 'TỪNG GIÂY PHÚT'}
                 </EditableWrapper>
              </span>
           </h4>
        </div>

       <div class="bento-grid-narrative">
          <!-- SCENE 1: LARGE HERO CARD -->
          <div class="bento-item main-scene" style:--parallax="{scrollY * scenarios[0].parallax * 0.005}px">
             {#if visibleLevels > 3}
                <div class="scene-card p-12 md:p-16 h-full flex flex-col justify-end relative overflow-hidden group" in:fly={{ y: 50, duration: 1200 }}>
                   <div class="absolute inset-0 bg-slate-900/50 group-hover:bg-slate-900/40 transition-all duration-700"></div>
                   <div class="scene-lens-flare"></div>
                    <div class="relative z-10">
                       <EditableWrapper path={`metadata.scene_0_title`} type="text" label="THẺ SCENE">
                          <span class="text-[9px] font-black text-luxury-gold uppercase tracking-[0.4em] mb-3 block">{product?.metadata?.scene_0_title || scenarios[0].title}</span>
                       </EditableWrapper>
                       <EditableWrapper path={`metadata.scene_0_result`} type="text" label="KẾT QUẢ">
                          <h5 class="text-3xl md:text-5xl font-black text-white italic mb-4 leading-none">{product?.metadata?.scene_0_result || scenarios[0].result}</h5>
                       </EditableWrapper>
                       <EditableWrapper path={`metadata.scene_0_desc`} type="text" label="MÔ TẢ">
                          <p class="text-sm md:text-lg text-slate-300 font-medium max-w-md opacity-0 group-hover:opacity-100 transition-all duration-700 transform translate-y-4 group-hover:translate-y-0">{product?.metadata?.scene_0_desc || scenarios[0].desc}</p>
                       </EditableWrapper>
                    </div>
                </div>
             {/if}
          </div>

          <!-- SUB SCENES GRID -->
          <div class="sub-scenes flex flex-col gap-6">
             {#each scenarios.slice(1) as scene, i}
                <div class="bento-item sub-scene" style:--parallax="{scrollY * scene.parallax * 0.005}px">
                   {#if visibleLevels > (i + 4)}
                      <div class="scene-card p-8 md:p-10 h-full flex flex-col justify-end group" in:fly={{ x: 30, duration: 1000, delay: i * 200 }}>
                         <div class="absolute inset-0 bg-slate-900/60 group-hover:bg-luxury-sakura/10 transition-all duration-500"></div>
                          <div class="relative z-10">
                             <EditableWrapper path={`metadata.scene_${i+1}_title`} type="text" label="THẺ SCENE">
                                <span class="text-[8px] font-black text-white/40 uppercase tracking-widest mb-1 block">{product?.metadata?.[`scene_${i+1}_title`] || scene.title}</span>
                             </EditableWrapper>
                             <EditableWrapper path={`metadata.scene_${i+1}_result`} type="text" label="KẾT QUẢ">
                                <h5 class="text-xl md:text-2xl font-bold text-white italic leading-tight">{product?.metadata?.[`scene_${i+1}_result`] || scene.result}</h5>
                             </EditableWrapper>
                             <EditableWrapper path={`metadata.scene_${i+1}_desc`} type="text" label="MÔ TẢ">
                                <p class="text-xs text-slate-400 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">{product?.metadata?.[`scene_${i+1}_desc`] || scene.desc}</p>
                             </EditableWrapper>
                          </div>
                      </div>
                   {/if}
                </div>
             {/each}
          </div>
       </div>
    </div>

    <!-- ELITE HUD FOMO OVERLAY -->
    <div class="elite-hud-fomo mt-32 md:mt-48">
       <div class="hud-container p-12 md:p-16 rounded-[4rem] bg-white/[0.01] border border-white/5 backdrop-blur-3xl relative overflow-hidden group">
          <div class="hud-glow absolute -top-1/2 -left-1/2 w-full h-full bg-luxury-sakura/5 blur-[120px] rounded-full"></div>
          
          <div class="relative z-10 flex flex-col md:flex-row items-center justify-between gap-12">
             <div class="text-left">
                <div class="flex items-center gap-3 mb-6">
                   <div class="w-2 h-2 rounded-full bg-red-500 animate-ping"></div>
                   <EditableWrapper path="metadata.timeline_fomo_tag" type="text" label="THẺ FOMO">
                      <span class="text-luxury-gold text-xs font-black uppercase tracking-[0.4em]">{product?.metadata?.timeline_fomo_tag || 'Limited_Allocation'}</span>
                   </EditableWrapper>
                </div>
                <h6 class="text-4xl md:text-6xl font-black text-white italic tracking-tighter leading-none mb-6">
                   <EditableWrapper path="metadata.timeline_fomo_h1" type="text" label="MỞ ĐẦU" class="inline">
                      {product?.metadata?.timeline_fomo_h1 || 'CHỈ CÒN'}
                   </EditableWrapper>
                   <span class="text-luxury-sakura transition-all duration-1000 tabular-nums">{displaySlots < 10 ? '0' + displaySlots : displaySlots} SUẤT</span> <br/> 
                   <EditableWrapper path="metadata.timeline_fomo_h2" type="text" label="KẾT THÚC" class="inline">
                      {product?.metadata?.timeline_fomo_h2 || 'ƯU ĐÃI TẶNG ẨN'}
                   </EditableWrapper>
                </h6>
             </div>
             
             <div class="hud-metrics flex gap-8 md:gap-16">
                <div class="metric-box">
                   <EditableWrapper path="metadata.timeline_fomo_metric1_desc" type="text" label="THẺ METRIC 1">
                      <div class="text-white/20 text-[8px] font-black uppercase tracking-widest mb-2">{product?.metadata?.timeline_fomo_metric1_desc || 'Inventory_Status'}</div>
                   </EditableWrapper>
                   <EditableWrapper path="metadata.timeline_fomo_metric1_value" type="text" label="GIÁ TRỊ 1">
                      <div class="text-white text-xl font-bold italic">{product?.metadata?.timeline_fomo_metric1_value || 'SẮP CHÁY HÀNG'}</div>
                   </EditableWrapper>
                   <div class="w-full h-px bg-red-500/30 mt-2"></div>
                </div>
                <div class="metric-box">
                   <EditableWrapper path="metadata.timeline_fomo_metric2_desc" type="text" label="THẺ METRIC 2">
                      <div class="text-white/20 text-[8px] font-black uppercase tracking-widest mb-2">{product?.metadata?.timeline_fomo_metric2_desc || 'Demand_Index'}</div>
                   </EditableWrapper>
                   <EditableWrapper path="metadata.timeline_fomo_metric2_value" type="text" label="GIÁ TRỊ 2">
                      <div class="text-luxury-gold text-xl font-bold italic font-mono uppercase">{product?.metadata?.timeline_fomo_metric2_value || 'Extreme'}</div>
                   </EditableWrapper>
                   <div class="w-full h-px bg-luxury-gold/30 mt-2"></div>
                </div>
             </div>
          </div>
       </div>
    </div>

    <footer class="mt-20 text-center opacity-20">
      <p class="text-[10px] font-black uppercase tracking-[0.5em] text-white">* PHÁC ĐỒ PHỤ THUỘC VÀO CƠ ĐỊA THỰC TẾ *</p>
    </footer>
  </div>
</section>
