<script lang="ts">
  import { ShieldCheck, Zap, Droplets } from 'lucide-svelte';
  
  let { product } = $props();
  const metadata = $derived(product?.metadata || {});
  
  const claims = $derived([
    metadata.science_claims?.[0] || { label: 'HỆ THỐNG // LÕI NANO-BẠC', content: 'Phá vỡ cấu trúc vi khuẩn gây mùi ngay lập tức bằng mạng lưới ion bạc tự kích hoạt.' },
    metadata.science_claims?.[1] || { label: 'KIỂM ĐỊNH // CHỨNG THỰC', content: 'Công nghệ khóa mùi tuyệt đối, giữ bạn khô thoáng và tự tin suốt 48H.' }
  ]);
  const stats = $derived(metadata.science_stats || { value: '48', unit: 'H', label: 'PHÒNG NGỰ CHỦ ĐỘNG' });

  const tech = $derived([
    {
      icon: ShieldCheck,
      title: typeof claims[0].label === 'string' ? claims[0].label : 'Innovation Core',
      desc: typeof claims[0].content === 'string' ? claims[0].content : 'Protective molecular shield.'
    },
    {
      icon: Zap,
      title: `${stats.value}${stats.unit} ${stats.label}`,
      desc: typeof metadata.science_subheadline === 'string' ? metadata.science_subheadline : "Công nghệ Nano Bạc Tự Thân độc bản."
    },
    {
      icon: Droplets,
      title: typeof claims[1].label === 'string' ? claims[1].label : 'Quality Analysis',
      desc: typeof claims[1].content === 'string' ? claims[1].content : 'High-precision stability verification.'
    }
  ]);
</script>

<div class="h-full flex flex-col justify-center px-6 py-20 bg-[#020617]">
  <div class="mb-10">
    <h2 class="text-3xl font-black text-white leading-tight uppercase tracking-tighter italic">
      {metadata.science_headline || 'TẠI SAO LẠI HIỆU QUẢ?'}
    </h2>
    <p class="mt-4 text-white/40 text-[10px] uppercase tracking-[0.3em] font-medium leading-relaxed max-w-[90%]">
      {metadata.science_subheadline || `Công nghệ Nano Bạc Tự Thân độc bản.`}
    </p>
  </div>

  <div class="space-y-4">
    {#each tech as item}
      {@const Icon = item.icon}
      <div class="p-5 bg-white/5 border border-white/10 rounded-3xl backdrop-blur-md flex gap-4">
        <div class="w-10 h-10 rounded-2xl bg-blue-500/20 flex items-center justify-center shrink-0 border border-blue-500/20">
          <Icon class="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h4 class="text-white font-black mb-1 uppercase tracking-wider text-[11px] leading-tight">{@html item.title}</h4>
          <p class="text-white/50 text-[10px] leading-relaxed">{@html item.desc}</p>
        </div>
      </div>
    {/each}
  </div>

  <div class="mt-12 p-1 bg-gradient-to-r from-blue-500/20 to-transparent rounded-2xl">
    <div class="px-5 py-3 bg-black/40 rounded-[inherit] flex items-center justify-between">
      <span class="text-[10px] text-white/60 font-medium tracking-[0.2em] uppercase">Clinical Verification</span>
      <div class="flex gap-2">
        <div class="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
          <ShieldCheck class="w-2.5 h-2.5 text-emerald-400" />
        </div>
        <div class="w-4 h-4 rounded-full bg-blue-500/20 flex items-center justify-center">
          <Zap class="w-2.5 h-2.5 text-blue-400" />
        </div>
      </div>
    </div>
  </div>
</div>
