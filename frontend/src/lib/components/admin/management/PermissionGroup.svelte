<script lang="ts">
    import ChevronRight from "lucide-svelte/icons/chevron-right";
    import Check from "lucide-svelte/icons/check";
    import Lock from "lucide-svelte/icons/lock";
    import type { Permission } from "$lib/types";

    let { group, perms, getGroupIcon, getGroupLabel, roleHasPerm } = $props<{
        group: string;
        perms: Permission[];
        getGroupIcon: (g: string) => string;
        getGroupLabel: (g: string) => string;
        roleHasPerm: (code: string) => boolean;
    }>();

    let activeCount = $derived(perms.filter((p) => roleHasPerm(p.code)).length);
    let groupPercent = $derived(perms.length ? Math.round((activeCount / perms.length) * 100) : 0);
    let isExpanded = $state(true);

    // Color scheme based on completion
    let barColor = $derived(
        groupPercent === 100 ? 'bg-[#00FFFF] shadow-[0_0_8px_rgba(0,255,255,0.3)]'
        : groupPercent > 50 ? 'bg-blue-400'
        : groupPercent > 0 ? 'bg-fuchsia-500'
        : 'bg-transparent'
    );
</script>

<div class="rounded-xl border border-white/[0.06] overflow-hidden bg-white/[0.015] hover:bg-white/[0.025] transition-colors">
    <button
        onclick={() => isExpanded = !isExpanded}
        class="w-full flex items-center gap-3 px-5 py-3.5 cursor-pointer transition-colors group/gh text-left"
    >
        <span class="text-sm grayscale-[30%] opacity-80 group-hover/gh:opacity-100 transition-opacity">{getGroupIcon(group)}</span>
        <span class="text-[11px] font-bold text-white tracking-wide">{getGroupLabel(group)}</span>
        <span class="px-1.5 py-0.5 rounded bg-white/[0.06] text-[9px] font-mono text-gray-500">{activeCount}/{perms.length}</span>

        <div class="flex-1 h-[3px] bg-white/[0.04] rounded-full overflow-hidden mx-3">
            <div
                class="h-full rounded-full transition-all duration-700 ease-out {barColor}"
                style:width="{groupPercent}%"
            ></div>
        </div>

        <span class="text-[9px] font-mono {groupPercent === 100 ? 'text-[#00FFFF]' : 'text-gray-600'}">{groupPercent}%</span>
        <ChevronRight size={14} class="text-gray-600 group-hover/gh:text-white transition-all duration-300 {isExpanded ? 'rotate-90' : ''}" />
    </button>

    {#if isExpanded && activeCount > 0}
        <div class="px-5 pb-4 pt-1">
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 sm:gap-1.5">
                {#each perms as perm}
                    {@const active = roleHasPerm(perm.code)}
                    {#if active}
                        <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#00FFFF]/[0.04] border border-[#00FFFF]/10 group/item hover:border-[#00FFFF]/25 transition-all">
                            <div class="w-3.5 h-3.5 rounded flex items-center justify-center bg-[#00FFFF]/15 text-[#00FFFF]">
                                <Check size={9} />
                            </div>
                            <span class="text-[10px] font-mono text-gray-200 truncate tracking-wide">{perm.code.split(':')[1] || perm.code}</span>
                        </div>
                    {:else}
                        <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.01] border border-white/[0.03] opacity-25">
                            <div class="w-3.5 h-3.5 rounded flex items-center justify-center bg-white/5 text-gray-700">
                                <Lock size={8} />
                            </div>
                            <span class="text-[10px] font-mono text-gray-600 truncate">{perm.code.split(':')[1] || perm.code}</span>
                        </div>
                    {/if}
                {/each}
            </div>
        </div>
    {/if}
</div>
