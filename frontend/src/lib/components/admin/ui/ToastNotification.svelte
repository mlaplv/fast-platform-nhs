<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { fade, fly, slide } from "svelte/transition";
  import { flip } from "svelte/animate";
  import CheckCircle from "@lucide/svelte/icons/check-circle";
  import AlertCircle from "@lucide/svelte/icons/alert-circle";
  import Info from "@lucide/svelte/icons/info";
  import X from "@lucide/svelte/icons/x";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";

  const toasts = $derived(nanobot.toasts);

  const TYPE_CONFIG = {
    success: {
      bg: "bg-[#0A0A0A]/90",
      border: "border-hacker-green/40",
      icon: ShieldCheck,
      iconColor: "text-hacker-green",
      glow: "shadow-[0_0_30px_rgba(0,255,102,0.15)]",
      label: "PROTOCOL_SUCCESS"
    },
    error: {
      bg: "bg-[#0A0A0A]/90",
      border: "border-alert-red/40",
      icon: AlertCircle,
      iconColor: "text-alert-red",
      glow: "shadow-[0_0_30px_rgba(255,51,51,0.15)]",
      label: "INTERNAL_ERROR"
    },
    info: {
      bg: "bg-[#0A0A0A]/90",
      border: "border-neon-cyan/40",
      icon: Info,
      iconColor: "text-neon-cyan",
      glow: "shadow-[0_0_30px_rgba(0,255,255,0.15)]",
      label: "SYSTEM_SIGNAL"
    },
    warning: {
      bg: "bg-[#0A0A0A]/90",
      border: "border-yellow-500/40",
      icon: AlertCircle,
      iconColor: "text-yellow-500",
      glow: "shadow-[0_0_30px_rgba(234,179,8,0.15)]",
      label: "SECURITY_WARNING"
    }
  };
</script>

<div class="fixed top-8 right-8 flex flex-col gap-3 w-80 pointer-events-none" style:z-index={Z_INDEX_ADMIN.TOAST}>
  {#each toasts as toast (toast.id)}
    {@const config = TYPE_CONFIG[toast.type]}
    <div
      animate:flip={{ duration: 400 }}
      in:fly={{ x: 50, duration: 500, opacity: 0 }}
      out:fly={{ x: 20, duration: 300, opacity: 0 }}
      class="pointer-events-auto relative group"
    >
      <div class="{config.bg} {config.border} {config.glow} border-2 rounded-2xl p-4 overflow-hidden bg-black/95 md:backdrop-blur-xl transition-all duration-300 hover:scale-[1.02]">
        
        <!-- Animated Background Line -->
        <div class="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
        
        <div class="flex items-start gap-4">
          <!-- Icon with Glow -->
          <div class="relative shrink-0 mt-1">
             <div class="absolute inset-0 {config.iconColor} blur-lg opacity-40 animate-pulse"></div>
             <config.icon size={20} class="relative {config.iconColor}" />
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <span class="{config.iconColor} font-mono text-[8px] font-bold tracking-[0.2em]">{config.label}</span>
              <button 
                onclick={() => nanobot.removeToast(toast.id)}
                class="text-white/20 hover:text-white transition-colors"
              >
                <X size={12} />
              </button>
            </div>
            
            <p class="text-xs text-white/80 font-mono leading-relaxed line-clamp-3">
              {toast.message}
            </p>
          </div>
        </div>

        <!-- Progress Bar (Ephemeral feel) -->
        <div class="absolute bottom-0 left-0 w-full h-[1px] bg-white/5 overflow-hidden">
            <div 
              class="h-full {config.iconColor.replace('text-', 'bg-')} opacity-40 animate-toast-progress"
              style:animation-duration="{(toast.duration || 4000)}ms"
            ></div>
        </div>
      </div>
    </div>
  {/each}
</div>

<style>
  .animate-toast-progress {
    animation-name: toast-progress;
    animation-timing-function: linear;
    animation-fill-mode: forwards;
  }

  @keyframes toast-progress {
    from { width: 100%; }
    to { width: 0%; }
  }
</style>
