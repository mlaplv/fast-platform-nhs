<script lang="ts">
  import { slide } from "svelte/transition";
  import Shield from "lucide-svelte/icons/shield";
  import MoreVertical from "lucide-svelte/icons/more-vertical";
  import Check from "lucide-svelte/icons/check";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import Lock from "lucide-svelte/icons/lock";
  import Unlock from "lucide-svelte/icons/unlock";
  import Edit2 from "lucide-svelte/icons/edit-2";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import type { User, Role, Permission } from "$lib/types";

  let {
    user,
    roles,
    isExpanded,
    onToggleExpand,
    onToggleRole,
    onToggleStatus,
    onDelete,
    onEdit,
  } = $props<{
    user: User;
    roles: Role[];
    isExpanded: boolean;
    onToggleExpand: (id: string) => void;
    onToggleRole: (userId: string, roleCode: string) => void;
    onToggleStatus: (userId: string) => void;
    onDelete: (userId: string) => void;
    onEdit: (user: User) => void;
  }>();

  function getUniquePermissions(user: User) {
    const perms = new Set<string>();
    user.roles.forEach((r: Role) => {
      r.permissions.forEach((p: Permission) => perms.add(p.code));
    });
    return Array.from(perms).sort();
  }
</script>

<div
  class="group relative z-10 hover:z-50 focus-within:z-50 flex flex-col md:grid md:grid-cols-[minmax(250px,2fr)_1fr_100px] md:items-center bg-[#0a0a0a] md:bg-transparent border border-white/5 md:border-none rounded-xl md:rounded-none p-4 sm:p-0 hover:bg-white/[0.03] transition-colors duration-300 {isExpanded
    ? 'bg-white/[0.03] border-l border-l-[#00FFFF]/50'
    : ''}"
>
  <!-- User Info Column -->
  <div class="sm:px-6 sm:py-5 relative z-10">
    <div class="flex items-start sm:items-center gap-3">
      <button
        onclick={() => onToggleExpand(user.id)}
        class="p-2 bg-black/40 hover:bg-[#00FFFF]/10 border border-transparent hover:border-[#00FFFF]/20 shadow-sm rounded-xl transition-all {isExpanded
          ? 'rotate-180 text-[#00FFFF] border-[#00FFFF]/20 bg-[#00FFFF]/5'
          : 'text-gray-500 hover:text-[#00FFFF]'}"
      >
        <ChevronDown size={14} />
      </button>
      <div class="flex flex-col justify-center min-w-0 flex-1">
        <span
          class="text-[14px] sm:text-[13px] font-bold text-gray-100 group-hover:text-white transition-colors tracking-wide flex items-center flex-wrap gap-2 truncate"
        >
          {user.name || "Unknown Entity"}
          {#if user.status === "LOCKED"}
            <span
              class="px-2 py-0.5 rounded text-[8px] font-mono font-bold bg-red-500/20 text-red-500 uppercase tracking-widest border border-red-500/30"
              >LOCKED</span
            >
          {/if}
        </span>
        <span
          class="text-[10px] font-mono text-gray-500 mt-1 uppercase tracking-widest group-hover:text-[#00FFFF]/50 transition-colors truncate"
          >{user.email}</span
        >
      </div>
    </div>
  </div>

  <!-- Assigned Tiers -->
  <div class="sm:px-6 sm:py-5 mt-3 sm:mt-0 pl-11 sm:pl-0">
    <div class="flex flex-wrap gap-2">
      {#each user.roles as role}
        <span
          class="px-3 py-1.5 rounded-lg text-[9px] font-bold font-mono uppercase tracking-widest shadow-inner inline-flex border border-[#00FFFF]/40 bg-[#00FFFF]/10 text-[#00FFFF]"
        >
          {role.code}
        </span>
      {/each}
    </div>
  </div>

  <!-- Access Control Actions -->
  <div
    class="absolute top-4 right-4 sm:relative sm:top-0 sm:right-0 sm:px-6 sm:py-5 md:text-right relative z-30 sm:w-[120px]"
  >
    <div
      class="relative inline-block text-left group/menu {isExpanded
        ? 'z-50'
        : ''}"
    >
      <button
        class="p-2 text-gray-500 hover:text-white transition-colors bg-white/5 sm:bg-transparent hover:bg-white/10 rounded-xl"
      >
        <MoreVertical size={16} />
      </button>
      <div
        class="absolute right-0 top-full sm:pt-2 w-56 opacity-0 invisible group-hover/menu:opacity-100 group-hover/menu:visible transition-all duration-300 z-[var(--z-admin-hud)] origin-top-right group-hover/menu:scale-100 scale-95 mt-1 sm:mt-0 border border-white/10 rounded-xl bg-[#0a0a0a]/95 backdrop-blur-xl shadow-[0_10px_40px_rgba(0,0,0,0.8)]"
      >
        <div class="flex flex-col overflow-hidden">
          <div class="p-1 border-b border-white/5">
            <button
              onclick={() => onEdit(user)}
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[10px] font-mono tracking-wide transition-colors text-gray-400 hover:text-white hover:bg-white/10"
            >
              <Edit2 size={12} class="text-[#00FFFF]/70" /><span
                >Modify Identity</span
              >
            </button>
            <button
              onclick={() => onToggleStatus(user.id)}
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[10px] font-mono tracking-wide transition-colors text-gray-400 hover:text-white hover:bg-white/10"
            >
              {#if user.status === "LOCKED"}
                <Unlock size={12} class="text-[#00FFFF]/70" /><span
                  >Unlock Entity</span
                >
              {:else}
                <Lock size={12} class="text-red-500/70" /><span
                  class="text-red-400">Lock Entity</span
                >
              {/if}
            </button>
            <button
              onclick={() => onDelete(user.id)}
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[10px] font-mono tracking-wide transition-colors text-red-500/70 hover:text-red-500 hover:bg-red-500/10"
            >
              <Trash2 size={12} /><span>Revoke Access</span>
            </button>
          </div>
          <div class="px-4 py-2 bg-white/[0.02] border-b border-white/5">
            <span
              class="text-[9px] font-mono font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2"
            >
              <Shield size={10} class="text-[#00FFFF]" /> Assign Security Tier
            </span>
          </div>
          <div class="max-h-[180px] overflow-y-auto p-1">
            {#each roles as role}
              <button
                onclick={() => onToggleRole(user.id, role.code)}
                class="w-full flex items-center justify-between px-3 py-3 rounded-lg text-[10px] font-mono tracking-wide transition-colors {user.roles.some(
                  (r) => r.code === role.code,
                )
                  ? 'text-white bg-white/5'
                  : 'text-gray-400 hover:text-white hover:bg-white/10'}"
              >
                <span>{role.name}</span>
                {#if user.roles.some((r) => r.code === role.code)}
                  <Check size={14} class="text-[#00FFFF]" />
                {/if}
              </button>
            {/each}
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Permission Matrix Expandable Section -->
  {#if isExpanded}
    <div
      class="col-span-1 md:col-span-3 mt-4 sm:mt-0 px-2 sm:px-0"
      transition:slide
    >
      <div
        class="sm:px-16 py-4 sm:py-6 bg-black/40 sm:bg-black/20 rounded-xl sm:rounded-none"
      >
        <div class="flex flex-col gap-3 sm:gap-4 px-3 sm:px-0">
          <div class="flex items-center gap-2">
            <Lock size={12} class="text-[#FFB800]/60" />
            <span
              class="text-[9px] font-mono text-gray-500 uppercase tracking-widest"
              >Effective Permission Matrix</span
            >
          </div>
          <div
            class="grid grid-cols-2 xs:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2"
          >
            {#each getUniquePermissions(user) as perm}
              <div
                class="px-2 py-1.5 sm:py-1 bg-white/[0.02] border border-white/5 rounded-lg flex items-center justify-center text-center"
              >
                <span
                  class="text-[8px] font-mono text-gray-400 uppercase break-all leading-tight"
                  >{perm}</span
                >
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>
