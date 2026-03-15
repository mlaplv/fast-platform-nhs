<script lang="ts">
  import CircleCheck from "lucide-svelte/icons/circle-check";
  import ShieldCheck from "lucide-svelte/icons/shield-check";

  import type { Role } from "$lib/types";

  let { role, isSelected, allPermissionsCount, style, onSelect } = $props<{
    role: Role;
    isSelected: boolean;
    allPermissionsCount: number;
    style: { gradient: string; badge: string; border: string };
    onSelect: (id: string) => void;
  }>();

  let permCount = $derived(role.permissions.length);
  let isFullAccess = $derived(permCount === allPermissionsCount);
  let percent = $derived(allPermissionsCount ? Math.round((permCount / allPermissionsCount) * 100) : 0);
</script>

<button
  onclick={() => onSelect(role.id)}
  class="relative flex flex-col justify-between p-5 rounded-xl bg-gradient-to-br {style.gradient} border transition-all text-left group overflow-hidden
    {isSelected ? style.border + ' shadow-[0_0_20px_rgba(255,255,255,0.05)] scale-[1.02]' : 'border-white/5 hover:border-white/15 hover:shadow-lg'}"
>
  <!-- Scan Line Effect -->
  {#if isSelected}
    <div class="absolute inset-0 bg-gradient-to-b from-white/[0.03] via-transparent to-transparent pointer-events-none"></div>
    <div class="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
  {/if}

  <div class="flex items-center justify-between mb-3 relative">
    <span class="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold text-white tracking-wider {style.badge} shadow-sm">{role.name}</span>
    <span class="text-[10px] font-mono text-gray-400/60 ml-4">{permCount}/{allPermissionsCount}</span>
  </div>

  <!-- Permission Arc Indicator -->
  <div class="flex items-center gap-2 mt-1 relative">
    <div class="flex-1 h-0.5 bg-white/5 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-700 ease-out {isFullAccess ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.4)]' : 'bg-white/20'}"
        style:width="{percent}%"
      ></div>
    </div>
  </div>

  <span class="text-[9px] font-mono mt-2 relative">
    {#if isFullAccess}
      <span class="flex items-center gap-1 text-green-400/90">
        <ShieldCheck size={10} /> FULL ACCESS
      </span>
    {:else}
      <span class="text-gray-500 tracking-wider uppercase">Limited</span>
    {/if}
  </span>

  {#if isSelected}
    <div class="absolute bottom-0 left-0 right-0 h-0.5 {style.badge}"></div>
  {/if}
</button>
