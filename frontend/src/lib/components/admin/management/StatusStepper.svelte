<script lang="ts">
  import { fly, fade, scale } from "svelte/transition";
  import FileText from "lucide-svelte/icons/file-text";
  import ShieldCheck from "lucide-svelte/icons/shield-check";
  import Truck from "lucide-svelte/icons/truck";
  import PackageCheck from "lucide-svelte/icons/package-check";
  import Check from "lucide-svelte/icons/check";
  import { ORDER_STATUS_MAP } from "$lib/constants/order";

  let { 
    currentStatus = "pending",
    onStatusChange
  } = $props<{
    currentStatus: string;
    onStatusChange?: (status: string) => void;
  }>();

  const STAGES = [
    { key: "pending", label: "Tiếp nhận", icon: FileText },
    { key: "packed", label: "Bảo mật", icon: ShieldCheck },
    { key: "shipping", label: "Vận chuyển", icon: Truck },
    { key: "delivered", label: "Thành công", icon: PackageCheck }
  ];

  const statusOrder = ["pending", "packed", "shipping", "delivered"];
  const currentIndex = $derived(statusOrder.indexOf(currentStatus.toLowerCase()));

  function isCompleted(index: number) {
    return index < currentIndex && currentStatus.toLowerCase() !== 'cancelled';
  }

  function isActive(index: number) {
    return index === currentIndex && currentStatus.toLowerCase() !== 'cancelled';
  }

  function canInteract(index: number) {
    // Only allow clicking the NEXT logical step (Elite Direct Action)
    return index === currentIndex + 1 && currentStatus.toLowerCase() !== 'cancelled' && currentStatus.toLowerCase() !== 'delivered';
  }

  function handleNodeClick(key: string, index: number) {
    if (canInteract(index)) {
      onStatusChange?.(key);
    }
  }
</script>

<div class="relative w-full py-10 px-4 sm:px-8 bg-black/40 backdrop-blur-3xl border border-white/5 rounded-3xl overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)] group">
  <!-- Background Glow -->
  <div class="absolute -top-24 -left-24 w-48 h-48 bg-neon-cyan/5 rounded-full blur-[100px] animate-pulse"></div>
  <div class="absolute -bottom-24 -right-24 w-48 h-48 bg-fuchsia-500/5 rounded-full blur-[100px] animate-pulse" style="animation-delay: 1s"></div>

  <!-- Progress Track (2-row: icons + connectors, then labels) -->
  <div class="flex flex-col gap-3">

    <!-- Row 1: Icons + Connectors -->
    <div class="flex items-center">
      {#each STAGES as stage, i}
        <!-- Node button -->
        <button
          onclick={() => handleNodeClick(stage.key, i)}
          disabled={!canInteract(i)}
          class="relative shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-500 border z-20
          {isCompleted(i) ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.2)]' :
           isActive(i)    ? 'bg-fuchsia-500/20 border-fuchsia-500/50 text-white scale-110 shadow-[0_0_40px_rgba(240,0,255,0.4)] ring-4 ring-fuchsia-500/10' :
           'bg-[#0a0a0a] border-white/10 text-gray-500'}
          {canInteract(i) ? 'cursor-pointer hover:scale-125 hover:border-fuchsia-400 hover:bg-fuchsia-500/30 hover:shadow-[0_0_30px_rgba(240,0,255,0.4)] animate-pulse' : 'cursor-default'}"
        >
          <!-- Solid inner to hide bg artifacts -->
          <div class="absolute inset-[1px] rounded-[10px] bg-[#050505] -z-10"></div>

          {#if isCompleted(i)}
            <div in:scale={{ duration: 400 }}>
              <Check size={20} strokeWidth={3} />
            </div>
          {:else}
            <stage.icon size={18} class={isActive(i) ? 'text-white pulse' : ''} />
          {/if}
        </button>

        <!-- Connector segment (EXISTS ONLY BETWEEN nodes) -->
        {#if i < STAGES.length - 1}
          <div class="flex-1 relative h-[3px] mx-1 pointer-events-none">
            <!-- Track -->
            <div class="absolute inset-0 bg-white/8 rounded-full"></div>
            <!-- Fill -->
            {#if i < currentIndex}
              <div
                class="absolute inset-0 rounded-full bg-gradient-to-r from-neon-cyan via-fuchsia-500 to-neon-cyan shadow-[0_0_12px_rgba(240,0,255,0.35)]"
                in:fade={{ duration: 600 }}
              >
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
              </div>
            {/if}
          </div>
        {/if}
      {/each}
    </div>

    <!-- Row 2: Labels (mirrored flex widths) -->
    <div class="flex items-start">
      {#each STAGES as stage, i}
        <!-- Label cell — same fixed width as icon button -->
        <div class="shrink-0 w-10 flex flex-col items-center">
          <span class="text-[9px] font-mono font-black tracking-[0.2em] uppercase transition-all duration-500
            {isActive(i) ? 'text-white' : isCompleted(i) ? 'text-neon-cyan/80' : 'text-gray-600'}">
            {stage.label}
          </span>
          {#if isActive(i)}
            <div in:fade class="w-1.5 h-1.5 rounded-full bg-neon-cyan mt-1 shadow-[0_0_10px_#00ffff,0_0_20px_#00ffff]"></div>
          {/if}
        </div>
        <!-- Spacer matching connector width -->
        {#if i < STAGES.length - 1}
          <div class="flex-1 mx-1"></div>
        {/if}
      {/each}
    </div>

  </div>
</div>

<style>
  @keyframes scale {
    from { transform: scale(0); }
    to { transform: scale(1); }
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%) scaleX(0.5); opacity: 0; }
    50% { opacity: 0.5; }
    100% { transform: translateX(200%) scaleX(0.5); opacity: 0; }
  }

  .animate-shimmer {
    animation: shimmer 2s infinite linear;
  }

  .pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1.1); }
    50% { opacity: 0.7; transform: scale(1); }
  }
</style>
