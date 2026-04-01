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

<div class="h-full flex flex-col px-6 pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] bg-[#01030a] relative overflow-hidden">
  <div class="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/3"></div>
  <div class="absolute bottom-0 left-0 w-48 h-48 bg-indigo-600/5 blur-[100px] rounded-full translate-y-1/2 -translate-x-1/4"></div>

  <div class="mt-10 mb-8">
    <h2 class="text-4xl font-black text-white leading-[1.1] uppercase tracking-tighter italic">
      {metadata.science_headline || 'TẠI SAO LẠI HIỆU QUẢ?'}
    </h2>
    <p class="mt-4 text-white/40 text-[9px] uppercase tracking-[0.4em] font-black leading-relaxed max-w-[85%] italic">
      {metadata.science_subheadline || `Công nghệ Nano Bạc Tự Thân độc bản.`}
    </p>
  </div>

  <div class="space-y-4 flex-1 overflow-y-auto pr-1">
    {#each tech as item}
      {@const Icon = item.icon}
      <div class="p-6 bg-white/[0.03] border border-white/10 rounded-[2.5rem] backdrop-blur-2xl flex gap-5 group hover:bg-white/[0.05] transition-all duration-300">
        <div class="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center shrink-0 border border-blue-500/20 relative">
          <div class="absolute inset-0 bg-blue-400/20 blur-md rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <Icon class="w-6 h-6 text-blue-400 relative z-10" />
        </div>
        <div>
          <h4 class="text-white font-black mb-1.5 uppercase tracking-[0.1em] text-xs leading-tight">{item.title}</h4>
          <p class="text-white/40 text-[10px] leading-relaxed font-medium">{@html item.desc}</p>
        </div>
      </div>
    {/each}
  </div>

  <div class="mt-8 mb-4 p-[1px] bg-gradient-to-r from-blue-500/30 to-white/5 rounded-3xl">
    <div class="px-6 py-4 bg-[#050510]/80 backdrop-blur-3xl rounded-[inherit] flex items-center justify-between">
      <div class="flex flex-col">
        <span class="text-[8px] text-white/20 font-black tracking-[0.3em] uppercase mb-0.5">Safety & Protocol</span>
        <span class="text-[10px] text-white/80 font-black tracking-widest uppercase italic">Clinical Verification</span>
      </div>
      <div class="flex -space-x-2">
        <div class="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center backdrop-blur-md">
          <ShieldCheck class="w-4 h-4 text-emerald-400" />
        </div>
        <div class="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-500/30 flex items-center justify-center backdrop-blur-md relative z-10">
          <Zap class="w-4 h-4 text-blue-400" />
        </div>
      </div>
    </div>
  </div>
</div>
