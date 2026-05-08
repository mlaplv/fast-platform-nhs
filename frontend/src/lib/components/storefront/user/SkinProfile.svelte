<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Zap from "@lucide/svelte/icons/zap";
  import Droplets from "@lucide/svelte/icons/droplets";
  import Wind from "@lucide/svelte/icons/wind";
  import Layers from "@lucide/svelte/icons/layers";
  import Heart from "@lucide/svelte/icons/heart";
  import Smile from "@lucide/svelte/icons/smile";

  interface SkinData {
    skinType: string;
    concerns: string[];
    sensitivity: number;
  }

  let { data = $bindable({ skinType: '', concerns: [], sensitivity: 5 }) }: { data: SkinData } = $props();

  const skinTypes = [
    { id: 'oily', label: 'Dầu', desc: 'Tiết nhiều bã nhờn, lỗ chân lông to', icon: Droplets },
    { id: 'dry', label: 'Khô', desc: 'Thường xuyên căng rát, bong tróc', icon: Wind },
    { id: 'combination', label: 'Hỗn hợp', desc: 'Dầu vùng chữ T, khô vùng chữ U', icon: Layers },
    { id: 'sensitive', label: 'Nhạy cảm', desc: 'Dễ đỏ, kích ứng với môi trường', icon: Heart },
    { id: 'normal', label: 'Thường', desc: 'Cân bằng, khỏe mạnh', icon: Smile }
  ];

  const concernsList = [
    'Mụn & thâm', 'Lão hóa & nếp nhăn', 'Sạm nám', 'Lỗ chân lông', 'Cấp ẩm'
  ];

  function toggleConcern(concern: string) {
    if (data.concerns.includes(concern)) {
      data.concerns = data.concerns.filter(c => c !== concern);
    } else {
      data.concerns = [...data.concerns, concern];
    }
  }
</script>

<div class="space-y-16 py-6" in:fade={{ duration: 600 }}>
  <!-- Skin Type Selection: Viral Modern Segmented Picker -->
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-luxury-copper/10 flex items-center justify-center">
           <Sparkles class="w-4 h-4 text-luxury-copper" />
        </div>
        <h3 class="text-xl font-serif italic text-stone-800 leading-none">Bản sắc làn da</h3>
      </div>
      <p class="text-[9px] uppercase tracking-widest text-stone-400 font-bold">Skin Identity</p>
    </div>

    <div class="relative bg-stone-50 p-1.5 rounded-2xl border border-stone-100 flex items-center gap-1 overflow-x-auto no-scrollbar scroll-smooth">
      {#each skinTypes as type}
        <button
          onclick={() => data.skinType = type.id}
          class="flex-1 min-w-[90px] md:min-w-0 flex flex-col items-center justify-center py-4 px-2 rounded-xl transition-all duration-500 relative group
          {data.skinType === type.id ? 'bg-white shadow-[0_10px_20px_rgba(0,0,0,0.05)] text-stone-900' : 'text-stone-400 hover:text-stone-600'}"
        >
          <type.icon class="w-5 h-5 mb-2 transition-transform duration-500 group-hover:scale-110 {data.skinType === type.id ? 'text-luxury-copper' : 'opacity-40'}" />
          <span class="text-[11px] font-bold uppercase tracking-wider">{type.label}</span>

          {#if data.skinType === type.id}
            <div class="absolute bottom-1 w-1 h-1 bg-luxury-copper rounded-full" in:fade></div>
          {/if}
        </button>
      {/each}
    </div>

    <!-- Active Skin Type Description Card -->
    {#if data.skinType}
      {#each skinTypes.filter(t => t.id === data.skinType) as active}
        <div
          in:fly={{ y: 10, duration: 600 }}
          class="bg-luxury-copper/5 border border-luxury-copper/10 p-4 rounded-xl flex items-start gap-4"
        >
          <div class="w-10 h-10 rounded-full bg-white flex items-center justify-center shrink-0 shadow-sm">
            <active.icon class="w-5 h-5 text-luxury-copper" />
          </div>
          <div>
            <h4 class="text-[12px] font-bold text-stone-800 uppercase tracking-widest mb-1">Đặc tính {active.label}</h4>
            <p class="text-[13px] text-stone-500 leading-relaxed italic">{active.desc}</p>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- Concerns: Elegant Pill Cloud -->
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-luxury-copper/10 flex items-center justify-center">
          <ShieldCheck class="w-4 h-4 text-luxury-copper" />
        </div>
        <h3 class="text-xl font-serif italic text-stone-800 leading-none">Mục tiêu chăm sóc</h3>
      </div>
      <p class="text-[9px] uppercase tracking-widest text-stone-400 font-bold">Skin Goals</p>
    </div>

    <div class="flex flex-wrap gap-2.5">
      {#each concernsList as concern}
        <button
          onclick={() => toggleConcern(concern)}
          class="px-5 py-3 rounded-full border text-[11px] font-bold uppercase tracking-widest transition-all duration-500
          {data.concerns.includes(concern)
            ? 'bg-stone-900 text-white border-stone-900 shadow-[0_5px_15px_rgba(0,0,0,0.1)] scale-105'
            : 'bg-white text-stone-400 border-stone-100 hover:border-stone-200 hover:text-stone-600'}"
        >
          {concern}
        </button>
      {/each}
    </div>
  </div>

  <!-- Sensitivity Scale: Minimalist Luxury Slider -->
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-luxury-copper/10 flex items-center justify-center">
          <Zap class="w-4 h-4 text-luxury-copper" />
        </div>
        <h3 class="text-xl font-serif italic text-stone-800 leading-none">Chỉ số nhạy cảm</h3>
      </div>
      <div class="flex items-baseline gap-1">
        <span class="text-2xl font-serif italic text-luxury-copper leading-none">{data.sensitivity}</span>
        <span class="text-[9px] uppercase tracking-widest text-stone-300 font-bold">/ 10</span>
      </div>
    </div>

    <div class="relative py-4 flex items-center">
      <input
        type="range"
        min="1"
        max="10"
        bind:value={data.sensitivity}
        class="luxury-slider w-full h-1.5 bg-stone-100 rounded-full appearance-none cursor-pointer outline-none transition-all"
        style="background: linear-gradient(to right, #c5a059 {((data.sensitivity - 1) / 9) * 100}%, #f5f5f4 {((data.sensitivity - 1) / 9) * 100}%);"
      />
      <div class="absolute -bottom-6 left-0 right-0 flex justify-between text-[9px] text-stone-300 uppercase tracking-[4px] font-black italic">
        <span>Resilient</span>
        <span>Sensitive</span>
      </div>
    </div>
  </div>
</div>

<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  /* Luxury Range Slider Styling */
  .luxury-slider::-webkit-slider-runnable-track {
    height: 6px;
    border-radius: 999px;
  }

  .luxury-slider::-webkit-slider-thumb {
    appearance: none;
    width: 22px;
    height: 22px;
    background: #ffffff;
    border: 3px solid #c5a059;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(197, 160, 89, 0.3);
    margin-top: -8px; /* Centers thumb on 6px track */
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }

  .luxury-slider::-webkit-slider-thumb:hover {
    transform: scale(1.15);
    background: #c5a059;
    box-shadow: 0 0 0 8px rgba(197, 160, 89, 0.1);
  }

  .luxury-slider::-moz-range-track {
    height: 6px;
    border-radius: 999px;
  }

  .luxury-slider::-moz-range-thumb {
    width: 22px;
    height: 22px;
    background: #ffffff;
    border: 3px solid #c5a059;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(197, 160, 89, 0.3);
    transition: all 0.3s ease;
  }
</style>
