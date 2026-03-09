<script lang="ts">
    import Check from "lucide-svelte/icons/check";

    let { filteredPermissions, roleHasPerm, togglePermission, getGroupLabel, viewMode } = $props<{
        filteredPermissions: any[];
        roleHasPerm: (code: string) => boolean;
        togglePermission: (code: string) => void;
        getGroupLabel: (prefix: string) => string;
        viewMode: "grid" | "list";
    }>();
</script>

<div class="{viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3' : 'flex flex-col gap-2'}">
    {#each filteredPermissions as perm, i (perm.id)}
        {@const active = roleHasPerm(perm.code)}
        {@const group = perm.code.split(':')[0]}
        <button
            onclick={() => togglePermission(perm.code)}
            class="flex items-start gap-3 p-3.5 rounded-xl border transition-all text-left
            {active
                ? 'bg-green-500/5 border-green-500/20 hover:border-green-500/40'
                : 'bg-white/[0.02] border-white/5 hover:border-white/10 opacity-60 hover:opacity-100'}"
        >
            <div class="w-5 h-5 rounded-md flex items-center justify-center shrink-0 mt-0.5
            {active ? 'bg-red-500 text-white' : 'bg-white/5 border border-white/10'}">
                {#if active}
                    <Check size={12} strokeWidth={3} />
                {/if}
            </div>
            <div class="flex-1 min-w-0">
                <div class="text-[11px] font-semibold text-white truncate">{perm.name}</div>
                <div class="text-[9px] font-mono text-gray-600 mt-0.5 truncate">{perm.code}</div>
                <div class="mt-1.5 flex items-center justify-between">
                    <span class="text-[9px] px-2 py-0.5 rounded-md bg-white/5 text-gray-500">{getGroupLabel(group)}</span>
                    <span class="text-[9px] font-mono text-gray-700">ID: {i + 1}</span>
                </div>
            </div>
        </button>
    {/each}
</div>
