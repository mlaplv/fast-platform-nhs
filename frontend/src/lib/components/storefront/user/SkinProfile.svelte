<script lang="ts">
  import { fade, slide } from 'svelte/transition';

  interface SkinData {
    skinType: string;
    concerns: string[];
    sensitivity: number;
  }

  let { data = $bindable({ skinType: '', concerns: [], sensitivity: 5 }) }: { data: SkinData } = $props();

  const skinTypes = [
    { id: 'oily', label: 'Da dầu', desc: 'Tiết nhiều bã nhờn, lỗ chân lông to' },
    { id: 'dry', label: 'Da khô', desc: 'Thường xuyên căng rát, bong tróc' },
    { id: 'combination', label: 'Da hỗn hợp', desc: 'Dầu vùng chữ T, khô vùng chữ U' },
    { id: 'sensitive', label: 'Da nhạy cảm', desc: 'Dễ đỏ, kích ứng với môi trường' },
    { id: 'normal', label: 'Da thường', desc: 'Cân bằng, khỏe mạnh' }
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

<div class="space-y-10 py-6" in:fade>
  <!-- Skin Type Selection -->
  <div class="space-y-4">
    <div class="flex items-center gap-2">
      <div class="w-1 h-5 bg-luxury-copper"></div>
      <h3 class="text-lg font-serif italic text-stone-800">Loại da của bạn</h3>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
      {#each skinTypes as type}
        <button
          onclick={() => data.skinType = type.id}
          class="flex flex-col p-4 border transition-all duration-300 text-left group
          {data.skinType === type.id ? 'border-luxury-copper bg-stone-50 ring-1 ring-luxury-copper' : 'border-stone-100 hover:border-stone-300 bg-white'}"
        >
          <span class="text-[14px] font-bold {data.skinType === type.id ? 'text-luxury-copper' : 'text-stone-700'}">{type.label}</span>
          <span class="text-[11px] text-stone-400 mt-1 leading-relaxed opacity-0 group-hover:opacity-100 transition-opacity">{type.desc}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Concerns -->
  <div class="space-y-4">
    <div class="flex items-center gap-2">
      <div class="w-1 h-5 bg-luxury-copper"></div>
      <h3 class="text-lg font-serif italic text-stone-800">Vấn đề da quan tâm</h3>
    </div>
    <div class="flex flex-wrap gap-3">
      {#each concernsList as concern}
        <button
          onclick={() => toggleConcern(concern)}
          class="px-5 py-2 rounded-full border text-[13px] transition-all duration-300
          {data.concerns.includes(concern) ? 'bg-stone-800 text-white border-stone-800' : 'bg-white text-stone-500 border-stone-200 hover:border-stone-400'}"
        >
          {concern}
        </button>
      {/each}
    </div>
  </div>

  <!-- Sensitivity Scale -->
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="w-1 h-5 bg-luxury-copper"></div>
        <h3 class="text-lg font-serif italic text-stone-800">Mức độ nhạy cảm</h3>
      </div>
      <span class="text-sm font-medium text-luxury-copper italic">{data.sensitivity}/10</span>
    </div>
    <div class="relative pt-2">
      <input
        type="range"
        min="1"
        max="10"
        bind:value={data.sensitivity}
        class="w-full h-1 bg-stone-200 rounded-lg appearance-none cursor-pointer accent-luxury-copper"
      />
      <div class="flex justify-between mt-2 text-[10px] text-stone-400 uppercase tracking-widest">
        <span>Rất khỏe</span>
        <span>Rất nhạy cảm</span>
      </div>
    </div>
  </div>
</div>

<style>
  input[type='range']::-webkit-slider-runnable-track {
    background: #e5e7eb;
    height: 2px;
  }
  input[type='range']::-webkit-slider-thumb {
    margin-top: -6px;
    width: 14px;
    height: 14px;
    background: #c5a059;
    border-radius: 50%;
    cursor: pointer;
    appearance: none;
    border: 2px solid white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
</style>
