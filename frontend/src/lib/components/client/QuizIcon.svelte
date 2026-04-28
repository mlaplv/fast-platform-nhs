<script lang="ts">
  import { 
    Sparkles, 
    Waves, 
    Zap, 
    Timer, 
    Calendar, 
    Dna, 
    PlusCircle, 
    ShieldAlert,
    Activity,
    ShieldX,
    Wind,
    Shield,
    Sun,
    Layers,
    Moon,
    CloudMoon,
    ShieldCheck,
    Target,
    Heart,
    Flame,
    Droplets,
    RefreshCw,
    Circle
  } from 'lucide-svelte';

  let { icon } = $props<{ icon: string }>();

  const iconMap: Record<string, import('svelte').Component> = {
    // 🚀 Elite V2.2: Comprehensive Bio-Icon Mapping
    'Circle': Circle,
    'Zap': Zap,
    'Sparkles': Sparkles,
    'Flame': Flame,
    'Sun': Sun,
    'Droplets': Droplets,
    'Moon': Moon,
    'CloudMoon': CloudMoon,
    'Activity': Activity,
    'ShieldAlert': ShieldAlert,
    'ShieldCheck': ShieldCheck,
    'Target': Target,
    'Heart': Heart,
    'Wind': Wind,
    'Shield': Shield,
    'Layers': Layers,
    
    // Legacy Emoji Mappings (Backwards Compatibility)
    '🛁': Wind,
    '👙': Shield,
    '✨': Sun,
    '💧': Layers,
    '🌕': Moon,
    '🌗': CloudMoon,
    '🌑': ShieldAlert,
    '🔘': ShieldCheck,
    '🌱': Sparkles,
    '🔄': RefreshCw,
    '🚀': Zap,
    '😊': Sparkles,
    '😐': Activity,
    '🕒': Timer,
    '📅': Calendar,
    '🧬': Dna,
    'Plus': PlusCircle,
    'none': Circle,

    // Legacy String Mappings
    'light': Sparkles,
    'medium': Waves,
    'heavy': ShieldAlert,
    'recent': Timer,
    'chronic': Calendar,
    'genetic': Dna,
    'failed': ShieldX
  };

  const IconComponent = $derived(iconMap[icon] || Activity);
</script>

<div class="relative flex items-center justify-center w-full h-full group/icon">
  <!-- Liquid Glow Layer -->
  <div class="absolute inset-0 bg-blue-500/10 blur-[20px] rounded-full scale-110 opacity-0 group-hover/icon:opacity-100 transition-opacity duration-700"></div>
  
  <!-- Icon Stack -->
  <div class="relative transition-all duration-500 group-hover/icon:scale-110 group-hover/icon:rotate-[5deg]">
    <IconComponent 
      size={36} 
      strokeWidth={1.5} 
      class="text-blue-400/80 drop-shadow-[0_0_12px_rgba(96,165,250,0.4)]"
    />
  </div>

  <!-- Subtle Inner Flare -->
  <div class="absolute w-1 h-1 bg-white rounded-full blur-[2px] top-1/4 left-1/4 opacity-30"></div>
</div>

<style>
  :global(.lucide) {
    transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  }
</style>
