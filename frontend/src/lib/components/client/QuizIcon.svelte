<script lang="ts">
    import Sparkles from "@lucide/svelte/icons/sparkles";
  import Waves from "@lucide/svelte/icons/waves";
  import Zap from "@lucide/svelte/icons/zap";
  import Timer from "@lucide/svelte/icons/timer";
  import Calendar from "@lucide/svelte/icons/calendar";
  import Dna from "@lucide/svelte/icons/dna";
  import PlusCircle from "@lucide/svelte/icons/plus-circle";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Activity from "@lucide/svelte/icons/activity";
  import ShieldX from "@lucide/svelte/icons/shield-x";
  import Wind from "@lucide/svelte/icons/wind";
  import Shield from "@lucide/svelte/icons/shield";
  import Sun from "@lucide/svelte/icons/sun";
  import Layers from "@lucide/svelte/icons/layers";
  import Moon from "@lucide/svelte/icons/moon";
  import CloudMoon from "@lucide/svelte/icons/cloud-moon";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Target from "@lucide/svelte/icons/target";
  import Heart from "@lucide/svelte/icons/heart";
  import Flame from "@lucide/svelte/icons/flame";
  import Droplets from "@lucide/svelte/icons/droplets";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Circle from "@lucide/svelte/icons/circle";

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
  <div class="absolute inset-0 bg-luxury-sakura/10 blur-[20px] rounded-full scale-110 opacity-0 group-hover/icon:opacity-100 transition-opacity duration-700"></div>
  
  <!-- Icon Stack -->
  <div class="relative transition-all duration-500 group-hover/icon:scale-110 group-hover/icon:rotate-[5deg]">
    <IconComponent 
      size={36} 
      strokeWidth={1.5} 
      class="text-[var(--luxury-sakura,#FFB7C5)] drop-shadow-[0_0_12px_rgba(255,183,197,0.4)]"
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
