<script lang="ts">
  import { onMount } from 'svelte';
  import './EmotionalIncentive.css';
  import { fade, fly } from 'svelte/transition';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';

  const shopStore = getShopStore();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);
  const metadata = $derived(product?.metadata || {});

  interface Scenario {
    title: string;
    result: string;
    caption: string;
    image: string;
  }

  const scenarios: Scenario[] = [
    {
      title: "KIÊU SA TRONG TIỆC TỐI",
      result: "Tự tin diện những mẫu đầm hở lưng quyến rũ nhất.",
      caption: "Không còn lo ngại các vùng da thâm sạm, bạn là tâm điểm của sự chú ý.",
      image: "https://micsmo.com/wp-content/uploads/2024/03/h6-img-1.jpg" // Placeholder for luxury image
    },
    {
      title: "RẠNG RỠ TRÊN BIỂN XANH",
      result: "Tự do phô diễn đường cong cùng bộ Bikini yêu thích.",
      caption: "Làn da trắng mịn không tì vết giúp bạn tỏa sáng dưới ánh nắng mặt trời.",
      image: "https://micsmo.com/wp-content/uploads/2024/03/h6-img-2.jpg"
    },
    {
      title: "CẢM GIÁC CHẠM ĐẦY MÊ HOẶC",
      result: "Làn da mướt mịn đánh thức mọi giác quan.",
      caption: "Xóa tan mọi rào cản, tự tin trong những khoảnh khắc gần gũi nhất.",
      image: "https://micsmo.com/wp-content/uploads/2024/03/h6-img-3.jpg"
    }
  ];

  let visibleLevels = $state(0);

  onMount(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        let i = 0;
        const interval = setInterval(() => {
          visibleLevels++;
          i++;
          if (i >= scenarios.length) clearInterval(interval);
        }, 800);
        observer.disconnect();
      }
    }, { threshold: 0.3 });

    const el = document.getElementById('transformation');
    if (el) observer.observe(el);
  });
</script>

<section id="transformation" class="emotional-section snap-session">
  <div class="luxury-bg-overlay"></div>
  
  <div class="container mx-auto px-6 max-w-6xl relative z-10">
    <header class="text-center mb-16 md:mb-24">
      <div class="hud-tag inline-flex items-center gap-3 px-6 py-2 bg-luxury-sakura/5 border border-luxury-sakura/20 rounded-full mb-6">
        <span class="w-2 h-2 rounded-full bg-luxury-sakura animate-pulse shadow-[0_0_10px_rgba(193,143,126,0.8)]"></span>
        <span class="text-[9px] font-black text-luxury-sakura uppercase tracking-[0.4em]">Imagine_The_Result</span>
      </div>
      <h2 class="text-4xl md:text-7xl font-black text-white tracking-tighter leading-none mb-6 italic uppercase">
        <EditableWrapper path="metadata.emotional_headline_1" type="text" label="SỬA TIÊU ĐỀ 1" class="inline" as="span">
          {product?.metadata?.emotional_headline_1 || 'HÃY BẮT ĐẦU'}
        </EditableWrapper>
        <span class="text-luxury-gold">
          <EditableWrapper path="metadata.emotional_headline_2" type="text" label="SỬA TIÊU ĐỀ 2" class="inline" as="span">
            {product?.metadata?.emotional_headline_2 || 'SỐNG KHÁC BIỆT'}
          </EditableWrapper>
        </span>
      </h2>
      <p class="text-slate-400 text-sm md:text-lg max-w-2xl mx-auto font-medium tracking-tight leading-relaxed">
        <EditableWrapper path="metadata.emotional_subheadline" type="text" label="SỬA MÔ TẢ PHỤ" as="span">
          {product?.metadata?.emotional_subheadline || 'Đừng mua một hũ kem, hãy sở hữu sự tự tin để làm chủ mọi khoảnh khắc đắt giá nhất của cuộc đời bạn.'}
        </EditableWrapper>
      </p>
    </header>

    <div class="scenario-grid grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-8">
      {#each scenarios as item, i}
        <div class="scenario-card-wrapper" class:is-visible={visibleLevels > i}>
          {#if visibleLevels > i}
            <div class="scenario-card group" in:fly={{ y: 100, duration: 1200, delay: i * 300 }}>
              <div class="image-frame relative overflow-hidden rounded-3xl aspect-[4/5] mb-8 border border-white/5 group-hover:border-luxury-sakura/30 transition-all duration-700">
                <div class="image-shimmer absolute inset-0 bg-gradient-to-tr from-luxury-sakura/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>
                <!-- Elite V2.2: We use a stylized placeholder or background for now, assuming images flow from metadata later -->
                <div class="w-full h-full bg-slate-900 flex items-center justify-center relative inner-shadow-elite">
                   <div class="flex flex-col items-center gap-4 opacity-20 group-hover:opacity-100 transition-all duration-700">
                      <div class="w-20 h-px bg-luxury-sakura group-hover:w-32 transition-all duration-1000"></div>
                      <span class="text-[10px] uppercase tracking-[1em] text-luxury-gold">SCENE_{i+1}</span>
                      <div class="w-20 h-px bg-luxury-sakura group-hover:w-32 transition-all duration-1000"></div>
                   </div>
                </div>
              </div>

              <div class="content-frame">
                <span class="text-[8px] font-black text-luxury-sakura/60 uppercase tracking-[0.3em] mb-2 block">
                  <EditableWrapper path={`metadata.scenario_${i}_title`} type="text" label="NHÃN KỊCH BẢN">
                    {product?.metadata?.[`scenario_${i}_title`] || item.title}
                  </EditableWrapper>
                </span>
                <h4 class="text-2xl font-bold text-white mb-4 leading-tight italic">
                  <EditableWrapper path={`metadata.scenario_${i}_result`} type="text" label="KẾT QUẢ" as="span">
                    {product?.metadata?.[`scenario_${i}_result`] || item.result}
                  </EditableWrapper>
                </h4>
                <p class="text-sm text-slate-500 font-medium leading-relaxed opacity-80 group-hover:opacity-100 transition-opacity">
                  <EditableWrapper path={`metadata.scenario_${i}_caption`} type="text" label="CHI TIẾT" as="span">
                    {product?.metadata?.[`scenario_${i}_caption`] || item.caption}
                  </EditableWrapper>
                </p>
              </div>

              <div class="card-indicator mt-8 h-px w-0 bg-luxury-sakura group-hover:w-full transition-all duration-1000"></div>
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <div class="fomo-callout mt-24 md:mt-32 p-8 md:p-12 rounded-[3.5rem] bg-white/[0.02] backdrop-blur-3xl border border-white/5 border-t-white/10 text-center relative overflow-hidden group">
      <div class="absolute inset-0 bg-radial-at-t from-luxury-sakura/5 to-transparent"></div>
      
      <div class="relative z-10">
        <h5 class="text-luxury-gold text-2xl md:text-3xl font-black tracking-tight italic mb-4">
          <EditableWrapper path="metadata.emotional_fomo_h1" type="text" label="TIÊU ĐỀ FOMO" as="span">
             {product?.metadata?.emotional_fomo_h1 || 'CƠ HỘI CHỈ DÀNH CHO NGƯỜI QUYẾT ĐOÁN'}
          </EditableWrapper>
        </h5>
        <div class="flex flex-wrap items-center justify-center gap-4 md:gap-8 opacity-60">
          <div class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 bg-luxury-sakura rounded-full animate-ping"></span>
            <span class="text-[10px] font-black text-white/40 uppercase tracking-widest">
              <EditableWrapper path="metadata.emotional_fomo_msg1" type="text" label="THÔNG BÁO 1">
                {product?.metadata?.emotional_fomo_msg1 || 'Đang cháy hàng tại kho Nhật Bản'}
              </EditableWrapper>
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
            <span class="text-[10px] font-black text-white/40 uppercase tracking-widest">
               <EditableWrapper path="metadata.emotional_fomo_msg2" type="text" label="THÔNG BÁO 2">
                  {product?.metadata?.emotional_fomo_msg2 || 'Duy nhất 07 suất tặng ẩn cuối ngày'}
               </EditableWrapper>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
